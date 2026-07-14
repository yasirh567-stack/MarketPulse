import json


def test_websocket_subscribe_and_receive_quote(client):
    with client.websocket_connect("/api/v1/ws/market") as ws:
        ws.send_text(json.dumps({"action": "subscribe", "ticker": "AAPL"}))
        ack = ws.receive_json()
        assert ack == {"type": "subscribed", "ticker": "AAPL"}

        quote_msg = ws.receive_json()
        assert quote_msg["type"] == "quote"
        assert quote_msg["ticker"] == "AAPL"
        assert quote_msg["data"]["data_status"] == "demo"
        assert "poll_interval_seconds" in quote_msg["data"]


def test_websocket_ping_pong(client):
    with client.websocket_connect("/api/v1/ws/market") as ws:
        ws.send_text(json.dumps({"action": "ping"}))
        reply = ws.receive_json()
        assert reply == {"type": "pong"}


def test_websocket_rejects_invalid_message(client):
    with client.websocket_connect("/api/v1/ws/market") as ws:
        ws.send_text("not valid json")
        reply = ws.receive_json()
        assert reply["type"] == "error"


def test_websocket_unsubscribe_stops_further_quotes(client):
    with client.websocket_connect("/api/v1/ws/market") as ws:
        ws.send_text(json.dumps({"action": "subscribe", "ticker": "AAPL"}))
        assert ws.receive_json()["type"] == "subscribed"
        assert ws.receive_json()["type"] == "quote"

        ws.send_text(json.dumps({"action": "unsubscribe", "ticker": "AAPL"}))
        ack = ws.receive_json()
        assert ack == {"type": "unsubscribed", "ticker": "AAPL"}


def test_websocket_subscribe_requires_ticker(client):
    with client.websocket_connect("/api/v1/ws/market") as ws:
        ws.send_text(json.dumps({"action": "subscribe"}))
        reply = ws.receive_json()
        assert reply["type"] == "error"
