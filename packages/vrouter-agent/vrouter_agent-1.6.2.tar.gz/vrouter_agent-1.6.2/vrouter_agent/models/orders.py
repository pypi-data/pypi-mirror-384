"""
Order models for FastAPI SQLModel.
"""

from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field, Relationship, Text, Session, select
from enum import Enum
from .base import UUIDBaseModel


class ConnectionType(str, Enum):
    INTERCONNECT = "interconnect"
    INTRACONNECT = "intraconnect"


class NetworkType(str, Enum):
    FABRICLINK = "fabriclink"
    EDGELINK = "edgelink"


class OrderType(str, Enum):
    PROVISION = "provision"
    DECOMMISSION = "decommission"
    MODIFY = "modify"


class OrderStatus(str, Enum):
    REQUESTED = "requested"
    PENDING = "pending"
    PROVISION_PENDING = "provision_pending"
    PROVISION_COMPLETE = "provision_complete"
    DECOMMISSION_PENDING = "decommission_pending"
    DECOMMISSION_COMPLETE = "decommission_complete"
    FAILED = "failed"
    INCOMPLETE = "incomplete"
    UPDATE_ORDER_FAILED = "update_order_failed"


class Order(UUIDBaseModel, table=True):
    """Order model equivalent to Django Order model"""

    __tablename__ = "orders"

    # Organization relationships (simplified - assuming you have organization models)
    organization_id: Optional[int] = Field(default=None)

    # Order details
    connection_type: ConnectionType = Field(
        default=ConnectionType.INTERCONNECT,
        description="Connection type (e.g. interconnect, intraconnect, etc.)",
    )
    network_type: NetworkType = Field(
        default=NetworkType.FABRICLINK,
        description="Network type (e.g. fabriclink, edgelink, etc.)",
    )
    order_number: Optional[str] = Field(max_length=256, unique=True)
    order_type: OrderType = Field(default=OrderType.PROVISION)
    status: OrderStatus = Field(default=OrderStatus.REQUESTED)

    # Topology relationship
    topology_id: Optional[int] = Field(foreign_key="topologies.id")
    topology: Optional["Topology"] = Relationship(back_populates="orders")

    # User relationships (simplified - assuming you have user models)
    created_by_id: Optional[int] = Field(default=None)
    updated_by_id: Optional[int] = Field(default=None)

    # Status and metadata
    archived: bool = Field(default=False, description="Archive order")
    order_status_message: Optional[str]

    # FRR Configuration
    frr_enabled: bool = Field(
        default=False, description="Enable FRR routing configuration for this order"
    )
    frr_configuration: Optional[str] = Field(
        default=None,
        description="FRR configuration settings for nodes in this order (JSON string)",
    )

    @classmethod
    def get_or_create(cls, session: Session, order_data: Dict[str, Any]) -> "Order":
        """
        Retrieve an existing order by its ID or create a new one if it doesn't exist.

        Args:
            session (Session): The database session to use for the query.
            order_data (dict): The data to create a new order if it doesn't exist.

        Returns:
            Order: The existing or newly created order object.
        """
        order_id = order_data.get("id")

        # Try to find existing order by ID
        if order_id:
            statement = select(cls).where(cls.id == order_id)
            result = session.exec(statement).first()
            if result:
                return result

        # Try to find by order_number if provided
        order_number = order_data.get("order_number")
        if order_number:
            statement = select(cls).where(cls.order_number == order_number)
            result = session.exec(statement).first()
            if result:
                return result

        # Create new order if not found
        order = cls(**order_data)
        session.add(order)
        session.commit()
        session.refresh(order)
        return order

    @classmethod
    def get_order_by_id(cls, session: Session, order_id: int) -> Optional["Order"]:
        """
        Retrieve an order by its ID.

        Args:
            session (Session): The database session to use for the query.
            order_id (int): The ID of the order to retrieve.

        Returns:
            Order: The order object if found, None otherwise.
        """
        statement = select(cls).where(cls.id == order_id)
        return session.exec(statement).first()


# Import here to avoid circular imports
from .tunnels import Topology

# Rebuild model to resolve forward references
Order.model_rebuild()
