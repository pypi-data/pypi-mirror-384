"""
NAT Configuration Manager

This module provides specialized management for NAT (Network Address Translation)
configurations, implementing security management interfaces.
"""

from typing import List, Dict, Any, Optional
from itertools import chain
import ipaddress

from loguru import logger as log
from vpp_vrouter.common import models
from vrouter_agent.core.config import get_primary_interface
from vrouter_agent.schemas.nat_acl_config import NatConfig

from ..base_interfaces import SecurityManager, create_result_dict
from ..connection.vpp_connection import VPPConnectionManager
from ...core.base import Interface
from ...core.config import settings

class NATManager(SecurityManager):
    """
    Manages NAT44 configuration through VPP API.
    
    This class handles NAT interface configuration, address pools,
    port mappings, and identity mappings for various protocols.
    """
    
    def __init__(self, connection_manager: VPPConnectionManager):
        """
        Initialize the NAT manager.
        
        Args:
            connection_manager: VPP connection manager instance
        """
        self.connection = connection_manager
        self.active_policies: Dict[str, Dict[str, Any]] = {}
    
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

    def configure_nat(self, nat_config: NatConfig) -> bool:
        """
        Configure NAT44 for LAN/WAN interfaces with address pools and port mappings.
        
        Args:
            nat_config: NatConfig schema object containing NAT configuration
            
        Returns:
            bool: True if configuration successful, False otherwise
        """
        try:
            if not nat_config.enabled:
                log.info("NAT configuration is disabled, skipping")
                return True

            log.info("Starting NAT configuration")

            primary_wan = get_primary_interface(type='wan')
            primary_lan = get_primary_interface(type='lan')
         
            # Create NAT interface configurations from schema
            nat_interfaces = []
            
            if nat_config.nat44_interfaces:
                # Use interfaces from the schema
                for iface in nat_config.nat44_interfaces:
                    nat_interfaces.append(
                        models.Nat44InterfaceConfigurationItem(
                            name=iface.name,
                            nat_inside=iface.nat_inside,
                            nat_outside=iface.nat_outside,
                            output_feature=iface.output_feature,
                        )
                    )
            else:
                # Fallback to default LAN/WAN configuration
                nat_interfaces.extend([
                    models.Nat44InterfaceConfigurationItem(
                        name=primary_lan.interface_name,
                        nat_inside=True,
                        nat_outside=False,
                        output_feature=False,
                    ),
                    models.Nat44InterfaceConfigurationItem(
                        name=primary_wan.interface_name,
                        nat_inside=False,
                        nat_outside=True,
                        output_feature=False,
                    )
                ])
            
            # Create NAT pool addresses from schema
            pool_addresses = []
            if nat_config.address_pools:
                for i, pool in enumerate(nat_config.address_pools):
                    # If last_ip is empty, use first_ip (single IP pool)
                    last_ip = pool.last_ip if pool.last_ip else pool.first_ip
                    
                    pool_addresses.append(
                        models.Nat44AddressPoolConfigurationItem(
                            name=pool.name or f"nat-pool-{i}",
                            first_ip=ipaddress.IPv4Address(pool.first_ip),
                            last_ip=ipaddress.IPv4Address(last_ip),
                        )
                    )
            
            # Create static mappings and identity mappings from schema
            static_mappings = []
            identity_mappings = []
            
            if nat_config.dnat:
                # Process static mappings
                if nat_config.dnat.static_mappings:
                    for mapping in nat_config.dnat.static_mappings:
                        # Convert schema LocalIP objects to VPP models.LocalIP objects
                        local_ips = [
                            models.LocalIP(
                                local_ip=ipaddress.IPv4Address(lip.local_ip),
                                local_port=lip.local_port,
                                probability=lip.probability
                            ) 
                            for lip in mapping.local_ips
                        ]
                        
                        # Determine external_ip and external_interface
                        # Note: VPP library has a bug where external_sw_if_index=0 maps to local0
                        # Even when using explicit IP, we need to provide a valid interface name
                        # VPP will use external_ip when both are provided (IP takes precedence)
                        if mapping.external_ip and mapping.external_ip != "0.0.0.0" and mapping.external_ip != "":
                            # Use explicit external IP with WAN interface as reference
                            external_interface = primary_wan.interface_name  # Provide valid interface to avoid local0
                            external_ip = ipaddress.IPv4Address(mapping.external_ip)
                            log.info(f"NAT static mapping: Using explicit external_ip={external_ip} with interface={external_interface}")
                            
                            static_mappings.append(
                                models.StaticMapping(
                                    external_interface=external_interface,
                                    external_ip=external_ip,
                                    external_port=mapping.external_port,
                                    local_ips=local_ips,
                                    protocol=models.ProtocolInNAT(mapping.protocol),
                                )
                            )
                        else:
                            # Use WAN interface to get IP dynamically
                            external_interface = mapping.external_interface or primary_wan.interface_name
                            external_ip = ipaddress.IPv4Address(str(primary_wan.ip_address))
                            log.info(f"NAT static mapping: Using external_interface={external_interface}, external_ip={external_ip}")
                            
                            static_mappings.append(
                                models.StaticMapping(
                                    external_interface=external_interface,
                                    external_ip=external_ip,
                                    external_port=mapping.external_port,
                                    local_ips=local_ips,
                                    protocol=models.ProtocolInNAT(mapping.protocol),
                                )
                            )
                
                # Process identity mappings
                if nat_config.dnat.identity_mappings:
                    for mapping in nat_config.dnat.identity_mappings:
                        identity_mappings.append(
                            models.IdentityMapping(
                                interface=mapping.interface or primary_wan.interface_name,
                                port=mapping.port,
                                protocol=models.ProtocolInNAT(mapping.protocol)
                            )
                        )
            
            # Create NAT mappings configuration
            nat_mappings = None
            if static_mappings or identity_mappings:
                nat_mappings = models.DNat44ConfigurationItem(
                    label=nat_config.dnat.label if nat_config.dnat and nat_config.dnat.label else "nat-mappings",
                    static_mappings=static_mappings,
                    identity_mappings=identity_mappings
                )
            
            # Apply configuration to VPP
            configs_to_add = nat_interfaces + pool_addresses
            if nat_mappings:
                configs_to_add.append(nat_mappings)
            
            reply = self.connection.client.add_configuration(*configs_to_add)
            
            errors = self._extract_reply_errors(reply)
            if errors:
                for error in errors:
                    log.error(f"Error adding NAT configuration: {error}")
                return False
            
            # Store policy information for management
            policy_name = f"nat-{primary_lan.interface_name}-{primary_wan.interface_name}"
            self.active_policies[policy_name] = {
                'enabled': nat_config.enabled,
                'lan_interface': primary_lan.interface_name,
                'wan_interface': primary_wan.interface_name,
                'created_at': self._get_current_timestamp(),
                'nat_config': nat_config  # Store the full config for reference
            }

            log.info(f"NAT configuration '{policy_name}' applied successfully")
            return True
            
        except Exception as e:
            log.error(f"Exception configuring NAT: {e}")
            return False
    
    def remove_nat_configuration(self, lan_interface: Interface, wan_interface: Interface,
                                wg_ports_to_open: List[int], tcp_ports: List[int] = None,
                                udp_ports: List[int] = None) -> bool:
        """
        Remove NAT configuration.
        
        Args:
            lan_interface: LAN interface configuration
            wan_interface: WAN interface configuration
            wg_ports_to_open: WireGuard ports that were opened
            tcp_ports: TCP ports that were opened
            udp_ports: UDP ports that were opened
            
        Returns:
            bool: True if removal successful, False otherwise
        """
        try:
            tcp_ports = tcp_ports or []
            udp_ports = udp_ports or []
            
            policy_name = f"nat-{lan_interface.interface_name}-{wan_interface.interface_name}"
            
            log.info(f"Removing NAT configuration '{policy_name}'")
            
            # Find existing NAT configurations
            current_config = self.connection.client.get_configuration()
            
            nat_configs = [
                item.config
                for item in current_config.items
                if isinstance(item.config, models.Nat44InterfaceConfigurationItem)
                and item.config.name in [lan_interface.interface_name, wan_interface.interface_name]
            ]
            
            # Find port mappings to remove
            all_ports = set(wg_ports_to_open + tcp_ports + udp_ports)
            port_mappings = [
                item.config
                for item in current_config.items
                if isinstance(item.config, models.IdentityMapping)
                and item.config.port in all_ports
            ]
            
            if not nat_configs:
                log.warning("No NAT configuration found to remove")
                return True
            
            # Remove configurations from VPP
            configs_to_remove = nat_configs + port_mappings
            reply = self.connection.client.delete_configuration(*configs_to_remove)
            
            errors = self._extract_reply_errors(reply)
            if errors:
                for error in errors:
                    log.error(f"Error deleting NAT configuration: {error}")
                return False
            
            # Remove from active policies
            if policy_name in self.active_policies:
                del self.active_policies[policy_name]
            
            log.info(f"NAT configuration '{policy_name}' removed successfully")
            return True
            
        except Exception as e:
            log.error(f"Exception removing NAT configuration: {e}")
            return False
    
    # Implementation of SecurityManager abstract methods
    
    def create_policy(self, policy_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a NAT policy from configuration.
        
        Args:
            policy_config: NAT policy configuration dictionary or NatConfig object
            
        Returns:
            dict: Creation result
        """
        try:
            # If it's already a NatConfig object, use it directly
            if isinstance(policy_config, NatConfig):
                nat_config = policy_config
            else:
                # Convert dictionary to NatConfig object
                nat_config = NatConfig.from_dict(policy_config)
            
            # Configure NAT using the schema object
            success = self.configure_nat(nat_config)
            
            primary_wan = get_primary_interface(type='wan')
            primary_lan = get_primary_interface(type='lan')
            policy_name = f"nat-{primary_lan.interface_name}-{primary_wan.interface_name}"
            
            if success:
                return create_result_dict(
                    success=True,
                    data={'policy_name': policy_name, 'status': 'active'}
                )
            else:
                return create_result_dict(success=False, error="Failed to configure NAT")
                
        except Exception as e:
            log.error(f"Exception creating NAT policy: {e}")
            return create_result_dict(success=False, error=str(e))
    
    def apply_policy(self, policy_name: str) -> bool:
        """
        Apply a NAT policy by name.
        
        Args:
            policy_name: Name of policy to apply
            
        Returns:
            bool: True if applied successfully, False otherwise
        """
        if policy_name not in self.active_policies:
            log.error(f"NAT policy '{policy_name}' not found")
            return False
        
        # Policy is already applied when created in this implementation
        log.info(f"NAT policy '{policy_name}' is already active")
        return True
    
    def remove_policy(self, policy_name: str) -> bool:
        """
        Remove a NAT policy by name.
        
        Args:
            policy_name: Name of policy to remove
            
        Returns:
            bool: True if removed successfully, False otherwise
        """
        if policy_name not in self.active_policies:
            log.warning(f"NAT policy '{policy_name}' not found")
            return True
        
        try:
            policy = self.active_policies[policy_name]
            nat_config = policy.get('nat_config')
            
            # Get current VPP configuration
            current_config = self.connection.client.get_configuration()
            configs_to_remove = []
            
            # Find NAT interfaces to remove
            nat_interfaces = [
                item.config
                for item in current_config.items
                if isinstance(item.config, models.Nat44InterfaceConfigurationItem)
                and item.config.name in [policy['lan_interface'], policy['wan_interface']]
            ]
            configs_to_remove.extend(nat_interfaces)
            
            # Find address pools to remove
            if nat_config and nat_config.address_pools:
                pool_names = [pool.name or f"nat-pool-{i}" for i, pool in enumerate(nat_config.address_pools)]
                address_pools = [
                    item.config
                    for item in current_config.items
                    if isinstance(item.config, models.Nat44AddressPoolConfigurationItem)
                    and item.config.name in pool_names
                ]
                configs_to_remove.extend(address_pools)
            
            # Find DNAT mappings to remove
            if nat_config and nat_config.dnat:
                dnat_items = [
                    item.config
                    for item in current_config.items
                    if isinstance(item.config, models.DNat44ConfigurationItem)
                ]
                configs_to_remove.extend(dnat_items)
            
            if not configs_to_remove:
                log.warning(f"No configurations found to remove for policy '{policy_name}'")
                del self.active_policies[policy_name]
                return True
            
            # Remove configurations from VPP
            reply = self.connection.client.delete_configuration(*configs_to_remove)
            
            errors = self._extract_reply_errors(reply)
            if errors:
                for error in errors:
                    log.error(f"Error deleting NAT configuration: {error}")
                return False
            
            # Remove from active policies
            del self.active_policies[policy_name]
            
            log.info(f"NAT configuration '{policy_name}' removed successfully")
            return True
            
        except Exception as e:
            log.error(f"Exception removing NAT policy '{policy_name}': {e}")
            return False
    
    # Implementation of NetworkComponent abstract methods
    
    def create(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create NAT configuration from config."""
        return self.create_policy(config)
    
    def delete(self, identifier: str) -> bool:
        """Delete NAT policy by name."""
        return self.remove_policy(identifier)
    
    def get_status(self, identifier: str) -> Dict[str, Any]:
        """Get status of NAT policy."""
        if identifier in self.active_policies:
            policy = self.active_policies[identifier]
            nat_config = policy.get('nat_config')
            
            status = {
                'name': identifier,
                'status': 'active',
                'lan_interface': policy['lan_interface'],
                'wan_interface': policy['wan_interface'],
                'created_at': policy['created_at']
            }
            
            # Add NAT config details if available
            if nat_config:
                status['enabled'] = nat_config.enabled
                status['address_pools_count'] = len(nat_config.address_pools) if nat_config.address_pools else 0
                status['nat44_interfaces_count'] = len(nat_config.nat44_interfaces) if nat_config.nat44_interfaces else 0
                
                if nat_config.dnat:
                    status['static_mappings_count'] = len(nat_config.dnat.static_mappings) if nat_config.dnat.static_mappings else 0
                    status['identity_mappings_count'] = len(nat_config.dnat.identity_mappings) if nat_config.dnat.identity_mappings else 0
            
            return status
        else:
            return {'name': identifier, 'status': 'not_found'}
    
    def list_components(self) -> List[Dict[str, Any]]:
        """List all active NAT policies."""
        result = []
        for name, policy in self.active_policies.items():
            nat_config = policy.get('nat_config')
            component = {
                'name': name,
                'status': 'active',
                'lan_interface': policy['lan_interface'],
                'wan_interface': policy['wan_interface']
            }
            
            # Add counts if nat_config is available
            if nat_config:
                pool_count = len(nat_config.address_pools) if nat_config.address_pools else 0
                static_count = len(nat_config.dnat.static_mappings) if nat_config.dnat and nat_config.dnat.static_mappings else 0
                identity_count = len(nat_config.dnat.identity_mappings) if nat_config.dnat and nat_config.dnat.identity_mappings else 0
                component['mapping_count'] = static_count + identity_count
                component['pool_count'] = pool_count
            
            result.append(component)
        
        return result
    
    # Public utility methods
    
    def get_nat_statistics(self) -> Dict[str, Any]:
        """
        Get NAT statistics and session information.
        
        Returns:
            dict: NAT statistics
        """
        try:
            # Calculate statistics from active policies
            total_pools = 0
            total_static_mappings = 0
            total_identity_mappings = 0
            
            for policy in self.active_policies.values():
                nat_config = policy.get('nat_config')
                if nat_config:
                    total_pools += len(nat_config.address_pools) if nat_config.address_pools else 0
                    if nat_config.dnat:
                        total_static_mappings += len(nat_config.dnat.static_mappings) if nat_config.dnat.static_mappings else 0
                        total_identity_mappings += len(nat_config.dnat.identity_mappings) if nat_config.dnat.identity_mappings else 0
            
            return {
                'active_policies': len(self.active_policies),
                'policies': list(self.active_policies.keys()),
                'total_address_pools': total_pools,
                'total_static_mappings': total_static_mappings,
                'total_identity_mappings': total_identity_mappings,
                'total_mappings': total_static_mappings + total_identity_mappings
            }
            
        except Exception as e:
            log.error(f"Error getting NAT statistics: {e}")
            return {'error': str(e)}
    
    def verify_nat_configuration(self, policy_name: str) -> Dict[str, Any]:
        """
        Verify that a NAT policy is correctly configured in VPP.
        
        Args:
            policy_name: Name of the policy to verify
            
        Returns:
            dict: Verification results
        """
        if policy_name not in self.active_policies:
            return {'verified': False, 'error': 'Policy not found'}
        
        try:
            policy = self.active_policies[policy_name]
            nat_config = policy.get('nat_config')
            
            # Check if NAT interfaces are configured in VPP
            current_config = self.connection.client.get_configuration()
            
            nat_interfaces = [
                item.config
                for item in current_config.items
                if isinstance(item.config, models.Nat44InterfaceConfigurationItem)
                and item.config.name in [policy['lan_interface'], policy['wan_interface']]
            ]
            
            # Check address pools
            pool_count = 0
            if nat_config and nat_config.address_pools:
                address_pools = [
                    item.config
                    for item in current_config.items
                    if isinstance(item.config, models.Nat44AddressPoolConfigurationItem)
                ]
                pool_count = len(address_pools)
            
            # Check mappings
            static_mappings_count = 0
            identity_mappings_count = 0
            if nat_config and nat_config.dnat:
                static_mappings_count = len(nat_config.dnat.static_mappings) if nat_config.dnat.static_mappings else 0
                identity_mappings_count = len(nat_config.dnat.identity_mappings) if nat_config.dnat.identity_mappings else 0
            
            interfaces_ok = len(nat_interfaces) >= 1  # At least one interface should be configured
            pools_ok = pool_count >= len(nat_config.address_pools) if nat_config and nat_config.address_pools else True
            
            return {
                'verified': interfaces_ok and pools_ok,
                'interfaces_configured': interfaces_ok,
                'pools_configured': pools_ok,
                'interface_count': len(nat_interfaces),
                'pool_count': pool_count,
                'static_mappings_count': static_mappings_count,
                'identity_mappings_count': identity_mappings_count
            }
            
        except Exception as e:
            log.error(f"Error verifying NAT configuration for '{policy_name}': {e}")
            return {'verified': False, 'error': str(e)}
    
    # Private helper methods
    
    def _dict_to_interface(self, interface_config: Dict[str, Any]) -> Interface:
        """Convert dictionary to Interface object."""
        # This assumes your Interface class can be constructed from a dict
        # Adjust based on your actual Interface implementation
        return Interface(
            interface_name=interface_config.get('interface_name'),
            ip_address=interface_config.get('ip_address'),
            prefix_len=interface_config.get('prefix_len')
        )
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp as string."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _find_nat_interfaces_in_config(self, current_config, interface_names: List[str]) -> List:
        """Find NAT interface configurations in VPP config."""
        return [
            item.config
            for item in current_config.items
            if isinstance(item.config, models.Nat44InterfaceConfigurationItem)
            and item.config.name in interface_names
        ]
    
    def _find_port_mappings_in_config(self, current_config, ports: List[int]) -> List:
        """Find port mapping configurations in VPP config."""
        return [
            item.config
            for item in current_config.items
            if isinstance(item.config, models.IdentityMapping)
            and item.config.port in ports
        ]
