from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db
import psycopg2
import logging
from typing import Dict, Any
import time

logger = logging.getLogger(__name__)

router = APIRouter()

def check_database_health(db: Session) -> Dict[str, Any]:
    """Check database connectivity and basic operations"""
    try:
        start_time = time.time()
        # Simple query to test database connection
        result = db.execute(text("SELECT 1")).fetchone()
        response_time = time.time() - start_time

        return {
            "status": "healthy",
            "response_time_ms": round(response_time * 1000, 2),
            "message": "Database connection successful"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Database connection failed"
        }

def check_email_service_health() -> Dict[str, Any]:
    """Check email service configuration"""
    from ..utils.email_utils import check_email_configuration

    try:
        is_configured = check_email_configuration()
        if is_configured:
            return {
                "status": "healthy",
                "message": "Email service configured"
            }
        else:
            return {
                "status": "degraded",
                "message": "Email service not configured"
            }
    except Exception as e:
        logger.error(f"Email service health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Email service check failed"
        }

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "auth_service",
        "timestamp": time.time()
    }

@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check with component status"""
    checks = {
        "database": check_database_health(db),
        "email_service": check_email_service_health()
    }

    # Determine overall status
    overall_status = "healthy"
    for check_name, check_result in checks.items():
        if check_result["status"] == "unhealthy":
            overall_status = "unhealthy"
            break
        elif check_result["status"] == "degraded" and overall_status == "healthy":
            overall_status = "degraded"

    return {
        "status": overall_status,
        "service": "auth_service",
        "timestamp": time.time(),
        "checks": checks
    }

@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """Kubernetes readiness probe"""
    health = await detailed_health_check(db)
    # For readiness, we consider degraded as ready (email service might be optional)
    is_ready = health["status"] in ["healthy", "degraded"]
    return {
        "ready": is_ready,
        "status": health["status"]
    }

@router.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe - always returns healthy if service is running"""
    return {
        "alive": True,
        "status": "healthy",
        "timestamp": time.time()
    }