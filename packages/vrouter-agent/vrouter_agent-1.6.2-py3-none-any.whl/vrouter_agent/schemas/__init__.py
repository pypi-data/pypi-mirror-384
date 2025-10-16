"""
Main schemas module - imports all schemas for easy access.
"""

from vrouter_agent.schemas.devices import (
    DeviceBase,
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
    DeviceWithInterfaces,
    InterfaceBase,
    InterfaceCreate,
    InterfaceUpdate,
    InterfaceResponse,
)

from vrouter_agent.schemas.tunnels import (
    NetworkBase,
    NetworkCreate,
    NetworkResponse,
    TopologyBase,
    TopologyCreate,
    TopologyUpdate,
    TopologyResponse,
    TopologyWithTunnels,
    TunnelBase,
    TunnelCreate,
    TunnelUpdate,
    TunnelResponse,
    TunnelWithDetails,
)

from vrouter_agent.schemas.orders import (
    OrderBase,
    OrderCreate,
    OrderUpdate,
    OrderResponse,
    OrderWithTopology,
    OrderListResponse,
    OrderProcessingRequest,
    OrderProcessingResponse,
)

from vrouter_agent.schemas.tunnel_config import (
    TopologyInfo,
    WireGuardConfig,
    TunnelConfigData,
    NodeTunnelConfig,
    BlockchainPostData,
    TunnelConfigRequest,
    TunnelConfigResponse,
    BlockchainPostRequest,
    BlockchainPostResponse,
)

__all__ = [
    # Device schemas
    "DeviceBase",
    "DeviceCreate",
    "DeviceUpdate",
    "DeviceResponse",
    "DeviceWithInterfaces",
    "InterfaceBase",
    "InterfaceCreate",
    "InterfaceUpdate",
    "InterfaceResponse",
    # Tunnel schemas
    "NetworkBase",
    "NetworkCreate",
    "NetworkResponse",
    "TopologyBase",
    "TopologyCreate",
    "TopologyUpdate",
    "TopologyResponse",
    "TopologyWithTunnels",
    "TunnelBase",
    "TunnelCreate",
    "TunnelUpdate",
    "TunnelResponse",
    "TunnelWithDetails",
    # Order schemas
    "OrderBase",
    "OrderCreate",
    "OrderUpdate",
    "OrderResponse",
    "OrderWithTopology",
    "OrderListResponse",
    "OrderProcessingRequest",
    "OrderProcessingResponse",
    # Tunnel config schemas
    "TopologyInfo",
    "WireGuardConfig",
    "TunnelConfigData",
    "NodeTunnelConfig",
    "BlockchainPostData",
    "TunnelConfigRequest",
    "TunnelConfigResponse",
    "BlockchainPostRequest",
    "BlockchainPostResponse",
]
