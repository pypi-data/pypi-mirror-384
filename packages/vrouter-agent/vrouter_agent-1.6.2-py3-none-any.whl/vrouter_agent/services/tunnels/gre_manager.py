"""
GRE Tunnel Manager

This module provides specialized management for GRE tunnel operations,
implementing the TunnelManager interface with GRE-specific functionality.
"""

from typing import List, Dict, Any, Optional
import ipaddress
import re

from loguru import logger as log
from vpp_vrouter.common import models

from ..base_interfaces import TunnelManager, ComponentStatus, create_result_dict
from ..connection.vpp_connection import VPPConnectionManager
from ...utils.gre_manager import get_gre_manager, convert_wg_to_gre_ip_addr_safe
from ...utils.cli import run_command
from ...core.base import CreatedWireguardTunnel
from ...schemas.tunnel_config import WireGuardConfig


class GRETunnelManager(TunnelManager):
    """
    Manages GRE tunnel operations through VPP API.
    
    This class handles GRE tunnel creation, configuration, and management,
    including integration with WireGuard tunnels and FRR containers.
    """
    
    def __init__(self, connection_manager: VPPConnectionManager):
        """
        Initialize the GRE tunnel manager.
        
        Args:
            connection_manager: VPP connection manager instance
        """
        self.connection = connection_manager
        self.created_tunnels: List[CreatedWireguardTunnel] = []
        self.gre_manager = get_gre_manager()
    
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

    def _dict_to_wireguard_config(self, config_dict: Dict[str, Any]) -> WireGuardConfig:
        """Convert dictionary to WireGuardConfig object."""
        if isinstance(config_dict, WireGuardConfig):
            # Already a WireGuardConfig object, return as-is
            return config_dict
        elif isinstance(config_dict, dict):
            # Convert dictionary to WireGuardConfig
            return WireGuardConfig(**config_dict)
        else:
            raise TypeError(f"Expected dict or WireGuardConfig, got {type(config_dict)}")
    
    def create_tunnels_from_wireguard(self, wireguard_tunnels: List[CreatedWireguardTunnel], 
                                     original_configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create GRE tunnels based on existing WireGuard tunnels.
        
        Args:
            wireguard_tunnels: List of created WireGuard tunnels
            original_configs: Original tunnel configurations with GRE fields
            
        Returns:
            List[dict]: Created GRE tunnel information
        """
        if not wireguard_tunnels:
            log.error("No WireGuard tunnels provided for GRE creation")
            return []
        
        try:
            log.info(f"Creating GRE tunnels for {len(wireguard_tunnels)} WireGuard tunnels")
            
            self.created_tunnels = []
            
            # Sort tunnels by name to ensure consistent processing order (wg0, wg1, wg2, etc.)
            sorted_wireguard_tunnels = self._sort_tunnels_by_name(wireguard_tunnels)
            log.info(f"Processing tunnels in sorted order: {[t.name for t in sorted_wireguard_tunnels]}")
            
            # Convert original_configs to WireGuardConfig objects once outside the loop
            converted_configs = []
            for cfg in original_configs:
                if isinstance(cfg, dict):
                    converted_configs.append(self._dict_to_wireguard_config(cfg))
                else:
                    # Already a WireGuardConfig object
                    converted_configs.append(cfg)
            
            for i, wg_tunnel in enumerate(sorted_wireguard_tunnels):
                # Find corresponding original tunnel config
                if not converted_configs:
                    log.error("No original configurations provided for GRE creation")
                    continue
                
                original_tunnel = self._find_original_config(wg_tunnel, converted_configs, i)
                
                try:
                    
                    gre_name, gre_ip = self._create_single_gre_tunnel(wg_tunnel, original_tunnel)
                    
                    self.created_tunnels.append(
                        CreatedWireguardTunnel(
                            name=gre_name, 
                            ip_address=gre_ip,
                            peer_ip_address=getattr(wg_tunnel, 'peer_ip_address', None),
                            mapped_name=f"gre-{wg_tunnel.name}"
                        )
                    )
                    
                    log.info(f"Successfully created GRE tunnel {gre_name} for WireGuard tunnel {wg_tunnel.name}")
                    
                except Exception as e:
                    log.error(f"Failed to create GRE tunnel for {wg_tunnel.name}: {e}")
                    # Continue with other tunnels
                    continue
            
            log.info(f"Created {len(self.created_tunnels)} GRE tunnels")
            
            # Sort created tunnels by name for consistent output ordering
            sorted_created_tunnels = self._sort_tunnels_by_name(self.created_tunnels)
            
            return [
                {
                    'name': tunnel.name,
                    'ip_address': tunnel.ip_address,
                    'peer_ip_address': tunnel.peer_ip_address,
                    'wireguard_tunnel': tunnel.mapped_name
                }
                for tunnel in sorted_created_tunnels
            ]
            
        except Exception as e:
            log.error(f"Exception creating GRE tunnels: {e}")
            return []
    
    def create_tunnels(self, configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create GRE tunnels from configuration list.
        
        Args:
            configs: List of GRE tunnel configurations
            
        Returns:
            dict: Result with success status and created tunnel data
        """
        try:
            # Sort configurations by interface name to ensure consistent processing order
            sorted_configs = self._sort_configs_by_interface_name(configs)
            log.info(f"Processing GRE configs in sorted order: {[cfg.get('interface_name', cfg.get('name', 'unknown')) for cfg in sorted_configs]}")
            
            created_tunnels = []
            
            for config in sorted_configs:
                result = self._create_gre_from_config(config)
                if result['success']:
                    created_tunnels.append(result['tunnel'])
                else:
                    log.error(f"Failed to create GRE tunnel: {result.get('error')}")
            
            return create_result_dict(
                success=len(created_tunnels) > 0,
                data={'tunnels': created_tunnels, 'created_count': len(created_tunnels)}
            )
            
        except Exception as e:
            log.error(f"Exception creating GRE tunnels from configs: {e}")
            return create_result_dict(success=False, error=str(e))
    
    def remove_tunnels(self, tunnel_names: Optional[List[str]] = None) -> bool:
        """
        Remove GRE tunnels and deallocate their addresses.
        
        Args:
            tunnel_names: Optional list of tunnel names to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            success = True
            
            tunnels_to_remove = self.created_tunnels
            if tunnel_names:
                tunnels_to_remove = [t for t in self.created_tunnels if t.name in tunnel_names]
            
            # Sort tunnels in reverse order for removal (remove higher numbered tunnels first)
            # This helps avoid potential dependency issues
            sorted_tunnels_to_remove = self._sort_tunnels_by_name(tunnels_to_remove)
            sorted_tunnels_to_remove.reverse()
            
            log.info(f"Removing tunnels in reverse order: {[t.name for t in sorted_tunnels_to_remove]}")
            
            # Clean up GRE allocations
            for tunnel in sorted_tunnels_to_remove:
                # Extract WireGuard tunnel name from mapped_name
                wg_tunnel_name = tunnel.mapped_name.replace('gre-', '') if tunnel.mapped_name else tunnel.name
                
                if not self.gre_manager.deallocate_gre_addresses(wg_tunnel_name):
                    log.warning(f"Failed to deallocate GRE addresses for {wg_tunnel_name}")
                    success = False
            
            # Remove tunnels from VPP (implementation would go here)
            # This would involve finding and removing GRE interface configurations
            
            # Update tracking
            if tunnel_names:
                self.created_tunnels = [t for t in self.created_tunnels if t.name not in tunnel_names]
            else:
                self.created_tunnels = []
            
            if success:
                log.info("GRE tunnels removed and addresses deallocated successfully")
            else:
                log.warning("GRE tunnel removal completed with some warnings")
                
            return success
            
        except Exception as e:
            log.error(f"Exception while removing GRE tunnels: {e}")
            return False
    
    def verify_tunnels(self, tunnel_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Verify operational status of GRE tunnels.
        
        Args:
            tunnel_names: Optional list of tunnel names to verify
            
        Returns:
            List[dict]: List of tunnel verification results
        """
        results = []
        
        tunnels_to_verify = self.created_tunnels
        if tunnel_names:
            tunnels_to_verify = [t for t in self.created_tunnels if t.name in tunnel_names]
        
        # Sort tunnels to ensure consistent verification order
        sorted_tunnels_to_verify = self._sort_tunnels_by_name(tunnels_to_verify)
        
        for tunnel in sorted_tunnels_to_verify:
            try:
                # Check if GRE interface exists and is up
                interface_up = self._check_gre_interface_status(tunnel.name)
                
                # Test connectivity through GRE tunnel
                connectivity = False
                if interface_up and tunnel.peer_ip_address:
                    connectivity = self._test_gre_connectivity(tunnel.name, tunnel.peer_ip_address)
                
                status = ComponentStatus.ACTIVE.value if (interface_up and connectivity) else ComponentStatus.INACTIVE.value
                
                results.append({
                    'tunnel_name': tunnel.name,
                    'status': status,
                    'interface_up': interface_up,
                    'connectivity': connectivity,
                    'local_ip': tunnel.ip_address,
                    'peer_ip': tunnel.peer_ip_address
                })
                
            except Exception as e:
                log.error(f"Error verifying GRE tunnel {tunnel.name}: {e}")
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
        Get detailed information about a specific GRE tunnel.
        
        Args:
            tunnel_name: Name of the GRE tunnel
            
        Returns:
            Optional[dict]: Tunnel information or None if not found
        """
        tunnel = next((t for t in self.created_tunnels if t.name == tunnel_name), None)
        if not tunnel:
            return None
        
        try:
            # Get VPP GRE interface configuration
            vpp_config = self._get_gre_vpp_config(tunnel_name)
            
            return {
                'name': tunnel.name,
                'type': 'gre',
                'ip_address': tunnel.ip_address,
                'peer_ip_address': tunnel.peer_ip_address,
                'wireguard_tunnel': tunnel.mapped_name,
                'vpp_config': vpp_config,
                'status': self._get_tunnel_status(tunnel_name)
            }
            
        except Exception as e:
            log.error(f"Error getting GRE tunnel info for {tunnel_name}: {e}")
            return None
    
    # Implementation of NetworkComponent abstract methods
    
    def create(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a single GRE tunnel from configuration."""
        return self.create_tunnels([config])
    
    def delete(self, identifier: str) -> bool:
        """Delete a GRE tunnel by name."""
        return self.remove_tunnels([identifier])
    
    def get_status(self, identifier: str) -> Dict[str, Any]:
        """Get status of a specific GRE tunnel."""
        verification_results = self.verify_tunnels([identifier])
        if verification_results:
            return verification_results[0]
        return {'status': ComponentStatus.UNKNOWN.value, 'error': 'GRE tunnel not found'}
    
    def list_components(self) -> List[Dict[str, Any]]:
        """List all managed GRE tunnels in sorted order."""
        # Sort tunnels by name for consistent output
        sorted_tunnels = self._sort_tunnels_by_name(self.created_tunnels)
        
        return [
            {
                'name': tunnel.name,
                'type': 'gre',
                'ip_address': tunnel.ip_address,
                'peer_ip_address': tunnel.peer_ip_address,
                'wireguard_tunnel': tunnel.mapped_name
            }
            for tunnel in sorted_tunnels
        ]
    
    # Private helper methods
    
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
    
    def _find_original_config(self, wg_tunnel: CreatedWireguardTunnel, 
                             original_configs: List[WireGuardConfig], index: int) -> Optional[WireGuardConfig]:
        """
        Find the original tunnel configuration for a WireGuard tunnel.
        Now handles sorted tunnels by matching interface names first, then falling back to index.
        """
        # First try to match by interface name (most reliable)
        for tunnel_config in original_configs:
            # Check direct interface name match
            if (hasattr(tunnel_config, 'interface_name') and 
                tunnel_config.interface_name == wg_tunnel.name):
                return tunnel_config
            
            # Check mapped name match
            if (hasattr(tunnel_config, 'interface_name') and 
                tunnel_config.interface_name == wg_tunnel.mapped_name):
                return tunnel_config
        
        # Second try: match by tunnel name pattern (wg0 -> config with interface_name=wg0)
        for tunnel_config in original_configs:
            if hasattr(tunnel_config, 'interface_name'):
                config_name = tunnel_config.interface_name
                tunnel_name = wg_tunnel.name
                
                # Extract numbers from both names and compare
                config_numbers = re.findall(r'\d+', config_name)
                tunnel_numbers = re.findall(r'\d+', tunnel_name)
                
                if (config_numbers and tunnel_numbers and 
                    config_numbers[-1] == tunnel_numbers[-1]):
                    return tunnel_config
        
        # Fallback: match by index (less reliable after sorting)
        if index < len(original_configs):
            log.warning(f"Using index-based matching for tunnel {wg_tunnel.name} (index {index})")
            return original_configs[index]
        
        log.warning(f"No matching original config found for tunnel {wg_tunnel.name}")
        return None
    
    def _create_single_gre_tunnel(self, wg_tunnel: CreatedWireguardTunnel, 
                                 original_tunnel: Optional[WireGuardConfig]) -> tuple:
        """
        Create a single GRE tunnel for a WireGuard tunnel.
        
        Returns:
            tuple: (gre_interface_name, gre_interface_ip_with_mask)
        """
        try:
            log.info(f"Original tunnel config: {original_tunnel}")
            # Check if we have predefined GRE configuration
            if (original_tunnel and 
                hasattr(original_tunnel, 'gre_local_name') and original_tunnel.gre_local_name and 
                hasattr(original_tunnel, 'gre_remote_name') and original_tunnel.gre_remote_name and
                hasattr(original_tunnel, 'gre_local_tunnel_ip') and original_tunnel.gre_local_tunnel_ip and 
                hasattr(original_tunnel, 'gre_remote_tunnel_ip') and original_tunnel.gre_remote_tunnel_ip):
                
                # Use predefined GRE configuration
                gre_local_interface_name = original_tunnel.gre_local_name
                gre_remote_interface_name = original_tunnel.gre_remote_name
                gre_interface_ip_address = original_tunnel.gre_local_tunnel_ip
                remote_gre_interface_ip_address = original_tunnel.gre_remote_tunnel_ip
                
                if "/" in gre_interface_ip_address:
                    local_gre_ip_with_mask = gre_interface_ip_address
                    gre_interface_ip_address = gre_interface_ip_address.split("/")[0]
                    gre_interface_ip_address_mask = local_gre_ip_with_mask.split("/")[1]
                else:
                    gre_interface_ip_address_mask = "30"
                    local_gre_ip_with_mask = f"{gre_interface_ip_address}/{gre_interface_ip_address_mask}"
                
                log.info(f"Using predefined GRE config - Interface: {gre_local_interface_name}, "
                        f"Local: {local_gre_ip_with_mask}, Remote: {remote_gre_interface_ip_address}")
                        
            else:
                # Use automatic generation
                log.info(f"Using automatic GRE generation for {wg_tunnel.name}")
                
                # Extract index from tunnel name
                if wg_tunnel.name.startswith("wg"):
                    index = wg_tunnel.name[2:]
                else:
                    index = wg_tunnel.name.split("_")[-1]
                
                gre_local_interface_name = f"gre{index}"
                
                # Use GRE manager for safe address allocation
                local_gre_ip_with_mask, remote_gre_interface_ip_address = convert_wg_to_gre_ip_addr_safe(
                    wg_tunnel, self.gre_manager
                )
                
                gre_interface_ip_address = local_gre_ip_with_mask.split("/")[0]
                gre_interface_ip_address_mask = local_gre_ip_with_mask.split("/")[1]
                
                log.info(f"GRE auto-generated - Interface: {gre_local_interface_name}, "
                        f"Local: {local_gre_ip_with_mask}, Remote: {remote_gre_interface_ip_address}")
            
            # Create the GRE tunnel in VPP
            success = self._create_gre_tunnel_in_vpp(
                gre_local_interface_name,
                gre_interface_ip_address,
                gre_interface_ip_address_mask,
                remote_gre_interface_ip_address,
                wg_tunnel
            )
            
            if success:
                # Add additional configurations (OSPF routing, LCP, etc.)
                self._configure_gre_routing(
                    gre_local_interface_name,
                    remote_gre_interface_ip_address
                )
                
                # Add FRR agent IP translation
                self._add_frr_ip_translation(
                    gre_interface_ip_address,
                    self._safe_extract_ip(wg_tunnel.ip_address),
                    remote_gre_interface_ip_address,
                    self._safe_extract_ip(wg_tunnel.peer_ip_address) if hasattr(wg_tunnel, 'peer_ip_address') else remote_gre_interface_ip_address
                )
                
                return gre_local_interface_name, local_gre_ip_with_mask
            else:
                raise Exception("Failed to create GRE tunnel in VPP")
                
        except Exception as e:
            log.error(f"Failed to create GRE tunnel for {wg_tunnel.name}: {e}")
            # Cleanup on failure
            if not (original_tunnel and hasattr(original_tunnel, 'gre_local_name')):
                try:
                    self.gre_manager.deallocate_gre_addresses(wg_tunnel.name)
                except Exception as cleanup_error:
                    log.warning(f"Failed to cleanup GRE allocation: {cleanup_error}")
            raise
    
    def _create_gre_tunnel_in_vpp(self, gre_name: str, local_ip: str, mask: str, 
                                 remote_ip: str, wg_tunnel: CreatedWireguardTunnel) -> bool:
        """Create GRE tunnel configuration in VPP."""
        try:
            # Create GRE interface
            gre_iface = models.InterfaceConfigurationItem(
                name=gre_name,
                type=models.InterfaceType.GRE_TUNNEL,
                enabled=False,
                ip_addresses=[],
                link=models.GREInterfaceLink(
                    type=models.GRELinkType.L3,
                    src_addr=ipaddress.IPv4Address(local_ip),
                    dst_addr=ipaddress.IPv4Address(remote_ip),
                ),
            )
            
            
            # Add initial configuration
            reply = self.connection.client.add_configuration(gre_iface)
            
            log.debug(f"Reply from configuration add: {reply}")
            errors = self._extract_reply_errors(reply)
            if errors:
                log.error(f"Error adding GRE interface: {'; '.join(errors)}")
                return False
            
            # Add route to remote GRE endpoint via WireGuard tunnel
            if not self._add_gre_route(remote_ip, wg_tunnel):
                log.warning(f"Failed to add GRE route, but continuing with tunnel creation")
            
            # Create LCP interface pairing
            if not self._add_lcp_interface(gre_name, wg_tunnel.name, "frr", True):
                log.warning(f"Failed to add LCP interface pairing, but continuing with tunnel creation")
            
            # Enable interface with IP address
            reply = self.connection.client.update_configuration(
                gre_iface,
                models.InterfaceConfigurationItem(
                    name=gre_name,
                    type=models.InterfaceType.GRE_TUNNEL,
                    enabled=True,
                    ip_addresses=[f"{local_ip}/{mask}"],
                    link=models.GREInterfaceLink(
                        type=models.GRELinkType.L3,
                        src_addr=ipaddress.IPv4Address(local_ip),
                        dst_addr=ipaddress.IPv4Address(remote_ip),
                    ),
                ),
            )
            
            errors = self._extract_reply_errors(reply)
            if errors:
                log.error(f"Error enabling GRE interface: {'; '.join(errors)}")
                return False
            
            log.info(f"Successfully created GRE tunnel {gre_name}")
            return True
            
        except Exception as e:
            log.error(f"Exception creating GRE tunnel in VPP: {e}")
            return False
    
    def _add_gre_route(self, remote_ip: str, wg_tunnel: CreatedWireguardTunnel) -> bool:
        """Add route to GRE remote endpoint via WireGuard tunnel.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            reply = self.connection.client.add_configuration(
                models.RouteConfigurationItem(
                    destination_network=f"{remote_ip}/32",
                    next_hop_address=self._safe_extract_ip(wg_tunnel.peer_ip_address) if hasattr(wg_tunnel, 'peer_ip_address') else remote_ip,
                    outgoing_interface=wg_tunnel.name,
                )
            )
            log.debug(f"Reply from configuration add: {reply}")

            errors = self._extract_reply_errors(reply)
            if errors:
                log.error(f"Error adding GRE route: {'; '.join(errors)}")
                return False
            
            return True
        except Exception as e:
            log.error(f"Exception adding GRE route: {e}")
            return False
    
    def _add_lcp_interface(self, vpp_iface: str, host_iface: str, host_netns: str, is_tun: bool = False):
        """Add LCP interface pairing."""
        try:
            iface_type = (
                models.LCPHostInterfaceTypeEnum.TUN if is_tun 
                else models.LCPHostInterfaceTypeEnum.TAP
            )
            
            reply = self.connection.client.add_configuration(
                models.LCPPairConfigurationItem(
                    interface=vpp_iface,
                    mirror_interface_host_name=host_iface,
                    mirror_interface_type=iface_type,
                    host_namespace=host_netns,
                )
            )
            log.debug(f"Reply from configuration add: {reply}")

            errors = self._extract_reply_errors(reply)
            if errors:
                log.error(f"Error adding LCP interface: {'; '.join(errors)}")
                return False
            
            return True
            
        except Exception as e:
            log.error(f"Exception adding LCP interface: {e}")
            return False
    
    def _configure_gre_routing(self, gre_name: str, remote_ip: str):
        """Configure OSPF routing for GRE tunnel."""
        try:
            # Add multicast routes for OSPF
            run_command([
                "vppctl", "ip", "mroute", "add",
                remote_ip, "224.0.0.5",
                "via", gre_name, "Accept"
            ])
            
            run_command([
                "vppctl", "ip", "mroute", "add",
                remote_ip, "224.0.0.5",
                "via", "local", "Forward"
            ])
            
        except Exception as e:
            log.error(f"Error configuring GRE routing: {e}")
    
    def _add_frr_ip_translation(self, gre_local_ip: str, wg_local_ip: str, 
                               gre_remote_ip: str, wg_remote_ip: str, 
                               frr_container: str = "frr", 
                               replace_file: str = "/rr-ip-replace.txt"):
        """Add FRR agent IP translation from GRE to WireGuard."""
        try:
            # Add local IP translation
            run_command([
                "docker", "exec", "-t", frr_container, "sh", "-c",
                f"echo '{gre_local_ip}=>{wg_local_ip}' >> {replace_file}"
            ])
            
            # Add remote IP translation
            run_command([
                "docker", "exec", "-t", frr_container, "sh", "-c",
                f"echo '{gre_remote_ip}=>{wg_remote_ip}' >> {replace_file}"
            ])
            
            log.debug(f"Added FRR IP translation: {gre_local_ip}=>{wg_local_ip}, {gre_remote_ip}=>{wg_remote_ip}")
            
        except Exception as e:
            log.error(f"Error adding FRR IP translation: {e}")
    
    def _check_gre_interface_status(self, interface_name: str) -> bool:
        """Check if GRE interface is up."""
        try:
            cmd = f"vppctl show interface {interface_name}"
            res, _ = run_command(cmd.split())
            
            return interface_name in res and "up" in res.lower() and "down" not in res.lower()
            
        except Exception as e:
            log.error(f"Error checking GRE interface {interface_name}: {e}")
            return False
    
    def _test_gre_connectivity(self, interface_name: str, peer_ip: str) -> bool:
        """Test connectivity through GRE tunnel."""
        try:
            # Simple ping test through the GRE interface
            cmd = f"vppctl ping {self._safe_extract_ip(peer_ip)} repeat 1"
            res, _ = run_command(cmd.split())
            
            return "1 sent, 1 received" in res
            
        except Exception as e:
            log.error(f"Error testing GRE connectivity: {e}")
            return False
    
    def _get_gre_vpp_config(self, tunnel_name: str) -> Optional[Dict[str, Any]]:
        """Get VPP configuration for GRE tunnel."""
        try:
            current_config = self.connection.client.get_configuration()
            
            for item in current_config.items:
                if (hasattr(item.config, 'name') and 
                    item.config.name == tunnel_name and
                    hasattr(item.config, 'type') and
                    item.config.type == models.InterfaceType.GRE_TUNNEL):
                    
                    config_data = {
                        'name': item.config.name,
                        'type': str(item.config.type),
                        'enabled': getattr(item.config, 'enabled', None),
                        'ip_addresses': getattr(item.config, 'ip_addresses', [])
                    }
                    
                    # Add GRE-specific link information
                    if hasattr(item.config, 'link') and item.config.link:
                        link = item.config.link
                        config_data['link'] = {
                            'type': str(getattr(link, 'type', None)),
                            'src_addr': str(getattr(link, 'src_addr', None)),
                            'dst_addr': str(getattr(link, 'dst_addr', None))
                        }
                    
                    return config_data
            
            return None
            
        except Exception as e:
            log.error(f"Error getting GRE VPP config for {tunnel_name}: {e}")
            return None
    
    def _get_tunnel_status(self, tunnel_name: str) -> str:
        """Get current status of GRE tunnel."""
        try:
            if self._check_gre_interface_status(tunnel_name):
                return ComponentStatus.ACTIVE.value
            else:
                return ComponentStatus.INACTIVE.value
        except Exception:
            return ComponentStatus.ERROR.value
    
    def _safe_extract_ip(self, ip_with_mask: str) -> str:
        """Safely extract IP address from IP/mask format."""
        if not ip_with_mask:
            return "0.0.0.0"
        
        if "/" in ip_with_mask:
            return ip_with_mask.split("/")[0]
        else:
            return ip_with_mask
    
    def _create_gre_from_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create GRE tunnel from direct configuration."""
        # This would implement direct GRE creation from config
        # For now, return a placeholder
        return create_result_dict(success=False, error="Direct GRE creation not yet implemented")
