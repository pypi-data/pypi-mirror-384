"""
Route Manager

This module provides a specialized manager for route operations,
implementing functionality for both Linux and Docker route management.
"""

from typing import Dict, Any, Optional, List
import ipaddress
from loguru import logger as log

from vpp_vrouter.common import models
from vrouter_agent.utils.cli import run_command
from ..connection.vpp_connection import VPPConnectionManager


class RouteManager:
    """
    Manages route operations for both Linux and Docker environments.
    
    This class handles various routing operations including adding and removing
    routes in Linux and Docker environments.
    """
    
    def __init__(self, connection_manager: VPPConnectionManager):
        """
        Initialize the Route Manager.
        
        Args:
            connection_manager: VPP connection manager instance
        """
        self.connection = connection_manager
        self.client = connection_manager.client
        
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
     
    def remove_linux_route(
        self,
        dest_net: str,
        next_hop_addr: str,
        outgoing_iface: str,
        container: str = "",
    ) -> bool:
        """
        Remove a Linux route.
        
        Args:
            dest_net: Destination network (CIDR notation)
            next_hop_addr: Next hop IP address
            outgoing_iface: Outgoing interface name
            container: Docker container name (empty for default namespace)
            
        Returns:
            bool: True if route removed successfully, False otherwise
        """
        try:
            reply = self.client.remove_configuration(
                models.LinuxRouteConfigurationItem(
                    docker_container_name=container,
                    destination_network=dest_net,
                    next_hop_address=next_hop_addr,
                    outgoing_interface=outgoing_iface,
                )
            )
            
            errors = self._extract_reply_errors(reply)
            if errors:
                for error in errors:
                    log.error(f"Error removing Linux route: {error}")
                return False
            
            log.info(f"Linux route removed: {dest_net} via {next_hop_addr} dev {outgoing_iface}")
            return True
            
        except Exception as e:
            log.error(f"Exception removing Linux route: {e}")
            return False
            
    def add_docker_route(
        self,
        container: str,
        dest_net: str,
        next_hop_addr: str,
        outgoing_iface: str,
    ) -> bool:
        """
        Add a route to a Docker container.
        
        Args:
            container: Docker container name
            dest_net: Destination network (CIDR notation)
            next_hop_addr: Next hop IP address
            outgoing_iface: Outgoing interface name
            
        Returns:
            bool: True if route added successfully, False otherwise
        """
        return self.add_linux_route(dest_net, next_hop_addr, outgoing_iface, container)
    
    def remove_docker_route(
        self,
        container: str,
        dest_net: str,
        next_hop_addr: str,
        outgoing_iface: str,
    ) -> bool:
        """
        Remove a route from a Docker container.
        
        Args:
            container: Docker container name
            dest_net: Destination network (CIDR notation)
            next_hop_addr: Next hop IP address
            outgoing_iface: Outgoing interface name
            
        Returns:
            bool: True if route removed successfully, False otherwise
        """
        return self.remove_linux_route(dest_net, next_hop_addr, outgoing_iface, container)
        
    def add_vpp_route(
        self,
        dest_net: str,
        next_hop_addr: str,
        outgoing_iface: str,
        weight: int = 1,
    ) -> bool:
        """
        Add a VPP route.
        
        Args:
            dest_net: Destination network (CIDR notation)
            next_hop_addr: Next hop IP address
            outgoing_iface: Outgoing interface name
            weight: Route weight/priority (default: 1)
            
        Returns:
            bool: True if route added successfully, False otherwise
        """
        try:
            reply = self.client.add_configuration(
                models.RouteConfigurationItem(
                    destination_network=dest_net,
                    next_hop_address=next_hop_addr,
                    outgoing_interface=outgoing_iface,
                    weight=weight,
                )
            )
            
            errors = self._extract_reply_errors(reply)
            if errors:
                for error in errors:
                    log.error(f"Error adding VPP route: {error}")
                return False
            
            log.info(f"VPP route added: {dest_net} via {next_hop_addr} dev {outgoing_iface} weight {weight}")
            return True
            
        except Exception as e:
            log.error(f"Exception adding VPP route: {e}")
            return False
            
    def remove_vpp_route(
        self,
        dest_net: str,
        next_hop_addr: str,
        outgoing_iface: str,
        weight: int = 1,
    ) -> bool:
        """
        Remove a VPP route.
        
        Args:
            dest_net: Destination network (CIDR notation)
            next_hop_addr: Next hop IP address
            outgoing_iface: Outgoing interface name
            weight: Route weight/priority (default: 1)
            
        Returns:
            bool: True if route removed successfully, False otherwise
        """
        try:
            reply = self.client.remove_configuration(
                models.RouteConfigurationItem(
                    destination_network=dest_net,
                    next_hop_address=next_hop_addr,
                    outgoing_interface=outgoing_iface,
                    weight=weight,
                )
            )
            
            errors = self._extract_reply_errors(reply)
            if errors:
                for error in errors:
                    log.error(f"Error removing VPP route: {error}")
                return False
            
            log.info(f"VPP route removed: {dest_net} via {next_hop_addr} dev {outgoing_iface} weight {weight}")
            return True
            
        except Exception as e:
            log.error(f"Exception removing VPP route: {e}")
            return False
    
    def get_all_routes(self, container: str = "") -> List[Dict[str, Any]]:
        """
        Get all routes from a specific environment.
        
        Args:
            container: Docker container name (empty for Linux default namespace)
            
        Returns:
            List[Dict[str, Any]]: List of routes as dictionaries
        """
        try:
            # This is a placeholder implementation
            # In a real implementation, you would query the system or VPP API
            # to retrieve the actual routes
            if not container:
                # Get Linux routes
                pass
            else:
                # Get Docker container routes
                pass
            
            return []
            
        except Exception as e:
            log.error(f"Exception getting routes: {e}")
            return []

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

        # # Ensure the route does not already exist
        # existing_routes = self.get_all_routes(frr_container_name)
        # for route in existing_routes:
        #     if (
        #         route.get("destination_network") == local_bgp_loop_ip
        #         and route.get("next_hop_address") == frr_container_ip_address
        #     ):
        #         log.info(f"Route already exists: {local_bgp_loop_ip} via {frr_container_ip_address}")
        #         return
        # log.info(f"Adding route for BGP communication: {local_bgp_loop_ip} via {frr_container_ip_address}")
        # # Add the route to the FRR container

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
        log.info(
            f"Added iptables rule to allow forwarding from wg0 to docker0 for FRR container {frr_container_name}"
        )
        # adding route2
        self.add_linux_route(
            rr_wg_ip,
            host_ip_from_docker_container,
            "",
            frr_container_name,
        )
        log.info(f"Added route to RR wireguard IP {rr_wg_ip} via {host_ip_from_docker_container} in FRR container {frr_container_name}")
        # adding route3
        self.add_linux_route(
            rr_bgp_loop_ip,
            host_ip_from_docker_container,
            "",
            frr_container_name,
        )
        log.info(f"Added route to RR BGP loop IP {rr_bgp_loop_ip} via {host_ip_from_docker_container} in FRR container {frr_container_name}")

    def add_ebgp_route_in_frr_container(self, client_loop_ip: str, outgoing_interface: str, frr_container_name: str = "frr"):
        """
        Add a route in the FRR container for eBGP communication.
        
        Args:
            client_loop_ip: Client loopback IP address
            frr_container_name: Name of the FRR container (default: 'frr')
        """
        # Ensure the route does not already exist
        # existing_routes = self.get_all_routes(frr_container_name)
        # for route in existing_routes:
        #     if (
        #         route.get("destination_network") == client_loop_ip
        #         and route.get("next_hop_address") == ""
        #     ):
        #         log.info(f"Route already exists: {client_loop_ip}")
        #         return
        
        log.info(f"Adding eBGP route for client loop IP: {client_loop_ip} in FRR container {frr_container_name}")
        if self.add_linux_route(client_loop_ip, "", outgoing_interface, frr_container_name):
            log.info(f"Successfully added eBGP route for client loop IP: {client_loop_ip} in FRR container {frr_container_name}")
        else:
            log.error(f"Failed to add eBGP route for client loop IP: {client_loop_ip} in FRR container {frr_container_name}")
            return False
    def add_ebgp_routes_in_vpp(
        self,
        client_loop_ip: str,
        client_interface_ip: str,
        outgoing_interface: str,
    ) -> bool:
        """
        Add eBGP routes in VPP for communication with the client.
        
        Args:
            client_loop_ip: Client loopback IP address
            client_ip: Client IP address
            outgoing_interface: Outgoing interface name
            
        Returns:
            bool: True if routes added successfully, False otherwise
        """
        try:
            # Add route to client loopback IP
            client_loop_ip = f"{client_loop_ip}/32"
            if not self.add_vpp_route(client_loop_ip, client_interface_ip, outgoing_interface):
                return False

            log.info(f"Added eBGP routes for client {client_loop_ip} via {outgoing_interface}")
            return True
            
        except Exception as e:
            log.error(f"Exception adding eBGP routes in VPP: {e}")
            return False
    
    