"""
Tunnel Operations Module

This module contains all tunnel-related functionality extracted from the enhanced stream processor
to improve code organization and modularity. It manages the lifecycle of tunnel configurations including 
creation, updates, verification, and deletion of WireGuard tunnels and associated VPP interfaces.

This implementation has been refactored to simplify the code and improve maintainability.
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger as log
from sqlmodel import Session

from vrouter_agent.models.tunnel_config import (
    TunnelConfigData as TunnelConfigModel, 
    TunnelConfigHistory, 
    TunnelState, 
    ConfigDataState
)
from vrouter_agent.schemas.tunnel_config import (
    TunnelConfigData as TunnelConfigSchema
)
from vrouter_agent.schemas.nat_acl_config import convert_nat_config, convert_acl_config
from vrouter_agent.core.enums import StreamItemAction
from vrouter_agent.core.base import CreatedWireguardTunnel
from vrouter_agent.services.refactored_client import VRouterClient
from vrouter_agent.services.multichain_notifier import send_tunnel_status_notification
from vrouter_agent.core.config import get_primary_interface, settings
from vrouter_agent.telemetry import tunnel_telemetry_collector, TunnelStatus, TunnelType

class TunnelOperations:
    """
    Handles all tunnel-related operations for the enhanced stream processor.
    
    This class provides methods for managing the lifecycle of tunnel configurations,
    including creation, update, verification, and deletion of WireGuard and GRE tunnels.
    
    It interacts with the VRouterClient to perform the actual tunnel operations and 
    maintains state information in the database for monitoring and auditing.
    
    The main entry point is the process_tunnel_config_event method, which handles
    incoming tunnel configuration events from the stream processor.
    """
    
    def __init__(self, hostname: str):
        """
        Initialize tunnel operations handler.
        
        Args:
            hostname: Node hostname for tunnel configuration filtering
        """
        self.hostname = hostname
    
    async def process_tunnel_config_event(
        self, 
        decrypted_data: Dict[str, Any], 
        event: Any,
        trigger_callbacks_func: callable
    ) -> None:
        """
        Process a tunnel configuration event.
        
        Args:
            decrypted_data: Decrypted transaction data
            event: Transaction event being processed
            trigger_callbacks_func: Function to trigger callbacks
        """
        config_data = decrypted_data
        action = decrypted_data["action"]
        
        # Validate incoming data according to action type
        self._validate_config_data(config_data, action)
        
        # Get or create tunnel config record
        tunnel_config = self.get_or_create_tunnel_config(event.session, config_data)
        log.debug(f"Tunnel config retrieved or created: {tunnel_config.order_id}, action: {tunnel_config.action}")
        
        # Store old config data state for history tracking
        tunnel_config._old_config_data_state = tunnel_config.state
        
        # Extract tunnels for this node
        tunnels = self.extract_node_tunnels(tunnel_config)
        
        if len(tunnels) == 0:
            log.debug("No tunnels found for this host in tunnel config. Skipping processing.")
            return

        # Process tunnels based on action
        try:
            success, interfaces = await self._handle_tunnel_action(action, tunnels, tunnel_config, event)
            
            # Update tunnel state data
            await self._update_tunnel_states(tunnel_config, success, action, event)
            
            # Trigger appropriate callback
            await self._trigger_callback(trigger_callbacks_func, action, tunnel_config, event, interfaces)
            
            # Send status notification to controller multichain server
            await self._send_status_notification(tunnel_config, action, success, interfaces, event)
            
        except Exception as e:
            log.error(f"Error processing tunnel config {tunnel_config.order_id}: {e}")
            
            # Handle error state and rollback if needed
            await self._handle_error_state(e, tunnel_config, event)
            
            # Send error notification to controller
            await self._send_error_notification(tunnel_config, str(e), event)
            
            raise
    
    def _validate_config_data(self, config_data: Dict[str, Any], action: str) -> None:
        """Validate the incoming configuration data based on the action."""
        if action != StreamItemAction.DECOMMISSION:
            try:
                TunnelConfigSchema(**config_data)
            except Exception as e:
                log.error(f"Invalid tunnel config data structure: {e}")
                raise ValueError(f"Invalid tunnel config data: {e}")
        else:
            log.debug(f"Skipping full schema validation for decommission action {action}")
            # For decommission, we just need basic structure validation
            if not config_data.get('tunnels') or not isinstance(config_data.get('tunnels'), list):
                raise ValueError("Decommission action requires 'tunnels' list in config data")
            
            # Add the action field to each tunnel for decommission tracking
            for tunnel_data in config_data.get('tunnels', []):
                if isinstance(tunnel_data, dict):
                    tunnel_data['action'] = 'delete'
    
    async def _handle_tunnel_action(self, action: str, tunnels: List[Dict[str, Any]], 
                                  tunnel_config: TunnelConfigModel, event: Any) -> Tuple[bool, List[Dict[str, Any]]]:
        """Handle the tunnel action based on the action type (provision, update, decommission)."""
        success = False
        interfaces = []
        
        log.info(f"Processing tunnel config {tunnel_config.order_id} with action {action}")
        
        if action == StreamItemAction.PROVISION:
            success, interfaces = await self._handle_provision(tunnels, tunnel_config, event)
        elif action == StreamItemAction.UPDATE:
            success, interfaces = await self._handle_update(tunnels, tunnel_config, event)
        elif action == StreamItemAction.DECOMMISSION:
            success = await self._handle_decommission(tunnels, tunnel_config, event)
            
        return success, interfaces
    
    async def _handle_provision(self, tunnels: List[Dict[str, Any]], 
                              tunnel_config: TunnelConfigModel, event: Any) -> Tuple[bool, List[Dict[str, Any]]]:
        """Handle tunnel provisioning."""
        success = False
        interfaces = []
        
        try:
            with VRouterClient(tunnels, tunnel_config.frr_config) as client:
                if not client.is_connected():
                    log.error("Failed to connect to VPP")
                    return False, []
                
                # Create WireGuard tunnels
                result = client.create_wireguard_tunnels()
                if not result['success']:
                    log.error("Failed to create WireGuard tunnels")
                    return False, []
                
                log.info(f"Created {len(result['created_tunnels'])} tunnels")
                interfaces = result.get('interfaces', [])
                
                # Verify tunnels
                verification = client.verify_tunnels_operational()
                for tunnel_status in verification:
                    log.info(f"Tunnel {tunnel_status['tunnel_name']}: {tunnel_status['status']}")
                
                # Handle FRR configuration if present
                if tunnel_config.frr_config:
                    await self._apply_frr_configuration(client, tunnel_config)
                
                # Handle NAT configuration if present
                if tunnel_config.nat_config:
                    log.debug(f"NAT config details: {tunnel_config.nat_config}")
                    
                    # Add identity mappings for WireGuard ports to allow tunnel traffic
                    nat_config = tunnel_config.nat_config
                    if nat_config.get('enabled', True):
                        # Collect WireGuard ports from tunnels
                        wg_ports = set()
                        for tunnel in tunnels:
                            if 'listen_port' in tunnel and tunnel['listen_port']:
                                wg_ports.add(int(tunnel['listen_port']))
                        
                        # Add identity mappings for WireGuard ports (UDP protocol)
                        if wg_ports:
                            from vrouter_agent.schemas.nat_acl_config import NatConfig, IdentityMapping, ProtocolInNAT
                            
                            # Convert dict to NatConfig if needed
                            if isinstance(nat_config, dict):
                                nat_config_obj = NatConfig.from_dict(nat_config)
                            else:
                                nat_config_obj = nat_config
                            
                            # Ensure dnat section exists
                            if not nat_config_obj.dnat:
                                from vrouter_agent.schemas.nat_acl_config import DNat44
                                nat_config_obj.dnat = DNat44(label="nat-mappings", identity_mappings=[])
                            
                            # Add identity mappings for each WireGuard port
                            for port in wg_ports:
                                identity_mapping = IdentityMapping(
                                    interface="",  # Will use WAN interface by default in nat_manager
                                    port=port,
                                    protocol=ProtocolInNAT.UDP  # WireGuard uses UDP
                                )
                                nat_config_obj.dnat.identity_mappings.append(identity_mapping)
                                log.info(f"Added identity mapping for WireGuard port {port} (UDP)")
                            
                            # Apply NAT configuration with identity mappings
                            nat_success = client.add_nat_configuration(nat_config=nat_config_obj)
                        else:
                            # No WireGuard ports found, apply NAT as-is
                            nat_success = client.add_nat_configuration(nat_config=nat_config)
                    else:
                        nat_success = client.add_nat_configuration(nat_config=nat_config)
                    
                    if not nat_success:
                        log.error("Failed to apply NAT configuration")
                        success = False
                    else:
                        log.info("NAT configuration applied successfully")
                
                # Handle ACL configuration if present
                log.debug(f"Applying ACL configuration: {tunnel_config.acl_config}")
                if tunnel_config.acl_config:
                    # Apply ACL configuration - conversion handled in ACL manager
                    acl_success = client.add_acl_configuration(acl_config=tunnel_config.acl_config)
                    
                    if not acl_success:
                        log.error("Failed to apply ACL configuration")
                        success = False
                    else:
                        log.info("ACL configuration applied successfully")

                # Store interface information
                await self._store_interface_mappings(tunnel_config, interfaces, client, event)
                
                # Verify tunnel states
                await self._verify_tunnel_states(client, tunnel_config, event)
                
                success = True
                
        except Exception as e:
            log.error(f"Error provisioning tunnels: {e}")
            success = False
            
        return success, interfaces
    
    async def _handle_update(self, tunnels: List[Dict[str, Any]],
                           tunnel_config: TunnelConfigModel, event: Any) -> Tuple[bool, List[Dict[str, Any]]]:
        """Handle tunnel update."""
        success = False
        interfaces = []
        
        try:
            with VRouterClient(tunnels, tunnel_config.frr_config) as client:
                if not client.is_connected():
                    log.error("Failed to connect to VPP")
                    return False, []
                
                # Update WireGuard tunnels
                creation_result = client.create_wireguard_tunnels()
                success = creation_result.get('success', False)
                
                if not success:
                    log.error("Failed to update WireGuard tunnels")
                    return False, []
                
                interfaces = creation_result.get('interfaces', [])
                tunnel_names = creation_result.get('created_tunnels', [])
                log.info(f"Updated {len(interfaces)} WireGuard interfaces: {tunnel_names}")
                
                # Store updated interface information
                await self._store_interface_mappings(tunnel_config, interfaces, client, event)
                
                # Handle FRR configuration if present
                if tunnel_config.frr_config:
                    await self._apply_frr_configuration(client, tunnel_config)
                
                # Handle NAT configuration if present
                # log.debug(f"Applying NAT configuration: {tunnel_config.nat_config}")
                # if tunnel_config.nat_config:
                #     nat_success = client.add_nat_configuration(nat_config=tunnel_config.nat_config)
                #     if not nat_success:
                #         log.error("Failed to apply NAT configuration")
                #         success = False
                #     else:
                #         log.info("NAT configuration applied successfully")
                # # Handle ACL configuration if present
                # if tunnel_config.acl_config:
                #     acl_success = client.add_acl_configuration(acl_config=tunnel_config.acl_config)
                #     if not acl_success:
                #         log.error("Failed to apply ACL configuration")
                #         success = False
                #     else:
                #         log.info("ACL configuration applied successfully")
                
                # Verify tunnel states
                await self._verify_tunnel_states(client, tunnel_config, event)
                
        except Exception as e:
            log.error(f"Error updating tunnels: {e}")
            success = False
            
        return success, interfaces
    
    async def _handle_decommission(self, tunnels: List[Dict[str, Any]],
                                 tunnel_config: TunnelConfigModel, event: Any) -> bool:
        """Handle tunnel decommissioning."""
        success = False
        
        try:
            with VRouterClient(tunnels, tunnel_config.frr_config) as client:
                if not client.is_connected():
                    log.error("Failed to connect to VPP")
                    return False
                
                # Since interface names now directly match, we can use the tunnel names as is
                # Just create the required tunnel objects for deletion
                interface_names = [t.get('interface_name') for t in tunnel_config.tunnels_data 
                                  if t.get('interface_name')]
                
                if not interface_names:
                    log.warning(f"No interface names found for deletion in {tunnel_config.order_id}")
                    return False
                
                # Prepare tunnel objects for deletion and set them in the client
                created_tunnels = self._prepare_tunnels_for_deletion(tunnel_config)
                client.wireguard.created_tunnels = created_tunnels
                
                # Remove tunnels
                success = client.remove_wireguard_tunnels()
                
                if tunnel_config.frr_config:
                    # Apply FRR configuration cleanup
                    await client.utility.remove_frr_configuration(tunnel_config)

                if success:
                    log.info(f"Successfully removed WireGuard tunnels for {tunnel_config.order_id}")
                    
                    # Record telemetry for deleted tunnels
                    for tunnel_data in tunnel_config.tunnels_data:
                        self._record_tunnel_telemetry(
                            tunnel_data, 
                            TunnelStatus.DOWN, 
                            tunnel_config,
                            {'interface_up': False, 'operational': False, 'connectivity_test': False}
                        )
                   
                else:
                    log.error(f"Failed to remove WireGuard tunnels for {tunnel_config.order_id}")
                
        except Exception as e:
            log.error(f"Error decommissioning tunnels: {e}")
            success = False
            
        return success
  
    
    async def _apply_frr_configuration(self, client: VRouterClient, tunnel_config: TunnelConfigModel) -> None:
        """Apply FRR configuration including GRE tunnels and LAN interfaces."""
        log.info("Creating GRE tunnels for FRR configuration")
        client.create_gre_tunnels()
        
        log.info("Exposing LAN interfaces to FRR")
        primary_lan = get_primary_interface(type='lan')
        client.utility.expose_lan_interface_to_frr_container(primary_lan)
        
        log.info("Adding BGP loopback for FRR")
        client.utility.add_bgp_loopback(str(settings.config.frr.node.loopback_ip))
        
        log.debug(f"frr config: {tunnel_config.frr_config}")
        
        # Handle client interfaces if present and OSPF is enabled
        if tunnel_config.client_interfaces and tunnel_config.ospf_enabled:
            log.info("Processing client interfaces for OSPF LCP")
            for client_iface in tunnel_config.client_interfaces:
                if not all(key in client_iface for key in ['ip_address', 'name', 'mac_address']):
                    log.warning(f"Client interface {client_iface.get('name', 'unknown')} missing required fields")
                    continue
                    
                client.utility.add_ospf_lcp_fix(
                    client_iface.get('ip_address'),
                    primary_lan.interface_name
                )
                
                client.utility.add_client_neighbour_info(
                    primary_lan.interface_name,
                    client_iface.get('ip_address'),
                    client_iface.get('mac_address')
                )
                
                log.info(f"Added OSPF LCP fix for client interface {client_iface.get('name')}")
        
        # if ebgp enabled we need to add a few routes 
        if tunnel_config.ebgp_enabled and tunnel_config.bgp_peers:
            log.info("Adding routes for eBGP communication")
            log.debug(f"eBGP peers: {tunnel_config.bgp_peers}")
            for peer in tunnel_config.bgp_peers:
                client.route.add_ebgp_route_in_frr_container(
                    peer.get('peer_ip'),
                    primary_lan.interface_name
                )
                client.utility.add_client_neighbour_info(
                        primary_lan.interface_name,
                        peer.get('lan_interface_ip'),
                        peer.get('lan_mac_address')
                    )
                client.route.add_ebgp_routes_in_vpp(
                        peer.get('peer_ip'),
                        peer.get('lan_interface_ip'),
                        primary_lan.interface_name
                    )
                # add neighbour info for the client loopback as well - for namespace routing
                client.utility.add_client_neighbour_info(
                        primary_lan.interface_name,
                        peer.get('peer_ip'),
                        peer.get('lan_mac_address')
                    )
        # Apply FRR config and add routes
        client.utility.apply_frr_configuration(tunnel_config.frr_config)
        
        log.info("Adding routes for bidirectional BGP communication")
        client.route.add_routes_for_bidirectional_bgp_communication(
            settings.config.frr.node.loopback_ip,
            settings.config.frr.controller.loopback,
            settings.config.frr.controller.address
        )
    
    async def _store_interface_mappings(self, tunnel_config: TunnelConfigModel, 
                                      interfaces: List[Dict[str, Any]], client: VRouterClient, 
                                      event: Any) -> None:
        """Store interface information to tunnel configuration."""
        try:
            # Since interface names now match directly, we can store interface data directly
            interface_data_by_name = {}
            
            # Prepare interface data indexed by interface name
            for interface in interfaces:
                name = interface.get('name')
                if name:
                    interface_data_by_name[name] = {
                        'vpp_ip_address': interface.get('ip_address'),
                        'vpp_subnet_mask': interface.get('subnet_mask'),
                        'vpp_type': interface.get('type', 'tunnel'),
                        'vpp_used': interface.get('vpp_used', True),
                        'vpp_interface_index': interface.get('interface_index'),
                        'vpp_status': interface.get('status', 'created'),
                        'vpp_up': False,
                        'vpp_operational': False,
                        'vpp_connectivity_test_passed': False,
                        'vpp_created_at': time.time()
                    }
            
            # Update tunnel data with interface information
            updated_tunnels_data = []
            
            for tunnel_data in tunnel_config.tunnels_data:
                tunnel_copy = dict(tunnel_data)
                interface_name = tunnel_copy.get('interface_name')
                
                # Update with interface data if found
                if interface_name and interface_name in interface_data_by_name:
                    tunnel_copy.update(interface_data_by_name[interface_name])
                    log.debug(f"Added interface data for '{interface_name}'")
                
                updated_tunnels_data.append(tunnel_copy)
            
            # Update tunnel config with updated data
            tunnel_config.tunnels_data = updated_tunnels_data
            event.session.add(tunnel_config)
            
            log.info(f"Stored interface data for {len(updated_tunnels_data)} tunnels")
            
        except Exception as e:
            log.error(f"Failed to store interface data: {e}")
            raise
    
    async def _verify_tunnel_states(self, client: VRouterClient, 
                                  tunnel_config: TunnelConfigModel, event: Any) -> None:
        """Verify tunnel states and update status in configuration."""
        try:
            # Wait briefly for interfaces to initialize
            await asyncio.sleep(2)
            
            # Now that interface names match directly, we can verify the tunnels by their configured names
            configured_interface_names = [t.get('interface_name') for t in tunnel_config.tunnels_data 
                                         if t.get('interface_name')]
            
            if not configured_interface_names:
                log.warning(f"No interface names found for {tunnel_config.order_id}")
                return
            
            # Verify operational status directly using configured names
            verification_results = client.verify_tunnels_operational_enhanced(configured_interface_names)
            
            # Update tunnel data with verification results
            updated_tunnels_data = []
            
            for tunnel_data in tunnel_config.tunnels_data:
                tunnel_copy = dict(tunnel_data)
                interface_name = tunnel_copy.get('interface_name')
                
                if not interface_name:
                    updated_tunnels_data.append(tunnel_copy)
                    continue
                
                # Get verification result
                result = verification_results.get(interface_name, {})
                
                # Update state based on verification
                old_state = tunnel_copy.get('state', TunnelState.PENDING)
                
                # Update tunnel data with verification results
                tunnel_copy.update({
                    'vpp_up': result.get('interface_up', False),
                    'vpp_operational': result.get('operational', False),
                    'vpp_connectivity_test_passed': result.get('connectivity_test', False),
                    'vpp_last_verified_at': datetime.now().isoformat()
                })
                
                if result.get('operational', False):
                    tunnel_copy['state'] = TunnelState.ACTIVE
                    log.info(f"Tunnel {interface_name} is active")
                    
                    # Record tunnel as UP in telemetry
                    self._record_tunnel_telemetry(
                        tunnel_copy, 
                        TunnelStatus.UP, 
                        tunnel_config, 
                        result
                    )
                else:
                    tunnel_copy['state'] = TunnelState.PENDING
                    issue = 'unknown reasons'
                    if not result.get('interface_up', False):
                        issue = 'interface is down'
                    elif not result.get('connectivity_test', False):
                        issue = 'connectivity test failed'
                    log.warning(f"Tunnel {interface_name} is pending - {issue}")
                    
                    # Record tunnel as DOWN in telemetry
                    tunnel_status = TunnelStatus.DOWN
                    if not result.get('interface_up', False):
                        tunnel_status = TunnelStatus.ERROR
                    
                    self._record_tunnel_telemetry(
                        tunnel_copy, 
                        tunnel_status, 
                        tunnel_config, 
                        result
                    )
                
                # Add history record for state change
                if old_state != tunnel_copy['state']:
                    await self._add_tunnel_state_history(
                        tunnel_config, 
                        old_state, 
                        tunnel_copy['state'], 
                        f"Tunnel {interface_name} state changed from {old_state} to {tunnel_copy['state']}",
                        event
                    )
                
                updated_tunnels_data.append(tunnel_copy)
            
            # Update tunnel data
            tunnel_config.tunnels_data = updated_tunnels_data
            event.session.add(tunnel_config)
            
            # Log summary
            active_count = sum(1 for t in updated_tunnels_data if t.get('state') == TunnelState.ACTIVE)
            total_count = len(updated_tunnels_data)
            log.info(f"{active_count}/{total_count} tunnels verified as active")
            
        except Exception as e:
            log.error(f"Error verifying tunnel states: {e}")
            raise
    
    def _prepare_tunnels_for_deletion(self, tunnel_config: TunnelConfigModel) -> List[CreatedWireguardTunnel]:
        """Prepare tunnel data for deletion."""
        created_tunnels = []
        
        for tunnel_data in tunnel_config.tunnels_data:
            interface_name = tunnel_data.get('interface_name')
            vpp_ip = tunnel_data.get('vpp_ip_address')
            
            if interface_name:
                created_tunnel = CreatedWireguardTunnel(
                    name=interface_name,
                    ip_address=vpp_ip or "0.0.0.0/32", 
                    mapped_name=interface_name  # No mapping needed as they're the same
                )
                created_tunnels.append(created_tunnel)
                log.debug(f"Prepared tunnel for deletion: {interface_name}")
        
        return created_tunnels
    
    def _update_tunnels_to_inactive(self, tunnel_config: TunnelConfigModel, event: Any) -> List[Dict[str, Any]]:
        """Update tunnel states to inactive after successful deletion."""
        updated_data = []
        
        for tunnel_data in tunnel_config.tunnels_data:
            tunnel_copy = dict(tunnel_data)
            old_state = tunnel_copy.get('state', TunnelState.PENDING)
            
            # Set to inactive
            tunnel_copy['state'] = TunnelState.INACTIVE
            
            # Add history record if state changed
            if old_state != TunnelState.INACTIVE:
                interface_name = tunnel_copy.get('interface_name', 'unknown')
                
                history = TunnelConfigHistory(
                    config_id=tunnel_config.id,
                    change_type="state_update",
                    old_state=old_state,
                    new_state=TunnelState.INACTIVE,
                    old_config_data_state=tunnel_config.state,
                    new_config_data_state=tunnel_config.state,
                    change_description=f"Tunnel {interface_name} decommissioned",
                    changed_by="enhanced_stream_processor",
                    config_snapshot=tunnel_config.raw_config_data
                )
                event.session.add(history)
            
            updated_data.append(tunnel_copy)
        
        return updated_data
    
    async def _update_tunnel_states(self, tunnel_config: TunnelConfigModel, 
                                  success: bool, action: str, event: Any) -> None:
        """Update tunnel configuration state based on operation success."""
        # Update processed timestamp
        tunnel_config.processed_at = datetime.fromtimestamp(event.timestamp)
        
        if success:
            tunnel_config.state = ConfigDataState.APPLIED
            tunnel_config.applied_at = datetime.fromtimestamp(event.timestamp)
            tunnel_config.error_message = None
        else:
            tunnel_config.state = ConfigDataState.ERROR
            tunnel_config.error_message = f"Failed to {action} configuration"
        
        event.session.add(tunnel_config)
        
        # Add history record
        active_count = sum(1 for t in tunnel_config.tunnels_data if t.get('state') == TunnelState.ACTIVE)
        total_count = len(tunnel_config.tunnels_data)
        
        if success:
            desc = f"Configuration {action} succeeded - {active_count}/{total_count} tunnels active"
            state = TunnelState.ACTIVE
            change_type = "applied"
        else:
            desc = f"Configuration {action} failed"
            state = TunnelState.ERROR
            change_type = "failed"
            
        history = TunnelConfigHistory(
            config_id=tunnel_config.id,
            change_type=change_type,
            old_state=None,
            new_state=state,
            old_config_data_state=tunnel_config._old_config_data_state,
            new_config_data_state=tunnel_config.state,
            change_description=desc,
            changed_by="enhanced_stream_processor",
            config_snapshot=tunnel_config.raw_config_data
        )
        event.session.add(history)
        
        # Commit changes
        try:
            event.session.commit()
            log.info(f"Tunnel config {tunnel_config.order_id} state updated to {tunnel_config.state}")
        except Exception as e:
            log.error(f"Failed to commit tunnel config changes: {e}")
            try:
                event.session.rollback()
            except:
                pass
            raise
    
    async def _trigger_callback(self, trigger_callbacks_func: callable, action: str, 
                              tunnel_config: TunnelConfigModel, event: Any, 
                              interfaces: List[Dict[str, Any]]) -> None:
        """Trigger the appropriate callback based on the action."""
        if action == StreamItemAction.PROVISION:
            await trigger_callbacks_func('tunnel_config_created', {
                'config': tunnel_config, 
                'event': event,
                'interfaces': interfaces
            })
        elif action == StreamItemAction.UPDATE:
            await trigger_callbacks_func('tunnel_config_updated', {
                'config': tunnel_config, 
                'event': event,
                'interfaces': interfaces
            })
        elif action == StreamItemAction.DECOMMISSION:
            await trigger_callbacks_func('tunnel_config_deleted', {
                'config': tunnel_config, 
                'event': event
            })
    
    async def _handle_error_state(self, error: Exception, tunnel_config: TunnelConfigModel, event: Any) -> None:
        """Handle error state and update tunnel data."""
        # Rollback any pending changes
        try:
            event.session.rollback()
        except Exception as rollback_error:
            log.error(f"Failed to rollback session: {rollback_error}")
        
        # Update tunnel config with error state
        try:
            tunnel_config.state = ConfigDataState.ERROR
            tunnel_config.error_message = str(error)
            tunnel_config.processed_at = datetime.fromtimestamp(event.timestamp)
            
            # Set all tunnels to error state
            updated_tunnels_data = []
            for tunnel_data in tunnel_config.tunnels_data:
                tunnel_copy = dict(tunnel_data)
                tunnel_copy['state'] = TunnelState.ERROR
                updated_tunnels_data.append(tunnel_copy)
            
            tunnel_config.tunnels_data = updated_tunnels_data
            event.session.add(tunnel_config)
            
            # Add history record
            error_count = len(updated_tunnels_data)
            total_count = len(updated_tunnels_data)
            
            history = TunnelConfigHistory(
                config_id=tunnel_config.id,
                change_type="failed",
                old_state=None,
                new_state=TunnelState.ERROR,
                old_config_data_state=getattr(tunnel_config, '_old_config_data_state', None),
                new_config_data_state=ConfigDataState.ERROR,
                change_description=f"Configuration processing failed: {str(error)} - {error_count}/{total_count} tunnels in error state",
                changed_by="enhanced_stream_processor",
                config_snapshot=tunnel_config.raw_config_data
            )
            event.session.add(history)
            event.session.commit()
        except Exception as update_error:
            log.error(f"Failed to update tunnel config failure state: {update_error}")
            try:
                event.session.rollback()
            except:
                pass
    
    async def _add_tunnel_state_history(self, tunnel_config: TunnelConfigModel, old_state: str, 
                                      new_state: str, description: str, event: Any) -> None:
        """Add a history record for tunnel state change."""
        history = TunnelConfigHistory(
            config_id=tunnel_config.id,
            change_type="state_update",
            old_state=old_state,
            new_state=new_state,
            old_config_data_state=tunnel_config.state,
            new_config_data_state=tunnel_config.state,
            change_description=description,
            changed_by="enhanced_stream_processor",
            config_snapshot=tunnel_config.raw_config_data
        )
        event.session.add(history)

    async def _send_status_notification(
        self, 
        tunnel_config: TunnelConfigModel, 
        action: str, 
        success: bool,
        interfaces: List[Dict[str, Any]], 
        event: Any
    ) -> None:
        """
        Send tunnel status notification to controller multichain server.
        
        Args:
            tunnel_config: Tunnel configuration model
            action: Action performed (provision, update, decommission)
            success: Whether the operation was successful
            interfaces: List of interface data
            event: Transaction event
        """
        try:
            # Prepare additional context data
            additional_data = {
                "success": success,
                "operation_timestamp": event.timestamp,
                "event_id": getattr(event, 'id', None),
                "processing_duration": None,  # Could calculate if needed
                "node_version": getattr(settings, 'version', 'unknown')
            }
            
            # Add error context if operation failed
            if not success:
                additional_data["error_context"] = {
                    "error_message": tunnel_config.error_message,
                    "failed_at": datetime.now().isoformat()
                }
            
            # Send the notification
            notification_sent = await send_tunnel_status_notification(
                tunnel_config=tunnel_config,
                action=action,
                interfaces=interfaces if success else None,
                additional_data=additional_data
            )
            
            if notification_sent:
                log.info(f"Status notification sent to controller for order {tunnel_config.order_id}, "
                        f"action: {action}, success: {success}")
            else:
                log.warning(f"Failed to send status notification for order {tunnel_config.order_id}")
                
        except Exception as e:
            # Don't fail the main operation if notification fails
            log.error(f"Error sending status notification for order {tunnel_config.order_id}: {e}")

    async def _send_error_notification(
        self, 
        tunnel_config: TunnelConfigModel, 
        error_message: str, 
        event: Any
    ) -> None:
        """
        Send error notification to controller multichain server.
        
        Args:
            tunnel_config: Tunnel configuration model
            error_message: Error message
            event: Transaction event
        """
        try:
            from vrouter_agent.services.multichain_notifier import get_multichain_notifier
            
            notifier = get_multichain_notifier()
            
            error_details = {
                "event_id": getattr(event, 'id', None),
                "event_timestamp": event.timestamp,
                "node_hostname": self.hostname,
                "processing_stage": "tunnel_operations"
            }
            
            notification_sent = await notifier.send_error_notification(
                tunnel_config=tunnel_config,
                error_message=error_message,
                error_details=error_details
            )
            
            if notification_sent:
                log.info(f"Error notification sent to controller for order {tunnel_config.order_id}")
            else:
                log.warning(f"Failed to send error notification for order {tunnel_config.order_id}")
                
        except Exception as e:
            # Don't fail the main operation if notification fails
            log.error(f"Error sending error notification for order {tunnel_config.order_id}: {e}")

    def get_or_create_tunnel_config(self, session: Session, config_data: Dict[str, Any]) -> TunnelConfigModel:
        """
        Get an existing tunnel configuration record or create a new one.
        
        Args:
            session: Database session
            config_data: Configuration data dictionary
            
        Returns:
            TunnelConfigModel: The existing or new tunnel configuration record
        """
        order_id = config_data.get("order_id")
        node_hostname = self.hostname
        
        # Try to find existing config
        existing_config = session.query(TunnelConfigModel).filter(
            TunnelConfigModel.order_id == order_id,
            TunnelConfigModel.node_hostname == node_hostname
        ).first()
        
        if existing_config:
            # Update existing config with new data
            existing_config.raw_config_data = config_data
            existing_config.tunnels_data = config_data.get("tunnels", [])
            existing_config.topology_id = config_data.get("topology", {}).get("id") if config_data.get("topology") else None
            existing_config.topology_data = config_data.get("topology", {})
            existing_config.frr_config = config_data.get("frr_config")
            existing_config.nat_config = config_data.get("nat_config")
            existing_config.acl_config = config_data.get("acl_config")
            existing_config.client_interfaces = config_data.get("client_interfaces", [])
            existing_config.bgp_peers = config_data.get("bgp_peers", [])
            existing_config.ospf_enabled = config_data.get("ospf_enabled", False)
            existing_config.ebgp_enabled = config_data.get("ebgp_enabled", False)
            existing_config.action = config_data.get("action")
            existing_config.order_number = config_data.get("order_number")
            existing_config.config_version += 1
            log.info(f"Updated existing tunnel config: {existing_config.id} for order {order_id} (version {existing_config.config_version})")
            return existing_config
        
        # Create new config
        new_config = TunnelConfigModel(
            order_id=order_id,
            order_number=config_data.get("order_number"),
            node_hostname=node_hostname,
            tag=config_data.get("tag", "tunnel_config"),
            action=config_data.get("action"),
            topology_id=config_data.get("topology", {}).get("id") if config_data.get("topology") else None,
            topology_data=config_data.get("topology", {}),
            tunnels_data=config_data.get("tunnels", []),
            frr_config=config_data.get("frr_config"),
            nat_config=config_data.get("nat_config"),
            acl_config=config_data.get("acl_config"),
            client_interfaces=config_data.get("client_interfaces", []),
            bgp_peers=config_data.get("bgp_peers", []),
            ospf_enabled=config_data.get("ospf_enabled", False),
            ebgp_enabled=config_data.get("ebgp_enabled", False),
            raw_config_data=config_data,
            source="stream"
        )
        
        session.add(new_config)
        session.flush()  # Get the ID
        log.info(f"Created new tunnel config: {new_config.id} for order {order_id}")
        return new_config

    def extract_node_tunnels(self, tunnel_config: TunnelConfigModel) -> List[Dict[str, Any]]:
        """
        Extract tunnel configurations relevant to this node.
        
        Args:
            tunnel_config: Tunnel configuration model
            
        Returns:
            List of tunnel configuration dictionaries for this node
        """
        # Filter tunnels by hostname if needed
        if not tunnel_config.tunnels_data:
            log.warning(f"No tunnels found in configuration {tunnel_config.order_id}")
            return []
            
        return tunnel_config.tunnels_data
    
    def _record_tunnel_telemetry(
        self, 
        tunnel_data: Dict[str, Any], 
        status: TunnelStatus,
        tunnel_config: TunnelConfigModel,
        verification_result: Dict[str, Any]
    ) -> None:
        """
        Record tunnel telemetry data for Splunk ingestion and API retrieval.
        
        Args:
            tunnel_data: Tunnel configuration data
            status: Current tunnel status
            tunnel_config: Parent tunnel configuration
            verification_result: VPP verification results
        """
        try:
            # Import and check telemetry collector
            import vrouter_agent.telemetry.tunnel_telemetry as telemetry_module
            if telemetry_module.tunnel_telemetry_collector is None:
                log.debug("Tunnel telemetry collector not initialized, skipping telemetry recording")
                return
            
            # Prepare telemetry data
            telemetry_data = {
                'name': tunnel_data.get('interface_name', 'unknown'),
                'type': 'wireguard',  # Default to wireguard, could be determined from config
                'local_ip': tunnel_data.get('vpp_ip_address'),
                'remote_ip': tunnel_data.get('peer_endpoint_address'),
                'peer_endpoint': tunnel_data.get('peer_endpoint'),
                'interface_index': tunnel_data.get('vpp_interface_index'),
                'order_id': tunnel_config.order_id,
                'order_number': tunnel_config.order_number,
                'topology_id': tunnel_config.topology_id,
                'config_version': str(tunnel_config.config_version),
                'created_at': tunnel_data.get('vpp_created_at'),
                
                # Add VPP-specific data
                'vpp_up': verification_result.get('interface_up', False),
                'vpp_operational': verification_result.get('operational', False),
                'connectivity_test_passed': verification_result.get('connectivity_test', False),
                
                # Add custom tags for better categorization
                'tags': [
                    f"order:{tunnel_config.order_number}" if tunnel_config.order_number else None,
                    f"topology:{tunnel_config.topology_id}" if tunnel_config.topology_id else None,
                    f"action:{tunnel_config.action}" if tunnel_config.action else None,
                    "vpp_verified",
                    "automated_monitoring"
                ]
            }
            
            # Filter out None tags
            telemetry_data['tags'] = [tag for tag in telemetry_data['tags'] if tag is not None]
            
            # Record the telemetry using the module reference
            telemetry_module.tunnel_telemetry_collector.record_tunnel_status(
                tunnel_id=tunnel_data.get('interface_name', 'unknown'),
                status=status,
                tunnel_data=telemetry_data
            )
            log.debug(f"Recorded tunnel telemetry: {tunnel_data.get('interface_name')} -> {status.value}")
            
        except Exception as e:
            log.error(f"Error recording tunnel telemetry: {e}")
            # Don't raise - telemetry failures shouldn't break tunnel operations
    


