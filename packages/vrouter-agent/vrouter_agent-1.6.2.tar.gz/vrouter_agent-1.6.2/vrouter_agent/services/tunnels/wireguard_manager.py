"""
WireGuard Tunnel Manager

This module provides a specialized manager for WireGuard tunnel operations,
implementing the TunnelManager interface with WireGuard-specific functionality.
"""

from typing import List, Dict, Any, Optional
from itertools import chain
import ipaddress
import re

from loguru import logger as log
from vpp_vrouter.common import models

from ..base_interfaces import TunnelManager, ComponentStatus, create_result_dict, validate_component_config
from ..connection.vpp_connection import VPPConnectionManager
from ...models import Tunnel
from ...core.base import CreatedWireguardTunnel
from ...schemas.tunnel_config import WireGuardConfig


class WireGuardTunnelManager(TunnelManager):
    """
    Manages WireGuard tunnel operations through VPP API.
    
    This class handles the complete lifecycle of WireGuard tunnels including
    creation, configuration, monitoring, and removal.
    """
    
    def __init__(self, connection_manager: VPPConnectionManager):
        """
        Initialize the WireGuard tunnel manager.
        
        Args:
            connection_manager: VPP connection manager instance
        """
        self.connection = connection_manager
        self.created_tunnels: List[CreatedWireguardTunnel] = []
        self._tunnel_configs: List[WireGuardConfig] = []
    
    def _extract_reply_errors(self, reply) -> List[str]:
        """Extract all error messages from a VPP reply object."""
        errors = []
        
        # Check processing_error (legacy field)
        if hasattr(reply, 'processing_error') and reply.processing_error:
            errors.append(reply.processing_error)
        
        # Check added_items for errors
        if hasattr(reply, 'added_items'):
            for item in reply.added_items:
                if hasattr(item, 'error') and item.error:
                    errors.append(f"Added item error: {item.error}")
                if hasattr(item, 'state') and 'FAILURE' in str(item.state):
                    errors.append(f"Item state failure: {item.state}")
        
        # Check vpp_apply_attempted_items for detailed errors
        if hasattr(reply, 'vpp_apply_attempted_items'):
            for item in reply.vpp_apply_attempted_items:
                if hasattr(item, 'error') and item.error:
                    errors.append(f"VPP apply error: {item.error}")
                if hasattr(item, 'state') and 'FAILURE' in str(item.state):
                    errors.append(f"VPP apply state failure: {item.state}")
        
        # Check vpp_apply_success flag
        if hasattr(reply, 'vpp_apply_success') and reply.vpp_apply_success is False:
            if not errors:  # Only add generic message if no specific errors found
                errors.append("VPP apply failed without specific error message")
        
        return errors

    def create_tunnels(self, configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create WireGuard tunnels from configuration list.
        
        Args:
            configs: List of WireGuard tunnel configurations
            
        Returns:
            dict: Result with success status, created tunnels, and interface data
        """
        try:
            log.info(f"Creating {len(configs)} WireGuard tunnels")
            
            # Sort configurations by interface name to ensure consistent processing order
            sorted_configs = self._sort_configs_by_interface_name(configs)
            log.info(f"Processing WireGuard configs in sorted order: {[cfg.get('interface_name', cfg.get('name', 'unknown')) for cfg in sorted_configs]}")
            
            # Validate configurations
            # validation_result = self._validate_tunnel_configs(sorted_configs)
            # if not validation_result['valid']:
            #     return create_result_dict(
            #         success=False, 
            #         error=f"Configuration validation failed: {validation_result['errors']}"
            #     )
            
            # Convert to WireGuardConfig objects and sort them
            self._tunnel_configs = [self._dict_to_wireguard_config(config) for config in sorted_configs]
            self._tunnel_configs = self._sort_wireguard_configs(self._tunnel_configs)
            
            # Prepare VPP configurations
            interfaces, peers, routes = self._prepare_vpp_configurations()
        
            # Apply configurations to VPP
            result = self._apply_vpp_configurations(interfaces, peers, routes)
            
            if result['success']:
                # Track created tunnels (ensure they are sorted)
                self.created_tunnels = self._sort_tunnels_by_name(result['data']['created_tunnels'])
                
                # Generate interface data for external systems (e.g., Django)
                interface_data = self._generate_interface_data()
                
                log.info(f"Successfully created {len(self.created_tunnels)} WireGuard tunnels in order: {[t.name for t in self.created_tunnels]}")
                
                return create_result_dict(
                    success=True,
                    data={
                        'tunnels': [t.name for t in self.created_tunnels],
                        'interfaces': interface_data,
                        'created_count': len(self.created_tunnels)
                    }
                )
            else:
                return create_result_dict(success=False, error=result.get('error'))
                
        except Exception as e:
            log.error(f"Failed to create WireGuard tunnels: {e}")
            return create_result_dict(success=False, error=str(e))
    
    def remove_tunnels(self, tunnel_names: Optional[List[str]] = None) -> bool:
        """
        Remove WireGuard tunnels.
        
        Args:
            tunnel_names: Optional list of specific tunnel names to remove.
                         If None, removes all managed tunnels.
                         
        Returns:
            bool: True if all removals successful, False otherwise
        """
        if not self.created_tunnels:
            log.info("No WireGuard tunnels to remove")
            return True
        
        tunnels_to_remove = self.created_tunnels
        if tunnel_names:
            tunnels_to_remove = [t for t in self.created_tunnels if t.name in tunnel_names]
            if not tunnels_to_remove:
                log.warning(f"No tunnels found matching names: {tunnel_names}")
                return True
        
        # Sort tunnels in reverse order for removal (remove higher numbered tunnels first)
        # This helps avoid potential dependency issues
        sorted_tunnels_to_remove = self._sort_tunnels_by_name(tunnels_to_remove)
        sorted_tunnels_to_remove.reverse()
        
        try:
            log.info(f"Removing {len(sorted_tunnels_to_remove)} WireGuard tunnels in reverse order: {[t.name for t in sorted_tunnels_to_remove]}")
            
            # Find configurations to remove from VPP
            configs_to_remove = self._find_configurations_to_remove(sorted_tunnels_to_remove)
            
            if not configs_to_remove:
                log.warning("No VPP configurations found to remove")
                self._cleanup_tunnel_tracking(tunnel_names)
                return True
            
            # Remove from VPP
            reply = self.connection.client.delete_configuration(*configs_to_remove)
            
            errors = self._extract_reply_errors(reply)
            if errors:
                log.error(f"Error removing tunnels from VPP: {'; '.join(errors)}")
                return False
            
            # Update tracking
            self._cleanup_tunnel_tracking(tunnel_names)
            
            log.info("WireGuard tunnels removed successfully")
            return True
            
        except Exception as e:
            log.error(f"Exception removing WireGuard tunnels: {e}")
            return False
    
    def verify_tunnels(self, tunnel_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Verify operational status of WireGuard tunnels.
        
        Args:
            tunnel_names: Optional list of tunnel names to verify
            
        Returns:
            List[dict]: List of tunnel verification results
        """
        results = []
        
        tunnels_to_verify = self.created_tunnels
        if tunnel_names:
            tunnels_to_verify = [t for t in self.created_tunnels if t.name in tunnel_names]
        
        if not tunnels_to_verify:
            log.warning("No tunnels to verify")
            return results
        
        # Sort tunnels to ensure consistent verification order
        sorted_tunnels_to_verify = self._sort_tunnels_by_name(tunnels_to_verify)
        
        log.info(f"Verifying {len(sorted_tunnels_to_verify)} WireGuard tunnels in order: {[t.name for t in sorted_tunnels_to_verify]}")
        
        for tunnel in sorted_tunnels_to_verify:
            try:
                verification_result = self._verify_single_tunnel(tunnel)
                results.append(verification_result)
                
            except Exception as e:
                log.error(f"Error verifying tunnel {tunnel.name}: {e}")
                results.append({
                    'tunnel_name': tunnel.name,
                    'status': ComponentStatus.ERROR.value,
                    'interface_up': False,
                    'connectivity': False,
                    'error': str(e)
                })
        
        return results
    
    def get_tunnel_info(self, tunnel_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific tunnel.
        
        Args:
            tunnel_name: Name of the tunnel
            
        Returns:
            Optional[dict]: Tunnel information or None if not found
        """
        # Find the tunnel in our tracking
        tunnel = next((t for t in self.created_tunnels if t.name == tunnel_name), None)
        if not tunnel:
            return None
        
        try:
            # Get VPP configuration
            vpp_config = self._get_tunnel_vpp_config(tunnel_name)
            
            # Get tunnel configuration
            tunnel_config = self._find_tunnel_config_by_name(tunnel_name)
            
            info = {
                'name': tunnel.name,
                'ip_address': tunnel.ip_address,
                'peer_ip_address': getattr(tunnel, 'peer_ip_address', None),
                'mapped_name': getattr(tunnel, 'mapped_name', None),
                'vpp_config': vpp_config,
                'original_config': tunnel_config.__dict__ if tunnel_config else None,
                'status': self._get_tunnel_status(tunnel_name)
            }
            
            return info
            
        except Exception as e:
            log.error(f"Error getting tunnel info for {tunnel_name}: {e}")
            return None
    
    # Implementation of NetworkComponent abstract methods
    
    def create(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a single tunnel from configuration."""
        return self.create_tunnels([config])
    
    def delete(self, identifier: str) -> bool:
        """Delete a tunnel by name."""
        return self.remove_tunnels([identifier])
    
    def get_status(self, identifier: str) -> Dict[str, Any]:
        """Get status of a specific tunnel."""
        verification_results = self.verify_tunnels([identifier])
        if verification_results:
            return verification_results[0]
        return {'status': ComponentStatus.UNKNOWN.value, 'error': 'Tunnel not found'}
    
    def list_components(self) -> List[Dict[str, Any]]:
        """List all managed WireGuard tunnels in sorted order."""
        # Sort tunnels by name for consistent output
        sorted_tunnels = self._sort_tunnels_by_name(self.created_tunnels)
        
        return [
            {
                'name': tunnel.name,
                'ip_address': tunnel.ip_address,
                'peer_ip_address': getattr(tunnel, 'peer_ip_address', None),
                'mapped_name': getattr(tunnel, 'mapped_name', None)
            }
            for tunnel in sorted_tunnels
        ]
    
    # Public utility methods
    
    def get_next_available_index(self, start_index: int = 0) -> int:
        """
        Get the next available WireGuard interface index.
        
        Args:
            start_index: Starting index to check from
            
        Returns:
            int: Next available interface index
        """
        try:
            current_config = self.connection.client.get_configuration()
            existing_wg_names = set()
            
            # Extract existing WireGuard interface names
            for item in current_config.items:
                if (hasattr(item.config, 'name') and hasattr(item.config, 'type') and
                    hasattr(models.InterfaceType, 'WIREGUARD_TUNNEL') and 
                    item.config.type == models.InterfaceType.WIREGUARD_TUNNEL):
                    existing_wg_names.add(item.config.name)
            
            # Find next available index
            index = start_index
            while f"wg{index}" in existing_wg_names:
                index += 1
                
            log.debug(f"Next available WireGuard index: {index}")
            return index
            
        except Exception as e:
            log.warning(f"Could not check existing WireGuard interfaces: {e}")
            return start_index
    
    def get_existing_wireguard_ports(self) -> Dict[int, str]:
        """
        Get dictionary of existing WireGuard interface ports and their associated interfaces.
        
        Returns:
            Dict[int, str]: Mapping of port number to interface name
        """
        existing_ports = {}
        try:
            current_config = self.connection.client.get_configuration()
            
            for item in current_config.items:
                if (hasattr(item.config, 'type') and 
                    hasattr(models.InterfaceType, 'WIREGUARD_TUNNEL') and
                    item.config.type == models.InterfaceType.WIREGUARD_TUNNEL):
                    
                    if hasattr(item.config, 'link') and hasattr(item.config.link, 'port'):
                        port = item.config.link.port
                        if port:
                            existing_ports[port] = item.config.name
                            
            log.debug(f"Existing WireGuard ports: {existing_ports}")
            return existing_ports
            
        except Exception as e:
            log.warning(f"Could not check existing WireGuard interface ports: {e}")
            return {}
    
    def get_wireguard_interfaces(self) -> List[Dict[str, Any]]:
        """
        Get list of all WireGuard interfaces from VPP.
        
        Returns:
            List[dict]: List of WireGuard interface information
        """
        try:
            current_config = self.connection.client.get_configuration()
            interfaces = []
            
            for item in current_config.items:
                if (hasattr(item.config, 'type') and 
                    hasattr(models.InterfaceType, 'WIREGUARD_TUNNEL') and
                    item.config.type == models.InterfaceType.WIREGUARD_TUNNEL):
                    
                    interface_info = {
                        'name': item.config.name,
                        'enabled': getattr(item.config, 'enabled', False),
                        'ip_addresses': getattr(item.config, 'ip_addresses', []),
                        'mtu': getattr(item.config, 'mtu', None),
                        # render all object attributes as strings
                        'additional_attributes': {k: str(v) for k, v in item.config.__dict__.items() if k not in ['name', 'type', 'enabled', 'ip_addresses', 'mtu', 'link']}
                    }
                    
                    
                   

                    # Add WireGuard-specific link information
                    if hasattr(item.config, 'link') and item.config.link:
                        link = item.config.link
                        interface_info.update({
                            'private_key': getattr(link, 'private_key', None),
                            'listen_port': getattr(link, 'port', None),
                            'src_addr': str(getattr(link, 'src_addr', None)) if getattr(link, 'src_addr', None) else None
                        })
                    
                    interfaces.append(interface_info)
            
            return interfaces
            
        except Exception as e:
            log.error(f"Error getting WireGuard interfaces: {e}")
            return []
    
    def get_wireguard_peers(self) -> List[Dict[str, Any]]:
        """
        Get list of all WireGuard peers from VPP.
        
        Returns:
            List[dict]: List of WireGuard peer information
        """
        try:
            current_config = self.connection.client.get_configuration()
            peers = []
            
            for item in current_config.items:
                if isinstance(item.config, models.WireguardPeerConfigurationItem):
                    peer_info = {
                        'interface': item.config.wg_if_name,
                        'public_key': item.config.public_key,
                        'allowed_ips': getattr(item.config, 'allowed_ips', []),
                        'endpoint': str(item.config.endpoint) if item.config.endpoint else None,
                        'port': item.config.port,
                        'persistent_keepalive': getattr(item.config, 'persistent_keepalive', None)
                    }
                    peers.append(peer_info)
            
            return peers
            
        except Exception as e:
            log.error(f"Error getting WireGuard peers: {e}")
            return []
    
    # Private helper methods
    
    def _validate_tunnel_configs(self, configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate tunnel configurations."""
        required_fields = ['address', 'private_key', 'peer_public_key', 'peer_address']
        all_errors = []
        
        # Check for port conflicts among new configurations
        port_usage = {}
        
        # Check for port conflicts with existing interfaces
        existing_ports = self.get_existing_wireguard_ports()
        
        for i, config in enumerate(configs):
            # Basic field validation
            result = validate_component_config(config, required_fields)
            if not result['valid']:
                all_errors.extend([f"Config {i}: {error}" for error in result['errors']])
            
            # Check for port conflicts
            listen_port = config.get('listen_port')
            if listen_port:
                # Check against existing VPP interfaces
                if listen_port in existing_ports:
                    all_errors.append(
                        f"Port conflict: Config {i} wants to use port {listen_port} but it's already used by interface {existing_ports[listen_port]}"
                    )
                # Check against other new configurations
                elif listen_port in port_usage:
                    all_errors.append(
                        f"Port conflict: Config {i} and Config {port_usage[listen_port]} both use listen_port {listen_port}"
                    )
                else:
                    port_usage[listen_port] = i
            else:
                all_errors.append(f"Config {i}: Missing required field 'listen_port'")
        
        if port_usage:
            log.info(f"New port assignments: {port_usage}")
        if existing_ports:
            log.info(f"Existing port assignments: {existing_ports}")
        
        return {
            'valid': len(all_errors) == 0,
            'errors': all_errors
        }
    
    def _dict_to_wireguard_config(self, config_dict: Dict[str, Any]) -> WireGuardConfig:
        """Convert dictionary to WireGuardConfig object."""
        # This would need to be implemented based on your WireGuardConfig class
        # For now, assuming it can be constructed from a dict
        return WireGuardConfig(**config_dict)
    
    def _prepare_vpp_configurations(self) -> tuple:
        """Prepare VPP interface, peer, and route configurations."""
        interfaces = []
        peers = []
        routes = []
        
        # First pass: resolve and store all interface names to avoid conflicts
        for i, tunnel_config in enumerate(self._tunnel_configs):
            if not tunnel_config.interface_name:
                # Generate interface name based on index
                tunnel_config.interface_name = f"wg{i}"
                log.debug(f"Generated interface name: {tunnel_config.interface_name} for tunnel {i}")
            else:
                log.debug(f"Using provided interface name: {tunnel_config.interface_name} for tunnel {i}")
        
        # Second pass: create VPP configurations with resolved names
        for i, tunnel_config in enumerate(self._tunnel_configs):
            log.debug(f"Processing tunnel config {i}: interface_name={tunnel_config.interface_name}, listen_port={tunnel_config.listen_port}")
            
            # Interface configuration
            interfaces.append(
                models.InterfaceConfigurationItem(
                    name=tunnel_config.interface_name,
                    type=models.InterfaceType.WIREGUARD_TUNNEL,
                    enabled=True,
                    ip_addresses=[f"{tunnel_config.address}/30"],
                    mtu=tunnel_config.mtu if tunnel_config.mtu else 1420,
                    link=models.WireguardInterfaceLink(
                        private_key=tunnel_config.private_key,
                        port=tunnel_config.listen_port,
                        src_addr=ipaddress.IPv4Address(tunnel_config.source_ip) if tunnel_config.source_ip else None,
                    ),
                )
            )
            
            # Peer configuration
            peers.append(
                models.WireguardPeerConfigurationItem(
                    wg_if_name=tunnel_config.interface_name,
                    public_key=tunnel_config.peer_public_key,
                    allowed_ips=["0.0.0.0/0"],
                    persistent_keepalive=tunnel_config.persistent_keepalive,
                    endpoint=ipaddress.IPv4Address(tunnel_config.peer_endpoint.split(":")[0]) if tunnel_config.peer_endpoint else None,
                    port=tunnel_config.peer_endpoint.split(":")[1] if tunnel_config.peer_endpoint and ":" in tunnel_config.peer_endpoint else None,
                )
            )
            
            # Route configuration
            routes.append(
                models.RouteConfigurationItem(
                    destination_network=f"{tunnel_config.peer_address.split('/')[0]}/32",
                    next_hop_address=tunnel_config.address.split("/")[0],
                    outgoing_interface=tunnel_config.interface_name,
                )
            )
            
        
        return interfaces, peers, routes
    
    def _apply_vpp_configurations(self, interfaces, peers, routes) -> Dict[str, Any]:
        """Apply configurations to VPP."""
        if not (interfaces or peers or routes):
            return create_result_dict(success=True, data={'created_tunnels': []})
        
        try:
            reply = self.connection.client.add_configuration(
                *chain(interfaces, peers, routes)
            )
            log.debug(f"VPP reply: {reply}")
            
            errors = self._extract_reply_errors(reply)
            if errors:
                return create_result_dict(
                    success=False, 
                    error=f"VPP processing errors: {'; '.join(errors)}"
                )
            
            if reply and reply.all_added_items_applied_to_vpp:
                created_tunnels = self._create_tunnel_tracking_objects()
                return create_result_dict(
                    success=True, 
                    data={'created_tunnels': created_tunnels}
                )
            else:
                return create_result_dict(
                    success=False, 
                    error="Failed to apply configuration to VPP"
                )
                
        except Exception as e:
            return create_result_dict(success=False, error=str(e))
    
    def _create_tunnel_tracking_objects(self) -> List[CreatedWireguardTunnel]:
        """Create tunnel tracking objects for internal management."""
        created_tunnels = []        
        for tunnel_config in self._tunnel_configs:
            created_tunnels.append(
                CreatedWireguardTunnel(
                    name=tunnel_config.interface_name,
                    ip_address=tunnel_config.address,
                    peer_ip_address=tunnel_config.peer_address,
                    mapped_name=tunnel_config.interface_name,
                )
            )
        
        return created_tunnels
    
    def _generate_interface_data(self) -> List[Dict[str, Any]]:
        """Generate Django interface model data."""
        interface_data = []
        
        for i, (tunnel, config) in enumerate(zip(self.created_tunnels, self._tunnel_configs)):
            ip_address_without_cidr = config.address.split('/')[0]
            subnet_mask = int(config.address.split('/')[1]) if '/' in config.address else 30
            
            interface_info = {
                'name': tunnel.name,
                'type': 'tunnel',
                'up': True,
                'hwaddr': None,  # WireGuard interfaces don't have MAC addresses
                'ip_address': ip_address_without_cidr,
                'subnet_mask': subnet_mask,
                'vlan_id': None,
                'mtu': config.mtu if config.mtu else 1420,
                'vpp_used': True,
                'vpp_interface_name': tunnel.name,
                'is_enabled': True,
                'description': f"WireGuard tunnel to {config.peer_endpoint}",
                'is_management': False,
                'is_wan': True,
                'is_lan': False,
                'is_primary': False,
                'tunnel_metadata': {
                    'tunnel_type': 'wireguard',
                    'peer_public_key': config.peer_public_key,
                    'peer_endpoint': config.peer_endpoint,
                    'peer_address': config.peer_address,
                    'listen_port': config.listen_port,
                    'persistent_keepalive': config.persistent_keepalive
                }
            }
            interface_data.append(interface_info)
        
        return interface_data
    
    def _find_configurations_to_remove(self, tunnels_to_remove) -> List:
        """Find VPP configurations that need to be removed."""
        current_config = self.connection.client.get_configuration()
        configs = []
        
        for tunnel in tunnels_to_remove:
            # Find interface configuration
            interface_configs = [
                item.config for item in current_config.items
                if isinstance(item.config, models.InterfaceConfigurationItem)
                and item.config.name == tunnel.name
            ]
            
            # Find peer configuration
            peer_configs = [
                item.config for item in current_config.items
                if isinstance(item.config, models.WireguardPeerConfigurationItem)
                and item.config.wg_if_name == tunnel.name
            ]
            
            # Find route configuration
            route_configs = [
                item.config for item in current_config.items
                if isinstance(item.config, models.RouteConfigurationItem)
                and item.config.outgoing_interface == tunnel.name
            ]
            
            configs.extend(interface_configs + peer_configs + route_configs)
        
        return configs
    
    def _cleanup_tunnel_tracking(self, tunnel_names: Optional[List[str]]):
        """Clean up internal tunnel tracking."""
        if tunnel_names:
            self.created_tunnels = [
                t for t in self.created_tunnels if t.name not in tunnel_names
            ]
        else:
            self.created_tunnels = []
    
    def _verify_single_tunnel(self, tunnel: CreatedWireguardTunnel) -> Dict[str, Any]:
        """Verify a single tunnel's operational status."""
        # This would implement actual verification logic
        # For now, return a basic structure
        return {
            'tunnel_name': tunnel.name,
            'status': ComponentStatus.ACTIVE.value,
            'interface_up': True,  # Would check actual interface status
            'connectivity': True,  # Would test actual connectivity
            'local_ip': tunnel.ip_address,
            'peer_ip': getattr(tunnel, 'peer_ip_address', None)
        }
    
    def _get_tunnel_vpp_config(self, tunnel_name: str) -> Optional[Dict[str, Any]]:
        """Get VPP configuration for a specific tunnel."""
        try:
            current_config = self.connection.client.get_configuration()
            
            for item in current_config.items:
                if (hasattr(item.config, 'name') and 
                    item.config.name == tunnel_name):
                    return {
                        'name': item.config.name,
                        'type': str(item.config.type),
                        'enabled': getattr(item.config, 'enabled', None),
                        'ip_addresses': getattr(item.config, 'ip_addresses', []),
                        'mtu': getattr(item.config, 'mtu', None)
                    }
            
            return None
            
        except Exception as e:
            log.error(f"Error getting VPP config for {tunnel_name}: {e}")
            return None
    
    def _find_tunnel_config_by_name(self, tunnel_name: str) -> Optional[WireGuardConfig]:
        """Find original tunnel configuration by tunnel name."""
        # This would need to map tunnel names back to original configs
        # Implementation depends on how you want to maintain this mapping
        return None
    
    def _get_tunnel_status(self, tunnel_name: str) -> str:
        """Get current status of a tunnel."""
        # Implement actual status checking logic
        return ComponentStatus.ACTIVE.value
    
    def _sort_tunnels_by_name(self, tunnels: List[CreatedWireguardTunnel]) -> List[CreatedWireguardTunnel]:
        """
        Sort tunnels by name in numerical order (wg0, wg1, wg2, etc.).
        
        Args:
            tunnels: List of WireGuard tunnels to sort
            
        Returns:
            List[CreatedWireguardTunnel]: Sorted list of tunnels
        """
        def extract_tunnel_number(tunnel_name: str) -> int:
            """Extract numerical part from tunnel name for sorting."""
            try:
                # Handle names like 'wg0', 'wg1', etc.
                if tunnel_name.startswith('wg'):
                    return int(tunnel_name[2:])
                # Handle names with underscores or other patterns
                elif '_' in tunnel_name:
                    parts = tunnel_name.split('_')
                    for part in reversed(parts):
                        if part.isdigit():
                            return int(part)
                # Extract any trailing digits
                numbers = re.findall(r'\d+', tunnel_name)
                if numbers:
                    return int(numbers[-1])
                return 999999  # Put non-numeric tunnels at the end
            except (ValueError, IndexError):
                return 999999  # Put problematic names at the end
        
        return sorted(tunnels, key=lambda t: extract_tunnel_number(t.name))
    
    def _sort_configs_by_interface_name(self, configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sort configurations by interface name in numerical order.
        
        Args:
            configs: List of tunnel configurations to sort
            
        Returns:
            List[Dict[str, Any]]: Sorted list of configurations
        """
        def extract_config_number(config: Dict[str, Any]) -> int:
            """Extract numerical part from config interface name for sorting."""
            try:
                # Try different possible keys for interface name
                interface_name = config.get('interface_name') or config.get('name') or config.get('tunnel_name', '')
                
                if interface_name.startswith('wg'):
                    return int(interface_name[2:])
                elif '_' in interface_name:
                    parts = interface_name.split('_')
                    for part in reversed(parts):
                        if part.isdigit():
                            return int(part)
                
                numbers = re.findall(r'\d+', interface_name)
                if numbers:
                    return int(numbers[-1])
                return 999999
            except (ValueError, IndexError, AttributeError):
                return 999999
        
        return sorted(configs, key=lambda c: extract_config_number(c))
    
    def _sort_wireguard_configs(self, configs: List[WireGuardConfig]) -> List[WireGuardConfig]:
        """
        Sort WireGuardConfig objects by interface name in numerical order.
        
        Args:
            configs: List of WireGuardConfig objects to sort
            
        Returns:
            List[WireGuardConfig]: Sorted list of WireGuardConfig objects
        """
        def extract_wg_config_number(config: WireGuardConfig) -> int:
            """Extract numerical part from WireGuardConfig interface name for sorting."""
            try:
                interface_name = config.interface_name or ''
                
                if interface_name.startswith('wg'):
                    return int(interface_name[2:])
                elif '_' in interface_name:
                    parts = interface_name.split('_')
                    for part in reversed(parts):
                        if part.isdigit():
                            return int(part)
                
                numbers = re.findall(r'\d+', interface_name)
                if numbers:
                    return int(numbers[-1])
                return 999999
            except (ValueError, IndexError, AttributeError):
                return 999999
        
        return sorted(configs, key=lambda c: extract_wg_config_number(c))
