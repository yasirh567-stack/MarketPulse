"""Leakage-prevention tests for app.ml.features.

These are the most important tests in the whole ML pipeline: they assert
directly that perturbing FUTURE price bars or FUTURE news does not change any
EARLIER row's computed features, and that sentiment/event windows only ever
look at text published strictly before a bar's own close.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.ml.features import build_dataset, compute_price_features


def _make_bars(n=60, seed=7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2025-01-01", periods=n, freq="B", tz="UTC")
    prices = 100 + np.cumsum(rng.normal(0, 1, size=n))
    volumes = rng.integers(1_000_000, 5_000_000, size=n)
    return pd.DataFrame(
        {
            "open": prices,
            "high": prices + 1,
            "low": prices - 1,
            "close": prices,
            "volume": volumes,
        },
        index=dates,
    )


def test_price_features_unaffected_by_future_bar_changes():
    bars = _make_bars()
    baseline = compute_price_features(bars)

    perturbed = bars.copy()
    perturbed.iloc[-1, perturbed.columns.get_loc("close")] *= 5.0  # wildly change the LAST bar only

    perturbed_features = compute_price_features(perturbed)

    # Every row except the last must be identical — a change to the final
    # bar's close cannot affect any earlier row's rolling/lag features.
    pd.testing.assert_frame_equal(baseline.iloc[:-1], perturbed_features.iloc[:-1])


def test_label_reflects_next_bar_direction():
    bars = _make_bars(n=80)
    dataset = build_dataset(bars, sentiment_records=[], event_records=[])
    for date in dataset.dates:
        pos = bars.index.get_loc(date)
        if pos + 1 >= len(bars):
            continue
        expected_up = bars["close"].iloc[pos + 1] > bars["close"].iloc[pos]
        assert dataset.y.loc[date] == int(expected_up)


def test_sentiment_feature_ignores_articles_published_after_bar_close():
    bars = _make_bars(n=40)
    target_date = bars.index[25]  # comfortably past the rolling(20) warm-up

    # One article strictly before the bar close (should count), one strictly
    # after (must NOT count towards that bar's sentiment feature).
    sentiment_records = [
        {"published_at": target_date - pd.Timedelta(hours=1), "compound": 0.9, "label": "bullish"},
        {"published_at": target_date + pd.Timedelta(hours=1), "compound": -0.9, "label": "bearish"},
    ]
    dataset = build_dataset(bars, sentiment_records, event_records=[])
    row = dataset.X.loc[target_date]
    assert row["sentiment_avg_5d"] > 0  # only the earlier, bullish article should be visible
    assert row["article_count_5d"] == 1


def test_sentiment_feature_at_exact_close_timestamp_is_excluded():
    """A record published at exactly the bar's close timestamp must not count
    — the alignment rule is strictly-before, not before-or-equal."""
    bars = _make_bars(n=40)
    target_date = bars.index[25]  # comfortably past the rolling(20) warm-up
    sentiment_records = [{"published_at": target_date, "compound": 0.9, "label": "bullish"}]
    dataset = build_dataset(bars, sentiment_records, event_records=[])
    row = dataset.X.loc[target_date]
    assert row["article_count_5d"] == 0


def test_event_feature_ignores_events_after_bar_close():
    bars = _make_bars(n=40)
    target_date = bars.index[25]  # comfortably past the rolling(20) warm-up
    event_records = [
        {"published_at": target_date - pd.Timedelta(hours=2), "category": "earnings"},
        {"published_at": target_date + pd.Timedelta(hours=2), "category": "lawsuit"},
    ]
    dataset = build_dataset(bars, sentiment_records=[], event_records=event_records)
    row = dataset.X.loc[target_date]
    assert row["event_earnings_5d"] == 1.0
    assert row["event_lawsuit_5d"] == 0.0


def test_insufficient_history_yields_no_usable_rows():
    bars = _make_bars(n=5)  # far too short for a 20-day moving average etc.
    dataset = build_dataset(bars, sentiment_records=[], event_records=[])
    assert len(dataset.X) == 0


def test_latest_features_excluded_from_training_set():
    bars = _make_bars(n=40)
    dataset = build_dataset(bars, sentiment_records=[], event_records=[])
    assert dataset.latest_date == bars.index[-1]
    assert dataset.latest_date not in dataset.X.index
