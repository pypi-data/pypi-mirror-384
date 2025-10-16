"""
Base interfaces and abstract classes for VRouter component management.

This module defines the common interfaces that all VRouter components should implement,
promoting consistency and enabling polymorphic behavior across different managers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from enum import Enum


class ComponentStatus(Enum):
    """Status enumeration for network components."""
    UNKNOWN = "unknown"
    CREATING = "creating"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    REMOVING = "removing"


class NetworkComponent(ABC):
    """
    Base interface for all network components in the VRouter system.
    
    This abstract base class defines the minimum interface that all
    network components (tunnels, interfaces, routes, etc.) should implement.
    """
    
    @abstractmethod
    def create(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a network component from configuration.
        
        Args:
            config: Configuration dictionary for the component
            
        Returns:
            dict: Result dictionary with 'success' boolean and additional data
        """
        pass
    
    @abstractmethod
    def delete(self, identifier: str) -> bool:
        """
        Delete a network component by identifier.
        
        Args:
            identifier: Unique identifier for the component
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_status(self, identifier: str) -> Dict[str, Any]:
        """
        Get status information for a component.
        
        Args:
            identifier: Unique identifier for the component
            
        Returns:
            dict: Status information including health, configuration, etc.
        """
        pass
    
    @abstractmethod
    def list_components(self) -> List[Dict[str, Any]]:
        """
        List all components managed by this manager.
        
        Returns:
            List[dict]: List of component information dictionaries
        """
        pass


class TunnelManager(NetworkComponent):
    """
    Interface for tunnel management components.
    
    Extends NetworkComponent with tunnel-specific operations for
    creating, managing, and monitoring network tunnels.
    """
    
    @abstractmethod
    def create_tunnels(self, configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create multiple tunnels from configuration list.
        
        Args:
            configs: List of tunnel configuration dictionaries
            
        Returns:
            dict: Result with 'success', 'tunnels' list, and 'interfaces' data
        """
        pass
    
    @abstractmethod
    def remove_tunnels(self, tunnel_names: Optional[List[str]] = None) -> bool:
        """
        Remove tunnels by name or all if none specified.
        
        Args:
            tunnel_names: Optional list of tunnel names to remove
            
        Returns:
            bool: True if all removals successful, False otherwise
        """
        pass
    
    @abstractmethod
    def verify_tunnels(self, tunnel_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Verify operational status of tunnels.
        
        Args:
            tunnel_names: Optional list of tunnel names to verify
            
        Returns:
            List[dict]: List of tunnel status dictionaries
        """
        pass
    
    @abstractmethod
    def get_tunnel_info(self, tunnel_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific tunnel.
        
        Args:
            tunnel_name: Name of the tunnel
            
        Returns:
            Optional[dict]: Tunnel information or None if not found
        """
        pass


class RoutingManager(NetworkComponent):
    """
    Interface for routing management components.
    
    Handles route creation, deletion, and management for both
    VPP and Linux routing tables.
    """
    
    @abstractmethod
    def add_route(self, destination: str, next_hop: str, interface: str, 
                  **kwargs) -> bool:
        """
        Add a route to the routing table.
        
        Args:
            destination: Destination network (CIDR notation)
            next_hop: Next hop IP address
            interface: Outgoing interface name
            **kwargs: Additional route parameters
            
        Returns:
            bool: True if route added successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def remove_route(self, destination: str, next_hop: Optional[str] = None,
                     interface: Optional[str] = None) -> bool:
        """
        Remove a route from the routing table.
        
        Args:
            destination: Destination network to remove
            next_hop: Optional next hop to match
            interface: Optional interface to match
            
        Returns:
            bool: True if route removed successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def get_routes(self, destination: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get routes from the routing table.
        
        Args:
            destination: Optional destination filter
            
        Returns:
            List[dict]: List of route information dictionaries
        """
        pass


class InterfaceManager(NetworkComponent):
    """
    Interface for network interface management.
    
    Handles interface creation, configuration, monitoring,
    and status checking.
    """
    
    @abstractmethod
    def create_interface(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a network interface.
        
        Args:
            config: Interface configuration
            
        Returns:
            dict: Creation result with interface details
        """
        pass
    
    @abstractmethod
    def configure_interface(self, interface_name: str, 
                           config: Dict[str, Any]) -> bool:
        """
        Configure an existing interface.
        
        Args:
            interface_name: Name of interface to configure
            config: Configuration parameters
            
        Returns:
            bool: True if configuration successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_interface_status(self, interface_name: str) -> Dict[str, Any]:
        """
        Get detailed status of an interface.
        
        Args:
            interface_name: Name of the interface
            
        Returns:
            dict: Interface status and configuration details
        """
        pass
    
    @abstractmethod
    def is_interface_up(self, interface_name: str) -> bool:
        """
        Check if an interface is operationally up.
        
        Args:
            interface_name: Name of the interface
            
        Returns:
            bool: True if interface is up, False otherwise
        """
        pass


class MonitoringComponent(ABC):
    """
    Interface for monitoring and testing components.
    
    Defines methods for connectivity testing, performance monitoring,
    and health checks.
    """
    
    @abstractmethod
    def test_connectivity(self, target: str, **kwargs) -> Dict[str, Any]:
        """
        Test network connectivity to a target.
        
        Args:
            target: Target IP address or hostname
            **kwargs: Additional test parameters
            
        Returns:
            dict: Connectivity test results
        """
        pass
    
    @abstractmethod
    def monitor_performance(self, targets: List[str], 
                           duration: float = 60.0) -> Dict[str, Any]:
        """
        Monitor network performance to targets.
        
        Args:
            targets: List of target addresses
            duration: Monitoring duration in seconds
            
        Returns:
            dict: Performance monitoring results
        """
        pass
    
    @abstractmethod
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get overall health status of monitored components.
        
        Returns:
            dict: Health status summary
        """
        pass


class ConfigurationManager(ABC):
    """
    Interface for configuration management components.
    
    Handles loading, validation, and application of configurations.
    """
    
    @abstractmethod
    def load_configuration(self, config_data: Union[str, Dict[str, Any]]) -> bool:
        """
        Load configuration from string or dictionary.
        
        Args:
            config_data: Configuration data
            
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def validate_configuration(self, config_data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate configuration syntax and semantics.
        
        Args:
            config_data: Configuration to validate
            
        Returns:
            dict: Validation results with errors and warnings
        """
        pass
    
    @abstractmethod
    def apply_configuration(self) -> bool:
        """
        Apply the loaded configuration.
        
        Returns:
            bool: True if applied successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def get_current_configuration(self) -> Dict[str, Any]:
        """
        Get the current active configuration.
        
        Returns:
            dict: Current configuration data
        """
        pass


class SecurityManager(NetworkComponent):
    """
    Interface for security-related components (NAT, ACL, Firewall).
    
    Handles security policy creation, modification, and enforcement.
    """
    
    @abstractmethod
    def create_policy(self, policy_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a security policy.
        
        Args:
            policy_config: Policy configuration
            
        Returns:
            dict: Creation result
        """
        pass
    
    @abstractmethod
    def apply_policy(self, policy_name: str) -> bool:
        """
        Apply a security policy.
        
        Args:
            policy_name: Name of policy to apply
            
        Returns:
            bool: True if applied successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def remove_policy(self, policy_name: str) -> bool:
        """
        Remove a security policy.
        
        Args:
            policy_name: Name of policy to remove
            
        Returns:
            bool: True if removed successfully, False otherwise
        """
        pass


# Utility functions for working with components

def validate_component_config(config: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
    """
    Validate that a component configuration has required fields.
    
    Args:
        config: Configuration dictionary to validate
        required_fields: List of required field names
        
    Returns:
        dict: Validation result with 'valid' boolean and 'errors' list
    """
    errors = []
    
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")
        elif config[field] is None:
            errors.append(f"Field '{field}' cannot be None")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


def create_result_dict(success: bool, data: Any = None, error: str = None, 
                      warnings: List[str] = None) -> Dict[str, Any]:
    """
    Create a standardized result dictionary.
    
    Args:
        success: Whether the operation was successful
        data: Optional data to include in result
        error: Optional error message
        warnings: Optional list of warning messages
        
    Returns:
        dict: Standardized result dictionary
    """
    result = {'success': success}
    
    if data is not None:
        result['data'] = data
    
    if error:
        result['error'] = error
    
    if warnings:
        result['warnings'] = warnings
    
    return result
