"""Explainability: permutation importance by default, SHAP as an optional
enhancement when installed. Never fabricated — both methods are computed
directly from the actual fitted model and held-out data.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance

from app.ml.pipeline import RANDOM_SEED


def permutation_importance_report(
    model, X: pd.DataFrame, y: pd.Series, feature_names: list[str], top_n: int = 8
) -> list[dict]:
    result = permutation_importance(
        model, X.values, y.values, n_repeats=15, random_state=RANDOM_SEED, scoring="accuracy"
    )
    ranked = sorted(
        zip(feature_names, result.importances_mean, result.importances_std, strict=True),
        key=lambda t: t[1],
        reverse=True,
    )
    return [
        {"feature": name, "importance": float(mean), "std": float(std)}
        for name, mean, std in ranked[:top_n]
    ]


def shap_report(
    model, X_sample: pd.DataFrame, feature_names: list[str], top_n: int = 8
) -> list[dict] | None:
    """Returns None (not an error) when SHAP isn't installed — this is an
    optional enhancement per spec, not a requirement."""
    try:
        import shap
    except ImportError:
        return None

    try:
        explainer = shap.Explainer(model, X_sample)
        shap_values = explainer(X_sample)
        mean_abs = np.abs(shap_values.values).mean(axis=0)
        ranked = sorted(zip(feature_names, mean_abs, strict=True), key=lambda t: t[1], reverse=True)
        return [{"feature": name, "mean_abs_shap": float(val)} for name, val in ranked[:top_n]]
    except Exception:
        return None


def coefficient_report(model, feature_names: list[str], top_n: int = 8) -> list[dict] | None:
    """For linear models (logistic regression), raw coefficients are a
    second, cheap explainability signal alongside permutation importance."""
    clf = model.named_steps.get("clf") if hasattr(model, "named_steps") else None
    if clf is None or not hasattr(clf, "coef_"):
        return None
    coefs = clf.coef_[0]
    ranked = sorted(zip(feature_names, coefs, strict=True), key=lambda t: abs(t[1]), reverse=True)
    return [{"feature": name, "coefficient": float(c)} for name, c in ranked[:top_n]]
