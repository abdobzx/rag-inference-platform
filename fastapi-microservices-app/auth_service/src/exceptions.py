from fastapi import HTTPException, status
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class SothemaAIException(Exception):
    """Base exception class for SothemaAI application"""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

# Authentication & Authorization Exceptions
class AuthenticationError(SothemaAIException):
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_ERROR",
            details=details
        )

class AuthorizationError(SothemaAIException):
    def __init__(self, message: str = "Insufficient permissions", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_ERROR",
            details=details
        )

class InvalidTokenError(AuthenticationError):
    def __init__(self, message: str = "Invalid or expired token", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)

class TokenExpiredError(AuthenticationError):
    def __init__(self, message: str = "Token has expired", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)

# User Management Exceptions
class UserNotFoundError(SothemaAIException):
    def __init__(self, message: str = "User not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="USER_NOT_FOUND",
            details=details
        )

class UserAlreadyExistsError(SothemaAIException):
    def __init__(self, message: str = "User already exists", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="USER_ALREADY_EXISTS",
            details=details
        )

class EmailNotVerifiedError(SothemaAIException):
    def __init__(self, message: str = "Email not verified", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="EMAIL_NOT_VERIFIED",
            details=details
        )

class InvalidEmailDomainError(SothemaAIException):
    def __init__(self, message: str = "Invalid email domain", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INVALID_EMAIL_DOMAIN",
            details=details
        )

# API Key Exceptions
class APIKeyNotFoundError(SothemaAIException):
    def __init__(self, message: str = "API key not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="API_KEY_NOT_FOUND",
            details=details
        )

class APIKeyExpiredError(SothemaAIException):
    def __init__(self, message: str = "API key has expired", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="API_KEY_EXPIRED",
            details=details
        )

class APIKeyRevokedError(SothemaAIException):
    def __init__(self, message: str = "API key has been revoked", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="API_KEY_REVOKED",
            details=details
        )

class InvalidAPIKeyError(SothemaAIException):
    def __init__(self, message: str = "Invalid API key", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="INVALID_API_KEY",
            details=details
        )

# Validation Exceptions
class ValidationError(SothemaAIException):
    def __init__(self, message: str = "Validation error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="VALIDATION_ERROR",
            details=details
        )

# Service Unavailable Exceptions
class ServiceUnavailableError(SothemaAIException):
    def __init__(self, message: str = "Service temporarily unavailable", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="SERVICE_UNAVAILABLE",
            details=details
        )

class ModelNotLoadedError(ServiceUnavailableError):
    def __init__(self, message: str = "AI model not loaded", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)

class DatabaseConnectionError(ServiceUnavailableError):
    def __init__(self, message: str = "Database connection error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)

# Rate Limiting Exceptions
class RateLimitExceededError(SothemaAIException):
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details
        )

# External Service Exceptions
class ExternalServiceError(SothemaAIException):
    def __init__(self, message: str = "External service error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="EXTERNAL_SERVICE_ERROR",
            details=details
        )

class EmailServiceError(ExternalServiceError):
    def __init__(self, message: str = "Email service error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)