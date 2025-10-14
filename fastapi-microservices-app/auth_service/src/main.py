from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from .routes.auth import router as auth_router
from .routes.api_key_routes import router as api_key_router, internal_router as api_key_internal_router  # Importer le nouveau routeur interne
from .routes.health import router as health_router
from .database import engine, Base
from .models.user import User  # Import explicite du modèle User
from .models.api_key import APIKey  # Importer le modèle APIKey
from .exceptions import SothemaAIException
from .error_handlers import (
    sothema_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    generic_exception_handler,
    add_request_id
)
from .middleware.rate_limit import RateLimitMiddleware, rate_limiter
import sys
import os

# Add shared_utils to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared_utils.logging_utils import get_logger
from shared_utils.middleware.logging_middleware import LoggingMiddleware

# Initialize structured logger
logger = get_logger("auth_service")

app = FastAPI(
    title="SothemaAI Authentication Service",
    description="""
# SothemaAI Authentication & API Key Management Service

This service handles user authentication, authorization, and API key management for the SothemaAI platform.

## Features

- **🔐 JWT Authentication**: Secure token-based authentication with configurable expiration
- **👤 User Management**: Registration, email verification, and user profile management
- **🔑 API Key Management**: Generate, list, and revoke API keys for inference services
- **🛡️ Security**: Rate limiting, input validation, and secure password hashing
- **📊 Monitoring**: Health checks and comprehensive logging

## Authentication Flow

1. **Registration**: Users register with email verification requirement
2. **Email Verification**: 6-digit code sent to @mysothemalab.com emails only
3. **Login**: JWT tokens issued for authenticated sessions
4. **API Keys**: Generate keys for programmatic access to inference services

## Security Features

- Password complexity requirements (8+ chars, mixed case, digits, symbols)
- Email domain restrictions for organizational security
- Rate limiting to prevent brute force attacks
- Input sanitization and validation
- Secure API key generation and storage
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

# Add middleware
app.middleware("http")(add_request_id)
app.add_middleware(LoggingMiddleware, service_name="auth_service")
app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)

# Add exception handlers
app.add_exception_handler(SothemaAIException, sothema_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include routers
app.include_router(auth_router)
app.include_router(api_key_router)  # Inclure le routeur de gestion des clés API (protégé par JWT)
app.include_router(api_key_internal_router)  # Inclure le routeur de validation interne des clés API (non protégé par JWT)
app.include_router(health_router)

@app.on_event("startup")
async def startup_db_client():
    try:
        # Création des tables dans la base de données
        logger.info("Création des tables dans la base de données...")
        Base.metadata.create_all(bind=engine)
        logger.info("Tables créées avec succès!")
    except Exception as e:
        logger.error(f"Erreur lors de la création des tables: {e}")
        # Ne pas arrêter l'application si nous ne pouvons pas créer les tables
        # Cette approche permet à l'API de démarrer, même si la BDD n'est pas disponible
        # Dans un environnement de production, vous pourriez vouloir une approche différente

@app.get("/")
def read_root():
    return {
        "message": "Service d'Authentification et de Gestion des Accès SothemaAI",
        "description": "Ce service gère l'authentification des utilisateurs (inscription, connexion, vérification d'e-mail) et la gestion des clés API pour accéder aux autres services de la plateforme SothemaAI.",
        "routes_summary": {
            "/auth/register": "POST - Inscription de nouveaux utilisateurs.",
            "/auth/verify-email": "POST - Vérification de l'e-mail utilisateur avec un code.",
            "/token": "POST - Connexion des utilisateurs et obtention d'un token JWT (via form data: username, password).",
            "/apikeys": "POST, GET, DELETE - Gestion des clés API (création, listage, révocation - nécessite un token JWT).",
            "/internal/validate-apikey": "POST - Validation interne d'une clé API (utilisé par d'autres services, non destiné à un appel direct par l'utilisateur final)."
        },
        "notes_on_ai_models": "Pour les fonctionnalités d'intelligence artificielle, telles que la génération de texte, les résumés de documents ou l'utilisation de RAG (Retrieval Augmented Generation), la plateforme SothemaAI s'appuie sur des modèles de langage avancés. Un exemple de modèle pouvant être utilisé par le service dédié est 'deepseek-ai/deepseek-coder-1.3b-instruct'. Ce service d'authentification ne gère pas directement l'exécution ou la sélection des modèles IA, mais il sécurise l'accès aux services qui les utilisent.",
        "related_services": {
            "inference_service": "Ce service est responsable de l'exécution des modèles de langage et des tâches d'inférence. Veuillez consulter la documentation de l'inference_service (accessible via sa propre route racine) pour plus de détails sur les modèles spécifiques qu'il utilise et comment interagir avec ses endpoints."
        }
    }