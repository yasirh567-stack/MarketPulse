OWNER_KEY = "anon-test-user-1"


def test_watchlist_created_on_first_access(client):
    resp = client.get(f"/api/v1/watchlists/{OWNER_KEY}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["owner_key"] == OWNER_KEY
    assert body["items"] == []


def test_add_and_list_watchlist_item(client):
    resp = client.post(f"/api/v1/watchlists/{OWNER_KEY}/items", json={"ticker": "aapl"})
    assert resp.status_code == 201
    tickers = [i["ticker"] for i in resp.json()["items"]]
    assert "AAPL" in tickers  # normalized to uppercase


def test_adding_duplicate_ticker_is_idempotent(client):
    client.post(f"/api/v1/watchlists/{OWNER_KEY}/items", json={"ticker": "MSFT"})
    resp = client.post(f"/api/v1/watchlists/{OWNER_KEY}/items", json={"ticker": "MSFT"})
    tickers = [i["ticker"] for i in resp.json()["items"]]
    assert tickers.count("MSFT") == 1


def test_remove_watchlist_item(client):
    client.post(f"/api/v1/watchlists/{OWNER_KEY}/items", json={"ticker": "TSLA"})
    resp = client.delete(f"/api/v1/watchlists/{OWNER_KEY}/items/TSLA")
    assert resp.status_code == 200
    tickers = [i["ticker"] for i in resp.json()["items"]]
    assert "TSLA" not in tickers


def test_invalid_owner_key_rejected(client):
    resp = client.get("/api/v1/watchlists/x")  # too short
    assert resp.status_code == 422


def test_invalid_ticker_rejected(client):
    resp = client.post(f"/api/v1/watchlists/{OWNER_KEY}/items", json={"ticker": "!!!"})
    assert resp.status_code == 422
