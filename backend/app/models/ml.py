from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, utcnow


class ModelRun(Base):
    """Metadata + validation metrics for one trained model, so predictions can
    always be traced back to exactly what data/params produced them."""

    __tablename__ = "model_runs"
    __table_args__ = (Index("ix_model_runs_ticker_trained", "ticker", "trained_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(40), nullable=False)
    train_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    train_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    n_train_samples: Mapped[int] = mapped_column(nullable=False)
    n_test_samples: Mapped[int] = mapped_column(nullable=False)
    params_json: Mapped[str] = mapped_column(Text, nullable=False)
    metrics_json: Mapped[str] = mapped_column(Text, nullable=False)
    baseline_metrics_json: Mapped[str] = mapped_column(Text, nullable=False)
    feature_names_json: Mapped[str] = mapped_column(Text, nullable=False)
    artifact_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    random_seed: Mapped[int] = mapped_column(nullable=False, default=42)
    trained_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )


class Prediction(Base):
    """A single next-period direction estimate produced by a ModelRun."""

    __tablename__ = "predictions"
    __table_args__ = (Index("ix_predictions_ticker_asof", "ticker", "as_of_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    model_run_id: Mapped[int] = mapped_column(ForeignKey("model_runs.id"), nullable=False)
    ticker: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    as_of_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    predicted_direction: Mapped[str] = mapped_column(String(8), nullable=False)  # up|down
    probability_up: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_label: Mapped[str] = mapped_column(String(16), nullable=False)
    top_features_json: Mapped[str] = mapped_column(Text, nullable=False)
    sentiment_shift_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
