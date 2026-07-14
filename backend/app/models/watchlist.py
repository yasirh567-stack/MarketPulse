from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, utcnow


class Watchlist(Base):
    """An anonymous watchlist keyed by a client-generated browser identifier
    (stored in localStorage). No account/auth is required for the initial
    release, per spec — authentication can be layered on later without
    changing this shape (a real user would just get their own owner_key)."""

    __tablename__ = "watchlists"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_key: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    items: Mapped[list[WatchlistItem]] = relationship(
        back_populates="watchlist", cascade="all, delete-orphan"
    )


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"
    __table_args__ = (Index("ix_watchlist_items_unique", "watchlist_id", "ticker", unique=True),)

    id: Mapped[int] = mapped_column(primary_key=True)
    watchlist_id: Mapped[int] = mapped_column(ForeignKey("watchlists.id"), nullable=False)
    ticker: Mapped[str] = mapped_column(String(16), nullable=False)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    watchlist: Mapped[Watchlist] = relationship(back_populates="items")
