"""
Pydantic schemas for tunnel configuration data.
These schemas match the tunnel_data structure from the Django tasks.py file.

NAT and ACL schemas are imported from nat_acl_config module.
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum, IntEnum
import ipaddress

# Import NAT and ACL configurations from dedicated module
from vrouter_agent.schemas.nat_acl_config import NatConfig, AclConfig


class TunnelState(str, Enum):
    """Enumeration of possible tunnel configuration states"""
    PLANNED = "planned"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"


class TopologyInfo(BaseModel):
    """Topology information in tunnel configuration"""

    id: Union[str, int] = Field(description="Topology ID")
    name: str = Field(description="Topology name")
    type: str = Field(
        description="Topology type (hub_spoke, point_to_point, full_mesh)"
    )
    
    @validator('id', pre=True)
    def convert_id_to_string(cls, v):
        """Convert topology ID to string if it's an integer"""
        return str(v) if v is not None else None


class ClientInterface(BaseModel):
    """Client interface configuration for VPP and routing"""
    
    name: str = Field(description="Interface name (e.g., vpp-lan)")
    type: str = Field(description="Interface type (e.g., lan, wan)")
    ip_address: str = Field(description="IP address of the interface")
    subnet_mask: int = Field(description="Subnet mask (CIDR notation)")
    mac_address: Optional[str] = Field(None, description="MAC address of the interface")
    vpp_whitelisted: Optional[bool] = Field(None, description="Whether interface is whitelisted in VPP")
    distribution_mode: Optional[str] = Field(None, description="Routing distribution mode (ospf, bgp)")
    ospf_area: Optional[str] = Field(None, description="OSPF area for this interface")
    ospf_cost: Optional[int] = Field(None, description="OSPF cost for this interface")
    bgp_remote_asn: Optional[int] = Field(None, description="Remote BGP ASN if using BGP")
    is_enabled: Optional[bool] = Field(True, description="Whether the interface is enabled")

class BgpPeer(BaseModel):
    """BGP peer configuration for VPP and routing"""
    
    remote_asn: int = Field(description="Remote ASN for this BGP peer")
    peer_ip: str = Field(description="IP address of the BGP peer")
    peer_type: str = Field(description="Type of BGP peer (internal, external)")
    multihop: Optional[int] = Field(0, description="Whether multihop is enabled")
    next_hop_self: Optional[bool] = Field(False, description="Whether next-hop self is enabled")
    is_enabled: Optional[bool] = Field(True, description="Whether the BGP peer is enabled")
    lan_interface_ip: Optional[str] = Field(None, description="LAN interface IP address for this peer")
    lan_mac_address: Optional[str] = Field(None, description="LAN MAC address for this peer")

    @validator('remote_asn')
    def convert_asn_to_int(cls, v):
        """Convert ASN to integer if it's a string"""
        return int(v) if isinstance(v, str) and v.isdigit() else v
    
    
class WireGuardConfig(BaseModel):
    """WireGuard tunnel configuration"""

    interface_name: str = Field(description="WireGuard interface name")
    private_key: Optional[str] = Field(None, description="Private key for this node")
    listen_port: Optional[int] = Field(None, description="Listen port for WireGuard")
    address: Optional[str] = Field(None, description="Tunnel IP address")
    peer_public_key: Optional[str] = Field(None, description="Peer's public key")
    allowed_ips: Optional[str] = Field(None, description="Allowed IPs for the peer")
    persistent_keepalive: int = Field(default=25, description="Keepalive interval")
    peer_endpoint: Optional[str] = Field(None, description="Peer endpoint IP:port")
    mtu: Optional[int] = Field(default=1420, description="Maximum transmission unit")
    peer_address: Optional[str] = Field(None, description="Peer IP address for routing")
    source_ip: Optional[str] = Field(None, description="Source IP address for tunnel")
    
    # VPP Interface Data Fields (embedded from VPP interface mappings)
    vpp_interface_name: Optional[str] = Field(None, description="VPP interface name (e.g., wg0, wg1)")
    vpp_ip_address: Optional[str] = Field(None, description="VPP interface IP address")
    vpp_subnet_mask: Optional[int] = Field(None, description="VPP interface subnet mask")
    vpp_type: Optional[str] = Field(None, description="VPP interface type (tunnel)")
    vpp_used: Optional[bool] = Field(None, description="Whether VPP interface is in use")
    vpp_interface_index: Optional[int] = Field(None, description="VPP interface index")
    vpp_status: Optional[str] = Field(None, description="VPP interface status (created, up, down)")
    vpp_up: Optional[bool] = Field(None, description="Whether VPP interface is up")
    vpp_operational: Optional[bool] = Field(None, description="Whether VPP interface is operational")
    vpp_connectivity_test_passed: Optional[bool] = Field(None, description="Whether connectivity test passed")
    vpp_created_at: Optional[str] = Field(None, description="Timestamp when VPP interface was created")
    vpp_last_verified_at: Optional[str] = Field(None, description="Timestamp of last verification")
    
    # Tunnel State Management
    state: Optional[TunnelState] = Field(None, description="Current operational state of the tunnel")
    tunnel_id: Optional[str] = Field(None, description="Unique tunnel identifier")
    action: Optional[str] = Field(None, description="Action to perform on this tunnel (create, update, delete)")
    
    # GRE Tunnel Configuration
    gre_local_name: Optional[str] = Field(None, description="GRE tunnel local interface name")
    gre_remote_name: Optional[str] = Field(None, description="GRE tunnel remote interface name")
    gre_local_tunnel_ip: Optional[str] = Field(None, description="Local GRE tunnel IP address")
    gre_remote_tunnel_ip: Optional[str] = Field(None, description="Remote GRE tunnel IP address")
    
    @validator('tunnel_id', pre=True)
    def convert_tunnel_id_to_string(cls, v):
        """Convert tunnel_id to string if it's an integer"""
        return str(v) if v is not None else None



class FrrConfig(BaseModel):
    """FRR routing configuration structure"""

    zebra_config: Optional[str] = Field(None, description="Zebra daemon configuration")
    ospf_config: Optional[str] = Field(None, description="OSPF routing configuration")
    bgp_config: Optional[str] = Field(None, description="BGP routing configuration")
    static_config: Optional[str] = Field(None, description="Static routes configuration")
    full_config: Optional[str] = Field(None, description="Complete FRR configuration")
    config_hash: Optional[str] = Field(None, description="Configuration hash for validation")

    def to_config_string(self) -> str:
        """
        Convert the structured FRR configuration to a single configuration string.
        
        Returns:
            str: Complete FRR configuration as a string
        """
        # If full_config is available, use it
        if self.full_config:
            return self.full_config
        
        # Otherwise, build from components
        config_parts = []
        
        # Add header
        config_parts.append("! FRR Configuration")
        config_parts.append("! Generated by VRouter Agent")
        config_parts.append("!")
        
        # Add each configuration section
        if self.zebra_config:
            config_parts.append("! Zebra Configuration")
            config_parts.append(self.zebra_config.strip())
            config_parts.append("!")
        
        if self.ospf_config:
            config_parts.append("! OSPF Configuration")
            config_parts.append(self.ospf_config.strip())
            config_parts.append("!")
        
        if self.bgp_config:
            config_parts.append("! BGP Configuration")
            config_parts.append(self.bgp_config.strip())
            config_parts.append("!")
        
        if self.static_config:
            config_parts.append("! Static Routes Configuration")
            config_parts.append(self.static_config.strip())
            config_parts.append("!")
        
        return "\n".join(config_parts)

    @classmethod
    def from_string(cls, config_string: str) -> "FrrConfig":
        """
        Create an FrrConfig instance from a configuration string.
        This is a basic parser - for complex configurations, you may need a more sophisticated approach.
        
        Args:
            config_string: FRR configuration as a string
            
        Returns:
            FrrConfig: Parsed configuration object
        """
        return cls(full_config=config_string.strip())

    def is_empty(self) -> bool:
        """Check if the configuration is empty."""
        return not any([
            self.zebra_config,
            self.ospf_config, 
            self.bgp_config,
            self.static_config,
            self.full_config
        ])


class TunnelConfigData(BaseModel):
    """Main tunnel configuration data structure"""

    tag: str = Field(description="Configuration tag", default="tunnel_config")
    action: str = Field(description="Action to perform (provision, decommission)")
    order_id: str = Field(description="Order ID")
    order_number: str = Field(description="Order number")
    topology: Optional[TopologyInfo] = Field(None, description="Topology information")
    tunnels: List[WireGuardConfig] = Field(description="List of tunnel configurations")
    client_interfaces: Optional[List[ClientInterface]] = Field(
        None, description="List of client interface configurations"
    )
    bgp_peers: Optional[List[BgpPeer]] = Field(
        None, description="List of BGP peer configurations if eBGP is used"
    )
    ospf_enabled: Optional[bool] = Field(
        default=False, description="Whether OSPF protocol is enabled"
    )
    ebgp_enabled: Optional[bool] = Field(
        default=False, description="Whether eBGP protocol is enabled"
    )
    frr_config: Optional[FrrConfig] = Field(
        None, description="FRR configuration if available"
    )
    nat_config: Optional[NatConfig] = Field(
        None, description="NAT44 configuration (VPP-compatible)"
    )
    acl_config: Optional[AclConfig] = Field(
        None, description="ACL configuration (VPP-compatible)"
    )
    state: TunnelState = Field(
        default=TunnelState.PLANNED, 
        description="Current state of the tunnel configuration"
    )
 

class NodeTunnelConfig(BaseModel):
    """Node-specific tunnel configuration for blockchain posting"""

    hostname: str = Field(description="Node hostname")
    config: TunnelConfigData = Field(description="Tunnel configuration for this node")


class BlockchainPostData(BaseModel):
    """Data structure for posting to blockchain"""

    tunnel_data: TunnelConfigData = Field(description="Tunnel configuration data")
    encrypted_data: str = Field(description="Encrypted hex data for blockchain")
    stream_name: str = Field(description="Blockchain stream name")
    txid: Optional[str] = Field(None, description="Transaction ID after posting")


# Request/Response schemas for API endpoints
class TunnelConfigRequest(BaseModel):
    """Request schema for tunnel configuration"""

    order_id: str
    topology_id: str
    action: str = Field(default="provision", pattern="^(provision|decommission)$")


class TunnelConfigResponse(BaseModel):
    """Response schema for tunnel configuration"""

    success: bool
    message: str
    data: Optional[Dict[str, TunnelConfigData]] = None
    errors: Optional[List[str]] = None


class BlockchainPostRequest(BaseModel):
    """Request schema for blockchain posting"""

    order_id: str
    node_hostname: Optional[str] = Field(
        None, description="Specific node to post config for"
    )


class BlockchainPostResponse(BaseModel):
    """Response schema for blockchain posting"""

    success: bool
    results: List[Dict[str, Any]] = Field(description="Results per node")
    errors: Optional[List[str]] = None
