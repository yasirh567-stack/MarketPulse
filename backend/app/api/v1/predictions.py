from __future__ import annotations

import json

from fastapi import APIRouter, Path

from app.api.deps import AppSettings, DbSession
from app.ml.service import get_or_train
from app.schemas.ml import PredictionResponse

router = APIRouter()

LIMITATIONS = [
    "This is a statistical estimate from a research model trained on a limited history of "
    "daily bars and news sentiment — it is not financial advice and does not guarantee "
    "any outcome.",
    "Free daily-bar data cannot support intraday or high-frequency predictions; this model "
    "estimates only the next full trading day's direction.",
    "Model performance varies by ticker and period; see the Research page for this ticker's "
    "actual validation metrics and baseline comparison before trusting a probability.",
]


@router.get("/{ticker}", response_model=PredictionResponse)
def get_prediction(db: DbSession, settings: AppSettings, ticker: str = Path(...)):
    ticker = ticker.upper()
    run, prediction = get_or_train(db, settings, ticker)
    return PredictionResponse(
        ticker=ticker,
        model_name=run.model_name,
        predicted_direction=prediction.predicted_direction,
        probability_up=prediction.probability_up,
        confidence_label=prediction.confidence_label,
        as_of_date=prediction.as_of_date,
        trained_at=run.trained_at,
        train_start=run.train_start,
        train_end=run.train_end,
        n_train_samples=run.n_train_samples,
        top_features=json.loads(prediction.top_features_json),
        sentiment_shift_note=prediction.sentiment_shift_note,
        limitations=LIMITATIONS,
    )
