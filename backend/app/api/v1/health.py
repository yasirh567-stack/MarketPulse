from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import AppSettings, DbSession
from app.nlp.sentiment import FINBERT_MODEL_NAME, VADER_MODEL_NAME, finbert_available
from app.schemas.health import HealthResponse, ProviderStatus
from app.services import provider_health_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(db: DbSession, settings: AppSettings) -> HealthResponse:
    try:
        db.execute(text("SELECT 1"))
        database_ok = True
    except Exception:
        database_ok = False

    finbert_ok = settings.enable_finbert and finbert_available()

    providers = provider_health_service.get_all(db)
    return HealthResponse(
        status="ok" if database_ok else "degraded",
        demo_mode=settings.demo_mode,
        environment=settings.environment,
        database_ok=database_ok,
        active_sentiment_model=FINBERT_MODEL_NAME if finbert_ok else VADER_MODEL_NAME,
        finbert_available=finbert_ok,
        providers=[
            ProviderStatus(
                name=p.provider_name,
                status=p.status,
                last_success_at=p.last_success_at.isoformat() if p.last_success_at else None,
                last_failure_at=p.last_failure_at.isoformat() if p.last_failure_at else None,
                last_error=p.last_error,
            )
            for p in providers
        ],
    )
