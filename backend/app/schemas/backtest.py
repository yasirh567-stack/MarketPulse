from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class BacktestRequest(BaseModel):
    ticker: str
    start_date: datetime | None = None
    end_date: datetime | None = None
    prob_threshold: float = Field(0.55, ge=0.5, le=0.95)
    sentiment_threshold: float = Field(0.0, ge=-1.0, le=1.0)
    exit_prob_threshold: float = Field(0.45, ge=0.05, le=0.5)
    holding_period_days: int = Field(5, ge=1, le=60)
    transaction_cost_bps: float = Field(10.0, ge=0, le=500)
    slippage_bps: float = Field(5.0, ge=0, le=500)
    initial_capital: float = Field(10_000.0, ge=100, le=10_000_000)
    model_name: str = "gradient_boosting"


class BacktestResponse(BaseModel):
    run_id: int
    ticker: str
    status: str
    created_at: datetime
    config: dict
    metrics: dict
    equity_curve: list[dict]
    benchmark_curve: list[dict]
    drawdown_curve: list[dict]
    trades: list[dict]
    monthly_returns: list[dict]
    disclaimer: str = (
        "These results are hypothetical, based on historical/demo data and simplified execution "
        "assumptions. Past performance does not guarantee future results, and this is not "
        "financial advice."
    )


class ThresholdSweepRequest(BaseModel):
    """A variant of BacktestRequest for comparing several confidence
    thresholds against the same underlying signal. Deliberately does NOT
    subclass BacktestRequest: inheriting its singular `prob_threshold` field
    would leave an unused, ambiguous field on this request (which value
    wins?) — duplicating the shared fields explicitly is a little more
    verbose but leaves no room for that question."""

    ticker: str
    start_date: datetime | None = None
    end_date: datetime | None = None
    prob_thresholds: list[float] = Field(
        default_factory=lambda: [0.50, 0.55, 0.60, 0.65, 0.70],
        min_length=1,
        max_length=10,
    )
    sentiment_threshold: float = Field(0.0, ge=-1.0, le=1.0)
    exit_prob_threshold: float = Field(0.45, ge=0.05, le=0.5)
    holding_period_days: int = Field(5, ge=1, le=60)
    transaction_cost_bps: float = Field(10.0, ge=0, le=500)
    slippage_bps: float = Field(5.0, ge=0, le=500)
    initial_capital: float = Field(10_000.0, ge=100, le=10_000_000)
    model_name: str = "gradient_boosting"


class ThresholdSweepPoint(BaseModel):
    prob_threshold: float
    sharpe_ratio: float
    sortino_ratio: float
    total_return_pct: float
    win_rate_pct: float
    num_trades: int
    max_drawdown_pct: float


class ThresholdSweepResponse(BaseModel):
    ticker: str
    thresholds: list[ThresholdSweepPoint]
    disclaimer: str = (
        "These results are hypothetical, based on historical/demo data and simplified execution "
        "assumptions. Past performance does not guarantee future results, and this is not "
        "financial advice."
    )
