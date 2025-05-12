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

app = FastAPI()

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