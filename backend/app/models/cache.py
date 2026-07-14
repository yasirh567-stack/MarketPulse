from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, utcnow


class CacheEntry(Base):
    """DB-backed TTL cache used when Redis is not configured. Redis remains a
    drop-in optional accelerator (see app.core.cache), never a hard dependency."""

    __tablename__ = "cache_entries"

    key: Mapped[str] = mapped_column(String(300), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
