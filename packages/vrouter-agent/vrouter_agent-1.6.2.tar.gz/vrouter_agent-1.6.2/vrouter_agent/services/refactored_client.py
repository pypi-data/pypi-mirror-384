"""
Refactored VRouter Client - Facade Pattern Implementation

This is the new, simplified VRouter client that acts as a facade for the various
specialized managers. It provides the same interface as the original monolithic
client but delegates operations to focused, specialized components.
"""

from typing import List, Dict, Any, Optional
from loguru import logger as log
from vpp_vrouter.common import models

# Import specialized managers
from .connection.vpp_connection import VPPConnectionManager
from .tunnels.wireguard_manager import WireGuardTunnelManager
from .utility.utility_manager import UtilityManager
from .routes.route_manager import RouteManager
from .tunnels.gre_manager import GRETunnelManager
from .security.nat_manager import NATManager
from .security.acl_manager import ACLManager
from .base_interfaces import ComponentStatus


class VRouterClient:
    """
    Facade for VRouter operations - coordinates between specialized managers.
    
    This refactored client provides the same external interface as the original
    VRouterClient but internally delegates operations to specialized managers,
    making the codebase more maintainable and testable.
    """
    
    def __init__(self, tunnels: List[Dict], frr_config: Optional[str] = None, 
                 lcp_global: str = "frr"):
        """
        Initialize the VRouter client with specialized managers.
        
        Args:
            tunnels: List of tunnel configurations
            frr_config: Optional FRR configuration string
            lcp_global: LCP global namespace (default: "frr")
        """
        # Core connection management
        self.connection = VPPConnectionManager(auto_reconnect=True)
        
        # Specialized managers (initialize as needed)
        self._wireguard_manager = None
        self._gre_manager = None
        self._nat_manager = None
        self._acl_manager = None
        self._utility_manager = None 
        self._route_manager = None
        
        
        # Configuration storage
        self.tunnel_configs = tunnels
        self.frr_config = frr_config
        self.lcp_global = lcp_global
        
        log.debug(f"VRouterClient initialized with {len(tunnels)} tunnel configs")
    
    @property
    def wireguard(self) -> WireGuardTunnelManager:
        """Lazy-loaded WireGuard tunnel manager."""
        if self._wireguard_manager is None:
            self._wireguard_manager = WireGuardTunnelManager(self.connection)
        return self._wireguard_manager
    
    @property
    def gre(self) -> GRETunnelManager:
        """Lazy-loaded GRE tunnel manager."""
        if self._gre_manager is None:
            self._gre_manager = GRETunnelManager(self.connection)
        return self._gre_manager
    
    @property
    def nat(self) -> NATManager:
        """Lazy-loaded NAT manager."""
        if self._nat_manager is None:
            self._nat_manager = NATManager(self.connection)
        return self._nat_manager
    
    @property
    def acl(self) -> ACLManager:
        """Lazy-loaded ACL manager."""
        if self._acl_manager is None:
            self._acl_manager = ACLManager(self.connection)
        return self._acl_manager
    
    @property
    def utility(self) -> UtilityManager:
        """Lazy-loaded utility manager."""
        if self._utility_manager is None:
            self._utility_manager = UtilityManager(self.connection, self.route)
        return self._utility_manager
    @property
    def route(self) -> RouteManager:
        """Lazy-loaded route manager."""
        if self._route_manager is None:
            self._route_manager = RouteManager(self.connection)
        return self._route_manager
    
    # Public API methods - maintain compatibility with original interface
    
    def is_connected(self) -> bool:
        """
        Check if the client is connected to the vRouter.
        
        Returns:
            bool: True if connected, False otherwise.
        """
        try:
            connected = self.connection.is_connected()
            if connected:
                self.add_lcp_global_configuration()
            return connected
        except Exception as e:
            log.error(f"Error checking vRouter connection: {e}")
            return False
            
    def add_lcp_global_configuration(self):
        """
        Add a global LCP configuration to the vRouter agent.
        Args:
            lcp_interface_name (str): The name of the LCP interface.
        Returns:
            bool: True if the LCP configuration was added successfully, False otherwise.
        """
        # Check if the LCP global configuration already exists
        all_config = self.connection.client.get_configuration()
        current_config = [
            item.config
            for item in all_config.items
            if isinstance(item.config, models.LCPGlobalsConfigurationItem)
            and item.config.default_namespace == self.lcp_global
        ]
        if current_config:
            log.debug("LCP global configuration already exists. Skipping addition.")
            return False
        # Add the LCP global configuration

        reply = self.connection.client.add_configuration(
            models.LCPGlobalsConfigurationItem(
                default_namespace=self.lcp_global,
                lcp_sync=True,
                lcp_auto_subint=True,
            )
        )
        log.debug(reply)
        if reply.processing_error:
            log.error(
                f"Error adding LCP global configuration: {reply.processing_error}"
            )
            return False
        log.info("LCP global configuration added successfully")
        return True

    def create_wireguard_tunnels(self) -> Dict[str, Any]:
        """
        Create WireGuard tunnels from the configured tunnel list.
        
        Returns:
            dict: Contains 'success' boolean and 'interfaces' list with Django Interface model data
        """
        try:
            # Convert our tunnel configs to the format expected by the manager
            config_dicts = [self._tunnel_config_to_dict(config) for config in self.tunnel_configs]
            
            result = self.wireguard.create_tunnels(config_dicts)
            log.debug(f"WireGuard tunnel creation result: {result}")
            
            if result['success']:
                log.info(f"Successfully created {len(result['data']['tunnels'])} WireGuard tunnels")
                return {
                    'success': True,
                    'interfaces': result['data']['interfaces'],
                    'created_tunnels': result['data']['tunnels']
                }
            else:
                log.error(f"Failed to create WireGuard tunnels: {result.get('error')}")
                return {
                    'success': False,
                    'interfaces': [],
                    'error': result.get('error')
                }
                
        except Exception as e:
            log.error(f"Exception creating WireGuard tunnels: {e}")
            return {
                'success': False,
                'interfaces': [],
                'error': str(e)
            }

        
    def remove_wireguard_tunnels(self) -> bool:
        """
        Remove all WireGuard tunnels.
        
        Returns:
            bool: True if tunnels were removed successfully, False otherwise.
        """
        try:
            success = self.wireguard.remove_tunnels()
            if success:
                log.info("WireGuard tunnels removed successfully")
            else:
                log.error("Failed to remove WireGuard tunnels")
            return success
            
        except Exception as e:
            log.error(f"Exception removing WireGuard tunnels: {e}")
            return False
    
    def verify_tunnels_operational(self) -> List[Dict[str, Any]]:
        """
        Verify all created WireGuard tunnels are operational.
        
        Returns:
            List[dict]: List of tunnel status information
        """
        try:
            verification_results = self.wireguard.verify_tunnels()
            
            # Convert to original format for compatibility
            results = []
            for result in verification_results:
                # Map new format to old format
                status = 'active' if result.get('status') == ComponentStatus.ACTIVE.value else 'inactive'
                if result.get('status') == ComponentStatus.ERROR.value:
                    status = 'error'
                
                formatted_result = {
                    'tunnel_name': result.get('tunnel_name'),
                    'status': status,
                    'interface_up': result.get('interface_up', False),
                    'connectivity': result.get('connectivity', False),
                    'local_ip': result.get('local_ip'),
                    'peer_ip': result.get('peer_ip')
                }
                
                if 'error' in result:
                    formatted_result['error'] = result['error']
                
                results.append(formatted_result)
            
            return results
            
        except Exception as e:
            log.error(f"Exception verifying tunnels: {e}")
            return []
    
    def verify_tunnels_operational_enhanced(self, interface_names: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """
        Enhanced version of verify_tunnels_operational that can verify specific interfaces.
        
        Args:
            interface_names: List of interface names to verify. If None, verify all created tunnels.
        
        Returns:
            dict: Mapping of interface names to their verification results
        """
        try:
            verification_results = self.wireguard.verify_tunnels(interface_names)
            
            # Convert to enhanced format
            results = {}
            for result in verification_results:
                tunnel_name = result.get('tunnel_name')
                if tunnel_name:
                    operational = result.get('status') == ComponentStatus.ACTIVE.value
                    
                    results[tunnel_name] = {
                        'operational': operational,
                        'interface_up': result.get('interface_up', False),
                        'connectivity_test': result.get('connectivity', False)
                    }
                    
                    if 'error' in result:
                        results[tunnel_name]['error'] = result['error']
            
            return results
            
        except Exception as e:
            log.error(f"Exception in enhanced tunnel verification: {e}")
            return {}
    
    def get_wireguard_interfaces(self) -> List[Dict[str, Any]]:
        """
        Get list of WireGuard interfaces from VPP configuration.
        
        Returns:
            List[dict]: List of WireGuard interface information
        """
        try:
            return self.wireguard.get_wireguard_interfaces()
        except Exception as e:
            log.error(f"Error getting WireGuard interfaces: {e}")
            return []
    
    def get_wireguard_peers(self) -> List[Dict[str, Any]]:
        """
        Get list of WireGuard peers from VPP configuration.
        
        Returns:
            List[dict]: List of WireGuard peer information
        """
        try:
            return self.wireguard.get_wireguard_peers()
        except Exception as e:
            log.error(f"Error getting WireGuard peers: {e}")
            return []
    
    # GRE Tunnel Management Methods
    
    def create_gre_tunnels(self) -> List[Dict]:
        """
        Create GRE tunnels based on existing WireGuard tunnels.
        
        Returns:
            List[dict]: Created GRE tunnel information
        """
        if not self.wireguard.created_tunnels:
            log.error("No WireGuard tunnels to create GRE for")
            return []
        
        
        
        return self.gre.create_tunnels_from_wireguard(
            self.wireguard.created_tunnels, 
            self.tunnel_configs
        )
    
    def remove_gre_tunnels(self) -> bool:
        """
        Remove GRE tunnels and deallocate their addresses.
        
        Returns:
            bool: True if successful, False otherwise
        """
        return self.gre.remove_tunnels()
    
    # NAT Configuration Methods
    
    def add_nat_configuration(self, nat_config) -> bool:
        """
        Add NAT configuration for LAN/WAN interfaces.
        
        Args:
            nat_config: NAT configuration (NatConfig object or dict)
            
        Returns:
            bool: True if configuration successful, False otherwise
        """
        try:
            # Convert dict to NatConfig if needed
            if isinstance(nat_config, dict):
                from vrouter_agent.schemas.nat_acl_config import NatConfig
                nat_config = NatConfig.from_dict(nat_config)
            
            return self.nat.configure_nat(nat_config=nat_config)
        except Exception as e:
            log.error(f"Exception adding NAT configuration: {e}")
            return False
    
    def delete_nat_configuration(self, lan_iface, wan_iface, wg_ports_to_open: List[int],
                                tcp_ports: List[int] = None, udp_ports: List[int] = None) -> bool:
        """
        Remove NAT configuration.
        
        Args:
            lan_iface: LAN interface (Interface object or dict)
            wan_iface: WAN interface (Interface object or dict)  
            wg_ports_to_open: WireGuard ports that were opened
            tcp_ports: TCP ports that were opened
            udp_ports: UDP ports that were opened
            
        Returns:
            bool: True if removal successful, False otherwise
        """
        try:
            return self.nat.remove_nat_configuration(
                lan_interface=lan_iface,
                wan_interface=wan_iface,
                wg_ports_to_open=wg_ports_to_open,
                tcp_ports=tcp_ports or [],
                udp_ports=udp_ports or []
            )
        except Exception as e:
            log.error(f"Exception removing NAT configuration: {e}")
            return False
    
    # ACL Configuration Methods
    
    def add_acl_configuration(self, acl_config) -> bool:
        """
        Add ACL configuration.
        
        Args:
            acl_config: ACL configuration (AclConfig object or dict)
            
        Returns:
            bool: True if configuration successful, False otherwise
        """
        try:
            # Let ACL manager handle all conversions (supports both firewall and VPP formats)
            return self.acl.configure_acl_from_config(acl_config=acl_config)
        except Exception as e:
            log.error(f"Exception adding ACL configuration: {e}")
            return False
    
    def delete_acl_configuration(self, interface) -> bool:
        """
        Remove ACL configuration from interface.
        
        Args:
            interface: Interface to remove ACL from (Interface object or dict)
            
        Returns:
            bool: True if removal successful, False otherwise
        """
        try:
            return self.acl.remove_acl_configuration(interface)
        except Exception as e:
            log.error(f"Exception removing ACL configuration: {e}")
            return False
    
    # Routing and Utility Methods (TODO: Move to dedicated managers)
    
    def add_vpp_route(self, dest_net: str, next_hop_addr: str, outgoing_interface: str) -> bool:
        """
        Add a VPP route.
        
        Args:
            dest_net: Destination network (CIDR notation)
            next_hop_addr: Next hop IP address
            outgoing_interface: Outgoing interface name
            
        Returns:
            bool: True if route added successfully, False otherwise
        """
        # TODO: Move to VPPRoutingManager when implemented
        try:
            from vpp_vrouter.common import models
            
            reply = self.connection.client.add_configuration(
                models.RouteConfigurationItem(
                    destination_network=dest_net,
                    next_hop_address=next_hop_addr,
                    outgoing_interface=outgoing_interface,
                )
            )
            
            if reply.processing_error:
                log.error(f"Error adding VPP route: {reply.processing_error}")
                return False
            
            log.info(f"VPP route added: {dest_net} via {next_hop_addr} dev {outgoing_interface}")
            return True
            
        except Exception as e:
            log.error(f"Exception adding VPP route: {e}")
            return False
    
    def add_linux_route(self, dest_net: str, next_hop_addr: str = "", 
                       outgoing_iface: str = "", container: str = "") -> bool:
        """
        Add a Linux route.
        
        Args:
            dest_net: Destination network (CIDR notation)
            next_hop_addr: Next hop IP address
            outgoing_iface: Outgoing interface name
            container: Docker container name (empty for default namespace)
            
        Returns:
            bool: True if route added successfully, False otherwise
        """
        # TODO: Move to LinuxRoutingManager when implemented
        try:
            from vpp_vrouter.common import models
            
            reply = self.connection.client.add_configuration(
                models.LinuxRouteConfigurationItem(
                    docker_container_name=container,
                    destination_network=dest_net,
                    next_hop_address=next_hop_addr,
                    outgoing_interface=outgoing_iface,
                )
            )
            
            if reply.processing_error:
                log.error(f"Error adding Linux route: {reply.processing_error}")
                return False
            
            log.info(f"Linux route added: {dest_net} via {next_hop_addr} dev {outgoing_iface}")
            return True
            
        except Exception as e:
            log.error(f"Exception adding Linux route: {e}")
            return False
    
    def ping(self, destination_ip: str) -> bool:
        """
        Ping a destination IP through VPP.
        
        Args:
            destination_ip: IP address to ping
            
        Returns:
            bool: True if ping successful, False otherwise
        """
        # TODO: Move to ConnectivityTester when implemented
        try:
            from vrouter_agent.utils.cli import run_command
            
            cmd = f"sudo vppctl ping {destination_ip.split('/')[0]} repeat 1"
            res, _ = run_command(cmd.split())
            
            if "1 sent, 1 received" in res:
                log.info(f"Ping to {destination_ip} successful")
                return True
            
            log.error(f"Ping to {destination_ip} failed")
            return False
            
        except Exception as e:
            log.error(f"Exception pinging {destination_ip}: {e}")
            return False
    
    def check_interface_status(self, interface_name: str) -> bool:
        """
        Check if a VPP interface is up and operational.
        
        Args:
            interface_name: Name of the interface to check
            
        Returns:
            bool: True if interface is up, False otherwise
        """
        # TODO: Move to InterfaceManager when implemented
        try:
            from vrouter_agent.utils.cli import run_command
            
            cmd = f"sudo vppctl show interface {interface_name}"
            res, _ = run_command(cmd.split())
            
            if interface_name in res and "up" in res.lower() and "down" not in res.lower():
                log.info(f"Interface {interface_name} is up")
                return True
            else:
                log.warning(f"Interface {interface_name} is down or not found")
                return False
                
        except Exception as e:
            log.error(f"Error checking interface {interface_name} status: {e}")
            return False
    
    def get_interface_configuration(self, interface_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed configuration information for a VPP interface.
        
        Args:
            interface_name: Name of the interface
            
        Returns:
            Optional[dict]: Interface configuration details or None if not found
        """
        # TODO: Move to InterfaceManager when implemented
        try:
            current_config = self.connection.client.get_configuration()
            
            for item in current_config.items:
                if hasattr(item.config, 'name') and item.config.name == interface_name:
                    return {
                        'name': item.config.name,
                        'type': str(item.config.type),
                        'enabled': getattr(item.config, 'enabled', None),
                        'ip_addresses': getattr(item.config, 'ip_addresses', []),
                        'mtu': getattr(item.config, 'mtu', None)
                    }
            
            log.warning(f"Interface {interface_name} not found in configuration")
            return None
            
        except Exception as e:
            log.error(f"Error getting interface {interface_name} configuration: {e}")
            return None
    
    # Context manager support
    
    def __enter__(self):
        """Context manager entry."""
        if not self.connection.connect():
            raise ConnectionError("Failed to establish VPP connection")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.connection.disconnect()
    
    # Private helper methods
    
    def _tunnel_config_to_dict(self, config) -> Dict[str, Any]:
        """
        Convert tunnel configuration object to dictionary.
        
        Args:
            config: Tunnel configuration object
            
        Returns:
            dict: Configuration as dictionary
        """
        # This implementation depends on your actual tunnel config structure
        # For now, assuming it's already a dict or has a __dict__ method
        if isinstance(config, dict):
            return config
        elif hasattr(config, '__dict__'):
            return config.__dict__
        else:
            # Try to extract common attributes
            return {
                'address': getattr(config, 'address', None),
                'private_key': getattr(config, 'private_key', None),
                'peer_public_key': getattr(config, 'peer_public_key', None),
                'peer_address': getattr(config, 'peer_address', None),
                'peer_endpoint': getattr(config, 'peer_endpoint', None),
                'listen_port': getattr(config, 'listen_port', None),
                'persistent_keepalive': getattr(config, 'persistent_keepalive', None),
                'mtu': getattr(config, 'mtu', 1420),
                'source_ip': getattr(config, 'source_ip', None),
                'interface_name': getattr(config, 'interface_name', None)
            }


# Compatibility functions for gradual migration

def create_legacy_client(tunnels: List, frr_config: Optional[str] = None, 
                        lcp_global: str = "frr") -> VRouterClient:
    """
    Create a VRouter client with the same interface as the legacy client.
    
    This function provides a migration path for existing code.
    
    Args:
        tunnels: List of tunnel configurations
        frr_config: Optional FRR configuration
        lcp_global: LCP global namespace
        
    Returns:
        VRouterClient: New client instance
    """
    return VRouterClient(tunnels, frr_config, lcp_global)


# Example usage and migration guide
if __name__ == "__main__":
    # Example of how to use the new client
    tunnel_configs = [
        {
            'address': '10.0.1.1/30',
            'private_key': 'your_private_key',
            'peer_public_key': 'peer_public_key',
            'peer_address': '10.0.1.2/30',
            'peer_endpoint': '192.168.1.100:51820',
            'listen_port': 51820,
            'persistent_keepalive': 25
        }
    ]
    
    # Context manager usage (recommended)
    try:
        with VRouterClient(tunnel_configs) as client:
            # Check connection
            if client.is_connected():
                print("Connected to VPP")
                
                # Create tunnels
                result = client.create_wireguard_tunnels()
                if result['success']:
                    print(f"Created {len(result['created_tunnels'])} tunnels")
                    
                    # Verify tunnels
                    verification = client.verify_tunnels_operational()
                    for tunnel_status in verification:
                        print(f"Tunnel {tunnel_status['tunnel_name']}: {tunnel_status['status']}")
                
                # Get system status
                status = client.get_system_status()
                print(f"System status: {status}")
                
    except Exception as e:
        print(f"Error: {e}")
