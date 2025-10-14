# Enhanced Logging System for SothemaAI

This document describes the comprehensive logging, monitoring, and alerting system implemented for the SothemaAI microservices platform.

## Overview

The logging system provides:
- **Structured JSON logging** for better monitoring and analysis
- **Request/response tracing** with correlation IDs
- **Performance monitoring** and health checks
- **Alerting system** for critical issues
- **Centralized configuration** across all services

## Architecture

### Components

1. **Structured Logging** (`logging_utils.py`)
   - JSON-formatted logs with consistent structure
   - Correlation ID tracking across service calls
   - Performance metrics and error context

2. **Logging Middleware** (`middleware/logging_middleware.py`)
   - Automatic request/response logging
   - Performance timing and error tracking
   - Client information extraction

3. **Monitoring System** (`monitoring.py`)
   - Health status tracking
   - System metrics collection
   - Alert generation and management

4. **Configuration** (`logging_config.py`)
   - Centralized logging setup
   - Environment-based configuration
   - Production-ready defaults

## Log Format

All logs use JSON format with the following structure:

```json
{
  "timestamp": "2025-10-14T21:35:07.123Z",
  "level": "INFO",
  "logger": "auth_service",
  "message": "User login successful",
  "service": "auth_service",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "request_id": "550e8400-e29b-41d4-a716-446655440001",
  "user_id": "user123",
  "endpoint": "/auth/login",
  "method": "POST",
  "status_code": 200,
  "duration_ms": 150.5,
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0..."
}
```

## Configuration

### Environment Variables

```bash
# Logging level
LOG_LEVEL=INFO

# Output destinations
LOG_TO_FILE=true
LOG_TO_CONSOLE=true

# File configuration
LOG_FILE_PATH=/var/log/sothema/auth_service.log
LOG_MAX_BYTES=10485760  # 10MB
LOG_BACKUP_COUNT=5

# Format
LOG_JSON_FORMAT=true
```

### Service Integration

Each service initializes logging in `main.py`:

```python
from shared_utils import get_logger, LoggingMiddleware

# Initialize logger
logger = get_logger("service_name")

# Add middleware
app.add_middleware(LoggingMiddleware, service_name="service_name")
```

## Monitoring Features

### Health Checks

- Automatic health status logging every 5 minutes
- System metrics (CPU, memory, disk usage)
- Service metrics (request count, error rate, uptime)
- Configurable thresholds for alerts

### Alerting

- **High Error Rate**: Triggered when error rate exceeds 5%
- **High Memory Usage**: Triggered when memory usage exceeds 90%
- **Custom Alerts**: Services can raise application-specific alerts

### Performance Monitoring

- Request timing and slow request detection (>1 second)
- Error rate tracking
- System resource monitoring
- Historical metrics storage

## Usage Examples

### Basic Logging

```python
from shared_utils import get_logger

logger = get_logger("my_service")

# Simple message
logger.info("Service started successfully")

# With context
logger.info("User authenticated", user_id="123", endpoint="/login")

# Error with details
logger.error("Database connection failed", extra_fields={"db_host": "localhost"})
```

### Request Logging

The logging middleware automatically logs all requests:

```
INFO: Request: POST /auth/login - correlation_id: abc-123
INFO: Response: POST /auth/login - 200 (150ms) - correlation_id: abc-123
```

### Health Monitoring

```python
from shared_utils import get_service_monitor

monitor = get_service_monitor("my_service")
health_status = monitor.get_health_status()
monitor.log_health_status()  # Logs current health
```

### Alerting

```python
from shared_utils import get_alert_manager

alert_manager = get_alert_manager("my_service")

# Raise alert
alert_manager.raise_alert(
    "database_down",
    "Cannot connect to database",
    severity="critical"
)

# Resolve alert
alert_manager.resolve_alert("database_down", "Database connection restored")
```

## Log Analysis

### Using jq for JSON logs

```bash
# View recent errors
tail -f service.log | jq 'select(.level == "ERROR")'

# Count requests by endpoint
cat service.log | jq -r '.endpoint' | sort | uniq -c | sort -nr

# Find slow requests
cat service.log | jq 'select(.duration_ms > 1000)'
```

### Log Aggregation

For production deployments, consider:

- **ELK Stack**: Elasticsearch, Logstash, Kibana
- **Fluentd**: Log collection and forwarding
- **Grafana + Loki**: Log aggregation and visualization
- **AWS CloudWatch**: Cloud-native logging
- **Datadog/Sumologic**: Enterprise monitoring

## Best Practices

### 1. Structured Logging
- Use consistent field names
- Include relevant context in every log entry
- Avoid logging sensitive information

### 2. Log Levels
- **DEBUG**: Detailed debugging (development only)
- **INFO**: Normal operations and important events
- **WARNING**: Unexpected but non-critical issues
- **ERROR**: Errors that affect functionality
- **CRITICAL**: System-critical failures

### 3. Performance
- Log rotation prevents disk space issues
- Asynchronous logging for better performance
- Structured format enables efficient querying

### 4. Security
- Never log passwords, tokens, or sensitive data
- Use correlation IDs for request tracing
- Implement log access controls

### 5. Monitoring
- Set up alerts for critical conditions
- Monitor error rates and performance metrics
- Regular health check reviews

## Troubleshooting

### Common Issues

1. **Logs not appearing**: Check LOG_TO_CONSOLE and LOG_TO_FILE settings
2. **Permission errors**: Ensure log directory is writable
3. **Large log files**: Adjust LOG_MAX_BYTES or enable rotation
4. **Performance impact**: Use appropriate log levels in production

### Debug Mode

Enable debug logging temporarily:

```bash
export LOG_LEVEL=DEBUG
export LOG_JSON_FORMAT=false  # Human-readable format
```

## Integration with Existing Services

The logging system is backward-compatible. Existing services can gradually adopt the new features:

1. Replace basic logging setup with structured logger
2. Add logging middleware for automatic request logging
3. Implement health monitoring endpoints
4. Configure alerting for critical conditions

## Future Enhancements

- Distributed tracing integration (OpenTelemetry)
- Metrics export to Prometheus
- Log shipping to centralized systems
- Advanced alerting with notifications
- Performance profiling integration
