"""Temporal probability calibration (Platt scaling) without shuffling.

scikit-learn's `CalibratedClassifierCV` defaults to (shuffled) K-fold internal
splits, which would leak future-dated rows into calibration of earlier ones
for time series. Instead we fit a 1D logistic regression ("Platt scaling")
mapping raw model scores -> calibrated probabilities using only a
chronologically later held-out slice, never a shuffled fold.
"""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression


class TemporalPlattCalibrator:
    def __init__(self):
        self._lr = LogisticRegression()
        self._fitted = False

    def fit(self, raw_scores: np.ndarray, y: np.ndarray) -> TemporalPlattCalibrator:
        if len(set(y.tolist())) < 2:
            self._fitted = False  # can't calibrate with a single class present
            return self
        self._lr.fit(raw_scores.reshape(-1, 1), y)
        self._fitted = True
        return self

    def transform(self, raw_scores: np.ndarray) -> np.ndarray:
        if not self._fitted:
            return raw_scores
        return self._lr.predict_proba(raw_scores.reshape(-1, 1))[:, 1]
