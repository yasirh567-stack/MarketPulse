"""Walk-forward (expanding window) validation utilities and metrics.

Random/shuffled train-test splitting is never used for this market data —
every split here preserves chronological order, so a fold is always trained
only on data that would have been available before its test period began.
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def expanding_window_splits(
    n_samples: int, n_splits: int = 5, min_train_size: int = 40
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Returns [(train_idx, test_idx), ...] with strictly increasing,
    non-overlapping test blocks and an always-growing training prefix."""
    if n_samples <= min_train_size + n_splits:
        return []
    remaining = n_samples - min_train_size
    fold_size = max(remaining // n_splits, 1)
    splits = []
    train_end = min_train_size
    for i in range(n_splits):
        test_start = train_end
        test_end = test_start + fold_size if i < n_splits - 1 else n_samples
        if test_start >= n_samples:
            break
        train_idx = np.arange(0, test_start)
        test_idx = np.arange(test_start, test_end)
        if len(test_idx) == 0:
            continue
        splits.append((train_idx, test_idx))
        train_end = test_end
    return splits


def compute_classification_metrics(
    y_true: np.ndarray, y_pred: np.ndarray, y_proba: np.ndarray | None
) -> dict:
    metrics: dict = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist(),
        "n_samples": int(len(y_true)),
        "positive_rate": float(np.mean(y_true)) if len(y_true) else None,
    }
    if y_proba is not None and len(set(y_true.tolist())) > 1:
        try:
            metrics["roc_auc"] = float(roc_auc_score(y_true, y_proba))
        except ValueError:
            metrics["roc_auc"] = None
        metrics["brier_score"] = float(brier_score_loss(y_true, y_proba))
    else:
        metrics["roc_auc"] = None
        metrics["brier_score"] = (
            float(np.mean((y_proba - y_true) ** 2)) if y_proba is not None else None
        )
    return metrics


def average_fold_metrics(fold_metrics: list[dict]) -> dict:
    if not fold_metrics:
        return {}
    keys = ["accuracy", "balanced_accuracy", "precision", "recall", "f1", "roc_auc", "brier_score"]
    averaged = {}
    for key in keys:
        values = [m[key] for m in fold_metrics if m.get(key) is not None]
        averaged[key] = float(np.mean(values)) if values else None
    averaged["n_folds"] = len(fold_metrics)
    averaged["total_test_samples"] = sum(m["n_samples"] for m in fold_metrics)
    # Summed (not averaged) confusion matrix across every out-of-sample fold —
    # this is what the Research page's confusion-matrix panel renders, since
    # a single fold's matrix would understate how much data actually backs it.
    summed = np.zeros((2, 2), dtype=int)
    for m in fold_metrics:
        summed += np.array(m["confusion_matrix"])
    averaged["confusion_matrix"] = summed.tolist()
    return averaged
