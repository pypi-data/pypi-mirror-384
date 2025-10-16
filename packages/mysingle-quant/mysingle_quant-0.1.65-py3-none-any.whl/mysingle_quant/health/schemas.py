"""Health check utilities and endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    timestamp: datetime
    service: str
    version: str
    uptime: float
    checks: dict[str, dict[str, Any]]
