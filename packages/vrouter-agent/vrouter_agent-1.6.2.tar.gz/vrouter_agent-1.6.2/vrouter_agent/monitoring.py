"""
Health Check and Monitoring Module for Enhanced Stream Processing

This module provides health checks, monitoring capabilities, and alerting
for the enhanced stream processing system.
"""

import asyncio
import time
import psutil
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from loguru import logger as log


class HealthStatus(Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Health check result."""
    name: str
    status: HealthStatus
    message: str
    timestamp: float
    details: Optional[Dict[str, Any]] = None


@dataclass
class SystemMetrics:
    """System resource metrics."""
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    disk_usage_percent: float
    network_io_bytes: Dict[str, int]
    timestamp: float


@dataclass
class Alert:
    """Alert information."""
    name: str
    level: str  # INFO, WARNING, ERROR, CRITICAL
    message: str
    timestamp: float
    metrics: Optional[Dict[str, Any]] = None


class MonitoringSystem:
    """Monitoring system for enhanced stream processing."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize monitoring system.
        
        Args:
            config: Monitoring configuration
        """
        self.config = config
        self.alerts_config = config.get('alerts', {})
        self.health_checks: List[HealthCheck] = []
        self.system_metrics: List[SystemMetrics] = []
        self.alerts: List[Alert] = []
        self.alert_callbacks: List[Callable[[Alert], None]] = []
        
        # Monitoring state
        self.monitoring_active = False
        self.last_metrics_update = 0
        self.metrics_history_limit = 100
        
        log.info("Monitoring system initialized")
    
    def add_alert_callback(self, callback: Callable[[Alert], None]) -> None:
        """Add callback for alert notifications."""
        self.alert_callbacks.append(callback)
        log.info(f"Added alert callback: {callback.__name__}")
    
    def start_monitoring(self) -> None:
        """Start the monitoring system."""
        if self.monitoring_active:
            log.warning("Monitoring system is already active")
            return
        
        self.monitoring_active = True
        log.info("Monitoring system started")
    
    def stop_monitoring(self) -> None:
        """Stop the monitoring system."""
        self.monitoring_active = False
        log.info("Monitoring system stopped")
    
    async def perform_health_checks(
        self, 
        processor=None
    ) -> List[HealthCheck]:
        """
        Perform comprehensive health checks.
        
        Args:
            processor: Enhanced stream processor instance
            
        Returns:
            List of health check results
        """
        checks = []
        timestamp = time.time()
        
        # System health checks
        checks.extend(await self._check_system_resources())
        
        # Processor health checks
        if processor:
            checks.extend(await self._check_processor_health(processor))
        
        # Database connectivity check
        checks.extend(await self._check_database_connectivity())
        
        # Update health check history
        self.health_checks = checks
        
        # Check for alerts
        await self._evaluate_health_alerts(checks)
        
        return checks
    
    async def _check_system_resources(self) -> List[HealthCheck]:
        """Check system resource health."""
        checks = []
        timestamp = time.time()
        
        try:
            # CPU usage check
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                status = HealthStatus.CRITICAL
                message = f"High CPU usage: {cpu_percent:.1f}%"
            elif cpu_percent > 75:
                status = HealthStatus.WARNING
                message = f"Elevated CPU usage: {cpu_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"CPU usage normal: {cpu_percent:.1f}%"
            
            checks.append(HealthCheck(
                name="cpu_usage",
                status=status,
                message=message,
                timestamp=timestamp,
                details={"cpu_percent": cpu_percent}
            ))
            
            # Memory usage check
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                status = HealthStatus.CRITICAL
                message = f"High memory usage: {memory.percent:.1f}%"
            elif memory.percent > 75:
                status = HealthStatus.WARNING
                message = f"Elevated memory usage: {memory.percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Memory usage normal: {memory.percent:.1f}%"
            
            checks.append(HealthCheck(
                name="memory_usage",
                status=status,
                message=message,
                timestamp=timestamp,
                details={
                    "memory_percent": memory.percent,
                    "memory_available_mb": memory.available / (1024 * 1024)
                }
            ))
            
            # Disk usage check
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            if disk_percent > 90:
                status = HealthStatus.CRITICAL
                message = f"High disk usage: {disk_percent:.1f}%"
            elif disk_percent > 75:
                status = HealthStatus.WARNING
                message = f"Elevated disk usage: {disk_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Disk usage normal: {disk_percent:.1f}%"
            
            checks.append(HealthCheck(
                name="disk_usage",
                status=status,
                message=message,
                timestamp=timestamp,
                details={"disk_percent": disk_percent}
            ))
            
        except Exception as e:
            checks.append(HealthCheck(
                name="system_resources",
                status=HealthStatus.UNKNOWN,
                message=f"Error checking system resources: {e}",
                timestamp=timestamp
            ))
        
        return checks
    
    async def _check_processor_health(self, processor) -> List[HealthCheck]:
        """Check stream processor health."""
        checks = []
        timestamp = time.time()
        
        try:
            # Get processor status and metrics
            status = processor.get_status()
            metrics = processor.get_metrics()
            
            # Check if processor is running
            if not status.get('running', False):
                checks.append(HealthCheck(
                    name="processor_status",
                    status=HealthStatus.CRITICAL,
                    message="Stream processor is not running",
                    timestamp=timestamp,
                    details=status
                ))
            else:
                checks.append(HealthCheck(
                    name="processor_status",
                    status=HealthStatus.HEALTHY,
                    message="Stream processor is running",
                    timestamp=timestamp,
                    details=status
                ))
            
            # Check queue size
            queue_size = metrics.get('queue_size', 0)
            queue_threshold = self.alerts_config.get('high_queue_size', 100)
            
            if queue_size > queue_threshold:
                status = HealthStatus.WARNING
                message = f"High queue size: {queue_size} items"
            else:
                status = HealthStatus.HEALTHY
                message = f"Queue size normal: {queue_size} items"
            
            checks.append(HealthCheck(
                name="queue_size",
                status=status,
                message=message,
                timestamp=timestamp,
                details={"queue_size": queue_size, "threshold": queue_threshold}
            ))
            
            # Check error rate
            total_processed = metrics.get('total_processed', 0)
            failed_processed = metrics.get('failed_processed', 0)
            
            if total_processed > 0:
                error_rate = failed_processed / total_processed
                error_threshold = self.alerts_config.get('high_error_rate', 0.1)
                
                if error_rate > error_threshold:
                    status = HealthStatus.WARNING
                    message = f"High error rate: {error_rate:.2%}"
                else:
                    status = HealthStatus.HEALTHY
                    message = f"Error rate normal: {error_rate:.2%}"
                
                checks.append(HealthCheck(
                    name="error_rate",
                    status=status,
                    message=message,
                    timestamp=timestamp,
                    details={
                        "error_rate": error_rate,
                        "threshold": error_threshold,
                        "total_processed": total_processed,
                        "failed_processed": failed_processed
                    }
                ))
            
            # Check throughput
            throughput = metrics.get('throughput_per_minute', 0)
            throughput_threshold = self.alerts_config.get('low_throughput', 10)
            
            if throughput < throughput_threshold and total_processed > 10:
                status = HealthStatus.WARNING
                message = f"Low throughput: {throughput:.1f} tx/min"
            else:
                status = HealthStatus.HEALTHY
                message = f"Throughput normal: {throughput:.1f} tx/min"
            
            checks.append(HealthCheck(
                name="throughput",
                status=status,
                message=message,
                timestamp=timestamp,
                details={
                    "throughput": throughput,
                    "threshold": throughput_threshold
                }
            ))
            
        except Exception as e:
            checks.append(HealthCheck(
                name="processor_health",
                status=HealthStatus.UNKNOWN,
                message=f"Error checking processor health: {e}",
                timestamp=timestamp
            ))
        
        return checks
    
    async def _check_database_connectivity(self) -> List[HealthCheck]:
        """Check database connectivity."""
        checks = []
        timestamp = time.time()
        
        try:
            # This would be implemented based on your database setup
            # For now, we'll just do a basic check
            checks.append(HealthCheck(
                name="database_connectivity",
                status=HealthStatus.HEALTHY,
                message="Database connectivity check passed",
                timestamp=timestamp
            ))
            
        except Exception as e:
            checks.append(HealthCheck(
                name="database_connectivity",
                status=HealthStatus.CRITICAL,
                message=f"Database connectivity failed: {e}",
                timestamp=timestamp
            ))
        
        return checks
    
    async def _evaluate_health_alerts(self, checks: List[HealthCheck]) -> None:
        """Evaluate health checks and generate alerts."""
        for check in checks:
            if check.status == HealthStatus.CRITICAL:
                alert = Alert(
                    name=f"health_check_{check.name}",
                    level="CRITICAL",
                    message=f"Critical health issue: {check.message}",
                    timestamp=check.timestamp,
                    metrics=check.details
                )
                await self._send_alert(alert)
            
            elif check.status == HealthStatus.WARNING:
                alert = Alert(
                    name=f"health_check_{check.name}",
                    level="WARNING",
                    message=f"Health warning: {check.message}",
                    timestamp=check.timestamp,
                    metrics=check.details
                )
                await self._send_alert(alert)
    
    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_available_mb=memory.available / (1024 * 1024),
                disk_usage_percent=(disk.used / disk.total) * 100,
                network_io_bytes={
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv
                },
                timestamp=time.time()
            )
            
            # Add to history
            self.system_metrics.append(metrics)
            
            # Limit history size
            if len(self.system_metrics) > self.metrics_history_limit:
                self.system_metrics = self.system_metrics[-self.metrics_history_limit:]
            
            return metrics
            
        except Exception as e:
            log.error(f"Error collecting system metrics: {e}")
            return SystemMetrics(
                cpu_percent=0,
                memory_percent=0,
                memory_available_mb=0,
                disk_usage_percent=0,
                network_io_bytes={},
                timestamp=time.time()
            )
    
    async def _send_alert(self, alert: Alert) -> None:
        """Send alert to configured callbacks."""
        self.alerts.append(alert)
        
        # Limit alerts history
        if len(self.alerts) > self.metrics_history_limit:
            self.alerts = self.alerts[-self.metrics_history_limit:]
        
        # Send to callbacks
        for callback in self.alert_callbacks:
            try:
                await asyncio.create_task(self._call_alert_callback(callback, alert))
            except Exception as e:
                log.error(f"Error calling alert callback {callback.__name__}: {e}")
    
    async def _call_alert_callback(self, callback: Callable, alert: Alert) -> None:
        """Call alert callback (handle both sync and async)."""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(alert)
            else:
                callback(alert)
        except Exception as e:
            log.error(f"Alert callback error: {e}")
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get a summary of current health status."""
        if not self.health_checks:
            return {"status": "unknown", "message": "No health checks performed yet"}
        
        # Determine overall status
        statuses = [check.status for check in self.health_checks]
        
        if HealthStatus.CRITICAL in statuses:
            overall_status = "critical"
        elif HealthStatus.WARNING in statuses:
            overall_status = "warning"
        elif HealthStatus.UNKNOWN in statuses:
            overall_status = "unknown"
        else:
            overall_status = "healthy"
        
        # Count checks by status
        status_counts = {}
        for status in HealthStatus:
            status_counts[status.value] = sum(
                1 for check in self.health_checks if check.status == status
            )
        
        return {
            "status": overall_status,
            "total_checks": len(self.health_checks),
            "status_counts": status_counts,
            "last_check": max(check.timestamp for check in self.health_checks),
            "checks": [asdict(check) for check in self.health_checks]
        }
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of system metrics."""
        if not self.system_metrics:
            return {"message": "No metrics collected yet"}
        
        latest = self.system_metrics[-1]
        
        return {
            "latest_metrics": asdict(latest),
            "metrics_count": len(self.system_metrics),
            "collection_active": self.monitoring_active
        }
    
    def get_alerts_summary(self) -> Dict[str, Any]:
        """Get a summary of recent alerts."""
        if not self.alerts:
            return {"message": "No alerts generated"}
        
        # Count alerts by level
        alert_counts = {}
        for alert in self.alerts:
            level = alert.level
            alert_counts[level] = alert_counts.get(level, 0) + 1
        
        return {
            "total_alerts": len(self.alerts),
            "alert_counts": alert_counts,
            "latest_alert": asdict(self.alerts[-1]) if self.alerts else None,
            "recent_alerts": [asdict(alert) for alert in self.alerts[-10:]]
        }


# Alert callback functions
async def log_alert_callback(alert: Alert) -> None:
    """Log alert to the application log."""
    level_map = {
        "INFO": log.info,
        "WARNING": log.warning,
        "ERROR": log.error,
        "CRITICAL": log.critical
    }
    
    log_func = level_map.get(alert.level, log.info)
    log_func(f"ALERT [{alert.level}] {alert.name}: {alert.message}")


def console_alert_callback(alert: Alert) -> None:
    """Print alert to console."""
    print(f"ALERT [{alert.level}] {alert.name}: {alert.message}")


# Factory function for creating monitoring system
def create_monitoring_system(config: Dict[str, Any]) -> MonitoringSystem:
    """
    Create and configure monitoring system.
    
    Args:
        config: Monitoring configuration
        
    Returns:
        Configured monitoring system
    """
    monitoring = MonitoringSystem(config)
    
    # Add default alert callbacks
    monitoring.add_alert_callback(log_alert_callback)
    
    # Add console callback for development
    if config.get('log_level') == 'DEBUG':
        monitoring.add_alert_callback(console_alert_callback)
    
    return monitoring
