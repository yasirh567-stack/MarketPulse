from __future__ import annotations

import pandas as pd

from app.backtesting.engine import BacktestConfig, run_backtest


def _series(dates, values) -> pd.Series:
    return pd.Series(values, index=dates)


def _make_price_path(n=40, start=100.0, daily_step=1.0):
    dates = pd.date_range("2026-01-01", periods=n, freq="B", tz="UTC")
    closes = [start + i * daily_step for i in range(n)]
    opens = [c - 0.1 for c in closes]
    return dates, _series(dates, opens), _series(dates, closes)


def test_trade_executes_and_exits_on_holding_period():
    dates, opens, closes = _make_price_path(n=20, daily_step=1.0)
    # High probability + positive sentiment on day 0 triggers entry on day 1's open.
    proba = _series(dates, [0.9] * len(dates))
    sentiment = _series(dates, [0.5] * len(dates))

    config = BacktestConfig(
        ticker="TEST",
        start_date=None,
        end_date=None,
        prob_threshold=0.55,
        sentiment_threshold=0.0,
        exit_prob_threshold=0.1,  # low, so exit is driven by holding period, not probability
        holding_period_days=5,
        transaction_cost_bps=0,
        slippage_bps=0,
        initial_capital=10_000,
    )
    result = run_backtest(dates, opens, closes, proba, sentiment, config)
    assert result.metrics["num_trades"] >= 1
    first_trade = result.trades[0]
    assert first_trade["exit_reason"] in {"holding_period", "period_end"}


def test_transaction_costs_reduce_trade_return():
    dates, opens, closes = _make_price_path(n=20, daily_step=1.0)
    proba = _series(dates, [0.9] * len(dates))
    sentiment = _series(dates, [0.5] * len(dates))

    base_config = dict(
        ticker="TEST",
        start_date=None,
        end_date=None,
        prob_threshold=0.55,
        sentiment_threshold=0.0,
        exit_prob_threshold=0.1,
        holding_period_days=5,
        initial_capital=10_000,
    )
    no_cost = run_backtest(
        dates,
        opens,
        closes,
        proba,
        sentiment,
        BacktestConfig(**base_config, transaction_cost_bps=0, slippage_bps=0),
    )
    with_cost = run_backtest(
        dates,
        opens,
        closes,
        proba,
        sentiment,
        BacktestConfig(**base_config, transaction_cost_bps=100, slippage_bps=100),
    )

    assert with_cost.metrics["final_equity"] < no_cost.metrics["final_equity"]


def test_no_trade_when_probability_below_threshold():
    dates, opens, closes = _make_price_path(n=20, daily_step=1.0)
    proba = _series(dates, [0.4] * len(dates))  # always below threshold
    sentiment = _series(dates, [0.5] * len(dates))

    config = BacktestConfig(
        ticker="TEST",
        start_date=None,
        end_date=None,
        prob_threshold=0.55,
        sentiment_threshold=0.0,
        exit_prob_threshold=0.1,
        holding_period_days=5,
        transaction_cost_bps=0,
        slippage_bps=0,
        initial_capital=10_000,
    )
    result = run_backtest(dates, opens, closes, proba, sentiment, config)
    assert result.metrics["num_trades"] == 0
    assert result.metrics["final_equity"] == 10_000


def test_drawdown_is_nonpositive_and_zero_at_new_highs():
    dates, opens, closes = _make_price_path(n=20, daily_step=1.0)  # strictly rising
    proba = _series(dates, [0.9] * len(dates))
    sentiment = _series(dates, [0.5] * len(dates))
    config = BacktestConfig(
        ticker="TEST",
        start_date=None,
        end_date=None,
        prob_threshold=0.55,
        sentiment_threshold=0.0,
        exit_prob_threshold=0.1,
        holding_period_days=3,
        transaction_cost_bps=0,
        slippage_bps=0,
        initial_capital=10_000,
    )
    result = run_backtest(dates, opens, closes, proba, sentiment, config)
    for point in result.drawdown_curve:
        assert point["drawdown_pct"] <= 1e-9


def test_position_never_opens_using_same_day_close_it_was_signaled_on():
    """The entry fill must use the NEXT day's open, not the signal day's own
    close — otherwise the strategy would trade on information (that day's own
    close) before it was actually tradeable at that price."""
    dates, opens, closes = _make_price_path(n=10, daily_step=1.0)
    proba = _series(dates, [0.9] * len(dates))
    sentiment = _series(dates, [0.5] * len(dates))
    config = BacktestConfig(
        ticker="TEST",
        start_date=None,
        end_date=None,
        prob_threshold=0.55,
        sentiment_threshold=0.0,
        exit_prob_threshold=0.1,
        holding_period_days=2,
        transaction_cost_bps=0,
        slippage_bps=0,
        initial_capital=10_000,
    )
    result = run_backtest(dates, opens, closes, proba, sentiment, config)
    assert result.trades, "expected at least one trade"
    first_trade = result.trades[0]
    entry_date = pd.Timestamp(first_trade["entry_date"], tz="UTC")
    entry_day_open = float(opens.loc[entry_date])
    # entry price (after zero costs) should equal that day's open, not the
    # signal day's close.
    assert abs(first_trade["entry_price"] - entry_day_open) < 1e-6


def test_num_trades_non_increasing_as_prob_threshold_rises():
    """Structural property behind the confidence-threshold sweep feature:
    holding every other config field fixed, raising `prob_threshold` can only
    make the entry condition MORE restrictive, so the number of trades taken
    against the same signal must never increase as the threshold rises."""
    dates, opens, closes = _make_price_path(n=60, daily_step=0.1)
    cycle = [0.52, 0.58, 0.63, 0.68, 0.72, 0.40]
    proba = _series(dates, [cycle[i % len(cycle)] for i in range(len(dates))])
    sentiment = _series(dates, [0.5] * len(dates))

    trade_counts = []
    for threshold in [0.5, 0.55, 0.6, 0.65, 0.7]:
        config = BacktestConfig(
            ticker="TEST",
            start_date=None,
            end_date=None,
            prob_threshold=threshold,
            sentiment_threshold=0.0,
            exit_prob_threshold=0.05,
            holding_period_days=3,
            transaction_cost_bps=0,
            slippage_bps=0,
            initial_capital=10_000,
        )
        result = run_backtest(dates, opens, closes, proba, sentiment, config)
        trade_counts.append(result.metrics["num_trades"])

    assert all(a >= b for a, b in zip(trade_counts, trade_counts[1:], strict=False))
    assert trade_counts[0] > trade_counts[-1]  # sanity check: thresholds actually bind


def test_forced_exit_at_end_of_period():
    dates, opens, closes = _make_price_path(n=10, daily_step=1.0)
    proba = _series(dates, [0.9] * len(dates))
    sentiment = _series(dates, [0.5] * len(dates))
    config = BacktestConfig(
        ticker="TEST",
        start_date=None,
        end_date=None,
        prob_threshold=0.55,
        sentiment_threshold=0.0,
        exit_prob_threshold=0.01,
        holding_period_days=1000,
        transaction_cost_bps=0,
        slippage_bps=0,
        initial_capital=10_000,
    )
    result = run_backtest(dates, opens, closes, proba, sentiment, config)
    assert result.trades
    assert result.trades[-1]["exit_reason"] == "period_end"
    assert result.trades[-1]["exit_date"] == result.effective_end
