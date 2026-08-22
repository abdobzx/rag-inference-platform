from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..models.user import User
from ..utils import security
from ..utils.email_utils import send_verification_email
from ..database import get_db
from ..exceptions import (
    UserAlreadyExistsError,
    InvalidEmailDomainError,
    EmailServiceError,
    DatabaseConnectionError
)
from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional
import re
import html
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

ALLOWED_EMAIL_DOMAIN = "@mysothemalab.com"
VERIFICATION_CODE_EXPIRE_MINUTES = 15

USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,30}$')
PASSWORD_PATTERN = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')
VERIFICATION_CODE_PATTERN = re.compile(r'^\d{6}$')


def sanitize_string(value: str) -> str:
    """Sanitize input to prevent XSS: strip, HTML-escape, drop script tags/javascript: URIs."""
    if not isinstance(value, str):
        return value
    sanitized = html.escape(value.strip())
    sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
    return sanitized


class UserCreate(BaseModel):
    username: str = Field(
        min_length=3, max_length=30, pattern=r'^[a-zA-Z0-9_-]+$',
        description="Username must be 3-30 characters, alphanumeric with underscores and hyphens"
    )
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(
        min_length=8, max_length=128,
        description="Password must be 8-128 characters with uppercase, lowercase, digit, and special character"
    )
    full_name: Optional[str] = Field(
        None, min_length=1, max_length=100,
        description="Full name (optional, 1-100 characters)"
    )

    @validator('username')
    def validate_username(cls, v):
        if not USERNAME_PATTERN.match(v):
            raise ValueError(
                'Username must be 3-30 characters long and contain only letters, numbers, underscores, and hyphens'
            )
        return sanitize_string(v)

    @validator('email')
    def validate_email_domain(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError('Email is required')
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(v):
            raise ValueError('Invalid email format')
        if not v.endswith(ALLOWED_EMAIL_DOMAIN):
            raise ValueError(f'Email must belong to the {ALLOWED_EMAIL_DOMAIN} domain')
        return sanitize_string(v).lower()

    @validator('password')
    def validate_password_strength(cls, v):
        if not PASSWORD_PATTERN.match(v):
            raise ValueError(
                'Password must be at least 8 characters long and contain at least one uppercase letter, '
                'one lowercase letter, one digit, and one special character (@$!%*?&)'
            )
        return v  # never sanitize/transform the password itself

    @validator('full_name')
    def validate_full_name(cls, v):
        return sanitize_string(v) if v is not None else v


class VerifyEmailRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address to verify")
    code: str = Field(
        min_length=6, max_length=6, pattern=r'^\d{6}$',
        description="6-digit verification code"
    )

    @validator('email')
    def validate_email(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError('Email is required')
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(v):
            raise ValueError('Invalid email format')
        return sanitize_string(v).lower()

    @validator('code')
    def validate_verification_code(cls, v):
        if not VERIFICATION_CODE_PATTERN.match(v):
            raise ValueError('Verification code must be exactly 6 digits')
        return v


router = APIRouter()


@router.post("/auth/register")
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Registration attempt for username={user_data.username} email={user_data.email}")

    if db.query(User).filter(User.email == user_data.email).first():
        logger.warning(f"Registration attempt with existing email: {user_data.email}")
        raise UserAlreadyExistsError(
            message="This email is already registered.",
            details={"field": "email", "value": user_data.email}
        )

    if db.query(User).filter(User.username == user_data.username).first():
        logger.warning(f"Registration attempt with existing username: {user_data.username}")
        raise UserAlreadyExistsError(
            message="This username is already taken.",
            details={"field": "username", "value": user_data.username}
        )

    try:
        hashed_password = security.hash_password(user_data.password)
        verification_code = security.generate_verification_code()
        verification_code_expires_at = datetime.utcnow() + timedelta(minutes=VERIFICATION_CODE_EXPIRE_MINUTES)

        new_user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            is_verified=False,
            verification_code=verification_code,
            verification_code_expires_at=verification_code_expires_at
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        email_sent = send_verification_email(
            to_email=new_user.email,
            verification_code=verification_code,
            username=new_user.username
        )

        if not email_sent:
            logger.error(f"Failed to send verification email to {new_user.email}.")
            raise EmailServiceError(
                message="Failed to send the verification email. Please contact support.",
                details={"email": new_user.email}
            )

        logger.info(f"User registered: {new_user.email}. Verification email sent.")

        return {
            "message": "User registered successfully. Check your email for the verification code.",
            "user_id": new_user.id,
            "email": new_user.email,
        }
    except ValueError as ve:
        logger.error(f"Validation error during registration: {ve}")
        raise InvalidEmailDomainError(
            message=str(ve),
            details={"email": user_data.email}
        )
    except (EmailServiceError, UserAlreadyExistsError, InvalidEmailDomainError):
        raise
    except Exception as e:
        logger.error(f"Error registering user {user_data.username}: {e}", exc_info=True)
        db.rollback()
        raise DatabaseConnectionError(
            message="Internal server error during registration.",
            details={"username": user_data.username}
        )


@router.post("/auth/verify-email")
def verify_email(request_data: VerifyEmailRequest, db: Session = Depends(get_db)):
    logger.info(f"Email verification attempt for: {request_data.email}")
    user = db.query(User).filter(User.email == request_data.email).first()

    if not user:
        logger.warning(f"Verification attempt for unknown email: {request_data.email}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    is_verified = bool(user.is_verified)  # type: ignore
    verification_code = str(user.verification_code) if user.verification_code else None  # type: ignore
    expires_at = user.verification_code_expires_at  # type: ignore

    if is_verified:
        logger.info(f"Email already verified for: {request_data.email}")
        return {"message": "This email is already verified."}

    if verification_code != request_data.code:
        logger.warning(f"Invalid verification code for: {request_data.email}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code.")

    if expires_at and datetime.utcnow() > expires_at:
        logger.warning(f"Expired verification code for: {request_data.email}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification code expired.")

    user.is_verified = True  # type: ignore
    user.verification_code = None  # type: ignore
    user.verification_code_expires_at = None  # type: ignore
    db.commit()

    logger.info(f"Email verified successfully for: {request_data.email}")
    return {"message": "Email verified successfully. You can now log in."}


@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    logger.info(f"Login attempt for email: {form_data.username}")
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not security.verify_password(form_data.password, str(user.hashed_password)):  # type: ignore
        logger.warning(f"Failed login attempt for email: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not bool(user.is_verified):  # type: ignore
        logger.warning(f"Login blocked, email not verified: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in. A code was sent at registration.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email, "user_id": user.id}, expires_delta=access_token_expires
    )
    logger.info(f"Login successful, token issued for: {user.email}")
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id, "email": user.email}
