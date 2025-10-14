from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes.gateway import router as gateway_router
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .routes.gateway import router as gateway_router
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SothemaAI API Gateway",
    description="""
# SothemaAI Pharmaceutical AI Platform API Gateway

This is the central API Gateway for the SothemaAI microservices platform, providing secure access to AI-powered pharmaceutical services.

## Services Overview

- **🔐 Authentication Service**: User management, JWT authentication, and API key generation
- **🤖 Inference Service**: AI-powered text generation, embeddings, and Retrieval Augmented Generation (RAG) for pharmaceutical content
- **📊 Logging Service**: Centralized logging and monitoring across all services

## Authentication

Most endpoints require authentication via JWT tokens or API keys:

- **JWT Authentication**: Required for user management and API key operations
- **API Key Authentication**: Required for inference operations (pass in `X-API-Key` header)

## Pharmaceutical Content Validation

All inference requests are validated to ensure they contain pharmaceutical-related content, maintaining the platform's focus on healthcare and medical applications.

## Rate Limiting

The gateway implements rate limiting to prevent abuse and ensure fair usage across all services.

## Error Handling

Comprehensive error handling with detailed error messages and appropriate HTTP status codes.
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
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add security schemes for API documentation
security_schemes = {
    "BearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "JWT token obtained from /token endpoint"
    },
    "ApiKeyAuth": {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
        "description": "API key obtained from /auth/apikeys endpoint"
    }
}

if hasattr(app, 'openapi') and app.openapi():
    openapi_schema = app.openapi()
    openapi_schema["components"]["securitySchemes"] = security_schemes
    app.openapi_schema = openapi_schema

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ajustez ceci à vos besoins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclure les routes de la passerelle
app.include_router(gateway_router)

@app.on_event("startup")
async def startup_event():
    logger.info("Gateway service is starting up...")

@app.get("/")
async def root():
    return {"message": "Welcome to the SothemaAI API Gateway"}