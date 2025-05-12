from fastapi import APIRouter, Depends, HTTPException, Form, Request, Header  # Ajout de Form, Request et Header
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
async def login_gateway(username: str = Form(...), password: str = Form(...)): # Utiliser Form pour les paramètres
    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Redirection de la demande de token vers {AUTH_SERVICE_URL}/token pour l'utilisateur: {username}")
            # Le service d'authentification attend les données en form-data
            form_data_to_auth = {
                "username": username,
                "password": password
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

# --- Routes pour la gestion des clés API via le service d'authentification ---

@router.post("/auth/apikeys")
async def gateway_create_api_key(request: Request, token: str = Depends(oauth2_scheme)):
    try:
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            payload = await request.json()
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

@router.get("/auth/apikeys")
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

@router.delete("/auth/apikeys/{key_prefix}")
async def gateway_revoke_api_key(key_prefix: str, token: str = Depends(oauth2_scheme)):
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

@router.post("/inference/generate")
async def generate_inference(request: Request, x_api_key: str | None = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Clé API manquante dans l'en-tête X-API-Key")
    
    try:
        async with httpx.AsyncClient() as client:
            # Transmettre le corps de la requête originale et la clé API
            headers = {"X-API-Key": x_api_key, "Content-Type": "application/json"}
            payload = await request.json() # Lire le corps JSON de la requête entrante
            
            logger.info(f"Redirection de la demande d'inférence vers {INFERENCE_SERVICE_URL}/inference/generate avec le préfixe de clé: {x_api_key[:8]}...")
            
            response = await client.post(
                f"{INFERENCE_SERVICE_URL}/inference/generate", 
                json=payload, 
                headers=headers
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Erreur HTTP du service d'inférence: {e.response.status_code} - {e.response.text}")
        detail = "Erreur du service d'inférence"
        try:
            detail = e.response.json() # Essayer de récupérer le détail de l'erreur du service
        except Exception:
            pass # Garder le message par défaut si le JSON n'est pas valide
        raise HTTPException(status_code=e.response.status_code, detail=detail)
    except httpx.RequestError as e:
        logger.error(f"Erreur de requête lors de la redirection vers le service d'inférence: {e}")
        raise HTTPException(status_code=503, detail="Erreur de communication avec le service d'inférence")
    except Exception as e:
        logger.error(f"Erreur inattendue dans generate_inference (gateway): {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur dans le gateway")

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