# NOTE: intentionally no `from __future__ import annotations` — see the
# comment in app/api/v1/backtests.py; slowapi's @limiter.limit decorator
# breaks FastAPI's param resolution under postponed annotation evaluation.

import json

from fastapi import APIRouter, Request
from sqlalchemy import select

from app.api.deps import AppSettings, DbSession
from app.core.rate_limit import default_rate_limit, limiter
from app.ml.service import DEFAULT_MODEL_NAME, train_and_persist
from app.models.ml import ModelRun
from app.schemas.ml import ModelMetricsResponse, TrainModelRequest

router = APIRouter()


@router.post("/train", response_model=ModelMetricsResponse)
@limiter.limit(default_rate_limit())
def train_model(request: Request, body: TrainModelRequest, db: DbSession, settings: AppSettings):
    run = train_and_persist(
        db, settings, body.ticker.upper(), body.model_name or DEFAULT_MODEL_NAME
    )
    return _to_response(run)


@router.get("/{ticker}/latest", response_model=ModelMetricsResponse)
def get_latest_model(db: DbSession, ticker: str):
    ticker = ticker.upper()
    run = db.scalar(
        select(ModelRun).where(ModelRun.ticker == ticker).order_by(ModelRun.trained_at.desc())
    )
    if run is None:
        from app.core.errors import InsufficientDataError

        raise InsufficientDataError(
            f"No trained model yet for {ticker}. Request a prediction first to train one."
        )
    return _to_response(run)


def _to_response(run: ModelRun) -> ModelMetricsResponse:
    return ModelMetricsResponse(
        ticker=run.ticker,
        model_name=run.model_name,
        trained_at=run.trained_at,
        train_start=run.train_start,
        train_end=run.train_end,
        n_train_samples=run.n_train_samples,
        n_test_samples=run.n_test_samples,
        metrics=json.loads(run.metrics_json),
        baseline_metrics=json.loads(run.baseline_metrics_json),
        feature_names=json.loads(run.feature_names_json),
        random_seed=run.random_seed,
    )
