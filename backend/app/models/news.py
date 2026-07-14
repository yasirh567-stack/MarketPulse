from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, utcnow


class NewsArticle(Base):
    """A normalized, sanitized news headline tied to a ticker.

    `url_hash` enforces de-duplication: the same story surfaced by multiple
    RSS queries (or re-fetched later) collapses to one row.
    """

    __tablename__ = "news_articles"
    __table_args__ = (Index("ix_news_ticker_published", "ticker", "published_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    url_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    source: Mapped[str] = mapped_column(String(120), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    data_status: Mapped[str] = mapped_column(String(16), nullable=False, default="cached")
    is_demo: Mapped[bool] = mapped_column(default=False, nullable=False)


class SocialPost(Base):
    """An optional social-media post (e.g. Reddit). Empty table when the
    optional social provider is disabled — never required for the app to work."""

    __tablename__ = "social_posts"
    __table_args__ = (Index("ix_social_ticker_created", "ticker", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    external_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str | None] = mapped_column(String(120), nullable=True)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    is_demo: Mapped[bool] = mapped_column(default=False, nullable=False)
