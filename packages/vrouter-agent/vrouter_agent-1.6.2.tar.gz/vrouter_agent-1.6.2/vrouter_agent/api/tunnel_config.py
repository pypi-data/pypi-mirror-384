"""
API endpoints for tunnel configuration management.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from loguru import logger

from vrouter_agent.core.db import get_session
from vrouter_agent.models.tunnel_config import TunnelConfigData, TunnelConfigHistory, TunnelState, ConfigDataState
from vrouter_agent.schemas.tunnel_config import TunnelConfigData as TunnelConfigSchema
from vrouter_agent.utils import get_device_serial_number
from vrouter_agent.enhanced_stream_processor import get_stream_processor
from vrouter_agent.utils.config import get_device_short_hostname
from vrouter_agent.services.client import VRouterClient

router = APIRouter(prefix="/tunnel-config", tags=["tunnel-config"])


def extract_vpp_interface_data(tunnel_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract VPP interface data from a tunnel configuration.
    
    Args:
        tunnel_data: Dictionary containing tunnel configuration data
        
    Returns:
        Dictionary containing only VPP interface related fields
    """
    vpp_interface_data = {}
    vpp_fields = [
        'vpp_interface_name', 'vpp_ip_address', 'vpp_subnet_mask', 
        'vpp_type', 'vpp_used', 'vpp_interface_index', 'vpp_status',
        'vpp_up', 'vpp_operational', 'vpp_connectivity_test_passed',
        'vpp_created_at', 'vpp_last_verified_at'
    ]
    
    for field in vpp_fields:
        if field in tunnel_data:
            vpp_interface_data[field] = tunnel_data[field]
    
    return vpp_interface_data


def enhance_tunnel_config_with_vpp_data(config: TunnelConfigData) -> Dict[str, Any]:
    """
    Enhance tunnel configuration with VPP interface data embedded within each tunnel.
    
    Args:
        config: TunnelConfigData model instance
        
    Returns:
        Enhanced configuration dictionary with VPP interface data embedded in tunnels
    """
    enhanced_config = {
        "id": config.id,
        "order_id": config.order_id,
        "order_number": config.order_number,
        "node_hostname": config.node_hostname,
        "tag": config.tag,
        "action": config.action,
        "topology_id": config.topology_id,
        "topology_data": config.topology_data,
        "state": config.state,
        "config_version": config.config_version,
        "created_at": config.created_at,
        "updated_at": config.updated_at,
        "applied_at": config.applied_at,
        "processed_at": config.processed_at,
        "error_message": config.error_message,
        "source": config.source,
        "tunnels": []  # Changed from tunnels_data to tunnels
    }
    
    # Process each tunnel and embed VPP interface data
    for tunnel_data in config.tunnels_data or []:
        # Create a copy of tunnel data
        tunnel_info = dict(tunnel_data)
        logger.debug(f"MARK: Processing tunnel data: {tunnel_info}")
        
        # Extract VPP interface data if present
        vpp_interface_data = extract_vpp_interface_data(tunnel_data)
        
        # If we have VPP interface data, embed it as vpp_interface object
        if vpp_interface_data:
            tunnel_info["vpp_interface"] = vpp_interface_data
        else:
            tunnel_info["vpp_interface"] = None
        
        enhanced_config["tunnels"].append(tunnel_info)
    
    return enhanced_config


@router.get("/")
async def get_tunnel_configurations(
    session: Session = Depends(get_session),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    applied: bool = Query(False, description="Return only active configurations"),
    order_id: Optional[str] = Query(None, description="Filter by order ID"),
):
    """
    Retrieve tunnel configurations.
    
    Args:
        session: Database session
        offset: Number of records to skip for pagination
        limit: Maximum number of records to return
        applied: If True, return only active configurations
        order_id: Filter by order ID
    
    Returns:
        List of tunnel configurations in standardized format
    """
    try:
        query = select(TunnelConfigData)

        # Note: Since we removed config-level state, we'll filter based on individual tunnel states
        # applied parameter now means at least one tunnel is active
        configurations = session.exec(query.offset(offset).limit(limit).order_by(TunnelConfigData.created_at.desc())).all()
        
        # If applied filter is requested, filter configs that are applied
        if applied:
            filtered_configs = []
            for config in configurations:
                if config.state == ConfigDataState.APPLIED:
                    filtered_configs.append(config)
            configurations = filtered_configs
        
        if order_id:
            configurations = [c for c in configurations if c.order_id == order_id]
        
        logger.info(f"Retrieved {len(configurations)} tunnel configurations")
        
        # Enhance configurations with VPP interface data
        enhanced_configurations = []
        for config in configurations:
            enhanced_config = enhance_tunnel_config_with_vpp_data(config)
            enhanced_configurations.append(enhanced_config)
    
        return {
            "success": True,
            "data": enhanced_configurations,
            "total": len(enhanced_configurations),
            "offset": offset,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error retrieving tunnel configurations: {e}")
        return {
            "success": False,
            "error": f"Failed to retrieve tunnel configurations: {str(e)}"
        }


@router.get("/{config_id}")
async def get_tunnel_configuration(
    config_id: int,
    session: Session = Depends(get_session),
):
    """
    Retrieve a specific tunnel configuration by ID.
    
    Args:
        config_id: The ID of the tunnel configuration
        session: Database session
    
    Returns:
        Tunnel configuration details
    """
    try:
        configuration = session.get(TunnelConfigData, config_id)
        
        if not configuration:
            raise HTTPException(status_code=404, detail="Tunnel configuration not found")
        
        logger.info(f"Retrieved tunnel configuration {config_id}")
        
        # Enhance configuration with VPP interface data
        enhanced_config = enhance_tunnel_config_with_vpp_data(configuration)
                
        return {
            "success": True,
            "data": enhanced_config
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving tunnel configuration {config_id}: {e}")
        return {
            "success": False,
            "error": f"Failed to retrieve tunnel configuration: {str(e)}"
        }


@router.get("/by-tunnel/{tunnel_id}")
async def get_tunnel_configuration_by_tunnel_id(
    tunnel_id: str,
    session: Session = Depends(get_session),
    include_history: bool = Query(False, description="Include configuration history"),
):
    """
    Retrieve tunnel configuration by tunnel interface name.
    
    Args:
        tunnel_id: The tunnel interface name to search for (e.g., wg-20yzzp2)
        session: Database session
        include_history: Whether to include configuration history
    
    Returns:
        Tunnel configuration and optionally its history
    """
    try:
        # Get all configurations and filter by tunnel interface name
        query = select(TunnelConfigData)
        configurations = session.exec(query).all()
        
        matching_config = None
        for config in configurations:
            # Search through tunnels_data for matching interface_name
            if config.tunnels_data:
                for tunnel in config.tunnels_data:
                    if tunnel.get('interface_name') == tunnel_id:
                        matching_config = config
                        break
                if matching_config:
                    break
        
        if not matching_config:
            raise HTTPException(status_code=404, detail=f"Tunnel configuration with interface '{tunnel_id}' not found")
        
        # Enhance configuration with VPP interface data
        enhanced_config = enhance_tunnel_config_with_vpp_data(matching_config)
        
        result = {
            "success": True,
            "data": {
                "current_config": enhanced_config
            }
        }
        
        if include_history:
            # Get configuration history
            history_query = select(TunnelConfigHistory).where(
                TunnelConfigHistory.config_id == matching_config.id
            ).order_by(TunnelConfigHistory.created_at.desc())
            
            history = session.exec(history_query).all()
            result["data"]["history"] = [
                {
                    "id": h.id,
                    "config_id": h.config_id,
                    "change_type": h.change_type,
                    "old_state": h.old_state,
                    "new_state": h.new_state,
                    "old_config_data_state": h.old_config_data_state,
                    "new_config_data_state": h.new_config_data_state,
                    "change_description": h.change_description,
                    "changed_by": h.changed_by,
                    "config_snapshot": h.config_snapshot,
                    "created_at": h.created_at
                }
                for h in history
            ]
        
        logger.info(f"Retrieved tunnel configuration for tunnel interface {tunnel_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving tunnel configuration for tunnel {tunnel_id}: {e}")
        return {
            "success": False,
            "error": f"Failed to retrieve tunnel configuration: {str(e)}"
        }


@router.get("/device/{device_serial}")
async def get_device_tunnel_configurations(
    device_serial: str,
    session: Session = Depends(get_session),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    state: Optional[str] = Query(None, description="Filter by configuration state"),
    order_id: Optional[str] = Query(None, description="Filter by order ID"),
):
    """
    Retrieve all tunnel configurations for a specific device.
    
    Args:
        device_serial: The device serial number/hostname
        session: Database session
        offset: Number of records to skip for pagination
        limit: Maximum number of records to return
        state: Filter by configuration state
        order_id: Filter by order ID
    
    Returns:
        List of tunnel configurations for the device
    """
    try:
        query = select(TunnelConfigData).where(TunnelConfigData.node_hostname == device_serial)
        
        if order_id:
            query = query.where(TunnelConfigData.order_id == order_id)
        
        query = query.offset(offset).limit(limit).order_by(TunnelConfigData.created_at.desc())
        
        configurations = session.exec(query).all()

        # Filter by state if requested (based on config_data_state)
        if state:
            filtered_configs = []
            for config in configurations:
                if config.state == state:
                    filtered_configs.append(config)
            configurations = filtered_configs
    
            
        logger.info(f"Retrieved {len(configurations)} tunnel configurations for device {device_serial}")
        
        # Enhance configurations with VPP interface data
        enhanced_configurations = []
        for config in configurations:
            enhanced_config = enhance_tunnel_config_with_vpp_data(config)
            enhanced_configurations.append(enhanced_config)
        
        return {
            "success": True,
            "data": enhanced_configurations,
            "total": len(enhanced_configurations),
            "device_serial": device_serial,
            "offset": offset,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error retrieving tunnel configurations for device {device_serial}: {e}")
        return {
            "success": False,
            "error": f"Failed to retrieve tunnel configurations: {str(e)}"
        }


@router.get("/current-device/")
async def get_current_device_tunnel_configurations(
    session: Session = Depends(get_session),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    state: Optional[str] = Query(None, description="Filter by configuration state"),
    order_id: Optional[str] = Query(None, description="Filter by order ID"),
):
    """
    Retrieve all tunnel configurations for the current device with embedded VPP interface data.
    
    Args:
        session: Database session
        offset: Number of records to skip for pagination
        limit: Maximum number of records to return
        state: Filter by configuration state
        order_id: Filter by order ID
    
    Returns:
        List of tunnel configurations for the current device with VPP interface data properly formatted
    """
    try:
        hostname = get_device_short_hostname()
        
        # Query database directly instead of calling the other endpoint to avoid double enhancement
        query = select(TunnelConfigData).where(TunnelConfigData.node_hostname == hostname)
        
        if order_id:
            query = query.where(TunnelConfigData.order_id == order_id)
        
        query = query.offset(offset).limit(limit).order_by(TunnelConfigData.created_at.desc())
        
        configurations = session.exec(query).all()

        # Filter by state if requested (based on config_data_state)
        if state:
            filtered_configs = []
            for config in configurations:
                if config.state == state:
                    filtered_configs.append(config)
            configurations = filtered_configs
        
        logger.info(f"Retrieved {len(configurations)} tunnel configurations for current device {hostname}")
        
        # Enhance configurations with VPP interface data
        enhanced_configurations = []
        for config in configurations:
            enhanced_config = enhance_tunnel_config_with_vpp_data(config)
            enhanced_configurations.append(enhanced_config)
        
        return {
            "success": True,
            "data": enhanced_configurations,
            "total": len(enhanced_configurations),
            "device_serial": hostname,
            "offset": offset,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error retrieving tunnel configurations for current device: {e}")
        return {
            "success": False,
            "error": f"Failed to retrieve current device tunnel configurations: {str(e)}"
        }


@router.get("/stats/")
async def get_tunnel_configuration_stats(
    session: Session = Depends(get_session),
):
    """
    Get statistics about tunnel configurations.
    
    Args:
        session: Database session
    
    Returns:
        Statistics about tunnel configurations
    """
    try:
        total_configs = session.exec(select(TunnelConfigData)).all()
        
        # Group by config_data_state values
        state_counts = {}
        action_counts = {}
        node_counts = {}
        
        for config in total_configs:
            # Count by config_data_state
            config_state = config.state
            state_counts[config_state] = state_counts.get(config_state, 0) + 1
            
            # Count by action
            action = config.action
            action_counts[action] = action_counts.get(action, 0) + 1
            
            # Count by node
            node = config.node_hostname
            node_counts[node] = node_counts.get(node, 0) + 1
        
        stats = {
            "total_configurations": len(total_configs),
            "state_breakdown": state_counts,
            "action_breakdown": action_counts,
            "node_breakdown": node_counts,
            "applied_configurations": state_counts.get("applied", 0),
            "error_configurations": state_counts.get("error", 0),
            "pending_configurations": state_counts.get("pending", 0),
            "rollback_configurations": state_counts.get("rollback", 0),
            "current_device": get_device_short_hostname(),
        }
        
        logger.info("Retrieved tunnel configuration statistics")
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"Error retrieving tunnel configuration statistics: {e}")
        return {
            "success": False,
            "error": f"Failed to retrieve tunnel configuration statistics: {str(e)}"
        }


@router.get("/health/")
async def get_tunnel_config_health():
    """
    Get health status of tunnel configuration system.
    
    Returns:
        Health status and basic system information
    """
    try:
        # Get stream processor status for tunnel configuration processing
        processor = get_stream_processor()
        
        if processor:
            processor_status = processor.get_status()
            is_healthy = processor_status.get("status") == "running"
        else:
            processor_status = {}
            is_healthy = False
        
        health_status = {
            "status": "healthy" if is_healthy else "unhealthy",
            "processor_running": is_healthy,
            "worker_count": processor_status.get("worker_count", 0),
            "queue_size": processor_status.get("queue_size", 0),
            "current_device": get_device_short_hostname(),
            "timestamp": processor_status.get("last_activity"),
            "components": {
                "stream_processor": "healthy" if is_healthy else "unhealthy",
                "database": "healthy",  # If we can query, DB is working
            }
        }
        
        logger.info("Retrieved tunnel configuration health status")
        return {
            "success": True,
            "data": health_status
        }
        
    except Exception as e:
        logger.error(f"Error retrieving tunnel configuration health status: {e}")
        return {
            "success": False,
            "error": f"Failed to retrieve tunnel configuration health status: {str(e)}"
        }
