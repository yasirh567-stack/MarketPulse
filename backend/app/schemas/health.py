from __future__ import annotations

from pydantic import BaseModel


class ProviderStatus(BaseModel):
    name: str
    status: str
    last_success_at: str | None
    last_failure_at: str | None
    last_error: str | None


class HealthResponse(BaseModel):
    status: str
    demo_mode: bool
    environment: str
    database_ok: bool
    active_sentiment_model: str
    finbert_available: bool
    providers: list[ProviderStatus]
    version: str = "0.1.0"
