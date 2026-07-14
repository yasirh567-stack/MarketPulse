from __future__ import annotations

import json
from dataclasses import replace

import pandas as pd
from sqlalchemy.orm import Session

from app.backtesting.engine import BacktestConfig, BacktestResult, run_backtest
from app.backtesting.signal_generator import SignalSeries, build_oos_signal_series
from app.core.config import Settings
from app.core.errors import InsufficientDataError
from app.ml.service import load_bars_frame, prepare_dataset
from app.models.backtest import BacktestRun

MIN_SAMPLES_FOR_BACKTEST = 80


def _build_signal_and_prices(
    db: Session, settings: Settings, ticker: str, model_name: str
) -> tuple[SignalSeries, pd.Series, pd.Series]:
    """Shared, expensive first step for both a single backtest and a
    threshold sweep: builds the walk-forward out-of-sample signal exactly
    once and aligns open/close prices to it. Everything downstream
    (`run_backtest`) is a cheap simulation loop given this signal."""
    dataset = prepare_dataset(db, settings, ticker)
    if len(dataset.X) < MIN_SAMPLES_FOR_BACKTEST:
        raise InsufficientDataError(
            f"Only {len(dataset.X)} usable trading days are available for {ticker} "
            f"(minimum required for a backtest: {MIN_SAMPLES_FOR_BACKTEST})."
        )
    signal = build_oos_signal_series(dataset, model_name)
    bars_df = load_bars_frame(db, settings, ticker)
    open_prices = bars_df["open"].reindex(signal.dates)
    close_prices = bars_df["close"].reindex(signal.dates)
    return signal, open_prices, close_prices


def run_and_persist_backtest(
    db: Session, settings: Settings, config: BacktestConfig
) -> BacktestRun:
    ticker = config.ticker.upper()
    signal, open_prices, close_prices = _build_signal_and_prices(
        db, settings, ticker, config.model_name
    )

    result = run_backtest(
        dates=signal.dates,
        open_prices=open_prices,
        close_prices=close_prices,
        probability_up=signal.probability_up,
        sentiment_avg_5d=signal.sentiment_avg_5d,
        config=config,
    )

    run = BacktestRun(
        ticker=ticker,
        status="completed",
        config_json=json.dumps(config.__dict__, default=str),
        metrics_json=json.dumps(result.metrics),
        equity_curve_json=json.dumps(result.equity_curve),
        benchmark_curve_json=json.dumps(result.benchmark_curve),
        drawdown_curve_json=json.dumps(result.drawdown_curve),
        trades_json=json.dumps(result.trades),
        monthly_returns_json=json.dumps(result.monthly_returns),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def get_backtest(db: Session, run_id: int) -> BacktestRun | None:
    return db.get(BacktestRun, run_id)


def run_threshold_sweep(
    db: Session, settings: Settings, base_config: BacktestConfig, thresholds: list[float]
) -> list[BacktestResult]:
    """Runs the same strategy at several `prob_threshold` values against the
    SAME out-of-sample signal, computed only once — answers "does only
    trading when the model is more confident actually improve risk-adjusted
    returns, or just mean fewer trades with no edge?" without retraining
    anything per threshold.

    Deliberately not persisted (no BacktestRun rows) — the expensive part
    (`_build_signal_and_prices`) runs exactly once regardless of how many
    thresholds are swept, so there is no caching benefit to storing results,
    unlike a single `POST /backtests` call.
    """
    ticker = base_config.ticker.upper()
    signal, open_prices, close_prices = _build_signal_and_prices(
        db, settings, ticker, base_config.model_name
    )
    return [
        run_backtest(
            dates=signal.dates,
            open_prices=open_prices,
            close_prices=close_prices,
            probability_up=signal.probability_up,
            sentiment_avg_5d=signal.sentiment_avg_5d,
            config=replace(base_config, prob_threshold=t),
        )
        for t in thresholds
    ]
