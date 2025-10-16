"""
Root API endpoints for VRouter Agent
Provides general information and health status for the API
"""

from fastapi import APIRouter
from datetime import datetime
from vrouter_agent.enhanced_stream_processor import get_stream_processor
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/")
async def root():
    """
    Root endpoint providing basic API information
    """
    try:
        return {
            "success": True,
            "data": {
                "service": "VRouter Agent API",
                "version": "1.0.0",
                "description": "API for VRouter tunnel configuration and telemetry",
                "endpoints": {
                    "orders": "/orders",
                    "transactions": "/transactions", 
                    "tunnel_config": "/tunnel-config",
                    "telemetry": "/telemetry",
                    "docs": "/docs",
                    "health": "/health"
                },
                "documentation": "/docs"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in root endpoint: {str(e)}")
        return {
            "success": False,
            "error": f"Internal server error: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/health")
async def health_check():
    """
    Basic health check endpoint
    """
    try:
        # Try to get processor instance to check if system is healthy
        processor = await get_stream_processor()
        
        if processor:
            status = processor.get_status()
            is_healthy = status.get("status") == "running"
        else:
            is_healthy = False
            
        return {
            "success": True,
            "data": {
                "status": "healthy" if is_healthy else "unhealthy",
                "service": "VRouter Agent API",
                "processor_running": is_healthy,
                "timestamp": datetime.utcnow().isoformat()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return {
            "success": False,
            "error": f"Health check failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/version")
async def version_info():
    """
    Get version and build information
    """
    try:
        return {
            "success": True,
            "data": {
                "version": "1.0.0",
                "build_date": "2025-06-05",
                "api_version": "v1",
                "features": [
                    "tunnel_configuration",
                    "telemetry_monitoring", 
                    "health_checks",
                    "performance_metrics"
                ]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting version info: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to get version info: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }
