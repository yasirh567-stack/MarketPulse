"""Cross-ticker model quality comparison ("leaderboard"): reuses the existing
per-ticker training/staleness pipeline (`app.ml.service.get_or_train`) instead
of introducing a second training code path — this is purely a query/aggregation
layer over the already-persisted, append-only `model_runs` table.
"""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import InsufficientDataError, ProviderUnavailableError
from app.core.logging import get_logger
from app.ml.service import DEFAULT_MODEL_NAME, get_or_train
from app.schemas.leaderboard import LeaderboardEntry

logger = get_logger("app.services.leaderboard")


def get_leaderboard(
    db: Session,
    settings: Settings,
    tickers: list[str],
    model_name: str = DEFAULT_MODEL_NAME,
) -> list[LeaderboardEntry]:
    entries: list[LeaderboardEntry] = []
    for ticker in tickers:
        ticker = ticker.upper()
        try:
            run, _ = get_or_train(db, settings, ticker, model_name)
        except InsufficientDataError as exc:
            logger.info("Leaderboard: skipping %s, insufficient data: %s", ticker, exc)
            entries.append(
                LeaderboardEntry(
                    ticker=ticker,
                    model_name=model_name,
                    status="insufficient_data",
                    note=str(exc),
                )
            )
            continue
        except ProviderUnavailableError as exc:
            # A bad/unresolvable ticker (typo, delisted, provider outage) is
            # just as "expected" a per-ticker failure as insufficient data —
            # it must not abort the whole leaderboard request. Genuinely
            # unexpected exceptions (DB errors, etc.) are NOT caught here and
            # still propagate to the global 500 handler.
            logger.info("Leaderboard: skipping %s, provider unavailable: %s", ticker, exc)
            entries.append(
                LeaderboardEntry(
                    ticker=ticker,
                    model_name=model_name,
                    status="error",
                    note=str(exc),
                )
            )
            continue

        metrics = json.loads(run.metrics_json)["combined"]
        baseline = json.loads(run.baseline_metrics_json)
        majority_ba = baseline.get("majority_class", {}).get("balanced_accuracy")
        prevdir_ba = baseline.get("previous_direction", {}).get("balanced_accuracy")
        combined_ba = metrics.get("balanced_accuracy", 0.0) or 0.0
        beats_baseline = combined_ba > max(majority_ba or 0.0, prevdir_ba or 0.0)

        entries.append(
            LeaderboardEntry(
                ticker=ticker,
                model_name=model_name,
                trained_at=run.trained_at,
                n_train_samples=run.n_train_samples,
                accuracy=metrics.get("accuracy"),
                balanced_accuracy=metrics.get("balanced_accuracy"),
                roc_auc=metrics.get("roc_auc"),
                brier_score=metrics.get("brier_score"),
                baseline_majority_balanced_accuracy=majority_ba,
                baseline_previous_direction_balanced_accuracy=prevdir_ba,
                beats_baseline=beats_baseline,
                status="ok",
            )
        )
    return entries
