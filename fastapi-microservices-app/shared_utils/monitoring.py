"""
Monitoring and Alerting Utilities for SothemaAI

This module provides monitoring capabilities, health checks, and alerting
integration for the SothemaAI microservices platform.
"""

import time
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False

from .logging_utils import get_logger


class ServiceMonitor:
    """Monitor service health and performance metrics."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = get_logger(service_name)
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.last_health_check = datetime.utcnow()
        self.metrics_history: List[Dict[str, Any]] = []

    def record_request(self, method: str, endpoint: str, status_code: int, duration_ms: float):
        """Record a request for monitoring."""
        self.request_count += 1
        if status_code >= 400:
            self.error_count += 1

        # Log performance metrics for slow requests
        if duration_ms > 1000:  # Log requests taking more than 1 second
            self.logger.warning(
                f"Slow request detected: {method} {endpoint}",
                extra_fields={
                    "duration_ms": duration_ms,
                    "status_code": status_code,
                    "performance_issue": "slow_request"
                }
            )

    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        now = datetime.utcnow()
        uptime_seconds = time.time() - self.start_time

        # System metrics
        system_metrics = self._get_system_metrics()

        # Service metrics
        service_metrics = {
            "service_name": self.service_name,
            "uptime_seconds": uptime_seconds,
            "total_requests": self.request_count,
            "error_count": self.error_count,
            "error_rate": (self.error_count / max(self.request_count, 1)) * 100,
            "last_health_check": self.last_health_check.isoformat() + "Z",
            "status": "healthy" if self._is_healthy() else "unhealthy"
        }

        health_status = {
            "timestamp": now.isoformat() + "Z",
            "service": service_metrics,
            "system": system_metrics
        }

        self.last_health_check = now
        return health_status

    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get system-level metrics."""
        if not PSUTIL_AVAILABLE:
            return {"error": "psutil not available - system metrics disabled"}

        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),  # type: ignore
                "memory_percent": psutil.virtual_memory().percent,  # type: ignore
                "memory_used_mb": psutil.virtual_memory().used / 1024 / 1024,  # type: ignore
                "memory_available_mb": psutil.virtual_memory().available / 1024 / 1024,  # type: ignore
                "disk_usage_percent": psutil.disk_usage('/').percent,  # type: ignore
                "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None  # type: ignore
            }
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")
            return {"error": "Failed to collect system metrics"}

    def _is_healthy(self) -> bool:
        """Determine if the service is healthy."""
        # Basic health checks
        error_rate_threshold = 5.0  # 5% error rate threshold
        current_error_rate = (self.error_count / max(self.request_count, 1)) * 100

        # Memory usage threshold (90%)
        memory_threshold = 90.0

        system_metrics = self._get_system_metrics()
        memory_usage = system_metrics.get("memory_percent", 0)

        return (
            current_error_rate < error_rate_threshold and
            memory_usage < memory_threshold
        )

    def log_health_status(self):
        """Log current health status."""
        health_status = self.get_health_status()
        status = health_status["service"]["status"]

        if status == "healthy":
            self.logger.info(
                "Health check passed",
                extra_fields={
                    "health_status": health_status,
                    "monitoring": True
                }
            )
        else:
            self.logger.warning(
                "Health check failed",
                extra_fields={
                    "health_status": health_status,
                    "monitoring": True,
                    "alert": True
                }
            )


class AlertManager:
    """Manage alerts and notifications."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = get_logger(service_name)
        self.active_alerts: Dict[str, Dict[str, Any]] = {}
        self.alert_history: List[Dict[str, Any]] = []

    def raise_alert(
        self,
        alert_type: str,
        message: str,
        severity: str = "warning",
        details: Optional[Dict[str, Any]] = None
    ):
        """Raise a new alert."""
        if alert_type in self.active_alerts:
            # Update existing alert
            self.active_alerts[alert_type]["last_updated"] = datetime.utcnow().isoformat() + "Z"
            self.active_alerts[alert_type]["occurrences"] += 1
        else:
            # Create new alert
            alert = {
                "alert_id": f"{self.service_name}_{alert_type}_{int(time.time())}",
                "service": self.service_name,
                "type": alert_type,
                "message": message,
                "severity": severity,
                "created_at": datetime.utcnow().isoformat() + "Z",
                "last_updated": datetime.utcnow().isoformat() + "Z",
                "occurrences": 1,
                "status": "active",
                "details": details or {}
            }
            self.active_alerts[alert_type] = alert
            self.alert_history.append(alert)

        # Log the alert
        self.logger.error(
            f"Alert raised: {alert_type} - {message}",
            extra_fields={
                "alert_type": alert_type,
                "alert_severity": severity,
                "alert_details": details,
                "alerting": True
            }
        )

    def resolve_alert(self, alert_type: str, resolution_note: Optional[str] = None):
        """Resolve an active alert."""
        if alert_type in self.active_alerts:
            alert = self.active_alerts[alert_type]
            alert["status"] = "resolved"
            alert["resolved_at"] = datetime.utcnow().isoformat() + "Z"
            alert["resolution_note"] = resolution_note

            # Log resolution
            self.logger.info(
                f"Alert resolved: {alert_type}",
                extra_fields={
                    "alert_type": alert_type,
                    "resolution_note": resolution_note,
                    "alerting": True
                }
            )

            # Move to history and remove from active
            self.alert_history.append(alert)
            del self.active_alerts[alert_type]

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts."""
        return list(self.active_alerts.values())

    def get_alert_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get alert history for the specified time period."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [
            alert for alert in self.alert_history
            if datetime.fromisoformat(alert["created_at"].replace("Z", "+00:00")) > cutoff_time
        ]


# Global instances
_service_monitors: Dict[str, ServiceMonitor] = {}
_alert_managers: Dict[str, AlertManager] = {}


def get_service_monitor(service_name: str) -> ServiceMonitor:
    """Get or create a service monitor."""
    if service_name not in _service_monitors:
        _service_monitors[service_name] = ServiceMonitor(service_name)
    return _service_monitors[service_name]


def get_alert_manager(service_name: str) -> AlertManager:
    """Get or create an alert manager."""
    if service_name not in _alert_managers:
        _alert_managers[service_name] = AlertManager(service_name)
    return _alert_managers[service_name]


async def health_check_scheduler(service_name: str, interval_seconds: int = 300):
    """
    Run periodic health checks.

    Args:
        service_name: Name of the service
        interval_seconds: Interval between health checks (default: 5 minutes)
    """
    monitor = get_service_monitor(service_name)

    while True:
        try:
            monitor.log_health_status()

            # Check for critical conditions and raise alerts
            health_status = monitor.get_health_status()
            error_rate = health_status["service"]["error_rate"]
            memory_usage = health_status["system"].get("memory_percent", 0)

            alert_manager = get_alert_manager(service_name)

            if error_rate > 10:  # High error rate alert
                alert_manager.raise_alert(
                    "high_error_rate",
                    f"Error rate is {error_rate:.2f}%",
                    severity="error",
                    details={"error_rate": error_rate}
                )
            elif error_rate < 5:  # Auto-resolve if error rate drops
                alert_manager.resolve_alert("high_error_rate", "Error rate normalized")

            if memory_usage > 95:  # Critical memory usage
                alert_manager.raise_alert(
                    "high_memory_usage",
                    f"Memory usage is {memory_usage:.2f}%",
                    severity="critical",
                    details={"memory_percent": memory_usage}
                )
            elif memory_usage < 90:  # Auto-resolve if memory drops
                alert_manager.resolve_alert("high_memory_usage", "Memory usage normalized")

        except Exception as e:
            monitor.logger.error(f"Health check failed: {e}")

        await asyncio.sleep(interval_seconds)