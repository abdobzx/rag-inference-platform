from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging

logger = logging.getLogger(__name__)

# Si DATABASE_URL n'est pas défini, utilisez SQLite comme base de données par défaut
# Dans le docker-compose, nous définirons cette variable pour utiliser PostgreSQL
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")

# Configuration de connexion pour SQLite
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

# Création du moteur SQLAlchemy
try:
    logger.info(f"Tentative de connexion à la base de données: {SQLALCHEMY_DATABASE_URL}")
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
    logger.info("Connexion à la base de données établie avec succès.")
except Exception as e:
    logger.error(f"Erreur de connexion à la base de données: {e}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
