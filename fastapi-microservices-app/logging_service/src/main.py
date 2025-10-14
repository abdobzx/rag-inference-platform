from fastapi import FastAPI
from .routes.logs import router as logs_router
from .utils.logger import setup_logging

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

# Setup logging
setup_logging()

# Include the logs router
app.include_router(logs_router)

@app.get("/")
def read_root():
    return {"message": "Logging Service is running."}