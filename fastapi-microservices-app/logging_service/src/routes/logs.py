from fastapi import APIRouter, HTTPException
from typing import List
from ..utils.logger import log_event

router = APIRouter()

# In-memory log storage for demonstration purposes
logs = []

@router.post("/logs/", response_model=dict)
def create_log(log_entry: str) -> dict:
    log_event(log_entry)  # Log the event using the utility function
    logs.append(log_entry)
    return {"message": "Log entry created successfully."}

@router.get("/logs/", response_model=List[str])
def get_logs() -> List[str]:
    if not logs:
        raise HTTPException(status_code=404, detail="No logs found.")
    return logs