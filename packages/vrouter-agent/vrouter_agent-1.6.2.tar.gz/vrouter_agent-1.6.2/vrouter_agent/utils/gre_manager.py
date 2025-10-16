"""
GRE Tunnel Management Module

This module provides robust GRE tunnel IP address allocation and management
following network engineering best practices.
"""

import ipaddress
from typing import Dict, List, Optional, Tuple, Set
from loguru import logger as log
from vrouter_agent.core.base import CreatedWireguardTunnel


class GREAddressManager:
    """
    Manages GRE tunnel IP address allocation with collision detection
    and proper network isolation.
    """
    
    def __init__(self, 
                 gre_network: str = "10.200.0.0/16",
                 subnet_size: int = 30):
        """
        Initialize GRE address manager.
        
        Args:
            gre_network: Base network for GRE tunnels (default: 10.200.0.0/16)
            subnet_size: Subnet size for each tunnel (default: /30 for point-to-point)
        """
        self.gre_network = ipaddress.IPv4Network(gre_network)
        self.subnet_size = subnet_size
        self.allocated_subnets: Set[ipaddress.IPv4Network] = set()
        self.tunnel_mappings: Dict[str, Tuple[str, str]] = {}  # wg_name -> (gre_local, gre_remote)
        
        # Validate subnet size
        if subnet_size < 30 or subnet_size > 32:
            raise ValueError("GRE subnet size must be between /30 and /32")
            
        log.info(f"GRE Address Manager initialized with network {gre_network}, subnet size /{subnet_size}")
    
    def allocate_gre_addresses(self, 
                              wg_tunnel: CreatedWireguardTunnel,
                              prefer_sequential: bool = True) -> Tuple[str, str]:
        """
        Allocate GRE IP addresses for a WireGuard tunnel.
        
        Args:
            wg_tunnel: WireGuard tunnel configuration
            prefer_sequential: Whether to prefer sequential allocation
            
        Returns:
            Tuple of (local_gre_ip_with_mask, remote_gre_ip)
            
        Raises:
            ValueError: If no addresses are available or input is invalid
        """
        try:
            # Validate WireGuard tunnel configuration
            if not wg_tunnel.name:
                raise ValueError("WireGuard tunnel name is required")
            
            # Normalize IP address format - ensure it has CIDR notation
            ip_address = wg_tunnel.ip_address
            if not ip_address:
                # If no IP address provided, generate based on tunnel name
                log.warning(f"No IP address provided for {wg_tunnel.name}, using tunnel index for generation")
                ip_address = self._generate_fallback_ip(wg_tunnel.name)
            elif "/" not in ip_address:
                # Add default /30 if no CIDR notation
                log.warning(f"IP address {ip_address} missing CIDR notation, assuming /30")
                ip_address = f"{ip_address}/30"
            
            # Create a normalized tunnel object for processing
            normalized_tunnel = CreatedWireguardTunnel(
                name=wg_tunnel.name,
                ip_address=ip_address,
                peer_ip_address=getattr(wg_tunnel, 'peer_ip_address', None) or self._generate_peer_ip(ip_address),
                mapped_name=getattr(wg_tunnel, 'mapped_name', None)
            )
            
            # Check if already allocated
            if normalized_tunnel.name in self.tunnel_mappings:
                local_ip, remote_ip = self.tunnel_mappings[normalized_tunnel.name]
                log.debug(f"Using existing GRE mapping for {normalized_tunnel.name}: {local_ip} -> {remote_ip}")
                return local_ip, remote_ip.split('/')[0]
            
            # Generate deterministic addresses based on WireGuard tunnel
            local_gre_ip, remote_gre_ip = self._generate_deterministic_addresses(normalized_tunnel)
            
            # Fallback to sequential allocation if deterministic fails
            if not local_gre_ip:
                local_gre_ip, remote_gre_ip = self._allocate_sequential_addresses()
            
            if not local_gre_ip:
                raise ValueError("No available GRE addresses in the allocated network")
            
            # Store the mapping
            local_with_mask = f"{local_gre_ip}/{self.subnet_size}"
            remote_with_mask = f"{remote_gre_ip}/{self.subnet_size}"
            
            self.tunnel_mappings[normalized_tunnel.name] = (local_with_mask, remote_with_mask)
            
            log.info(f"Allocated GRE addresses for {normalized_tunnel.name}: {local_with_mask} -> {remote_gre_ip}")
            return local_with_mask, remote_gre_ip
            
        except Exception as e:
            log.error(f"Failed to allocate GRE addresses for {wg_tunnel.name if wg_tunnel.name else 'unknown'}: {e}")
            raise
    
    def _generate_deterministic_addresses(self, 
                                        wg_tunnel: CreatedWireguardTunnel) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate deterministic GRE addresses based on WireGuard configuration.
        This ensures consistent address allocation across restarts.
        """
        try:
            # Extract WireGuard IP and use it to generate deterministic GRE IPs
            wg_ip = ipaddress.IPv4Address(wg_tunnel.ip_address.split('/')[0])
            
            # Use a hash-based approach for deterministic but distributed allocation
            # Convert WG IP to integer and use it as a seed
            wg_ip_int = int(wg_ip)
            
            # Generate base offset within our GRE network
            network_size = self.gre_network.num_addresses
            subnet_count = network_size // (2 ** (32 - self.subnet_size))
            
            # Use modulo to ensure we stay within bounds
            base_offset = (wg_ip_int % (subnet_count - 1)) * (2 ** (32 - self.subnet_size))
            
            # Calculate the subnet
            gre_subnet_int = int(self.gre_network.network_address) + base_offset
            gre_subnet = ipaddress.IPv4Network(f"{ipaddress.IPv4Address(gre_subnet_int)}/{self.subnet_size}")
            
            # Check for collision
            if gre_subnet in self.allocated_subnets:
                log.debug(f"Deterministic subnet {gre_subnet} already allocated, falling back to sequential")
                return None, None
            
            # Allocate the first usable IP as local, second as remote
            hosts = list(gre_subnet.hosts())
            if len(hosts) >= 2:
                self.allocated_subnets.add(gre_subnet)
                return str(hosts[0]), str(hosts[1])
            else:
                # For /31 or /32, handle specially
                if self.subnet_size == 31:
                    self.allocated_subnets.add(gre_subnet)
                    return str(gre_subnet.network_address), str(gre_subnet.broadcast_address)
                
        except Exception as e:
            log.warning(f"Failed to generate deterministic addresses: {e}")
            
        return None, None
    
    def _allocate_sequential_addresses(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Allocate GRE addresses sequentially.
        """
        try:
            # Generate all possible subnets
            subnets = list(self.gre_network.subnets(new_prefix=self.subnet_size))
            
            for subnet in subnets:
                if subnet not in self.allocated_subnets:
                    hosts = list(subnet.hosts())
                    if len(hosts) >= 2:
                        self.allocated_subnets.add(subnet)
                        return str(hosts[0]), str(hosts[1])
                    elif self.subnet_size == 31:
                        # RFC 3021 - /31 networks for point-to-point links
                        self.allocated_subnets.add(subnet)
                        return str(subnet.network_address), str(subnet.broadcast_address)
                        
        except Exception as e:
            log.error(f"Sequential allocation failed: {e}")
            
        return None, None
    
    def deallocate_gre_addresses(self, wg_tunnel_name: str) -> bool:
        """
        Deallocate GRE addresses for a WireGuard tunnel.
        
        Args:
            wg_tunnel_name: Name of the WireGuard tunnel
            
        Returns:
            True if successfully deallocated, False otherwise
        """
        try:
            if wg_tunnel_name not in self.tunnel_mappings:
                log.warning(f"No GRE mapping found for {wg_tunnel_name}")
                return False
            
            local_ip, remote_ip = self.tunnel_mappings[wg_tunnel_name]
            
            # Find and remove the allocated subnet
            local_network = ipaddress.IPv4Network(local_ip, strict=False).supernet(new_prefix=self.subnet_size)
            self.allocated_subnets.discard(local_network)
            
            # Remove from mappings
            del self.tunnel_mappings[wg_tunnel_name]
            
            log.info(f"Deallocated GRE addresses for {wg_tunnel_name}: {local_ip}")
            return True
            
        except Exception as e:
            log.error(f"Failed to deallocate GRE addresses for {wg_tunnel_name}: {e}")
            return False
    
    def get_gre_mapping(self, wg_tunnel_name: str) -> Optional[Tuple[str, str]]:
        """
        Get existing GRE mapping for a WireGuard tunnel.
        
        Returns:
            Tuple of (local_gre_ip_with_mask, remote_gre_ip) or None
        """
        if wg_tunnel_name in self.tunnel_mappings:
            local_ip, remote_ip = self.tunnel_mappings[wg_tunnel_name]
            return local_ip, remote_ip.split('/')[0]
        return None
    
    def list_allocations(self) -> Dict[str, Tuple[str, str]]:
        """
        List all current GRE allocations.
        
        Returns:
            Dictionary mapping WireGuard tunnel names to (local_ip, remote_ip) tuples
        """
        result = {}
        for wg_name, (local_ip, remote_ip) in self.tunnel_mappings.items():
            result[wg_name] = (local_ip, remote_ip.split('/')[0])
        return result
    
    def validate_network_configuration(self) -> List[str]:
        """
        Validate the current network configuration and return any issues.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        issues = []
        
        # Check for overlapping allocations
        allocated_networks = []
        for subnet in self.allocated_subnets:
            for existing in allocated_networks:
                if subnet.overlaps(existing):
                    issues.append(f"Overlapping subnets detected: {subnet} and {existing}")
            allocated_networks.append(subnet)
        
        # Check if we're running out of space
        total_subnets = len(list(self.gre_network.subnets(new_prefix=self.subnet_size)))
        utilization = len(self.allocated_subnets) / total_subnets
        
        if utilization > 0.8:
            issues.append(f"High network utilization: {utilization:.1%} of GRE network space used")
        elif utilization > 0.9:
            issues.append(f"Critical network utilization: {utilization:.1%} of GRE network space used")
        
        return issues
    
    def _generate_fallback_ip(self, tunnel_name: str) -> str:
        """
        Generate a fallback IP address based on tunnel name when none is provided.
        
        Args:
            tunnel_name: Name of the tunnel (e.g., "wg0", "wg1")
            
        Returns:
            IP address with CIDR notation
        """
        try:
            # Extract index from tunnel name
            if tunnel_name.startswith("wg"):
                index = int(tunnel_name[2:])
            else:
                # Use hash of tunnel name if we can't extract index
                index = hash(tunnel_name) % 255
            
            # Generate IP in a safe range
            base_ip = f"192.168.{100 + (index % 155)}.{1 + (index % 2)}"
            return f"{base_ip}/30"
            
        except Exception:
            # Final fallback
            return "192.168.199.1/30"
    
    def _generate_peer_ip(self, local_ip: str) -> str:
        """
        Generate a peer IP address based on the local IP.
        
        Args:
            local_ip: Local IP address with CIDR notation
            
        Returns:
            Peer IP address with CIDR notation
        """
        try:
            if "/" not in local_ip:
                return f"{local_ip.rsplit('.', 1)[0]}.{int(local_ip.split('.')[-1]) + 1}/30"
            
            ip_part, cidr = local_ip.split("/")
            octets = ip_part.split(".")
            last_octet = int(octets[-1])
            
            # For /30 networks, alternate between .1/.2 and .5/.6, etc.
            if last_octet % 4 == 1:
                peer_last_octet = last_octet + 1
            elif last_octet % 4 == 2:
                peer_last_octet = last_octet - 1
            else:
                # Fallback to next IP
                peer_last_octet = last_octet + 1 if last_octet < 254 else last_octet - 1
            
            octets[-1] = str(peer_last_octet)
            return f"{'.'.join(octets)}/{cidr}"
            
        except Exception:
            # Fallback
            return "192.168.199.2/30"


# Global instance for the application
_gre_manager: Optional[GREAddressManager] = None


def get_gre_manager(**kwargs) -> GREAddressManager:
    """
    Get or create the global GRE address manager instance.
    
    Args:
        **kwargs: Arguments to pass to GREAddressManager constructor
        
    Returns:
        GREAddressManager instance
    """
    global _gre_manager
    if _gre_manager is None:
        _gre_manager = GREAddressManager(**kwargs)
    return _gre_manager


def convert_wg_to_gre_ip_addr_safe(wg_tunnel: CreatedWireguardTunnel, 
                                  manager: Optional[GREAddressManager] = None) -> Tuple[str, str]:
    """
    Safely convert WireGuard tunnel to GRE IP addresses using the manager.
    
    Args:
        wg_tunnel: WireGuard tunnel configuration
        manager: Optional GRE manager instance (uses global if None)
        
    Returns:
        Tuple of (local_gre_ip_with_mask, remote_gre_ip)
    """
    if manager is None:
        manager = get_gre_manager()
    
    return manager.allocate_gre_addresses(wg_tunnel)
