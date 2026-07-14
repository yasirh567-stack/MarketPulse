from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class LeaderboardEntry(BaseModel):
    ticker: str
    model_name: str
    trained_at: datetime | None = None
    n_train_samples: int | None = None
    accuracy: float | None = None
    balanced_accuracy: float | None = None
    roc_auc: float | None = None
    brier_score: float | None = None
    baseline_majority_balanced_accuracy: float | None = None
    baseline_previous_direction_balanced_accuracy: float | None = None
    beats_baseline: bool = False
    status: Literal["ok", "insufficient_data", "error"] = "ok"
    note: str | None = None


class LeaderboardResponse(BaseModel):
    entries: list[LeaderboardEntry]
    disclaimer: str = (
        "Walk-forward validation metrics only — not evidence of future performance. A ticker "
        "'beating baseline' here reflects one historical period and model, not a guarantee."
    )
