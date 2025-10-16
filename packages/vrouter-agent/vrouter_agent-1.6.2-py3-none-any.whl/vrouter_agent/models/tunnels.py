"""
Tunnel, Topology, and Network models for FastAPI SQLModel.
"""

from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum
from .base import BaseModel


class TopologyType(str, Enum):
    HUB_SPOKE = "hub_spoke"
    POINT_TO_POINT = "point_to_point"
    FULL_MESH = "full_mesh"
    PARTIAL_MESH = "partial_mesh"


class TunnelType(str, Enum):
    WIREGUARD = "wireguard"
    IPSEC = "ipsec"
    GRE = "gre"
    VXLAN = "vxlan"
    OPENVPN = "openvpn"


class TunnelState(str, Enum):
    PLANNED = "planned"
    CONFIGURED = "configured"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class Network(BaseModel, table=True):
    """Network model equivalent to Django Network model"""

    __tablename__ = "networks"

    name: str = Field(max_length=100)
    cidr: str = Field(max_length=18, description="Network CIDR (e.g., 192.168.1.0/24)")
    description: Optional[str]

    # Relationships
    tunnels: List["Tunnel"] = Relationship(back_populates="tunnel_network")


class Topology(BaseModel, table=True):
    """Topology model equivalent to Django Topology model"""

    __tablename__ = "topologies"

    name: str = Field(max_length=100)
    topology_type: TopologyType
    description: Optional[str]
    hub_node_id: Optional[int] = Field(foreign_key="devices.id")
    is_active: bool = Field(default=True)

    # Relationships
    hub_node: Optional["Device"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "Topology.hub_node_id",
            "post_update": True,
        }
    )
    tunnels: List["Tunnel"] = Relationship(back_populates="topology")
    orders: List["Order"] = Relationship(back_populates="topology")


class Tunnel(BaseModel, table=True):
    """Tunnel model equivalent to Django Tunnel model"""

    __tablename__ = "tunnels"

    name: Optional[str] = Field(max_length=100)
    tunnel_type: TunnelType

    # Relationships
    topology_id: Optional[int] = Field(foreign_key="topologies.id")
    topology: Optional[Topology] = Relationship(back_populates="tunnels")

    # Node relationships
    local_node_id: Optional[int] = Field(foreign_key="devices.id")
    remote_node_id: Optional[int] = Field(foreign_key="devices.id")
    local_node: Optional["Device"] = Relationship(
        back_populates="local_tunnels",
        sa_relationship_kwargs={"foreign_keys": "Tunnel.local_node_id"},
    )
    remote_node: Optional["Device"] = Relationship(
        back_populates="remote_tunnels",
        sa_relationship_kwargs={"foreign_keys": "Tunnel.remote_node_id"},
    )

    # Interface relationships
    local_interface_id: Optional[int] = Field(foreign_key="interfaces.id")
    remote_interface_id: Optional[int] = Field(foreign_key="interfaces.id")
    local_wan_interface_id: Optional[int] = Field(foreign_key="interfaces.id")
    remote_wan_interface_id: Optional[int] = Field(foreign_key="interfaces.id")

    local_interface: Optional["Interface"] = Relationship(
        back_populates="local_tunnels",
        sa_relationship_kwargs={"foreign_keys": "Tunnel.local_interface_id"},
    )
    remote_interface: Optional["Interface"] = Relationship(
        back_populates="remote_tunnels",
        sa_relationship_kwargs={"foreign_keys": "Tunnel.remote_interface_id"},
    )
    local_wan_interface: Optional["Interface"] = Relationship(
        back_populates="local_wan_tunnels",
        sa_relationship_kwargs={"foreign_keys": "Tunnel.local_wan_interface_id"},
    )
    remote_wan_interface: Optional["Interface"] = Relationship(
        back_populates="remote_wan_tunnels",
        sa_relationship_kwargs={"foreign_keys": "Tunnel.remote_wan_interface_id"},
    )

    # Network relationship
    tunnel_network_id: Optional[int] = Field(foreign_key="networks.id")
    tunnel_network: Optional[Network] = Relationship(back_populates="tunnels")

    # IP configuration
    local_tunnel_ip: Optional[str] = Field(description="Local tunnel IP address")
    remote_tunnel_ip: Optional[str] = Field(description="Remote tunnel IP address")

    # WireGuard specific settings
    local_public_key: Optional[str]
    local_private_key: Optional[str]
    remote_public_key: Optional[str]
    remote_private_key: Optional[str]  # Temporarily stored for blockchain publishing
    listen_port: Optional[int] = Field(ge=1, le=65535)

    # General tunnel settings
    mtu: int = Field(default=1420)
    keepalive_interval: int = Field(default=25)
    state: TunnelState = Field(default=TunnelState.PLANNED)
    is_enabled: bool = Field(default=True)


# Import here to avoid circular imports
from .devices import Device, Interface
from .orders import Order

# Rebuild models to resolve forward references
Network.model_rebuild()
Topology.model_rebuild()
Tunnel.model_rebuild()
