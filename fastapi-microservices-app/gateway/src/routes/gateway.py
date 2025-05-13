from fastapi import APIRouter, Depends, HTTPException, Form, Request, Header  # Ajout de Form, Request et Header
from fastapi.security import OAuth2PasswordBearer
import httpx
import logging
import json  # Ajout de l'import json

logger = logging.getLogger(__name__)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")  # Corrigé tokenUrl pour correspondre à l'endpoint /token

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

@router.post("/auth/verify-email") # Nouvelle route pour la vérification d'email
async def verify_email_gateway(verification_data: dict):
    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Redirection de la demande de vérification d'email vers {AUTH_SERVICE_URL}/auth/verify-email")
            response = await client.post(f"{AUTH_SERVICE_URL}/auth/verify-email", json=verification_data)
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

@router.get("/auth/info")
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

@router.post("/inference/generate")
async def generate_inference(request: Request, x_api_key: str | None = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Clé API manquante dans l'en-tête X-API-Key")
    
    raw_body = await request.body()
    try:
        # json.loads lèvera une JSONDecodeError si raw_body est vide ou n'est pas un JSON valide.
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        logger.error(f"Corps JSON invalide ou vide reçu pour /inference/generate. Corps brut: {raw_body.decode(errors='ignore')}")
        raise HTTPException(status_code=400, detail="Corps JSON invalide, vide ou malformé.")

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

@router.post("/inference/embed")
async def embed_texts(request: Request, x_api_key: str | None = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Clé API manquante dans l'en-tête X-API-Key")

    raw_body = await request.body()
    try:
        payload = json.loads(raw_body)
        if not isinstance(payload, dict) or "texts" not in payload or not isinstance(payload["texts"], list):
             logger.error(f"Corps JSON invalide pour /inference/embed. Attendu un objet avec une clé 'texts' (liste de chaînes). Reçu: {raw_body.decode(errors='ignore')}")
             raise HTTPException(status_code=400, detail="Corps JSON invalide. Attendu un objet avec une clé 'texts' (liste de chaînes).")
    except json.JSONDecodeError:
        logger.error(f"Corps JSON invalide ou vide reçu pour /inference/embed. Corps brut: {raw_body.decode(errors='ignore')}")
        raise HTTPException(status_code=400, detail="Corps JSON invalide, vide ou malformé.")

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