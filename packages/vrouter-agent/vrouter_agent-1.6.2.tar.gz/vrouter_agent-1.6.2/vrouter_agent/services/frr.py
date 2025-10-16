# from vrouter_agent.utils.helpers import run_frr_command
# from typing import List, Optional
# from loguru import logger as log
# from vrouter_agent.core.models import OSPFConfig
# from pydantic import BaseModel
# from typing import List, Optional
# from vrouter_agent.core.config import settings 
# from vrouter_agent.core.base import CreatedWireguardTunnel



# class FRR:
#     container_name: str = "frr"
#     namespace: str = "frr"
#     namespace_dir: str = "/run/netns/frr"
#     container_image: str = "public.ecr.aws/v3c4v9y4/frr:latest"

#     def __init__(
#         self,
#         ospf_config: OSPFConfig,
#         wireguard_tunnels: List[CreatedWireguardTunnel],
#     ):
#         self.ospf_config = ospf_config
#         self.wireguard_tunnels = wireguard_tunnels
#         self.route_reflector = settings.config.route_reflector
#         self.route_reflector_controller = settings.config.route_reflector_controller
#         self.vpp_lan_interface = settings.config.interfaces["lan_primary"]

#     def _run_frr_command(self, commands: List[str]):
#         """Helper method to run FRR commands."""
#         command_string = "\n".join(commands)
#         run_frr_command(command_string, self.container_name)

#     def _configure_interface(
#         self, interface_name: str, ip_address: str, ospf_area: Optional[str] = None
#     ):
#         """Helper method to configure an interface."""
#         commands = [
#             "enable",
#             "configure terminal",
#             f"interface {interface_name}",
#             f"ip address {ip_address}",
#         ]

#         if ospf_area:
#             commands += [
#                 f"ip ospf 1 area {ospf_area}",
#                 "ip ospf network point-to-point",
#                 "ip ospf hello-interval 2",
#                 "ip ospf dead-interval 8",
#                 "ip ospf cost 10",
#             ]

#         if self._run_frr_command(commands):
#             log.info(f"Added interface {interface_name} with IP address {ip_address}")

#     def add_loopback_interface(self):
#         """Add a loopback interface."""
#         self._configure_interface("lo", self.route_reflector.loopback + "/24")
#         # add ip ospf 2 area 0.0.0.0
#         commands = [
#             "enable",
#             "configure terminal",
#             "interface lo",
#             f"ip ospf 2 area 0.0.0.0",
#         ]
#         self._run_frr_command(commands)

#         log.info(
#             f"Added loopback interface with IP address {self.route_reflector.loopback}"
#         )

#     def add_ospf_config(self):
#         """Add core OSPF configuration."""
#         commands = [
#             "enable",
#             "configure terminal",
#             "router ospf 2",
#             f"router-id {self.ospf_config.router_id}",
#             "exit",
#         ]
#         self._run_frr_command(commands)

#     def add_address_family(self):
#         """Add BGP address-family configuration."""

#         def get_lan_network(ip_addr: str) -> str:
#             ip_parts = ip_addr.split(".")
#             ip_parts[-1] = "0"
#             return ".".join(ip_parts) + "/24"

#         commands = [
#             "enable",
#             "configure terminal",
#             "router bgp 64512",
#             "address-family ipv4 unicast",
#             f"network {get_lan_network(self.vpp_lan_interface.ip_address)}",
#             "redistribute ospf 1",
#             "exit-address-family",
#         ]
#         self._run_frr_command(commands)

#     def add_core_bgp_config(self):
#         """Add core BGP configuration including BGP neighbor."""
#         commands = [
#             "enable",
#             "configure terminal",
#             "router bgp 64512",
#             f"bgp router-id {self.route_reflector.loopback}",
#             f"neighbor {self.route_reflector_controller.loopback.split('/')[0]} remote-as internal",
#             f"neighbor {self.route_reflector_controller.loopback.split('/')[0]} update-source lo",
#             "neighbor "
#             + self.route_reflector_controller.loopback.split("/")[0]
#             + " timers connect 10",
#         ]
#         self._run_frr_command(commands)

#     def add_client_ospf_config(self):
#         """Add client OSPF configuration."""

#         self._configure_interface(
#             self.vpp_lan_interface.interface_name,
#             f"{self.vpp_lan_interface.ip_address}/{self.vpp_lan_interface.prefix_len}",
#             self.ospf_config.client_router_area,
#         )

#         commands = [
#             "enable",
#             "configure terminal",
#             "router ospf 1",
#             f"router-id {self.ospf_config.client_router_id}",
#             "redistribute bgp",
#             "exit",
#         ]
#         self._run_frr_command(commands)

#     def add_wireguard_config(
#         self,
#         interface_name: str,
#         ip_addr: str,
#     ):
#         """Add WireGuard interface configuration."""
#         self._configure_interface(interface_name, ip_addr)

#         commands = [
#             "enable",
#             "configure terminal",
#             f"interface {interface_name}",
#             "ip ospf 2 area 0.0.0.0",
#             "ip ospf hello-interval 2",
#             "ip ospf dead-interval 8",
#             "ip ospf cost 10",
#             "ip ospf network point-to-point",
#             "exit",
#         ]
#         self._run_frr_command(commands)

#     def apply_all_configs(self):
#         self.add_loopback_interface()
#         self.add_ospf_config()
#         self.add_address_family()
#         self.add_core_bgp_config()
#         if self.ospf_config.client_enabled:
#             self.add_client_ospf_config()
#         for wg in self.wireguard_tunnels:
#             self.add_wireguard_config(wg.name, wg.ip_address)
#         log.info("All FRR configurations applied successfully!")

#     def delete_all_configs(self):
#         """Delete all FRR configurations."""

#         # delete core OSPF configuration
#         commands = [
#             "enable",
#             "configure terminal",
#             "no router ospf 2",
#             "no router ospf 1",
#             "exit",
#         ]
#         self._run_frr_command(commands)

#         log.info("All FRR configurations deleted successfully!")



from typing import List, Optional, Dict, Any, Union
from loguru import logger as log
from ipaddress import IPv4Address, IPv4Network, IPv4Interface
from pydantic import BaseModel

from vrouter_agent.utils.helpers import run_frr_command
from vrouter_agent.core.frr_config import (
    OspfConfig, OspfArea, OspfInterface, OspfRedistribution,
    BgpConfig, BgpPeer, BgpNetwork, BgpRedistribution,
    InterfaceBase, RouterId, FrrDeviceConfig
)
from vrouter_agent.core.config import settings
from vrouter_agent.core.base import CreatedWireguardTunnel


class FRRCommandResult(BaseModel):
    """Model for FRR command execution results"""
    success: bool
    output: str = ""
    error: str = ""


class FRR:
    """Enhanced FRR management class to handle comprehensive FRR configurations"""
    
    container_name: str = "frr"
    namespace: str = "frr"
    namespace_dir: str = "/run/netns/frr"
    container_image: str = "public.ecr.aws/v3c4v9y4/frr:latest"

    def __init__(
        self,
        device_config: Optional[FrrDeviceConfig] = None,
        ospf_config: Optional[OspfConfig] = None,
        bgp_config: Optional[BgpConfig] = None,
        interfaces: Optional[List[InterfaceBase]] = None,
        wireguard_tunnels: Optional[List[CreatedWireguardTunnel]] = None,
    ):
        """
        Initialize FRR with either a comprehensive device configuration or individual components.
        
        Args:
            device_config: Complete FRR device configuration
            ospf_config: OSPF configuration if not using device_config
            bgp_config: BGP configuration if not using device_config
            interfaces: List of interface configurations if not using device_config
            wireguard_tunnels: List of wireguard tunnel configurations
        """
        if device_config:
            self.device_config = device_config
            self.ospf_config = device_config.ospf
            self.bgp_config = device_config.bgp
            self.interfaces = device_config.interfaces
        else:
            self.ospf_config = ospf_config
            self.bgp_config = bgp_config
            self.interfaces = interfaces or []
            self.device_config = None
            
        self.wireguard_tunnels = wireguard_tunnels or []
        
        # Load settings for backward compatibility
        if hasattr(settings, 'config'):
            self.route_reflector = getattr(settings.config, 'route_reflector', None)
            self.route_reflector_controller = getattr(settings.config, 'route_reflector_controller', None)
            self.vpp_lan_interface = getattr(settings.config, 'interfaces', {}).get('lan_primary')
        else:
            self.route_reflector = None
            self.route_reflector_controller = None
            self.vpp_lan_interface = None

    def run_frr_command(self, commands: List[str]) -> FRRCommandResult:
        """
        Execute FRR commands with improved error handling and feedback.
        
        Args:
            commands: List of FRR commands to execute
            
        Returns:
            FRRCommandResult: Result object with success status and output/error
        """
        command_string = "\n".join(commands)
        
        try:
            output = run_frr_command(command_string, self.container_name)
            log.debug(f"FRR command executed successfully: {commands}")
            return FRRCommandResult(success=True, output=output)
        except Exception as e:
            error_msg = f"Failed to execute FRR command: {e}"
            log.error(error_msg)
            return FRRCommandResult(success=False, error=error_msg)

    def configure_interface(
        self, 
        interface_name: str, 
        ip_address: str, 
        ospf_area: Optional[str] = None,
        ospf_process_id: int = 1,
        hello_interval: int = 10,
        dead_interval: int = 40,
        cost: int = 10,
        network_type: str = "point-to-point",
        passive: bool = False,
        description: Optional[str] = None,
    ) -> FRRCommandResult:
        """
        Configure a network interface with enhanced options.
        
        Args:
            interface_name: Name of the interface to configure
            ip_address: IP address with CIDR notation (e.g., '192.168.1.1/24')
            ospf_area: OSPF area ID (if applicable)
            ospf_process_id: OSPF process ID
            hello_interval: OSPF hello interval in seconds
            dead_interval: OSPF dead interval in seconds
            cost: OSPF interface cost
            network_type: OSPF network type
            passive: Whether the interface should be passive in OSPF
            description: Interface description
            
        Returns:
            FRRCommandResult: Result of the configuration operation
        """
        commands = [
            "enable",
            "configure terminal",
            f"interface {interface_name}",
            f"ip address {ip_address}",
        ]
        
        if description:
            commands.append(f"description {description}")

        if ospf_area:
            commands.extend([
                f"ip ospf {ospf_process_id} area {ospf_area}",
                f"ip ospf network {network_type}",
                f"ip ospf hello-interval {hello_interval}",
                f"ip ospf dead-interval {dead_interval}",
                f"ip ospf cost {cost}",
            ])
            
            if passive:
                commands.append("ip ospf passive")

        result = self.run_frr_command(commands)
        if result.success:
            log.info(f"Configured interface {interface_name} with IP address {ip_address}")
        
        return result

    def add_loopback_interface(self, ip_address: str, ospf_area: str = "0.0.0.0", ospf_process_id: int = 1) -> FRRCommandResult:
        """
        Add and configure a loopback interface.
        
        Args:
            ip_address: IP address for the loopback interface
            ospf_area: OSPF area ID for the loopback
            ospf_process_id: OSPF process ID
            
        Returns:
            FRRCommandResult: Result of the operation
        """
        # First create the basic loopback interface
        result = self.configure_interface("lo", ip_address)
        if not result.success:
            return result
        
        # Then add OSPF configuration if needed
        if ospf_area:
            commands = [
                "enable",
                "configure terminal",
                "interface lo",
                f"ip ospf {ospf_process_id} area {ospf_area}",
            ]
            result = self.run_frr_command(commands)
            
        if result.success:
            log.info(f"Added loopback interface with IP address {ip_address}")
            
        return result

    def configure_ospf(self, config: OspfConfig) -> FRRCommandResult:
        """
        Configure OSPF with comprehensive options.
        
        Args:
            config: Complete OSPF configuration
            
        Returns:
            FRRCommandResult: Result of the operation
        """
        commands = [
            "enable",
            "configure terminal",
            f"router ospf {config.process_id}",
            f"router-id {config.router_id}",
        ]
        
        # Add reference bandwidth if specified
        if config.reference_bandwidth:
            commands.append(f"auto-cost reference-bandwidth {config.reference_bandwidth}")
            
        # Set passive interface default if specified
        if config.passive_interfaces_default:
            commands.append("passive-interface default")
            
        # Configure passive interfaces
        if config.passive_interfaces:
            for interface in config.passive_interfaces:
                commands.append(f"passive-interface {interface}")
                
        # Configure non-passive interfaces
        if config.no_passive_interfaces:
            for interface in config.no_passive_interfaces:
                commands.append(f"no passive-interface {interface}")
                
        # Configure redistribution
        if config.redistribute:
            for redist in config.redistribute:
                redist_cmd = f"redistribute {redist.protocol}"
                if redist.metric:
                    redist_cmd += f" metric {redist.metric}"
                if redist.metric_type:
                    redist_cmd += f" metric-type {redist.metric_type}"
                if redist.route_map:
                    redist_cmd += f" route-map {redist.route_map}"
                commands.append(redist_cmd)
                
        # Configure default information originate
        if config.default_information_originate:
            commands.append("default-information originate")
            
        commands.append("exit")
        
        result = self.run_frr_command(commands)
        if result.success:
            log.info(f"Configured OSPF process {config.process_id} with router ID {config.router_id}")
            
        return result

    def configure_bgp(self, config: BgpConfig) -> FRRCommandResult:
        """
        Configure BGP with comprehensive options.
        
        Args:
            config: Complete BGP configuration
            
        Returns:
            FRRCommandResult: Result of the operation
        """
        commands = [
            "enable",
            "configure terminal",
            f"router bgp {config.local_as}",
            f"bgp router-id {config.router_id}",
        ]
        
        # Configure BGP settings
        if config.log_neighbor_changes:
            commands.append("bgp log-neighbor-changes")
            
        if config.deterministic_med:
            commands.append("bgp deterministic-med")
            
        if config.always_compare_med:
            commands.append("bgp always-compare-med")
            
        # Configure BGP peers
        for peer in config.peers:
            peer_cmd = f"neighbor {peer.peer_ip} remote-as {peer.remote_as}"
            commands.append(peer_cmd)
            
            if peer.description:
                commands.append(f"neighbor {peer.peer_ip} description {peer.description}")
                
            if peer.update_source:
                commands.append(f"neighbor {peer.peer_ip} update-source {peer.update_source}")
                
            if peer.next_hop_self:
                commands.append(f"neighbor {peer.peer_ip} next-hop-self")
                
            if peer.ebgp_multihop:
                commands.append(f"neighbor {peer.peer_ip} ebgp-multihop {peer.ebgp_multihop}")
                
            if peer.password:
                commands.append(f"neighbor {peer.peer_ip} password {peer.password}")
                
            if peer.timers:
                keepalive = peer.timers.get("keepalive", 60)
                holdtime = peer.timers.get("holdtime", 180)
                commands.append(f"neighbor {peer.peer_ip} timers {keepalive} {holdtime}")
            
            # Address family specific configurations
            commands.append("address-family ipv4 unicast")
            
            if peer.route_map_in:
                commands.append(f"neighbor {peer.peer_ip} route-map {peer.route_map_in} in")
                
            if peer.route_map_out:
                commands.append(f"neighbor {peer.peer_ip} route-map {peer.route_map_out} out")
                
            if peer.prefix_list_in:
                commands.append(f"neighbor {peer.peer_ip} prefix-list {peer.prefix_list_in} in")
                
            if peer.prefix_list_out:
                commands.append(f"neighbor {peer.peer_ip} prefix-list {peer.prefix_list_out} out")
                
            commands.append("exit-address-family")
            
        # Configure networks
        if config.networks:
            commands.append("address-family ipv4 unicast")
            for network in config.networks:
                net_cmd = f"network {network.network}"
                if network.route_map:
                    net_cmd += f" route-map {network.route_map}"
                commands.append(net_cmd)
            
            # Configure redistribution
            if config.redistribute:
                for redist in config.redistribute:
                    redist_cmd = f"redistribute {redist.protocol}"
                    if redist.metric:
                        redist_cmd += f" metric {redist.metric}"
                    if redist.route_map:
                        redist_cmd += f" route-map {redist.route_map}"
                    commands.append(redist_cmd)
                    
            commands.append("exit-address-family")
            
        commands.append("exit")
        
        result = self.run_frr_command(commands)
        if result.success:
            log.info(f"Configured BGP AS {config.local_as} with router ID {config.router_id}")
            
        return result

    def configure_address_family(self, asn: int, networks: List[str], redistribute: List[Dict[str, Any]] = None) -> FRRCommandResult:
        """
        Configure BGP address family with specific networks and redistribution.
        
        Args:
            asn: BGP autonomous system number
            networks: List of networks to advertise (in CIDR notation)
            redistribute: List of redistribution configurations
            
        Returns:
            FRRCommandResult: Result of the operation
        """
        commands = [
            "enable",
            "configure terminal",
            f"router bgp {asn}",
            "address-family ipv4 unicast",
        ]
        
        # Add networks
        for network in networks:
            commands.append(f"network {network}")
            
        # Add redistributions
        if redistribute:
            for redist in redistribute:
                redist_cmd = f"redistribute {redist['protocol']}"
                if 'metric' in redist:
                    redist_cmd += f" metric {redist['metric']}"
                if 'route_map' in redist:
                    redist_cmd += f" route-map {redist['route_map']}"
                commands.append(redist_cmd)
                
        commands.append("exit-address-family")
        commands.append("exit")
        
        result = self.run_frr_command(commands)
        if result.success:
            log.info(f"Configured address-family ipv4 unicast for BGP AS {asn}")
            
        return result

    def configure_route_map(self, name: str, sequence: int, action: str, match_conditions: Dict[str, Any] = None, set_actions: Dict[str, Any] = None) -> FRRCommandResult:
        """
        Configure a route-map with match and set clauses.
        
        Args:
            name: Name of the route-map
            sequence: Sequence number
            action: 'permit' or 'deny'
            match_conditions: Dictionary of match conditions
            set_actions: Dictionary of set actions
            
        Returns:
            FRRCommandResult: Result of the operation
        """
        commands = [
            "enable",
            "configure terminal",
            f"route-map {name} {action} {sequence}",
        ]
        
        # Add match conditions
        if match_conditions:
            for condition, value in match_conditions.items():
                if isinstance(value, list):
                    for item in value:
                        commands.append(f"match {condition} {item}")
                else:
                    commands.append(f"match {condition} {value}")
                    
        # Add set actions
        if set_actions:
            for action_name, value in set_actions.items():
                if isinstance(value, list):
                    for item in value:
                        commands.append(f"set {action_name} {item}")
                else:
                    commands.append(f"set {action_name} {value}")
                    
        commands.append("exit")
        
        result = self.run_frr_command(commands)
        if result.success:
            log.info(f"Configured route-map {name} {action} {sequence}")
            
        return result

    def configure_access_list(self, name: str, entries: List[Dict[str, Any]]) -> FRRCommandResult:
        """
        Configure an access list with multiple entries.
        
        Args:
            name: Name or number of the access list
            entries: List of access list entries
            
        Returns:
            FRRCommandResult: Result of the operation
        """
        commands = [
            "enable",
            "configure terminal",
        ]
        
        for entry in entries:
            action = entry.get("action", "permit")
            prefix = entry.get("prefix", "")
            commands.append(f"access-list {name} {action} {prefix}")
            
        commands.append("exit")
        
        result = self.run_frr_command(commands)
        if result.success:
            log.info(f"Configured access-list {name} with {len(entries)} entries")
            
        return result

    def configure_prefix_list(self, name: str, entries: List[Dict[str, Any]]) -> FRRCommandResult:
        """
        Configure a prefix list with multiple entries.
        
        Args:
            name: Name of the prefix list
            entries: List of prefix list entries
            
        Returns:
            FRRCommandResult: Result of the operation
        """
        commands = [
            "enable",
            "configure terminal",
        ]
        
        for entry in entries:
            seq = entry.get("seq", "")
            action = entry.get("action", "permit")
            prefix = entry.get("prefix", "")
            le = entry.get("le", "")
            ge = entry.get("ge", "")
            
            cmd = f"ip prefix-list {name}"
            if seq:
                cmd += f" seq {seq}"
            cmd += f" {action} {prefix}"
            if le:
                cmd += f" le {le}"
            if ge:
                cmd += f" ge {ge}"
                
            commands.append(cmd)
            
        commands.append("exit")
        
        result = self.run_frr_command(commands)
        if result.success:
            log.info(f"Configured prefix-list {name} with {len(entries)} entries")
            
        return result

    def configure_static_route(self, prefix: str, next_hop: str) -> FRRCommandResult:
        """
        Configure a static route.
        
        Args:
            prefix: Destination prefix in CIDR notation
            next_hop: Next hop IP address or interface
            
        Returns:
            FRRCommandResult: Result of the operation
        """
        commands = [
            "enable",
            "configure terminal",
            f"ip route {prefix} {next_hop}",
            "exit",
        ]
        
        result = self.run_frr_command(commands)
        if result.success:
            log.info(f"Configured static route for {prefix} via {next_hop}")
            
        return result

    def configure_wireguard_interface(self, tunnel: CreatedWireguardTunnel, ospf_area: str = "0.0.0.0", ospf_process_id: int = 2) -> FRRCommandResult:
        """
        Configure a WireGuard tunnel interface.
        
        Args:
            tunnel: WireGuard tunnel configuration
            ospf_area: OSPF area ID
            ospf_process_id: OSPF process ID
            
        Returns:
            FRRCommandResult: Result of the operation
        """
        # First configure the basic interface
        result = self.configure_interface(
            tunnel.name,
            tunnel.ip_address,
            ospf_area=ospf_area,
            ospf_process_id=ospf_process_id,
            hello_interval=2,
            dead_interval=8,
            cost=10,
            network_type="point-to-point",
            description=f"WireGuard tunnel to {tunnel.peer_public_key[:8]}..."
        )
        
        return result

    def apply_legacy_config(self) -> bool:
        """
        Apply the legacy configuration for backward compatibility.
        
        Returns:
            bool: True if all configurations were applied successfully, False otherwise
        """
        success = True
        
        # Add loopback interface
        if self.route_reflector and hasattr(self.route_reflector, 'loopback'):
            result = self.add_loopback_interface(
                self.route_reflector.loopback + "/24", 
                ospf_area="0.0.0.0", 
                ospf_process_id=2
            )
            success = success and result.success
        
        # Add OSPF config
        if self.ospf_config:
            ospf_config = OspfConfig(
                process_id=2,
                router_id=self.ospf_config.router_id,
                areas=[OspfArea(area_id="0.0.0.0")],
                interfaces=[]
            )
            result = self.configure_ospf(ospf_config)
            success = success and result.success
        
        # Add address family
        if self.vpp_lan_interface:
            ip_parts = self.vpp_lan_interface.ip_address.split(".")
            ip_parts[-1] = "0"
            network = ".".join(ip_parts) + "/24"
            
            result = self.configure_address_family(
                64512, 
                [network],
                [{"protocol": "ospf", "ospf_id": 1}]
            )
            success = success and result.success
        
        # Add core BGP config
        if self.route_reflector and self.route_reflector_controller:
            commands = [
                "enable",
                "configure terminal",
                "router bgp 64512",
                f"bgp router-id {self.route_reflector.loopback}",
                f"neighbor {self.route_reflector_controller.loopback.split('/')[0]} remote-as internal",
                f"neighbor {self.route_reflector_controller.loopback.split('/')[0]} update-source lo",
                "neighbor " + self.route_reflector_controller.loopback.split("/")[0] + " timers connect 10",
                "exit"
            ]
            result = self.run_frr_command(commands)
            success = success and result.success
        
        # Add client OSPF config if enabled
        if self.ospf_config and getattr(self.ospf_config, 'client_enabled', False):
            if self.vpp_lan_interface:
                result = self.configure_interface(
                    self.vpp_lan_interface.interface_name,
                    f"{self.vpp_lan_interface.ip_address}/{self.vpp_lan_interface.prefix_len}",
                    ospf_area=self.ospf_config.client_router_area,
                    ospf_process_id=1
                )
                success = success and result.success
            
            commands = [
                "enable",
                "configure terminal",
                "router ospf 1",
                f"router-id {self.ospf_config.client_router_id}",
                "redistribute bgp",
                "exit"
            ]
            result = self.run_frr_command(commands)
            success = success and result.success
        
        # Configure WireGuard tunnels
        for wg in self.wireguard_tunnels:
            result = self.configure_wireguard_interface(wg)
            success = success and result.success
        
        if success:
            log.info("All legacy FRR configurations applied successfully!")
        else:
            log.error("Some legacy FRR configurations failed to apply.")
        
        return success

    def apply_config(self) -> bool:
        """
        Apply comprehensive FRR configuration.
        
        Returns:
            bool: True if all configurations were applied successfully, False otherwise
        """
        if not self.device_config:
            return self.apply_legacy_config()
        
        success = True
        
        # Configure interfaces
        for interface in self.interfaces:
            result = self.configure_interface(
                interface.name,
                f"{interface.ip_address}/{interface.subnet_mask.prefixlen}",
                description=interface.description
            )
            success = success and result.success
        
        # Configure OSPF
        if self.ospf_config:
            result = self.configure_ospf(self.ospf_config)
            success = success and result.success
            
            # Configure OSPF interfaces
            for ospf_iface in self.ospf_config.interfaces:
                # Find the corresponding interface
                for iface in self.interfaces:
                    if iface.name == ospf_iface.interface_name:
                        result = self.configure_interface(
                            ospf_iface.interface_name,
                            f"{iface.ip_address}/{iface.subnet_mask.prefixlen}",
                            ospf_area=ospf_iface.area_id,
                            ospf_process_id=self.ospf_config.process_id,
                            hello_interval=ospf_iface.hello_interval,
                            dead_interval=ospf_iface.dead_interval,
                            cost=ospf_iface.cost,
                            passive=ospf_iface.passive
                        )
                        success = success and result.success
                        break
        
        # Configure BGP
        if self.bgp_config:
            result = self.configure_bgp(self.bgp_config)
            success = success and result.success
        
        # Configure static routes
        if self.device_config and self.device_config.static_routes:
            for prefix, next_hop in self.device_config.static_routes.items():
                result = self.configure_static_route(str(prefix), str(next_hop))
                success = success and result.success
        
        # Configure route maps
        if self.device_config and self.device_config.route_maps:
            for route_map in self.device_config.route_maps:
                result = self.configure_route_map(
                    route_map.name,
                    route_map.sequence,
                    route_map.action,
                    route_map.match_conditions,
                    route_map.set_actions
                )
                success = success and result.success
        
        # Configure access lists
        if self.device_config and self.device_config.access_lists:
            for access_list in self.device_config.access_lists:
                result = self.configure_access_list(access_list.name, access_list.entries)
                success = success and result.success
        
        # Configure prefix lists
        if self.device_config and self.device_config.prefix_lists:
            for prefix_list in self.device_config.prefix_lists:
                result = self.configure_prefix_list(prefix_list.name, prefix_list.entries)
                success = success and result.success
        
        # Configure WireGuard tunnels
        for wg in self.wireguard_tunnels:
            result = self.configure_wireguard_interface(wg)
            success = success and result.success
        
        if success:
            log.info("All FRR configurations applied successfully!")
        else:
            log.error("Some FRR configurations failed to apply.")
        
        return success

    def clear_config(self) -> bool:
        """
        Clear all FRR configurations.
        
        Returns:
            bool: True if all configurations were cleared successfully, False otherwise
        """
        commands = [
            "enable",
            "configure terminal",
            "no router ospf 1",
            "no router ospf 2",
            "no router bgp 64512",
            "exit"
        ]
        
        result = self.run_frr_command(commands)
        if result.success:
            log.info("All FRR configurations cleared successfully!")
        else:
            log.error("Failed to clear FRR configurations.")
        
        return result.success
