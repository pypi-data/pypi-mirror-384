"""
API request/response schemas for devices.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from vrouter_agent.models.devices import NodeType, DeviceStatus, InterfaceType


class DeviceBase(BaseModel):
    """Base device schema"""

    name: Optional[str] = Field(None, max_length=256, description="Friendly identifier")
    node_type: NodeType = Field(NodeType.PEER)
    management_ip: Optional[str] = Field(None, description="Management IP address")
    router_id: Optional[str] = Field(None, description="BGP/OSPF Router ID")
    asn: Optional[int] = Field(None, description="BGP AS Number", ge=1, le=4294967295)
    hostname: str = Field(max_length=256, description="Device hostname")
    fqdn: Optional[str] = Field(
        None, max_length=256, description="Fully qualified domain name"
    )
    manufacturer: Optional[str] = Field(None, max_length=256)
    model: Optional[str] = Field(None, max_length=256)
    firmware: Optional[str] = Field(None, max_length=256)
    is_active: bool = Field(True)
    status: DeviceStatus = Field(DeviceStatus.OPERATIONAL)
    status_text: str = Field("All systems operational", max_length=500)


class DeviceCreate(DeviceBase):
    """Schema for creating a device"""

    pass


class DeviceUpdate(BaseModel):
    """Schema for updating a device"""

    name: Optional[str] = Field(None, max_length=256)
    node_type: Optional[NodeType] = None
    management_ip: Optional[str] = None
    router_id: Optional[str] = None
    asn: Optional[int] = Field(None, ge=1, le=4294967295)
    manufacturer: Optional[str] = Field(None, max_length=256)
    model: Optional[str] = Field(None, max_length=256)
    firmware: Optional[str] = Field(None, max_length=256)
    is_active: Optional[bool] = None
    status: Optional[DeviceStatus] = None
    status_text: Optional[str] = Field(None, max_length=500)


class DeviceResponse(DeviceBase):
    """Schema for device response"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InterfaceBase(BaseModel):
    """Base interface schema"""

    name: str = Field(max_length=256, description="Interface name")
    type: InterfaceType = Field(InterfaceType.PHYSICAL)
    is_management: bool = Field(False)
    is_wan: bool = Field(False)
    is_lan: bool = Field(False)
    is_primary: bool = Field(False)
    up: bool = Field(False)
    ip_address: Optional[str] = Field(None, description="IP address")
    subnet_mask: Optional[int] = Field(None, ge=1, le=32)
    vlan_id: Optional[int] = Field(None, ge=1, le=4094)
    mtu: int = Field(1500)
    is_enabled: bool = Field(True)
    description: Optional[str] = None


class InterfaceCreate(InterfaceBase):
    """Schema for creating an interface"""

    device_id: int = Field(description="Device ID this interface belongs to")


class InterfaceUpdate(BaseModel):
    """Schema for updating an interface"""

    name: Optional[str] = Field(None, max_length=256)
    type: Optional[InterfaceType] = None
    is_management: Optional[bool] = None
    is_wan: Optional[bool] = None
    is_lan: Optional[bool] = None
    is_primary: Optional[bool] = None
    up: Optional[bool] = None
    ip_address: Optional[str] = None
    subnet_mask: Optional[int] = Field(None, ge=1, le=32)
    vlan_id: Optional[int] = Field(None, ge=1, le=4094)
    mtu: Optional[int] = None
    is_enabled: Optional[bool] = None
    description: Optional[str] = None


class InterfaceResponse(InterfaceBase):
    """Schema for interface response"""

    id: int
    device_id: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class DeviceWithInterfaces(DeviceResponse):
    """Schema for device response with interfaces"""

    interfaces: List[InterfaceResponse] = []
