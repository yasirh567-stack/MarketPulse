def test_news_returns_demo_articles_deduplicated(client):
    resp = client.get("/api/v1/news/AAPL", params={"page": 1, "page_size": 5})
    assert resp.status_code == 200
    body = resp.json()
    assert body["ticker"] == "AAPL"
    assert len(body["articles"]) <= 5
    urls = [a["url"] for a in body["articles"]]
    assert len(urls) == len(set(urls))  # no duplicates
    for article in body["articles"]:
        assert article["data_status"] == "demo"

    # Calling again must not duplicate rows (dedup by url_hash).
    resp2 = client.get("/api/v1/news/AAPL", params={"page": 1, "page_size": 5})
    assert resp2.json()["total"] == body["total"]


def test_sentiment_endpoint_reports_active_model_and_timeline(client):
    resp = client.get("/api/v1/sentiment/AAPL")
    assert resp.status_code == 200
    body = resp.json()
    assert body["active_model"] == "vader"
    assert isinstance(body["timeline"], list)
    assert "news" in body["by_source_type"]


def test_events_endpoint_returns_disclaimer_and_categories(client):
    resp = client.get("/api/v1/events/AAPL")
    assert resp.status_code == 200
    body = resp.json()
    assert "not proof" in body["disclaimer"] or "causal" in body["disclaimer"]
    assert len(body["events"]) > 0
    for event in body["events"]:
        assert isinstance(event["matched_keywords"], list)
