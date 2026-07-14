"""Declarative base shared by all ORM models."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    """Timezone-aware "now", used as the default for created_at/timestamp columns."""
    return datetime.now(UTC)
