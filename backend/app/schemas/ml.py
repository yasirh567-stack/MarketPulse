from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class FeatureImportanceEntry(BaseModel):
    feature: str
    importance: float | None = None
    std: float | None = None
    coefficient: float | None = None
    mean_abs_shap: float | None = None


class PredictionResponse(BaseModel):
    ticker: str
    model_name: str
    predicted_direction: str
    probability_up: float
    confidence_label: str
    as_of_date: datetime
    trained_at: datetime
    train_start: datetime
    train_end: datetime
    n_train_samples: int
    top_features: list[dict]
    sentiment_shift_note: str | None
    limitations: list[str]


class TrainModelRequest(BaseModel):
    ticker: str
    model_name: str = "gradient_boosting"


class ModelMetricsResponse(BaseModel):
    ticker: str
    model_name: str
    trained_at: datetime
    train_start: datetime
    train_end: datetime
    n_train_samples: int
    n_test_samples: int
    metrics: dict
    baseline_metrics: dict
    feature_names: list[str]
    random_seed: int
