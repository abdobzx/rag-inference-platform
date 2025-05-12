from fastapi import FastAPI
from .routes.auth import router as auth_router
from .database import engine, Base
import logging

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.include_router(auth_router)

@app.on_event("startup")
async def startup_db_client():
    try:
        # Création des tables dans la base de données
        logger.info("Création des tables dans la base de données...")
        Base.metadata.create_all(bind=engine)
        logger.info("Tables créées avec succès!")
    except Exception as e:
        logger.error(f"Erreur lors de la création des tables: {e}")
        raise

@app.get("/")
def read_root():
    return {"message": "Welcome to the Auth Service"}