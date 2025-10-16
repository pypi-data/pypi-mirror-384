"""
VRouter Agent Startup Service

This module handles the startup initialization of services including
the stream listener for automatic transaction monitoring.
"""

import asyncio
from typing import Optional
from loguru import logger as log

from vrouter_agent.services.stream_listener import (
    start_stream_listener, 
    StreamListenerConfig
)
from vrouter_agent.enhanced_stream_processor import get_stream_processor
from vrouter_agent.utils.config import get_device_short_hostname
from vrouter_agent.core.config import settings
from vrouter_agent.services.chain import Chain


class StartupService:
    """Service responsible for initializing application components on startup."""
    
    def __init__(self):
        self.hostname = get_device_short_hostname()
        self.initialized = False
    
    async def initialize(self) -> bool:
        """
        Initialize all application services.
        
        Returns:
            bool: True if initialization was successful
        """
        if self.initialized:
            log.warning("Startup service already initialized")
            return True
        
        try:
            log.info("Initializing VRouter Agent services...")
            
            # Initialize enhanced stream processor
            log.info("Starting enhanced stream processor...")
            processor = await get_stream_processor()
            if not processor:
                log.error("Failed to initialize enhanced stream processor")
                return False
            log.info("Enhanced stream processor started successfully")
            
            # Subscribe to multichain streams during startup
            log.info("Subscribing to multichain streams...")
            success = await self._subscribe_to_streams()
            if not success:
                log.error("Failed to subscribe to required streams")
                return False
            
            # Initialize and start stream listener
            log.info(f"Starting stream listener for hostname stream: {self.hostname}")
            
            # Configure stream listener for the hostname-based stream
            listener_config = StreamListenerConfig(
                stream_name=self.hostname,
                poll_interval=getattr(settings.config, 'stream_listener_poll_interval', 5.0),
                batch_size=getattr(settings.config, 'stream_listener_batch_size', 50),
                max_retries=getattr(settings.config, 'stream_listener_max_retries', 3),
                startup_delay=getattr(settings.config, 'stream_listener_startup_delay', 10.0)
            )
            
            success = await start_stream_listener(listener_config)
            if not success:
                log.error("Failed to start stream listener")
                return False
            
            log.info(f"Stream listener started successfully for stream: {self.hostname}")
            
            self.initialized = True
            log.info("VRouter Agent services initialized successfully")
            return True
            
        except Exception as e:
            log.error(f"Failed to initialize VRouter Agent services: {e}")
            return False
    
    async def _subscribe_to_streams(self) -> bool:
        """
        Subscribe to required multichain streams.
        
        Returns:
            bool: True if subscription was successful
        """
        try:
            # Initialize Chain client
            chain = Chain(
                chain=settings.config.multichain.chain, 
                user=settings.config.global_.user
            )
            
            # Check if multichain daemon is running
            if not chain.is_running():
                log.error(f"Multichain daemon for chain {settings.config.multichain.chain} is not running")
                return False
            
            streams_to_subscribe = [self.hostname, "order_update"]
            
            for stream_name in streams_to_subscribe:
                log.info(f"Subscribing to stream: {stream_name}")
                
                # Check if we're already subscribed
                if not chain.is_subscribe_to_stream(stream_name):
                    success = chain.subscribe_to_stream(stream_name)
                    if success:
                        log.info(f"Successfully subscribed to stream: {stream_name}")
                    else:
                        log.error(f"Failed to subscribe to stream: {stream_name}")
                        return False
                else:
                    log.info(f"Already subscribed to stream: {stream_name}")
            
            log.info("Successfully subscribed to all required streams")
            return True
            
        except Exception as e:
            log.error(f"Error subscribing to streams: {e}")
            return False
    
    async def shutdown(self) -> None:
        """Shutdown all application services gracefully."""
        if not self.initialized:
            log.warning("Services were not initialized, nothing to shutdown")
            return
        
        try:
            log.info("Shutting down VRouter Agent services...")
            
            # Stop stream listener
            from vrouter_agent.services.stream_listener import stop_stream_listener
            await stop_stream_listener()
            log.info("Stream listener stopped")
            
            # Stop enhanced stream processor
            processor = await get_stream_processor()
            await processor.stop()
            log.info("Enhanced stream processor stopped")
            
            self.initialized = False
            log.info("VRouter Agent services shutdown completed")
            
        except Exception as e:
            log.error(f"Error during shutdown: {e}")


# Global startup service instance
_startup_service: Optional[StartupService] = None


def get_startup_service() -> StartupService:
    """Get the global startup service instance."""
    global _startup_service
    
    if _startup_service is None:
        _startup_service = StartupService()
    
    return _startup_service


async def initialize_services() -> bool:
    """Initialize all application services."""
    startup_service = get_startup_service()
    return await startup_service.initialize()


async def shutdown_services() -> None:
    """Shutdown all application services."""
    startup_service = get_startup_service()
    await startup_service.shutdown()