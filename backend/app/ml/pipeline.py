"""Model registry, walk-forward evaluation orchestration, and final-fit logic."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.ml.baselines import majority_class_predict, previous_direction_predict
from app.ml.calibration import TemporalPlattCalibrator
from app.ml.validation import (
    average_fold_metrics,
    compute_classification_metrics,
    expanding_window_splits,
)

RANDOM_SEED = 42
MIN_TOTAL_SAMPLES = 80  # below this we report "insufficient data" rather than guess
N_SPLITS = 5
MIN_TRAIN_SIZE = 40


def build_model(model_name: str):
    if model_name == "logistic_regression":
        return Pipeline(
            [
                ("scaler", StandardScaler()),
                ("clf", LogisticRegression(max_iter=1000, random_state=RANDOM_SEED)),
            ]
        )
    if model_name == "gradient_boosting":
        return GradientBoostingClassifier(random_state=RANDOM_SEED, n_estimators=150, max_depth=3)
    raise ValueError(f"Unknown model_name: {model_name}")


def raw_score(model, X: pd.DataFrame) -> np.ndarray:
    """Uncalibrated positive-class score used as input to Platt scaling."""
    if hasattr(model, "decision_function"):
        return model.decision_function(X)
    return model.predict_proba(X)[:, 1]


@dataclass
class WalkForwardResult:
    model_metrics: dict
    baseline_metrics: dict[str, dict]
    n_folds: int
    fold_details: list[dict] = field(default_factory=list)


def run_walkforward_evaluation(X: pd.DataFrame, y: pd.Series, model_name: str) -> WalkForwardResult:
    n = len(X)
    splits = expanding_window_splits(n, n_splits=N_SPLITS, min_train_size=MIN_TRAIN_SIZE)
    X_arr, y_arr = X.values, y.values

    model_folds, majority_folds, prev_dir_folds = [], [], []
    fold_details = []
    for train_idx, test_idx in splits:
        X_train, y_train = X_arr[train_idx], y_arr[train_idx]
        X_test, y_test = X_arr[test_idx], y_arr[test_idx]

        model = build_model(model_name)
        model.fit(X_train, y_train)
        raw_train = raw_score(model, X_train)
        raw_test = raw_score(model, X_test)
        calibrator = TemporalPlattCalibrator().fit(raw_train, y_train)
        proba_test = calibrator.transform(raw_test)
        pred_test = (proba_test >= 0.5).astype(int)
        fold_metric = compute_classification_metrics(y_test, pred_test, proba_test)
        model_folds.append(fold_metric)
        fold_details.append(
            {"train_size": len(train_idx), "test_size": len(test_idx), **fold_metric}
        )

        majority_pred = majority_class_predict(y_train, len(test_idx))
        majority_folds.append(
            compute_classification_metrics(y_test, majority_pred, majority_pred.astype(float))
        )

        # "previous direction": use the label immediately before each test
        # point, which for a contiguous expanding-window test block is just
        # y shifted by one within [train_idx[-1], test_idx-1].
        context = np.concatenate([y_train[-1:], y_test[:-1]])
        prev_pred = previous_direction_predict(context, len(test_idx))
        prev_dir_folds.append(
            compute_classification_metrics(y_test, prev_pred, prev_pred.astype(float))
        )

    return WalkForwardResult(
        model_metrics=average_fold_metrics(model_folds),
        baseline_metrics={
            "majority_class": average_fold_metrics(majority_folds),
            "previous_direction": average_fold_metrics(prev_dir_folds),
        },
        n_folds=len(splits),
        fold_details=fold_details,
    )


def train_final_model(X: pd.DataFrame, y: pd.Series, model_name: str):
    """Fits on the first 80% of history (chronological) and calibrates on the
    remaining, later 20% — which the model never saw during training.

    This deliberately trades a little recency (the production model doesn't
    train on its most recent ~20% of labeled history) for calibration
    honesty. Fitting the calibrator on the model's OWN training data would
    let it read the model's memorized training-set confidence as if it were
    generalization performance — e.g. a gradient-boosted model can trivially
    separate its own training rows, which would make the calibrator output
    probabilities near 0/1 even when true out-of-sample accuracy is close to
    a coin flip. Calibrating on a truly held-out, later slice avoids that.
    """
    split_point = int(len(X) * 0.8)
    X_train, y_train = X.iloc[:split_point], y.iloc[:split_point]
    X_calib, y_calib = X.iloc[split_point:], y.iloc[split_point:]

    model = build_model(model_name)
    model.fit(X_train.values, y_train.values)

    raw_calib = raw_score(model, X_calib.values)
    calibrator = TemporalPlattCalibrator().fit(raw_calib, y_calib.values)
    return model, calibrator


def predict_proba_up(model, calibrator: TemporalPlattCalibrator, X_row: pd.DataFrame) -> float:
    raw = raw_score(model, X_row.values)
    calibrated = calibrator.transform(raw)
    return float(calibrated[0])
