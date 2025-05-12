from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .. import models  # Assurez-vous que models.user est accessible via models
from ..utils import security
from ..database import get_db  # Changement ici
from pydantic import BaseModel

# Définir un modèle Pydantic pour la validation des données d'enregistrement
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: str = None

router = APIRouter()

@router.post("/auth/register")
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    hashed_password = security.hash_password(user_data.password)
    new_user = models.user.User(
        username=user_data.username,
        email=user_data.email, 
        full_name=user_data.full_name, 
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "User registered successfully", "user_id": new_user.id}

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.user.User).filter(models.user.User.email == form_data.username).first()  # Assurez-vous que User a un attribut email
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = security.timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires  # Assurez-vous que User a un attribut email
    )
    return {"access_token": access_token, "token_type": "bearer"}