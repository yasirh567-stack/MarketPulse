def test_quote_returns_demo_labeled_data(client):
    resp = client.get("/api/v1/market/AAPL/quote")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ticker"] == "AAPL"
    assert body["data_status"] == "demo"
    assert body["price"] > 0


def test_quote_invalid_ticker_format_rejected(client):
    resp = client.get("/api/v1/market/$$$/quote")
    assert resp.status_code == 422


def test_quote_unknown_ticker_returns_503(client):
    # Not a demo ticker and demo_mode=True means no live fallback is attempted.
    resp = client.get("/api/v1/market/ZZZUNKNOWN/quote")
    assert resp.status_code == 503
    assert resp.json()["error"] == "provider_unavailable"


def test_history_returns_bars_within_period(client):
    resp = client.get("/api/v1/market/AAPL/history", params={"period_days": 30})
    assert resp.status_code == 200
    body = resp.json()
    assert body["data_status"] == "demo"
    assert len(body["bars"]) > 0
    for bar in body["bars"]:
        assert bar["high"] >= bar["low"]


def test_history_rejects_bad_interval(client):
    resp = client.get("/api/v1/market/AAPL/history", params={"interval": "5m"})
    assert resp.status_code == 422


def test_history_downsamples_large_payloads(client):
    resp = client.get("/api/v1/market/AAPL/history", params={"period_days": 1000})
    assert resp.status_code == 200
    assert len(resp.json()["bars"]) <= 500
