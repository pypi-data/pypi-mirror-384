"""
StreamHandler module for processing multichain stream data.
Provides enhanced functionality for stream data processing with multichain integration.
"""

import json
import threading
import time
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from enum import Enum

from loguru import logger as log
from vrouter_agent.utils.mutichain import (
    get_multichain_client, 
    list_stream_items,
    MultichainConfig,
    multichain_client_context,
    ensure_stream_subscription,
    MultichainConnectionError,
    StreamNotFoundError
)
from vrouter_agent.models import Transaction


class StreamState(Enum):
    """Stream processing state."""
    INITIALIZED = "initialized"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class StreamConfig:
    """Configuration for stream processing."""
    chain_name: str
    user: str
    stream_name: str
    poll_interval: float = 5.0
    max_retries: int = 3
    timeout: float = 30.0
    batch_size: int = 100


class StreamHandler:
    """
    Enhanced stream handler for processing multichain stream data.
    Integrates with the existing multichain functionality and provides
    robust stream processing capabilities.
    """
    
    def __init__(self, stream: str, txid: str, config: Optional[StreamConfig] = None):
        """
        Initialize the StreamHandler.
        
        Args:
            stream: Stream name to process
            txid: Transaction ID for tracking
            config: Stream configuration (optional)
        """
        self.stream = stream
        self.txid = txid
        self.config = config or StreamConfig(
            chain_name="default",
            user="multichain",
            stream_name=stream
        )
        
        # Create multichain config for enhanced utilities
        self.multichain_config = MultichainConfig(
            chain_name=self.config.chain_name,
            user=self.config.user,
            max_retries=3,
            retry_delay=2.0
        )
        
        self.state = StreamState.INITIALIZED
        self.multichain_client = None
        self.processing_thread = None
        self.stop_event = threading.Event()
        self.error_count = 0
        self.last_processed_txid = None
        self.processed_items = []
        self.callbacks: List[Callable] = []
        
        # Enhanced metrics tracking
        self.metrics = {
            'total_processed': 0,
            'total_errors': 0,
            'start_time': None,
            'last_activity': None,
            'processing_times': [],
            'throughput_per_minute': 0.0
        }
        
        # Transaction tracking
        self.transaction = None
        
        log.info(f"StreamHandler initialized for stream: {stream}, txid: {txid}")
    
    def add_callback(self, callback: Callable) -> None:
        """Add a callback function to be called when data is processed."""
        self.callbacks.append(callback)
        log.debug(f"Added callback: {callback.__name__}")
    
    def start(self) -> bool:
        """
        Start the stream processing.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        try:
            log.info(f"Starting stream handler for {self.stream}")
            
            # Initialize multichain client
            self.multichain_client = get_multichain_client(
                self.config.chain_name, 
                self.config.user
            )
            
            if not self.multichain_client:
                log.error("Failed to initialize multichain client")
                self.state = StreamState.ERROR
                return False
            
            # Create transaction record
            self._create_transaction()
            
            # Subscribe to stream if not already subscribed
            self._ensure_stream_subscription()
            
            # Start processing thread
            self.processing_thread = threading.Thread(
                target=self._processing_loop,
                daemon=True
            )
            self.processing_thread.start()
            
            self.state = StreamState.RUNNING
            self.metrics['start_time'] = time.time()
            self.metrics['last_activity'] = time.time()
            log.info(f"Stream handler started successfully for {self.stream}")
            return True
            
        except Exception as e:
            log.error(f"Failed to start stream handler: {e}")
            self.state = StreamState.ERROR
            return False
    
    def stop(self) -> None:
        """Stop the stream processing."""
        log.info(f"Stopping stream handler for {self.stream}")
        self.stop_event.set()
        self.state = StreamState.STOPPED
        
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=5.0)
    
    def read_data(self) -> Optional[Dict[str, Any]]:
        """
        Read data from the stream.
        
        Returns:
            Optional[Dict[str, Any]]: Stream data if available, None otherwise
        """
        if self.state != StreamState.RUNNING:
            return None
        
        try:
            # Get latest processed item
            if self.processed_items:
                return self.processed_items.pop(0)
            
            return None
            
        except Exception as e:
            log.error(f"Error reading data: {e}")
            self.handle_error(e)
            return None
    
    def process_data(self, data: Dict[str, Any], *args, **kwargs) -> bool:
        """
        Process stream data with enhanced metrics tracking.
        
        Args:
            data: Data to process
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
            
        Returns:
            bool: True if processed successfully, False otherwise
        """
        process_start_time = time.time()
        
        try:
            log.debug(f"Processing data: {data}")
            
            # Update metrics
            self.metrics['last_activity'] = process_start_time
            
            # Update transaction
            self._update_transaction_progress(data)
            
            # Call registered callbacks
            for callback in self.callbacks:
                try:
                    callback(data, *args, **kwargs)
                except Exception as e:
                    log.error(f"Callback {callback.__name__} failed: {e}")
                    self.metrics['total_errors'] += 1
            
            # Update last processed txid
            if 'txid' in data:
                self.last_processed_txid = data['txid']
            
            # Update metrics
            process_time = time.time() - process_start_time
            self.metrics['processing_times'].append(process_time)
            self.metrics['total_processed'] += 1
            
            # Keep only last 100 processing times for average calculation
            if len(self.metrics['processing_times']) > 100:
                self.metrics['processing_times'] = self.metrics['processing_times'][-100:]
            
            # Calculate throughput
            self._update_throughput()
            
            log.debug(f"Data processed successfully in {process_time:.3f}s")
            return True
            
        except Exception as e:
            log.error(f"Error processing data: {e}")
            self.metrics['total_errors'] += 1
            self.handle_error(e)
            return False
    
    def _update_throughput(self) -> None:
        """Update throughput metrics."""
        if self.metrics['start_time']:
            elapsed_minutes = (time.time() - self.metrics['start_time']) / 60.0
            if elapsed_minutes > 0:
                self.metrics['throughput_per_minute'] = self.metrics['total_processed'] / elapsed_minutes
    
    def handle_error(self, error: Exception) -> None:
        """
        Handle errors during processing.
        
        Args:
            error: The error that occurred
        """
        self.error_count += 1
        log.error(f"Stream handler error #{self.error_count}: {error}")
        
        if self.error_count >= self.config.max_retries:
            log.error(f"Max retries ({self.config.max_retries}) exceeded, stopping handler")
            self.state = StreamState.ERROR
            self.stop()
        else:
            # Implement exponential backoff
            backoff_time = min(30.0, 2.0 ** self.error_count)
            log.info(f"Retrying in {backoff_time} seconds...")
            time.sleep(backoff_time)
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        log.info(f"Cleaning up stream handler for {self.stream}")
        
        self.stop()
        
        # Final transaction update
        if self.transaction:
            self._finalize_transaction()
        
        # Clear callbacks
        self.callbacks.clear()
        
        # Close multichain client connection if needed
        self.multichain_client = None
        
        log.info("Stream handler cleanup completed")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current handler status with enhanced metrics.
        
        Returns:
            Dict[str, Any]: Status information including metrics
        """
        avg_processing_time = 0.0
        if self.metrics['processing_times']:
            avg_processing_time = sum(self.metrics['processing_times']) / len(self.metrics['processing_times'])
        
        uptime = 0.0
        if self.metrics['start_time']:
            uptime = time.time() - self.metrics['start_time']
        
        return {
            "stream": self.stream,
            "txid": self.txid,
            "state": self.state.value,
            "error_count": self.error_count,
            "last_processed_txid": self.last_processed_txid,
            "processed_count": len(self.processed_items),
            "is_running": self.state == StreamState.RUNNING,
            "config": {
                "chain_name": self.config.chain_name,
                "user": self.config.user,
                "stream_name": self.config.stream_name,
                "poll_interval": self.config.poll_interval
            },
            "metrics": {
                "total_processed": self.metrics['total_processed'],
                "total_errors": self.metrics['total_errors'],
                "uptime_seconds": uptime,
                "throughput_per_minute": self.metrics['throughput_per_minute'],
                "avg_processing_time": avg_processing_time,
                "last_activity": self.metrics['last_activity']
            }
        }
    
    # Private methods
    
    def _create_transaction(self) -> None:
        """Create a transaction record for tracking."""
        try:
            self.transaction = Transaction(
                txid=self.txid,
                stream=self.stream
            )
            log.debug(f"Created transaction record: {self.transaction}")
        except Exception as e:
            log.warning(f"Failed to create transaction record: {e}")
    
    def _update_transaction_progress(self, data: Dict[str, Any]) -> None:
        """Update transaction with processing progress."""
        if self.transaction:
            # Update transaction with current processing info
            # This could be extended to store more detailed progress
            pass
    
    def _finalize_transaction(self) -> None:
        """Finalize the transaction record."""
        if self.transaction:
            log.debug(f"Finalizing transaction: {self.transaction}")
            # Here you could save the transaction to a database
            # or perform any final transaction-related operations
    
    def _ensure_stream_subscription(self) -> None:
        """Ensure the stream is subscribed using enhanced utilities."""
        try:
            with multichain_client_context(self.multichain_config) as client:
                # Use the enhanced ensure_stream_subscription function
                ensure_stream_subscription(client, self.config.stream_name)
                log.info(f"Ensured subscription to stream: {self.config.stream_name}")
        except Exception as e:
            log.error(f"Failed to ensure stream subscription: {e}")
            raise
    
    def _processing_loop(self) -> None:
        """Main processing loop running in a separate thread."""
        log.info(f"Starting processing loop for stream: {self.stream}")
        
        while not self.stop_event.is_set():
            try:
                # Get processed txids to skip
                skip_txids = [self.last_processed_txid] if self.last_processed_txid else []
                
                # Use enhanced multichain utilities directly
                items = list_stream_items(
                    config=self.multichain_config,
                    stream_name=self.config.stream_name,
                    count=self.config.batch_size,
                    verbose=True
                )
                
                # Filter out already processed items
                new_items = []
                for item in items:
                    if hasattr(item, 'txid') and item.txid not in skip_txids:
                        new_items.append(item.__dict__ if hasattr(item, '__dict__') else item)
                    elif isinstance(item, dict) and item.get('txid') not in skip_txids:
                        new_items.append(item)
                
                # Add items to processing queue
                for item in new_items:
                    self.processed_items.append(item)
                
                if new_items:
                    log.debug(f"Retrieved {len(new_items)} new items from stream")
                    # Update last processed txid
                    if new_items:
                        last_item = new_items[-1]
                        if hasattr(last_item, 'txid'):
                            self.last_processed_txid = last_item.txid
                        elif isinstance(last_item, dict) and 'txid' in last_item:
                            self.last_processed_txid = last_item['txid']
                
                # Reset error count on successful processing
                if new_items and self.error_count > 0:
                    self.error_count = 0
                
                # Wait before next poll
                self.stop_event.wait(self.config.poll_interval)
                
            except (MultichainConnectionError, StreamNotFoundError) as e:
                log.error(f"Multichain error in processing loop: {e}")
                self.handle_error(e)
                
                if self.state == StreamState.ERROR:
                    break
                    
            except Exception as e:
                log.error(f"Error in processing loop: {e}")
                self.handle_error(e)
                
                if self.state == StreamState.ERROR:
                    break
        
        log.info(f"Processing loop ended for stream: {self.stream}")


def create_enhanced_stream_handler(
    stream: str, 
    txid: str, 
    chain_name: str = "default",
    user: str = "multichain",
    poll_interval: float = 5.0
) -> StreamHandler:
    """
    Factory function to create an enhanced stream handler.
    
    Args:
        stream: Stream name
        txid: Transaction ID
        chain_name: Multichain name
        user: User for multichain connection
        poll_interval: Polling interval in seconds
    
    Returns:
        StreamHandler: Configured stream handler
    """
    config = StreamConfig(
        chain_name=chain_name,
        user=user,
        stream_name=stream,
        poll_interval=poll_interval
    )
    
    return StreamHandler(stream, txid, config)
