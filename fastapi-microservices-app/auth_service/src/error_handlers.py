from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import logging
from typing import Union, Optional, Dict, Any
from .exceptions import SothemaAIException

logger = logging.getLogger(__name__)

def create_error_response(
    status_code: int,
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> JSONResponse:
    """Create a standardized error response"""
    error_response = {
        "error": {
            "code": error_code,
            "message": message,
            "details": details or {},
            "request_id": request_id
        },
        "success": False
    }
    return JSONResponse(status_code=status_code, content=error_response)

async def sothema_exception_handler(request: Request, exc: SothemaAIException) -> JSONResponse:
    """Handle custom SothemaAI exceptions"""
    # Log the error with context
    logger.error(
        f"SothemaAI Exception: {exc.error_code} - {exc.message}",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": str(request.url),
            "method": request.method,
            "client_ip": getattr(request.client, 'host', 'unknown') if request.client else 'unknown'
        }
    )

    return create_error_response(
        status_code=exc.status_code,
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
        request_id=getattr(request.state, 'request_id', None)
    )

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTPException"""
    logger.warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": str(request.url),
            "method": request.method,
            "client_ip": getattr(request.client, 'host', 'unknown') if request.client else 'unknown'
        }
    )

    return create_error_response(
        status_code=exc.status_code,
        error_code=f"HTTP_{exc.status_code}",
        message=exc.detail,
        request_id=getattr(request.state, 'request_id', None)
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    logger.warning(
        f"Validation Error: {len(errors)} validation errors",
        extra={
            "validation_errors": errors,
            "path": str(request.url),
            "method": request.method,
            "client_ip": getattr(request.client, 'host', 'unknown') if request.client else 'unknown'
        }
    )

    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        details={"validation_errors": errors},
        request_id=getattr(request.state, 'request_id', None)
    )

async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle SQLAlchemy database errors"""
    logger.error(
        f"Database Error: {type(exc).__name__}: {str(exc)}",
        extra={
            "exception_type": type(exc).__name__,
            "path": str(request.url),
            "method": request.method,
            "client_ip": getattr(request.client, 'host', 'unknown') if request.client else 'unknown'
        },
        exc_info=True
    )

    # Handle specific database errors
    if isinstance(exc, IntegrityError):
        return create_error_response(
            status_code=status.HTTP_409_CONFLICT,
            error_code="DATABASE_INTEGRITY_ERROR",
            message="Database integrity constraint violated",
            details={"original_error": str(exc)},
            request_id=getattr(request.state, 'request_id', None)
        )

    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="DATABASE_ERROR",
        message="Database operation failed",
        details={"original_error": str(exc)},
        request_id=getattr(request.state, 'request_id', None)
    )

async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    logger.error(
        f"Unexpected Error: {type(exc).__name__}: {str(exc)}",
        extra={
            "exception_type": type(exc).__name__,
            "path": str(request.url),
            "method": request.method,
            "client_ip": getattr(request.client, 'host', 'unknown') if request.client else 'unknown'
        },
        exc_info=True
    )

    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        details={"exception_type": type(exc).__name__},
        request_id=getattr(request.state, 'request_id', None)
    )

# Middleware to add request ID
async def add_request_id(request: Request, call_next):
    """Middleware to add request ID to each request"""
    import uuid
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)

    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id
    return response