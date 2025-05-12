from fastapi import FastAPI, Request  # Request ajouté
from .routes.inference import router as inference_router
from .utils.model_loader import load_model
import logging

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  # Utiliser un logger nommé

@app.on_event("startup")
async def startup_event():
    logger.info("Inference service is starting up... Loading model.")
    # Pour l'instant, charge le PlaceholderModel car aucun model_path n'est fourni.
    # Si vous aviez un fichier modèle, par exemple dans src/models/your_model.joblib :
    # app.state.model = load_model("src/models/your_model.joblib")
    # Assurez-vous que le chemin est correct *à l'intérieur du conteneur*.
    app.state.model = load_model()
    if app.state.model:
        logger.info("Model stored in app.state.model.")
    else:
        # Ne devrait pas se produire avec le PlaceholderModel
        logger.error("Failed to load model into app.state.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Inference service is shutting down...")

# Inclure les routes d'inférence
app.include_router(inference_router)

@app.get("/")
def read_root():
    return {"message": "Inference Service is running."}