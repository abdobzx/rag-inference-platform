from sqlalchemy import Column, Integer, String, Boolean, DateTime  # Ajout de Boolean et DateTime
from sqlalchemy.orm import relationship  # Importer relationship
from ..database import Base
import datetime  # Importer datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    
    is_active = Column(Boolean, default=True)  # Généralement utile
    is_verified = Column(Boolean, default=False)  # Pour la vérification d'email
    verification_code = Column(String, nullable=True)  # Code envoyé par email
    verification_code_expires_at = Column(DateTime, nullable=True)  # Expiration du code

    # Relation avec les clés API
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")