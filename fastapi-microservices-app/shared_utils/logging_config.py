"""
Logging Configuration for SothemaAI Microservices

This module provides centralized logging configuration for all microservices
in the SothemaAI platform. It sets up structured JSON logging with appropriate
formatters, handlers, and log levels for production use.
"""

import os
import logging.config
from typing import Dict, Any


def get_logging_config(service_name: str) -> Dict[str, Any]:
    """
    Get logging configuration for a specific service.

    Args:
        service_name: Name of the service (e.g., 'auth_service', 'inference_service')

    Returns:
        Dictionary containing logging configuration
    """

    # Environment-based configuration
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_to_file = os.getenv("LOG_TO_FILE", "true").lower() == "true"
    log_to_console = os.getenv("LOG_TO_CONSOLE", "true").lower() == "true"
    log_file_path = os.getenv("LOG_FILE_PATH", f"/var/log/sothema/{service_name}.log")
    max_bytes = int(os.getenv("LOG_MAX_BYTES", "10485760"))  # 10MB default
    backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))

    # Ensure log directory exists
    log_dir = os.path.dirname(log_file_path)
    if log_dir and not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir, exist_ok=True)
        except PermissionError:
            # Fallback to current directory if we can't create the log directory
            log_file_path = f"{service_name}.log"

    # Base configuration
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "shared_utils.logging_utils.StructuredFormatter",
            },
            "simple": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        },
        "handlers": {},
        "loggers": {
            service_name: {
                "level": log_level,
                "handlers": [],
                "propagate": False
            },
            "shared_utils": {
                "level": log_level,
                "handlers": [],
                "propagate": False
            }
        },
        "root": {
            "level": "WARNING",
            "handlers": []
        }
    }

    # Add console handler
    if log_to_console:
        config["handlers"]["console"] = {
            "class": "logging.StreamHandler",
            "formatter": "json" if os.getenv("LOG_JSON_FORMAT", "true").lower() == "true" else "simple",
            "stream": "ext://sys.stdout"
        }
        config["loggers"][service_name]["handlers"].append("console")
        config["loggers"]["shared_utils"]["handlers"].append("console")

    # Add file handler
    if log_to_file:
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "json",
            "filename": log_file_path,
            "maxBytes": max_bytes,
            "backupCount": backup_count,
            "encoding": "utf-8"
        }
        config["loggers"][service_name]["handlers"].append("file")
        config["loggers"]["shared_utils"]["handlers"].append("file")

    return config


def setup_service_logging(service_name: str) -> None:
    """
    Set up logging for a service using the centralized configuration.

    Args:
        service_name: Name of the service
    """
    config = get_logging_config(service_name)
    logging.config.dictConfig(config)


def get_service_logger(service_name: str) -> logging.Logger:
    """
    Get a configured logger for a service.

    Args:
        service_name: Name of the service

    Returns:
        Configured logger instance
    """
    setup_service_logging(service_name)
    return logging.getLogger(service_name)


# Environment variables reference:
"""
LOG_LEVEL: Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_TO_FILE: Enable/disable file logging (true/false)
LOG_TO_CONSOLE: Enable/disable console logging (true/false)
LOG_FILE_PATH: Path to log file (default: /var/log/sothema/{service_name}.log)
LOG_MAX_BYTES: Maximum log file size in bytes (default: 10485760 = 10MB)
LOG_BACKUP_COUNT: Number of backup log files to keep (default: 5)
LOG_JSON_FORMAT: Use JSON formatting for logs (true/false, default: true)
"""