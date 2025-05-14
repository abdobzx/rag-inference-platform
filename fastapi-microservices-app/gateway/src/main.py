from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes.gateway import router as gateway_router
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SothemaAI API Gateway",
    description="""
This is the central API Gateway for SothemaAI microservices.
It handles routing requests to the appropriate backend services, including:
- **Authentication Service**: Manages user registration, login, and API key generation.
- **Inference Service**: Provides access to AI models for text generation, embeddings, and Retrieval Augmented Generation (RAG).
- **Logging Service**: Collects and stores logs from various services.

Access to inference endpoints requires a valid API key passed in the `X-API-Key` header.
    """,
    version="1.0.0",
    contact={
        "name": "SothemaAI Support",
        "url": "http://sothema.ai/support", # Remplacez par une URL valide si disponible
        "email": "support@sothema.ai",    # Remplacez par une adresse email valide
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT", # Ou une autre licence si applicable
    }
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ajustez ceci à vos besoins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclure les routes de la passerelle
app.include_router(gateway_router)

@app.on_event("startup")
async def startup_event():
    logger.info("Gateway service is starting up...")

@app.get("/")
async def root():
    return {"message": "Welcome to the SothemaAI API Gateway"}