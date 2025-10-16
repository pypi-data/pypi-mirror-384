"""
Tunnel Telemetry Module

This module provides comprehensive tunnel telemetry collection, structured logging for Splunk ingestion,
and data management for tunnel status tracking. It integrates with the existing vRouter Agent
infrastructure to provide real-time tunnel status monitoring and historical data collection.
"""

import asyncio
import copy
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from loguru import logger as log
import statistics

from vrouter_agent.utils import get_device_serial_number
from vrouter_agent.utils.config import get_device_short_hostname
from vpp_vrouter.common import models

class TunnelStatus(Enum):
    """Tunnel operational status."""
    UP = "up"
    DOWN = "down"
    ERROR = "error"
    UNKNOWN = "unknown"
    CONNECTING = "connecting"
    DISCONNECTING = "disconnecting"


class TunnelType(Enum):
    """Supported tunnel types."""
    WIREGUARD = "wireguard"
    GRE = "gre"
    IPSEC = "ipsec"


@dataclass
class TunnelTelemetryData:
    """Tunnel telemetry data structure for structured logging and API retrieval."""
    
    # Core identification (required fields)
    tunnel_id: str              # Unique tunnel identifier (interface name)
    tunnel_name: str            # Human-readable tunnel name
    tunnel_type: TunnelType     # Type of tunnel (wireguard, gre, etc.)
    status: TunnelStatus        # Current operational status
    timestamp: float            # Current event timestamp
    
    # Optional status information
    previous_status: Optional[TunnelStatus] = None  # Previous status for change detection
    
    # Optional timestamps
    created_at: Optional[float] = None   # When tunnel was first created
    last_seen_up: Optional[float] = None # Last time tunnel was confirmed up
    last_status_change: Optional[float] = None # Last status change timestamp
    
    # Optional network configuration
    local_ip: Optional[str] = None      # Local tunnel IP address
    remote_ip: Optional[str] = None     # Remote tunnel IP address  
    peer_endpoint: Optional[str] = None # Remote peer endpoint
    interface_index: Optional[int] = None # VPP interface index
    
    # Optional performance metrics
    bytes_sent: Optional[int] = None    # Bytes transmitted
    bytes_received: Optional[int] = None # Bytes received
    packets_sent: Optional[int] = None  # Packets transmitted
    packets_received: Optional[int] = None # Packets received
    connection_time: Optional[float] = None # How long tunnel has been up
    
    # Optional configuration context
    order_id: Optional[str] = None      # Related order ID
    order_number: Optional[str] = None  # Human-readable order number
    topology_id: Optional[str] = None   # Topology identifier
    config_version: Optional[str] = None # Configuration version
    
    # Device context with defaults
    device_serial: str = ""             # Device serial number
    device_hostname: str = ""           # Device hostname
    
    # Tagging for retrieval and filtering
    tags: Set[str] = None              # Tags for categorization and search
    
    def __post_init__(self):
        """Initialize default values and tags."""
        if self.tags is None:
            self.tags = set()
        
        # Auto-populate device info
        if not self.device_serial:
            self.device_serial = get_device_serial_number()
        if not self.device_hostname:
            self.device_hostname = get_device_short_hostname()
        
        # Auto-generate base tags
        self.tags.update({
            f"tunnel_type:{self.tunnel_type.value}",
            f"status:{self.status.value}",
            f"device:{self.device_serial}",
            f"hostname:{self.device_hostname}"
        })
        
        # Add order-based tags if available
        if self.order_id:
            self.tags.add(f"order_id:{self.order_id}")
        if self.order_number:
            self.tags.add(f"order_number:{self.order_number}")
        if self.topology_id:
            self.tags.add(f"topology_id:{self.topology_id}")
    
    def add_tag(self, tag: str) -> None:
        """Add a custom tag for filtering and search."""
        self.tags.add(tag)
    
    def add_tags(self, tags: List[str]) -> None:
        """Add multiple custom tags."""
        self.tags.update(tags)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert enums to string values
        data['status'] = self.status.value
        data['tunnel_type'] = self.tunnel_type.value
        if self.previous_status:
            data['previous_status'] = self.previous_status.value
        # Convert set to list for JSON serialization
        data['tags'] = list(self.tags)
        return data
    
    def is_status_change(self) -> bool:
        """Check if this represents a status change event."""
        return self.previous_status is not None and self.previous_status != self.status


@dataclass
class TunnelUtilizationMetrics:
    """Comprehensive tunnel utilization metrics."""
    
    # Bandwidth utilization
    throughput_bps_tx: float = 0.0      # Bytes per second transmitted
    throughput_bps_rx: float = 0.0      # Bytes per second received
    throughput_pps_tx: float = 0.0      # Packets per second transmitted  
    throughput_pps_rx: float = 0.0      # Packets per second received
    bandwidth_utilization_percent: float = 0.0  # % of theoretical capacity used
    
    # Connection quality
    uptime_percent: float = 0.0         # % time tunnel has been up
    error_rate_percent: float = 0.0     # % of packets that are errors
    stability_score: float = 0.0        # Inverse of status change frequency (0-100)
    
    # Resource efficiency
    avg_packet_size_tx: float = 0.0     # Average transmitted packet size
    avg_packet_size_rx: float = 0.0     # Average received packet size
    connection_duration_hours: float = 0.0  # Hours of continuous connection
    
    # Composite scores
    overall_utilization_score: float = 0.0   # Weighted composite score (0-100)
    performance_grade: str = "N/A"      # Letter grade (A, B, C, D, F)
    
    # Metadata
    measurement_period_seconds: float = 0.0
    sample_count: int = 0
    last_calculated: float = 0.0


class TunnelUtilizationCalculator:
    """
    Calculates comprehensive tunnel utilization metrics from telemetry data.
    
    Provides multiple utilization perspectives:
    - Bandwidth utilization (primary metric)
    - Connection quality and stability 
    - Resource efficiency
    - Composite scoring for overall assessment
    """
    
    def __init__(self, max_bandwidth_mbps: float = 1000.0):
        """
        Initialize utilization calculator.
        
        Args:
            max_bandwidth_mbps: Theoretical maximum bandwidth in Mbps for utilization calculations
        """
        self.max_bandwidth_mbps = max_bandwidth_mbps
        self.max_bandwidth_bps = max_bandwidth_mbps * 1_000_000 / 8  # Convert to bytes per second
        
        # Historical data for trend analysis
        self._utilization_history: Dict[str, List[TunnelUtilizationMetrics]] = {}
        self._max_history_samples = 100  # Keep last 100 calculations per tunnel
        
    def calculate_utilization(
        self,
        current_data: TunnelTelemetryData,
        previous_data: Optional[TunnelTelemetryData] = None,
        measurement_period_seconds: float = None
    ) -> TunnelUtilizationMetrics:
        """
        Calculate comprehensive utilization metrics for a tunnel.
        
        Args:
            current_data: Current tunnel telemetry data
            previous_data: Previous telemetry data for rate calculations
            measurement_period_seconds: Time period between measurements
            
        Returns:
            TunnelUtilizationMetrics: Comprehensive utilization metrics
        """
        current_time = time.time()
        
        # Determine measurement period
        if measurement_period_seconds is None:
            if previous_data and previous_data.timestamp:
                measurement_period_seconds = current_data.timestamp - previous_data.timestamp
            else:
                measurement_period_seconds = 30.0  # Default to 30 seconds
        
        # Initialize metrics
        metrics = TunnelUtilizationMetrics(
            measurement_period_seconds=measurement_period_seconds,
            sample_count=1,
            last_calculated=current_time
        )
        
        # Calculate bandwidth utilization
        if previous_data and measurement_period_seconds > 0:
            metrics = self._calculate_bandwidth_metrics(current_data, previous_data, measurement_period_seconds, metrics)
        
        # Calculate connection quality metrics
        metrics = self._calculate_quality_metrics(current_data, previous_data, metrics)
        
        # Calculate resource efficiency metrics
        metrics = self._calculate_efficiency_metrics(current_data, previous_data, metrics)
        
        # Calculate composite scores
        metrics = self._calculate_composite_scores(metrics)
        
        # Store in history for trend analysis
        self._store_utilization_history(current_data.tunnel_id, metrics)
        
        return metrics
    
    def _calculate_bandwidth_metrics(
        self,
        current: TunnelTelemetryData,
        previous: TunnelTelemetryData,
        period_seconds: float,
        metrics: TunnelUtilizationMetrics
    ) -> TunnelUtilizationMetrics:
        """Calculate bandwidth-related utilization metrics."""
        
        log.debug(f"Calculating bandwidth metrics for {current.tunnel_id}")
        log.debug(f"Current: bytes_sent={current.bytes_sent}, bytes_received={current.bytes_received}, packets_sent={current.packets_sent}, packets_received={current.packets_received}")
        log.debug(f"Previous: bytes_sent={previous.bytes_sent}, bytes_received={previous.bytes_received}, packets_sent={previous.packets_sent}, packets_received={previous.packets_received}")
        log.debug(f"Period: {period_seconds} seconds")
        
        # Calculate byte rates
        if current.bytes_sent and previous.bytes_sent:
            byte_diff_tx = max(0, current.bytes_sent - previous.bytes_sent)
            metrics.throughput_bps_tx = byte_diff_tx / period_seconds
            log.debug(f"TX byte rate: {byte_diff_tx} bytes over {period_seconds}s = {metrics.throughput_bps_tx} bps")
            
        if current.bytes_received and previous.bytes_received:
            byte_diff_rx = max(0, current.bytes_received - previous.bytes_received)
            metrics.throughput_bps_rx = byte_diff_rx / period_seconds
            log.debug(f"RX byte rate: {byte_diff_rx} bytes over {period_seconds}s = {metrics.throughput_bps_rx} bps")
        
        # Calculate packet rates
        if current.packets_sent and previous.packets_sent:
            packet_diff_tx = max(0, current.packets_sent - previous.packets_sent)
            metrics.throughput_pps_tx = packet_diff_tx / period_seconds
            log.debug(f"TX packet rate: {packet_diff_tx} packets over {period_seconds}s = {metrics.throughput_pps_tx} pps")
            
        if current.packets_received and previous.packets_received:
            packet_diff_rx = max(0, current.packets_received - previous.packets_received)
            metrics.throughput_pps_rx = packet_diff_rx / period_seconds
            log.debug(f"RX packet rate: {packet_diff_rx} packets over {period_seconds}s = {metrics.throughput_pps_rx} pps")
        
        # Calculate bandwidth utilization percentage
        total_throughput_bps = metrics.throughput_bps_tx + metrics.throughput_bps_rx
        if self.max_bandwidth_bps > 0:
            metrics.bandwidth_utilization_percent = min(100.0, (total_throughput_bps / self.max_bandwidth_bps) * 100)
        
        log.debug(f"Total throughput: {total_throughput_bps} bps, utilization: {metrics.bandwidth_utilization_percent}%")
        
        return metrics
    
    def _calculate_quality_metrics(
        self,
        current: TunnelTelemetryData,
        previous: Optional[TunnelTelemetryData],
        metrics: TunnelUtilizationMetrics
    ) -> TunnelUtilizationMetrics:
        """Calculate connection quality metrics."""
        
        # Calculate uptime percentage
        if current.connection_time and current.connection_time > 0:
            # If we have connection time, tunnel has been up
            total_time = time.time() - (current.created_at or current.timestamp)
            if total_time > 0:
                metrics.uptime_percent = min(100.0, (current.connection_time / total_time) * 100)
        elif current.status == TunnelStatus.UP:
            metrics.uptime_percent = 100.0  # Currently up, assume good uptime
        
        # Calculate error rate (requires error counters from VPP stats)
        # This would be populated from the enhanced stats collection
        total_packets = (current.packets_sent or 0) + (current.packets_received or 0)
        if total_packets > 0:
            # Error rate calculation would use tx_errors + rx_errors from VPP stats
            # For now, assume low error rate if tunnel is up
            metrics.error_rate_percent = 0.1 if current.status == TunnelStatus.UP else 5.0
        
        # Calculate stability score based on status changes
        if previous and current.last_status_change and previous.last_status_change:
            time_since_last_change = current.timestamp - current.last_status_change
            # Higher score for longer periods without status changes
            # Convert to hours and cap at 100
            hours_stable = time_since_last_change / 3600
            metrics.stability_score = min(100.0, hours_stable * 10)  # 10 points per hour, max 100
        else:
            metrics.stability_score = 50.0  # Default moderate stability
        
        return metrics
    
    def _calculate_efficiency_metrics(
        self,
        current: TunnelTelemetryData,
        previous: Optional[TunnelTelemetryData],
        metrics: TunnelUtilizationMetrics
    ) -> TunnelUtilizationMetrics:
        """Calculate resource efficiency metrics."""
        
        # Calculate average packet sizes
        if metrics.throughput_pps_tx > 0 and metrics.throughput_bps_tx > 0:
            metrics.avg_packet_size_tx = metrics.throughput_bps_tx / metrics.throughput_pps_tx
        elif current.packets_sent and current.bytes_sent and current.packets_sent > 0:
            # Fallback: use absolute values if no throughput data available
            metrics.avg_packet_size_tx = current.bytes_sent / current.packets_sent
            
        if metrics.throughput_pps_rx > 0 and metrics.throughput_bps_rx > 0:
            metrics.avg_packet_size_rx = metrics.throughput_bps_rx / metrics.throughput_pps_rx
        elif current.packets_received and current.bytes_received and current.packets_received > 0:
            # Fallback: use absolute values if no throughput data available
            metrics.avg_packet_size_rx = current.bytes_received / current.packets_received
        
        # Connection duration in hours
        if current.connection_time:
            metrics.connection_duration_hours = current.connection_time / 3600
        
        return metrics
    
    def _calculate_composite_scores(self, metrics: TunnelUtilizationMetrics) -> TunnelUtilizationMetrics:
        """Calculate composite utilization scores."""
        
        # Weighted composite score
        # Bandwidth utilization: 40%
        # Uptime: 30% 
        # Stability: 20%
        # Error rate (inverted): 10%
        
        bandwidth_score = metrics.bandwidth_utilization_percent
        uptime_score = metrics.uptime_percent
        stability_score = metrics.stability_score
        error_score = max(0, 100 - metrics.error_rate_percent * 10)  # Invert error rate
        
        metrics.overall_utilization_score = (
            bandwidth_score * 0.4 +
            uptime_score * 0.3 +
            stability_score * 0.2 +
            error_score * 0.1
        )
        
        # Assign performance grade
        if metrics.overall_utilization_score >= 90:
            metrics.performance_grade = "A"
        elif metrics.overall_utilization_score >= 80:
            metrics.performance_grade = "B"
        elif metrics.overall_utilization_score >= 70:
            metrics.performance_grade = "C"
        elif metrics.overall_utilization_score >= 60:
            metrics.performance_grade = "D"
        else:
            metrics.performance_grade = "F"
        
        return metrics
    
    def _store_utilization_history(self, tunnel_id: str, metrics: TunnelUtilizationMetrics):
        """Store utilization metrics in history for trend analysis."""
        if tunnel_id not in self._utilization_history:
            self._utilization_history[tunnel_id] = []
        
        history = self._utilization_history[tunnel_id]
        history.append(metrics)
        
        # Keep only the most recent samples
        if len(history) > self._max_history_samples:
            history.pop(0)
    
    def get_utilization_trends(self, tunnel_id: str, sample_count: int = 10) -> Dict[str, Any]:
        """
        Get utilization trends for a tunnel.
        
        Args:
            tunnel_id: Tunnel identifier
            sample_count: Number of recent samples to analyze
            
        Returns:
            Dict containing trend analysis
        """
        if tunnel_id not in self._utilization_history:
            return {"error": "No utilization history found for tunnel"}
        
        history = self._utilization_history[tunnel_id]
        recent_samples = history[-sample_count:] if len(history) >= sample_count else history
        
        if not recent_samples:
            return {"error": "No utilization samples available"}
        
        # Calculate trends
        bandwidth_values = [s.bandwidth_utilization_percent for s in recent_samples]
        throughput_tx_values = [s.throughput_bps_tx for s in recent_samples]
        throughput_rx_values = [s.throughput_bps_rx for s in recent_samples]
        uptime_values = [s.uptime_percent for s in recent_samples]
        
        return {
            "sample_count": len(recent_samples),
            "time_range_hours": (recent_samples[-1].last_calculated - recent_samples[0].last_calculated) / 3600,
            "bandwidth_utilization": {
                "current": bandwidth_values[-1],
                "average": statistics.mean(bandwidth_values),
                "min": min(bandwidth_values),
                "max": max(bandwidth_values),
                "trend": "increasing" if bandwidth_values[-1] > bandwidth_values[0] else "decreasing"
            },
            "throughput_tx_bps": {
                "current": throughput_tx_values[-1],
                "average": statistics.mean(throughput_tx_values),
                "peak": max(throughput_tx_values)
            },
            "throughput_rx_bps": {
                "current": throughput_rx_values[-1],
                "average": statistics.mean(throughput_rx_values),
                "peak": max(throughput_rx_values)
            },
            "uptime_stability": {
                "average_uptime": statistics.mean(uptime_values),
                "consistency": min(uptime_values)  # Lowest uptime indicates consistency issues
            }
        }


class TunnelTelemetryCollector:
    """
    Collects and manages tunnel telemetry data with structured logging for Splunk ingestion.
    """
    
    def __init__(self, metrics_collection_interval: int = 30):
        """Initialize the tunnel telemetry collector.
        
        Args:
            metrics_collection_interval: Interval in seconds for metrics collection (default: 30)
        """
        self.device_serial = get_device_serial_number()
        self.device_hostname = get_device_short_hostname()
        
        # In-memory cache for tunnel state tracking
        self._tunnel_cache: Dict[str, TunnelTelemetryData] = {}
        self._cache_timeout = 3600  # 1 hour cache timeout
        
        # Store previous samples for rate calculations
        self._previous_samples: Dict[str, TunnelTelemetryData] = {}
        
        # Metrics collection configuration
        self.metrics_collection_interval = metrics_collection_interval
        self._metrics_collection_task = None
        self._metrics_collection_running = False
        
        # Configure structured logger for Splunk ingestion
        self._setup_tunnel_logger()
        
        # Initialize utilization calculator with realistic bandwidth limit
        # For low-traffic tunnels (monitoring, heartbeat), use 64 kbps baseline
        self._utilization_calculator = TunnelUtilizationCalculator(max_bandwidth_mbps=0.064)
        
        log.info(f"Tunnel telemetry collector initialized with {metrics_collection_interval}s metrics interval")
        log.info(f"Bandwidth utilization calculated against {self._utilization_calculator.max_bandwidth_mbps} Mbps baseline")
    
    def _setup_tunnel_logger(self):
        """Setup dedicated logger for tunnel telemetry with JSON formatting."""
        # Create a separate logger for tunnel telemetry
        tunnel_log_config = {
            "sink": "/var/log/vrouter-agent/tunnel-telemetry.log",
            "rotation": "50 MB",
            "retention": "90 days",  # Keep logs for 90 days
            "compression": None,  # No compression for Splunk compatibility
            "enqueue": True,
            "serialize": True,  # JSON format for Splunk
            "format": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name} | {message}",
            "level": "INFO",
            "backtrace": True,
            "diagnose": True,
        }
        
        # Add tunnel-specific logger
        log.add(**tunnel_log_config)
        
        # Create convenience method for tunnel logging
        self._tunnel_logger = log.bind(component="tunnel_telemetry")
    
    def record_tunnel_status(
        self, 
        tunnel_id: str,
        status: TunnelStatus,
        tunnel_data: Dict[str, Any],
        force_log: bool = False
    ) -> TunnelTelemetryData:
        """
        Record tunnel status and log structured data for Splunk ingestion.
        
        Args:
            tunnel_id: Unique tunnel identifier
            status: Current tunnel status
            tunnel_data: Additional tunnel data from VPP/system
            force_log: Force logging even if status hasn't changed
        
        Returns:
            TunnelTelemetryData: The recorded telemetry data
        """
        current_time = time.time()
        
        # Helper function to safely parse timestamps
        def safe_parse_timestamp(value, default=None):
            if value is None:
                return default
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                try:
                    # Try to parse ISO format timestamp
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    return dt.timestamp()
                except (ValueError, AttributeError):
                    # If parsing fails, return default
                    return default or current_time
            return default or current_time
        
        # Get previous state from cache
        previous_telemetry = self._tunnel_cache.get(tunnel_id)
        previous_status = previous_telemetry.status if previous_telemetry else None
        
        # Create new telemetry record
        telemetry = TunnelTelemetryData(
            tunnel_id=tunnel_id,
            tunnel_name=tunnel_data.get('name', tunnel_id),
            tunnel_type=TunnelType(tunnel_data.get('type', 'wireguard').lower()),
            status=status,
            previous_status=previous_status,
            timestamp=current_time,
            created_at=safe_parse_timestamp(tunnel_data.get('created_at'), current_time),
            last_status_change=current_time if status != previous_status else (
                previous_telemetry.last_status_change if previous_telemetry else current_time
            ),
            local_ip=tunnel_data.get('local_ip'),
            remote_ip=tunnel_data.get('remote_ip'),
            peer_endpoint=tunnel_data.get('peer_endpoint'),
            interface_index=tunnel_data.get('interface_index'),
            bytes_sent=tunnel_data.get('bytes_sent'),
            bytes_received=tunnel_data.get('bytes_received'),
            packets_sent=tunnel_data.get('packets_sent'),
            packets_received=tunnel_data.get('packets_received'),
            order_id=tunnel_data.get('order_id'),
            order_number=tunnel_data.get('order_number'),
            topology_id=tunnel_data.get('topology_id'),
            config_version=tunnel_data.get('config_version'),
            device_serial=self.device_serial,
            device_hostname=self.device_hostname
        )
        
        # Update last_seen_up for up status
        if status == TunnelStatus.UP:
            telemetry.last_seen_up = current_time
            if previous_telemetry and previous_telemetry.last_seen_up:
                telemetry.connection_time = current_time - previous_telemetry.last_seen_up
        elif previous_telemetry and previous_telemetry.last_seen_up:
            telemetry.last_seen_up = previous_telemetry.last_seen_up
        
        # Add custom tags from tunnel data
        custom_tags = tunnel_data.get('tags', [])
        if custom_tags:
            telemetry.add_tags(custom_tags)
        
        # Store previous sample before updating cache (create a copy to avoid reference issues)
        if tunnel_id in self._tunnel_cache:
            self._previous_samples[tunnel_id] = copy.deepcopy(self._tunnel_cache[tunnel_id])
        
        # Cache the telemetry data
        self._tunnel_cache[tunnel_id] = telemetry
        
        # Log to Splunk if status changed or forced
        if telemetry.is_status_change() or force_log:
            self._log_tunnel_telemetry(telemetry)
        
        return telemetry
    
    def _log_tunnel_telemetry(self, telemetry: TunnelTelemetryData):
        """Log tunnel telemetry data in structured JSON format for Splunk ingestion."""
        # Create structured log entry for Splunk
        log_data = {
            "event_type": "tunnel_status",
            "tunnel_id": telemetry.tunnel_id,
            "tunnel_name": telemetry.tunnel_name,
            "tunnel_type": telemetry.tunnel_type.value,
            "status": telemetry.status.value,
            "previous_status": telemetry.previous_status.value if telemetry.previous_status else None,
            "status_changed": telemetry.is_status_change(),
            "timestamp": telemetry.timestamp,
            "timestamp_iso": datetime.fromtimestamp(telemetry.timestamp).isoformat(),
            "created_at": telemetry.created_at,
            "last_seen_up": telemetry.last_seen_up,
            "last_status_change": telemetry.last_status_change,
            "connection_time_seconds": telemetry.connection_time,
            "network": {
                "local_ip": telemetry.local_ip,
                "remote_ip": telemetry.remote_ip,
                "peer_endpoint": telemetry.peer_endpoint,
                "interface_index": telemetry.interface_index
            },
            "metrics": {
                "bytes_sent": telemetry.bytes_sent,
                "bytes_received": telemetry.bytes_received,
                "packets_sent": telemetry.packets_sent,
                "packets_received": telemetry.packets_received
            },
            "context": {
                "order_id": telemetry.order_id,
                "order_number": telemetry.order_number,
                "topology_id": telemetry.topology_id,
                "config_version": telemetry.config_version
            },
            "device": {
                "serial": telemetry.device_serial,
                "hostname": telemetry.device_hostname
            },
            "tags": list(telemetry.tags)
        }
        
        # Log structured data for Splunk ingestion
        self._tunnel_logger.info(
            "Tunnel status event",
            **log_data  # Structured fields for Splunk
        )
        
        # Also log summary message for human readability
        status_msg = f"Tunnel {telemetry.tunnel_id} status: {telemetry.status.value}"
        if telemetry.is_status_change():
            status_msg += f" (was: {telemetry.previous_status.value})"
        
        log.info(status_msg, tunnel_id=telemetry.tunnel_id, status=telemetry.status.value)
    
    def get_tunnel_telemetry(self, tunnel_id: str) -> Optional[TunnelTelemetryData]:
        """Get cached tunnel telemetry data."""
        return self._tunnel_cache.get(tunnel_id)
    
    def get_all_tunnel_telemetry(self) -> List[TunnelTelemetryData]:
        """Get all cached tunnel telemetry data."""
        return list(self._tunnel_cache.values())
    
    def cleanup_cache(self):
        """Remove old entries from cache based on timeout."""
        current_time = time.time()
        expired_tunnels = []
        
        for tunnel_id, telemetry in self._tunnel_cache.items():
            if current_time - telemetry.timestamp > self._cache_timeout:
                expired_tunnels.append(tunnel_id)
        
        for tunnel_id in expired_tunnels:
            del self._tunnel_cache[tunnel_id]
        
        if expired_tunnels:
            log.debug(f"Cleaned up {len(expired_tunnels)} expired tunnel entries from cache")
    
    def query_by_tags(self, tags: List[str]) -> List[TunnelTelemetryData]:
        """Query tunnel telemetry by tags."""
        matching_tunnels = []
        tag_set = set(tags)
        
        for telemetry in self._tunnel_cache.values():
            if tag_set.issubset(telemetry.tags):
                matching_tunnels.append(telemetry)
        
        return matching_tunnels
    
    def query_by_status(self, status: TunnelStatus) -> List[TunnelTelemetryData]:
        """Query tunnel telemetry by status."""
        return [t for t in self._tunnel_cache.values() if t.status == status]
    
    def query_by_time_range(
        self, 
        start_time: float, 
        end_time: float,
        include_cache: bool = True
    ) -> List[TunnelTelemetryData]:
        """
        Query tunnel telemetry by time range.
        
        Note: This only queries the in-memory cache. For historical data,
        implement database storage or parse log files.
        """
        if not include_cache:
            return []  # Would need to implement log file parsing
        
        matching_tunnels = []
        for telemetry in self._tunnel_cache.values():
            if start_time <= telemetry.timestamp <= end_time:
                matching_tunnels.append(telemetry)
        
        return matching_tunnels
    
    def calculate_tunnel_utilization(self, tunnel_id: str) -> Optional[TunnelUtilizationMetrics]:
        """
        Calculate utilization metrics for a specific tunnel.
        
        Args:
            tunnel_id: Tunnel identifier
            
        Returns:
            TunnelUtilizationMetrics or None if tunnel not found
        """
        current_telemetry = self._tunnel_cache.get(tunnel_id)
        if not current_telemetry:
            return None
        
        # Get previous sample for rate calculations
        previous_telemetry = self._previous_samples.get(tunnel_id)
        
        log.debug(f"Calculating utilization for {tunnel_id}")
        log.debug(f"Current telemetry: {current_telemetry.bytes_sent if current_telemetry else None} bytes_sent")
        log.debug(f"Previous telemetry: {previous_telemetry.bytes_sent if previous_telemetry else 'None'} bytes_sent")
        
        return self._utilization_calculator.calculate_utilization(
            current_telemetry, 
            previous_telemetry, 
            self.metrics_collection_interval
        )
    
    def get_all_tunnel_utilization(self) -> Dict[str, TunnelUtilizationMetrics]:
        """
        Calculate utilization metrics for all cached tunnels.
        
        Returns:
            Dict mapping tunnel_id to utilization metrics
        """
        utilization_metrics = {}
        
        for tunnel_id in self._tunnel_cache.keys():
            metrics = self.calculate_tunnel_utilization(tunnel_id)
            if metrics:
                utilization_metrics[tunnel_id] = metrics
        
        return utilization_metrics
    
    def get_utilization_trends(self, tunnel_id: str, sample_count: int = 10) -> Dict[str, Any]:
        """
        Get utilization trends for a tunnel.
        
        Args:
            tunnel_id: Tunnel identifier
            sample_count: Number of recent samples to analyze
            
        Returns:
            Dict containing trend analysis
        """
        return self._utilization_calculator.get_utilization_trends(tunnel_id, sample_count)
    
    def get_utilization_summary(self) -> Dict[str, Any]:
        """
        Get a summary of utilization across all tunnels.
        
        Returns:
            Dict containing utilization summary statistics
        """
        all_utilization = self.get_all_tunnel_utilization()
        
        if not all_utilization:
            return {
                "total_tunnels": 0,
                "summary": "No tunnel utilization data available"
            }
        
        # Calculate summary statistics
        bandwidth_utilizations = [m.bandwidth_utilization_percent for m in all_utilization.values()]
        overall_scores = [m.overall_utilization_score for m in all_utilization.values()]
        uptimes = [m.uptime_percent for m in all_utilization.values()]
        
        # Count performance grades
        grade_counts = {}
        for metrics in all_utilization.values():
            grade = metrics.performance_grade
            grade_counts[grade] = grade_counts.get(grade, 0) + 1
        
        return {
            "total_tunnels": len(all_utilization),
            "bandwidth_utilization": {
                "average": statistics.mean(bandwidth_utilizations),
                "max": max(bandwidth_utilizations),
                "min": min(bandwidth_utilizations)
            },
            "overall_performance": {
                "average_score": statistics.mean(overall_scores),
                "best_score": max(overall_scores),
                "worst_score": min(overall_scores)
            },
            "uptime_stats": {
                "average_uptime": statistics.mean(uptimes),
                "best_uptime": max(uptimes),
                "worst_uptime": min(uptimes)
            },
            "performance_grades": grade_counts,
            "top_performers": [
                {"tunnel_id": tid, "score": metrics.overall_utilization_score, "grade": metrics.performance_grade}
                for tid, metrics in sorted(all_utilization.items(), 
                                         key=lambda x: x[1].overall_utilization_score, reverse=True)[:5]
            ],
            "underperformers": [
                {"tunnel_id": tid, "score": metrics.overall_utilization_score, "grade": metrics.performance_grade}
                for tid, metrics in sorted(all_utilization.items(), 
                                         key=lambda x: x[1].overall_utilization_score)[:5]
            ]
        }
    
    async def start_metrics_collection(self):
        """Start the periodic metrics collection task."""
        if self._metrics_collection_running:
            log.warning("Metrics collection is already running")
            return
            
        self._metrics_collection_running = True
        self._metrics_task = asyncio.create_task(self._metrics_collection_loop())
        log.info(f"Started tunnel metrics collection with {self.metrics_collection_interval}s interval")
        
    async def stop_metrics_collection(self):
        """Stop the periodic metrics collection task."""
        if not self._metrics_collection_running:
            log.warning("Metrics collection is not running")
            return
            
        self._metrics_collection_running = False
        if self._metrics_task:
            self._metrics_task.cancel()
            try:
                await self._metrics_task
            except asyncio.CancelledError:
                pass
            self._metrics_task = None
        log.info("Stopped tunnel metrics collection")
        
    def set_metrics_collection_interval(self, interval_seconds: int):
        """
        Update the metrics collection interval.
        
        Args:
            interval_seconds: New interval in seconds (1-3600)
            
        Raises:
            ValueError: If interval is out of valid range
        """
        if not 1 <= interval_seconds <= 3600:
            raise ValueError("Metrics collection interval must be between 1 and 3600 seconds")
            
        old_interval = self.metrics_collection_interval
        self.metrics_collection_interval = interval_seconds
        
        # If collection is running, restart with new interval
        if self._metrics_collection_running:
            log.info(f"Restarting metrics collection with new interval: {old_interval}s -> {interval_seconds}s")
            # Note: The collection loop will pick up the new interval on its next iteration
            # No need to restart the task, it checks the interval each loop
        else:
            log.info(f"Updated metrics collection interval: {old_interval}s -> {interval_seconds}s (not running)")
    
    async def _metrics_collection_loop(self):
        """Main metrics collection loop with immediate first collection."""
        # Run first collection immediately for API availability
        try:
            await self._collect_tunnel_metrics()
        except Exception as e:
            log.error(f"Error in initial metrics collection: {e}")
        
        # Then continue with interval-based collection
        while self._metrics_collection_running:
            try:
                await asyncio.sleep(self.metrics_collection_interval)
                if self._metrics_collection_running:  # Check again after sleep
                    await self._collect_tunnel_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error(f"Error in metrics collection loop: {e}")
                # Continue running even after errors
    
    async def _collect_tunnel_metrics(self):
        """Collect metrics for all active tunnels."""
        try:
            log.debug("Starting tunnel metrics collection...")
            
            # Create a temporary VRouterClient for metrics collection
            # This avoids issues with the main client being closed after tunnel operations
            from vrouter_agent.services.refactored_client import VRouterClient
            
            with VRouterClient([], None) as metrics_client:  # Empty config for metrics only
                if not metrics_client.is_connected():
                    log.warning("Could not establish VRouter connection for metrics collection")
                    return
                
                log.debug("Established VRouter connection for metrics collection")
                
                # Access the VPP client through the VRouter client
                vpp_client = metrics_client.connection.client
                
                # Get current tunnel interfaces from cache AND discover from VPP
                cached_active_tunnels = [t for t in self._tunnel_cache.values() if t.status == TunnelStatus.UP]
                
                # Also discover tunnels directly from VPP (WireGuard interfaces)
                discovered_tunnels = await self._discover_tunnels_from_vpp_with_client(vpp_client, metrics_client)
                
                # Combine cached and discovered tunnels
                all_tunnel_ids = set()
                if cached_active_tunnels:
                    all_tunnel_ids.update(t.tunnel_id for t in cached_active_tunnels)
                if discovered_tunnels:
                    all_tunnel_ids.update(discovered_tunnels.keys())
                
                if not all_tunnel_ids:
                    log.debug("No active tunnels found for metrics collection (cache + VPP discovery)")
                    return
                
                log.debug(f"Found {len(all_tunnel_ids)} tunnels for metrics collection: {list(all_tunnel_ids)}")
                
                # Create tunnel data structures for discovered tunnels if not in cache
                active_tunnels = list(cached_active_tunnels)
                for tunnel_id in discovered_tunnels:
                    if tunnel_id not in [t.tunnel_id for t in cached_active_tunnels]:
                        # Create a basic telemetry entry for discovered tunnel
                        tunnel_info = discovered_tunnels[tunnel_id]
                        basic_telemetry = TunnelTelemetryData(
                            tunnel_id=tunnel_id,
                            tunnel_name=tunnel_id,
                            tunnel_type=TunnelType.WIREGUARD,
                            status=TunnelStatus.UP if tunnel_info.get('up', False) else TunnelStatus.DOWN,
                            timestamp=time.time(),
                            interface_index=tunnel_info.get('interface_index'),
                            device_serial=self.device_serial,
                            device_hostname=self.device_hostname
                        )
                        active_tunnels.append(basic_telemetry)
                        # Add to cache so we track it going forward
                        self._tunnel_cache[tunnel_id] = basic_telemetry
                
                # Collect VPP interface statistics
                interface_stats = await self._get_vpp_interface_stats(vpp_client, active_tunnels)
                
                # Update telemetry data with metrics and log
                for tunnel in active_tunnels:
                    stats = interface_stats.get(tunnel.tunnel_id, {})
                    if stats:
                        # Store previous sample before updating (create a copy to avoid reference issues)
                        if tunnel.tunnel_id in self._tunnel_cache:
                            self._previous_samples[tunnel.tunnel_id] = copy.deepcopy(self._tunnel_cache[tunnel.tunnel_id])
                        
                        # Update cached telemetry with new metrics
                        tunnel.bytes_sent = stats.get('bytes_sent', tunnel.bytes_sent)
                        tunnel.bytes_received = stats.get('bytes_received', tunnel.bytes_received)
                        tunnel.packets_sent = stats.get('packets_sent', tunnel.packets_sent)
                        tunnel.packets_received = stats.get('packets_received', tunnel.packets_received)
                        tunnel.timestamp = time.time()
                        
                        # Update cache with new data
                        self._tunnel_cache[tunnel.tunnel_id] = tunnel
                        
                        # Log metrics update (separate from status changes)
                        self._log_tunnel_metrics(tunnel, stats)
                
                log.debug(f"Successfully collected metrics for {len(interface_stats)} tunnels")
            
        except Exception as e:
            log.error(f"Error collecting tunnel metrics: {e}")
            import traceback
            log.debug(f"Metrics collection traceback: {traceback.format_exc()}")
    
    async def _get_vpp_interface_stats(self, vpp_client, active_tunnels: List[TunnelTelemetryData]) -> Dict[str, Dict[str, Any]]:
        """Get VPP interface statistics for active tunnels."""
        interface_stats = {}
        
        try:
            # Get interface names to query
            log.debug("Querying VPP for interface statistics...")
            interface_names = [tunnel.tunnel_id for tunnel in active_tunnels]
            log.debug(f"Collecting stats for interfaces: {interface_names}")
            
            if not interface_names:
                log.debug("No interface names to query")
                return interface_stats
            
            # Create VPP stats query for specific interfaces
            query = models.VPPStatsQuery(
                interface_names=interface_names,
                include_error_counters=True,
                debug=False,  # Set to True for detailed debugging
            )
            
            # Query VPP for interface statistics
            reply = vpp_client.get_vpp_stats(query)
            
            if reply.success:
                log.debug(f"Successfully collected VPP stats for {len(interface_names)} interfaces")
                
                # Extract statistics for each interface
                for interface_name in interface_names:
                    counters = reply.summarize_interface(interface_name)
                    if counters:
                        # Map VPP counter names to our telemetry format
                        stats = {
                            'bytes_sent': counters.get('tx_bytes', counters.get('tx-bytes', 0)),
                            'bytes_received': counters.get('rx_bytes', counters.get('rx-bytes', 0)),
                            'packets_sent': counters.get('tx_packets', counters.get('tx-packets', 0)),
                            'packets_received': counters.get('rx_packets', counters.get('rx-packets', 0)),
                            'tx_errors': counters.get('tx_errors', counters.get('tx-errors', 0)),
                            'rx_errors': counters.get('rx_errors', counters.get('rx-errors', 0)),
                            'drops': counters.get('drops', 0),
                            'interface_up': True,  # If we got stats, interface is likely up
                            'mtu': counters.get('mtu', 0)
                        }
                        
                        interface_stats[interface_name] = stats
                        log.debug(f"Stats for {interface_name}: tx_bytes={stats['bytes_sent']}, rx_bytes={stats['bytes_received']}")
                    else:
                        log.debug(f"No counters found for interface {interface_name}")
                        # Create empty stats entry to indicate interface was queried but no data
                        interface_stats[interface_name] = {
                            'bytes_sent': 0,
                            'bytes_received': 0,
                            'packets_sent': 0,
                            'packets_received': 0,
                            'tx_errors': 0,
                            'rx_errors': 0,
                            'drops': 0,
                            'interface_up': False,
                            'mtu': 0
                        }
            else:
                log.error(f"Failed to collect VPP interface stats: {reply.error}")
                # Fall back to empty stats for all interfaces
                for interface_name in interface_names:
                    interface_stats[interface_name] = {
                        'bytes_sent': 0,
                        'bytes_received': 0,
                        'packets_sent': 0,
                        'packets_received': 0,
                        'tx_errors': 0,
                        'rx_errors': 0,
                        'drops': 0,
                        'interface_up': False,
                        'mtu': 0
                    }
            
        except Exception as e:
            log.error(f"Error getting VPP interface stats: {e}")
            import traceback
            log.debug(f"VPP stats error traceback: {traceback.format_exc()}")
        
        return interface_stats
    
    async def _discover_tunnels_from_vpp_with_client(self, vpp_client, vrouter_client) -> Dict[str, Dict[str, Any]]:
        """
        Discover active WireGuard and other tunnel interfaces from VPP configuration.
        
        Returns:
            Dict mapping tunnel_id to tunnel info
        """
        discovered_tunnels = {}
        
        try:
            log.debug("Starting tunnel discovery from VPP...")
            
            # Method 1: Use the VRouter client's method to get WireGuard interfaces  
            if hasattr(vrouter_client, 'get_wireguard_interfaces'):
                log.debug("Attempting to get WireGuard interfaces from VRouter client...")
                try:
                    wireguard_interfaces = vrouter_client.get_wireguard_interfaces()
                    log.debug(f"Got {len(wireguard_interfaces) if wireguard_interfaces else 0} WireGuard interfaces from VRouter client")
                    
                    for interface in wireguard_interfaces:
                        tunnel_id = interface.get('name', interface.get('interface_name'))
                        if tunnel_id:
                            discovered_tunnels[tunnel_id] = {
                                'interface_index': interface.get('index', interface.get('sw_if_index')),
                                'up': interface.get('enabled', True),
                                'name': tunnel_id,
                                'interface_type': 'wireguard',
                                'additional_attributes': {k: str(v) for k, v in interface.items() if k not in ['name', 'type', 'enabled', 'ip_addresses', 'mtu', 'link']}
                            }
                            log.debug(f"Added WireGuard interface: {tunnel_id}")
                            
                    log.debug(f"Discovered {len(discovered_tunnels)} WireGuard tunnels from VRouter client")
                except Exception as e:
                    log.warning(f"Error getting WireGuard interfaces from VRouter client: {e}")
            else:
                log.debug("VRouter client does not have get_wireguard_interfaces method")
            
            # Method 2: Fallback - discover from VPP configuration directly
            if not discovered_tunnels:
                log.debug("Attempting to discover tunnels from VPP configuration...")
                try:
                    current_config = vpp_client.get_configuration()
                    log.debug(f"Got VPP configuration with {len(current_config.items) if hasattr(current_config, 'items') else 0} items")
                    
                    for item in current_config.items:
                        item_name = getattr(item.config, 'name', 'unknown')
                        item_type = getattr(item.config, 'type', 'unknown')
                        
                        # Look for WireGuard interfaces
                        if (hasattr(item.config, 'name') and 
                            hasattr(item.config, 'type') and
                            'wireguard' in str(item.config.type).lower()):
                            
                            tunnel_id = item.config.name
                            discovered_tunnels[tunnel_id] = {
                                'interface_index': getattr(item.config, 'index', None),
                                'up': getattr(item.config, 'enabled', True),
                                'name': tunnel_id,
                                'interface_type': 'wireguard'
                            }
                            log.debug(f"Added WireGuard interface from config: {tunnel_id}")
                        # Also look for tunnel-like interface names
                        elif (hasattr(item.config, 'name') and 
                              (item.config.name.startswith('wg') or 
                               item.config.name.startswith('tun') or
                               'tunnel' in item.config.name.lower())):
                            
                            tunnel_id = item.config.name
                            # Determine tunnel type from name
                            tunnel_type = 'wireguard' if item.config.name.startswith('wg') else 'gre'
                            
                            discovered_tunnels[tunnel_id] = {
                                'interface_index': getattr(item.config, 'index', None),
                                'up': getattr(item.config, 'enabled', True),
                                'name': tunnel_id,
                                'interface_type': tunnel_type
                            }
                            log.debug(f"Added tunnel-like interface from config: {tunnel_id} (type: {tunnel_type})")
                    
                    log.debug(f"Discovered {len(discovered_tunnels)} tunnels from VPP config")
                except Exception as e:
                    log.warning(f"Error discovering tunnels from VPP config: {e}")
            
            # Method 3: Try to get interface list and filter for tunnel interfaces
            if not discovered_tunnels:
                log.debug("Attempting to discover tunnels from interface list...")
                try:
                    # Use VPP stats to get all interfaces and filter for tunnel-like names
                    query = models.VPPStatsQuery(
                        patterns=["/if/names"],
                        include_error_counters=False,
                        debug=False,
                    )
                    
                    reply = vpp_client.get_vpp_stats(query)
                    if reply.success:
                        log.debug(f"Got {len(reply.entries)} interface entries from VPP stats")
                        
                        # Look through interface names for tunnel-like interfaces
                        for entry in reply.entries:
                            if hasattr(entry, 'name') and hasattr(entry, 'value'):
                                interface_names = entry.value
                                if isinstance(interface_names, (list, tuple)):
                                    for idx, name in enumerate(interface_names):
                                        if (name and isinstance(name, str) and 
                                            (name.startswith('wg') or 
                                             name.startswith('tun') or
                                             'tunnel' in name.lower())):
                                            
                                            tunnel_type = 'wireguard' if name.startswith('wg') else 'gre'
                                            discovered_tunnels[name] = {
                                                'interface_index': idx,
                                                'up': True,  # Assume up if in interface list
                                                'name': name,
                                                'interface_type': tunnel_type
                                            }
                                            log.debug(f"Added interface from stats: {name} (type: {tunnel_type})")
                    else:
                        log.debug(f"Failed to get interface names from VPP stats: {reply.error}")
                except Exception as e:
                    log.warning(f"Error discovering tunnels from interface list: {e}")
            
            total_discovered = len(discovered_tunnels)
            if total_discovered > 0:
                log.debug(f"Successfully discovered {total_discovered} tunnel interfaces: {list(discovered_tunnels.keys())}")
            else:
                log.debug("No tunnel interfaces discovered from VPP")
                
        except Exception as e:
            log.warning(f"Error discovering tunnels from VPP: {e}")
            import traceback
            log.debug(f"Tunnel discovery error traceback: {traceback.format_exc()}")
        
        return discovered_tunnels
    
    def _log_tunnel_metrics(self, telemetry: TunnelTelemetryData, stats: Dict[str, Any]):
        """Log tunnel metrics data in structured JSON format for Splunk ingestion."""
        
        # Calculate utilization metrics for this tunnel
        utilization_metrics = self.calculate_tunnel_utilization(telemetry.tunnel_id)
        
        # Create structured log entry for metrics (separate from status events)
        log_data = {
            "event_type": "tunnel_metrics",
            "tunnel_id": telemetry.tunnel_id,
            "tunnel_name": telemetry.tunnel_name,
            "tunnel_type": telemetry.tunnel_type.value,
            "status": telemetry.status.value,
            "timestamp": telemetry.timestamp,
            "timestamp_iso": datetime.fromtimestamp(telemetry.timestamp).isoformat(),
            "network": {
                "local_ip": telemetry.local_ip,
                "remote_ip": telemetry.remote_ip,
                "peer_endpoint": telemetry.peer_endpoint,
                "interface_index": telemetry.interface_index,
                "interface_up": stats.get('interface_up', False),
                "mtu": stats.get('mtu', 0)
            },
            "metrics": {
                "bytes_sent": telemetry.bytes_sent,
                "bytes_received": telemetry.bytes_received,
                "packets_sent": telemetry.packets_sent,
                "packets_received": telemetry.packets_received,
                "tx_errors": stats.get('tx_errors', 0),
                "rx_errors": stats.get('rx_errors', 0),
                "drops": stats.get('drops', 0),
                "collection_interval_seconds": self.metrics_collection_interval
            },
            "utilization": {
                "bandwidth_utilization_percent": utilization_metrics.bandwidth_utilization_percent if utilization_metrics else 0.0,
                "throughput_bps_tx": utilization_metrics.throughput_bps_tx if utilization_metrics else 0.0,
                "throughput_bps_rx": utilization_metrics.throughput_bps_rx if utilization_metrics else 0.0,
                "throughput_pps_tx": utilization_metrics.throughput_pps_tx if utilization_metrics else 0.0,
                "throughput_pps_rx": utilization_metrics.throughput_pps_rx if utilization_metrics else 0.0,
                "uptime_percent": utilization_metrics.uptime_percent if utilization_metrics else 0.0,
                "error_rate_percent": utilization_metrics.error_rate_percent if utilization_metrics else 0.0,
                "stability_score": utilization_metrics.stability_score if utilization_metrics else 0.0,
                "avg_packet_size_tx": utilization_metrics.avg_packet_size_tx if utilization_metrics else 0.0,
                "avg_packet_size_rx": utilization_metrics.avg_packet_size_rx if utilization_metrics else 0.0,
                "connection_duration_hours": utilization_metrics.connection_duration_hours if utilization_metrics else 0.0,
                "overall_utilization_score": utilization_metrics.overall_utilization_score if utilization_metrics else 0.0,
                "performance_grade": utilization_metrics.performance_grade if utilization_metrics else "N/A",
                "measurement_period_seconds": utilization_metrics.measurement_period_seconds if utilization_metrics else self.metrics_collection_interval
            },
            "context": {
                "order_id": telemetry.order_id,
                "order_number": telemetry.order_number,
                "topology_id": telemetry.topology_id,
                "config_version": telemetry.config_version
            },
            "device": {
                "serial": telemetry.device_serial,
                "hostname": telemetry.device_hostname
            },
            "tags": list(telemetry.tags)
        }
        
        # Log structured metrics data for Splunk ingestion
        self._tunnel_logger.info(
            "Tunnel metrics and utilization update",
            **log_data
        )
    
    def set_metrics_collection_interval(self, interval_seconds: int):
        """Update the metrics collection interval."""
        if interval_seconds < 1:
            raise ValueError("Metrics collection interval must be at least 1 second")
        
        old_interval = self.metrics_collection_interval
        self.metrics_collection_interval = interval_seconds
        
        log.info(f"Updated metrics collection interval from {old_interval}s to {interval_seconds}s")
        
        # If collection is running, restart with new interval
        if self._metrics_collection_running:
            log.info("Restarting metrics collection with new interval")
            # Note: The loop will pick up the new interval on next iteration
    
    def set_bandwidth_baseline(self, max_bandwidth_mbps: float):
        """
        Update the maximum bandwidth baseline for utilization calculations.
        
        Args:
            max_bandwidth_mbps: Maximum bandwidth in Mbps (e.g., 1.0 for 1 Mbps)
            
        Examples:
            collector.set_bandwidth_baseline(0.064)  # 64 kbps for low-traffic tunnels
            collector.set_bandwidth_baseline(1.0)    # 1 Mbps for moderate usage
            collector.set_bandwidth_baseline(100.0)  # 100 Mbps for high-bandwidth scenarios
        """
        if max_bandwidth_mbps <= 0:
            raise ValueError("Bandwidth baseline must be greater than 0")
            
        old_bandwidth = self._utilization_calculator.max_bandwidth_mbps
        self._utilization_calculator.max_bandwidth_mbps = max_bandwidth_mbps
        self._utilization_calculator.max_bandwidth_bps = max_bandwidth_mbps * 1_000_000 / 8
        
        log.info(f"Updated bandwidth utilization baseline: {old_bandwidth} Mbps -> {max_bandwidth_mbps} Mbps")


# Global instance for use throughout the application (will be initialized with VRouter client)
tunnel_telemetry_collector = None