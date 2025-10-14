"""
Shared utilities for SothemaAI microservices.

This package contains common utilities that can be shared across
all microservices in the SothemaAI platform.
"""

__version__ = "1.0.0"

from .logging_utils import get_logger, generate_correlation_id, generate_request_id
from .logging_config import setup_service_logging, get_service_logger
from .monitoring import get_service_monitor, get_alert_manager, health_check_scheduler
from .middleware.logging_middleware import LoggingMiddleware

__all__ = [
    'get_logger',
    'generate_correlation_id',
    'generate_request_id',
    'setup_service_logging',
    'get_service_logger',
    'get_service_monitor',
    'get_alert_manager',
    'health_check_scheduler',
    'LoggingMiddleware'
]