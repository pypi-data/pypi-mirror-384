"""
ACL (Access Control List) Configuration Manager

This module provides specialized management for ACL configurations,
implementing security management interfaces for network access control.
"""

from typing import List, Dict, Any, Optional
import ipaddress

from loguru import logger as log
from vpp_vrouter.common import models

from ..base_interfaces import SecurityManager, create_result_dict
from ..connection.vpp_connection import VPPConnectionManager
from ...core.base import Interface
from ...schemas.nat_acl_config import AclConfig
from ...core.config import get_primary_interface


class ACLManager(SecurityManager):
    """
    Manages ACL (Access Control List) configuration through VPP API.
    
    This class handles ACL rule creation, application to interfaces,
    and management of network access control policies.
    """
    
    def __init__(self, connection_manager: VPPConnectionManager):
        """
        Initialize the ACL manager.
        
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

    def configure_acl_from_config(self, acl_config) -> bool:
        """
        Configure ACL from AclConfig schema object or dict.
        
        Handles both VPP ACL format and simple firewall rule format.
        
        Args:
            acl_config: AclConfig schema object or dict containing ACL/firewall configuration
            
        Returns:
            bool: True if configuration successful, False otherwise
        """
        try:
            log.debug(f"Received ACL configuration: {acl_config}")
            log.debug(f"Type of acl_config: {type(acl_config)}")
            # Convert dict to AclConfig if needed
            if isinstance(acl_config, dict):
                log.debug(f"ACL config is dict, checking format. Has 'rules': {'rules' in acl_config}")
                # Check if this is a simple firewall format or VPP ACL format
                if 'rules' in acl_config and acl_config.get('rules'):
                    first_rule = acl_config['rules'][0] if isinstance(acl_config['rules'], list) and len(acl_config['rules']) > 0 else {}
                    log.debug(f"First rule keys: {list(first_rule.keys()) if first_rule else 'None'}")
                    # Simple firewall format has 'name', 'action', 'protocol', 'source_ip', 'destination_ip'
                    # VPP ACL format has 'action', 'refinement' with nested structure
                    if 'source_ip' in first_rule or 'destination_ip' in first_rule:
                        # Convert simple firewall format to VPP ACL format
                        log.info("Converting simple firewall rules to VPP ACL format")
                        acl_config = self._convert_firewall_to_acl_config(acl_config)
                    else:
                        # Already in VPP format, use convert_acl_config utility
                        log.debug("Using convert_acl_config for VPP format")
                        from vrouter_agent.schemas.nat_acl_config import convert_acl_config
                        acl_config = convert_acl_config(acl_config)
                else:
                    log.debug("No rules or rules is not a list, using convert_acl_config")
                    from vrouter_agent.schemas.nat_acl_config import convert_acl_config
                    acl_config = convert_acl_config(acl_config)
            
            if not acl_config.enabled:
                log.info("ACL configuration is disabled, skipping")
                return True

            log.info(f"Starting ACL configuration: {acl_config.name}")
            
            # Validate that ACL will be applied to at least one interface
            if not acl_config.ingress_interfaces and not acl_config.egress_interfaces:
                log.error(f"ACL configuration '{acl_config.name}' has no interfaces specified. "
                         "ACL rules will not be applied to any traffic. Please specify ingress_interfaces or egress_interfaces.")
                return False

            # Convert schema ACL rules to VPP models
            vpp_rules = []
            for schema_rule in acl_config.rules:
                # Convert ACLAction enum to VPP models.ACLAction
                action = models.ACLAction.PERMIT if schema_rule.action.value == "permit" else models.ACLAction.DENY
                
                # Convert IPSpecification
                refinement = None
                if schema_rule.refinement:
                    ref = schema_rule.refinement
                    
                    # Convert IP addresses
                    addresses = None
                    if ref.addresses:
                        addresses = models.IPAddresses(
                            source_network=ipaddress.IPv4Network(ref.addresses.source_network) if ref.addresses.source_network else None,
                            destination_network=ipaddress.IPv4Network(ref.addresses.destination_network) if ref.addresses.destination_network else None
                        )
                    
                    # Convert protocol specification
                    protocol = None
                    if ref.protocol:
                        proto = ref.protocol
                        # Determine protocol type and convert accordingly
                        if hasattr(proto, 'source_port_range'):  # TCP or UDP
                            port_range_class = models.PortRange
                            if proto.__class__.__name__ == 'TCPProtocol':
                                protocol = models.TCPProtocol(
                                    source_port_range=port_range_class(
                                        lower_port=proto.source_port_range.lower_port,
                                        upper_port=proto.source_port_range.upper_port
                                    ) if proto.source_port_range else None,
                                    destination_port_range=port_range_class(
                                        lower_port=proto.destination_port_range.lower_port,
                                        upper_port=proto.destination_port_range.upper_port
                                    ) if proto.destination_port_range else None
                                )
                            elif proto.__class__.__name__ == 'UDPProtocol':
                                protocol = models.UDPProtocol(
                                    source_port_range=port_range_class(
                                        lower_port=proto.source_port_range.lower_port,
                                        upper_port=proto.source_port_range.upper_port
                                    ) if proto.source_port_range else None,
                                    destination_port_range=port_range_class(
                                        lower_port=proto.destination_port_range.lower_port,
                                        upper_port=proto.destination_port_range.upper_port
                                    ) if proto.destination_port_range else None
                                )
                        elif hasattr(proto, 'icmpv6'):  # ICMP
                            protocol = models.ICMPProtocol(icmpv6=proto.icmpv6)
                        elif hasattr(proto, 'protocol'):  # Other
                            protocol = models.OtherProtocol(protocol=proto.protocol)
                    
                    # Create IP specification
                    if addresses or protocol:
                        refinement = models.IPSpecification(
                            addresses=addresses,
                            protocol=protocol
                        )
                
                # Create VPP ACL rule
                vpp_rule = models.ACLRuleConfigurationItem(
                    action=action,
                    refinement=refinement
                )
                vpp_rules.append(vpp_rule)
            
            # Create VPP ACL configuration
            vpp_acl_config = models.ACLConfigurationItem(
                name=acl_config.name,
                ingress=acl_config.ingress_interfaces if acl_config.ingress_interfaces else [],
                egress=acl_config.egress_interfaces if acl_config.egress_interfaces else [],
                rules=vpp_rules,
            )
            
            # Log the configuration details
            log.info(f"Applying ACL '{acl_config.name}' with {len(vpp_rules)} rules")
            if acl_config.ingress_interfaces:
                log.info(f"  Ingress interfaces: {', '.join(acl_config.ingress_interfaces)}")
            if acl_config.egress_interfaces:
                log.info(f"  Egress interfaces: {', '.join(acl_config.egress_interfaces)}")
            
            # Apply configuration to VPP
            reply = self.connection.client.add_configuration(vpp_acl_config)
            
            errors = self._extract_reply_errors(reply)
            if errors:
                for error in errors:
                    log.error(f"Error adding ACL configuration: {error}")
                return False
            
            # Store policy information
            self.active_policies[acl_config.name] = {
                'ingress_interfaces': acl_config.ingress_interfaces,
                'egress_interfaces': acl_config.egress_interfaces,
                'rule_count': len(vpp_rules),
                'created_at': self._get_current_timestamp(),
                'acl_config': acl_config  # Store the full config for reference
            }
            
            log.info(f"ACL configuration '{acl_config.name}' applied successfully with {len(vpp_rules)} rules")
            return True
            
        except Exception as e:
            log.error(f"Exception configuring ACL from config: {e}")
            import traceback
            log.error(traceback.format_exc())
            return False

    def configure_acl(self, ingress_interface: Interface, deny_network: str,
                     additional_rules: List[Dict[str, Any]] = None) -> bool:
        """
        Configure ACL with basic deny rule and optional additional rules.
        
        Args:
            ingress_interface: Interface to apply ACL to
            deny_network: Network to deny (CIDR notation)
            additional_rules: Optional list of additional ACL rules
            
        Returns:
            bool: True if configuration successful, False otherwise
        """
        try:
            policy_name = f"acl-{ingress_interface.interface_name}"
            additional_rules = additional_rules or []
            
            log.info(f"Configuring ACL policy '{policy_name}' on {ingress_interface.interface_name}")
            
            # Create ACL rules
            rules = []
            
            # Add deny rule for specified network
            rules.append(
                models.ACLRuleConfigurationItem(
                    action=models.ACLAction.DENY,
                    refinement=models.IPSpecification(
                        addresses=models.IPAddresses(
                            destination_network=ipaddress.IPv4Network(deny_network)
                        )
                    ),
                )
            )
            
            # Add additional custom rules
            for rule_config in additional_rules:
                rule = self._create_acl_rule_from_config(rule_config)
                if rule:
                    rules.append(rule)
            
            # Add final permit-all rule (standard practice)
            rules.append(
                models.ACLRuleConfigurationItem(
                    action=models.ACLAction.PERMIT,
                )
            )
            
            # Create ACL configuration
            acl_config = models.ACLConfigurationItem(
                name=policy_name,
                ingress=[ingress_interface.interface_name],
                rules=rules,
            )
            
            # Apply configuration to VPP
            reply = self.connection.client.add_configuration(acl_config)
            
            errors = self._extract_reply_errors(reply)
            if errors:
                for error in errors:
                    log.error(f"Error adding ACL configuration: {error}")
                return False
            
            # Store policy information
            self.active_policies[policy_name] = {
                'interface': ingress_interface.interface_name,
                'deny_network': deny_network,
                'additional_rules': additional_rules,
                'rule_count': len(rules),
                'created_at': self._get_current_timestamp()
            }
            
            log.info(f"ACL policy '{policy_name}' applied successfully with {len(rules)} rules")
            return True
            
        except Exception as e:
            log.error(f"Exception configuring ACL: {e}")
            return False
    
    def remove_acl_configuration(self, interface: Interface) -> bool:
        """
        Remove ACL configuration from an interface.
        
        Args:
            interface: Interface to remove ACL from
            
        Returns:
            bool: True if removal successful, False otherwise
        """
        try:
            policy_name = f"acl-{interface.interface_name}"
            
            log.info(f"Removing ACL configuration '{policy_name}'")
            
            # Find existing ACL configuration
            current_config = self.connection.client.get_configuration()
            
            acl_configs = [
                item.config
                for item in current_config.items
                if isinstance(item.config, models.ACLConfigurationItem)
                and item.config.ingress == [interface.interface_name]
            ]
            
            if not acl_configs:
                log.warning(f"No ACL configuration found for interface {interface.interface_name}")
                return True
            
            # Remove configurations from VPP
            reply = self.connection.client.delete_configuration(*acl_configs)
            
            errors = self._extract_reply_errors(reply)
            if errors:
                for error in errors:
                    log.error(f"Error deleting ACL configuration: {error}")
                return False
            
            # Remove from active policies
            if policy_name in self.active_policies:
                del self.active_policies[policy_name]
            
            log.info(f"ACL configuration '{policy_name}' removed successfully")
            return True
            
        except Exception as e:
            log.error(f"Exception removing ACL configuration: {e}")
            return False
    
    def add_acl_rule(self, policy_name: str, rule_config: Dict[str, Any]) -> bool:
        """
        Add a new rule to an existing ACL policy.
        
        Args:
            policy_name: Name of the ACL policy
            rule_config: Configuration for the new rule
            
        Returns:
            bool: True if rule added successfully, False otherwise
        """
        try:
            if policy_name not in self.active_policies:
                log.error(f"ACL policy '{policy_name}' not found")
                return False
            
            # This would require rebuilding the entire ACL with the new rule
            # For simplicity, we'll return not implemented for now
            log.warning("Adding individual ACL rules not yet implemented")
            return False
            
        except Exception as e:
            log.error(f"Exception adding ACL rule: {e}")
            return False
    
    def remove_acl_rule(self, policy_name: str, rule_index: int) -> bool:
        """
        Remove a rule from an existing ACL policy.
        
        Args:
            policy_name: Name of the ACL policy
            rule_index: Index of the rule to remove
            
        Returns:
            bool: True if rule removed successfully, False otherwise
        """
        try:
            if policy_name not in self.active_policies:
                log.error(f"ACL policy '{policy_name}' not found")
                return False
            
            # This would require rebuilding the entire ACL without the rule
            # For simplicity, we'll return not implemented for now
            log.warning("Removing individual ACL rules not yet implemented")
            return False
            
        except Exception as e:
            log.error(f"Exception removing ACL rule: {e}")
            return False
    
    # Implementation of SecurityManager abstract methods
    
    def create_policy(self, policy_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an ACL policy from configuration.
        
        Args:
            policy_config: ACL policy configuration
            
        Returns:
            dict: Creation result
        """
        try:
            # Extract configuration parameters
            interface_config = policy_config.get('interface')
            deny_network = policy_config.get('deny_network')
            additional_rules = policy_config.get('additional_rules', [])
            
            if not interface_config:
                return create_result_dict(
                    success=False, 
                    error="Missing required interface configuration"
                )
            
            if not deny_network:
                return create_result_dict(
                    success=False, 
                    error="Missing required deny_network parameter"
                )
            
            # Convert to Interface object
            interface = self._dict_to_interface(interface_config)
            
            # Configure ACL
            success = self.configure_acl(
                ingress_interface=interface,
                deny_network=deny_network,
                additional_rules=additional_rules
            )
            
            policy_name = f"acl-{interface.interface_name}"
            
            if success:
                return create_result_dict(
                    success=True,
                    data={'policy_name': policy_name, 'status': 'active'}
                )
            else:
                return create_result_dict(success=False, error="Failed to configure ACL")
                
        except Exception as e:
            log.error(f"Exception creating ACL policy: {e}")
            return create_result_dict(success=False, error=str(e))
    
    def apply_policy(self, policy_name: str) -> bool:
        """
        Apply an ACL policy by name.
        
        Args:
            policy_name: Name of policy to apply
            
        Returns:
            bool: True if applied successfully, False otherwise
        """
        if policy_name not in self.active_policies:
            log.error(f"ACL policy '{policy_name}' not found")
            return False
        
        # Policy is already applied when created in this implementation
        log.info(f"ACL policy '{policy_name}' is already active")
        return True
    
    def remove_policy(self, policy_name: str) -> bool:
        """
        Remove an ACL policy by name.
        
        Args:
            policy_name: Name of policy to remove
            
        Returns:
            bool: True if removed successfully, False otherwise
        """
        if policy_name not in self.active_policies:
            log.warning(f"ACL policy '{policy_name}' not found")
            return True
        
        try:
            policy = self.active_policies[policy_name]
            
            # Create Interface object from stored data
            interface = Interface(interface_name=policy['interface'])
            
            # Remove the ACL configuration
            success = self.remove_acl_configuration(interface)
            
            return success
            
        except Exception as e:
            log.error(f"Exception removing ACL policy '{policy_name}': {e}")
            return False
    
    # Implementation of NetworkComponent abstract methods
    
    def create(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create ACL configuration from config."""
        return self.create_policy(config)
    
    def delete(self, identifier: str) -> bool:
        """Delete ACL policy by name."""
        return self.remove_policy(identifier)
    
    def get_status(self, identifier: str) -> Dict[str, Any]:
        """Get status of ACL policy."""
        if identifier in self.active_policies:
            policy = self.active_policies[identifier]
            return {
                'name': identifier,
                'status': 'active',
                'interface': policy['interface'],
                'deny_network': policy['deny_network'],
                'rule_count': policy['rule_count'],
                'created_at': policy['created_at']
            }
        else:
            return {'name': identifier, 'status': 'not_found'}
    
    def list_components(self) -> List[Dict[str, Any]]:
        """List all active ACL policies."""
        return [
            {
                'name': name,
                'status': 'active',
                'interface': policy['interface'],
                'deny_network': policy['deny_network'],
                'rule_count': policy['rule_count']
            }
            for name, policy in self.active_policies.items()
        ]
    
    # Public utility methods
    
    def get_acl_statistics(self) -> Dict[str, Any]:
        """
        Get ACL statistics and hit counts.
        
        Returns:
            dict: ACL statistics
        """
        try:
            # This would implement actual ACL statistics retrieval from VPP
            # For now, return basic information
            return {
                'active_policies': len(self.active_policies),
                'policies': list(self.active_policies.keys()),
                'total_rules': sum(
                    policy['rule_count'] for policy in self.active_policies.values()
                ),
                'interfaces_protected': len(set(
                    policy['interface'] for policy in self.active_policies.values()
                ))
            }
            
        except Exception as e:
            log.error(f"Error getting ACL statistics: {e}")
            return {'error': str(e)}
    
    def verify_acl_configuration(self, policy_name: str) -> Dict[str, Any]:
        """
        Verify that an ACL policy is correctly configured in VPP.
        
        Args:
            policy_name: Name of the policy to verify
            
        Returns:
            dict: Verification results
        """
        if policy_name not in self.active_policies:
            return {'verified': False, 'error': 'Policy not found'}
        
        try:
            policy = self.active_policies[policy_name]
            
            # Check if ACL is configured in VPP
            current_config = self.connection.client.get_configuration()
            
            acl_configs = [
                item.config
                for item in current_config.items
                if isinstance(item.config, models.ACLConfigurationItem)
                and item.config.ingress == [policy['interface']]
                and item.config.name == policy_name
            ]
            
            acl_exists = len(acl_configs) > 0
            rule_count_matches = False
            
            if acl_exists:
                actual_rule_count = len(acl_configs[0].rules) if acl_configs[0].rules else 0
                rule_count_matches = actual_rule_count == policy['rule_count']
            
            return {
                'verified': acl_exists and rule_count_matches,
                'acl_exists': acl_exists,
                'rule_count_matches': rule_count_matches,
                'expected_rules': policy['rule_count'],
                'actual_rules': len(acl_configs[0].rules) if acl_exists and acl_configs[0].rules else 0
            }
            
        except Exception as e:
            log.error(f"Error verifying ACL configuration for '{policy_name}': {e}")
            return {'verified': False, 'error': str(e)}
    
    def create_advanced_acl_policy(self, policy_name: str, interface_name: str, 
                                  rules: List[Dict[str, Any]]) -> bool:
        """
        Create an advanced ACL policy with custom rules.
        
        Args:
            policy_name: Name for the new policy
            interface_name: Interface to apply ACL to
            rules: List of rule configurations
            
        Returns:
            bool: True if policy created successfully, False otherwise
        """
        try:
            log.info(f"Creating advanced ACL policy '{policy_name}' on {interface_name}")
            
            # Convert rule configurations to ACL rule objects
            acl_rules = []
            for rule_config in rules:
                rule = self._create_acl_rule_from_config(rule_config)
                if rule:
                    acl_rules.append(rule)
            
            # Create ACL configuration
            acl_config = models.ACLConfigurationItem(
                name=policy_name,
                ingress=[interface_name],
                rules=acl_rules,
            )
            
            # Apply configuration to VPP
            reply = self.connection.client.add_configuration(acl_config)
            
            errors = self._extract_reply_errors(reply)
            if errors:
                log.error(f"Error adding advanced ACL configuration: {'; '.join(errors)}")
                return False
            
            # Store policy information
            self.active_policies[policy_name] = {
                'interface': interface_name,
                'custom_rules': rules,
                'rule_count': len(acl_rules),
                'type': 'advanced',
                'created_at': self._get_current_timestamp()
            }
            
            log.info(f"Advanced ACL policy '{policy_name}' created successfully")
            return True
            
        except Exception as e:
            log.error(f"Exception creating advanced ACL policy: {e}")
            return False
    
    # Private helper methods
    
    def _create_acl_rule_from_config(self, rule_config: Dict[str, Any]) -> Optional[models.ACLRuleConfigurationItem]:
        """
        Create an ACL rule from configuration dictionary.
        
        Args:
            rule_config: Rule configuration
            
        Returns:
            Optional[ACLRuleConfigurationItem]: ACL rule object or None if invalid
        """
        try:
            action_str = rule_config.get('action', 'permit').upper()
            action = models.ACLAction.PERMIT if action_str == 'PERMIT' else models.ACLAction.DENY
            
            # Basic rule without refinement
            if not rule_config.get('refinement'):
                return models.ACLRuleConfigurationItem(action=action)
            
            refinement_config = rule_config['refinement']
            
            # Create IP specification if provided
            ip_spec = None
            if refinement_config.get('ip'):
                ip_config = refinement_config['ip']
                addresses = models.IPAddresses()
                
                if ip_config.get('source_network'):
                    addresses.source_network = ipaddress.IPv4Network(ip_config['source_network'])
                
                if ip_config.get('destination_network'):
                    addresses.destination_network = ipaddress.IPv4Network(ip_config['destination_network'])
                
                ip_spec = models.IPSpecification(addresses=addresses)
            
            return models.ACLRuleConfigurationItem(
                action=action,
                refinement=ip_spec
            )
            
        except Exception as e:
            log.error(f"Error creating ACL rule from config: {e}")
            return None
    
    def _convert_firewall_to_acl_config(self, firewall_config: Dict[str, Any]):
        """Convert simple firewall rule format to VPP ACL format.
        
        Args:
            firewall_config: Dictionary with 'rules' and 'global_settings'
            
        Returns:
            AclConfig object compatible with VPP
        """
        from vrouter_agent.schemas.nat_acl_config import (
            AclConfig, ACLRule, ACLAction, IPSpecification, IPAddresses,
            TCPProtocol, UDPProtocol, ICMPProtocol, OtherProtocol, PortRange
        )
        
        rules_data = firewall_config.get('rules', [])
        global_settings = firewall_config.get('global_settings', {})
        
        acl_rules = []
        
        for rule_data in rules_data:
            if not rule_data.get('enabled', True):
                log.debug(f"Skipping disabled rule: {rule_data.get('name')}")
                continue
            
            # Map action
            action_str = rule_data.get('action', 'deny').lower()
            action = ACLAction.PERMIT if action_str == 'permit' or action_str == 'allow' else ACLAction.DENY
            
            # Build IP addresses
            source_ip = rule_data.get('source_ip', '').strip()
            dest_ip = rule_data.get('destination_ip', '').strip()
            
            # Convert single IPs to CIDR notation
            source_network = f"{source_ip}/32" if source_ip and '/' not in source_ip else (source_ip or "0.0.0.0/0")
            dest_network = f"{dest_ip}/32" if dest_ip and '/' not in dest_ip else (dest_ip or "0.0.0.0/0")
            
            addresses = IPAddresses(
                source_network=source_network,
                destination_network=dest_network
            )
            
            # Build protocol specification
            protocol_str = rule_data.get('protocol', '').lower()
            source_port = rule_data.get('source_port', '')
            dest_port = rule_data.get('destination_port', '')
            
            protocol_spec = None
            
            if protocol_str == 'tcp':
                # Parse port ranges
                src_lower, src_upper = self._parse_port_range(source_port)
                dst_lower, dst_upper = self._parse_port_range(dest_port)
                
                protocol_spec = TCPProtocol(
                    source_port_range=PortRange(lower_port=src_lower, upper_port=src_upper),
                    destination_port_range=PortRange(lower_port=dst_lower, upper_port=dst_upper)
                )
            elif protocol_str == 'udp':
                src_lower, src_upper = self._parse_port_range(source_port)
                dst_lower, dst_upper = self._parse_port_range(dest_port)
                
                protocol_spec = UDPProtocol(
                    source_port_range=PortRange(lower_port=src_lower, upper_port=src_upper),
                    destination_port_range=PortRange(lower_port=dst_lower, upper_port=dst_upper)
                )
            elif protocol_str == 'icmp':
                protocol_spec = ICMPProtocol(icmpv6=False)
            else:
                # Other protocol or any
                protocol_number = self._get_protocol_number(protocol_str)
                protocol_spec = OtherProtocol(protocol=protocol_number)
            
            # Create IP specification
            ip_spec = IPSpecification(
                addresses=addresses,
                protocol=protocol_spec
            )
            
            # Create ACL rule
            acl_rule = ACLRule(
                action=action,
                refinement=ip_spec
            )
            
            acl_rules.append(acl_rule)
            log.info(f"Converted ACL rule '{rule_data.get('name')}': {action_str} {protocol_str} "
                    f"{source_network} -> {dest_network}")
        
        # Determine interfaces to apply ACL to
        primary_wan = get_primary_interface(type='wan')
        primary_lan = get_primary_interface(type='lan')
        
        if not primary_wan:
            log.error("Cannot apply ACL: Primary WAN interface not found")
            raise ValueError("Primary WAN interface not found")
        
        if not primary_lan:
            log.warning("Primary LAN interface not found, will use WAN for both directions")
        
        log.debug(f"Primary WAN interface: {primary_wan.interface_name}")
        log.debug(f"Primary LAN interface: {primary_lan.interface_name if primary_lan else 'None'}")
        
        # Apply ACL based on direction (only process enabled rules)
        # Default: ingress=LAN (traffic from LAN), egress=WAN (traffic to WAN)
        ingress_interfaces = []
        egress_interfaces = []
        
        for rule_data in rules_data:
            # Skip disabled rules
            if not rule_data.get('enabled', True):
                continue
                
            direction = rule_data.get('direction', 'inbound').lower()
            log.debug(f"Processing rule '{rule_data.get('name')}' with direction: {direction}")
            
            if direction == 'inbound' or direction == 'ingress':
                # Inbound = traffic coming FROM LAN (apply ACL on LAN interface ingress)
                if primary_lan:
                    if primary_lan.interface_name not in ingress_interfaces:
                        ingress_interfaces.append(primary_lan.interface_name)
                        log.debug(f"Added {primary_lan.interface_name} to ingress interfaces")
                else:
                    # Fallback to WAN if LAN not available
                    if primary_wan.interface_name not in ingress_interfaces:
                        ingress_interfaces.append(primary_wan.interface_name)
                        log.debug(f"Added {primary_wan.interface_name} to ingress interfaces (fallback)")
            elif direction == 'outbound' or direction == 'egress':
                # Outbound = traffic going TO WAN (apply ACL on WAN interface egress)
                if primary_wan.interface_name not in egress_interfaces:
                    egress_interfaces.append(primary_wan.interface_name)
                    log.debug(f"Added {primary_wan.interface_name} to egress interfaces")
            else:
                # Both directions or unknown - apply on both LAN ingress and WAN egress
                log.warning(f"Unknown direction '{direction}' for rule '{rule_data.get('name')}', applying to both directions")
                if primary_lan:
                    if primary_lan.interface_name not in ingress_interfaces:
                        ingress_interfaces.append(primary_lan.interface_name)
                        log.debug(f"Added {primary_lan.interface_name} to ingress interfaces (both)")
                if primary_wan.interface_name not in egress_interfaces:
                    egress_interfaces.append(primary_wan.interface_name)
                    log.debug(f"Added {primary_wan.interface_name} to egress interfaces (both)")
        
        log.info(f"ACL will be applied to ingress interfaces: {ingress_interfaces}")
        log.info(f"ACL will be applied to egress interfaces: {egress_interfaces}")
        
        # Create ACL config
        acl_config = AclConfig(
            enabled=True,
            name="firewall-rules",
            rules=acl_rules,
            ingress_interfaces=ingress_interfaces,
            egress_interfaces=egress_interfaces
        )
        
        log.info(f"Converted {len(acl_rules)} firewall rules to VPP ACL format")
        return acl_config
    
    def _parse_port_range(self, port_spec: str) -> tuple:
        """Parse port specification into lower and upper bounds.
        
        Args:
            port_spec: Port specification (empty, single port, or range like "80-443")
            
        Returns:
            Tuple of (lower_port, upper_port)
        """
        if not port_spec or port_spec.strip() == '':
            return (0, 65535)
        
        port_spec = port_spec.strip()
        
        if '-' in port_spec:
            parts = port_spec.split('-')
            try:
                lower = int(parts[0].strip())
                upper = int(parts[1].strip())
                return (lower, upper)
            except (ValueError, IndexError):
                return (0, 65535)
        else:
            try:
                port = int(port_spec)
                return (port, port)
            except ValueError:
                return (0, 65535)
    
    def _get_protocol_number(self, protocol_str: str) -> int:
        """Get IP protocol number from protocol name.
        
        Args:
            protocol_str: Protocol name (tcp, udp, icmp, etc.)
            
        Returns:
            IP protocol number
        """
        protocol_map = {
            'tcp': 6,
            'udp': 17,
            'icmp': 1,
            'icmpv6': 58,
            'igmp': 2,
            'esp': 50,
            'ah': 51,
            'gre': 47,
            'any': 0
        }
        return protocol_map.get(protocol_str.lower(), 0)
    
    def _dict_to_interface(self, interface_config: Dict[str, Any]) -> Interface:
        """Convert dictionary to Interface object."""
        return Interface(
            interface_name=interface_config.get('interface_name'),
            ip_address=interface_config.get('ip_address'),
            prefix_len=interface_config.get('prefix_len')
        )
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp as string."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _find_acl_configs_in_vpp(self, current_config, interface_name: str) -> List:
        """Find ACL configurations for a specific interface in VPP config."""
        return [
            item.config
            for item in current_config.items
            if isinstance(item.config, models.ACLConfigurationItem)
            and interface_name in item.config.ingress
        ]
