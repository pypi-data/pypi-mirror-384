
    
from pydantic import BaseModel, Field, IPvAnyAddress
from typing import List, Optional, Dict, Union, Literal
from vrouter_agent.utils.config import get_frr_sync_dir
from ipaddress import IPv4Address, IPv4Network
from .frr_config import InitialFRRConfig, NodeConfig


class Multichain(BaseModel):
    """
    Multichain config defined in the YAML file. 
    This will be used to determine the chain name and directory for the multichain node.
    """
    chain: str
    chain_dir: str
    stream: str
  

class CreatedWireguardTunnel(BaseModel):
    """
    Created Wireguard Tunnel model.
    """
    name: str
    ip_address: str
    peer_ip_address: Optional[str] = None
    mapped_name: Optional[str] = None
    
class Interface(BaseModel):
    """
    Interface config defined in the YAML file.
    """
    interface_name: str
    type: Literal['wan','lan']
    ip_address: Optional[IPvAnyAddress] = None
    prefix_len: Optional[int]
    subnet_mask: Optional[str]
    is_primary: bool
    gateway: Optional[str]
    mtu: Optional[int] = 1500


class GlobalSettings(BaseModel):
    environment: str = Field(default="development")
    user: str = Field(default="usdn-admin")
    secret_key: str = Field(default="usdn-admin") # to decrypt the data


class AppConfig(BaseModel):
    global_:  GlobalSettings = Field(..., alias="global")
    interfaces: List[Interface] = Field(default=[])
    multichain: Multichain = Field(default=Multichain(chain="multichain", chain_dir="/opt/multichain", stream="vrouter"))
    frr: InitialFRRConfig
    
    
