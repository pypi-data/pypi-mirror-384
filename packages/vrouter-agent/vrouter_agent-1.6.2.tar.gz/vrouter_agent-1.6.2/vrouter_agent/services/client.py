from itertools import chain
from typing import List, Optional
from pydantic import BaseModel
from vpp_vrouter.client import ExtendedVPPAPIClient
from vpp_vrouter.common import models
from loguru import logger as log
import ipaddress
from vrouter_agent.utils.cli import run_command
from vrouter_agent.utils.config import convert_wg_to_gre_ip_addr
from vrouter_agent.utils.gre_manager import get_gre_manager, convert_wg_to_gre_ip_addr_safe
from vrouter_agent.models import Tunnel
from vrouter_agent.core.base import CreatedWireguardTunnel, Interface
from vrouter_agent.core.config import settings
from vrouter_agent.services.frr import FRR
from vrouter_agent.schemas.tunnel_config import WireGuardConfig

    
class VRouterClient:
    """
    A class to manage VPP API client operations.
    """
    
    def __init__(self, tunnels: List[WireGuardConfig], frr_config:Optional[str]=None, lcp_global: str = "frr"):
        self.client = ExtendedVPPAPIClient()
        self.tunnels = tunnels
        self.wireguard_tunnels: Optional[List[CreatedWireguardTunnel]] = None
        self.gre_tunnels = None
        self.lcp_global = lcp_global
        self.frr_config = frr_config
        
        
    def is_connected(self):
        """
        Check if the client is connected to the vRouter.
        vRouter is the VPP agent.
        Returns:
            bool: True if connected, False otherwise.
        """
        try:
            self.client.get_configuration()
            self.add_lcp_global_configuration()
            return True
        except Exception as e:
            log.error(f"Error connecting to vRouter: {e}")
            return False
    def _get_next_available_wg_index(self, start_index: int = 0) -> int:
        """
        Get the next available WireGuard interface index by checking existing interfaces.
        Args:
            start_index (int): The starting index to check from.
        Returns:
            int: The next available index for WireGuard interface naming.
        """
        try:
            current_config = self.client.get_configuration()
            existing_wg_names = set()
            
            # Extract existing WireGuard interface names
            for item in current_config.items:
                if hasattr(item.config, 'name') and hasattr(item.config, 'type'):
                    if (hasattr(models.InterfaceType, 'WIREGUARD_TUNNEL') and 
                        item.config.type == models.InterfaceType.WIREGUARD_TUNNEL):
                        existing_wg_names.add(item.config.name)
            
            # Find the next available index
            index = start_index
            while f"wg{index}" in existing_wg_names:
                index += 1
                
            log.debug(f"Next available WireGuard index: {index}, existing interfaces: {existing_wg_names}")
            return index
            
        except Exception as e:
            log.warning(f"Could not check existing WireGuard interfaces: {e}, starting from index {start_index}")
            return start_index

    def create_wireguard_tunnels(self) -> dict:
        """
        Create wireguard tunnels.
        Returns:
            dict: Contains 'success' boolean and 'interfaces' list with Django Interface model data
        """
        wireguard_interfaces = []
        wireguard_peers = []
        routes= []
        log.debug(f"Creating wireguard tunnels: {self.tunnels}")
        
        # Get the starting index for new WireGuard interfaces
        current_wg_index = self._get_next_available_wg_index()
        created_tunnels = []
        created_interfaces_data = []  # For Django Interface model data
        
        for tunnel in self.tunnels:
            wg_name = f"wg{current_wg_index}"
            log.debug(f"Creating WireGuard tunnel with name: {wg_name}")
            wireguard_interfaces.append(
                models.InterfaceConfigurationItem(
                    name=wg_name,
                    type=models.InterfaceType.WIREGUARD_TUNNEL,
                    enabled=True,
                    ip_addresses=[f"{tunnel.address}/30"],
                    mtu= tunnel.mtu if tunnel.mtu else 1420,  # default mtu is 1420
                    link=models.WireguardInterfaceLink(
                        private_key=tunnel.private_key,
                        port=tunnel.listen_port,
                        src_addr=ipaddress.IPv4Address(tunnel.source_ip) if tunnel.source_ip else None,
                    ),
                )
            )
            wireguard_peers.append(
                models.WireguardPeerConfigurationItem(
                    wg_if_name=wg_name,
                    public_key=tunnel.peer_public_key,
                    allowed_ips=["0.0.0.0/0"],
                    persistent_keepalive=tunnel.persistent_keepalive,
                    endpoint=ipaddress.IPv4Address(tunnel.peer_endpoint.split(":")[0]) if tunnel.peer_endpoint else None,
                    port=tunnel.peer_endpoint.split(":")[1] if tunnel.peer_endpoint and ":" in tunnel.peer_endpoint else None,
                )
            )
            
            routes.append(
                models.RouteConfigurationItem(
                    destination_network=f"{tunnel.peer_address.split('/')[0]}/32",
                    next_hop_address=tunnel.address.split("/")[0],
                    outgoing_interface=wg_name,
                )
            )
            created_tunnels.append(
                CreatedWireguardTunnel(
                    name=wg_name,  # Use the actual VPP interface name
                    ip_address=tunnel.address,
                    peer_ip_address=tunnel.peer_address,
                    mapped_name=tunnel.interface_name if tunnel.interface_name else None,  # Use the provided interface name if available
                )
            )
            
            # Create Django Interface model data
            ip_address_without_cidr = tunnel.address.split('/')[0]
            subnet_mask = int(tunnel.address.split('/')[1]) if '/' in tunnel.address else 30
            
            interface_data = {
                'name': wg_name,
                'type': 'tunnel',
                'up': True,  # Will be set to True initially, can be verified later
                'hwaddr': None,  # WireGuard interfaces don't have MAC addresses
                'ip_address': ip_address_without_cidr,
                'subnet_mask': subnet_mask,
                'vlan_id': None,
                'mtu': tunnel.mtu if tunnel.mtu else 1420,
                'vpp_used': True,
                'vpp_interface_name': wg_name,
                'is_enabled': True,
                'description': f"WireGuard tunnel to {tunnel.peer_endpoint}",
                'is_management': False,
                'is_wan': True,  # WireGuard tunnels are typically WAN connections
                'is_lan': False,
                'is_primary': False,
                # Additional tunnel-specific metadata
                'tunnel_metadata': {
                    'tunnel_type': 'wireguard',
                    'peer_public_key': tunnel.peer_public_key,
                    'peer_endpoint': tunnel.peer_endpoint,
                    'peer_address': tunnel.peer_address,
                    'listen_port': tunnel.listen_port,
                    'persistent_keepalive': tunnel.persistent_keepalive
                }
            }
            created_interfaces_data.append(interface_data)
            
            current_wg_index += 1
            

        # Apply all configurations at once outside the loop
        if wireguard_interfaces or wireguard_peers or routes:
            reply = self.client.add_configuration(
                *chain(wireguard_interfaces, wireguard_peers, routes)
            )
            log.debug(reply)
            
         
            if reply and reply.processing_error:
                log.error(f"Error adding wireguard tunnels: {reply.processing_error}")
                return {
                    'success': False,
                    'interfaces': [],
                    'error': reply.processing_error
                }
            
            if reply and reply.all_added_items_applied_to_vpp:
                self.wireguard_tunnels = created_tunnels
                log.info(f"Wireguard tunnels created successfully: {[t.name for t in created_tunnels]}")
                return {
                    'success': True,
                    'interfaces': created_interfaces_data,
                    'created_tunnels': [t.name for t in created_tunnels]
                }
            else:
                log.error(f"Failed to create wireguard tunnels")
                return {
                    'success': False,
                    'interfaces': [],
                    'error': 'Failed to apply configuration to VPP'
                }
        else:
            log.warning("No WireGuard tunnels to create")
            return {
                'success': True,
                'interfaces': [],
                'message': 'No tunnels to create'
            }


    def remove_wireguard_tunnels(self) -> bool:
        """
        Remove all WireGuard tunnels.
        Returns:
            bool: True if tunnels were removed successfully, False otherwise.
        """
        if not self.wireguard_tunnels:
            log.warning("No WireGuard tunnels to remove")
            return True
        log.debug(f"Removing WireGuard tunnels: {[t.name for t in self.wireguard_tunnels]}")
        try:
            current_config = self.client.get_configuration()
            configs = []
            
            for tunnel in self.wireguard_tunnels:
                #Find the WireGuard interface configuration
                interface_config = [
                    item.config
                    for item in current_config.items
                    if isinstance(item.config, models.InterfaceConfigurationItem)
                    and item.config.name == tunnel.name
                ]
                if not interface_config:
                    log.error(f"Wireguard interface {tunnel.name} not found")
                    
      
                peer_config = [ item.config  for item in current_config.items if isinstance(item.config, models.WireguardPeerConfigurationItem) and item.config.wg_if_name == tunnel.name]
                if not peer_config:
                    log.error(f"Wireguard peer for interface {tunnel.name} not found")
                    
                
                route_config = [
                    item.config
                    for item in current_config.items
                    if isinstance(item.config, models.RouteConfigurationItem)
                    and item.config.outgoing_interface == tunnel.name
                ]
                if not route_config:
                    log.info(f"Route for Wireguard interface {tunnel.name} not found")
                    
                configs.extend(interface_config + peer_config + route_config)
            if not configs:
                log.warning("No WireGuard configurations found to remove")
                return True
            
            log.debug(f"Configurations to remove: {configs}")
               
            # Remove the WireGuard interface, peer, and route if they exist
            reply = self.client.delete_configuration(*configs)
            log.debug(reply)

            self.wireguard_tunnels = []
            log.info("WireGuard tunnels removed successfully")
            return True
        except Exception as e:
            log.error(f"Exception while removing WireGuard tunnels: {e}")
            return False
        
    def create_gre_tunnels(self) -> List[CreatedWireguardTunnel]:
        """
        Create GRE tunnels based on the WireGuard tunnels.
        Returns:
            List[CreatedWireguardTunnel]: A list of created GRE tunnels.
        """
        if not self.wireguard_tunnels:
            log.error("No WireGuard tunnels created yet")
            return []

        self.gre_tunnels = []
        for i, wg_tunnel in enumerate(self.wireguard_tunnels):
            # Find the corresponding original tunnel config to get GRE fields
            original_tunnel = None
            if i < len(self.tunnels):
                original_tunnel = self.tunnels[i]
            else:
                # Fallback: find by interface name matching
                for tunnel_config in self.tunnels:
                    if tunnel_config.interface_name == wg_tunnel.mapped_name:
                        original_tunnel = tunnel_config
                        break
            log.debug(f"Creating GRE tunnel for WireGuard tunnel: {wg_tunnel.name}, original tunnel: {original_tunnel}")
            gre_name, gre_ip = self.add_wireguard_gre_tunnel(
                wg_tunnel,
                original_tunnel
            )
            self.gre_tunnels.append(
                CreatedWireguardTunnel(name=gre_name, ip_address=gre_ip)
            )
        return self.gre_tunnels
    
    def create_ospf_configuration(self):
        
        # primary_lan = [intf for intf in settings.config.interfaces if intf.is_primary and intf.type == "lan"][0]
        # # expose the primary LAN interface to the FRR container
        # self.expose_lan_interface_to_frr_container(
        #     primary_lan.interface_name,
        #     primary_lan.ip_address,
        #     primary_lan.prefix_len,
            
        # )
        # add bgp loopback so that the FRR container can communicate with the route reflector
        self.add_bgp_loopback(
            settings.config.frr.loopback.split("/")[0]
        )
        if self.ospf_config.client_enabled:
            self.add_ospf_lcp_fix(
                self.ospf_config.lan_ip_address,
                primary_lan.interface_name
            )
            self.add_client_neighbour_info(
                primary_lan.interface_name,
                self.ospf_config.lan_ip_address,
                self.ospf_config.lan_mac_address,
            )
        
        frr = FRR(self.ospf_config, self.wireguard_tunnels )
        frr.apply_all_configs()

        # self.add_routes_for_bidirectional_bgp_communication(
        #     "frr",
        #     settings.config.frr.loopback.split("/")[0],
        #     settings.config.frr.controller_bgp.loopback.split("/")[0],
        #     settings.config.frr.controller_bgp.peer_ip.split("/")[0],
        # )
        
        # self.add_nat_configuration(
        #     lan_iface=settings.config.interfaces["lan_primary"],
        #     wan_iface=settings.config.interfaces["wan_primary"],
        #     wg_ports_to_open=list(
        #         set([tunnel.source_on_host.listen_port for tunnel in self.tunnels])
        #     ),
        #     tcp_ports=[
        #         22,
        #         2206,
        #         2205,
        #     ],  # TODO: Add the ports from the order
        #     udp_ports=[settings.config.route_reflector.port],
        # )
        # self.add_acl_configuration(
        #     ingress_iface=settings.config.interfaces["lan_primary"],
        #     deny_network="8.8.4.4/32",
        # )


    def apply_frr_configuration(self):
        """
        Apply the FRR configuration to the vRouter agent.
        Returns:
            bool: True if the FRR configuration was applied successfully, False otherwise.
        """
        if not self.frr_config:
            log.error("FRR configuration is not set")
            return False
        
        reply = self.client.add_configuration(
            models.FRRConfigurationItem(
                config=self.frr_config,
            )
        )
        log.debug(reply)
        if reply.processing_error:
            log.error(f"Error applying FRR configuration: {reply.processing_error}")
            return False
        return True

        
    def add_lcp_global_configuration(self):
        """
        Add a global LCP configuration to the vRouter agent.
        Args:
            lcp_interface_name (str): The name of the LCP interface.
        Returns:
            bool: True if the LCP configuration was added successfully, False otherwise.
        """
        # Check if the LCP global configuration already exists
        current_config = self.client.get_configuration()
        lcp_config = [
            item.config
            for item in current_config.items
            if isinstance(item.config, models.LCPGlobalsConfigurationItem)
            and item.config.default_namespace == self.lcp_global
        ]
        if lcp_config:
            log.debug("LCP global configuration already exists. Skipping addition.")
            return False
        # Add the LCP global configuration

        reply = self.client.add_configuration(
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

    def delete_lcp_global_configuration(self, namespace: str):
        """
        Delete the global LCP configuration from the vRouter agent.
        Args:
            client: The client object used to communicate with the server.
        Returns:
            bool: True if the LCP configuration was deleted successfully, False otherwise.
        """

        current_config = self.client.get_configuration()
        lcp_config = [
            item.config
            for item in current_config.items
            if isinstance(item.config, models.LCPGlobalsConfigurationItem)
            and item.config.default_namespace == namespace
        ]
        if not lcp_config:
            log.error("LCP global configuration not found")
            return False
        reply = self.client.delete_configuration(lcp_config[0])
        if reply.processing_error:
            log.error(
                f"Error deleting LCP global configuration: {reply.processing_error}"
            )
            return False
        return True

    def add_bgp_loopback(self, ip_addr: str):
        """
        Add a BGP loopback interface to the client.
        Args:
            client: The client object used to communicate with the server.
            ip_addr (str): The IP address of the loopback interface.
        Returns:
            bool: True if the loopback interface was added successfully, False otherwise.
        """

        reply = self.client.add_configuration(
            models.InterfaceConfigurationItem(
                name="loop0",
                type=models.InterfaceType.SOFTWARE_LOOPBACK,
                enabled=True,
                ip_addresses=[ip_addr + "/32"],
            )
        )
        log.debug(reply)
        if reply.processing_error:
            log.error(f"Error adding loopback interface: {reply.processing_error}")
            return False
        return True

    
    def add_vpp_route(self, dest_net, next_hop_addr, outgoing_interface):
        reply = self.client.add_configuration(
            models.RouteConfigurationItem(
                destination_network=dest_net,
                next_hop_address=next_hop_addr,
                outgoing_interface=outgoing_interface,
            )
        )
        log.debug(reply)
        if reply.processing_error:
            log.error(f"Error adding route: {reply.processing_error}")
            return False
        return True

    def add_linux_route(
        self,
        dest_net: str,
        next_hop_addr: str = "",
        outgoing_iface: str = "",
        container: str = "",  # empty container name means default linux namespace
    ):
        reply = self.client.add_configuration(
            models.LinuxRouteConfigurationItem(
                docker_container_name=container,
                destination_network=dest_net,
                next_hop_address=next_hop_addr,
                outgoing_interface=outgoing_iface,
            )
        )
        log.debug(reply)
        if reply.processing_error:
            log.error(f"Error adding route: {reply.processing_error}")
            return False
        return True

 
    def ping(self, destination_ip: str):
        cmd = f"sudo vppctl ping {destination_ip.split('/')[0]} repeat 1"
        res, _ = run_command(cmd.split())
        log.debug(res)
        if "1 sent, 1 received" in res:
            log.info(f"Ping to {destination_ip} successful")
            return True
        log.error(f"Ping to {destination_ip} failed")
        return False

    def check_interface_status(self, interface_name: str) -> bool:
        """
        Check if a VPP interface is up and operational.
        
        Args:
            interface_name (str): Name of the interface to check
            
        Returns:
            bool: True if interface is up, False otherwise
        """
        try:
            cmd = f"sudo vppctl show interface {interface_name}"
            res, _ = run_command(cmd.split())
            log.debug(f"Interface status for {interface_name}: {res}")
            
            # Check if interface is listed and not down
            if interface_name in res and "up" in res.lower() and "down" not in res.lower():
                log.info(f"Interface {interface_name} is up")
                return True
            else:
                log.warning(f"Interface {interface_name} is down or not found")
                return False
                
        except Exception as e:
            log.error(f"Error checking interface {interface_name} status: {e}")
            return False

    def get_interface_configuration(self, interface_name: str) -> Optional[dict]:
        """
        Get detailed configuration information for a VPP interface.
        
        Args:
            interface_name (str): Name of the interface
            
        Returns:
            Optional[dict]: Interface configuration details or None if not found
        """
        try:
            current_config = self.client.get_configuration()
            
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

    def test_tunnel_connectivity(self, tunnel_name: str, peer_address: str, retries: int = 3) -> bool:
        """
        Test connectivity through a tunnel by checking interface status and ping.
        
        Args:
            tunnel_name (str): Name of the tunnel interface
            peer_address (str): Peer IP address to ping (without CIDR)
            retries (int): Number of ping attempts
            
        Returns:
            bool: True if tunnel is operational (interface up + ping successful)
        """
        try:
            log.info(f"Testing connectivity for tunnel {tunnel_name} to {peer_address}")
            
            # First check if interface is up
            if not self.check_interface_status(tunnel_name):
                log.error(f"Tunnel {tunnel_name} interface is not up")
                return False
            
            # Test connectivity with retries
            for attempt in range(retries):
                if self.ping(peer_address):
                    log.info(f"Tunnel {tunnel_name} connectivity test successful (attempt {attempt + 1})")
                    return True
                
                if attempt < retries - 1:  # Don't sleep on last attempt
                    log.debug(f"Ping attempt {attempt + 1} failed, retrying...")
                    import time
                    time.sleep(1)
            
            log.error(f"Tunnel {tunnel_name} connectivity test failed after {retries} attempts")
            return False
            
        except Exception as e:
            log.error(f"Error testing tunnel {tunnel_name} connectivity: {e}")
            return False

    def verify_tunnels_operational(self) -> List[dict]:
        """
        Verify all created WireGuard tunnels are operational.
        
        Returns:
            List[dict]: List of tunnel status information
        """
        results = []
        
        if not self.wireguard_tunnels:
            log.warning("No WireGuard tunnels to verify")
            return results
        
        log.info(f"Verifying {len(self.wireguard_tunnels)} WireGuard tunnels")
        
        for tunnel in self.wireguard_tunnels:
            try:
                # Get corresponding tunnel config to find peer address
                tunnel_config = None
                for config in self.tunnels:
                    if config.address.split('/')[0] in tunnel.ip_address:
                        tunnel_config = config
                        break
                
                if not tunnel_config:
                    log.error(f"Could not find config for tunnel {tunnel.name}")
                    results.append({
                        'tunnel_name': tunnel.name,
                        'status': 'error',
                        'interface_up': False,
                        'connectivity': False,
                        'error': 'Configuration not found'
                    })
                    continue
                
                # Check interface status
                interface_up = self.check_interface_status(tunnel.name)
                
                # Test connectivity to peer
                peer_ip = tunnel_config.peer_address.split('/')[0]
                connectivity = False
                if interface_up:
                    connectivity = self.test_tunnel_connectivity(tunnel.name, peer_ip)
                
                status = 'active' if (interface_up and connectivity) else 'inactive'
                
                results.append({
                    'tunnel_name': tunnel.name,
                    'status': status,
                    'interface_up': interface_up,
                    'connectivity': connectivity,
                    'peer_ip': peer_ip,
                    'local_ip': tunnel.ip_address
                })
                
                log.info(f"Tunnel {tunnel.name} verification: {status} (interface: {interface_up}, connectivity: {connectivity})")
                
            except Exception as e:
                log.error(f"Error verifying tunnel {tunnel.name}: {e}")
                results.append({
                    'tunnel_name': tunnel.name,
                    'status': 'error',
                    'interface_up': False,
                    'connectivity': False,
                    'error': str(e)
                })
        
        return results

    def get_wireguard_interfaces(self) -> List[dict]:
        """
        Get list of WireGuard interfaces from VPP configuration.
        
        Returns:
            List[dict]: List of WireGuard interface information
        """
        try:
            # Ensure we're connected before making the call
            if not self.is_connected():
                log.warning("VPP client not connected, attempting to reconnect")
                return []
                
            current_config = self.client.get_configuration()
            wireguard_interfaces = []
            
            for item in current_config.items:
                if (hasattr(item.config, 'type') and 
                    hasattr(models.InterfaceType, 'WIREGUARD_TUNNEL') and
                    item.config.type == models.InterfaceType.WIREGUARD_TUNNEL):
                    
                    iface_info = {
                        'name': item.config.name,
                        'enabled': getattr(item.config, 'enabled', False),
                        'ip_addresses': getattr(item.config, 'ip_addresses', []),
                        'mtu': getattr(item.config, 'mtu', None)
                    }
                    
                    # Extract WireGuard-specific info if available
                    if hasattr(item.config, 'link') and item.config.link:
                        link = item.config.link
                        iface_info.update({
                            'private_key': getattr(link, 'private_key', None),
                            'listen_port': getattr(link, 'port', None),
                            'src_addr': str(getattr(link, 'src_addr', None)) if getattr(link, 'src_addr', None) else None
                        })
                    
                    wireguard_interfaces.append(iface_info)
            
            log.debug(f"Found {len(wireguard_interfaces)} WireGuard interfaces: {[iface['name'] for iface in wireguard_interfaces]}")
            return wireguard_interfaces
            
        except Exception as e:
            log.error(f"Error getting WireGuard interfaces: {e}")
            return []
    
    def get_wireguard_peers(self) -> List[dict]:
        """
        Get list of WireGuard peers from VPP configuration.
        
        Returns:
            List[dict]: List of WireGuard peer information
        """
        try:
            # Ensure we're connected before making the call
            if not self.is_connected():
                log.warning("VPP client not connected, attempting to reconnect")
                return []
                
            current_config = self.client.get_configuration()
            wireguard_peers = []
            
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
                    wireguard_peers.append(peer_info)
            
            log.debug(f"Found {len(wireguard_peers)} WireGuard peers")
            return wireguard_peers
            
        except Exception as e:
            log.error(f"Error getting WireGuard peers: {e}")
            return []

    def verify_tunnels_operational_enhanced(self, interface_names: Optional[List[str]] = None) -> dict:
        """
        Enhanced version of verify_tunnels_operational that can verify specific interfaces.
        
        Args:
            interface_names: List of interface names to verify. If None, verify all created tunnels.
        
        Returns:
            dict: Mapping of interface names to their verification results
        """
        results = {}
        
        # If specific interface names provided, verify those
        if interface_names:
            log.info(f"Verifying specified WireGuard interfaces: {interface_names}")
            
            for interface_name in interface_names:
                try:
                    # Check interface status
                    interface_up = self.check_interface_status(interface_name)
                    
                    # Get interface configuration to find peer info
                    iface_config = self.get_interface_configuration(interface_name)
                    connectivity_test = False
                    
                    if interface_up and iface_config:
                        # Try to find peer address for connectivity test
                        peers = self.get_wireguard_peers()
                        interface_peers = [p for p in peers if p.get('interface') == interface_name]
                        
                        if interface_peers:
                            # For now, mark connectivity as True if interface is up and has peers
                            # More sophisticated connectivity testing could be added here
                            connectivity_test = True
                    
                    operational = interface_up and connectivity_test
                    
                    results[interface_name] = {
                        'operational': operational,
                        'interface_up': interface_up,
                        'connectivity_test': connectivity_test
                    }
                    
                    log.info(f"Interface {interface_name} verification: operational={operational} "
                           f"(interface_up={interface_up}, connectivity={connectivity_test})")
                    
                except Exception as e:
                    log.error(f"Error verifying interface {interface_name}: {e}")
                    results[interface_name] = {
                        'operational': False,
                        'interface_up': False,
                        'connectivity_test': False,
                        'error': str(e)
                    }
            
            return results
        
        # Fallback to original behavior if no specific interfaces provided
        original_results = self.verify_tunnels_operational()
        
        # Convert to new format
        for result in original_results:
            tunnel_name = result.get('tunnel_name')
            if tunnel_name:
                operational = result.get('status') == 'active'
                results[tunnel_name] = {
                    'operational': operational,
                    'interface_up': result.get('interface_up', False),
                    'connectivity_test': result.get('connectivity', False)
                }
                if 'error' in result:
                    results[tunnel_name]['error'] = result['error']
        
        return results


    def add_ospf_lcp_fix(self, client_vpp_intf_address, vpp_lan_intf):
        # https://lists.fd.io/g/vpp-dev/topic/83103366#19478
        # for 224.0.0.5 and 224.0.0.6 used by OSPF (https://en.wikipedia.org/wiki/Open_Shortest_Path_First)

        # run_command(["sudo", "vppctl", "ip", "mroute", "add", "224.0.0.0/24", "via", "local", "Forward"])
        # for i in range(4):
        #     run_command(["sudo", "vppctl", "ip", "mroute", "add", "224.0.0.0/24", "via", os.environ[os.environ["VPP"]+f"_WG{i}_INTERFACE_NAME"], "Accept"])

        # to steer OSPF Hello packets from FRR container to client
        self.add_vpp_route(
            "224.0.0.0/24",  # static due to OSPF hello packets always destined for 224.0.0.5
            client_vpp_intf_address,
            vpp_lan_intf,
        )

        # to get ospf hello packets from client to frr container through vpp
        run_command(
            [
                "sudo",
                "vppctl",
                "ip",
                "mroute",
                "add",
                client_vpp_intf_address,
                "224.0.0.5",  # static destination ip address of Hello OSPF packets, fixed by OSPF protocol itself
                "via",
                vpp_lan_intf,
                "Accept",
            ]
        )
        run_command(
            [
                "sudo",
                "vppctl",
                "ip",
                "mroute",
                "add",
                client_vpp_intf_address,
                "224.0.0.5",  # static destination ip address of Hello OSPF packets, fixed by OSPF protocol itself
                "via",
                "local",  # static, set to be locally processed (processed by LCP)
                "Forward",
            ]
        )

    # Note: this does not include RR-node wireguard tunnel (for that see makefile) and RR setup => only path from linux WG
    # on node to BGP in container on node
    def add_routes_for_bidirectional_bgp_communication(
        self,
        local_bgp_loop_ip: str,
        rr_bgp_loop_ip: str,
        rr_wg_ip: str,
        frr_container_name: str = "frr"
    ):
        # Some path explanation:
        # RR-to-node path: node-linux-wg0 -(adding here route1+iptables forwarding)-> FRR container default interface ->
        #   FRR container routing to local loopback -(ping echo going back, need to add route2)-> FRR container default
        #   interface -(routing path was added as part of wg configuration)-> node-linux-wg0
        # Node-to-RR path: FRR instance in FRR container -(need to add route3)-> FRR container default interface
        #   -> node linux host route(actually controlled by WG allowed ip configuration) -> wg tunnel to RR
        host_ip_from_docker_container = "172.17.0.1"

        # adding route1
        frr_container_ip_address, _ = run_command(
            [
                "docker",
                "inspect",
                "-f",
                "'{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'",
                frr_container_name,
            ]
        )
        frr_container_ip_address = frr_container_ip_address.replace("\n", "").replace(
            "'", ""
        )
        log.debug(f"FRR container IP address: {frr_container_ip_address}")

        self.add_linux_route(
            local_bgp_loop_ip,
            frr_container_ip_address,
        )
        run_command(
            [
                "sudo",
                "iptables",
                "-A",
                "FORWARD",
                "-i",
                "wg0",  # static for default wireguard interface between controller and node 
                "-o",
                "docker0",  # static for default docker installation
                "-j",
                "ACCEPT",
            ]
        )
        # adding route2
        self.add_linux_route(
            rr_wg_ip,
            host_ip_from_docker_container,
            "",
            frr_container_name,
        )
        # adding route3
        self.add_linux_route(
            rr_bgp_loop_ip,
            host_ip_from_docker_container,
            "",
            frr_container_name,
        )

    def add_client_neighbour_info(
        self, vpp_lan_intf: str, client_vpp_intf_ip: str, client_vpp_intf_mac: str
    ):

        # using MAC address of client interface (or at least what TREX traffic destination MAC address that VPP must
        # steer back to Trex through client interface)
        cmd = f"sudo vppctl ip neighbor {vpp_lan_intf} {client_vpp_intf_ip} {client_vpp_intf_mac}"
        _, ret = run_command(cmd.split())
        if ret == 0:
            log.info(f"Added neighbour info for {client_vpp_intf_ip}")
        else:

            log.error(f"Error adding neighbour info for {client_vpp_intf_ip}")
            return False
        return True

    def add_wireguard_gre_tunnel(
        self,
        tunnel: CreatedWireguardTunnel,
        original_tunnel_config: Optional[WireGuardConfig] = None,
    ):
        """
        Add a GRE tunnel for a WireGuard tunnel using predefined GRE configuration or fallback to automatic generation.
        
        Args:
            tunnel: WireGuard tunnel configuration
            original_tunnel_config: Original tunnel configuration containing GRE fields
            
        Returns:
            Tuple of (gre_interface_name, gre_interface_ip_with_mask)
        """
        try:
            # Check if we have predefined GRE configuration
            if (original_tunnel_config and 
                original_tunnel_config.gre_name and 
                original_tunnel_config.gre_local_tunnel_ip and 
                original_tunnel_config.gre_remote_tunnel_ip):
                
                # Use predefined GRE configuration from tunnel data
                gre_interface_name = original_tunnel_config.gre_name
                gre_interface_ip_address = original_tunnel_config.gre_local_tunnel_ip
                remote_gre_interface_ip_address = original_tunnel_config.gre_remote_tunnel_ip
                
                # Determine the subnet mask - default to /30 for GRE point-to-point links
                if "/" in gre_interface_ip_address:
                    local_gre_ip_with_mask = gre_interface_ip_address
                    gre_interface_ip_address = gre_interface_ip_address.split("/")[0]
                    gre_interface_ip_address_mask = local_gre_ip_with_mask.split("/")[1]
                else:
                    # Default to /30 for point-to-point GRE tunnels
                    gre_interface_ip_address_mask = "30"
                    local_gre_ip_with_mask = f"{gre_interface_ip_address}/{gre_interface_ip_address_mask}"
                
                log.info(
                    f"Using predefined GRE configuration - Interface: {gre_interface_name}, "
                    f"Local: {local_gre_ip_with_mask}, Remote: {remote_gre_interface_ip_address}, "
                    f"WG Tunnel: {tunnel.name} ({tunnel.ip_address})"
                )
            else:
                # Fallback to automatic generation using GRE manager
                log.info(f"No predefined GRE configuration found for {tunnel.name}, using automatic generation")
                
                # Extract index from tunnel name (e.g., "wg0" -> "0")
                if tunnel.name.startswith("wg"):
                    index = tunnel.name[2:]  # Remove "wg" prefix to get the numeric index
                else:
                    # Fallback to old method for backward compatibility
                    index = tunnel.name.split("_")[-1]
                
                gre_interface_name = f"gre{index}"
                
                # Use the new GRE manager to allocate addresses safely
                gre_manager = get_gre_manager()
                local_gre_ip_with_mask, remote_gre_interface_ip_address = convert_wg_to_gre_ip_addr_safe(tunnel, gre_manager)
                
                # Extract components for processing
                gre_interface_ip_address = local_gre_ip_with_mask.split("/")[0]
                gre_interface_ip_address_mask = local_gre_ip_with_mask.split("/")[1]
                
                log.info(
                    f"GRE tunnel allocation (auto-generated) - Interface: {gre_interface_name}, "
                    f"Local: {local_gre_ip_with_mask}, Remote: {remote_gre_interface_ip_address}, "
                    f"WG Tunnel: {tunnel.name} ({tunnel.ip_address})"
                )

            def add_frr_agent_ip_translation_from_gre_to_wg(
                gre_interface_ip_address: str,
                interface_ip: str,
                remote_gre_interface_ip_address: str,
                remote_tunnel_end_ip: str,
                frr_container_name: str = "frr",
                replace_file_path: str = "/rr-ip-replace.txt",
            ):
                # TODO when proper python client API will be created for this then replace this with python client code
                _, code1 = run_command(
                    [
                        "docker",
                        "exec",
                        "-t",
                        frr_container_name,
                        "sh",
                        "-c",
                        "echo '"
                        + gre_interface_ip_address
                        + "=>"
                        + interface_ip
                        + "' >> "
                        + replace_file_path,
                    ]
                )
                _, code2 = run_command(
                    [
                        "docker",
                        "exec",
                        "-t",
                        frr_container_name,
                        "sh",
                        "-c",
                        "echo '"
                        + remote_gre_interface_ip_address
                        + "=>"
                        + remote_tunnel_end_ip
                        + "' >> "
                        + replace_file_path,
                    ]
                )
                return code1 == 0 and code2 == 0

            def add_lcp_interface(
                vpp_iface: str,
                host_iface: str,
                host_netns: str,
                is_tun: bool = False,
            ):
                iface_type = (
                    models.LCPHostInterfaceTypeEnum.TUN
                    if is_tun
                    else models.LCPHostInterfaceTypeEnum.TAP
                )
                reply = self.client.add_configuration(
                    models.LCPPairConfigurationItem(
                        interface=vpp_iface,
                        mirror_interface_host_name=host_iface,
                        mirror_interface_type=iface_type,
                        host_namespace=host_netns,
                    )
                )
                log.debug(reply)
                if reply.processing_error:
                    log.error(f"Error adding LCP interface: {reply.processing_error}")
                    return False
                return True

            def add_gre_tunnel_to_wg_and_lcp_it_to_frr_container(
                gre_interface_name: str,
                gre_interface_ip_address: str,
                gre_interface_ip_address_mask: str,
                remote_gre_interface_ip_address: str,
                interface_name: str,
                remote_tunnel_end_ip: str,
                frr_container_name: str = "frr",
            ):

                gre_iface = models.InterfaceConfigurationItem(
                    name=gre_interface_name,
                    type=models.InterfaceType.GRE_TUNNEL,
                    enabled=False,
                    ip_addresses=[],
                    link=models.GREInterfaceLink(
                        type=models.GRELinkType.L3,
                        src_addr=ipaddress.IPv4Address(gre_interface_ip_address),
                        dst_addr=ipaddress.IPv4Address(remote_gre_interface_ip_address),
                    ),
                )

                reply = self.client.add_configuration(gre_iface)
                if reply and reply.processing_error:
                    log.error(f"Error adding GRE interface: {reply.processing_error}")
                    return False

                self.add_vpp_route(
                    remote_gre_interface_ip_address
                    + "/32",  # route to one ip address => mask /32 is static value
                    remote_tunnel_end_ip,
                    interface_name,
                )

                add_lcp_interface(
                    gre_interface_name,
                    interface_name,
                    frr_container_name,
                    True,
                )

                reply = self.client.update_configuration(
                    gre_iface,
                    models.InterfaceConfigurationItem(
                        name=gre_interface_name,
                        type=models.InterfaceType.GRE_TUNNEL,
                        enabled=True,
                        ip_addresses=[
                            gre_interface_ip_address + "/" + gre_interface_ip_address_mask
                        ],
                        link=models.GREInterfaceLink(
                            type=models.GRELinkType.L3,
                            src_addr=ipaddress.IPv4Address(gre_interface_ip_address),
                            dst_addr=ipaddress.IPv4Address(remote_gre_interface_ip_address),
                        ),
                    ),
                )
                log.debug(reply)
                if reply and reply.processing_error:
                    log.error(f"Error enabling GRE interface: {reply.processing_error}")
                    return False
                return True

            if add_gre_tunnel_to_wg_and_lcp_it_to_frr_container(
                gre_interface_name,
                gre_interface_ip_address,
                gre_interface_ip_address_mask,
                remote_gre_interface_ip_address,
                tunnel.name,
                self._safe_extract_ip(tunnel.peer_ip_address) if hasattr(tunnel, 'peer_ip_address') and tunnel.peer_ip_address else remote_gre_interface_ip_address,
            ):
                log.info(f"Added GRE tunnel to VPP for {gre_interface_name}")

            run_command(
                [
                    "sudo",
                    "vppctl",
                    "ip",
                    "mroute",
                    "add",
                    remote_gre_interface_ip_address,
                    "224.0.0.5",  # static destination ip address of Hello OSPF packets, fixed by OSPF protocol itself
                    "via",
                    gre_interface_name,
                    "Accept",
                ]
            )
            run_command(
                [
                    "sudo",
                    "vppctl",
                    "ip",
                    "mroute",
                    "add",
                    remote_gre_interface_ip_address,
                    "224.0.0.5",  # static destination ip address of Hello OSPF packets, fixed by OSPF protocol itself
                    "via",
                    "local",  # static forwarding to local processing (it will be processed by LCP)
                    "Forward",
                ]
            )

            if add_frr_agent_ip_translation_from_gre_to_wg(
                gre_interface_ip_address,
                self._safe_extract_ip(tunnel.ip_address),
                remote_gre_interface_ip_address,
                self._safe_extract_ip(tunnel.peer_ip_address) if hasattr(tunnel, 'peer_ip_address') and tunnel.peer_ip_address else remote_gre_interface_ip_address,
            ):
                log.info(
                    f"Added FRR agent IP translation for GRE interface {gre_interface_name}"
                )
            
            return (
                gre_interface_name,
                local_gre_ip_with_mask,
            )
            
        except Exception as e:
            log.error(f"Failed to create GRE tunnel for {tunnel.name}: {e}")
            # Attempt cleanup on failure only if we used automatic generation
            if not (original_tunnel_config and 
                    original_tunnel_config.gre_name and 
                    original_tunnel_config.gre_local_tunnel_ip and 
                    original_tunnel_config.gre_remote_tunnel_ip):
                try:
                    gre_manager = get_gre_manager()
                    gre_manager.deallocate_gre_addresses(tunnel.name)
                except Exception as cleanup_error:
                    log.warning(f"Failed to cleanup GRE allocation for {tunnel.name}: {cleanup_error}")
            raise

    def expose_lan_interface_to_frr_container(
        self,
        interface: Interface,
        frr_container_name: str = "frr",
    ):
        lcp = f"vppctl lcp create {interface.interface_name} host-if {interface.interface_name} netns {frr_container_name} tun"
        _, ret1 = run_command(lcp.split())
        if ret1 == 0:
            log.debug(f"Created LCP interface: {interface.interface_name}")
        else:
            log.error(f"Error creating LCP interface: {interface.interface_name}")
            return False

        ip_addr_del = f"vppctl set interface ip address del {interface.interface_name} {str(interface.ip_address)}/{interface.prefix_len}"
        _, ret2 = run_command(ip_addr_del.split())

        if ret2 == 0:
            log.debug(f"Deleted IP address from interface: {interface.interface_name}")
        else:
            log.error(f"Error deleting IP address from interface: {interface.interface_name}")
            return False

        set_ip = f"vppctl set interface ip address {interface.interface_name} {str(interface.ip_address)}/{interface.prefix_len}"
        _, ret3 = run_command(set_ip.split())

        if ret3 == 0:
            log.debug(f"Set IP address on interface: {interface.interface_name}")
        else:
            log.error(f"Error setting IP address on interface: {interface.interface_name}")
            return False

    def add_nat_configuration(
        self,
        lan_iface: Interface,
        wan_iface: Interface,
        wg_ports_to_open: List[int],
        tcp_ports: List[int] = [],
        udp_ports: List[int] = [],
    ):
        lan_nat_iface = models.Nat44InterfaceConfigurationItem(
            name=lan_iface.interface_name,
            nat_inside=True,
            nat_outside=False,
            output_feature=False,
        )
        wan_nat_iface = models.Nat44InterfaceConfigurationItem(
            name=wan_iface.interface_name,
            nat_inside=False,
            nat_outside=True,
            output_feature=False,
        )
        nat_address_pool = models.Nat44AddressPoolConfigurationItem(
            name="nat-pool",
            first_ip=ipaddress.IPv4Address(wan_iface.ip_address),
            last_ip=ipaddress.IPv4Address(wan_iface.ip_address),
        )

        wg_port_mappings = [
            models.IdentityMapping(
                interface=wan_iface.interface_name,
                protocol=models.ProtocolInNAT.UDP,
                port=p,
            )
            for p in wg_ports_to_open
        ]
        tcp_port_mappings = [
            models.IdentityMapping(
                interface=wan_iface.interface_name,
                protocol=models.ProtocolInNAT.TCP,
                port=p,
            )
            for p in tcp_ports
        ]
        udp_port_mappings = [
            models.IdentityMapping(
                interface=wan_iface.interface_name,
                protocol=models.ProtocolInNAT.UDP,
                port=p,
            )
            for p in udp_ports
        ]

        nat_mappings = models.DNat44ConfigurationItem(
            label="nat-mappings",
            static_mappings=[],
            identity_mappings=list(
                chain(wg_port_mappings, tcp_port_mappings, udp_port_mappings)
            ),
        )
        reply = self.client.add_configuration(
            lan_nat_iface,
            wan_nat_iface,
            nat_address_pool,
            nat_mappings,
        )
        log.debug(reply)
        if reply and reply.processing_error:
            log.error(f"Error adding NAT configuration: {reply.processing_error}")
            return False
        return True

    def add_acl_configuration(
        self,
        ingress_iface: Interface,
        deny_network: str,
    ):
        reply = self.client.add_configuration(
            models.ACLConfigurationItem(
                name="lab-acl-rules",
                ingress=[ingress_iface.interface_name],
                rules=[
                    models.ACLRuleConfigurationItem(
                        action=models.ACLAction.DENY,
                        refinement=models.IPSpecification(
                            addresses=models.IPAddresses(
                                destination_network=ipaddress.IPv4Network(deny_network)
                            )
                        ),
                    ),
                    models.ACLRuleConfigurationItem(
                        action=models.ACLAction.PERMIT,
                    ),
                ],
            )
        )
        log.debug(reply)
        if reply and reply.processing_error:
            log.error(f"Error adding ACL configuration: {reply.processing_error}")
            return False
        return True

    def delete_nat_configuration(
        self,
        lan_iface: Interface,
        wan_iface: Interface,
        wg_ports_to_open: List[int],
        tcp_ports: List[int] = [],
        udp_ports: List[int] = [],
    ):
        current_config = self.client.get_configuration()
        nat_config = [
            item.config
            for item in current_config.items
            if isinstance(item.config, models.Nat44InterfaceConfigurationItem)
            and item.config.name in [lan_iface.interface_name, wan_iface.interface_name]
        ]
        port_mappings = [
            item.config
            for item in current_config.items
            if isinstance(item.config, models.IdentityMapping)
            and item.config.port in chain(wg_ports_to_open, tcp_ports, udp_ports)
        ]

        if not nat_config:
            log.error("NAT configuration not found")
            return False
        reply = self.client.delete_configuration(*nat_config, *port_mappings)
        if reply.processing_error:
            log.error(f"Error deleting NAT configuration: {reply.processing_error}")
            return False
        log.info("NAT configuration deleted successfully")
        return True

    def delete_acl_configuration(self, lan_iface):
        current_config = self.client.get_configuration()
        acl_config = [
            item.config
            for item in current_config.items
            if isinstance(item.config, models.ACLConfigurationItem)
            and item.config.ingress == [lan_iface.interface_name]
        ]
        if not acl_config:
            log.error("ACL configuration not found")
            return False
        reply = self.client.delete_configuration(*acl_config)
        if reply.processing_error:
            log.error(f"Error deleting ACL configuration: {reply.processing_error}")
            return False
        log.info("ACL configuration deleted successfully")
        return True

    def remove_gre_tunnels(self) -> bool:
        """
        Remove GRE tunnels and deallocate their addresses.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            gre_manager = get_gre_manager()
            success = True
            
            # Clean up GRE allocations for all WireGuard tunnels
            if self.wireguard_tunnels:
                for tunnel in self.wireguard_tunnels:
                    if not gre_manager.deallocate_gre_addresses(tunnel.name):
                        log.warning(f"Failed to deallocate GRE addresses for {tunnel.name}")
                        success = False
            
            # Clear the GRE tunnels list
            self.gre_tunnels = []
            
            if success:
                log.info("GRE tunnels removed and addresses deallocated successfully")
            else:
                log.warning("GRE tunnel removal completed with some warnings")
                
            return success
            
        except Exception as e:
            log.error(f"Exception while removing GRE tunnels: {e}")
            return False
    
    def _safe_extract_ip(self, ip_with_mask: str) -> str:
        """
        Safely extract IP address from IP/mask format.
        
        Args:
            ip_with_mask: IP address potentially with CIDR notation
            
        Returns:
            IP address without CIDR notation
        """
        if not ip_with_mask:
            return "0.0.0.0"  # Fallback
        
        if "/" in ip_with_mask:
            return ip_with_mask.split("/")[0]
        else:
            return ip_with_mask
