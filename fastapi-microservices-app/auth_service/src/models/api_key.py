from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key_prefix = Column(String(8), unique=True, index=True, nullable=False) # Pour identification rapide, les 8 premiers caractères de la clé
    hashed_key = Column(String, nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    description = Column(String, nullable=True) # Permettre à l'utilisateur de nommer ses clés

    user = relationship("User", back_populates="api_keys")
