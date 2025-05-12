from sqlalchemy import Column, Integer, String
from ..database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    # Si vous aviez un champ full_name avec SQLModel, vous pouvez l'ajouter ici aussi:
    # full_name = Column(String, nullable=True)