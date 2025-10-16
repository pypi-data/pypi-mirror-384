"""
Tunnel telemetry package for vrouter-agent

This package provides comprehensive tunnel status monitoring, structured logging for Splunk ingestion,
and API endpoints for telemetry data retrieval.
"""

from .tunnel_telemetry import (
    TunnelTelemetryCollector,
    TunnelTelemetryData,
    TunnelStatus,
    TunnelType,
    tunnel_telemetry_collector
)

__all__ = [
    'TunnelTelemetryCollector',
    'TunnelTelemetryData', 
    'TunnelStatus',
    'TunnelType',
    'tunnel_telemetry_collector'
]