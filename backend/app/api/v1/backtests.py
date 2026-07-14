# NOTE: intentionally no `from __future__ import annotations` here. slowapi's
# @limiter.limit decorator resolves string annotations using its own wrapper
# module's __globals__, so postponed evaluation (PEP 563) breaks FastAPI's
# dependency/body resolution for decorated routes (params silently fall back
# to query params). Routes using @limiter.limit must keep real annotations.

import json

from fastapi import APIRouter, HTTPException, Path, Request

from app.api.deps import AppSettings, DbSession
from app.backtesting.engine import BacktestConfig
from app.backtesting.service import get_backtest, run_and_persist_backtest, run_threshold_sweep
from app.core.rate_limit import default_rate_limit, limiter
from app.models.backtest import BacktestRun
from app.schemas.backtest import (
    BacktestRequest,
    BacktestResponse,
    ThresholdSweepPoint,
    ThresholdSweepRequest,
    ThresholdSweepResponse,
)

router = APIRouter()


def _to_response(run: BacktestRun) -> BacktestResponse:
    return BacktestResponse(
        run_id=run.id,
        ticker=run.ticker,
        status=run.status,
        created_at=run.created_at,
        config=json.loads(run.config_json),
        metrics=json.loads(run.metrics_json or "{}"),
        equity_curve=json.loads(run.equity_curve_json or "[]"),
        benchmark_curve=json.loads(run.benchmark_curve_json or "[]"),
        drawdown_curve=json.loads(run.drawdown_curve_json or "[]"),
        trades=json.loads(run.trades_json or "[]"),
        monthly_returns=json.loads(run.monthly_returns_json or "[]"),
    )


@router.post("", response_model=BacktestResponse)
@limiter.limit(default_rate_limit())
def create_backtest(request: Request, body: BacktestRequest, db: DbSession, settings: AppSettings):
    config = BacktestConfig(
        ticker=body.ticker.upper(),
        start_date=body.start_date,
        end_date=body.end_date,
        prob_threshold=body.prob_threshold,
        sentiment_threshold=body.sentiment_threshold,
        exit_prob_threshold=body.exit_prob_threshold,
        holding_period_days=body.holding_period_days,
        transaction_cost_bps=body.transaction_cost_bps,
        slippage_bps=body.slippage_bps,
        initial_capital=body.initial_capital,
        model_name=body.model_name,
    )
    run = run_and_persist_backtest(db, settings, config)
    return _to_response(run)


@router.post("/threshold-sweep", response_model=ThresholdSweepResponse)
@limiter.limit(default_rate_limit())
def sweep_thresholds(
    request: Request, body: ThresholdSweepRequest, db: DbSession, settings: AppSettings
):
    """Runs the identical strategy at several confidence thresholds against
    the same out-of-sample signal — answers whether only trading when the
    model is more confident actually improves risk-adjusted returns, or just
    means fewer trades with no edge. Not persisted (see run_threshold_sweep's
    docstring); always recomputed fresh."""
    thresholds = sorted(set(body.prob_thresholds))
    config = BacktestConfig(
        ticker=body.ticker.upper(),
        start_date=body.start_date,
        end_date=body.end_date,
        prob_threshold=thresholds[0],  # placeholder — overwritten per-point below
        sentiment_threshold=body.sentiment_threshold,
        exit_prob_threshold=body.exit_prob_threshold,
        holding_period_days=body.holding_period_days,
        transaction_cost_bps=body.transaction_cost_bps,
        slippage_bps=body.slippage_bps,
        initial_capital=body.initial_capital,
        model_name=body.model_name,
    )
    results = run_threshold_sweep(db, settings, config, thresholds)
    points = [
        ThresholdSweepPoint(
            prob_threshold=t,
            sharpe_ratio=r.metrics["sharpe_ratio"],
            sortino_ratio=r.metrics["sortino_ratio"],
            total_return_pct=r.metrics["total_return_pct"],
            win_rate_pct=r.metrics["win_rate_pct"],
            num_trades=r.metrics["num_trades"],
            max_drawdown_pct=r.metrics["max_drawdown_pct"],
        )
        for t, r in zip(thresholds, results, strict=True)
    ]
    return ThresholdSweepResponse(ticker=body.ticker.upper(), thresholds=points)


@router.get("/{run_id}", response_model=BacktestResponse)
def get_backtest_result(db: DbSession, run_id: int = Path(...)):
    run = get_backtest(db, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Backtest run not found")
    return _to_response(run)
