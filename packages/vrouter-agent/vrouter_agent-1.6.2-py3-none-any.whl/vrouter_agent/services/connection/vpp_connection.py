"""
VPP Connection Management Module

This module provides a clean interface for managing VPP API client connections,
replacing the connection logic scattered throughout the original VRouterClient class.
"""

from typing import Optional
from vpp_vrouter.client import ExtendedVPPAPIClient
from loguru import logger as log
import threading
import time


class VPPConnectionManager:
    """
    Manages VPP API client connections with automatic reconnection and health monitoring.
    
    This class encapsulates all VPP connection logic, providing a clean interface
    for other components to use VPP API functionality.
    """
    
    def __init__(self, auto_reconnect: bool = True, health_check_interval: float = 30.0):
        """
        Initialize the VPP connection manager.
        
        Args:
            auto_reconnect: Whether to automatically attempt reconnection on failure
            health_check_interval: Interval in seconds for health checks
        """
        self._client: Optional[ExtendedVPPAPIClient] = None
        self._connected = False
        self._connection_lock = threading.Lock()
        self._auto_reconnect = auto_reconnect
        self._health_check_interval = health_check_interval
        self._health_check_thread: Optional[threading.Thread] = None
        self._shutdown_requested = False
    
    @property
    def client(self) -> ExtendedVPPAPIClient:
        """
        Get the VPP API client, connecting if necessary.
        
        Returns:
            ExtendedVPPAPIClient: The VPP API client instance
            
        Raises:
            ConnectionError: If connection cannot be established
        """
        with self._connection_lock:
            if not self._connected:
                if not self.connect():
                    raise ConnectionError("Failed to establish VPP connection")
            return self._client
    
    
    def connect(self) -> bool:
        """
        Establish connection to VPP.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            with self._connection_lock:
                log.debug("Attempting to connect to VPP...")
                
                # Create VPP client
                client = ExtendedVPPAPIClient()
                
                # Test the connection by getting configuration
                client.get_configuration()
                
                self._client = client
                self._connected = True
                log.debug("Successfully connected to VPP")
                
                # Start health monitoring if auto-reconnect is enabled
                if self._auto_reconnect and not self._health_check_thread:
                    self._start_health_monitoring()
                
                return True
                
        except Exception as e:
            log.error(f"Failed to connect to VPP: {e}")
            self._connected = False
            self._client = None
            return False
    
    def is_connected(self) -> bool:
        """
        Check if client is connected to VPP.
        
        Returns:
            bool: True if connected and healthy, False otherwise
        """
        if not self._connected or not self._client:
            return False
        
        try:
            # Perform a lightweight operation to test connectivity
            self._client.get_configuration()
            return True
        except Exception as e:
            log.warning(f"Connection health check failed: {e}")
            with self._connection_lock:
                self._connected = False
            return False
    
    def disconnect(self):
        """Close VPP connection and cleanup resources."""
        log.debug("Disconnecting from VPP...")
        
        # Stop health monitoring
        self._shutdown_requested = True
        if self._health_check_thread and self._health_check_thread.is_alive():
            self._health_check_thread.join(timeout=5.0)
        
        with self._connection_lock:
            self._connected = False
            if self._client:
                # VPP client doesn't have an explicit close method
                # Just clear the reference
                self._client = None
        
        log.debug("Disconnected from VPP")
    
    def ensure_connected(self) -> bool:
        """
        Ensure VPP connection is active, reconnecting if necessary.
        
        Returns:
            bool: True if connection is active, False otherwise
        """
        if self.is_connected():
            return True
        
        if self._auto_reconnect:
            log.debug("Connection lost, attempting to reconnect...")
            return self.connect()
        
        return False
    
    def _start_health_monitoring(self):
        """Start background health monitoring thread."""
        if self._health_check_thread and self._health_check_thread.is_alive():
            return
        
        self._shutdown_requested = False
        self._health_check_thread = threading.Thread(
            target=self._health_monitor_loop,
            daemon=True,
            name="VPP-HealthMonitor"
        )
        self._health_check_thread.start()
        log.debug("Started VPP health monitoring thread")
    
    def _health_monitor_loop(self):
        """Background health monitoring loop."""
        while not self._shutdown_requested:
            try:
                time.sleep(self._health_check_interval)
                
                if self._shutdown_requested:
                    break
                
                if not self.is_connected() and self._auto_reconnect:
                    log.warning("Health check failed, attempting reconnection...")
                    self.connect()
                    
            except Exception as e:
                log.error(f"Error in health monitoring loop: {e}")
    
    def get_connection_stats(self) -> dict:
        """
        Get connection statistics and status.
        
        Returns:
            dict: Connection statistics
        """
        return {
            'connected': self._connected,
            'auto_reconnect': self._auto_reconnect,
            'health_check_interval': self._health_check_interval,
            'health_monitor_active': (
                self._health_check_thread is not None and 
                self._health_check_thread.is_alive()
            ),
            'client_available': self._client is not None
        }
    
    def __enter__(self):
        """Context manager entry."""
        if not self.connect():
            raise ConnectionError("Failed to establish VPP connection")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
