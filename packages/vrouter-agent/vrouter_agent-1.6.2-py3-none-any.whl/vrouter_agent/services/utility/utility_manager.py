"""
Utility Manager

This module provides a specialized manager for miscellaneous utility functions
that are used across different components of the vRouter agent.
"""

from typing import Dict, Any, Optional, List, List
import ipaddress
from loguru import logger as log

from vpp_vrouter.common import models
from vrouter_agent.services.routes.route_manager import RouteManager
from ..connection.vpp_connection import VPPConnectionManager
from vrouter_agent.core.base import Interface
from ...utils import run_command


class UtilityManager:
    """
    Manages miscellaneous utility operations for the vRouter agent.
    
    This class handles various utility operations like exposing LAN interfaces
    to FRR containers, configuring BGP loopbacks, and managing client
    neighbor information.
    """
    
    def __init__(self, connection_manager: VPPConnectionManager, route_manager: RouteManager):
        """
        Initialize the Utility Manager.
        
        Args:
            connection_manager: VPP connection manager instance
        """
        self.connection = connection_manager
        self.client = connection_manager.client
        self.route = route_manager
    
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

    def expose_lan_interface_to_frr_container(
        self,
        interface: Interface,
        frr_container_name: str = "frr",
    ) -> bool:
        """
        Expose a LAN interface to the FRR container.
        
        Args:
            interface: Interface object containing interface details
            frr_container_name: Name of the FRR container
            
        Returns:
            bool: True if the interface was successfully exposed, False otherwise
        """
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
        return True

    def add_bgp_loopback(self, ip_addr: str) -> bool:
        """
        Add a BGP loopback interface.
        
        Args:
            ip_addr: The IP address of the loopback interface
            
        Returns:
            bool: True if the loopback interface was added successfully, False otherwise
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
        errors = self._extract_reply_errors(reply)
        if errors:
            log.error(f"Error adding loopback interface: {'; '.join(errors)}")
            return False
            
        return True

    def add_client_neighbour_info(
        self,
        vpp_lan_intf: str,
        client_vpp_intf_ip: str,
        client_vpp_intf_mac: str,
 
    ) -> bool:
        """
        Add client neighbour information to the routing table.
        
        Args:
            vpp_lan_intf: VPP LAN interface name
            client_vpp_intf_ip: Client VPP interface IP address
            client_vpp_intf_mac: Client VPP interface MAC address
          
            
        Returns:
            bool: True if the neighbour was added successfully, False otherwise
        """
        try:
             # using MAC address of client interface (or at least what TREX traffic destination MAC address that VPP must
             # steer back to Trex through client interface)
            cmd = f"vppctl ip neighbor {vpp_lan_intf} {client_vpp_intf_ip} {client_vpp_intf_mac}"
            _, ret = run_command(cmd.split())
            if ret == 0:
                log.info(f"Added neighbour info for {client_vpp_intf_ip}")
            else:

                log.error(f"Error adding neighbour info for {client_vpp_intf_ip}")
                return False
            return True
        except Exception as e:
            log.error(f"Error adding client neighbour info: {str(e)}")
            return False


    def add_ospf_lcp_fix(self, client_vpp_intf_address, vpp_lan_intf):
        # https://lists.fd.io/g/vpp-dev/topic/83103366#19478
        # for 224.0.0.5 and 224.0.0.6 used by OSPF (https://en.wikipedia.org/wiki/Open_Shortest_Path_First)

        # run_command(["sudo", "vppctl", "ip", "mroute", "add", "224.0.0.0/24", "via", "local", "Forward"])
        # for i in range(4):
        #     run_command(["sudo", "vppctl", "ip", "mroute", "add", "224.0.0.0/24", "via", os.environ[os.environ["VPP"]+f"_WG{i}_INTERFACE_NAME"], "Accept"])

        # to steer OSPF Hello packets from FRR container to client
        self.route.add_vpp_route(
            "224.0.0.0/24",  # static due to OSPF hello packets always destined for 224.0.0.5
            client_vpp_intf_address,
            vpp_lan_intf,
        )

        # to get ospf hello packets from client to frr container through vpp
        run_command(
            [
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

    # def add_ospf_lcp_fix(self, client_vpp_intf_address, vpp_lan_intf) -> bool:
    #     """
    #     Add OSPF LCP fix for routing between interfaces.
        
    #     Args:
    #         client_vpp_intf_address: Client VPP interface address
    #         vpp_lan_intf: VPP LAN interface name
            
    #     Returns:
    #         bool: True if the fix was applied successfully, False otherwise
    #     """
    #     try:
    #         HELLO_MULTICAST_ADDRESS = "244.0.0.5"  # OSPF Hello multicast address
    #         HELLO_MULTICAST_NETWORK = "224.0.0.0/24"  # OSPF Hello multicast network
    #         # Ensure the client_vpp_intf_address is a valid IP address
    #         ipaddress.ip_address(client_vpp_intf_address)
    #         # Ensure the vpp_lan_intf is a valid interface name
    #         if not isinstance(vpp_lan_intf, str) or not vpp_lan_intf:
    #             log.error("Invalid VPP LAN interface name provided")
    #             return False
    #         # to steer OSPF Hello packets from FRR container to client
    #         self.route.add_vpp_route(
    #             HELLO_MULTICAST_NETWORK,  # static due to OSPF hello packets always destined for 224.0.0.5
    #             client_vpp_intf_address,
    #             vpp_lan_intf,
    #         )   
    #         # Apply OSPF LCP fix via VPP API
    #         cmds = [
    #             f"sudo vppctl ip mroute add {client_vpp_intf_address} {HELLO_MULTICAST_ADDRESS} via {vpp_lan_intf} Accept",
    #             f"sudo vppctl ip mroute add {client_vpp_intf_address} {HELLO_MULTICAST_ADDRESS} via local Forward",
    #         ]
            
    #         for cmd in cmds:
    #             _, ret = run_command(cmd.split())
    #             if ret != 0:
    #                 log.error(f"Error applying OSPF LCP fix command: {cmd}")
    #                 return False
                    
    #         log.debug(f"Applied OSPF LCP fix for {client_vpp_intf_address} on {vpp_lan_intf}")
    #         return True
            
    #     except Exception as e:
    #         log.error(f"Error applying OSPF LCP fix: {str(e)}")
    #         return False

    def apply_frr_configuration(self, frr_config) -> bool:
        """
        Apply the FRR configuration to the vRouter agent.
        
        Args:
            frr_config: Either a dictionary containing FRR config sections or a string with the full config
            
        Returns:
            bool: True if the FRR configuration was applied successfully, False otherwise.
        """
        if not frr_config:
            log.error("FRR configuration is not set")
            return False
        
        try:
            # Extract the actual configuration string from the config structure
            if isinstance(frr_config, dict):
                # If it's a dictionary, try to get the full_config key first
                if 'full_config' in frr_config:
                    config_string = frr_config['full_config']
                    log.debug("Using full_config from FRR configuration dictionary")
                # If full_config is not available, try to build from individual sections
                elif any(key in frr_config for key in ['zebra_config', 'ospf_config', 'bgp_config', 'static_config']):
                    config_parts = []
                    
                    # Add zebra config
                    if frr_config.get('zebra_config'):
                        config_parts.append(frr_config['zebra_config'])
                    
                    # Add OSPF config
                    if frr_config.get('ospf_config'):
                        config_parts.append(frr_config['ospf_config'])
                    
                    # Add BGP config
                    if frr_config.get('bgp_config'):
                        config_parts.append(frr_config['bgp_config'])
                    
                    # Add static config
                    if frr_config.get('static_config'):
                        config_parts.append(frr_config['static_config'])
                    
                    config_string = '\n'.join(filter(None, config_parts))
                    log.debug("Built FRR configuration from individual sections")
                else:
                    log.error(f"FRR configuration dictionary does not contain expected keys: {list(frr_config.keys())}")
                    return False
            elif isinstance(frr_config, str):
                config_string = frr_config
                log.debug("Using FRR configuration string directly")
            else:
                log.error(f"FRR configuration must be a string or dictionary, got {type(frr_config)}")
                return False
            
            if not config_string or not config_string.strip():
                log.error("FRR configuration string is empty")
                return False
            
            # Apply the FRR configuration via VPP API
            log.debug(f"Applying FRR configuration: {config_string[:200]}...")
            reply = self.client.add_configuration(
                models.FRRConfigurationItem(
                    config=config_string,
                )
            )
            errors = self._extract_reply_errors(reply)
            if errors:
                for error in errors:
                    log.error(f"Error applying FRR configuration: {error}")
                return False
            
            log.debug("FRR configuration applied successfully")
            return True
        except Exception as e:
            log.error(f"Exception applying FRR configuration: {str(e)}")
            return False
    
    def remove_frr_configuration(self,frr_config) -> bool:
        """
        Remove the FRR configuration from the vRouter agent.
        
        Returns:
            bool: True if the FRR configuration was removed successfully, False otherwise.
        """
        try:
            log.debug("Removing FRR configuration")
            current_conf = self.client.get_frr_configuration()
            if not current_conf:
                log.warning("No FRR configuration found to remove")
                return True
            # If frr_config is a string, we assume it's the full config to remove
            if isinstance(frr_config, str):
                config_string = frr_config
            elif isinstance(frr_config, dict):
                # If it's a dictionary, we assume it contains the full config under 'full_config'
                config_string = frr_config.get('full_config', '')
            else:
                log.error(f"FRR configuration must be a string or dictionary, got {type(frr_config)}")
                return False    
            if not config_string or not config_string.strip():
                log.error("FRR configuration string is empty")
                return False
            # Remove the FRR configuration via VPP API
            log.debug(f"Removing FRR configuration: {config_string[:200]}...")
            reply = self.client.remove_configuration(
                models.FRRConfigurationItem(
                    config=config_string,
                )
            )
            if not reply:
                log.error("Failed to get reply from VPP when removing FRR configuration")
                return False
            errors = self._extract_reply_errors(reply)
            if errors:
                for error in errors:
                    log.error(f"Error removing FRR configuration: {error}")
                return False

            log.debug("FRR configuration removed successfully")
            return True
        except Exception as e:
            log.error(f"Exception removing FRR configuration: {str(e)}")
            return False

  