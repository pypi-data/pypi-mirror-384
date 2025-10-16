"""
API endpoints for telemetry and metrics data.
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Query
from loguru import logger
import time
from datetime import datetime, timedelta

from vrouter_agent.enhanced_stream_processor import get_stream_processor
from vrouter_agent.utils import get_device_serial_number
from vrouter_agent.telemetry import tunnel_telemetry_collector, TunnelStatus

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.get("/metrics/")
async def get_metrics():
    """
    Get current system metrics from the stream processor.
    
    Returns:
        Current metrics including processing statistics, performance data, and system health
    """
    try:
        processor = await get_stream_processor()
        metrics = processor.get_metrics()
        
        # Enhance metrics with additional computed values
        enhanced_metrics = {
            **metrics,
            "device_serial": get_device_serial_number(),
            "timestamp": time.time(),
            "uptime_seconds": time.time() - metrics.get('start_time', time.time()),
        }
        
        # Calculate success rate
        total_processed = metrics.get('total_processed', 0)
        successful_processed = metrics.get('successful_processed', 0)
        if total_processed > 0:
            enhanced_metrics['success_rate'] = successful_processed / total_processed
        else:
            enhanced_metrics['success_rate'] = 0.0
        
        # Calculate failure rate
        failed_processed = metrics.get('failed_processed', 0)
        if total_processed > 0:
            enhanced_metrics['failure_rate'] = failed_processed / total_processed
        else:
            enhanced_metrics['failure_rate'] = 0.0
        
        logger.info("Retrieved system metrics")
        return enhanced_metrics
        
    except Exception as e:
        logger.error(f"Error retrieving metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")


@router.get("/status/")
async def get_system_status():
    """
    Get current system status and health information.
    
    Returns:
        System status including processor state, worker information, and health indicators
    """
    try:
        processor = await get_stream_processor()
        status = processor.get_status()
        
        # Enhance status with additional information
        enhanced_status = {
            **status,
            "device_serial": get_device_serial_number(),
            "timestamp": time.time(),
            "system_health": "healthy" if status.get("running", False) else "unhealthy",
        }
        
        # Add worker utilization status
        worker_utilization = status.get('worker_utilization', 0.0)
        if worker_utilization > 0.9:
            enhanced_status['worker_status'] = "high_load"
        elif worker_utilization > 0.7:
            enhanced_status['worker_status'] = "moderate_load"
        else:
            enhanced_status['worker_status'] = "normal"
        
        # Add queue status
        queue_size = status.get('queue_size', 0)
        if queue_size > 100:
            enhanced_status['queue_status'] = "high"
        elif queue_size > 50:
            enhanced_status['queue_status'] = "moderate"
        else:
            enhanced_status['queue_status'] = "normal"
        
        logger.info("Retrieved system status")
        return enhanced_status
        
    except Exception as e:
        logger.error(f"Error retrieving system status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system status")


@router.get("/health/")
async def get_health_check():
    """
    Comprehensive health check endpoint.
    
    Returns:
        Detailed health information including all subsystems
    """
    try:
        processor = await get_stream_processor()
        metrics = processor.get_metrics()
        status = processor.get_status()
        
        current_time = time.time()
        
        # Determine overall health
        is_healthy = True
        health_issues = []
        
        # Check if processor is running
        if not status.get("running", False):
            is_healthy = False
            health_issues.append("Stream processor is not running")
        
        # Check worker utilization
        worker_utilization = status.get('worker_utilization', 0.0)
        if worker_utilization > 0.95:
            health_issues.append("High worker utilization")
        
        # Check queue size
        queue_size = status.get('queue_size', 0)
        if queue_size > 200:
            is_healthy = False
            health_issues.append("Queue size is critically high")
        elif queue_size > 100:
            health_issues.append("Queue size is elevated")
        
        # Check for recent activity
        last_activity = status.get('last_activity')
        if last_activity and (current_time - last_activity) > 300:  # 5 minutes
            health_issues.append("No recent processing activity")
        
        # Check failure rate
        total_processed = metrics.get('total_processed', 0)
        failed_processed = metrics.get('failed_processed', 0)
        if total_processed > 0:
            failure_rate = failed_processed / total_processed
            if failure_rate > 0.1:  # 10% failure rate
                is_healthy = False
                health_issues.append(f"High failure rate: {failure_rate:.2%}")
        
        health_status = {
            "healthy": is_healthy,
            "status": "healthy" if is_healthy else "unhealthy",
            "issues": health_issues,
            "checks": {
                "processor_running": status.get("running", False),
                "worker_utilization_ok": worker_utilization < 0.95,
                "queue_size_ok": queue_size < 200,
                "recent_activity": last_activity is not None and (current_time - last_activity) < 300,
                "failure_rate_ok": (failed_processed / max(total_processed, 1)) < 0.1,
            },
            "metrics_summary": {
                "total_processed": total_processed,
                "success_rate": (metrics.get('successful_processed', 0) / max(total_processed, 1)),
                "failure_rate": (failed_processed / max(total_processed, 1)),
                "average_processing_time": metrics.get('average_processing_time', 0),
                "queue_size": queue_size,
                "worker_utilization": worker_utilization,
            },
            "device_serial": get_device_serial_number(),
            "timestamp": current_time,
        }
        
        logger.info(f"Health check completed - Status: {health_status['status']}")
        return health_status
        
    except Exception as e:
        logger.error(f"Error during health check: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform health check")


@router.get("/performance/")
async def get_performance_metrics():
    """
    Get detailed performance metrics.
    
    Returns:
        Performance-focused metrics and statistics
    """
    try:
        processor = await get_stream_processor()
        metrics = processor.get_metrics()
        status = processor.get_status()
        
        current_time = time.time()
        uptime = current_time - metrics.get('start_time', current_time)
        
        performance_metrics = {
            "processing_performance": {
                "total_processed": metrics.get('total_processed', 0),
                "successful_processed": metrics.get('successful_processed', 0),
                "failed_processed": metrics.get('failed_processed', 0),
                "retry_count": metrics.get('retry_count', 0),
                "average_processing_time_ms": metrics.get('average_processing_time', 0),
            },
            "system_performance": {
                "uptime_seconds": uptime,
                "uptime_hours": uptime / 3600,
                "worker_count": status.get('worker_count', 0),
                "worker_utilization": status.get('worker_utilization', 0.0),
                "queue_size": status.get('queue_size', 0),
            },
            "throughput": {
                "transactions_per_second": metrics.get('total_processed', 0) / max(uptime, 1),
                "successful_per_second": metrics.get('successful_processed', 0) / max(uptime, 1),
                "failed_per_second": metrics.get('failed_processed', 0) / max(uptime, 1),
            },
            "device_serial": get_device_serial_number(),
            "timestamp": current_time,
        }
        
        logger.info("Retrieved performance metrics")
        return performance_metrics
        
    except Exception as e:
        logger.error(f"Error retrieving performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance metrics")


@router.get("/system-info/")
async def get_system_info():
    """
    Get general system information.
    
    Returns:
        System information including device details and configuration
    """
    try:
        processor = await get_stream_processor()
        metrics = processor.get_metrics()
        
        system_info = {
            "device_serial": get_device_serial_number(),
            "processor_config": {
                "max_workers": getattr(processor, 'max_workers', 'unknown'),
                "batch_size": getattr(processor, 'batch_size', 'unknown'),
            },
            "runtime_info": {
                "start_time": metrics.get('start_time'),
                "start_time_iso": datetime.fromtimestamp(metrics.get('start_time', 0)).isoformat() if metrics.get('start_time') else None,
                "uptime_seconds": time.time() - metrics.get('start_time', time.time()),
                "last_activity": metrics.get('last_activity'),
                "last_activity_iso": datetime.fromtimestamp(metrics.get('last_activity', 0)).isoformat() if metrics.get('last_activity') else None,
            },
            "current_timestamp": time.time(),
            "current_timestamp_iso": datetime.now().isoformat(),
        }
        
        logger.info("Retrieved system information")
        return system_info
        
    except Exception as e:
        logger.error(f"Error retrieving system information: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system information")


@router.get("/alerts/")
async def get_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity: low, medium, high, critical"),
):
    """
    Get current system alerts and warnings.
    
    Args:
        severity: Optional severity filter
    
    Returns:
        List of current alerts and warnings
    """
    try:
        processor = await get_stream_processor()
        metrics = processor.get_metrics()
        status = processor.get_status()
        
        alerts = []
        current_time = time.time()
        
        # Check for various alert conditions
        
        # Critical alerts
        if not status.get("running", False):
            alerts.append({
                "severity": "critical",
                "message": "Stream processor is not running",
                "timestamp": current_time,
                "component": "stream_processor"
            })
        
        queue_size = status.get('queue_size', 0)
        if queue_size > 200:
            alerts.append({
                "severity": "critical",
                "message": f"Queue size critically high: {queue_size}",
                "timestamp": current_time,
                "component": "queue"
            })
        
        # High severity alerts
        worker_utilization = status.get('worker_utilization', 0.0)
        if worker_utilization > 0.95:
            alerts.append({
                "severity": "high",
                "message": f"Worker utilization very high: {worker_utilization:.1%}",
                "timestamp": current_time,
                "component": "workers"
            })
        
        total_processed = metrics.get('total_processed', 0)
        failed_processed = metrics.get('failed_processed', 0)
        if total_processed > 0:
            failure_rate = failed_processed / total_processed
            if failure_rate > 0.1:
                alerts.append({
                    "severity": "high",
                    "message": f"High failure rate: {failure_rate:.1%}",
                    "timestamp": current_time,
                    "component": "processing"
                })
        
        # Medium severity alerts
        if queue_size > 100:
            alerts.append({
                "severity": "medium",
                "message": f"Queue size elevated: {queue_size}",
                "timestamp": current_time,
                "component": "queue"
            })
        
        if worker_utilization > 0.8:
            alerts.append({
                "severity": "medium",
                "message": f"Worker utilization high: {worker_utilization:.1%}",
                "timestamp": current_time,
                "component": "workers"
            })
        
        # Low severity alerts
        last_activity = status.get('last_activity')
        if last_activity and (current_time - last_activity) > 300:  # 5 minutes
            alerts.append({
                "severity": "low",
                "message": "No recent processing activity",
                "timestamp": current_time,
                "component": "activity"
            })
        
        # Filter by severity if requested
        if severity:
            alerts = [alert for alert in alerts if alert['severity'] == severity.lower()]
        
        # Sort by severity (critical first)
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        alerts.sort(key=lambda x: severity_order.get(x['severity'], 4))
        
        result = {
            "alerts": alerts,
            "alert_count": len(alerts),
            "critical_count": len([a for a in alerts if a['severity'] == 'critical']),
            "high_count": len([a for a in alerts if a['severity'] == 'high']),
            "medium_count": len([a for a in alerts if a['severity'] == 'medium']),
            "low_count": len([a for a in alerts if a['severity'] == 'low']),
            "device_serial": get_device_serial_number(),
            "timestamp": current_time,
        }
        
        logger.info(f"Retrieved {len(alerts)} alerts")
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")


# Tunnel Telemetry Endpoints

@router.get("/tunnels/")
async def get_tunnel_telemetry(
    status: Optional[str] = Query(None, description="Filter by tunnel status: up, down, error, unknown"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    tunnel_id: Optional[str] = Query(None, description="Filter by specific tunnel ID"),
    include_metrics: bool = Query(True, description="Include performance metrics in response")
):
    """
    Get tunnel telemetry data with filtering capabilities.
    
    Args:
        status: Optional status filter (up, down, error, unknown)
        tags: Optional comma-separated list of tags for filtering
        tunnel_id: Optional specific tunnel ID to retrieve
        include_metrics: Whether to include performance metrics
    
    Returns:
        List of tunnel telemetry data matching the filters
    """
    try:
        # Check if tunnel telemetry collector is initialized
        if tunnel_telemetry_collector is None:
            logger.warning("Tunnel telemetry collector not initialized - returning empty results")
            return {
                "tunnels": [],
                "count": 0,
                "filters": {
                    "status": status,
                    "tags": tags,
                    "tunnel_id": tunnel_id,
                    "include_metrics": include_metrics
                }
            }
        
        # Get all tunnel telemetry data
        all_tunnels = tunnel_telemetry_collector.get_all_tunnel_telemetry()
        
        # Apply filters
        filtered_tunnels = all_tunnels
        
        # Filter by specific tunnel ID
        if tunnel_id:
            filtered_tunnels = [t for t in filtered_tunnels if t.tunnel_id == tunnel_id]
        
        # Filter by status
        if status:
            try:
                status_enum = TunnelStatus(status.lower())
                filtered_tunnels = [t for t in filtered_tunnels if t.status == status_enum]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        # Filter by tags
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',')]
            tag_set = set(tag_list)
            filtered_tunnels = [t for t in filtered_tunnels if tag_set.issubset(t.tags)]
        
        # Convert to dictionaries for response
        tunnel_data = []
        for tunnel in filtered_tunnels:
            tunnel_dict = tunnel.to_dict()
            
            # Optionally exclude metrics for lighter response
            if not include_metrics:
                tunnel_dict.pop('bytes_sent', None)
                tunnel_dict.pop('bytes_received', None)
                tunnel_dict.pop('packets_sent', None)
                tunnel_dict.pop('packets_received', None)
            
            tunnel_data.append(tunnel_dict)
        
        # Generate summary statistics
        summary = {
            "total_tunnels": len(tunnel_data),
            "status_breakdown": {},
            "device_serial": get_device_serial_number(),
            "timestamp": time.time(),
            "timestamp_iso": datetime.now().isoformat()
        }
        
        # Calculate status breakdown
        for status_val in TunnelStatus:
            count = len([t for t in filtered_tunnels if t.status == status_val])
            if count > 0:
                summary["status_breakdown"][status_val.value] = count
        
        result = {
            "tunnels": tunnel_data,
            "summary": summary,
            "filters_applied": {
                "status": status,
                "tags": tags,
                "tunnel_id": tunnel_id,
                "include_metrics": include_metrics
            }
        }
        
        logger.info(f"Retrieved tunnel telemetry: {len(tunnel_data)} tunnels")
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving tunnel telemetry: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve tunnel telemetry")


@router.get("/tunnels/{tunnel_id}")
async def get_tunnel_telemetry_by_id(tunnel_id: str):
    """
    Get detailed telemetry data for a specific tunnel.
    
    Args:
        tunnel_id: The tunnel identifier to retrieve
    
    Returns:
        Detailed tunnel telemetry data
    """
    try:
        # Check if tunnel telemetry collector is initialized
        if tunnel_telemetry_collector is None:
            logger.warning("Tunnel telemetry collector not initialized")
            raise HTTPException(status_code=503, detail="Tunnel telemetry service not available - no tunnel operations have been performed yet")
        
        tunnel_telemetry = tunnel_telemetry_collector.get_tunnel_telemetry(tunnel_id)
        
        if not tunnel_telemetry:
            raise HTTPException(status_code=404, detail=f"Tunnel '{tunnel_id}' not found")
        
        result = {
            "tunnel": tunnel_telemetry.to_dict(),
            "device_serial": get_device_serial_number(),
            "timestamp": time.time(),
            "timestamp_iso": datetime.now().isoformat()
        }
        
        logger.info(f"Retrieved telemetry for tunnel: {tunnel_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving tunnel telemetry for {tunnel_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve tunnel telemetry")


@router.get("/tunnels/summary/")
async def get_tunnel_summary():
    """
    Get a summary overview of all tunnel telemetry.
    
    Returns:
        Summary statistics and status overview of all tunnels
    """
    try:
        # Check if tunnel telemetry collector is initialized
        if tunnel_telemetry_collector is None:
            logger.warning("Tunnel telemetry collector not initialized - returning empty summary")
            return {
                "total_tunnels": 0,
                "status_breakdown": {},
                "tunnel_types": {},  
                "recent_changes": 0,
                "message": "Tunnel telemetry service not available - no tunnel operations have been performed yet",
                "device_serial": get_device_serial_number(),
                "timestamp": time.time(),
                "timestamp_iso": datetime.now().isoformat()
            }
        
        all_tunnels = tunnel_telemetry_collector.get_all_tunnel_telemetry()
        
        current_time = time.time()
        
        # Calculate summary statistics
        summary = {
            "total_tunnels": len(all_tunnels),
            "status_breakdown": {},
            "tunnel_types": {},
            "recent_changes": 0,
            "oldest_tunnel": None,
            "newest_tunnel": None,
            "active_time_stats": {
                "total_connection_time": 0,
                "average_connection_time": 0,
                "longest_connection": 0
            },
            "device_serial": get_device_serial_number(),
            "timestamp": current_time,
            "timestamp_iso": datetime.now().isoformat()
        }
        
        if not all_tunnels:
            return summary
        
        # Status breakdown
        for status in TunnelStatus:
            count = len([t for t in all_tunnels if t.status == status])
            if count > 0:
                summary["status_breakdown"][status.value] = count
        
        # Tunnel type breakdown
        for tunnel in all_tunnels:
            tunnel_type = tunnel.tunnel_type.value
            summary["tunnel_types"][tunnel_type] = summary["tunnel_types"].get(tunnel_type, 0) + 1
        
        # Recent changes (last 5 minutes)
        five_minutes_ago = current_time - 300
        summary["recent_changes"] = len([
            t for t in all_tunnels 
            if t.last_status_change and t.last_status_change > five_minutes_ago
        ])
        
        # Helper function to safely convert timestamp to ISO string
        def safe_timestamp_to_iso(timestamp):
            if not timestamp:
                return None
            try:
                # Handle both float timestamps and string ISO timestamps
                if isinstance(timestamp, str):
                    # Validate if it's a proper ISO string by trying to parse it
                    try:
                        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        return timestamp  # Valid ISO string
                    except ValueError:
                        # Invalid ISO string, return None
                        return None
                return datetime.fromtimestamp(float(timestamp)).isoformat()
            except (ValueError, TypeError):
                return None
        
        # Oldest and newest tunnels
        tunnels_by_creation = sorted(all_tunnels, key=lambda x: x.created_at or 0)
        if tunnels_by_creation:
            summary["oldest_tunnel"] = {
                "tunnel_id": tunnels_by_creation[0].tunnel_id,
                "created_at": tunnels_by_creation[0].created_at,
                "created_at_iso": safe_timestamp_to_iso(tunnels_by_creation[0].created_at)
            }
            summary["newest_tunnel"] = {
                "tunnel_id": tunnels_by_creation[-1].tunnel_id,
                "created_at": tunnels_by_creation[-1].created_at,
                "created_at_iso": safe_timestamp_to_iso(tunnels_by_creation[-1].created_at)
            }
        
        # Connection time statistics for UP tunnels
        up_tunnels = [t for t in all_tunnels if t.status == TunnelStatus.UP and t.connection_time]
        if up_tunnels:
            connection_times = [t.connection_time for t in up_tunnels if t.connection_time]
            if connection_times:
                summary["active_time_stats"]["total_connection_time"] = sum(connection_times)
                summary["active_time_stats"]["average_connection_time"] = sum(connection_times) / len(connection_times)
                summary["active_time_stats"]["longest_connection"] = max(connection_times)
        
        logger.info("Retrieved tunnel summary statistics")
        return summary
        
    except Exception as e:
        logger.error(f"Error retrieving tunnel summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve tunnel summary")


@router.post("/tunnels/cleanup/")
async def cleanup_tunnel_cache():
    """
    Clean up expired tunnel entries from the in-memory cache.
    
    Returns:
        Result of the cleanup operation
    """
    try:
        # Check if tunnel telemetry collector is initialized
        if tunnel_telemetry_collector is None:
            logger.warning("Tunnel telemetry collector not initialized - cannot cleanup cache")
            return {
                "cleaned_entries": 0,
                "remaining_entries": 0,
                "message": "Tunnel telemetry service not available - no cache to cleanup",
                "timestamp": time.time(),
                "timestamp_iso": datetime.now().isoformat()
            }
        
        before_count = len(tunnel_telemetry_collector.get_all_tunnel_telemetry())
        tunnel_telemetry_collector.cleanup_cache()
        after_count = len(tunnel_telemetry_collector.get_all_tunnel_telemetry())
        
        cleaned_count = before_count - after_count
        
        result = {
            "cleaned_entries": cleaned_count,
            "remaining_entries": after_count,
            "timestamp": time.time(),
            "timestamp_iso": datetime.now().isoformat()
        }
        
        logger.info(f"Cleaned up {cleaned_count} expired tunnel entries")
        return result
        
    except Exception as e:
        logger.error(f"Error during tunnel cache cleanup: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup tunnel cache")


@router.get("/tunnels/metrics/config/")
async def get_metrics_collection_config():
    """
    Get current metrics collection configuration.
    
    Returns:
        Current metrics collection settings
    """
    try:
        # Check if tunnel telemetry collector is initialized
        if tunnel_telemetry_collector is None:
            return {
                "metrics_collection_interval_seconds": 30,  # Default value
                "metrics_collection_running": False,
                "cache_timeout_seconds": 3600,  # Default value
                "active_tunnels_count": 0,
                "total_tunnels_count": 0,
                "status": "service_not_initialized",
                "message": "Tunnel telemetry service not available - no tunnel operations have been performed yet",
                "timestamp": time.time(),
                "timestamp_iso": datetime.now().isoformat()
            }
        
        result = {
            "metrics_collection_interval_seconds": tunnel_telemetry_collector.metrics_collection_interval,
            "metrics_collection_running": tunnel_telemetry_collector._metrics_collection_running,
            "cache_timeout_seconds": tunnel_telemetry_collector._cache_timeout,
            "active_tunnels_count": len([t for t in tunnel_telemetry_collector.get_all_tunnel_telemetry() if t.status == TunnelStatus.UP]),
            "total_tunnels_count": len(tunnel_telemetry_collector.get_all_tunnel_telemetry()),
            "timestamp": time.time(),
            "timestamp_iso": datetime.now().isoformat()
        }
        
        logger.info("Retrieved metrics collection configuration")
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving metrics collection config: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics collection configuration")


@router.post("/tunnels/metrics/config/")
async def update_metrics_collection_config(
    interval_seconds: int = Query(..., ge=1, le=3600, description="Metrics collection interval in seconds (1-3600)")
):
    """
    Update metrics collection interval.
    
    Args:
        interval_seconds: New collection interval in seconds (1-3600)
    
    Returns:
        Updated configuration
    """
    try:
        # Check if tunnel telemetry collector is initialized
        if tunnel_telemetry_collector is None:
            raise HTTPException(status_code=503, detail="Tunnel telemetry service not available - no tunnel operations have been performed yet")
        
        old_interval = tunnel_telemetry_collector.metrics_collection_interval
        tunnel_telemetry_collector.set_metrics_collection_interval(interval_seconds)
        
        result = {
            "old_interval_seconds": old_interval,
            "new_interval_seconds": interval_seconds,
            "metrics_collection_running": tunnel_telemetry_collector._metrics_collection_running,
            "timestamp": time.time(),
            "timestamp_iso": datetime.now().isoformat(),
            "message": f"Metrics collection interval updated from {old_interval}s to {interval_seconds}s"
        }
        
        logger.info(f"Updated metrics collection interval: {old_interval}s -> {interval_seconds}s")
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating metrics collection config: {e}")
        raise HTTPException(status_code=500, detail="Failed to update metrics collection configuration")


@router.post("/tunnels/metrics/start/")
async def start_metrics_collection():
    """
    Manually start tunnel metrics collection.
    
    Returns:
        Result of the start operation
    """
    try:
        # Check if tunnel telemetry collector is initialized
        if tunnel_telemetry_collector is None:
            raise HTTPException(status_code=503, detail="Tunnel telemetry service not available - no tunnel operations have been performed yet")
        
        if tunnel_telemetry_collector._metrics_collection_running:
            return {
                "already_running": True,
                "interval_seconds": tunnel_telemetry_collector.metrics_collection_interval,
                "message": "Metrics collection is already running",
                "timestamp": time.time(),
                "timestamp_iso": datetime.now().isoformat()
            }
        
        await tunnel_telemetry_collector.start_metrics_collection()
        
        result = {
            "started": True,
            "interval_seconds": tunnel_telemetry_collector.metrics_collection_interval,
            "message": "Metrics collection started successfully",
            "timestamp": time.time(),
            "timestamp_iso": datetime.now().isoformat()
        }
        
        logger.info("Manually started tunnel metrics collection")
        return result
        
    except Exception as e:
        logger.error(f"Error starting metrics collection: {e}")
        raise HTTPException(status_code=500, detail="Failed to start metrics collection")


@router.post("/tunnels/metrics/stop/")
async def stop_metrics_collection():
    """
    Manually stop tunnel metrics collection.
    
    Returns:
        Result of the stop operation
    """
    try:
        # Check if tunnel telemetry collector is initialized
        if tunnel_telemetry_collector is None:
            return {
                "already_stopped": True,
                "message": "Tunnel telemetry service not available - no metrics collection to stop",
                "timestamp": time.time(),
                "timestamp_iso": datetime.now().isoformat()
            }
        
        if not tunnel_telemetry_collector._metrics_collection_running:
            return {
                "already_stopped": True,
                "message": "Metrics collection is not running",
                "timestamp": time.time(),
                "timestamp_iso": datetime.now().isoformat()
            }
        
        await tunnel_telemetry_collector.stop_metrics_collection()
        
        result = {
            "stopped": True,
            "message": "Metrics collection stopped successfully",
            "timestamp": time.time(),
            "timestamp_iso": datetime.now().isoformat()
        }
        
        logger.info("Manually stopped tunnel metrics collection")
        return result
        
    except Exception as e:
        logger.error(f"Error stopping metrics collection: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop metrics collection")
