from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
import httpx

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

AUTH_SERVICE_URL = "http://auth_service:8000" # Port interne du service d'authentification
INFERENCE_SERVICE_URL = "http://inference_service:8001" # Port interne du service d'inférence
LOGGING_SERVICE_URL = "http://logging_service:8002" # Port interne du service de journalisation

@router.post("/auth/token") # Changement de l'URL pour correspondre à ce que OAuth2PasswordBearer attend
async def login(credentials: dict): # Enlever token = Depends(oauth2_scheme) ici, car c'est le point de terminaison du token lui-même
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{AUTH_SERVICE_URL}/auth/login", json=credentials)
    return response.json()

@router.post("/inference/generate")
async def generate_inference(data: dict, token: str = Depends(oauth2_scheme)):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{INFERENCE_SERVICE_URL}/inference/generate", json=data)
    return response.json()

@router.get("/logs")
async def get_logs(token: str = Depends(oauth2_scheme)):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{LOGGING_SERVICE_URL}/logs")
    return response.json()