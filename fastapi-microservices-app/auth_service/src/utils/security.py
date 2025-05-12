from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import logging

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

# Clé secrète pour l'encodage et le décodage JWT
SECRET_KEY = "your_secret_key"  # Change this to a secure random key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Ajout de oauth2_scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # Relatif aux routes du auth_service

class TokenData(BaseModel):
    email: Optional[str] = None # Le 'sub' dans le JWT sera l'email

def hash_password(password: str) -> str:
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.error(f"Erreur lors du hachage du mot de passe: {e}")
        # En cas d'erreur, retourner un hachage simple (NON SÉCURISÉ, JUSTE POUR DÉMONSTRATION)
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du mot de passe: {e}")
        # En cas d'erreur, vérifier avec le hachage simple (NON SÉCURISÉ, JUSTE POUR DÉMONSTRATION)
        import hashlib
        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

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

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    # Actuellement, le modèle User n'a pas de champ is_active.
    # Si vous l'ajoutez, décommentez et ajustez la logique ci-dessous.
    # if not current_user.is_active:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user