from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..models.user import User
from ..utils import security  # security contient maintenant generate_verification_code
from ..utils.email_utils import send_verification_email  # Import de la fonction d'envoi d'email
from ..database import get_db
from pydantic import BaseModel, EmailStr, validator  # Ajout de EmailStr et validator
import logging
from datetime import datetime, timedelta  # Ajout de datetime et timedelta

# Configuration des logs
logger = logging.getLogger(__name__)

# Domaines email autorisés
ALLOWED_EMAIL_DOMAIN = "@mysothemalab.com"  # Corrigé ici
VERIFICATION_CODE_EXPIRE_MINUTES = 15

class UserCreate(BaseModel):
    username: str
    email: EmailStr  # Utiliser EmailStr pour une validation basique de l'email
    password: str
    full_name: str = None

    @validator('email')
    def validate_email_domain(cls, v):
        if not v.endswith(ALLOWED_EMAIL_DOMAIN):
            raise ValueError(f"L'adresse e-mail doit appartenir au domaine {ALLOWED_EMAIL_DOMAIN}")
        return v

class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str

router = APIRouter()

@router.post("/auth/register")
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Tentative d'enregistrement pour l'utilisateur: {user_data.username} avec email: {user_data.email}")
    
    # Vérification si l'email ou username existe déjà
    existing_user_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_user_email:
        logger.warning(f"Tentative d'enregistrement avec un email déjà existant: {user_data.email}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cet email est déjà enregistré.")
    
    existing_user_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_user_username:
        logger.warning(f"Tentative d'enregistrement avec un nom d'utilisateur déjà existant: {user_data.username}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ce nom d'utilisateur est déjà pris.")

    try:
        hashed_password = security.hash_password(user_data.password)
        verification_code = security.generate_verification_code()
        verification_code_expires_at = datetime.utcnow() + timedelta(minutes=VERIFICATION_CODE_EXPIRE_MINUTES)
        
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            is_verified=False,  # L'utilisateur n'est pas vérifié au moment de l'inscription
            verification_code=verification_code,
            verification_code_expires_at=verification_code_expires_at
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Envoi de l'email de vérification
        email_sent = send_verification_email(
            to_email=new_user.email, 
            verification_code=verification_code, 
            username=new_user.username
        )
        
        if not email_sent:
            logger.error(f"Échec de l'envoi de l'e-mail de vérification à {new_user.email}. L'utilisateur devra peut-être vérifier manuellement ou réessayer.")
            return {
                "message": "Utilisateur enregistré avec succès, mais l'envoi de l'e-mail de vérification a échoué. Veuillez contacter le support si vous ne recevez pas d'e-mail.", 
                "user_id": new_user.id, 
                "email": new_user.email,
                "verification_code_for_dev_only": verification_code  # Garder pour le dev si l'email échoue
            }

        logger.info(f"UTILISATEUR ENREGISTRÉ: {new_user.email}. Email de vérification envoyé.")
        
        return {"message": "Utilisateur enregistré avec succès. Veuillez vérifier votre e-mail pour le code de vérification.", "user_id": new_user.id, "email": new_user.email}
    except ValueError as ve:  # Capturer l'erreur de validation de domaine
        logger.error(f"Erreur de validation lors de l'enregistrement: {ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement de l'utilisateur {user_data.username}: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erreur interne du serveur lors de l'enregistrement.")

@router.post("/auth/verify-email")
def verify_email(request_data: VerifyEmailRequest, db: Session = Depends(get_db)):
    logger.info(f"Tentative de vérification d'email pour: {request_data.email} avec le code: {request_data.code}")
    user = db.query(User).filter(User.email == request_data.email).first()

    if not user:
        logger.warning(f"Tentative de vérification pour un email non trouvé: {request_data.email}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé.")

    if user.is_verified:
        logger.info(f"Email déjà vérifié pour: {request_data.email}")
        return {"message": "Cet e-mail est déjà vérifié."}

    if user.verification_code != request_data.code:
        logger.warning(f"Code de vérification invalide pour: {request_data.email}. Attendu: {user.verification_code}, Reçu: {request_data.code}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code de vérification invalide.")

    if datetime.utcnow() > user.verification_code_expires_at:
        logger.warning(f"Code de vérification expiré pour: {request_data.email}. Expiré à: {user.verification_code_expires_at}")
        # Optionnel : Renvoyer un nouveau code ou demander à l'utilisateur de s'inscrire à nouveau / demander un nouveau code
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code de vérification expiré.")

    user.is_verified = True
    user.verification_code = None  # Effacer le code après utilisation
    user.verification_code_expires_at = None
    db.commit()
    
    logger.info(f"Email vérifié avec succès pour: {request_data.email}")
    return {"message": "E-mail vérifié avec succès. Vous pouvez maintenant vous connecter."}


@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    logger.info(f"Tentative de connexion pour l'email: {form_data.username}")  # form_data.username est l'email ici
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user:
        logger.warning(f"Tentative de connexion échouée: Utilisateur non trouvé pour l'email {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not security.verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Tentative de connexion échouée: Mot de passe incorrect pour l'email {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect.",  # Message générique pour la sécurité
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_verified:
        logger.warning(f"Tentative de connexion échouée: Email non vérifié pour {form_data.username}")
        # Optionnel: Renvoyer un message plus spécifique ou permettre de renvoyer un code de vérification
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,  # 403 Forbidden
            detail="Veuillez vérifier votre e-mail avant de vous connecter. Un code vous a été envoyé lors de l'inscription.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email, "user_id": user.id}, expires_delta=access_token_expires  # Ajout de user_id au token
    )
    logger.info(f"Connexion réussie et token généré pour: {user.email}")
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id, "email": user.email}