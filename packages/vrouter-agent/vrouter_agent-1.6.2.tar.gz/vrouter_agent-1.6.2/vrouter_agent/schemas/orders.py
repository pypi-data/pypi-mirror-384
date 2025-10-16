"""
API request/response schemas for orders.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from vrouter_agent.models.orders import ConnectionType, NetworkType, OrderType, OrderStatus


class OrderBase(BaseModel):
    """Base order schema"""

    connection_type: ConnectionType = Field(
        ConnectionType.INTERCONNECT,
        description="Connection type (e.g. interconnect, intraconnect, etc.)",
    )
    network_type: NetworkType = Field(
        NetworkType.FABRICLINK,
        description="Network type (e.g. fabriclink, edgelink, etc.)",
    )
    order_number: Optional[str] = Field(
        None, max_length=256, description="Order number"
    )
    order_type: OrderType = Field(OrderType.PROVISION, description="Type of order")
    status: OrderStatus = Field(OrderStatus.REQUESTED, description="Order status")
    archived: bool = Field(False, description="Is order archived")
    order_status_message: Optional[str] = Field(None, description="Status message")
    frr_enabled: bool = Field(
        False, description="Enable FRR routing configuration for this order"
    )
    frr_configuration: Dict[str, Any] = Field(
        default_factory=dict,
        description="FRR configuration settings for nodes in this order",
    )


class OrderCreate(OrderBase):
    """Schema for creating an order"""

    topology_id: Optional[int] = Field(None, description="Topology ID")
    # Fields for creating topology with order
    topology_name: Optional[str] = Field(None, description="Name for new topology")
    topology_type: Optional[str] = Field(None, description="Type of topology to create")
    topology_description: Optional[str] = Field(
        None, description="Topology description"
    )
    nodes: Optional[List[int]] = Field(
        None, description="List of device IDs for topology"
    )
    hub_node_id: Optional[int] = Field(
        None, description="Hub node ID for hub-spoke topology"
    )
    tunnel_network_base: Optional[str] = Field(
        None, description="Base network CIDR for tunnel subnets"
    )


class OrderUpdate(BaseModel):
    """Schema for updating an order"""

    connection_type: Optional[ConnectionType] = None
    network_type: Optional[NetworkType] = None
    order_type: Optional[OrderType] = None
    status: Optional[OrderStatus] = None
    archived: Optional[bool] = None
    order_status_message: Optional[str] = None
    frr_enabled: Optional[bool] = None
    frr_configuration: Optional[Dict[str, Any]] = None


class OrderResponse(OrderBase):
    """Schema for order response"""

    id: int
    uuid: str
    topology_id: Optional[int]
    organization_id: Optional[int]
    created_by_id: Optional[int]
    updated_by_id: Optional[int]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class OrderWithTopology(OrderResponse):
    """Schema for order response with topology details"""

    topology: Optional[Dict[str, Any]] = None


class OrderListResponse(BaseModel):
    """Schema for paginated order list response"""

    items: List[OrderResponse]
    total: int
    page: int
    size: int
    pages: int


# Schemas for order processing and blockchain integration
class OrderProcessingRequest(BaseModel):
    """Schema for order processing request"""

    order_id: int
    action: str = Field(pattern="^(provision|decommission)$")


class OrderProcessingResponse(BaseModel):
    """Schema for order processing response"""

    success: bool
    message: str
    order_id: int
    results: Optional[List[Dict[str, Any]]] = None
    errors: Optional[List[str]] = None
