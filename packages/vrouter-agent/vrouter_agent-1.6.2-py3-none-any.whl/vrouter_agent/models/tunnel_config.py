"""
SQLModel for storing tunnel configuration data received from streams.
This stores the complete tunnel configuration with nested tunnel data.
"""

from sqlmodel import SQLModel, Field, Column, JSON, Relationship, text
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import json

from .base import BaseModel, TimestampMixin


class TunnelState(str, Enum):
    """Enumeration for individual tunnel operational states."""
    PLANNED = "planned"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"


class ConfigDataState(str, Enum):
    """Enumeration for tunnel configuration data application states."""
    APPLIED = "applied"
    ERROR = "error"
    ROLLBACK = "rollback"
    PENDING = "pending"


class TunnelConfigData(BaseModel, TimestampMixin, table=True):
    """
    Stores tunnel configuration data received from streams.
    Contains the complete nested configuration structure.
    """

    __tablename__ = "tunnel_config_data"

    # Basic identification
    order_id: str = Field(index=True, description="Order ID this config belongs to")
    order_number: Optional[str] = Field(None, description="Human-readable order number")
    node_hostname: str = Field(
        index=True, description="Hostname of the node this config is for"
    )

    # Configuration metadata
    tag: str = Field(default="tunnel_config", description="Configuration tag")
    action: str = Field(description="Action (provision, decommission, etc.)")
    state: ConfigDataState = Field(
        default=ConfigDataState.PENDING,
        description="Configuration application state (applied, error, rollback, pending)",
    )

    # Topology information
    topology_id: Optional[int] = Field(None, description="Topology ID")
    topology_data: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Topology information (idc name, type)",
    )

    # Tunnel configurations (stored as JSON array)
    # Each tunnel object now contains embedded VPP interface data
    tunnels_data: List[Dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="Array of tunnel configuration objects with embedded VPP interface data",
    )

    # Additional configuration data
    frr_config: Optional[Dict[str, Any]] = Field(
        None, sa_column=Column(JSON), description="FRR configuration with zebra, ospf, bgp, and static configs"
    )
    
    # NAT configuration
    nat_config: Optional[Dict[str, Any]] = Field(
        None, sa_column=Column(JSON), description="NAT44 configuration including pool addresses and static mappings"
    )
    
    # ACL configuration
    acl_config: Optional[Dict[str, Any]] = Field(
        None, sa_column=Column(JSON), description="ACL (Access Control List) configuration including rules"
    )

    # Client interfaces configuration
    client_interfaces: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list,
        sa_column=Column(JSON), 
        description="List of client interface configurations"
    )
    
    # bgp peers if ebgp is used
    bgp_peers: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="List of BGP peer configurations if eBGP is used",
    )
    
    # Protocol enablement flags
    ospf_enabled: Optional[bool] = Field(
        default=False,
        description="Whether OSPF protocol is enabled for this configuration"
    )
    
    ebgp_enabled: Optional[bool] = Field(
        default=False,
        description="Whether eBGP protocol is enabled for this configuration"
    )

    # Raw data storage for debugging/auditing
    raw_config_data: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Complete raw configuration data as received",
    )

    # Processing metadata
    source: Optional[str] = Field(
        None, description="Source of the configuration (stream, api, etc.)"
    )
    processed_at: Optional[datetime] = Field(
        None, description="When this config was processed"
    )
    applied_at: Optional[datetime] = Field(
        None, description="When this config was applied to the node"
    )
    error_message: Optional[str] = Field(
        None, description="Error message if processing failed"
    )

    # Version/revision tracking
    config_version: int = Field(
        default=1, description="Version number of this configuration"
    )
    superseded_by_id: Optional[int] = Field(
        None,
        foreign_key="tunnel_config_data.id",
        description="ID of newer config that supersedes this one",
    )

    # Relationships
    superseded_by: Optional["TunnelConfigData"] = Relationship(
        back_populates="supersedes",
        sa_relationship_kwargs={"remote_side": "TunnelConfigData.id"},
    )
    supersedes: List["TunnelConfigData"] = Relationship(back_populates="superseded_by")


class TunnelConfigHistory(BaseModel, TimestampMixin, table=True):
    """
    Audit trail for tunnel configuration changes.
    Tracks all modifications to tunnel configurations.
    """

    __tablename__ = "tunnel_config_history"

    config_id: int = Field(
        foreign_key="tunnel_config_data.id", description="Reference to the main config"
    )
    change_type: str = Field(
        description="Type of change (created, updated, applied, failed)"
    )
    old_state: Optional[TunnelState] = Field(None, description="Previous tunnel state")
    new_state: TunnelState = Field(description="New tunnel state")
    old_config_data_state: Optional[ConfigDataState] = Field(None, description="Previous config data state")
    new_config_data_state: ConfigDataState = Field(description="New config data state")
    change_description: Optional[str] = Field(
        None, description="Description of what changed"
    )
    changed_by: Optional[str] = Field(None, description="Who/what made the change")

    # Store the configuration state at time of change
    config_snapshot: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Snapshot of config at time of change",
    )

    # Relationship
    config: TunnelConfigData = Relationship()
