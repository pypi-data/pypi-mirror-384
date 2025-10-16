"""
API request/response schemas for tunnels and topologies.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from vrouter_agent.models.tunnels import TopologyType, TunnelType, TunnelState


class NetworkBase(BaseModel):
    """Base network schema"""

    name: str = Field(max_length=100, description="Network name")
    cidr: str = Field(max_length=18, description="Network CIDR (e.g., 192.168.1.0/24)")
    description: Optional[str] = Field(None, description="Network description")


class NetworkCreate(NetworkBase):
    """Schema for creating a network"""

    pass


class NetworkResponse(NetworkBase):
    """Schema for network response"""

    id: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class TopologyBase(BaseModel):
    """Base topology schema"""

    name: str = Field(max_length=100, description="Topology name")
    topology_type: TopologyType = Field(description="Type of topology")
    description: Optional[str] = Field(None, description="Topology description")
    hub_node_id: Optional[int] = Field(
        None, description="Hub node ID for hub-spoke topology"
    )
    is_active: bool = Field(True, description="Is topology active")


class TopologyCreate(TopologyBase):
    """Schema for creating a topology"""

    node_ids: List[int] = Field(description="List of device IDs to include in topology")
    tunnel_network_base: Optional[str] = Field(
        None, description="Base network CIDR for tunnel subnets (e.g., '10.10.0.0/16')"
    )


class TopologyUpdate(BaseModel):
    """Schema for updating a topology"""

    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class TopologyResponse(TopologyBase):
    """Schema for topology response"""

    id: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class TunnelBase(BaseModel):
    """Base tunnel schema"""

    name: Optional[str] = Field(None, max_length=100, description="Tunnel name")
    tunnel_type: TunnelType = Field(description="Type of tunnel")
    local_tunnel_ip: Optional[str] = Field(None, description="Local tunnel IP address")
    remote_tunnel_ip: Optional[str] = Field(
        None, description="Remote tunnel IP address"
    )
    listen_port: Optional[int] = Field(None, ge=1, le=65535, description="Listen port")
    mtu: int = Field(1420, description="Maximum transmission unit")
    keepalive_interval: int = Field(25, description="Keepalive interval in seconds")
    state: TunnelState = Field(TunnelState.PLANNED, description="Tunnel state")
    is_enabled: bool = Field(True, description="Is tunnel enabled")


class TunnelCreate(TunnelBase):
    """Schema for creating a tunnel"""

    topology_id: Optional[int] = Field(None, description="Topology ID")
    local_node_id: Optional[int] = Field(None, description="Local node ID")
    remote_node_id: Optional[int] = Field(None, description="Remote node ID")
    local_interface_id: Optional[int] = Field(None, description="Local interface ID")
    remote_interface_id: Optional[int] = Field(None, description="Remote interface ID")
    local_wan_interface_id: Optional[int] = Field(
        None, description="Local WAN interface ID"
    )
    remote_wan_interface_id: Optional[int] = Field(
        None, description="Remote WAN interface ID"
    )
    tunnel_network_id: Optional[int] = Field(None, description="Tunnel network ID")


class TunnelUpdate(BaseModel):
    """Schema for updating a tunnel"""

    name: Optional[str] = Field(None, max_length=100)
    local_tunnel_ip: Optional[str] = None
    remote_tunnel_ip: Optional[str] = None
    listen_port: Optional[int] = Field(None, ge=1, le=65535)
    mtu: Optional[int] = None
    keepalive_interval: Optional[int] = None
    state: Optional[TunnelState] = None
    is_enabled: Optional[bool] = None
    local_public_key: Optional[str] = None
    remote_public_key: Optional[str] = None


class TunnelResponse(TunnelBase):
    """Schema for tunnel response"""

    id: int
    topology_id: Optional[int]
    local_node_id: Optional[int]
    remote_node_id: Optional[int]
    tunnel_network_id: Optional[int]
    local_public_key: Optional[str]
    remote_public_key: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class TopologyWithTunnels(TopologyResponse):
    """Schema for topology response with tunnels"""

    tunnels: List[TunnelResponse] = []


class TunnelWithDetails(TunnelResponse):
    """Schema for tunnel response with detailed information"""

    topology: Optional[TopologyResponse] = None
    local_node: Optional[Dict[str, Any]] = None
    remote_node: Optional[Dict[str, Any]] = None
    tunnel_network: Optional[NetworkResponse] = None
