"""Produces an out-of-sample (walk-forward) probability-of-up series for the
full available history of a ticker, for use by the backtesting engine.

Reuses the exact same expanding-window fold structure as the research
pipeline (`app.ml.pipeline`): for each fold, a model is fit ONLY on data
strictly before the fold's test block, then used to score that block. Every
probability in the resulting series was therefore produced by a model that
had never seen that day (or any later day) during training — the same
no-look-ahead guarantee the research pipeline relies on, which is exactly
what a legitimate backtest needs.

Days before the first fold's test block (the initial expanding-window
warm-up) have no out-of-sample signal and are excluded from backtesting.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from app.ml.calibration import TemporalPlattCalibrator
from app.ml.features import Dataset
from app.ml.pipeline import MIN_TRAIN_SIZE, N_SPLITS, build_model, raw_score
from app.ml.validation import expanding_window_splits


@dataclass
class SignalSeries:
    dates: pd.DatetimeIndex
    probability_up: pd.Series
    sentiment_avg_5d: pd.Series
    actual_label: pd.Series


def build_oos_signal_series(dataset: Dataset, model_name: str) -> SignalSeries:
    n = len(dataset.X)
    splits = expanding_window_splits(n, n_splits=N_SPLITS, min_train_size=MIN_TRAIN_SIZE)
    X_arr, y_arr = dataset.X.values, dataset.y.values

    proba_by_pos: dict[int, float] = {}
    for train_idx, test_idx in splits:
        model = build_model(model_name)
        model.fit(X_arr[train_idx], y_arr[train_idx])
        raw_train = raw_score(model, X_arr[train_idx])
        raw_test = raw_score(model, X_arr[test_idx])
        calibrator = TemporalPlattCalibrator().fit(raw_train, y_arr[train_idx])
        proba_test = calibrator.transform(raw_test)
        for pos, p in zip(test_idx, proba_test, strict=True):
            proba_by_pos[int(pos)] = float(p)

    covered_positions = sorted(proba_by_pos.keys())
    dates = dataset.dates[covered_positions]
    probability_up = pd.Series([proba_by_pos[p] for p in covered_positions], index=dates)
    sentiment_avg_5d = dataset.X["sentiment_avg_5d"].iloc[covered_positions]
    sentiment_avg_5d.index = dates
    actual_label = dataset.y.iloc[covered_positions]
    actual_label.index = dates

    return SignalSeries(
        dates=dates,
        probability_up=probability_up,
        sentiment_avg_5d=sentiment_avg_5d,
        actual_label=actual_label,
    )
