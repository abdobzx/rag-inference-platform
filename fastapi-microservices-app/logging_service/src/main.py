from fastapi import FastAPI
from .routes.logs import router as logs_router
import sys
import os

# Add shared_utils to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared_utils.logging_utils import get_logger
from shared_utils.middleware.logging_middleware import LoggingMiddleware

# Initialize structured logger
logger = get_logger("logging_service")

app = FastAPI(
    title="SothemaAI Logging Service",
    description="""
# SothemaAI Centralized Logging Service

Centralized logging and monitoring service for the SothemaAI microservices platform.

## Features

- **📊 Log Aggregation**: Collects logs from all microservices
- **🔍 Log Retrieval**: RESTful API for log access and analysis
- **📈 Monitoring**: Structured logging with configurable levels
- **🔒 Security**: Access control and audit trail logging

## Log Levels

- **DEBUG**: Detailed debugging information
- **INFO**: General operational messages
- **WARNING**: Warning conditions that don't stop operation
- **ERROR**: Error conditions that may affect functionality
- **CRITICAL**: Critical errors requiring immediate attention

## Use Cases

- System monitoring and alerting
- Debugging microservices issues
- Audit trail for security events
- Performance analysis and optimization
    """,
    version="1.0.0",
    contact={
        "name": "SothemaAI Development Team",
        "url": "https://github.com/abdobzx/SothemaAI",
        "email": "dev@sothema.ai",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    }
)

# Add logging middleware
app.add_middleware(LoggingMiddleware, service_name="logging_service")

# Include the logs router
app.include_router(logs_router)


@app.get("/health")
async def health_check():
    """Liveness check for docker-compose / orchestrator healthchecks."""
    return {"status": "healthy", "service": "logging_service"}