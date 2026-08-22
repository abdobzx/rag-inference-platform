from fastapi import APIRouter, Depends, HTTPException, Form, Request, Header, Security  # Ajout de Form, Request et Header
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
import httpx
import logging
import json  # Ajout de l'import json

from ..validation import (
    LoginRequest, RegisterRequest, VerifyEmailRequest, APIKeyCreateRequest,
    InferenceRequest, EmbeddingRequest, validate_api_key_header, validate_json_payload
)

logger = logging.getLogger(__name__)

# Security schemes
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

router = APIRouter(
    prefix="",
    tags=["Gateway"],
    responses={
        401: {"description": "Unauthorized - Invalid or missing authentication"},
        403: {"description": "Forbidden - Insufficient permissions"},
        404: {"description": "Not Found - Resource not found"},
        422: {"description": "Validation Error - Invalid request data"},
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error - Unexpected server error"},
        503: {"description": "Service Unavailable - Backend service unavailable"}
    }
)

# Définition des URLs des services micro-services
# Utiliser les noms de service Docker qui servent de noms DNS dans le réseau Docker
AUTH_SERVICE_URL = "http://auth_service:8000"  # Port interne du service d'authentification
INFERENCE_SERVICE_URL = "http://inference_service:8001"  # Port interne du service d'inférence
LOGGING_SERVICE_URL = "http://logging_service:8002"  # Port interne du service de journalisation

@router.post(
    "/token",
    summary="User Login",
    description="""
Authenticate a user and obtain a JWT access token.

**Credentials Requirements:**
- Username: 3-30 characters, alphanumeric + underscore
- Password: 8+ characters with uppercase, lowercase, digit, and special character

**Returns:** JWT access token for authenticated requests
""",
    response_description="JWT access token",
    responses={
        200: {
            "description": "Successful authentication",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer"
                    }
                }
            }
        },
        401: {"description": "Invalid credentials"}
    }
)
async def login_gateway(login_data: LoginRequest):
    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Redirection de la demande de token vers {AUTH_SERVICE_URL}/token pour l'utilisateur: {login_data.username}")
            # Le service d'authentification attend les données en form-data
            form_data_to_auth = {
                "username": login_data.username,
                "password": login_data.password
            }
            response = await client.post(f"{AUTH_SERVICE_URL}/token", data=form_data_to_auth) # Envoyer en tant que form-data
            response.raise_for_status()  # Lever une exception pour les codes d'erreur HTTP
            return response.json()
    except httpx.HTTPStatusError as e: # Capturer spécifiquement les erreurs HTTP de la requête proxy
        logger.error(f"Erreur HTTP du service d'authentification lors de la demande de token: {e.response.status_code} - {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=e.response.json())
    except httpx.RequestError as e: # Capturer les erreurs de requête (ex: service non joignable)
        logger.error(f"Erreur de requête lors de la redirection vers le service d'authentification: {e}")
        raise HTTPException(status_code=503, detail="Erreur de communication avec le service d'authentification") # 503 Service Unavailable
    except Exception as e:
        logger.error(f"Erreur inattendue dans login_gateway: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur dans le gateway")

@router.post(
    "/auth/register",
    summary="User Registration",
    description="""
Register a new user account in the SothemaAI platform.

**Requirements:**
- Username: 3-30 characters, alphanumeric + underscore
- Email: Must be from @mysothemalab.com domain
- Password: 8+ characters with mixed case, digits, and special characters

**Process:** Registration requires email verification before account activation.
""",
    response_description="User registration confirmation",
    responses={
        200: {
            "description": "Registration successful",
            "content": {
                "application/json": {
                    "example": {
                        "message": "User registered successfully. Please check your email for verification."
                    }
                }
            }
        },
        400: {"description": "Invalid registration data"},
        409: {"description": "User already exists"}
    }
)
async def register_user(user_data: RegisterRequest):
    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Redirection de la demande d'enregistrement vers {AUTH_SERVICE_URL}/auth/register")
            # Convert validated model to dict for JSON serialization
            payload = user_data.model_dump()
            response = await client.post(f"{AUTH_SERVICE_URL}/auth/register", json=payload)
            response.raise_for_status()  # Lève une exception pour les codes d'erreur HTTP 4xx/5xx
            return response.json()
    except httpx.HTTPStatusError as e: # Capturer spécifiquement les erreurs HTTP de la requête proxy
        logger.error(f"Erreur HTTP du service d'authentification lors de l'enregistrement: {e.response.status_code} - {e.response.text}")
        detail = "Erreur du service d'authentification"
        try:
            # Essayer de parser le détail de l'erreur si la réponse est du JSON
            detail = e.response.json()
        except json.JSONDecodeError:
            # Si la réponse n'est pas du JSON, utiliser le texte brut si disponible
            detail = e.response.text if e.response.text else detail
        except Exception:
            # Fallback si une autre erreur se produit lors de l'analyse des détails
            pass
        raise HTTPException(status_code=e.response.status_code, detail=detail)
    except httpx.RequestError as e: # Capturer les erreurs de requête (ex: service non joignable)
        logger.error(f"Erreur de requête lors de la redirection vers le service d'authentification pour l'enregistrement: {e}")
        raise HTTPException(status_code=503, detail="Erreur de communication avec le service d'authentification") # 503 Service Unavailable
    except Exception as e:
        logger.error(f"Erreur inattendue dans register_user (gateway): {type(e).__name__} - {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur dans le gateway")

@router.post(
    "/auth/verify-email",
    summary="Email Verification",
    description="""
Verify user email address using verification code sent during registration.

**Requirements:**
- Email: Must match the registered email address
- Verification Code: 6-digit code sent to the email

**Process:** Email verification activates the user account for full platform access.
""",
    response_description="Email verification confirmation",
    responses={
        200: {
            "description": "Email verified successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Email verified successfully. Account is now active."
                    }
                }
            }
        },
        400: {"description": "Invalid verification code or email"},
        404: {"description": "User not found"}
    }
)
async def verify_email_gateway(verification_data: VerifyEmailRequest):
    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Redirection de la demande de vérification d'email vers {AUTH_SERVICE_URL}/auth/verify-email")
            # Convert validated model to dict for JSON serialization
            payload = verification_data.model_dump()
            response = await client.post(f"{AUTH_SERVICE_URL}/auth/verify-email", json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Erreur HTTP du service d'authentification lors de la vérification d'email: {e.response.status_code} - {e.response.text}")
        detail = "Erreur du service d'authentification"
        try:
            detail = e.response.json()
        except json.JSONDecodeError:
            detail = e.response.text if e.response.text else detail
        except Exception:
            pass
        raise HTTPException(status_code=e.response.status_code, detail=detail)
    except httpx.RequestError as e:
        logger.error(f"Erreur de requête lors de la redirection pour la vérification d'email: {e}")
        raise HTTPException(status_code=503, detail="Erreur de communication avec le service d'authentification")
    except Exception as e:
        logger.error(f"Erreur inattendue dans verify_email_gateway: {type(e).__name__} - {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur dans le gateway")

# --- Routes pour la gestion des clés API via le service d'authentification ---

@router.post(
    "/auth/apikeys",
    summary="Create API Key",
    description="""
Create a new API key for accessing inference services.

**Requirements:**
- Valid JWT authentication required
- Description: Optional, max 200 characters

**API Key Format:** sk-[32-64 character string]

**Usage:** Use the generated API key in X-API-Key header for inference requests.
""",
    response_description="New API key details",
    responses={
        200: {
            "description": "API key created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "key": "sk-abc123def456ghi789jkl012mno345pqr678stu901vwx",
                        "description": "My API key for pharmaceutical research",
                        "created_at": "2025-10-14T10:30:00Z"
                    }
                }
            }
        },
        401: {"description": "Authentication required"}
    },
    dependencies=[Depends(oauth2_scheme)]
)
async def gateway_create_api_key(api_key_data: APIKeyCreateRequest, token: str = Depends(oauth2_scheme)):
    try:
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            # Convert validated model to dict for JSON serialization
            payload = api_key_data.model_dump()
            logger.info(f"Redirection de la création de clé API vers {AUTH_SERVICE_URL}/apikeys")
            response = await client.post(f"{AUTH_SERVICE_URL}/apikeys", json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Erreur HTTP du service d'authentification (apikeys): {e.response.status_code} - {e.response.text}")
        # Essayer de parser le détail de l'erreur si disponible
        detail = "Erreur du service d'authentification"
        try:
            detail = e.response.json()
        except Exception:
            pass # Garder le message par défaut si le JSON n'est pas valide
        raise HTTPException(status_code=e.response.status_code, detail=detail)
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la création de clé API via gateway: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur dans le gateway")

@router.get(
    "/auth/apikeys",
    summary="List API Keys",
    description="""
Retrieve all API keys associated with the authenticated user.

**Returns:** List of API keys with metadata (masked for security)
""",
    response_description="List of user's API keys",
    responses={
        200: {
            "description": "API keys retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "prefix": "sk-abc123...",
                            "description": "Research API key",
                            "created_at": "2025-10-14T10:30:00Z",
                            "last_used": "2025-10-14T11:15:00Z"
                        }
                    ]
                }
            }
        },
        401: {"description": "Authentication required"}
    },
    dependencies=[Depends(oauth2_scheme)]
)
async def gateway_list_api_keys(token: str = Depends(oauth2_scheme)):
    try:
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {token}"}
            logger.info(f"Redirection de la liste des clés API vers {AUTH_SERVICE_URL}/apikeys")
            response = await client.get(f"{AUTH_SERVICE_URL}/apikeys", headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Erreur HTTP du service d'authentification (apikeys): {e.response.status_code} - {e.response.text}")
        detail = "Erreur du service d'authentification"
        try:
            detail = e.response.json()
        except Exception:
            pass
        raise HTTPException(status_code=e.response.status_code, detail=detail)
    except Exception as e:
        logger.error(f"Erreur inattendue lors du listage des clés API via gateway: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur dans le gateway")

@router.delete(
    "/auth/apikeys/{key_prefix}",
    summary="Revoke API Key",
    description="""
Revoke an API key permanently. The key will no longer work for inference requests.

**Key Prefix Format:** sk-xxxxx... (first 8+ characters of the API key)
""",
    response_description="API key revocation confirmation",
    responses={
        204: {"description": "API key revoked successfully"},
        400: {"description": "Invalid key prefix format"},
        401: {"description": "Authentication required"},
        404: {"description": "API key not found"}
    },
    dependencies=[Depends(oauth2_scheme)]
)
async def gateway_revoke_api_key(key_prefix: str, token: str = Depends(oauth2_scheme)):
    # Validate key_prefix format (should be like "sk-xxxxx...")
    if not key_prefix or not key_prefix.startswith("sk-") or len(key_prefix) < 5:
        raise HTTPException(status_code=400, detail="Format de préfixe de clé API invalide")
    
    try:
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {token}"}
            logger.info(f"Redirection de la révocation de clé API {key_prefix} vers {AUTH_SERVICE_URL}/apikeys/{key_prefix}")
            response = await client.delete(f"{AUTH_SERVICE_URL}/apikeys/{key_prefix}", headers=headers)
            response.raise_for_status()
            if response.status_code == 204:
                # Pour FastAPI, retourner une Response avec status_code 204 est plus propre
                from fastapi.responses import Response
                return Response(status_code=204)
            return response.json() # Au cas où il y aurait un corps pour d'autres codes de succès
    except httpx.HTTPStatusError as e:
        logger.error(f"Erreur HTTP du service d'authentification (apikeys): {e.response.status_code} - {e.response.text}")
        detail = "Erreur du service d'authentification"
        try:
            detail = e.response.json()
        except Exception:
            pass
        raise HTTPException(status_code=e.response.status_code, detail=detail)
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la révocation de clé API via gateway: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur dans le gateway")

@router.get(
    "/auth/info",
    summary="Authentication Service Info",
    description="""
Get information about the authentication service status and capabilities.

**Returns:** Service health and version information
""",
    response_description="Authentication service information",
    responses={
        200: {
            "description": "Service information retrieved",
            "content": {
                "application/json": {
                    "example": {
                        "service": "Authentication Service",
                        "version": "1.0.0",
                        "status": "healthy",
                        "features": ["JWT auth", "API keys", "User management"]
                    }
                }
            }
        },
        401: {"description": "Authentication required"}
    },
    dependencies=[Depends(oauth2_scheme)]
)
async def get_auth_service_info(token: str = Depends(oauth2_scheme)):
    try:
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {token}"}
            logger.info(f"Redirection de la demande d'informations du service d'authentification vers {AUTH_SERVICE_URL}/")
            response = await client.get(f"{AUTH_SERVICE_URL}/", headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Erreur HTTP du service d'authentification lors de la récupération des informations: {e.response.status_code} - {e.response.text}")
        detail = "Erreur du service d'authentification"
        try:
            detail = e.response.json()
        except json.JSONDecodeError:
            detail = e.response.text if e.response.text else detail
        raise HTTPException(status_code=e.response.status_code, detail=detail)
    except httpx.RequestError as e:
        logger.error(f"Erreur de requête lors de la récupération des informations du service d'authentification: {e}")
        raise HTTPException(status_code=503, detail="Erreur de communication avec le service d'authentification")
    except Exception as e:
        logger.error(f"Erreur inattendue dans get_auth_service_info: {type(e).__name__} - {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur dans le gateway")

@router.post(
    "/inference/generate",
    summary="Generate AI Response",
    description="""
Generate AI-powered text responses using pharmaceutical knowledge and RAG (Retrieval Augmented Generation).

**Requirements:**
- Valid API key in X-API-Key header
- Text input must contain pharmaceutical/medical content
- Maximum 2000 characters input, 10 context chunks

**Features:**
- Retrieval Augmented Generation (RAG) for accurate medical responses
- Content validation ensures pharmaceutical relevance
- Configurable response length (max 8000 tokens)
""",
    response_description="AI-generated response with pharmaceutical context",
    responses={
        200: {
            "description": "AI response generated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "response": "Based on current medical literature, aspirin dosage for adults is typically 325-650mg every 4-6 hours as needed for pain relief...",
                        "confidence": 0.92,
                        "sources": ["medical_guidelines_2024.pdf", "pharmacology_textbook_ch7.pdf"]
                    }
                }
            }
        },
        400: {"description": "Invalid input or non-pharmaceutical content"},
        401: {"description": "Invalid or missing API key"},
        429: {"description": "Rate limit exceeded"}
    }
)
async def generate_inference(request: Request, x_api_key: str | None = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Clé API manquante dans l'en-tête X-API-Key")

    # Validate API key format
    try:
        validate_api_key_header(x_api_key)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Format de clé API invalide: {str(e)}")

    # Validate and parse JSON payload
    raw_body = await request.body()
    try:
        payload = validate_json_payload(raw_body, InferenceRequest)
    except ValueError as e:
        logger.error(f"Validation du payload échouée pour /inference/generate: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Payload invalide: {str(e)}")

    try:
        # Augmentation du timeout à 120 secondes pour cet appel
        timeout_config = httpx.Timeout(120.0, connect=5.0)
        async with httpx.AsyncClient(timeout=timeout_config) as client:
            # Préparer les en-têtes pour la requête au service d'inférence.
            # httpx définit Content-Type à application/json si le paramètre `json` est utilisé.
            # Le code original incluait Content-Type, donc nous le gardons pour la cohérence.
            headers_for_post = {"X-API-Key": x_api_key, "Content-Type": "application/json"}

            logger.info(f"Redirection de la demande d'inférence vers {INFERENCE_SERVICE_URL}/generate avec le préfixe de clé: {x_api_key[:8]}...")

            response = await client.post(
                f"{INFERENCE_SERVICE_URL}/generate",
                json=payload,
                headers=headers_for_post
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Erreur HTTP du service d'inférence: {e.response.status_code} - {e.response.text}")
        detail_message = "Erreur du service d'inférence"
        try:
            error_detail_json = e.response.json()
            if isinstance(error_detail_json, dict) and 'detail' in error_detail_json:
                detail_message = error_detail_json['detail']
            elif isinstance(error_detail_json, str):
                detail_message = error_detail_json
            else:
                detail_message = e.response.text if e.response.text else "Détail de l'erreur non-JSON ou mal structuré du service d'inférence."
        except json.JSONDecodeError: # Au cas où la réponse d'erreur elle-même n'est pas JSON
            detail_message = e.response.text if e.response.text else "Détail de l'erreur non-JSON du service d'inférence."
        except Exception:
            # Fallback si une autre erreur se produit lors de l'analyse des détails
            pass
        raise HTTPException(status_code=e.response.status_code, detail=detail_message)
    except httpx.RequestError as e: # Capturer les erreurs de requête (ex: service non joignable)
        logger.error(f"Erreur de requête lors de la redirection vers le service d'inférence: {e}")
        raise HTTPException(status_code=503, detail="Erreur de communication avec le service d'inférence")
    except Exception as e: # Capturer les autres exceptions potentielles
        logger.error(f"Erreur inattendue dans generate_inference (gateway): {type(e).__name__} - {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur dans le gateway")

@router.post(
    "/inference/embed",
    summary="Generate Text Embeddings",
    description="""
Generate vector embeddings for text inputs using advanced transformer models.

**Requirements:**
- Valid API key in X-API-Key header
- 1-50 texts per request
- Texts are validated for pharmaceutical content

**Use Cases:**
- Semantic search in medical literature
- Document similarity analysis
- Knowledge base indexing
- Clinical trial matching
""",
    response_description="Vector embeddings for input texts",
    responses={
        200: {
            "description": "Embeddings generated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "embeddings": [
                            [0.123, -0.456, 0.789, ...],  # 768-dimensional vector
                            [0.234, -0.567, 0.890, ...]
                        ],
                        "model": "sentence-transformers/all-MiniLM-L6-v2",
                        "dimensions": 384
                    }
                }
            }
        },
        400: {"description": "Invalid input format"},
        401: {"description": "Invalid or missing API key"}
    }
)
async def embed_texts(request: Request, x_api_key: str | None = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Clé API manquante dans l'en-tête X-API-Key")

    # Validate API key format
    try:
        validate_api_key_header(x_api_key)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Format de clé API invalide: {str(e)}")

    # Validate and parse JSON payload
    raw_body = await request.body()
    try:
        payload = validate_json_payload(raw_body, EmbeddingRequest)
    except ValueError as e:
        logger.error(f"Validation du payload échouée pour /inference/embed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Payload invalide: {str(e)}")

    try:
        # Augmentation du timeout à 120 secondes pour cet appel
        timeout_config = httpx.Timeout(120.0, connect=5.0)
        async with httpx.AsyncClient(timeout=timeout_config) as client:
            headers_for_post = {"X-API-Key": x_api_key, "Content-Type": "application/json"}

            logger.info(f"Redirection de la demande d'embedding vers {INFERENCE_SERVICE_URL}/embed avec le préfixe de clé: {x_api_key[:8]}...")

            response = await client.post(
                f"{INFERENCE_SERVICE_URL}/embed",
                json=payload,
                headers=headers_for_post
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Erreur HTTP du service d'inférence (embed): {e.response.status_code} - {e.response.text}")
        detail_message = "Erreur du service d'inférence (embed)"
        try:
            error_detail_json = e.response.json()
            if isinstance(error_detail_json, dict) and 'detail' in error_detail_json:
                detail_message = error_detail_json['detail']
            elif isinstance(error_detail_json, str):
                detail_message = error_detail_json
            else:
                detail_message = e.response.text if e.response.text else "Détail de l'erreur non-JSON ou mal structuré du service d'inférence."
        except json.JSONDecodeError:
            detail_message = e.response.text if e.response.text else "Détail de l'erreur non-JSON du service d'inférence."
        except Exception:
            pass
        raise HTTPException(status_code=e.response.status_code, detail=detail_message)
    except httpx.RequestError as e:
        logger.error(f"Erreur de requête lors de la redirection vers le service d'inférence (embed): {e}")
        raise HTTPException(status_code=503, detail="Erreur de communication avec le service d'inférence")
    except Exception as e:
        logger.error(f"Erreur inattendue dans embed_texts (gateway): {type(e).__name__} - {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur dans le gateway")

@router.get(
    "/logs",
    summary="Get System Logs",
    description="""
Retrieve system logs from all microservices for monitoring and debugging.

**Returns:** Recent log entries with timestamps, levels, and service information
""",
    response_description="System log entries",
    responses={
        200: {
            "description": "Logs retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "timestamp": "2025-10-14T11:30:15Z",
                            "level": "INFO",
                            "service": "inference_service",
                            "message": "AI model loaded successfully"
                        },
                        {
                            "timestamp": "2025-10-14T11:30:20Z",
                            "level": "WARNING",
                            "service": "gateway",
                            "message": "Rate limit approaching for user@example.com"
                        }
                    ]
                }
            }
        },
        401: {"description": "Authentication required"}
    },
    dependencies=[Depends(oauth2_scheme)]
)
async def get_logs(token: str = Depends(oauth2_scheme)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{LOGGING_SERVICE_URL}/logs")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Erreur lors de la redirection vers le service de journalisation: {e}")
        raise HTTPException(status_code=500, detail="Erreur de communication avec le service de journalisation")