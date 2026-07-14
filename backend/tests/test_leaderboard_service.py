"""Unit tests for the leaderboard aggregation layer — no network/DB training
needed, `get_or_train` is monkeypatched so these stay fast and isolated."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from app.core.errors import InsufficientDataError, ProviderUnavailableError
from app.models.ml import ModelRun
from app.services import leaderboard_service


def _fake_run(ticker: str, combined_ba: float, majority_ba: float, prevdir_ba: float) -> ModelRun:
    return ModelRun(
        ticker=ticker,
        model_name="gradient_boosting",
        train_start=datetime(2026, 1, 1, tzinfo=UTC),
        train_end=datetime(2026, 6, 1, tzinfo=UTC),
        n_train_samples=200,
        n_test_samples=40,
        params_json=json.dumps({}),
        metrics_json=json.dumps(
            {
                "combined": {
                    "accuracy": 0.6,
                    "balanced_accuracy": combined_ba,
                    "roc_auc": 0.58,
                    "brier_score": 0.24,
                }
            }
        ),
        baseline_metrics_json=json.dumps(
            {
                "majority_class": {"balanced_accuracy": majority_ba},
                "previous_direction": {"balanced_accuracy": prevdir_ba},
            }
        ),
        feature_names_json=json.dumps([]),
        random_seed=42,
        trained_at=datetime(2026, 7, 13, tzinfo=UTC),
    )


def test_beats_baseline_true_when_combined_exceeds_both_baselines(monkeypatch):
    run = _fake_run("AAPL", combined_ba=0.58, majority_ba=0.50, prevdir_ba=0.52)
    monkeypatch.setattr(leaderboard_service, "get_or_train", lambda *a, **k: (run, None))

    entries = leaderboard_service.get_leaderboard(db=None, settings=None, tickers=["AAPL"])

    assert len(entries) == 1
    assert entries[0].status == "ok"
    assert entries[0].beats_baseline is True
    assert entries[0].balanced_accuracy == 0.58


def test_beats_baseline_false_when_a_baseline_is_stronger(monkeypatch):
    run = _fake_run("MSFT", combined_ba=0.51, majority_ba=0.50, prevdir_ba=0.55)
    monkeypatch.setattr(leaderboard_service, "get_or_train", lambda *a, **k: (run, None))

    entries = leaderboard_service.get_leaderboard(db=None, settings=None, tickers=["MSFT"])

    assert entries[0].beats_baseline is False


def test_ticker_with_insufficient_data_does_not_abort_the_rest(monkeypatch):
    good_run = _fake_run("AAPL", combined_ba=0.58, majority_ba=0.50, prevdir_ba=0.52)

    def fake_get_or_train(db, settings, ticker, model_name):
        if ticker == "ZZZNOPE":
            raise InsufficientDataError("not enough history for ZZZNOPE")
        return good_run, None

    monkeypatch.setattr(leaderboard_service, "get_or_train", fake_get_or_train)

    entries = leaderboard_service.get_leaderboard(
        db=None, settings=None, tickers=["AAPL", "ZZZNOPE"]
    )

    assert len(entries) == 2
    aapl, zzz = entries
    assert aapl.status == "ok"
    assert zzz.status == "insufficient_data"
    assert zzz.note and "ZZZNOPE" in zzz.note


def test_ticker_with_provider_error_does_not_abort_the_rest(monkeypatch):
    """A bad/unresolvable ticker (typo, delisted, provider outage) fails at
    the market-data layer with ProviderUnavailableError, not
    InsufficientDataError — it must be treated the same way: marked on its
    own row, not allowed to 503 the whole leaderboard request."""
    good_run = _fake_run("AAPL", combined_ba=0.58, majority_ba=0.50, prevdir_ba=0.52)

    def fake_get_or_train(db, settings, ticker, model_name):
        if ticker == "BADTICK":
            raise ProviderUnavailableError("market data", "no data for BADTICK")
        return good_run, None

    monkeypatch.setattr(leaderboard_service, "get_or_train", fake_get_or_train)

    entries = leaderboard_service.get_leaderboard(
        db=None, settings=None, tickers=["AAPL", "BADTICK"]
    )

    assert len(entries) == 2
    aapl, bad = entries
    assert aapl.status == "ok"
    assert bad.status == "error"
    assert bad.note and "BADTICK" in bad.note
