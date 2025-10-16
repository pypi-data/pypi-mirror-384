"""
Multichain Notification Service

This service handles sending tunnel configuration status updates to the controller
multichain server to notify about order processing status, tunnel states, etc.
"""

import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger as log

from vrouter_agent.utils.config import get_device_short_hostname
from vrouter_agent.services.chain import Chain
from vrouter_agent.models.tunnel_config import TunnelConfigData, TunnelState, ConfigDataState
from vrouter_agent.core.config import settings

class MultichainNotifier:
    """
    Service for sending tunnel configuration status updates to the multichain controller.
    
    This service publishes status updates to a dedicated "order_update" stream that the controller
    monitors for order processing status and tunnel state changes. Operational metrics and other
    data are published to a stream named after the hostname.
    """
    
    def __init__(self, chain_client: Optional[Chain] = None):
        """
        Initialize the multichain notifier.
        
        Args:
            chain_client: Optional Chain client. If not provided,
                         will be created from settings.
        """
        self.chain = chain_client or self._create_chain_from_settings()
        self.status_stream = get_device_short_hostname()  
        self.order_update_stream = "order_update"  # Dedicated stream for order status updates
        self.node_hostname = get_device_short_hostname()
        
    def _create_chain_from_settings(self) -> Chain:
        """Create chain client from application settings."""
        return Chain(
            chain=settings.config.multichain.chain,
            user=settings.config.global_.user
        )
    
    async def send_tunnel_status_update(
        self, 
        tunnel_config: TunnelConfigData, 
        action: str,
        interfaces: Optional[List[Dict[str, Any]]] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send a tunnel status update to the controller.
        
        Args:
            tunnel_config: Tunnel configuration data
            action: Action performed (provision, update, decommission)
            interfaces: List of interface data (for provision/update)
            additional_data: Any additional context data
            
        Returns:
            bool: True if notification was sent successfully
        """
        try:
            # Ensure order_update stream exists before publishing
            if not await self.ensure_order_update_stream_exists():
                log.error("Failed to ensure order_update stream exists")
                return False
            
            status_data = self._build_status_payload(
                tunnel_config, action, interfaces, additional_data
            )
            log.debug(f"Building status payload for action '{action}': {status_data}")
            
            # Use order_id as the key for easy tracking
            key = f"{tunnel_config.order_id}_{action}_{int(datetime.now().timestamp())}"
            
            # Publish to the dedicated order_update stream instead of status stream
            txid = await self._publish_async(self.order_update_stream, key, status_data)
            
            log.info(f"Sent tunnel status update for order {tunnel_config.order_id}, "
                    f"action: {action}, txid: {txid}")
            return True
            
        except Exception as e:
            log.error(f"Failed to send tunnel status update for order {tunnel_config.order_id}: {e}")
            return False
    
    async def send_tunnel_metrics(
        self, 
        tunnel_config: TunnelConfigData,
        metrics: Dict[str, Any]
    ) -> bool:
        """
        Send tunnel operational metrics to the controller.
        
        Args:
            tunnel_config: Tunnel configuration data
            metrics: Operational metrics data
            
        Returns:
            bool: True if metrics were sent successfully
        """
        try:
            metrics_data = {
                "type": "metrics",
                "timestamp": datetime.now().isoformat(),
                "node_hostname": self.node_hostname,
                "order_id": tunnel_config.order_id,
                "topology_id": tunnel_config.topology_id,
                "metrics": metrics
            }
            
            key = f"metrics_{tunnel_config.order_id}_{int(datetime.now().timestamp())}"
            txid = await self._publish_async(self.status_stream, key, metrics_data)
            
            log.debug(f"Sent tunnel metrics for order {tunnel_config.order_id}, txid: {txid}")
            return True
            
        except Exception as e:
            log.error(f"Failed to send tunnel metrics for order {tunnel_config.order_id}: {e}")
            return False
    
    async def send_error_notification(
        self, 
        tunnel_config: TunnelConfigData,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send error notification to the controller.
        
        Args:
            tunnel_config: Tunnel configuration data
            error_message: Error message
            error_details: Additional error context
            
        Returns:
            bool: True if error notification was sent successfully
        """
        try:
            # Ensure order_update stream exists before publishing
            if not await self.ensure_order_update_stream_exists():
                log.error("Failed to ensure order_update stream exists")
                return False
            
            error_data = {
                "type": "error",
                "timestamp": datetime.now().isoformat(),
                "node_hostname": self.node_hostname,
                "order_id": tunnel_config.order_id,
                "topology_id": tunnel_config.topology_id,
                "error_message": error_message,
                "error_details": error_details or {},
                "config_state": tunnel_config.state,
                "tunnel_states": [
                    {
                        "interface_name": t.get("interface_name"),
                        "state": t.get("state"),
                        "last_error": t.get("last_error")
                    }
                    for t in tunnel_config.tunnels_data
                ]
            }
            
            key = f"error_{tunnel_config.order_id}_{int(datetime.now().timestamp())}"
            txid = await self._publish_async(self.order_update_stream, key, error_data)
            
            log.info(f"Sent error notification for order {tunnel_config.order_id}, txid: {txid}")
            return True
            
        except Exception as e:
            log.error(f"Failed to send error notification for order {tunnel_config.order_id}: {e}")
            return False
    
    def _build_status_payload(
        self, 
        tunnel_config: TunnelConfigData,
        action: str,
        interfaces: Optional[List[Dict[str, Any]]] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build the status payload for multichain publishing."""
        
        # Count tunnel states
        tunnel_counts = {
            "total": len(tunnel_config.tunnels_data),
            "active": sum(1 for t in tunnel_config.tunnels_data if t.get("state") == TunnelState.ACTIVE),
            "pending": sum(1 for t in tunnel_config.tunnels_data if t.get("state") == TunnelState.PENDING),
            "inactive": sum(1 for t in tunnel_config.tunnels_data if t.get("state") == TunnelState.INACTIVE),
            "error": sum(1 for t in tunnel_config.tunnels_data if t.get("state") == TunnelState.ERROR)
        }
        
        # Build tunnel details
        tunnel_details = []
        for tunnel_data in tunnel_config.tunnels_data:
            tunnel_detail = {
                "tunnel_id": tunnel_data.get("tunnel_id"),
                "interface_name": tunnel_data.get("interface_name"),
                "state": tunnel_data.get("state"),
                "vpp_up": tunnel_data.get("vpp_up", False),
                "vpp_operational": tunnel_data.get("vpp_operational", False),
                "connectivity_test_passed": tunnel_data.get("vpp_connectivity_test_passed", False),
                "ip_address": tunnel_data.get("vpp_ip_address"),
                "last_verified": tunnel_data.get("vpp_last_verified_at")
            }
            
            # Add interface data if available
            if interfaces:
                matching_interface = next(
                    (iface for iface in interfaces if iface.get("name") == tunnel_data.get("interface_name")),
                    None
                )
                if matching_interface:
                    tunnel_detail.update({
                        "interface_index": matching_interface.get("interface_index"),
                        "interface_status": matching_interface.get("status")
                    })
            
            tunnel_details.append(tunnel_detail)
        
        # Build main status payload
        status_payload = {
            "type": "status_update",
            "timestamp": datetime.now().isoformat(),
            "node_hostname": self.node_hostname,
            "order_id": tunnel_config.order_id,
            "order_number": tunnel_config.order_number,
            "topology_id": tunnel_config.topology_id,
            "action": action,
            "config_state": tunnel_config.state,
            "config_version": tunnel_config.config_version,
            "processed_at": tunnel_config.processed_at.isoformat() if tunnel_config.processed_at else None,
            "applied_at": tunnel_config.applied_at.isoformat() if tunnel_config.applied_at else None,
            "error_message": tunnel_config.error_message,
            "tunnel_counts": tunnel_counts,
            "tunnel_details": tunnel_details,
            "frr_enabled": bool(tunnel_config.frr_config),
            "nat_enabled": bool(tunnel_config.nat_config) and tunnel_config.nat_config.get("enabled", False) if tunnel_config.nat_config else False,
            "acl_enabled": bool(tunnel_config.acl_config) and tunnel_config.acl_config.get("enabled", False) if tunnel_config.acl_config else False,
            "ospf_enabled": tunnel_config.ospf_enabled,
            "ebgp_enabled": tunnel_config.ebgp_enabled,
            "client_interfaces_count": len(tunnel_config.client_interfaces) if tunnel_config.client_interfaces else 0,
            "bgp_peers_count": len(tunnel_config.bgp_peers) if tunnel_config.bgp_peers else 0
        }
        
        # Add any additional data
        if additional_data:
            status_payload["additional_data"] = additional_data
            
        return status_payload
    
    async def _publish_async(self, stream_name: str, key: str, data: Dict[str, Any]) -> str:
        """
        Publish data to multichain stream asynchronously using the Chain client.
        
        Args:
            stream_name: Name of the stream
            key: Key for the data
            data: Data to publish
            
        Returns:
            str: Transaction ID
        """
        loop = asyncio.get_event_loop()
     
        
        # Run the publishing in a thread pool to avoid blocking
        return await loop.run_in_executor(
            None,
            self._publish_sync,
            stream_name,
            key,
            data
        )
    
    def _publish_sync(self, stream_name: str, key: str, data: Dict[str, Any]) -> str:
        """
        Synchronous publish method using Chain client.
        
        Args:
            stream_name: Name of the stream
            key: Key for the data
            data: Data to publish
            
        Returns:
            str: Transaction ID
        """
        try:
            if not self.chain.client:
                raise Exception("Multichain client not available")
            
            # Convert data to hex format
            data_str = json.dumps(data)
            data_hex = data_str.encode('utf-8').hex()
            # encrypted_data = self.chain.encrypt_data(data_hex)


            # Publish to stream using the Chain client
            txid = self.chain.client.publish(stream_name, key, data_hex)
            log.debug(f"Publishing to stream '{stream_name}' with key '{key}', data: {data_hex}")

            log.debug(f"Published to stream '{stream_name}' with key '{key}', txid: {txid}")
            return txid
            
        except Exception as e:
            log.error(f"Failed to publish to stream '{stream_name}': {e}")
            raise
    
    async def ensure_status_stream_exists(self) -> bool:
        """
        Ensure the status stream exists and is subscribed using Chain client.
        
        Returns:
            bool: True if stream is available
        """
        try:
            if not self.chain.client:
                log.error("Multichain client not available")
                return False
                
            # Check if stream exists and subscribe if needed
            try:
                # Check if we're subscribed to the stream
                if not self.chain.is_subscribe_to_stream(self.status_stream):
                    log.info(f"Subscribing to status stream: {self.status_stream}")
                    success = self.chain.subscribe_to_stream(self.status_stream)
                    if success:
                        log.info(f"Successfully subscribed to status stream: {self.status_stream}")
                    else:
                        log.warning(f"Failed to subscribe to status stream: {self.status_stream}")
                        return False
                else:
                    log.debug(f"Already subscribed to status stream: {self.status_stream}")
                
                return True
                    
            except Exception as e:
                log.error(f"Failed to setup status stream: {e}")
                return False
                
        except Exception as e:
            log.error(f"Failed to connect to multichain for stream setup: {e}")
            return False
    
    async def ensure_order_update_stream_exists(self) -> bool:
        """
        Ensure the order_update stream exists and is subscribed using Chain client.
        
        Returns:
            bool: True if stream is available
        """
        try:
            if not self.chain.client:
                log.error("Multichain client not available")
                return False
                
            # Check if stream exists and subscribe if needed
            try:
                # Check if we're subscribed to the order_update stream
                if not self.chain.is_subscribe_to_stream(self.order_update_stream):
                    log.info(f"Subscribing to order update stream: {self.order_update_stream}")
                    success = self.chain.subscribe_to_stream(self.order_update_stream)
                    if success:
                        log.info(f"Successfully subscribed to order update stream: {self.order_update_stream}")
                    else:
                        log.warning(f"Failed to subscribe to order update stream: {self.order_update_stream}")
                        return False
                else:
                    log.debug(f"Already subscribed to order update stream: {self.order_update_stream}")
                
                return True
                    
            except Exception as e:
                log.error(f"Failed to setup order update stream: {e}")
                return False
                
        except Exception as e:
            log.error(f"Failed to connect to multichain for order update stream setup: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test connection to multichain using Chain client.
        
        Returns:
            bool: True if connection is successful
        """
        try:
            if not self.chain.is_running():
                log.error("Multichain daemon is not running")
                return False
                
            if not self.chain.client:
                log.error("Multichain client not available")
                return False
                
            # Test with a simple getinfo call
            info = self.chain.client.getinfo()
            log.info(f"Multichain connection test successful. Chain: {info.get('chainname')}")
            return True
        except Exception as e:
            log.error(f"Multichain connection test failed: {e}")
            return False


# Global notifier instance
_notifier_instance: Optional[MultichainNotifier] = None

def get_multichain_notifier() -> MultichainNotifier:
    """Get or create a global multichain notifier instance."""
    global _notifier_instance
    if _notifier_instance is None:
        _notifier_instance = MultichainNotifier()
    return _notifier_instance

async def send_tunnel_status_notification(
    tunnel_config: TunnelConfigData,
    action: str,
    interfaces: Optional[List[Dict[str, Any]]] = None,
    additional_data: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Convenience function to send tunnel status notification.
    
    Args:
        tunnel_config: Tunnel configuration data
        action: Action performed
        interfaces: Interface data
        additional_data: Additional context
        
    Returns:
        bool: True if notification sent successfully
    """
    notifier = get_multichain_notifier()
    return await notifier.send_tunnel_status_update(
        tunnel_config, action, interfaces, additional_data
    )
