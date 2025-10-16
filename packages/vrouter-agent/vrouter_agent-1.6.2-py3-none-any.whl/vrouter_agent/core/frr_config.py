from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Union, Literal
from ipaddress import IPv4Address, IPv4Network


# Base models for common attributes
class RouterId(BaseModel):
    router_id: IPv4Address


class InterfaceBase(BaseModel):
    name: str
    description: Optional[str] = None
    ip_address: IPv4Address
    subnet_mask: IPv4Network
    enabled: bool = True


# OSPF specific models
class OspfArea(BaseModel):
    area_id: Union[int, str]  # Can be either numeric (0) or dotted decimal (0.0.0.0)
    area_type: Optional[Literal["normal", "stub", "nssa"]] = "normal"
    authentication: Optional[bool] = False


class OspfInterface(BaseModel):
    interface_name: str
    area_id: Union[int, str]
    hello_interval: Optional[int] = 10
    dead_interval: Optional[int] = 40
    priority: Optional[int] = 1
    cost: Optional[int] = 10
    passive: Optional[bool] = False


class OspfRedistribution(BaseModel):
    protocol: Literal["bgp", "connected", "static", "kernel"]
    metric: Optional[int] = None
    metric_type: Optional[Literal[1, 2]] = None
    route_map: Optional[str] = None


class OspfConfig(RouterId):
    process_id: int = 1
    areas: List[OspfArea]
    interfaces: List[OspfInterface]
    redistribute: Optional[List[OspfRedistribution]] = None
    reference_bandwidth: Optional[int] = 100000  # in Mbps
    default_information_originate: Optional[bool] = False
    passive_interfaces_default: Optional[bool] = False
    passive_interfaces: Optional[List[str]] = None
    no_passive_interfaces: Optional[List[str]] = None


# BGP specific models
class BgpPeer(BaseModel):
    peer_ip: IPv4Address
    remote_as: int
    description: Optional[str] = None
    update_source: Optional[str] = None  # Interface name or IP
    next_hop_self: Optional[bool] = False
    ebgp_multihop: Optional[int] = None
    password: Optional[str] = None
    route_map_in: Optional[str] = None
    route_map_out: Optional[str] = None
    prefix_list_in: Optional[str] = None
    prefix_list_out: Optional[str] = None
    timers: Optional[Dict[str, int]] = None  # {'keepalive': 30, 'holdtime': 90}
    lan_interface_ip: Optional[str] = None
    lan_mac_address: Optional[str] = None


class BgpNetwork(BaseModel):
    network: IPv4Network
    route_map: Optional[str] = None


class BgpRedistribution(BaseModel):
    protocol: Literal["ospf", "connected", "static", "kernel"]
    metric: Optional[int] = None
    route_map: Optional[str] = None


class BgpConfig(RouterId):
    local_as: int
    peers: List[BgpPeer]
    networks: Optional[List[BgpNetwork]] = None
    redistribute: Optional[List[BgpRedistribution]] = None
    log_neighbor_changes: Optional[bool] = True
    deterministic_med: Optional[bool] = True
    always_compare_med: Optional[bool] = False

class ControllerBgpPeer(BgpPeer):
    loopback: IPv4Address
    
# Combined device configuration
class DeviceInterfaces(BaseModel):
    interfaces: List[InterfaceBase]


class RouteMap(BaseModel):
    name: str
    sequence: int
    action: Literal["permit", "deny"]
    match_conditions: Optional[Dict[str, Union[str, List[str]]]] = None
    set_actions: Optional[Dict[str, Union[str, int, List[str]]]] = None


class AccessList(BaseModel):
    name: str
    entries: List[Dict[str, Union[str, IPv4Network]]]


class PrefixList(BaseModel):
    name: str
    entries: List[Dict[str, Union[str, IPv4Network, int]]]


class FrrDeviceConfig(BaseModel):
    hostname: str
    interfaces: List[InterfaceBase]
    ospf: Optional[OspfConfig] = None
    bgp: Optional[BgpConfig] = None
    route_maps: Optional[List[RouteMap]] = None
    access_lists: Optional[List[AccessList]] = None
    prefix_lists: Optional[List[PrefixList]] = None
    static_routes: Optional[Dict[IPv4Network, Union[IPv4Address, str]]] = None


# Topology-specific models
class NodeConfig(FrrDeviceConfig):
    """Configuration for node 1 and node 2 devices"""
    controller_bgp: ControllerBgpPeer  # Connection to the controller
    loopback: IPv4Address  # Loopback address for the node
    node_interconnection: Union[OspfInterface, BgpPeer]  # Connection to the other node
    client_connections: List[Union[OspfInterface, BgpPeer]]  # Connections to clients


class ClientConfig(FrrDeviceConfig):
    """Configuration for client 1 and client 2 devices"""
    node_connection: Union[OspfInterface, BgpPeer]  # Connection to node


class InitialControllerConfig(BaseModel):
    """Configuration for the controller device"""
    loopback: IPv4Address  # Loopback address for the controller
    address: IPv4Address  # Address of the controller (wireguard tunnel)

class InitialNodeConfig(BaseModel):
    """Configuration for the node device"""
    local_asn: Optional[int] = 64512  # Local AS number for the node
    loopback_ip: IPv4Address  # Loopback address for the node
    loopback_mask: Optional[int] = 32  # Subnet mask for the loopback address
class InitialFRRConfig(BaseModel):
    """FRR configuration for the entire system."""
    controller: InitialControllerConfig
    node: InitialNodeConfig