"""Tracks per-provider health so /api/v1/health and the status page can show
real, current provider state instead of assuming everything is fine."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.base import utcnow
from app.models.provider_health import ProviderHealth


def record_success(db: Session, provider_name: str) -> None:
    row = db.scalar(select(ProviderHealth).where(ProviderHealth.provider_name == provider_name))
    now = utcnow()
    if row is None:
        row = ProviderHealth(
            provider_name=provider_name, status="ok", last_success_at=now, checked_at=now
        )
        db.add(row)
    else:
        row.status = "ok"
        row.last_success_at = now
        row.consecutive_failures = 0
        row.checked_at = now
    db.commit()


def record_failure(db: Session, provider_name: str, error: str) -> None:
    row = db.scalar(select(ProviderHealth).where(ProviderHealth.provider_name == provider_name))
    now = utcnow()
    if row is None:
        row = ProviderHealth(
            provider_name=provider_name,
            status="degraded",
            last_failure_at=now,
            last_error=error[:500],
            consecutive_failures=1,
            checked_at=now,
        )
        db.add(row)
    else:
        row.consecutive_failures += 1
        row.status = "down" if row.consecutive_failures >= 3 else "degraded"
        row.last_failure_at = now
        row.last_error = error[:500]
        row.checked_at = now
    db.commit()


def get_all(db: Session) -> list[ProviderHealth]:
    return list(db.scalars(select(ProviderHealth)).all())
