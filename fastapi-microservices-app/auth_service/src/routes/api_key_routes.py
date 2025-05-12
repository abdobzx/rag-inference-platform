import secrets
import hashlib
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import update  # Ajout pour la mise à jour
from datetime import datetime  # Ajout de datetime pour APIKeyResponse

from ..database import get_db
from ..models.user import User
from ..models.api_key import APIKey
from ..utils import security
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/apikeys",
    tags=["API Keys"],
    dependencies=[Depends(security.get_current_active_user)]  # Protéger toutes les routes de ce routeur
)

# --- Pydantic Schemas ---
class APIKeyCreate(BaseModel):
    description: str = None

class APIKeyResponse(BaseModel):
    key_prefix: str
    created_at: datetime  # Changé de security.datetime à datetime
    description: str | None = None
    last_used_at: datetime | None = None  # Changé de security.datetime à datetime
    is_active: bool

    class Config:
        orm_mode = True  # Permet de mapper directement depuis les modèles SQLAlchemy

class NewAPIKeyResponse(APIKeyResponse):
    full_key: str  # La clé complète n'est retournée qu'une seule fois

class APIKeyValidationRequest(BaseModel):
    api_key: str

class ValidatedAPIKeyInfo(BaseModel):
    user_id: int
    key_prefix: str  # Renvoyer le préfixe pour le logging côté service appelant
    description: str | None = None
    # On pourrait ajouter d'autres infos utilisateur si nécessaire, comme le rôle, les permissions, etc.

# --- Helper Functions ---
def generate_api_key_pair():
    """Génère une clé API brute et sa version hachée."""
    api_key = secrets.token_urlsafe(32)  # Génère une clé de 32 bytes, URL-safe
    hashed_key = hashlib.sha256(api_key.encode()).hexdigest()
    return api_key, hashed_key

# --- API Key Routes ---
@router.post("", response_model=NewAPIKeyResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(
    api_key_data: APIKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user)  # Changé ici
):
    """
    Crée une nouvelle clé API pour l'utilisateur actuellement authentifié.
    La clé complète est retournée UNIQUEMENT lors de la création.
    """
    raw_key, hashed_api_key = generate_api_key_pair()
    key_prefix = raw_key[:8]  # Utiliser les 8 premiers caractères comme préfixe

    # Vérifier si le préfixe existe déjà (très improbable, mais bonne pratique)
    existing_key = db.query(APIKey).filter(APIKey.key_prefix == key_prefix).first()
    if existing_key:
        # Gérer la collision, par exemple en régénérant ou en levant une erreur
        logger.error(f"Collision de préfixe de clé API pour {key_prefix}. Cela ne devrait pas arriver.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur lors de la génération de la clé API. Veuillez réessayer.")

    db_api_key = APIKey(
        key_prefix=key_prefix,
        hashed_key=hashed_api_key,
        user_id=current_user.id,
        description=api_key_data.description
    )
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)

    return NewAPIKeyResponse(
        full_key=raw_key,  # Important: retourner la clé brute ici
        key_prefix=db_api_key.key_prefix,
        created_at=db_api_key.created_at,
        description=db_api_key.description,
        last_used_at=db_api_key.last_used_at,
        is_active=db_api_key.is_active
    )

@router.get("", response_model=List[APIKeyResponse])
def list_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user)  # Changé ici
):
    """Liste toutes les clés API pour l'utilisateur actuellement authentifié."""
    api_keys = db.query(APIKey).filter(APIKey.user_id == current_user.id).all()
    return api_keys

@router.delete("/{key_prefix}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(
    key_prefix: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user)  # Changé ici
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
        logger.error(f"Erreur DB lors de la suppression de la clé API {key_prefix}: {e}")
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

@internal_router.post("/validate", response_model=ValidatedAPIKeyInfo)
async def validate_api_key_internal(
    payload: APIKeyValidationRequest,
    db: Session = Depends(get_db)
):
    raw_key = payload.api_key
    
    # Hacher la clé brute fournie pour la comparaison
    hashed_raw_key = hashlib.sha256(raw_key.encode()).hexdigest()
    
    # Rechercher la clé par son hash. C'est la méthode la plus sûre.
    potential_key = None
    try:
        potential_key = db.query(APIKey).filter(APIKey.hashed_key == hashed_raw_key).first()
    except Exception as e:  # Remplacé SQLAlchemyError par Exception générique
        logger.error(f"Erreur DB lors de la recherche de la clé API par hash ({hashed_raw_key[:10]}...): {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Erreur de service lors de la validation de la clé API.")

    if not potential_key:
        logger.info(f"Validation interne : Clé API avec hachage {hashed_raw_key[:10]}... non trouvée.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Clé API invalide ou non trouvée.")

    if not potential_key.is_active:
        logger.warning(f"Validation interne : Clé API {potential_key.key_prefix} (utilisateur {potential_key.user_id}) est inactive.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="La clé API est inactive.")

    # Mettre à jour last_used_at
    try:
        current_time_utc = datetime.utcnow()  # Utiliser UTC pour la cohérence
        
        stmt = (
            update(APIKey)
            .where(APIKey.id == potential_key.id)
            .values(last_used_at=current_time_utc)
        )
        db.execute(stmt)
        db.commit()
        logger.info(f"Clé API {potential_key.key_prefix} (utilisateur {potential_key.user_id}) validée. last_used_at mis à jour.")
    except Exception as e:  # Remplacé SQLAlchemyError par Exception générique
        db.rollback()
        logger.error(f"Erreur DB lors de la mise à jour de last_used_at pour la clé {potential_key.key_prefix}: {e}")
        # Ne pas bloquer la validation si cette mise à jour échoue, mais enregistrer l'erreur.
        # Une alternative serait de lever une HTTP 500 si cette mise à jour est critique.

    return ValidatedAPIKeyInfo(
        user_id=potential_key.user_id,
        key_prefix=potential_key.key_prefix,
        description=potential_key.description
    )