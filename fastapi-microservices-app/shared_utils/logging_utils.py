"""
Enhanced Logging System for SothemaAI Microservices

This module provides structured, production-ready logging capabilities
with JSON formatting, correlation IDs, and monitoring integration.
"""

import json
import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import uuid


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        # Create the base log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": getattr(record, 'service', 'unknown'),
            "correlation_id": getattr(record, 'correlation_id', None),
            "request_id": getattr(record, 'request_id', None),
            "user_id": getattr(record, 'user_id', None),
            "endpoint": getattr(record, 'endpoint', None),
            "method": getattr(record, 'method', None),
            "status_code": getattr(record, 'status_code', None),
            "duration_ms": getattr(record, 'duration_ms', None),
            "ip_address": getattr(record, 'ip_address', None),
            "user_agent": getattr(record, 'user_agent', None),
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, 'extra_fields'):
            log_entry.update(getattr(record, 'extra_fields', {}))

        # Remove None values
        log_entry = {k: v for k, v in log_entry.items() if v is not None}

        return json.dumps(log_entry, default=str)


class SothemaLogger:
    """Enhanced logger for SothemaAI services."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)
        self._configured = False

    def configure(
        self,
        level: str = "INFO",
        log_to_file: bool = True,
        log_to_console: bool = True,
        log_file: Optional[str] = None,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        json_format: bool = True
    ) -> None:
        """Configure the logger with production-ready settings."""

        if self._configured:
            return

        # Clear existing handlers
        self.logger.handlers.clear()

        # Set log level
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.setLevel(numeric_level)

        # Create formatters
        if json_format:
            formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

        # Console handler
        if log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # File handler with rotation
        if log_to_file:
            if log_file is None:
                log_file = f"{self.service_name}.log"

            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        self._configured = True

    def _log_with_context(
        self,
        level: int,
        message: str,
        correlation_id: Optional[str] = None,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        status_code: Optional[int] = None,
        duration_ms: Optional[float] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        extra_fields: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a message with structured context."""

        # Create log record with extra attributes
        extra = {
            'service': self.service_name,
            'correlation_id': correlation_id,
            'request_id': request_id,
            'user_id': user_id,
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'duration_ms': duration_ms,
            'ip_address': ip_address,
            'user_agent': user_agent,
        }

        if extra_fields:
            extra['extra_fields'] = extra_fields

        self.logger.log(level, message, extra=extra)

    def debug(self, message: str, **kwargs) -> None:
        self._log_with_context(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        self._log_with_context(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        self._log_with_context(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        self._log_with_context(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        self._log_with_context(logging.CRITICAL, message, **kwargs)

    def log_request(
        self,
        method: str,
        endpoint: str,
        correlation_id: Optional[str] = None,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """Log an incoming request."""
        self.info(
            f"Request: {method} {endpoint}",
            correlation_id=correlation_id,
            request_id=request_id,
            method=method,
            endpoint=endpoint,
            ip_address=ip_address,
            user_agent=user_agent
        )

    def log_response(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration_ms: float,
        correlation_id: Optional[str] = None,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> None:
        """Log an outgoing response."""
        level = logging.INFO if status_code < 400 else logging.WARNING if status_code < 500 else logging.ERROR

        self.logger.log(
            level,
            f"Response: {method} {endpoint} - {status_code} ({duration_ms:.2f}ms)",
            extra={
                'service': self.service_name,
                'correlation_id': correlation_id,
                'request_id': request_id,
                'user_id': user_id,
                'endpoint': endpoint,
                'method': method,
                'status_code': status_code,
                'duration_ms': duration_ms,
            }
        )

    def log_error(
        self,
        error: Exception,
        message: Optional[str] = None,
        correlation_id: Optional[str] = None,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None
    ) -> None:
        """Log an error with context."""
        error_msg = message or str(error)
        self.error(
            f"Error: {error_msg}",
            correlation_id=correlation_id,
            request_id=request_id,
            user_id=user_id,
            endpoint=endpoint,
            extra_fields={'error_type': type(error).__name__}
        )


# Global logger instances
_loggers: Dict[str, SothemaLogger] = {}


def get_logger(service_name: str) -> SothemaLogger:
    """Get or create a logger for a service."""
    if service_name not in _loggers:
        _loggers[service_name] = SothemaLogger(service_name)

        # Auto-configure with environment variables
        log_level = os.getenv("LOG_LEVEL", "INFO")
        json_format = os.getenv("LOG_JSON_FORMAT", "true").lower() == "true"
        log_to_file = os.getenv("LOG_TO_FILE", "true").lower() == "true"

        _loggers[service_name].configure(
            level=log_level,
            json_format=json_format,
            log_to_file=log_to_file
        )

    return _loggers[service_name]


def generate_correlation_id() -> str:
    """Generate a unique correlation ID for request tracing."""
    return str(uuid.uuid4())


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())