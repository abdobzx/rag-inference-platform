from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import logging
import os
import random
import string

# Imports ajoutés
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel # Ajouté pour TokenData

# Import des dépendances locales (à ajuster si les chemins relatifs sont incorrects)
# Ces imports supposent que security.py est dans src/utils/
from ..database import get_db
from ..models.user import User

logger = logging.getLogger(__name__)

# Configuration pour le hachage des mots de passe
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    logger.info("Configuration réussie de CryptContext avec bcrypt")
except Exception as e:
    logger.error(f"Erreur lors de la configuration de CryptContext: {e}")
    # Fallback à un hachage plus simple si bcrypt échoue
    pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
    logger.warning("Utilisation de sha256_crypt comme fallback pour le hachage des mots de passe")

# JWT signing secret: must come from the environment (JWT_SECRET_KEY in .env.auth).
# Never hardcode this — anyone who can read the source can forge valid tokens.
SECRET_KEY = os.environ["JWT_SECRET_KEY"]
ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 30
VERIFICATION_CODE_LENGTH = 6 # Longueur du code de vérification

# Ajout de oauth2_scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # Relatif aux routes du auth_service

class TokenData(BaseModel):
    email: Optional[str] = None # Le 'sub' dans le JWT sera l'email

def hash_password(password: str) -> str:
    # No insecure fallback: if bcrypt hashing fails, the caller must see the failure
    # rather than silently getting an unsalted, crackable hash.
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.critical(f"Password hashing failed (bcrypt unavailable/misconfigured): {e}")
        raise

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification failed: {e}")
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return {}

async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            logger.warning("Email non trouvé dans le payload JWT.")
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError as e:
        logger.error(f"Erreur de décodage JWT: {e}")
        raise credentials_exception
    
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        logger.warning(f"Utilisateur non trouvé pour l'email: {token_data.email}")
        raise credentials_exception
    return user

def generate_verification_code(length: int = VERIFICATION_CODE_LENGTH) -> str:
    """Génère un code de vérification numérique aléatoire."""
    return "".join(random.choices(string.digits, k=length))

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    # Mise à jour pour utiliser le champ is_verified que nous avons ajouté
    # et potentiellement is_active si vous l'utilisez plus tard.
    if not current_user.is_verified: # Ou `if not current_user.is_active or not current_user.is_verified:`
        logger.warning(f"Tentative d'accès par l'utilisateur non vérifié/inactif: {current_user.email}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Compte inactif ou non vérifié")
    return current_user