from fastapi import FastAPI, Request
from .routes.inference import router as inference_router
# Changement ici : importer la nouvelle fonction de chargement
from .utils.model_loader import load_model_and_tokenizer 
import logging

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    logger.info("Service d'inférence en cours de démarrage... Chargement du modèle et du tokenizer.")
    try:
        # Charger le modèle et le tokenizer au démarrage
        # Le nom du modèle (par ex. "distilgpt2") est codé en dur dans load_model_and_tokenizer pour l'instant
        model, tokenizer = load_model_and_tokenizer()
        app.state.model = model
        app.state.tokenizer = tokenizer
        if app.state.model and app.state.tokenizer:
            logger.info("Modèle et tokenizer stockés dans app.state.")
        else:
            # Ce cas ne devrait pas se produire si load_model_and_tokenizer lève une exception en cas d'échec
            logger.error("Échec du chargement du modèle et/ou du tokenizer dans app.state.")
            # Vous pourriez vouloir arrêter l'application ici si le modèle est critique
    except Exception as e:
        logger.error(f"Erreur critique lors du chargement du modèle au démarrage: {e}", exc_info=True)
        # Gérer l'échec du chargement du modèle - par exemple, arrêter l'application
        # ou fonctionner en mode dégradé si possible.
        # Pour l'instant, nous laissons l'application démarrer, mais les requêtes d'inférence échoueront.
        app.state.model = None
        app.state.tokenizer = None

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Inference service is shutting down...")

# Inclure les routes d'inférence
app.include_router(inference_router)

@app.get("/")
def read_root():
    return {"message": "Inference Service is running."}