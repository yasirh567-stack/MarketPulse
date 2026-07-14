"""Time-aligned feature engineering for the next-period direction model.

The single most important property of this module is the alignment rule
enforced in `build_dataset`:

    A feature row for trading day T may use:
      - price/volume data through and including day T's close
      - text (news sentiment / events) published strictly BEFORE day T's close

    The label for row T is the *next* period's direction (sign of close_{T+1}
    minus close_T) — this is the only place future information appears, and
    only as the prediction target, never as a feature.

Every rolling/shift operation below looks backward only, so there is no
leakage from computing indicators. `tests/test_feature_alignment.py` asserts
this directly by checking that perturbing a future bar/article never changes
an earlier row's feature values.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

SENTIMENT_WINDOW_DAYS = 5
EVENT_WINDOW_DAYS = 5

PRICE_FEATURE_NAMES = [
    "lag_return_1",
    "lag_return_5",
    "momentum_10",
    "volatility_10",
    "ma_dist_5",
    "ma_dist_20",
    "volume_change",
    "avg_volume_10_rel",
    "rsi_14",
    "macd",
    "macd_signal",
    "macd_hist",
]

SENTIMENT_FEATURE_NAMES = [
    "sentiment_avg_5d",
    "sentiment_momentum",
    "bullish_bearish_ratio",
    "article_count_5d",
]

EVENT_CATEGORIES = [
    "earnings",
    "guidance",
    "acquisition",
    "lawsuit",
    "investigation",
    "product_launch",
    "executive_departure",
    "analyst_upgrade",
    "analyst_downgrade",
    "dividend",
    "stock_split",
    "macro",
]
EVENT_FEATURE_NAMES = [f"event_{c}_5d" for c in EVENT_CATEGORIES]

ALL_FEATURE_NAMES = PRICE_FEATURE_NAMES + SENTIMENT_FEATURE_NAMES + EVENT_FEATURE_NAMES


@dataclass
class Dataset:
    X: pd.DataFrame
    y: pd.Series
    dates: pd.DatetimeIndex
    feature_names: list[str]
    latest_features: pd.Series  # most recent bar's features (label unknown — "predict tomorrow")
    latest_date: pd.Timestamp


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)  # neutral RSI when undefined (e.g. no losses yet)


def _macd(close: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    macd = ema_12 - ema_26
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal
    return macd, signal, hist


def compute_price_features(bars: pd.DataFrame) -> pd.DataFrame:
    """`bars` must be sorted ascending by date with columns: close, volume."""
    close = bars["close"]
    volume = bars["volume"].astype(float)

    features = pd.DataFrame(index=bars.index)
    features["lag_return_1"] = close.pct_change(1)
    features["lag_return_5"] = close.pct_change(5)
    features["momentum_10"] = close / close.shift(10) - 1
    features["volatility_10"] = close.pct_change().rolling(10).std()
    ma_5 = close.rolling(5).mean()
    ma_20 = close.rolling(20).mean()
    features["ma_dist_5"] = close / ma_5 - 1
    features["ma_dist_20"] = close / ma_20 - 1
    features["volume_change"] = volume.pct_change(1).replace([np.inf, -np.inf], np.nan)
    avg_volume_10 = volume.rolling(10).mean()
    features["avg_volume_10_rel"] = (volume / avg_volume_10 - 1).replace([np.inf, -np.inf], np.nan)
    features["rsi_14"] = _rsi(close, 14)
    macd, signal, hist = _macd(close)
    features["macd"] = macd
    features["macd_signal"] = signal
    features["macd_hist"] = hist
    return features


def compute_sentiment_features(
    dates: pd.DatetimeIndex, sentiment_records: list[dict]
) -> pd.DataFrame:
    """`sentiment_records`: list of {"published_at": Timestamp, "compound": float, "label": str}.

    For each bar close timestamp T, only records with published_at < T are
    eligible (strict inequality enforces "known before this bar's close").
    """
    out = pd.DataFrame(index=dates, columns=SENTIMENT_FEATURE_NAMES, dtype=float)
    if not sentiment_records:
        out[:] = 0.0
        out["bullish_bearish_ratio"] = 1.0
        return out

    rec_df = pd.DataFrame(sentiment_records)
    rec_df["published_at"] = pd.to_datetime(rec_df["published_at"], utc=True)

    window = pd.Timedelta(days=SENTIMENT_WINDOW_DAYS)
    prev_avgs: dict[pd.Timestamp, float] = {}
    for date in dates:
        cutoff = date
        window_start = date - window
        mask = (rec_df["published_at"] < cutoff) & (rec_df["published_at"] >= window_start)
        window_rows = rec_df.loc[mask]
        if window_rows.empty:
            avg_compound = 0.0
            bullish = bearish = 0
        else:
            avg_compound = float(window_rows["compound"].mean())
            bullish = int((window_rows["label"] == "bullish").sum())
            bearish = int((window_rows["label"] == "bearish").sum())
        prev_avgs[date] = avg_compound
        out.loc[date, "sentiment_avg_5d"] = avg_compound
        out.loc[date, "bullish_bearish_ratio"] = bullish / (bearish + 1)
        out.loc[date, "article_count_5d"] = float(len(window_rows))

    # Momentum: change in the rolling sentiment average vs. the prior bar's
    # rolling average — still only ever compares two already-computed,
    # backward-looking aggregates.
    avg_series = out["sentiment_avg_5d"]
    out["sentiment_momentum"] = avg_series.diff().fillna(0.0)
    return out


def compute_event_features(dates: pd.DatetimeIndex, event_records: list[dict]) -> pd.DataFrame:
    """`event_records`: list of {"published_at": Timestamp, "category": str}."""
    out = pd.DataFrame(0.0, index=dates, columns=EVENT_FEATURE_NAMES)
    if not event_records:
        return out
    rec_df = pd.DataFrame(event_records)
    rec_df["published_at"] = pd.to_datetime(rec_df["published_at"], utc=True)
    window = pd.Timedelta(days=EVENT_WINDOW_DAYS)
    for date in dates:
        mask = (rec_df["published_at"] < date) & (rec_df["published_at"] >= date - window)
        cats = set(rec_df.loc[mask, "category"])
        for cat in cats:
            col = f"event_{cat}_5d"
            if col in out.columns:
                out.loc[date, col] = 1.0
    return out


def build_dataset(
    bars: pd.DataFrame,
    sentiment_records: list[dict],
    event_records: list[dict],
) -> Dataset:
    """`bars` must have a DatetimeIndex (tz-aware, ascending) and columns
    open/high/low/close/volume. Returns the aligned feature matrix, binary
    up/down label, and the dates each row corresponds to."""
    bars = bars.sort_index()
    price_feats = compute_price_features(bars)
    sentiment_feats = compute_sentiment_features(bars.index, sentiment_records)
    event_feats = compute_event_features(bars.index, event_records)

    X = pd.concat([price_feats, sentiment_feats, event_feats], axis=1)[ALL_FEATURE_NAMES]

    next_close = bars["close"].shift(-1)
    label = (next_close > bars["close"]).astype(float)
    label[next_close.isna()] = np.nan  # last row has no next-day label yet

    combined = pd.concat([X, label.rename("label")], axis=1)
    latest_date = combined.index[-1]
    latest_features = combined.iloc[-1][ALL_FEATURE_NAMES]

    trainable = combined.dropna()
    y = trainable["label"].astype(int)
    X_clean = trainable[ALL_FEATURE_NAMES]
    return Dataset(
        X=X_clean,
        y=y,
        dates=trainable.index,
        feature_names=ALL_FEATURE_NAMES,
        latest_features=latest_features,
        latest_date=latest_date,
    )
