from fastapi import APIRouter, Request
import logging
from typing import Dict, Any
import time

logger = logging.getLogger(__name__)

router = APIRouter()

def check_model_health(request: Request) -> Dict[str, Any]:
    """Check if AI models are loaded and available"""
    try:
        app_state = request.app.state

        model_status = "healthy" if hasattr(app_state, 'model') and app_state.model is not None else "unhealthy"
        tokenizer_status = "healthy" if hasattr(app_state, 'tokenizer') and app_state.tokenizer is not None else "unhealthy"
        embedding_status = "healthy" if hasattr(app_state, 'embedding_model') and app_state.embedding_model is not None else "unhealthy"
        rag_status = "healthy" if hasattr(app_state, 'rag_augmenter') and app_state.rag_augmenter is not None else "unhealthy"

        overall_status = "healthy"
        if any(status == "unhealthy" for status in [model_status, tokenizer_status]):
            overall_status = "unhealthy"
        elif any(status == "unhealthy" for status in [embedding_status, rag_status]):
            overall_status = "degraded"

        return {
            "status": overall_status,
            "components": {
                "model": model_status,
                "tokenizer": tokenizer_status,
                "embedding_model": embedding_status,
                "rag_augmenter": rag_status
            },
            "message": f"Model components status: {overall_status}"
        }
    except Exception as e:
        logger.error(f"Model health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Model health check failed"
        }

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "inference_service",
        "timestamp": time.time()
    }

@router.get("/health/detailed")
async def detailed_health_check(request: Request):
    """Detailed health check with model status"""
    checks = {
        "models": check_model_health(request)
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
        "service": "inference_service",
        "timestamp": time.time(),
        "checks": checks
    }

@router.get("/health/ready")
async def readiness_check(request: Request):
    """Kubernetes readiness probe - checks if models are loaded"""
    health = await detailed_health_check(request)
    # For readiness, we need models to be loaded
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