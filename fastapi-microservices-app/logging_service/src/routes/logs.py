import json
import os
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..utils.logger import log_event

router = APIRouter()

# Persisted log store: a JSON-lines file, not an in-memory list. The previous
# implementation kept aggregated logs in a plain Python list, so every restart
# silently wiped the entire audit trail - inconsistent with this service's own
# README, which advertises "audit trail" and "monitoring" as its purpose.
LOG_STORE_PATH = os.getenv("LOG_STORE_PATH", "aggregated_logs.jsonl")


class LogEntry(BaseModel):
    service: str = Field(..., description="Name of the service emitting the log")
    level: str = Field("INFO", description="DEBUG, INFO, WARNING, ERROR, or CRITICAL")
    message: str = Field(..., description="Log message content")


class StoredLogEntry(LogEntry):
    timestamp: str


def _append_log(entry: StoredLogEntry) -> None:
    with open(LOG_STORE_PATH, "a", encoding="utf-8") as f:
        f.write(entry.model_dump_json() + "\n")


def _read_logs(limit: int) -> List[StoredLogEntry]:
    if not os.path.exists(LOG_STORE_PATH):
        return []
    entries: List[StoredLogEntry] = []
    with open(LOG_STORE_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(StoredLogEntry(**json.loads(line)))
            except (json.JSONDecodeError, ValueError):
                continue  # skip malformed lines rather than fail the whole read
    return entries[-limit:]


@router.post("/logs/", response_model=StoredLogEntry, status_code=201)
def create_log(entry: LogEntry) -> StoredLogEntry:
    stored = StoredLogEntry(
        timestamp=datetime.now(timezone.utc).isoformat(),
        **entry.model_dump(),
    )
    _append_log(stored)
    log_event(f"[{stored.service}] {stored.message}", level=stored.level)
    return stored


@router.get("/logs/", response_model=List[StoredLogEntry])
def get_logs(limit: int = Query(100, ge=1, le=1000)) -> List[StoredLogEntry]:
    # An empty result set is a normal state (nothing logged yet), not an error -
    # the previous implementation raised 404 here, which conflated "no data" with
    # "resource not found".
    return _read_logs(limit)
