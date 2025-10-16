"""
Enhanced Stream Processor for VRouter Agent

This module provides an event-driven, push-based stream processing system
that replaces the polling-based approach with efficient transaction handling.
"""

import asyncio
import json
import time
from typing import Dict, Any,List, Callable
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ThreadPoolExecutor

from loguru import logger as log
from sqlmodel import Session

from vrouter_agent.models import Transaction
from vrouter_agent.core.enums import  StreamItemTag
from vrouter_agent.services.chain import Chain, StreamItem
from vrouter_agent.core.config import settings
from vrouter_agent.utils.config import get_device_short_hostname
from vrouter_agent.tunnel_operations import TunnelOperations


class ProcessingStatus(Enum):
    """Transaction processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class TransactionEvent:
    """Represents a transaction event for processing."""
    transaction: Transaction
    stream: str
    session: Session
    timestamp: float
    retry_count: int = 0
    max_retries: int = 3
    status: ProcessingStatus = ProcessingStatus.PENDING


class EnhancedStreamProcessor:
    """
    Enhanced stream processor that handles transactions through push events
    instead of polling. Provides asynchronous processing, proper error handling,
    and comprehensive metrics.
    """
    
    def __init__(self, max_workers: int = 5, batch_size: int = 10):
        """
        Initialize the enhanced stream processor.
        
        Args:
            max_workers: Maximum number of worker threads
            batch_size: Number of transactions to process in batch
        """
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.hostname = get_device_short_hostname()
        
        # Initialize tunnel operations handler
        self.tunnel_operations = TunnelOperations(self.hostname)
        
        # Event queue for transactions
        self.event_queue = asyncio.Queue()
        self.processing_queue = asyncio.Queue()
        
        # Worker management
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.workers_running = False
        self.worker_tasks = []
        
        # Metrics and monitoring
        self.metrics = {
            'total_processed': 0,
            'successful_processed': 0,
            'failed_processed': 0,
            'retry_count': 0,
            'average_processing_time': 0.0,
            'queue_size': 0,
            'worker_utilization': 0.0,
            'start_time': time.time(),
            'last_activity': None
        }
        
        # Callbacks for different event types
        self.event_callbacks: Dict[str, List[Callable]] = {
            'transaction_received': [],
            'processing_started': [],
            'processing_completed': [],
            'processing_failed': [],
            'order_created': [],
            'order_updated': [],
            'order_deleted': []
        }
        
        # Configuration
        self.config = {
            'retry_delay_base': 2.0,
            'retry_delay_max': 30.0,
            'processing_timeout': 300.0,  # 5 minutes
            'batch_processing_interval': 1.0,
            'metrics_update_interval': 10.0
        }
        
        log.debug(f"Enhanced stream processor initialized with {max_workers} workers")
    
    async def start(self) -> bool:
        """
        Start the enhanced stream processor.
        
        Returns:
            bool: True if started successfully
        """
        try:
            log.debug("Starting enhanced stream processor...")
            
            self.workers_running = True
            
            # Start worker tasks
            for i in range(self.max_workers):
                worker_task = asyncio.create_task(
                    self._worker_loop(f"worker-{i}")
                )
                self.worker_tasks.append(worker_task)
            
            # Start monitoring task
            monitor_task = asyncio.create_task(self._monitor_loop())
            self.worker_tasks.append(monitor_task)
            
            # Start batch processor
            batch_task = asyncio.create_task(self._batch_processor_loop())
            self.worker_tasks.append(batch_task)
            
            # Start tunnel telemetry collection parallel to stream processing
            await self._start_tunnel_telemetry_collection()
            
            log.debug(f"Started {len(self.worker_tasks)} worker tasks")
            return True
            
        except Exception as e:
            log.error(f"Failed to start enhanced stream processor: {e}")
            return False
    
    async def stop(self) -> None:
        """Stop the enhanced stream processor."""
        log.debug("Stopping enhanced stream processor...")
        
        self.workers_running = False
        
        # Cancel all worker tasks
        for task in self.worker_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.worker_tasks:
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        # Stop tunnel telemetry collection
        await self._stop_tunnel_telemetry_collection()
        
        log.debug("Enhanced stream processor stopped")
    
    async def process_transaction(
        self, 
        transaction: Transaction, 
        stream: str, 
        session: Session
    ) -> bool:
        """
        Process a transaction event (push-based).
        
        Args:
            transaction: The transaction to process
            stream: Stream name
            session: Database session
            
        Returns:
            bool: True if successfully queued for processing
        """
        try:
            # Create transaction event
            event = TransactionEvent(
                transaction=transaction,
                stream=stream,
                session=session,
                timestamp=time.time()
            )
            
            # Add to processing queue
            await self.event_queue.put(event)
            
            # Update metrics
            self.metrics['queue_size'] = self.event_queue.qsize()
            self.metrics['last_activity'] = time.time()
            
            # Trigger callbacks
            await self._trigger_callbacks('transaction_received', event)
            
            log.debug(f"Transaction {transaction.txid} queued for processing")
            return True
            
        except Exception as e:
            log.error(f"Failed to queue transaction {transaction.txid}: {e}")
            return False
    
    async def _worker_loop(self, worker_id: str) -> None:
        """
        Main worker loop for processing transactions.
        
        Args:
            worker_id: Unique identifier for this worker
        """
        log.debug(f"Worker {worker_id} started")
        
        while self.workers_running:
            try:
                # Get event from queue with timeout
                try:
                    event = await asyncio.wait_for(
                        self.event_queue.get(), 
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Process the event
                await self._process_transaction_event(event, worker_id)
                
                # Mark task as done
                self.event_queue.task_done()
                
            except asyncio.CancelledError:
                log.debug(f"Worker {worker_id} cancelled")
                break
            except Exception as e:
                log.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1.0)
        
        log.debug(f"Worker {worker_id} stopped")
    
    async def _process_transaction_event(
        self, 
        event: TransactionEvent, 
        worker_id: str
    ) -> None:
        """
        Process a single transaction event.
        
        Args:
            event: Transaction event to process
            worker_id: ID of the processing worker
        """
        start_time = time.time()
        
        try:
            log.debug(f"Worker {worker_id} processing transaction {event.transaction.txid}")
            
            # Update event status
            event.status = ProcessingStatus.PROCESSING
            await self._trigger_callbacks('processing_started', event)
            
            
            # # Get stream item from blockchain
            chain = Chain(
                chain=settings.config.multichain.chain,
                user=settings.config.global_.user,
            )
 
            stream_data = chain.get_stream_item(event.stream, event.transaction.txid)   
            if not stream_data:
                raise ValueError(f"Transaction {event.transaction.txid} not found in stream")
            
            log.debug(f"Retrieved stream item for txid: {event.transaction.txid}, data size: {len(stream_data['data']) if stream_data.get('data') else 0}")
            
            # Create stream item
            if not stream_data.get("data"):
                raise ValueError(f"Invalid stream data: missing 'data' field. Available fields: {list(stream_data.keys())}")
            if not stream_data.get("txid"):
                raise ValueError(f"Invalid stream data: missing 'txid' field. Available fields: {list(stream_data.keys())}")
            log.debug(f"Stream data {stream_data['data']}")

            stream_item = StreamItem(
                data=stream_data['data'],
                txid=stream_data['txid']
            )
            log.debug(f"Created stream item for txid: {stream_item.txid}, data size: {len(stream_item.data) if stream_item.data else 0}")
            try:
                decrypted_data = stream_item.get_decrypted_data()
                
                decrypted_data = json.loads(decrypted_data)
                log.debug(f"Decrypted data {decrypted_data} for txid: {stream_item.txid}")
            except Exception as decrypt_error:
                raise ValueError(f"Failed to decrypt or parse stream data: {decrypt_error}")
            
            # Validate required fields in decrypted data
            if not decrypted_data.get("tag"):
                raise ValueError(f"Decrypted data missing 'tag' field. Available fields: {list(decrypted_data.keys())}")
            
            
            # Process based on tag
            if decrypted_data["tag"] == StreamItemTag.ORDER:
                await self.tunnel_operations.process_tunnel_config_event(decrypted_data, event, self._trigger_callbacks)
            elif decrypted_data["tag"] == StreamItemTag.TUNNEL_CONFIG:
                await self.tunnel_operations.process_tunnel_config_event(decrypted_data, event, self._trigger_callbacks)
            elif decrypted_data["tag"] == StreamItemTag.NETWORK:
                await self._process_network_event(decrypted_data, event)
            else:
                log.warning(f"Unknown tag: {decrypted_data['tag']}")
            
            # Update metrics
            processing_time = time.time() - start_time
            self.metrics['total_processed'] += 1
            self.metrics['successful_processed'] += 1
            self._update_average_processing_time(processing_time)
            
            event.status = ProcessingStatus.COMPLETED
            await self._trigger_callbacks('processing_completed', event)
            
            log.debug(f"Transaction {event.transaction.txid} processed successfully in {processing_time:.2f}s")
            
        except Exception as e:
            log.error(f"Failed to process transaction {event.transaction.txid}: {e}")
            
            # Handle retry logic
            if event.retry_count < event.max_retries:
                event.retry_count += 1
                event.status = ProcessingStatus.RETRY
                
                # Calculate retry delay with exponential backoff
                delay = min(
                    self.config['retry_delay_max'],
                    self.config['retry_delay_base'] ** event.retry_count
                )
                
                log.debug(f"Retrying transaction {event.transaction.txid} in {delay}s (attempt {event.retry_count})")
                
                # Re-queue with delay
                await asyncio.sleep(delay)
                await self.event_queue.put(event)
                
                self.metrics['retry_count'] += 1
            else:
                log.error(f"Max retries exceeded for transaction {event.transaction.txid}")
                event.status = ProcessingStatus.FAILED
                self.metrics['failed_processed'] += 1
                await self._trigger_callbacks('processing_failed', event)
    
    async def _process_network_event(
        self, 
        decrypted_data: Dict[str, Any], 
        event: TransactionEvent
    ) -> None:
        """
        Process a network-related event.
        
        Args:
            decrypted_data: Decrypted transaction data
            event: Transaction event being processed
        """
        log.debug(f"Processing network event for transaction {event.transaction.txid}")
        # Placeholder for network event processing
        # Add your network-specific logic here
        pass
    
    async def _trigger_callbacks(self, event_type: str, data: Any) -> None:
        """
        Trigger registered callbacks for an event type.
        
        Args:
            event_type: Type of event
            data: Event data to pass to callbacks
        """
        if event_type in self.event_callbacks:
            for callback in self.event_callbacks[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    log.error(f"Error in callback for {event_type}: {e}")
    
    def _update_average_processing_time(self, processing_time: float) -> None:
        """Update the average processing time metric."""
        current_avg = self.metrics['average_processing_time']
        total_processed = self.metrics['total_processed']
        
        if total_processed == 1:
            self.metrics['average_processing_time'] = processing_time
        else:
            # Calculate running average
            self.metrics['average_processing_time'] = (
                (current_avg * (total_processed - 1)) + processing_time
            ) / total_processed
    
    async def _batch_processor_loop(self) -> None:
        """
        Background loop for batch processing optimization.
        """
        log.debug("Batch processor loop started")
        
        while self.workers_running:
            try:
                await asyncio.sleep(self.config['batch_processing_interval'])
                
                # Update queue size metric
                self.metrics['queue_size'] = self.event_queue.qsize()
                
                # Calculate worker utilization
                active_workers = sum(1 for task in self.worker_tasks if not task.done())
                self.metrics['worker_utilization'] = active_workers / self.max_workers
                
            except asyncio.CancelledError:
                log.debug("Batch processor loop cancelled")
                break
            except Exception as e:
                log.error(f"Error in batch processor loop: {e}")
                await asyncio.sleep(1.0)
        
        log.debug("Batch processor loop stopped")
    
    async def _monitor_loop(self) -> None:
        """
        Background monitoring loop for metrics and health checks.
        """
        log.debug("Monitor loop started")
        
        while self.workers_running:
            try:
                await asyncio.sleep(self.config['metrics_update_interval'])
                
                # Log current metrics
                log.debug(f"Processor metrics: {self.metrics}")
                
                # Health check - restart workers if needed
                for i, task in enumerate(self.worker_tasks):
                    if task.done() and not task.cancelled():
                        log.warning(f"Worker task {i} completed unexpectedly, restarting...")
                        # Restart the worker
                        new_task = asyncio.create_task(
                            self._worker_loop(f"worker-{i}-restart")
                        )
                        self.worker_tasks[i] = new_task
                
            except asyncio.CancelledError:
                log.debug("Monitor loop cancelled")
                break
            except Exception as e:
                log.error(f"Error in monitor loop: {e}")
                await asyncio.sleep(1.0)
        
        log.debug("Monitor loop stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current processor status.
        
        Returns:
            Dict containing processor status information
        """
        return {
            "running": self.workers_running,
            "worker_count": len(self.worker_tasks),
            "queue_size": self.event_queue.qsize() if hasattr(self, 'event_queue') else 0,
            "uptime": time.time() - self.metrics['start_time'],
            "last_activity": self.metrics.get('last_activity'),
            "worker_utilization": self.metrics.get('worker_utilization', 0.0)
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current processor metrics.
        
        Returns:
            Dict containing processor metrics
        """
        return self.metrics.copy()
    
    def register_callback(self, event_type: str, callback: Callable) -> None:
        """
        Register a callback for a specific event type.
        
        Args:
            event_type: Type of event to listen for
            callback: Callback function to register
        """
        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []
        self.event_callbacks[event_type].append(callback)
    
    def unregister_callback(self, event_type: str, callback: Callable) -> None:
        """
        Unregister a callback for a specific event type.
        
        Args:
            event_type: Type of event
            callback: Callback function to unregister
        """
        if event_type in self.event_callbacks:
            try:
                self.event_callbacks[event_type].remove(callback)
            except ValueError:
                pass  # Callback not found
    
    async def _start_tunnel_telemetry_collection(self):
        """Start tunnel telemetry collection parallel to stream processing."""
        try:
            from vrouter_agent.telemetry.tunnel_telemetry import TunnelTelemetryCollector
            import vrouter_agent.telemetry.tunnel_telemetry as telemetry_module
            
            if telemetry_module.tunnel_telemetry_collector is None:
                log.debug("Initializing tunnel telemetry collector at application startup...")
                telemetry_module.tunnel_telemetry_collector = TunnelTelemetryCollector()
                await telemetry_module.tunnel_telemetry_collector.start_metrics_collection()
                log.debug("Successfully started tunnel telemetry collection parallel to stream processing")
            else:
                log.debug("Tunnel telemetry collector already exists")
                # Ensure metrics collection is running
                if not telemetry_module.tunnel_telemetry_collector._metrics_collection_running:
                    await telemetry_module.tunnel_telemetry_collector.start_metrics_collection()
                    log.debug("Restarted tunnel telemetry metrics collection")
                    
        except Exception as e:
            log.warning(f"Failed to start tunnel telemetry collection: {e}")
            # Don't raise - telemetry failures shouldn't break the application
    
    async def _stop_tunnel_telemetry_collection(self):
        """Stop tunnel telemetry collection."""
        try:
            import vrouter_agent.telemetry.tunnel_telemetry as telemetry_module
            
            if telemetry_module.tunnel_telemetry_collector is not None:
                await telemetry_module.tunnel_telemetry_collector.stop_metrics_collection()
                log.debug("Stopped tunnel telemetry collection")
            else:
                log.debug("Tunnel telemetry collector was not initialized")
                
        except Exception as e:
            log.warning(f"Error stopping tunnel telemetry collection: {e}")


# Global instance management
_processor_instance = None


async def get_stream_processor() -> EnhancedStreamProcessor:
    """
    Get the global stream processor singleton instance.
    
    Returns:
        EnhancedStreamProcessor: The singleton processor instance
    """
    global _processor_instance
    
    if _processor_instance is None:
        _processor_instance = EnhancedStreamProcessor()
        await _processor_instance.start()
    
    return _processor_instance



