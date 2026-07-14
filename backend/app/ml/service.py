"""Orchestrates the full research pipeline for one ticker: load data -> build
time-aligned features -> walk-forward evaluate baselines/price-only/
sentiment-only/combined -> fit the final model -> explainability -> persist.

This is the module both `POST /api/v1/models/train` and the on-demand
"train if stale" path in `GET /api/v1/predictions/{ticker}` call into.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import cast

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import InsufficientDataError
from app.core.logging import get_logger
from app.ml.explain import coefficient_report, permutation_importance_report, shap_report
from app.ml.features import (
    EVENT_FEATURE_NAMES,
    PRICE_FEATURE_NAMES,
    SENTIMENT_FEATURE_NAMES,
    build_dataset,
)
from app.ml.pipeline import (
    MIN_TOTAL_SAMPLES,
    RANDOM_SEED,
    predict_proba_up,
    run_walkforward_evaluation,
    train_final_model,
)
from app.models.ml import ModelRun, Prediction
from app.services import event_service, market_service, news_service, sentiment_service

logger = get_logger("app.ml.service")

DEFAULT_MODEL_NAME = "gradient_boosting"
MODEL_STALE_HOURS = 12


def load_bars_frame(db: Session, settings: Settings, ticker: str) -> pd.DataFrame:
    bars = market_service.get_history(db, settings, ticker, interval="1d", period_days=400)
    if not bars:
        raise InsufficientDataError(f"No price history available for {ticker}.")
    # yfinance returns bar timestamps localized to the exchange's own timezone
    # (e.g. America/New_York), whose UTC offset changes across a DST
    # transition. A 400-day window almost always crosses at least one, so the
    # raw list can mix two different fixed offsets — which pandas refuses to
    # build a single DatetimeIndex from without an explicit UTC normalization
    # first (real bug, not a demo-data artifact: reproduces on any live
    # ticker with enough history to span a DST change).
    ts_index = pd.DatetimeIndex(
        [b.ts.astimezone(UTC) if b.ts.tzinfo else b.ts for b in bars], name="ts"
    )
    df = pd.DataFrame(
        {
            "open": [b.open for b in bars],
            "high": [b.high for b in bars],
            "low": [b.low for b in bars],
            "close": [b.close for b in bars],
            "volume": [b.volume or 0 for b in bars],
        },
        index=ts_index,
    )
    df = df[~df.index.duplicated(keep="last")].sort_index()
    return df


def _load_sentiment_records(db: Session, ticker: str) -> list[dict]:
    scores = sentiment_service.get_recent_scores(db, ticker, limit=5000)
    return [
        {"published_at": s.published_at, "compound": s.compound, "label": s.label} for s in scores
    ]


def _load_event_records(db: Session, ticker: str) -> list[dict]:
    events = event_service.get_recent_events(db, ticker, limit=1000)
    return [{"published_at": e.published_at, "category": e.category} for e in events]


def prepare_dataset(db: Session, settings: Settings, ticker: str):
    news_service.fetch_and_store_news(db, settings, ticker, limit=20)
    bars_df = load_bars_frame(db, settings, ticker)
    sentiment_records = _load_sentiment_records(db, ticker)
    event_records = _load_event_records(db, ticker)
    return build_dataset(bars_df, sentiment_records, event_records)


def train_and_persist(
    db: Session, settings: Settings, ticker: str, model_name: str = DEFAULT_MODEL_NAME
) -> ModelRun:
    ticker = ticker.upper()
    dataset = prepare_dataset(db, settings, ticker)

    if len(dataset.X) < MIN_TOTAL_SAMPLES:
        raise InsufficientDataError(
            f"Only {len(dataset.X)} usable trading days of aligned data are available for {ticker} "
            f"(minimum required: {MIN_TOTAL_SAMPLES}). Try a ticker with a longer trading history."
        )

    combined_result = run_walkforward_evaluation(dataset.X, dataset.y, model_name)
    price_cols = PRICE_FEATURE_NAMES
    sentiment_cols = SENTIMENT_FEATURE_NAMES + EVENT_FEATURE_NAMES
    price_only_result = run_walkforward_evaluation(dataset.X[price_cols], dataset.y, model_name)
    sentiment_only_result = run_walkforward_evaluation(
        dataset.X[sentiment_cols], dataset.y, model_name
    )

    final_model, calibrator = train_final_model(dataset.X, dataset.y, model_name)

    split_point = int(len(dataset.X) * 0.8)
    holdout_X, holdout_y = dataset.X.iloc[split_point:], dataset.y.iloc[split_point:]
    perm_importance = (
        permutation_importance_report(final_model, holdout_X, holdout_y, dataset.feature_names)
        if len(holdout_X) >= 10
        else []
    )
    coef_report = coefficient_report(final_model, dataset.feature_names)
    shap_rep = shap_report(
        final_model, dataset.X.tail(min(50, len(dataset.X))), dataset.feature_names
    )

    metrics_payload = {
        "combined": combined_result.model_metrics,
        "price_only": price_only_result.model_metrics,
        "sentiment_only": sentiment_only_result.model_metrics,
        "permutation_importance": perm_importance,
        "coefficients": coef_report,
        "shap": shap_rep,
    }
    baseline_payload = combined_result.baseline_metrics

    run = ModelRun(
        ticker=ticker,
        model_name=model_name,
        train_start=dataset.dates[0].to_pydatetime(),
        train_end=dataset.dates[-1].to_pydatetime(),
        n_train_samples=len(dataset.X),
        n_test_samples=combined_result.model_metrics.get("total_test_samples", 0) or 0,
        params_json=json.dumps({"model_name": model_name, "random_seed": RANDOM_SEED}),
        metrics_json=json.dumps(metrics_payload, default=str),
        baseline_metrics_json=json.dumps(baseline_payload, default=str),
        feature_names_json=json.dumps(dataset.feature_names),
        random_seed=RANDOM_SEED,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    _store_prediction(db, run, dataset, final_model, calibrator)
    return run


def _confidence_label(probability_up: float) -> str:
    distance = abs(probability_up - 0.5)
    if distance < 0.05:
        return "low"
    if distance < 0.15:
        return "moderate"
    return "high"


def _store_prediction(db: Session, run: ModelRun, dataset, final_model, calibrator) -> Prediction:
    latest_row = dataset.latest_features
    if latest_row.isna().any():
        raise InsufficientDataError(
            "The most recent trading day does not have complete feature data yet "
            "(e.g. not enough trailing history for rolling indicators)."
        )
    X_row = pd.DataFrame([latest_row.values], columns=dataset.feature_names)
    probability_up = predict_proba_up(final_model, calibrator, X_row)
    direction = "up" if probability_up >= 0.5 else "down"

    top_features: list[dict] = []
    try:
        metrics = json.loads(run.metrics_json)
        top_features = metrics.get("permutation_importance") or []
    except Exception:
        pass

    sentiment_shift_note = None
    if "sentiment_momentum" in latest_row.index:
        momentum = latest_row["sentiment_momentum"]
        if abs(momentum) > 0.05:
            direction_word = "improved" if momentum > 0 else "worsened"
            sentiment_shift_note = (
                f"Recent sentiment has {direction_word} noticeably "
                f"(5-day momentum: {momentum:.3f})."
            )
        else:
            sentiment_shift_note = "Recent sentiment has been relatively stable."

    prediction = Prediction(
        model_run_id=run.id,
        ticker=run.ticker,
        as_of_date=dataset.latest_date.to_pydatetime(),
        predicted_direction=direction,
        probability_up=probability_up,
        confidence_label=_confidence_label(probability_up),
        top_features_json=json.dumps(top_features),
        sentiment_shift_note=sentiment_shift_note,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


def get_or_train(
    db: Session, settings: Settings, ticker: str, model_name: str = DEFAULT_MODEL_NAME
) -> tuple[ModelRun, Prediction]:
    ticker = ticker.upper()
    existing_run = db.scalar(
        select(ModelRun)
        .where(ModelRun.ticker == ticker, ModelRun.model_name == model_name)
        .order_by(ModelRun.trained_at.desc())
    )
    is_stale = (
        existing_run is None
        or (datetime.now(UTC) - existing_run.trained_at.replace(tzinfo=UTC)).total_seconds()
        > MODEL_STALE_HOURS * 3600
    )
    run = (
        train_and_persist(db, settings, ticker, model_name)
        if is_stale
        else cast(ModelRun, existing_run)
    )

    prediction = db.scalar(
        select(Prediction)
        .where(Prediction.model_run_id == run.id)
        .order_by(Prediction.created_at.desc())
    )
    if prediction is None:
        # Existing run but no prediction row (shouldn't normally happen) — retrain fully.
        run = train_and_persist(db, settings, ticker, model_name)
        prediction = db.scalar(
            select(Prediction)
            .where(Prediction.model_run_id == run.id)
            .order_by(Prediction.created_at.desc())
        )
    return run, prediction
