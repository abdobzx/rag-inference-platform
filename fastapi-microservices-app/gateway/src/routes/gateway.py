from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
import httpx
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Définition des URLs des services micro-services
# Utiliser les noms de service Docker qui servent de noms DNS dans le réseau Docker
AUTH_SERVICE_URL = "http://auth_service:8000"  # Port interne du service d'authentification
INFERENCE_SERVICE_URL = "http://inference_service:8001"  # Port interne du service d'inférence
LOGGING_SERVICE_URL = "http://logging_service:8002"  # Port interne du service de journalisation

@router.post("/token") # Changé de /auth/token à /token
async def login_gateway(credentials: dict): # Renommé la fonction pour éviter confusion avec oauth2_scheme si importé globalement
    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Redirection de la demande de token vers {AUTH_SERVICE_URL}/token")
            # Le service d'authentification attend les données en form-data, pas en JSON pour /token
            response = await client.post(f"{AUTH_SERVICE_URL}/token", data=credentials) # Changé json=credentials en data=credentials
            response.raise_for_status()  # Lever une exception pour les codes d'erreur HTTP
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Erreur lors de la redirection vers le service d'authentification: {e}")
        raise HTTPException(status_code=500, detail="Erreur de communication avec le service d'authentification")

@router.post("/auth/register")
async def register_user(user_data: dict):
    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Redirection de la demande d'enregistrement vers {AUTH_SERVICE_URL}/auth/register")
            response = await client.post(f"{AUTH_SERVICE_URL}/auth/register", json=user_data)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Erreur lors de la redirection vers le service d'authentification: {e}")
        raise HTTPException(status_code=500, detail="Erreur de communication avec le service d'authentification")

@router.post("/inference/generate")
async def generate_inference(data: dict, token: str = Depends(oauth2_scheme)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{INFERENCE_SERVICE_URL}/inference/generate", json=data)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Erreur lors de la redirection vers le service d'inférence: {e}")
        raise HTTPException(status_code=500, detail="Erreur de communication avec le service d'inférence")

@router.get("/logs")
async def get_logs(token: str = Depends(oauth2_scheme)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{LOGGING_SERVICE_URL}/logs")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Erreur lors de la redirection vers le service de journalisation: {e}")
        raise HTTPException(status_code=500, detail="Erreur de communication avec le service de journalisation")