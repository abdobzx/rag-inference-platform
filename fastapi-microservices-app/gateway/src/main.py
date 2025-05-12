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
    allow_origins=["*"],  # Adjust this to your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the gateway routes
app.include_router(gateway_router)

@app.on_event("startup")
async def startup_event():
    logger.info("Gateway service is starting up...")

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI Microservices Gateway!"}