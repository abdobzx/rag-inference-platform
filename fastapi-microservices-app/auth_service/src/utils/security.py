from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Configuration for password hashing
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    logger.info("Configuration réussie de CryptContext avec bcrypt")
except Exception as e:
    logger.error(f"Erreur lors de la configuration de CryptContext: {e}")
    # Fallback à un hachage plus simple si bcrypt échoue
    pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
    logger.warning("Utilisation de sha256_crypt comme fallback pour le hachage des mots de passe")

# Secret key for JWT encoding and decoding
SECRET_KEY = "your_secret_key"  # Change this to a secure random key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

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