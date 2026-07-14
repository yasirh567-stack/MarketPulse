"""Event-driven backtest simulator for a sentiment+probability threshold
strategy, benchmarked against buy-and-hold.

Strategy (configurable):
  - Enter long at the NEXT bar's open when, using ONLY information known as
    of today's close (an out-of-sample model probability + trailing
    sentiment), probability_up > prob_threshold AND sentiment_avg_5d >
    sentiment_threshold.
  - Exit at the next bar's open when ANY of: holding_period_days elapsed,
    probability_up has fallen below exit_prob_threshold, or the test period
    has ended (forced close-out — never left open past the data).

Every decision at "day t" only ever reads data with index <= t from the
out-of-sample signal series (itself already walk-forward/no-look-ahead, see
signal_generator.py) and executes at day t+1's open — so no trade ever fills
at a price that was not yet observable at decision time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
import pandas as pd


@dataclass
class BacktestConfig:
    ticker: str
    start_date: datetime | None
    end_date: datetime | None
    prob_threshold: float = 0.55
    sentiment_threshold: float = 0.0
    exit_prob_threshold: float = 0.45
    holding_period_days: int = 5
    transaction_cost_bps: float = 10.0  # basis points of trade value, each side
    slippage_bps: float = 5.0
    initial_capital: float = 10_000.0
    model_name: str = "gradient_boosting"


@dataclass
class Trade:
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    return_pct: float
    exit_reason: str


@dataclass
class BacktestResult:
    metrics: dict
    equity_curve: list[dict]
    benchmark_curve: list[dict]
    drawdown_curve: list[dict]
    trades: list[dict]
    monthly_returns: list[dict]
    effective_start: str
    effective_end: str
    warnings: list[str] = field(default_factory=list)


def _apply_costs(price: float, side: str, cost_bps: float, slippage_bps: float) -> float:
    total_bps = (cost_bps + slippage_bps) / 10_000.0
    return price * (1 + total_bps) if side == "buy" else price * (1 - total_bps)


def run_backtest(
    dates: pd.DatetimeIndex,
    open_prices: pd.Series,
    close_prices: pd.Series,
    probability_up: pd.Series,
    sentiment_avg_5d: pd.Series,
    config: BacktestConfig,
) -> BacktestResult:
    warnings: list[str] = []

    mask = pd.Series(True, index=dates)
    if config.start_date is not None:
        mask &= dates >= pd.Timestamp(config.start_date, tz="UTC")
    if config.end_date is not None:
        mask &= dates <= pd.Timestamp(config.end_date, tz="UTC")
    sim_dates = dates[mask]

    if len(sim_dates) < 10:
        warnings.append(
            "Fewer than 10 out-of-sample trading days are available in the requested date "
            "range; results are not statistically meaningful."
        )

    cash = config.initial_capital
    shares = 0.0
    position_open = False
    entry_price = 0.0
    entry_date: pd.Timestamp | None = None
    days_held = 0
    trades: list[Trade] = []

    equity_points: list[dict] = []
    benchmark_points: list[dict] = []

    bh_shares = config.initial_capital / open_prices.loc[sim_dates[0]] if len(sim_dates) else 0.0

    for i, date in enumerate(sim_dates):
        price_open = float(open_prices.loc[date])
        price_close = float(close_prices.loc[date])
        proba = float(probability_up.loc[date])
        sentiment = float(sentiment_avg_5d.loc[date])
        is_last_day = i == len(sim_dates) - 1

        if position_open:
            days_held += 1
            should_exit = (
                days_held >= config.holding_period_days
                or proba < config.exit_prob_threshold
                or is_last_day
            )
            if should_exit:
                exit_price = _apply_costs(
                    price_open, "sell", config.transaction_cost_bps, config.slippage_bps
                )
                cash = shares * exit_price
                trade_return = (exit_price - entry_price) / entry_price
                reason = (
                    "period_end"
                    if is_last_day
                    else (
                        "holding_period"
                        if days_held >= config.holding_period_days
                        else "probability_exit"
                    )
                )
                trades.append(
                    Trade(
                        entry_date=str(entry_date.date()),
                        exit_date=str(date.date()),
                        entry_price=round(entry_price, 4),
                        exit_price=round(exit_price, 4),
                        return_pct=round(trade_return * 100, 4),
                        exit_reason=reason,
                    )
                )
                shares = 0.0
                position_open = False
                days_held = 0

        if (
            not position_open
            and not is_last_day
            and proba > config.prob_threshold
            and sentiment > config.sentiment_threshold
        ):
            entry_price = _apply_costs(
                price_open, "buy", config.transaction_cost_bps, config.slippage_bps
            )
            shares = cash / entry_price
            cash = 0.0
            position_open = True
            entry_date = date
            days_held = 0

        portfolio_value = cash + shares * price_close
        equity_points.append({"date": date.date().isoformat(), "value": round(portfolio_value, 2)})
        benchmark_points.append(
            {"date": date.date().isoformat(), "value": round(bh_shares * price_close, 2)}
        )

    equity_series = pd.Series(
        [p["value"] for p in equity_points],
        index=[pd.Timestamp(p["date"]) for p in equity_points],
    )

    metrics = _compute_metrics(equity_series, trades, config.initial_capital)
    drawdown_curve = _drawdown_curve(equity_series)
    monthly_returns = _monthly_returns(equity_series)

    return BacktestResult(
        metrics=metrics,
        equity_curve=equity_points,
        benchmark_curve=benchmark_points,
        drawdown_curve=drawdown_curve,
        trades=[t.__dict__ for t in trades],
        monthly_returns=monthly_returns,
        effective_start=str(sim_dates[0].date()) if len(sim_dates) else "",
        effective_end=str(sim_dates[-1].date()) if len(sim_dates) else "",
        warnings=warnings,
    )


def _compute_metrics(equity: pd.Series, trades: list[Trade], initial_capital: float) -> dict:
    if len(equity) < 2:
        return {"insufficient_data": True}

    daily_returns = equity.pct_change().dropna()
    total_return = (equity.iloc[-1] / initial_capital) - 1
    n_days = len(equity)
    annualization_factor = 252 / max(n_days, 1)
    annualized_return = (
        (1 + total_return) ** annualization_factor - 1 if total_return > -1 else -1.0
    )
    annualized_vol = float(daily_returns.std() * np.sqrt(252)) if len(daily_returns) > 1 else 0.0

    sharpe = (
        float((daily_returns.mean() / daily_returns.std()) * np.sqrt(252))
        if daily_returns.std() > 0
        else 0.0
    )
    downside = daily_returns[daily_returns < 0]
    sortino = (
        float((daily_returns.mean() / downside.std()) * np.sqrt(252))
        if len(downside) > 1 and downside.std() > 0
        else 0.0
    )

    running_max = equity.cummax()
    drawdown = equity / running_max - 1
    max_drawdown = float(drawdown.min())

    winning_trades = [t for t in trades if t.return_pct > 0]
    win_rate = len(winning_trades) / len(trades) if trades else 0.0
    avg_trade = float(np.mean([t.return_pct for t in trades])) if trades else 0.0
    exposure = len(trades) and sum(
        (pd.Timestamp(t.exit_date) - pd.Timestamp(t.entry_date)).days for t in trades
    ) / max(n_days, 1)
    turnover = len(trades) * 2  # each trade = one buy + one sell

    return {
        "total_return_pct": round(total_return * 100, 4),
        "annualized_return_pct": round(annualized_return * 100, 4),
        "annualized_volatility_pct": round(annualized_vol * 100, 4),
        "sharpe_ratio": round(sharpe, 4),
        "sortino_ratio": round(sortino, 4),
        "max_drawdown_pct": round(max_drawdown * 100, 4),
        "win_rate_pct": round(win_rate * 100, 4),
        "num_trades": len(trades),
        "avg_trade_return_pct": round(avg_trade, 4),
        "exposure_pct": round((exposure or 0) * 100, 4),
        "turnover_count": turnover,
        "final_equity": round(float(equity.iloc[-1]), 2),
    }


def _drawdown_curve(equity: pd.Series) -> list[dict]:
    if equity.empty:
        return []
    running_max = equity.cummax()
    drawdown = (equity / running_max - 1) * 100
    return [
        {"date": d.date().isoformat(), "drawdown_pct": round(v, 4)} for d, v in drawdown.items()
    ]


def _monthly_returns(equity: pd.Series) -> list[dict]:
    if equity.empty:
        return []
    monthly = equity.resample("ME").last()
    monthly_returns = monthly.pct_change().dropna() * 100
    return [
        {"month": idx.strftime("%Y-%m"), "return_pct": round(val, 4)}
        for idx, val in monthly_returns.items()
    ]
