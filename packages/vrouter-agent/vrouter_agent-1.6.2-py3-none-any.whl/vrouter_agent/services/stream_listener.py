"""
Stream Listener Service for VRouter Agent

This service implements a continuous stream listener that monitors a designated
multichain stream (based on hostname) for new transactions instead of relying
on POST endpoint data. It provides real-time processing of stream items as
they appear on the blockchain.
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
from loguru import logger as log
from sqlmodel import Session

from vrouter_agent.services.chain import Chain, StreamItem
from vrouter_agent.core.config import settings
from vrouter_agent.utils.config import get_device_short_hostname
from vrouter_agent.enhanced_stream_processor import get_stream_processor
from vrouter_agent.models import Transaction
from vrouter_agent.core.db import get_session, engine
from sqlmodel import Session, select


@dataclass
class StreamListenerConfig:
    """Configuration for the stream listener."""
    stream_name: str
    poll_interval: float = 5.0  # seconds between polls
    batch_size: int = 50  # maximum items to fetch per poll
    max_retries: int = 3
    retry_delay: float = 2.0
    startup_delay: float = 10.0  # delay before first poll


class StreamListener:
    """
    Continuous stream listener that monitors a designated multichain stream
    for new transactions and processes them through the enhanced stream processor.
    """
    
    def __init__(self, config: Optional[StreamListenerConfig] = None):
        """
        Initialize the stream listener.
        
        Args:
            config: Optional stream listener configuration
        """
        self.hostname = get_device_short_hostname()
        self.config = config or StreamListenerConfig(stream_name=self.hostname)
        
        # Initialize chain client
        self.chain = Chain(
            chain=settings.config.multichain.chain,
            user=settings.config.global_.user
        )
        
        # State management
        self.is_running = False
        self.listener_task: Optional[asyncio.Task] = None
        self.processed_txids: Set[str] = set()
        self.last_poll_time: Optional[datetime] = None
        self.consecutive_errors = 0
        
        # Load previously processed transactions from database on startup
        self._load_processed_transactions()
        
        # Metrics
        self.metrics = {
            'total_items_processed': 0,
            'successful_items': 0,
            'failed_items': 0,
            'polls_completed': 0,
            'last_poll_duration': 0.0,
            'start_time': None,
            'last_activity': None,
            'consecutive_errors': 0
        }
        
        log.info(f"Stream listener initialized for stream: {self.config.stream_name}")
    
    def _load_processed_transactions(self) -> None:
        """
        Load previously processed transaction IDs from the database to avoid reprocessing.
        This ensures continuity across service restarts.
        """
        try:
            with Session(engine) as session:
                # Get recent transactions from the database (last 5000 to avoid memory issues)
                statement = select(Transaction.txid).where(
                    Transaction.stream == self.config.stream_name
                ).order_by(Transaction.timestamp.desc()).limit(5000)
                
                result = session.exec(statement)
                loaded_txids = set(result.all())
                
                self.processed_txids.update(loaded_txids)
                log.info(f"Loaded {len(loaded_txids)} previously processed transaction IDs from database")
                
        except Exception as e:
            log.warning(f"Failed to load processed transactions from database: {e}")
            # Continue with empty set - not a critical failure
    
    async def start(self) -> bool:
        """
        Start the stream listener.
        
        Returns:
            bool: True if started successfully
        """
        if self.is_running:
            log.warning("Stream listener is already running")
            return False
        
        try:
            log.info(f"Starting stream listener for stream: {self.config.stream_name}")
            
            # Validate chain connection
            if not self.chain.is_running():
                log.error("Multichain daemon is not running")
                return False
            
            if not self.chain.client:
                log.error("Failed to create multichain client")
                return False
            
            # Ensure we're subscribed to the stream
            if not await self._ensure_stream_subscription():
                log.error(f"Failed to subscribe to stream: {self.config.stream_name}")
                return False
            
            # Start the listener task
            self.is_running = True
            self.metrics['start_time'] = time.time()
            self.listener_task = asyncio.create_task(self._listener_loop())
            
            log.info(f"Stream listener started successfully for stream: {self.config.stream_name}")
            return True
            
        except Exception as e:
            log.error(f"Failed to start stream listener: {e}")
            self.is_running = False
            return False
    
    async def stop(self) -> None:
        """Stop the stream listener."""
        if not self.is_running:
            log.warning("Stream listener is not running")
            return
        
        log.info("Stopping stream listener...")
        self.is_running = False
        
        if self.listener_task:
            self.listener_task.cancel()
            try:
                await self.listener_task
            except asyncio.CancelledError:
                pass
        
        log.info("Stream listener stopped")
    
    async def _ensure_stream_subscription(self) -> bool:
        """
        Ensure we're subscribed to the target stream.
        
        Returns:
            bool: True if subscription is successful
        """
        try:
            if not self.chain.is_subscribe_to_stream(self.config.stream_name):
                log.info(f"Subscribing to stream: {self.config.stream_name}")
                success = self.chain.subscribe_to_stream(self.config.stream_name)
                if not success:
                    log.error(f"Failed to subscribe to stream: {self.config.stream_name}")
                    return False
            else:
                log.debug(f"Already subscribed to stream: {self.config.stream_name}")
            
            return True
            
        except Exception as e:
            log.error(f"Error checking stream subscription: {e}")
            return False
    
    async def _listener_loop(self) -> None:
        """Main listener loop that continuously polls the stream for new items."""
        log.debug("Stream listener loop started")
        
        # Initial startup delay to allow system initialization
        await asyncio.sleep(self.config.startup_delay)
        
        while self.is_running:
            try:
                poll_start_time = time.time()
                
                # Poll for new stream items
                new_items = await self._poll_stream()
                
                # Process new items
                if new_items:
                    await self._process_stream_items(new_items)
                    self.metrics['last_activity'] = time.time()
                
                # Update metrics
                poll_duration = time.time() - poll_start_time
                self.metrics['polls_completed'] += 1
                self.metrics['last_poll_duration'] = poll_duration
                self.consecutive_errors = 0
                self.metrics['consecutive_errors'] = 0
                
                self.last_poll_time = datetime.now()
                
                log.debug(f"Poll completed in {poll_duration:.2f}s, found {len(new_items)} new items")
                
                # Wait before next poll
                await asyncio.sleep(self.config.poll_interval)
                
            except asyncio.CancelledError:
                log.info("Stream listener loop cancelled")
                break
            except Exception as e:
                self.consecutive_errors += 1
                self.metrics['consecutive_errors'] = self.consecutive_errors
                
                log.error(f"Error in stream listener loop: {e}")
                
                # Exponential backoff on consecutive errors
                if self.consecutive_errors >= self.config.max_retries:
                    log.error(f"Too many consecutive errors ({self.consecutive_errors}), stopping listener")
                    self.is_running = False
                    break
                
                backoff_delay = min(30.0, self.config.retry_delay * (2 ** self.consecutive_errors))
                await asyncio.sleep(backoff_delay)
        
        log.info("Stream listener loop stopped")
    
    async def _poll_stream(self) -> List[Dict[str, Any]]:
        """
        Poll the stream for new items.
        
        Returns:
            List[Dict[str, Any]]: List of new stream items
        """
        try:
            # Get recent stream items
            raw_items = self.chain.client.liststreamitems(
                self.config.stream_name,
                verbose=True,
                count=self.config.batch_size,
                start=-self.config.batch_size  # Get latest items
            )
            
            # Filter out already processed items using in-memory cache first
            new_items = []
            for item in raw_items:
                txid = item.get('txid')
                if txid and txid not in self.processed_txids:
                    new_items.append(item)
            
            # Manage memory usage of processed_txids set
            self._cleanup_processed_txids()
            
            log.debug(f"Polled {len(raw_items)} items, {len(new_items)} are new")
            return new_items
            
        except Exception as e:
            log.error(f"Error polling stream {self.config.stream_name}: {e}")
            raise
    
    def _cleanup_processed_txids(self) -> None:
        """
        Clean up the processed_txids set to prevent excessive memory usage.
        Keeps only the most recent transactions in memory.
        """
        if len(self.processed_txids) > 10000:
            # Convert to list, sort (though txids aren't naturally sortable by time),
            # and keep the most recent 5000. This is a rough cleanup.
            # In practice, we rely more on database checking for accuracy.
            recent_txids = set(list(self.processed_txids)[-5000:])
            removed_count = len(self.processed_txids) - len(recent_txids)
            self.processed_txids = recent_txids
            log.debug(f"Cleaned up {removed_count} old transaction IDs from memory cache")
    
    async def _process_stream_items(self, items: List[Dict[str, Any]]) -> None:
        """
        Process new stream items through the enhanced stream processor.
        
        Args:
            items: List of stream items to process
        """
        log.info(f"Processing {len(items)} new stream items")
        
        processor = await get_stream_processor()
        
        for item in items:
            try:
                txid = item.get('txid')
                if not txid:
                    log.warning("Stream item missing txid, skipping")
                    continue
                
                # Double-check if transaction was processed (could have been added by another process)
                if txid in self.processed_txids:
                    log.debug(f"Transaction {txid} already in memory cache, skipping")
                    continue
                
                # Create a Transaction record for consistency with existing system
                try:
                    # Create session directly from engine
                    with Session(engine) as session:
                        # Check if transaction already exists in database
                        statement = select(Transaction).where(Transaction.txid == txid)
                        existing_transaction = session.exec(statement).first()
                        
                        if existing_transaction:
                            log.debug(f"Transaction {txid} already exists in database, skipping")
                            # Add to memory cache to avoid future database queries
                            self.processed_txids.add(txid)
                            continue
                        
                        # Create new transaction record
                        new_transaction = Transaction(
                            txid=txid,
                            stream=self.config.stream_name
                        )
                        session.add(new_transaction)
                        session.commit()
                        session.refresh(new_transaction)  # Ensure we have the ID
                        
                        # Add to processed cache immediately after database insert
                        self.processed_txids.add(txid)
                        
                        # Process through enhanced stream processor
                        success = await processor.process_transaction(
                            new_transaction,
                            self.config.stream_name,
                            session
                        )
                        
                        if success:
                            self.metrics['successful_items'] += 1
                            log.debug(f"Successfully processed stream item {txid}")
                        else:
                            self.metrics['failed_items'] += 1
                            log.error(f"Failed to process stream item {txid}")
                            # Even if processing failed, keep it in cache to avoid reprocessing
                
                except Exception as session_error:
                    log.error(f"Database session error for txid {txid}: {session_error}")
                    self.metrics['failed_items'] += 1
                    # Don't add to processed cache if database operation failed
                
                self.metrics['total_items_processed'] += 1
                
            except Exception as e:
                self.metrics['failed_items'] += 1
                log.error(f"Error processing stream item {item.get('txid', 'unknown')}: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the stream listener."""
        uptime = (time.time() - self.metrics['start_time']) if self.metrics['start_time'] else 0
        
        return {
            'running': self.is_running,
            'stream_name': self.config.stream_name,
            'hostname': self.hostname,
            'uptime_seconds': uptime,
            'last_poll_time': self.last_poll_time.isoformat() if self.last_poll_time else None,
            'consecutive_errors': self.consecutive_errors,
            'processed_txids_count': len(self.processed_txids),
            'memory_cache_size': len(self.processed_txids)
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get detailed metrics for the stream listener."""
        return self.metrics.copy()
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive processing statistics including database information.
        
        Returns:
            Dict containing processing statistics
        """
        try:
            with Session(engine) as session:
                # Count total transactions in database for this stream
                total_db_count = session.exec(
                    select(Transaction).where(Transaction.stream == self.config.stream_name)
                ).all()
                
                return {
                    'stream_name': self.config.stream_name,
                    'memory_cache_size': len(self.processed_txids),
                    'database_total_transactions': len(total_db_count),
                    'metrics': self.get_metrics(),
                    'status': self.get_status()
                }
        except Exception as e:
            log.error(f"Error getting processing stats: {e}")
            return {
                'stream_name': self.config.stream_name,
                'memory_cache_size': len(self.processed_txids),
                'database_total_transactions': 'error',
                'error': str(e),
                'metrics': self.get_metrics(),
                'status': self.get_status()
            }
    
    def mark_transaction_processed(self, txid: str) -> None:
        """
        Manually mark a transaction as processed.
        
        Args:
            txid: Transaction ID to mark as processed
        """
        self.processed_txids.add(txid)
        log.debug(f"Manually marked transaction {txid} as processed")
    
    def is_transaction_processed(self, txid: str) -> bool:
        """
        Check if a transaction has been processed.
        
        Args:
            txid: Transaction ID to check
            
        Returns:
            bool: True if transaction has been processed
        """
        # Check memory cache first (fast)
        if txid in self.processed_txids:
            return True
        
        # Check database (slower but authoritative)
        try:
            with Session(engine) as session:
                statement = select(Transaction).where(
                    Transaction.txid == txid,
                    Transaction.stream == self.config.stream_name
                )
                existing = session.exec(statement).first()
                
                if existing:
                    # Add to memory cache for future fast lookups
                    self.processed_txids.add(txid)
                    return True
                    
                return False
        except Exception as e:
            log.error(f"Error checking if transaction {txid} is processed: {e}")
            # Return False to allow reprocessing rather than assuming it's processed
            return False
    
    def clear_processed_cache(self) -> None:
        """
        Clear the in-memory processed transactions cache.
        This will force the system to reload from database on next startup.
        """
        old_size = len(self.processed_txids)
        self.processed_txids.clear()
        log.info(f"Cleared processed transactions cache ({old_size} items)")
    
    def reload_processed_transactions(self) -> None:
        """
        Reload processed transactions from database.
        Useful for synchronizing with external changes to the database.
        """
        self.processed_txids.clear()
        self._load_processed_transactions()
        log.info("Reloaded processed transactions from database")


# Global stream listener instance
_listener_instance: Optional[StreamListener] = None


async def get_stream_listener(config: Optional[StreamListenerConfig] = None) -> StreamListener:
    """
    Get the global stream listener singleton instance.
    
    Args:
        config: Optional configuration for the listener
        
    Returns:
        StreamListener: The singleton listener instance
    """
    global _listener_instance
    
    if _listener_instance is None:
        _listener_instance = StreamListener(config)
    
    return _listener_instance


async def start_stream_listener(config: Optional[StreamListenerConfig] = None) -> bool:
    """
    Start the global stream listener.
    
    Args:
        config: Optional configuration for the listener
        
    Returns:
        bool: True if started successfully
    """
    listener = await get_stream_listener(config)
    return await listener.start()


async def stop_stream_listener() -> None:
    """Stop the global stream listener."""
    global _listener_instance
    
    if _listener_instance:
        await _listener_instance.stop()
