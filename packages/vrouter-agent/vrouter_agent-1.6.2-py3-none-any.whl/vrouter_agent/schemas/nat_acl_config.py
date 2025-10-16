"""
NAT and ACL Configuration Schemas (VPP-compatible)

This module provides Pydantic schemas for NAT44 and ACL configurations
that are compatible with VPP vpp_vrouter models. It includes conversion
utilities for dictionary-to-object transformations with proper typing.
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum, IntEnum
import ipaddress


# ============================================================================
# NAT44 Configuration Models (VPP-compatible)
# ============================================================================

class ProtocolInNAT(IntEnum):
    """Available protocols that can be used in NAT configuration.
    Numbers from: http://www.iana.org/assignments/protocol-numbers
    """
    TCP = 6
    UDP = 17
    ICMP = 1


class LocalIP(BaseModel):
    """LocalIP defines a local IP address for NAT static mapping."""
    
    local_ip: str = Field(description="Local IP address")
    local_port: int = Field(0, description="Port (0 for address mapping)")
    probability: int = Field(0, description="Probability level for load-balancing mode")
    
    class Config:
        use_enum_values = True
    
    @validator('local_ip')
    def validate_local_ip(cls, v):
        """Validate IP address format"""
        if v:
            try:
                ipaddress.IPv4Address(v)
            except ValueError:
                raise ValueError(f"Invalid IPv4 address: {v}")
        return v
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LocalIP":
        """Create LocalIP from dictionary with type conversion."""
        return cls(
            local_ip=str(data.get("local_ip", "0.0.0.0")),
            local_port=int(data.get("local_port", 0)),
            probability=int(data.get("probability", 0))
        )


class StaticMapping(BaseModel):
    """StaticMapping defines a static mapping in DNAT.
    
    Supports both VPP format (with local_ips list) and decrypted data format 
    (with local_ip and local_port fields).
    """
    
    external_interface: str = Field("", description="Interface to use external IP from; preferred over external_ip")
    external_ip: str = Field("", description="External IPv4 address")
    external_port: int = Field(0, description="Port (0 for address mapping)")
    local_ips: List[LocalIP] = Field(default_factory=list, description="List of local IP addresses (multiple = load-balancing)")
    protocol: ProtocolInNAT = Field(ProtocolInNAT.TCP, description="Protocol used for static mapping")
    
    # Fields from decrypted data format
    local_ip: Optional[str] = Field(None, description="Local IP address (simplified format)")
    local_port: Optional[int] = Field(None, description="Local port (simplified format)")
    tag: str = Field("", description="Tag for the mapping")
    name: str = Field("", description="Name of the mapping")
    type: str = Field("nat44_dynamic", description="Type of NAT mapping")
    vrf_id: int = Field(0, description="VRF ID")
    enabled: bool = Field(True, description="Whether mapping is enabled")
    twice_nat: bool = Field(False, description="Enable twice NAT")
    out2in_only: bool = Field(False, description="Out2in only")
    description: str = Field("", description="Description of the mapping")
    
    class Config:
        use_enum_values = True
    
    @root_validator(pre=True)
    def convert_local_ip_to_local_ips(cls, values):
        """Convert local_ip/local_port to local_ips list if needed"""
        # If we have local_ip but no local_ips, convert it
        if 'local_ip' in values and values.get('local_ip') and not values.get('local_ips'):
            local_ip_obj = {
                "local_ip": values['local_ip'],
                "local_port": values.get('local_port', 0),
                "probability": 0
            }
            values['local_ips'] = [local_ip_obj]
        return values
    
    @validator('external_ip')
    def validate_external_ip(cls, v):
        """Validate IP address format"""
        if v and v != "0.0.0.0" and v != "":
            try:
                ipaddress.IPv4Address(v)
            except ValueError:
                raise ValueError(f"Invalid IPv4 address: {v}")
        return v
    
    @validator('protocol', pre=True)
    def convert_protocol(cls, v):
        """Convert string protocol to enum"""
        if isinstance(v, str):
            protocol_map = {
                'tcp': ProtocolInNAT.TCP,
                'udp': ProtocolInNAT.UDP,
                'icmp': ProtocolInNAT.ICMP
            }
            return protocol_map.get(v.lower(), ProtocolInNAT.TCP)
        elif isinstance(v, int):
            return ProtocolInNAT(v)
        return v
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StaticMapping":
        """Create StaticMapping from dictionary with type conversion."""
        # Handle local_ips if provided
        local_ips_data = data.get("local_ips", [])
        local_ips = [LocalIP.from_dict(lip) if isinstance(lip, dict) else lip 
                     for lip in local_ips_data]
        
        # If no local_ips but we have local_ip, let the root_validator handle it
        return cls(
            external_interface=str(data.get("external_interface", "")),
            external_ip=str(data.get("external_ip", "")),
            external_port=int(data.get("external_port", 0)),
            local_ips=local_ips,
            local_ip=data.get("local_ip"),
            local_port=data.get("local_port"),
            protocol=data.get("protocol", ProtocolInNAT.TCP),
            tag=str(data.get("tag", "")),
            name=str(data.get("name", "")),
            type=str(data.get("type", "nat44_dynamic")),
            vrf_id=int(data.get("vrf_id", 0)),
            enabled=bool(data.get("enabled", True)),
            twice_nat=bool(data.get("twice_nat", False)),
            out2in_only=bool(data.get("out2in_only", False)),
            description=str(data.get("description", ""))
        )


class IdentityMapping(BaseModel):
    """IdentityMapping defines an identity mapping in DNAT."""
    
    interface: str = Field("", description="Name of the interface to use address from; preferred over ip_address")
    ip_address: str = Field("0.0.0.0", description="IPv4 address")
    port: int = Field(0, description="Port (0 for address mapping)")
    protocol: ProtocolInNAT = Field(ProtocolInNAT.TCP, description="Protocol used for identity mapping")
    
    class Config:
        use_enum_values = True
    
    @validator('ip_address')
    def validate_ip_address(cls, v):
        """Validate IP address format"""
        if v and v != "0.0.0.0" and v != "":
            try:
                ipaddress.IPv4Address(v)
            except ValueError:
                raise ValueError(f"Invalid IPv4 address: {v}")
        return v
    
    @validator('protocol', pre=True)
    def convert_protocol(cls, v):
        """Convert string protocol to enum"""
        if isinstance(v, str):
            protocol_map = {
                'tcp': ProtocolInNAT.TCP,
                'udp': ProtocolInNAT.UDP,
                'icmp': ProtocolInNAT.ICMP
            }
            return protocol_map.get(v.lower(), ProtocolInNAT.TCP)
        elif isinstance(v, int):
            return ProtocolInNAT(v)
        return v
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IdentityMapping":
        """Create IdentityMapping from dictionary with type conversion."""
        return cls(
            interface=str(data.get("interface", "")),
            ip_address=str(data.get("ip_address", "0.0.0.0")),
            port=int(data.get("port", 0)),
            protocol=data.get("protocol", ProtocolInNAT.TCP)
        )


class DNat44(BaseModel):
    """DNat44 defines destination NAT44 configuration."""
    
    label: str = Field("", description="Unique identifier for the DNAT configuration")
    static_mappings: List[StaticMapping] = Field(default_factory=list, description="List of static mappings in DNAT")
    identity_mappings: List[IdentityMapping] = Field(default_factory=list, description="List of identity mappings in DNAT")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DNat44":
        """Create DNat44 from dictionary with type conversion."""
        static_mappings_data = data.get("static_mappings", [])
        static_mappings = [StaticMapping.from_dict(sm) if isinstance(sm, dict) else sm 
                          for sm in static_mappings_data]
        
        identity_mappings_data = data.get("identity_mappings", [])
        identity_mappings = [IdentityMapping.from_dict(im) if isinstance(im, dict) else im 
                            for im in identity_mappings_data]
        
        return cls(
            label=str(data.get("label", "")),
            static_mappings=static_mappings,
            identity_mappings=identity_mappings
        )


class Nat44Interface(BaseModel):
    """Nat44Interface defines a local network interface enabled for NAT44."""
    
    name: str = Field(description="Interface name (logical)")
    nat_inside: bool = Field(False, description="Enable/disable NAT on inside")
    nat_outside: bool = Field(False, description="Enable/disable NAT on outside")
    output_feature: bool = Field(False, description="Enable/disable output feature")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Nat44Interface":
        """Create Nat44Interface from dictionary with type conversion."""
        return cls(
            name=str(data.get("name", "")),
            nat_inside=bool(data.get("nat_inside", False)),
            nat_outside=bool(data.get("nat_outside", False)),
            output_feature=bool(data.get("output_feature", False))
        )


class Nat44AddressPool(BaseModel):
    """Nat44AddressPool defines an address pool used for NAT44."""
    
    name: str = Field("", description="Unique name for address pool")
    first_ip: str = Field(description="First IP address of the pool")
    last_ip: str = Field("", description="Last IP address of the pool (higher than first_ip or empty for single IP)")
    
    # Support for decrypted data format
    start_address: Optional[str] = Field(None, description="Alias for first_ip (from decrypted data)")
    end_address: Optional[str] = Field(None, description="Alias for last_ip (from decrypted data)")
    vrf_id: int = Field(0, description="VRF ID for the address pool")
    twice_nat: bool = Field(False, description="Enable twice NAT")
    
    @root_validator(pre=True)
    def convert_address_fields(cls, values):
        """Convert start_address/end_address to first_ip/last_ip"""
        # Handle start_address -> first_ip
        if 'start_address' in values and values['start_address']:
            values['first_ip'] = values['start_address']
        elif 'first_ip' not in values:
            values['first_ip'] = values.get('start_address', '0.0.0.0')
        
        # Handle end_address -> last_ip
        if 'end_address' in values and values['end_address']:
            values['last_ip'] = values['end_address']
        elif 'last_ip' not in values:
            values['last_ip'] = values.get('end_address', '')
        
        return values
    
    @validator('first_ip')
    def validate_first_ip(cls, v):
        """Validate first IP address"""
        if v:
            try:
                ipaddress.IPv4Address(v)
            except ValueError:
                raise ValueError(f"Invalid IPv4 address: {v}")
        return v
    
    @validator('last_ip')
    def validate_last_ip(cls, v, values):
        """Validate last IP address"""
        if v and v != "":
            try:
                ipaddress.IPv4Address(v)
                # Verify last_ip >= first_ip
                if 'first_ip' in values and values['first_ip']:
                    first = ipaddress.IPv4Address(values['first_ip'])
                    last = ipaddress.IPv4Address(v)
                    if last < first:
                        raise ValueError(f"last_ip ({v}) must be >= first_ip ({values['first_ip']})")
            except ValueError as e:
                if "last_ip" not in str(e):
                    raise ValueError(f"Invalid IPv4 address: {v}")
                raise
        return v
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Nat44AddressPool":
        """Create Nat44AddressPool from dictionary with type conversion."""
        return cls(
            name=str(data.get("name", "")),
            first_ip=str(data.get("first_ip", data.get("start_address", "0.0.0.0"))),
            last_ip=str(data.get("last_ip", data.get("end_address", ""))),
            start_address=data.get("start_address"),
            end_address=data.get("end_address"),
            vrf_id=int(data.get("vrf_id", 0)),
            twice_nat=bool(data.get("twice_nat", False))
        )


class NatConfig(BaseModel):
    """NAT44 configuration structure (VPP-compatible).
    
    This combines interface configuration, address pools, and DNAT mappings.
    Supports both VPP format (with dnat nested) and decrypted data format 
    (with static_mappings at top level).
    """
    
    enabled: bool = Field(default=False, description="Whether NAT is enabled")
    endpoint_dependent: bool = Field(True, description="Endpoint-dependent NAT mode")
    connection_tracking: bool = Field(True, description="Enable connection tracking")
    max_translations_per_thread: int = Field(10240, description="Maximum translations per thread")
    max_users_per_thread: int = Field(1000, description="Maximum users per thread")
    
    # VPP-compatible configuration structures
    nat44_interfaces: List[Nat44Interface] = Field(
        default_factory=list, 
        description="NAT44 interface configurations",
        alias="interfaces"
    )
    address_pools: List[Nat44AddressPool] = Field(
        default_factory=list, 
        description="NAT44 address pool configurations (also accepts pool_addresses)"
    )
    
    # Support both formats: nested dnat or top-level static_mappings
    dnat: Optional[DNat44] = Field(
        None, 
        description="Destination NAT44 configuration with static and identity mappings"
    )
    static_mappings: List[StaticMapping] = Field(
        default_factory=list,
        description="Static mappings (top-level, from decrypted data format)"
    )
    identity_mappings: List[IdentityMapping] = Field(
        default_factory=list,
        description="Identity mappings (top-level, from decrypted data format)"
    )
    
    @root_validator(pre=True)
    def normalize_structure(cls, values):
        """Normalize between different input formats"""
        # Handle pool_addresses alias
        if 'pool_addresses' in values and not values.get('address_pools'):
            values['address_pools'] = values['pool_addresses']
        
        # Handle interfaces alias
        if 'interfaces' in values and not values.get('nat44_interfaces'):
            values['nat44_interfaces'] = values['interfaces']
        
        # If we have top-level static_mappings/identity_mappings but no dnat, create dnat
        if (values.get('static_mappings') or values.get('identity_mappings')) and not values.get('dnat'):
            values['dnat'] = {
                'label': 'nat-mappings',
                'static_mappings': values.get('static_mappings', []),
                'identity_mappings': values.get('identity_mappings', [])
            }
        # If we have dnat, also populate top-level fields for easy access
        elif values.get('dnat'):
            if isinstance(values['dnat'], dict):
                if not values.get('static_mappings'):
                    values['static_mappings'] = values['dnat'].get('static_mappings', [])
                if not values.get('identity_mappings'):
                    values['identity_mappings'] = values['dnat'].get('identity_mappings', [])
        
        return values
    
    class Config:
        allow_population_by_field_name = True  # Allow using aliases
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NatConfig":
        """Create NatConfig from dictionary with type conversion.
        
        This handles various input formats including simplified formats.
        """
        if not data:
            return cls(enabled=False)
        
        # Handle nat44_interfaces/interfaces
        interfaces_data = data.get("nat44_interfaces", data.get("interfaces", []))
        interfaces = [Nat44Interface.from_dict(iface) if isinstance(iface, dict) else iface 
                     for iface in interfaces_data]
        
        # Handle address_pools/pool_addresses
        pools_data = data.get("address_pools", data.get("pool_addresses", []))
        address_pools = [Nat44AddressPool.from_dict(pool) if isinstance(pool, dict) else pool 
                        for pool in pools_data]
        
        # Handle static_mappings (either top-level or in dnat)
        static_mappings_data = data.get("static_mappings", [])
        static_mappings = [StaticMapping.from_dict(sm) if isinstance(sm, dict) else sm 
                          for sm in static_mappings_data]
        
        # Handle identity_mappings (either top-level or in dnat)
        identity_mappings_data = data.get("identity_mappings", [])
        identity_mappings = [IdentityMapping.from_dict(im) if isinstance(im, dict) else im 
                           for im in identity_mappings_data]
        
        # Handle DNAT (if provided)
        dnat_data = data.get("dnat")
        dnat = None
        if dnat_data and isinstance(dnat_data, dict):
            dnat = DNat44.from_dict(dnat_data)
        elif static_mappings or identity_mappings:
            # Create DNat44 from top-level mappings
            dnat = DNat44(
                label="nat-mappings",
                static_mappings=static_mappings,
                identity_mappings=identity_mappings
            )
        
        return cls(
            enabled=bool(data.get("enabled", False)),
            endpoint_dependent=bool(data.get("endpoint_dependent", True)),
            connection_tracking=bool(data.get("connection_tracking", True)),
            max_translations_per_thread=int(data.get("max_translations_per_thread", 10240)),
            max_users_per_thread=int(data.get("max_users_per_thread", 1000)),
            nat44_interfaces=interfaces,
            address_pools=address_pools,
            dnat=dnat,
            static_mappings=static_mappings,
            identity_mappings=identity_mappings
        )
    
    def to_vpp_config(self) -> Dict[str, Any]:
        """Convert to VPP-compatible configuration dictionary."""
        return {
            "enabled": self.enabled,
            "endpoint_dependent": self.endpoint_dependent,
            "connection_tracking": self.connection_tracking,
            "max_translations_per_thread": self.max_translations_per_thread,
            "max_users_per_thread": self.max_users_per_thread,
            "nat44_interfaces": [iface.dict() for iface in self.nat44_interfaces],
            "address_pools": [pool.dict() for pool in self.address_pools],
            "dnat": self.dnat.dict() if self.dnat else None
        }


# ============================================================================
# ACL Configuration Models (VPP-compatible)
# ============================================================================

class ACLAction(str, Enum):
    """ACL action enumeration"""
    DENY = "deny"
    PERMIT = "permit"
    REFLECT = "reflect"


class ICMPRange(BaseModel):
    """Range for ICMP codes and types.
    See https://www.iana.org/assignments/icmp-parameters/icmp-parameters.xhtml
    """
    
    first: int = Field(0, ge=0, le=255, description="First value in range")
    last: int = Field(255, ge=0, le=255, description="Last value in range")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ICMPRange":
        """Create ICMPRange from dictionary with type conversion."""
        return cls(
            first=int(data.get("first", 0)),
            last=int(data.get("last", 255))
        )


class ICMPProtocol(BaseModel):
    """ICMP protocol selector for ACL rules."""
    
    icmpv6: bool = Field(False, description="ICMPv6 flag, if false ICMPv4 will be used")
    icmp_code_range: ICMPRange = Field(
        default_factory=ICMPRange, 
        description="Inclusive range representing icmp codes to be used"
    )
    icmp_type_range: ICMPRange = Field(
        default_factory=ICMPRange, 
        description="Inclusive range representing icmp types to be used"
    )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ICMPProtocol":
        """Create ICMPProtocol from dictionary with type conversion."""
        code_range_data = data.get("icmp_code_range", {})
        code_range = ICMPRange.from_dict(code_range_data) if isinstance(code_range_data, dict) else ICMPRange()
        
        type_range_data = data.get("icmp_type_range", {})
        type_range = ICMPRange.from_dict(type_range_data) if isinstance(type_range_data, dict) else ICMPRange()
        
        return cls(
            icmpv6=bool(data.get("icmpv6", False)),
            icmp_code_range=code_range,
            icmp_type_range=type_range
        )


class PortRange(BaseModel):
    """Inclusive range representing ports to be used.
    When only lower_port is present, it represents a single port.
    """
    
    lower_port: int = Field(0, ge=0, le=65535, description="Lower port bound")
    upper_port: int = Field(65535, ge=0, le=65535, description="Upper port bound")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PortRange":
        """Create PortRange from dictionary with type conversion."""
        return cls(
            lower_port=int(data.get("lower_port", 0)),
            upper_port=int(data.get("upper_port", 65535))
        )


class TCPProtocol(BaseModel):
    """TCP protocol selector for ACL rules."""
    
    destination_port_range: PortRange = Field(
        default_factory=PortRange, 
        description="Destination port range"
    )
    source_port_range: PortRange = Field(
        default_factory=PortRange, 
        description="Source port range"
    )
    tcp_flags_mask: int = Field(
        0, ge=0, le=255,
        description="Binary mask for tcp flags to match. MSB order (FIN at position 0)"
    )
    tcp_flags_value: int = Field(
        0, ge=0, le=255,
        description="Binary value for tcp flags to match. MSB order (FIN at position 0)"
    )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TCPProtocol":
        """Create TCPProtocol from dictionary with type conversion."""
        dest_range_data = data.get("destination_port_range", {})
        dest_range = PortRange.from_dict(dest_range_data) if isinstance(dest_range_data, dict) else PortRange()
        
        src_range_data = data.get("source_port_range", {})
        src_range = PortRange.from_dict(src_range_data) if isinstance(src_range_data, dict) else PortRange()
        
        return cls(
            destination_port_range=dest_range,
            source_port_range=src_range,
            tcp_flags_mask=int(data.get("tcp_flags_mask", 0)),
            tcp_flags_value=int(data.get("tcp_flags_value", 0))
        )


class UDPProtocol(BaseModel):
    """UDP protocol selector for ACL rules."""
    
    destination_port_range: PortRange = Field(
        default_factory=PortRange, 
        description="Destination port range"
    )
    source_port_range: PortRange = Field(
        default_factory=PortRange, 
        description="Source port range"
    )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UDPProtocol":
        """Create UDPProtocol from dictionary with type conversion."""
        dest_range_data = data.get("destination_port_range", {})
        dest_range = PortRange.from_dict(dest_range_data) if isinstance(dest_range_data, dict) else PortRange()
        
        src_range_data = data.get("source_port_range", {})
        src_range = PortRange.from_dict(src_range_data) if isinstance(src_range_data, dict) else PortRange()
        
        return cls(
            destination_port_range=dest_range,
            source_port_range=src_range
        )


class OtherProtocol(BaseModel):
    """ACL rule's packet selector based on IP protocol.
    For ICMP, TCP, UDP use custom protocol selectors.
    """
    
    protocol: int = Field(
        0, 
        description="IP protocol number (http://www.iana.org/assignments/protocol-numbers/protocol-numbers.xhtml)"
    )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OtherProtocol":
        """Create OtherProtocol from dictionary with type conversion."""
        return cls(protocol=int(data.get("protocol", 0)))


class IPAddresses(BaseModel):
    """IP address specifications for ACL rules."""
    
    destination_network: str = Field(
        "0.0.0.0/0", 
        description="Destination IPv4 network address (<ip>/<prefix>)"
    )
    source_network: str = Field(
        "0.0.0.0/0", 
        description="Source IPv4 network address (<ip>/<prefix>)"
    )
    
    @validator('destination_network', 'source_network')
    def validate_network(cls, v):
        """Validate network address format"""
        if v:
            try:
                ipaddress.IPv4Network(v)
            except ValueError:
                raise ValueError(f"Invalid IPv4 network: {v}")
        return v
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IPAddresses":
        """Create IPAddresses from dictionary with type conversion."""
        return cls(
            destination_network=str(data.get("destination_network", "0.0.0.0/0")),
            source_network=str(data.get("source_network", "0.0.0.0/0"))
        )


class IPSpecification(BaseModel):
    """IP specification combining addresses and protocol selectors."""
    
    addresses: Optional[IPAddresses] = Field(None, description="IP address specifications")
    protocol: Optional[Union[ICMPProtocol, TCPProtocol, UDPProtocol, OtherProtocol]] = Field(
        None, 
        description="Protocol-specific selector (ICMP, TCP, UDP, or Other)"
    )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IPSpecification":
        """Create IPSpecification from dictionary with type conversion."""
        addresses_data = data.get("addresses")
        addresses = IPAddresses.from_dict(addresses_data) if addresses_data and isinstance(addresses_data, dict) else None
        
        protocol_data = data.get("protocol")
        protocol = None
        if protocol_data and isinstance(protocol_data, dict):
            # Determine protocol type based on fields
            if "icmp_code_range" in protocol_data or "icmp_type_range" in protocol_data:
                protocol = ICMPProtocol.from_dict(protocol_data)
            elif "tcp_flags_mask" in protocol_data or "tcp_flags_value" in protocol_data:
                protocol = TCPProtocol.from_dict(protocol_data)
            elif "destination_port_range" in protocol_data and "source_port_range" in protocol_data:
                # Could be TCP or UDP, check if tcp flags present
                if "tcp_flags_mask" in protocol_data or "tcp_flags_value" in protocol_data:
                    protocol = TCPProtocol.from_dict(protocol_data)
                else:
                    protocol = UDPProtocol.from_dict(protocol_data)
            else:
                protocol = OtherProtocol.from_dict(protocol_data)
        
        return cls(
            addresses=addresses,
            protocol=protocol
        )


class ACLRule(BaseModel):
    """ACL rule configuration item (IP-based rule)."""
    
    action: ACLAction = Field(ACLAction.DENY, description="Action to take")
    refinement: Optional[IPSpecification] = Field(None, description="IP and protocol specifications")
    
    @validator('action', pre=True)
    def convert_action(cls, v):
        """Convert string action to enum"""
        if isinstance(v, str):
            return ACLAction(v.lower())
        return v
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ACLRule":
        """Create ACLRule from dictionary with type conversion."""
        refinement_data = data.get("refinement")
        refinement = IPSpecification.from_dict(refinement_data) if refinement_data and isinstance(refinement_data, dict) else None
        
        return cls(
            action=data.get("action", ACLAction.DENY),
            refinement=refinement
        )


class AclConfig(BaseModel):
    """ACL (Access Control List) configuration structure (VPP-compatible)."""
    
    enabled: bool = Field(default=False, description="Whether ACL is enabled")
    name: str = Field("", description="ACL name/identifier")
    rules: List[ACLRule] = Field(default_factory=list, description="List of ACL rules")
    egress_interfaces: List[str] = Field(
        default_factory=list, 
        description="Names of egress interfaces to apply ACL"
    )
    ingress_interfaces: List[str] = Field(
        default_factory=list, 
        description="Names of ingress interfaces to apply ACL"
    )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AclConfig":
        """Create AclConfig from dictionary with type conversion."""
        if not data:
            return cls(enabled=False)
        
        rules_data = data.get("rules", [])
        rules = [ACLRule.from_dict(rule) if isinstance(rule, dict) else rule 
                for rule in rules_data]
        
        return cls(
            enabled=bool(data.get("enabled", False)),
            name=str(data.get("name", "")),
            rules=rules,
            egress_interfaces=list(data.get("egress_interfaces", [])),
            ingress_interfaces=list(data.get("ingress_interfaces", []))
        )
    
    def to_vpp_config(self) -> Dict[str, Any]:
        """Convert to VPP-compatible configuration dictionary."""
        return {
            "enabled": self.enabled,
            "name": self.name,
            "rules": [rule.dict() for rule in self.rules],
            "egress_interfaces": self.egress_interfaces,
            "ingress_interfaces": self.ingress_interfaces
        }


# ============================================================================
# Conversion Utilities
# ============================================================================

def convert_nat_config(data: Union[Dict[str, Any], NatConfig, None]) -> Optional[NatConfig]:
    """Convert various NAT config formats to NatConfig object.
    
    Args:
        data: Dictionary, NatConfig object, or None
        
    Returns:
        NatConfig object or None
    """
    if data is None:
        return None
    if isinstance(data, NatConfig):
        return data
    if isinstance(data, dict):
        return NatConfig.from_dict(data)
    raise ValueError(f"Cannot convert {type(data)} to NatConfig")


def convert_acl_config(data: Union[Dict[str, Any], AclConfig, None]) -> Optional[AclConfig]:
    """Convert various ACL config formats to AclConfig object.
    
    Args:
        data: Dictionary, AclConfig object, or None
        
    Returns:
        AclConfig object or None
    """
    if data is None:
        return None
    if isinstance(data, AclConfig):
        return data
    if isinstance(data, dict):
        return AclConfig.from_dict(data)
    raise ValueError(f"Cannot convert {type(data)} to AclConfig")
