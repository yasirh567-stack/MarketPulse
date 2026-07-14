def test_health_ok(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["demo_mode"] is True
    assert body["active_sentiment_model"] == "vader"


def test_search_returns_demo_ticker(client):
    resp = client.get("/api/v1/instruments/search", params={"q": "AAPL"})
    assert resp.status_code == 200
    results = resp.json()
    assert any(r["ticker"] == "AAPL" and r["is_demo"] for r in results)


def test_search_empty_query_rejected(client):
    resp = client.get("/api/v1/instruments/search", params={"q": ""})
    assert resp.status_code == 422


def test_search_no_match_returns_empty_list(client):
    resp = client.get("/api/v1/instruments/search", params={"q": "ZZZNOPE"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_screener_defaults_to_demo_tickers(client):
    resp = client.get("/api/v1/instruments/screener")
    assert resp.status_code == 200
    body = resp.json()
    tickers = {e["ticker"] for e in body["entries"]}
    assert {"AAPL", "MSFT", "TSLA", "NVDA", "GME"} <= tickers
    for entry in body["entries"]:
        assert entry["sentiment_label"] in {"bullish", "neutral", "bearish"}


def test_screener_respects_explicit_tickers(client):
    resp = client.get("/api/v1/instruments/screener", params={"tickers": "AAPL,GME"})
    assert resp.status_code == 200
    tickers = {e["ticker"] for e in resp.json()["entries"]}
    assert tickers == {"AAPL", "GME"}
