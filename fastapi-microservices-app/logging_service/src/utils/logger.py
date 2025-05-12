from datetime import datetime
import logging
import os

# Configure the logger
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = os.getenv("LOG_FILE", "app.log")

# Renamed to be callable from main.py
def setup_logging():
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )

logger = logging.getLogger(__name__)

def log_event(event: str, level: str = "INFO"):
    """Log an event with the specified level."""
    if level.upper() == "DEBUG":
        logger.debug(event)
    elif level.upper() == "INFO":
        logger.info(event)
    elif level.upper() == "WARNING":
        logger.warning(event)
    elif level.upper() == "ERROR":
        logger.error(event)
    elif level.upper() == "CRITICAL":
        logger.critical(event)
    else:
        logger.info(event)  # Default to INFO level if level is unknown

def log_request(request):
    """Log details of an incoming request."""
    log_event(f"Request: {request.method} {request.url} - Body: {request.body()}")

def log_response(response):
    """Log details of an outgoing response."""
    log_event(f"Response: {response.status_code} - Body: {response.body}")