from enum import Enum


class TunnelStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNKNOWN = "unknown"
    DELETED = "deleted"


class WireguardPeerStatus(str, Enum):
    ESTABLISHED = "established"
    DEAD = "dead"
    UNKNOWN = "unknown"


class TunnelType(str, Enum):
    WIREGUARD = "wireguard"
    VXLAN = "vxlan"
    GRE = "gre"
    IPIP = "ipip"
    IPSEC = "ipsec"
    L2TPV3 = "l2tpv3"
    OPENVPN = "openvpn"
    TINC = "tinc"
    ZEROTIER = "zerotier"
    UNKNOWN = "unknown"


class InterfaceStatus(str, Enum):
    UP = "up"
    DOWN = "down"
    UNKNOWN = "unknown"



class OrderStatus(str, Enum):
    REQUESTED = "requested"
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    INCOMPLETE = "incomplete"
    UNKNOWN = "unknown"
    DELETED = "deleted"

class OrderType(str, Enum):
    PROVISION = "provision"
    DECOMMISSION = "decommission"
    UPDATE = "update"
     
     

class StreamItemTag(str, Enum):
    """
    Enum for stream item tags
    """
    ORDER = "order"
    NETWORK = "network"
    INTERFACE = "interface"
    TUNNEL = "tunnel"
    TUNNEL_CONFIG = "tunnel_config"

class StreamItemAction(str, Enum):
    """
    Enum for stream item types
    """
    PROVISION= "provision"
    UPDATE = "update"
    DECOMMISSION = "decommission"
    REPLACE = "replace"
    REMOVE = "remove"
    RESTART = "restart"

    