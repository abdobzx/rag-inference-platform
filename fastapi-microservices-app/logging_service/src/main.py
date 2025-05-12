from fastapi import FastAPI
from .routes.logs import router as logs_router
from .utils.logger import setup_logging

app = FastAPI()

# Setup logging
setup_logging()

# Include the logs router
app.include_router(logs_router)

@app.get("/")
def read_root():
    return {"message": "Logging Service is running."}