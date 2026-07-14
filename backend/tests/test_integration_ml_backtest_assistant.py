"""End-to-end integration tests through the real API for the heavier
subsystems (ML training/prediction, backtesting, assistant) that the unit
tests exercise only in isolated pieces. These are slower (each prediction
call trains a real model on the bundled demo fixtures) but they're what
actually proves the full pipeline wires together correctly."""

import pytest


@pytest.mark.slow
def test_prediction_endpoint_trains_and_returns_explainable_result(client):
    resp = client.get("/api/v1/predictions/AAPL")
    assert resp.status_code == 200
    body = resp.json()
    assert body["predicted_direction"] in {"up", "down"}
    assert 0.0 <= body["probability_up"] <= 1.0
    assert body["confidence_label"] in {"low", "moderate", "high"}
    assert len(body["top_features"]) > 0
    assert len(body["limitations"]) >= 1

    # Second call should reuse the just-trained model rather than retraining
    # (staleness window is hours, not seconds).
    resp2 = client.get("/api/v1/predictions/AAPL")
    assert resp2.json()["trained_at"] == body["trained_at"]


@pytest.mark.slow
def test_model_metrics_endpoint_reports_baselines_and_combined(client):
    client.get("/api/v1/predictions/AAPL")  # ensure a model exists
    resp = client.get("/api/v1/models/AAPL/latest")
    assert resp.status_code == 200
    body = resp.json()
    assert "combined" in body["metrics"]
    assert "price_only" in body["metrics"]
    assert "sentiment_only" in body["metrics"]
    assert "majority_class" in body["baseline_metrics"]
    assert "previous_direction" in body["baseline_metrics"]
    assert body["random_seed"] == 42


def test_model_metrics_endpoint_404s_when_nothing_trained_yet(client):
    resp = client.get("/api/v1/models/MSFT/latest")
    assert resp.status_code == 422  # InsufficientDataError-style: not trained yet
    assert resp.json()["error"] == "insufficient_data"


@pytest.mark.slow
def test_backtest_endpoint_returns_hypothetical_labeled_results(client):
    resp = client.post(
        "/api/v1/backtests",
        json={"ticker": "AAPL", "holding_period_days": 5, "prob_threshold": 0.55},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "hypothetical" in body["disclaimer"].lower()
    assert "total_return_pct" in body["metrics"]
    assert isinstance(body["equity_curve"], list) and len(body["equity_curve"]) > 0
    assert isinstance(body["benchmark_curve"], list) and len(body["benchmark_curve"]) > 0

    # GET by id should return the exact same stored result.
    run_id = body["run_id"]
    resp2 = client.get(f"/api/v1/backtests/{run_id}")
    assert resp2.status_code == 200
    assert resp2.json()["metrics"] == body["metrics"]


def test_backtest_missing_run_id_404s(client):
    resp = client.get("/api/v1/backtests/999999")
    assert resp.status_code == 404


@pytest.mark.slow
def test_threshold_sweep_endpoint_returns_one_point_per_threshold(client):
    resp = client.post(
        "/api/v1/backtests/threshold-sweep",
        json={"ticker": "AAPL", "prob_thresholds": [0.6, 0.5, 0.7]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ticker"] == "AAPL"
    thresholds = body["thresholds"]
    assert len(thresholds) == 3
    assert [t["prob_threshold"] for t in thresholds] == [0.5, 0.6, 0.7]  # deduped + sorted
    for point in thresholds:
        assert "sharpe_ratio" in point
        assert "num_trades" in point


def test_threshold_sweep_endpoint_503s_on_unresolvable_ticker(client):
    # In DEMO_MODE (forced by conftest), a ticker that is neither a demo
    # ticker nor a resolvable live one fails at the market-data provider
    # level (ProviderUnavailableError/503), same as the existing single
    # `POST /backtests` endpoint — not an InsufficientDataError/422, since
    # the data source itself never returns anything sample-count-related.
    resp = client.post(
        "/api/v1/backtests/threshold-sweep",
        json={"ticker": "ZZZNOPE", "prob_thresholds": [0.55, 0.6]},
    )
    assert resp.status_code == 503
    assert resp.json()["error"] == "provider_unavailable"


@pytest.mark.slow
def test_leaderboard_endpoint_returns_entries_for_demo_tickers(client):
    resp = client.get("/api/v1/leaderboard", params={"tickers": "AAPL,MSFT"})
    assert resp.status_code == 200
    body = resp.json()
    entries = body["entries"]
    assert len(entries) == 2
    tickers = {e["ticker"] for e in entries}
    assert tickers == {"AAPL", "MSFT"}
    for entry in entries:
        assert entry["status"] == "ok"
        assert isinstance(entry["beats_baseline"], bool)
        assert entry["roc_auc"] is not None


@pytest.mark.slow
def test_leaderboard_endpoint_marks_unresolvable_ticker_without_failing_others(client):
    # ZZZNOPE fails at the market-data-provider level (unknown ticker, not
    # "insufficient data") — the leaderboard must still 200 with AAPL's real
    # entry rather than letting one bad ticker 503 the whole request.
    resp = client.get("/api/v1/leaderboard", params={"tickers": "AAPL,ZZZNOPE"})
    assert resp.status_code == 200
    entries = {e["ticker"]: e for e in resp.json()["entries"]}
    assert entries["AAPL"]["status"] == "ok"
    assert entries["ZZZNOPE"]["status"] == "error"
    assert entries["ZZZNOPE"]["note"]


def test_assistant_why_moving_question(client):
    resp = client.post(
        "/api/v1/assistant/query", json={"ticker": "AAPL", "question": "Why is AAPL moving?"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["data_sufficient"] is True
    assert len(body["citations"]) > 0
    assert (
        "not proof of causality" in body["disclaimer"]
        or "not financial advice" in body["disclaimer"]
    )


def test_assistant_risks_question_filters_to_negative_categories(client):
    resp = client.post(
        "/api/v1/assistant/query",
        json={"ticker": "AAPL", "question": "What are the main risks in the latest news?"},
    )
    assert resp.status_code == 200
    assert "investigation" in resp.json()["answer"].lower()


def test_assistant_sentiment_trend_question(client):
    resp = client.post(
        "/api/v1/assistant/query",
        json={"ticker": "AAPL", "question": "Has sentiment become more negative?"},
    )
    assert resp.status_code == 200
    assert resp.json()["answer"]  # non-empty deterministic answer


def test_assistant_empty_question_rejected(client):
    resp = client.post("/api/v1/assistant/query", json={"ticker": "AAPL", "question": "   "})
    assert resp.status_code == 422


def test_assistant_insufficient_evidence_is_honest_for_unknown_ticker(client):
    resp = client.post(
        "/api/v1/assistant/query", json={"ticker": "ZZZNOPE", "question": "Why is this moving?"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["data_sufficient"] is False
