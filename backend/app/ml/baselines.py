"""Naive baselines the real model must beat to be worth showing.

Reporting these alongside the combined model is what prevents a misleading
"85% accurate!" headline number — if the majority-class baseline gets 83%
because the data is imbalanced, 85% is not impressive.
"""

from __future__ import annotations

import numpy as np


def majority_class_predict(y_train: np.ndarray, n: int) -> np.ndarray:
    majority = int(round(y_train.mean())) if len(y_train) else 1
    return np.full(n, majority)


def previous_direction_predict(y_context: np.ndarray, n: int) -> np.ndarray:
    """Predicts that tomorrow's direction repeats today's realized direction.
    `y_context` is the label immediately preceding each test point (i.e. for
    test index i, the label at train/test boundary + i - 1)."""
    return y_context[:n]
