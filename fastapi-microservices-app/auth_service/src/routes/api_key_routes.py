import secrets
import hashlib
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import update  # Ajout pour la mise à jour
from datetime import datetime  # Ajout de datetime pour APIKeyResponse
import re
import html

from ..database import get_db
from ..models.user import User
from ..models.api_key import APIKey
from ..utils import security
import logging

logger = logging.getLogger(__name__)

# Validation patterns
API_KEY_PATTERN = re.compile(r'^sk-[a-zA-Z0-9]{32,64}$')
DESCRIPTION_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_.,!?()]{1,200}$')

def sanitize_string(value):
    """Sanitize string input to prevent XSS attacks"""
    if not isinstance(value, str):
        return value
    # Remove HTML tags and escape special characters
    sanitized = html.escape(value.strip())
    # Remove potential script tags (double protection)
    sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
    return sanitized

def validate_api_key_description(description):
    """Validate API key description"""
    if description is not None:
        if not DESCRIPTION_PATTERN.match(description):
            raise ValueError(
                'Description can only contain letters, numbers, spaces, and basic punctuation (-_.,!?())'
            )
        return sanitize_string(description)
    return description

def validate_api_key_format(api_key):
    """Validate API key format"""
    if not API_KEY_PATTERN.match(api_key):
        raise ValueError('API key must be in format sk-xxxxxxxxxxxxxxxx (35-70 characters)')
    return api_key

router = APIRouter(
    prefix="/apikeys",
    tags=["API Keys"],
    dependencies=[Depends(security.get_current_active_user)]  # Protéger toutes les routes de ce routeur
)

# --- Pydantic Schemas (Python 2 compatible) ---
class APIKeyCreate(object):
    def __init__(self, description=None):
        self.description = validate_api_key_description(description)

class APIKeyResponse(object):
    def __init__(self, key_prefix, created_at, description=None, last_used_at=None, is_active=True):
        self.key_prefix = key_prefix
        self.created_at = created_at
        self.description = description
        self.last_used_at = last_used_at
        self.is_active = is_active

class NewAPIKeyResponse(APIKeyResponse):
    def __init__(self, key_prefix, created_at, full_key, description=None, last_used_at=None, is_active=True):
        super(NewAPIKeyResponse, self).__init__(key_prefix, created_at, description, last_used_at, is_active)
        self.full_key = full_key  # La clé complète n'est retournée qu'une seule fois

class APIKeyValidationRequest(object):
    def __init__(self, api_key):
        self.api_key = validate_api_key_format(api_key)

class ValidatedAPIKeyInfo(object):
    def __init__(self, user_id, key_prefix, description=None):
        self.user_id = user_id
        self.key_prefix = key_prefix  # Renvoyer le préfixe pour le logging côté service appelant
        self.description = description
        # On pourrait ajouter d'autres infos utilisateur si nécessaire, comme le rôle, les permissions, etc.

# --- Helper Functions ---
def generate_api_key_pair():
    """Génère une clé API brute et sa version hachée."""
    api_key = secrets.token_urlsafe(32)  # Génère une clé de 32 bytes, URL-safe
    hashed_key = hashlib.sha256(api_key.encode()).hexdigest()
    return api_key, hashed_key

# --- API Key Routes ---
@router.post("", status_code=status.HTTP_201_CREATED)
def create_api_key(
    api_key_data,  # APIKeyCreate
    db = Depends(get_db),
    current_user = Depends(security.get_current_active_user)
):
    """
    Crée une nouvelle clé API pour l'utilisateur actuellement authentifié.
    La clé complète est retournée UNIQUEMENT lors de la création.
    """
    # Validate the description
    try:
        validated_description = validate_api_key_description(api_key_data.description)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    raw_key, hashed_api_key = generate_api_key_pair()
    key_prefix = raw_key[:8]  # Utiliser les 8 premiers caractères comme préfixe

    # Vérifier si le préfixe existe déjà (très improbable, mais bonne pratique)
    existing_key = db.query(APIKey).filter(APIKey.key_prefix == key_prefix).first()
    if existing_key:
        # Gérer la collision, par exemple en régénérant ou en levant une erreur
        logger.error("Collision de préfixe de clé API pour {}. Cela ne devrait pas arriver.".format(key_prefix))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur lors de la génération de la clé API. Veuillez réessayer.")

    db_api_key = APIKey(
        key_prefix=key_prefix,
        hashed_key=hashed_api_key,
        user_id=current_user.id,
        description=validated_description
    )
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)

    return {
        "full_key": raw_key,  # Important: retourner la clé brute ici
        "key_prefix": db_api_key.key_prefix,
        "created_at": db_api_key.created_at.isoformat(),
        "description": db_api_key.description,
        "last_used_at": db_api_key.last_used_at.isoformat() if db_api_key.last_used_at is not None else None,
        "is_active": db_api_key.is_active
    }

@router.get("")
def list_api_keys(
    db = Depends(get_db),
    current_user = Depends(security.get_current_active_user)
):
    """Liste toutes les clés API pour l'utilisateur actuellement authentifié."""
    api_keys = db.query(APIKey).filter(APIKey.user_id == current_user.id).all()
    return [
        {
            "key_prefix": key.key_prefix,
            "created_at": key.created_at.isoformat(),
            "description": key.description,
            "last_used_at": key.last_used_at.isoformat() if key.last_used_at is not None else None,
            "is_active": key.is_active
        }
        for key in api_keys
    ]

@router.delete("/{key_prefix}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(
    key_prefix,
    db = Depends(get_db),
    current_user = Depends(security.get_current_active_user)
):
    """Révoque (supprime) une clé API par son préfixe."""
    api_key = db.query(APIKey).filter(APIKey.key_prefix == key_prefix, APIKey.user_id == current_user.id).first()
    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clé API non trouvée ou non autorisée.")
    
    try:
        db.delete(api_key)
        db.commit()
    except Exception as e:  # Remplacé SQLAlchemyError par Exception générique pour le moment
        db.rollback()
        logger.error("Erreur DB lors de la suppression de la clé API {}: {}".format(key_prefix, e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne du serveur lors de la révocation de la clé.")
    return

# Nouveau routeur pour les opérations internes non protégées par JWT utilisateur
internal_router = APIRouter(
    prefix="/internal/apikeys",
    tags=["Internal API Key Validation"],
    # Pas de dépendance d'authentification utilisateur ici, 
    # la sécurité repose sur le fait que ce service n'est pas exposé publiquement
    # et que les appels viennent du réseau interne Docker.
)

@internal_router.post("/validate")
def validate_api_key_internal(
    payload,  # APIKeyValidationRequest
    db = Depends(get_db)
):
    # Validate the API key format
    try:
        validated_api_key = validate_api_key_format(payload.api_key)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    raw_key = validated_api_key

    # Hacher la clé brute fournie pour la comparaison
    hashed_raw_key = hashlib.sha256(raw_key.encode()).hexdigest()

    # Rechercher la clé par son hash. C'est la méthode la plus sûre.
    potential_key = None
    try:
        potential_key = db.query(APIKey).filter(APIKey.hashed_key == hashed_raw_key).first()
    except Exception as e:  # Remplacé SQLAlchemyError par Exception générique
        logger.error("Erreur DB lors de la recherche de la clé API par hash ({}...): {}".format(hashed_raw_key[:10], e))
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Erreur de service lors de la validation de la clé API.")

    if not potential_key:
        logger.info("Validation interne : Clé API avec hachage {}... non trouvée.".format(hashed_raw_key[:10]))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Clé API invalide ou non trouvée.")

    if not bool(potential_key.is_active):  # type: ignore
        logger.warning("Validation interne : Clé API {} (utilisateur {}) est inactive.".format(potential_key.key_prefix, potential_key.user_id))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="La clé API est inactive.")

    # Mettre à jour last_used_at
    try:
        current_time_utc = datetime.utcnow()  # Utiliser UTC pour la cohérence

        stmt = (
            update(APIKey)
            .where(APIKey.id == potential_key.id)  # type: ignore
            .values(last_used_at=current_time_utc)
        )
        db.execute(stmt)
        db.commit()
        logger.info("Clé API {} (utilisateur {}) validée. last_used_at mis à jour.".format(potential_key.key_prefix, potential_key.user_id))
    except Exception as e:  # Remplacé SQLAlchemyError par Exception générique
        db.rollback()
        logger.error("Erreur DB lors de la mise à jour de last_used_at pour la clé {}: {}".format(potential_key.key_prefix, e))
        # Ne pas bloquer la validation si cette mise à jour échoue, mais enregistrer l'erreur.
        # Une alternative serait de lever une HTTP 500 si cette mise à jour est critique.

    return {
        "user_id": potential_key.user_id,  # type: ignore
        "key_prefix": potential_key.key_prefix,  # type: ignore
        "description": potential_key.description  # type: ignore
    }