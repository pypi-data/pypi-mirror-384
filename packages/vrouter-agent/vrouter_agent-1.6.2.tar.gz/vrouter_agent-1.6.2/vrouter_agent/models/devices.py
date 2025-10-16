"""
Device and Interface models for FastAPI SQLModel.
"""

from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum
from .base import BaseModel


class NodeType(str, Enum):
    HUB = "hub"
    SPOKE = "spoke"
    PEER = "peer"
    EDGE = "edge"
    TRANSIT = "transit"
    ENDPOINT = "endpoint"


class DeviceStatus(str, Enum):
    OPERATIONAL = "operational"
    WARNING = "warning"
    CRITICAL = "critical"
    ERROR = "error"


class InterfaceType(str, Enum):
    PHYSICAL = "physical"
    VLAN = "vlan"
    LOOPBACK = "loopback"
    TUNNEL = "tunnel"
    BRIDGE = "bridge"


class Device(BaseModel, table=True):
    """Device model equivalent to Django Device model"""

    __tablename__ = "devices"

    # Basic device information
    name: Optional[str] = Field(max_length=256, description="Friendly identifier")
    node_type: NodeType = Field(default=NodeType.PEER)
    management_ip: Optional[str] = Field(description="Management IP address")
    router_id: Optional[str] = Field(description="BGP/OSPF Router ID")
    asn: Optional[int] = Field(description="BGP AS Number", ge=1, le=4294967295)

    # Hardware/System information
    serial_number: Optional[str] = Field(max_length=200, unique=True)
    stream: Optional[str] = Field(max_length=100)
    hostname: str = Field(max_length=256, unique=True)
    fqdn: Optional[str] = Field(max_length=256, unique=True)
    manufacturer: Optional[str] = Field(max_length=256)
    model: Optional[str] = Field(max_length=256)
    firmware: Optional[str] = Field(max_length=256)
    domain: Optional[str] = Field(max_length=256)
    cpu_arch: Optional[str] = Field(max_length=256)
    os_codename: Optional[str] = Field(max_length=256)
    product_name: Optional[str] = Field(max_length=256)
    processor_type: Optional[str] = Field(max_length=256)
    num_cpus: Optional[int]
    core_count: Optional[int]
    ram_size: Optional[int]

    # Status and operational fields
    is_active: bool = Field(default=True)
    last_checked: Optional[str]  # ISO format datetime string
    status: DeviceStatus = Field(default=DeviceStatus.OPERATIONAL)
    status_text: str = Field(
        default="All systems operational",
        max_length=500,
        description="Human readable description of the device status",
    )

    # Relationships
    interfaces: List["Interface"] = Relationship(back_populates="device")
    local_tunnels: List["Tunnel"] = Relationship(
        back_populates="local_node",
        sa_relationship_kwargs={"foreign_keys": "Tunnel.local_node_id"},
    )
    remote_tunnels: List["Tunnel"] = Relationship(
        back_populates="remote_node",
        sa_relationship_kwargs={"foreign_keys": "Tunnel.remote_node_id"},
    )


class Interface(BaseModel, table=True):
    """Interface model equivalent to Django Interface model"""

    __tablename__ = "interfaces"

    # Device relationship
    device_id: Optional[int] = Field(foreign_key="devices.id")
    device: Optional[Device] = Relationship(back_populates="interfaces")

    # Interface classification
    is_management: bool = Field(
        default=False, description="Is this interface used for management purposes?"
    )
    is_wan: bool = Field(
        default=False, description="Is this interface used for WAN connectivity?"
    )
    is_lan: bool = Field(
        default=False, description="Is this interface used for LAN connectivity?"
    )
    is_primary: bool = Field(
        default=False,
        description="Is this the primary interface of its type (WAN or LAN)?",
    )

    # Interface details
    name: str = Field(max_length=256)
    type: InterfaceType = Field(
        default=InterfaceType.PHYSICAL,
        description="Type of interface (e.g. physical, vlan, loopback, tunnel, bridge)",
    )
    up: bool = Field(default=False)
    hwaddr: Optional[str] = Field(max_length=50, description="Hardware address")
    ip_address: Optional[str] = Field(description="IP address")
    subnet_mask: Optional[int] = Field(ge=1, le=32, description="Subnet mask CIDR")
    vlan_id: Optional[int] = Field(ge=1, le=4094, description="VLAN ID")
    mtu: int = Field(default=1500)

    # VPP specific fields
    vpp_used: bool = Field(default=False, description="Is this interface used by VPP?")
    vpp_interface_name: Optional[str] = Field(
        max_length=256, description="VPP interface name"
    )
    is_enabled: bool = Field(default=True)
    description: Optional[str]

    # Relationships
    local_tunnels: List["Tunnel"] = Relationship(
        back_populates="local_interface",
        sa_relationship_kwargs={"foreign_keys": "Tunnel.local_interface_id"},
    )
    remote_tunnels: List["Tunnel"] = Relationship(
        back_populates="remote_interface",
        sa_relationship_kwargs={"foreign_keys": "Tunnel.remote_interface_id"},
    )
    local_wan_tunnels: List["Tunnel"] = Relationship(
        back_populates="local_wan_interface",
        sa_relationship_kwargs={"foreign_keys": "Tunnel.local_wan_interface_id"},
    )
    remote_wan_tunnels: List["Tunnel"] = Relationship(
        back_populates="remote_wan_interface",
        sa_relationship_kwargs={"foreign_keys": "Tunnel.remote_wan_interface_id"},
    )


# Forward reference resolution
from .tunnels import Tunnel

Device.model_rebuild()
Interface.model_rebuild()
