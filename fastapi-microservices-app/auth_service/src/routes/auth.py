from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..models.user import User
from ..utils import security
from ..database import get_db
from pydantic import BaseModel
import logging

# Configuration des logs
logger = logging.getLogger(__name__)

# Définir un modèle Pydantic pour la validation des données d'enregistrement
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: str = None

router = APIRouter()

@router.post("/auth/register")
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Tentative d'enregistrement pour l'utilisateur: {user_data.username}")
    try:
        hashed_password = security.hash_password(user_data.password)
        logger.info("Mot de passe haché avec succès")
        
        new_user = User(
            username=user_data.username,
            email=user_data.email, 
            full_name=user_data.full_name, 
            hashed_password=hashed_password
        )
        logger.info("Objet utilisateur créé avec succès")
        
        db.add(new_user)
        logger.info("Utilisateur ajouté à la session DB")
        
        db.commit()
        logger.info("Transaction DB validée avec succès")
        
        db.refresh(new_user)
        logger.info("Utilisateur rafraîchi depuis la DB")
        
        return {"message": "User registered successfully", "user_id": new_user.id}
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement de l'utilisateur: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = security.timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}