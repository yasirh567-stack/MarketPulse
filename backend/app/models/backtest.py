from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, utcnow


class BacktestRun(Base):
    """A stored backtest result: config in, metrics + curves + trades out.

    All series (equity curve, benchmark curve, trades, monthly returns) are
    stored as JSON text — they're small (one run == one ticker/date-range) and
    always read back wholesale for the results page, so a normalized trade
    table would add joins without a real benefit at this scale.
    """

    __tablename__ = "backtest_runs"
    __table_args__ = (Index("ix_backtest_runs_ticker_created", "ticker", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="completed")
    config_json: Mapped[str] = mapped_column(Text, nullable=False)
    metrics_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    equity_curve_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    benchmark_curve_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    drawdown_curve_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    trades_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    monthly_returns_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
