"""
Example implementation showing how to use UtilityManager and RouteManager
"""

from typing import List, Optional
from loguru import logger as log

from vpp_vrouter.client import ExtendedVPPAPIClient
from vrouter_agent.schemas.tunnel_config import WireGuardConfig
from vrouter_agent.models import Interface, Tunnel
from vrouter_agent.core.base import CreatedWireguardTunnel
from vrouter_agent.services.connection.vpp_connection import VPPConnectionManager
from vrouter_agent.services.utility.utility_manager import UtilityManager
from vrouter_agent.services.routes.route_manager import RouteManager


class EnhancedVRouterClient:
    """
    Enhanced VRouter client implementation demonstrating how to use 
    the UtilityManager and RouteManager.
    """
    
    def __init__(self, tunnels: List[WireGuardConfig], frr_config: Optional[str] = None, lcp_global: str = "frr"):
        """
        Initialize the enhanced VRouter client.
        
        Args:
            tunnels: List of WireGuard tunnel configurations
            frr_config: FRR configuration (optional)
            lcp_global: LCP global name
        """
        # Initialize the connection manager
        self.connection_manager = VPPConnectionManager()
        self.client = self.connection_manager.client
        
        # Initialize specialized managers
        self.route_manager = RouteManager(self.connection_manager)
        self.utility_manager = UtilityManager(self.connection_manager, self.route_manager)
        
        # Store configuration
        self.tunnels = tunnels
        self.wireguard_tunnels: Optional[List[CreatedWireguardTunnel]] = None
        self.gre_tunnels = None
        self.lcp_global = lcp_global
        self.frr_config = frr_config
    
    def configure_lan_interface(self, interface: Interface, expose_to_frr: bool = True) -> bool:
        """
        Configure a LAN interface and optionally expose it to the FRR container.
        
        Args:
            interface: The interface to configure
            expose_to_frr: Whether to expose the interface to the FRR container
            
        Returns:
            bool: True if configuration was successful, False otherwise
        """
        # Configure interface through VPP API
        # ... (Implementation details)
        
        # If needed, expose the interface to the FRR container
        if expose_to_frr:
            return self.utility_manager.expose_lan_interface_to_frr_container(
                interface, 
                frr_container_name=self.lcp_global
            )
        
        return True
        
    def configure_bgp_routing(self, router_ip: str, neighbor_ip: str) -> bool:
        """
        Configure BGP routing by setting up loopback and routes.
        
        Args:
            router_ip: Router IP address
            neighbor_ip: Neighbor IP address
            
        Returns:
            bool: True if configuration was successful, False otherwise
        """
        # Add BGP loopback using the utility manager
        if not self.utility_manager.add_bgp_loopback(router_ip):
            return False
            
        # Add routes using the route manager
        if not self.route_manager.add_vpp_route(
            dest_net=f"{neighbor_ip}/32",
            next_hop_addr=neighbor_ip,
            outgoing_iface="loop0"
        ):
            return False
            
        return True
        
    def configure_ospf_routing(self, client_vpp_intf_address: str, vpp_lan_intf: str) -> bool:
        """
        Configure OSPF routing with necessary fixes.
        
        Args:
            client_vpp_intf_address: Client VPP interface address
            vpp_lan_intf: VPP LAN interface name
            
        Returns:
            bool: True if configuration was successful, False otherwise
        """
        return self.utility_manager.add_ospf_lcp_fix(
            client_vpp_intf_address, 
            vpp_lan_intf
        )
        
    def configure_neighbor_info(
        self,
        router_ip: str,
        client_ip: str,
        interface_name: str,
        mac_address: str,
        network: Optional[str] = None
    ) -> bool:
        """
        Configure neighbor information for client communication.
        
        Args:
            router_ip: Router IP address
            client_ip: Client IP address
            interface_name: Interface name
            mac_address: MAC address
            network: Network address (optional)
            
        Returns:
            bool: True if configuration was successful, False otherwise
        """
        return self.utility_manager.add_client_neighbour_info(
            router_ip,
            client_ip,
            interface_name,
            mac_address,
            network
        )
        
    def add_docker_routes(self, container: str, routes: List[dict]) -> bool:
        """
        Add multiple routes to a Docker container.
        
        Args:
            container: Docker container name
            routes: List of routes with keys 'dest_net', 'next_hop', 'interface'
            
        Returns:
            bool: True if all routes were added successfully, False otherwise
        """
        success = True
        
        for route in routes:
            if not self.route_manager.add_docker_route(
                container=container,
                dest_net=route['dest_net'],
                next_hop_addr=route['next_hop'],
                outgoing_iface=route['interface']
            ):
                success = False
                
        return success
