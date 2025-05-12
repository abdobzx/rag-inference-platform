\
# filepath: /Users/abderrahman/Desktop/SothemaAI/fastapi-microservices-app/inference_service/src/utils/security.py
import httpx
from fastapi import Depends, HTTPException, status, Request
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

# L'URL du service d'authentification, devrait idéalement être configurée via des variables d'environnement.
AUTH_SERVICE_URL = "http://auth_service:8000" # Port interne du service d'authentification

api_key_header_scheme = APIKeyHeader(name="X-API-Key", auto_error=True)

class ValidatedUserData(BaseModel):
    user_id: int
    key_prefix: str
    description: str | None = None

async def validate_api_key(api_key: str = Depends(api_key_header_scheme)) -> ValidatedUserData:
    if not api_key:
        logger.warning("Tentative d'accès sans clé API.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API requise.",
        )
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AUTH_SERVICE_URL}/internal/apikeys/validate",
                json={"api_key": api_key}
            )
            response.raise_for_status() # Lève une exception pour les codes d'erreur HTTP 4xx/5xx
            
            validated_data = response.json()
            logger.info(f"Clé API validée avec succès pour user_id: {validated_data.get('user_id')}, préfixe: {validated_data.get('key_prefix')}")
            return ValidatedUserData(**validated_data)

    except httpx.HTTPStatusError as e:
        # Transférer l'erreur du service d'authentification
        detail = e.response.json().get("detail", "Erreur de validation de la clé API")
        logger.warning(f"Échec de la validation de la clé API (préfixe: {api_key[:8]}...): {e.response.status_code} - {detail}")
        raise HTTPException(
            status_code=e.response.status_code, # Utiliser le code d'erreur original du service d'auth
            detail=detail,
        )
    except httpx.RequestError as e:
        logger.error(f"Erreur de communication avec le service d'authentification lors de la validation de la clé API: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Erreur de communication avec le service d'authentification.",
        )
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la validation de la clé API: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne du serveur lors de la validation de la clé API.",
        )
