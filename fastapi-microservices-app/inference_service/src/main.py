from fastapi import FastAPI
from .routes.inference import router as inference_router
from .utils.model_loader import load_model
import logging

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load the model at startup
model = load_model()

@app.on_event("startup")
async def startup_event():
    logging.info("Inference service is starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    logging.info("Inference service is shutting down...")

# Include the inference routes
app.include_router(inference_router)