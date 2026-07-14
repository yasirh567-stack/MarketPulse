"""Per-connection WebSocket handler for `/api/v1/ws/market`.

Protocol (JSON text frames both ways):
  Client -> Server: {"action": "subscribe", "ticker": "AAPL"}
                     {"action": "unsubscribe", "ticker": "AAPL"}
                     {"action": "ping"}
  Server -> Client:  {"type": "quote", "ticker": "AAPL", "data": {...}}
                      {"type": "pong"}
                      {"type": "error", "message": "..."}
                      {"type": "subscribed"/"unsubscribed", "ticker": "AAPL"}

Design notes:
  - One asyncio task reads client frames (subscribe/unsubscribe/ping), another
    periodically pushes quotes for whatever is currently subscribed — modeled
    as two coroutines raced with `asyncio.wait(..., FIRST_COMPLETED)` so a
    client disconnect (read task ending) promptly cancels the push loop too,
    and unsubscribing takes effect on the very next push tick (spec:
    "stop unused subscriptions").
  - Quotes are pushed on a fixed interval (`MARKET_POLL_INTERVAL_SECONDS`),
    never faster — this is explicitly NOT tick-level streaming, since free
    data sources don't support that; every payload carries `data_status` so
    the client never mistakes a polling push for a live tick.
  - In demo mode, since the bundled fixture "closes" don't change intra-day,
    a small deterministic jitter is layered on top purely so the dashboard
    visibly animates — still tagged `data_status: "demo"`.
"""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
import time

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from starlette.websockets import WebSocketState

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.database.session import get_session_factory
from app.services import market_service
from app.websocket.schemas import ClientMessage

logger = get_logger("app.websocket.market")

MAX_SUBSCRIPTIONS_PER_CONNECTION = 20


def _demo_jitter(ticker: str, base_price: float) -> float:
    """Deterministic-but-varying jitter so demo mode visibly "moves" without
    ever claiming to be real live data."""
    tick = int(time.time() // 3)  # changes every 3s regardless of poll interval
    seed_input = f"{ticker}-{tick}".encode()
    seed = int(hashlib.sha256(seed_input).hexdigest()[:8], 16)
    pct = ((seed % 200) - 100) / 100_000  # +/- 0.1%
    return round(base_price * (1 + pct), 4)


class MarketWebSocketConnection:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.subscriptions: set[str] = set()
        self.settings: Settings = get_settings()

    async def send_json(self, payload: dict) -> None:
        if self.websocket.client_state == WebSocketState.CONNECTED:
            await self.websocket.send_text(json.dumps(payload, default=str))

    async def handle(self) -> None:
        await self.websocket.accept()
        logger.info("WebSocket connected")
        receiver = asyncio.create_task(self._receive_loop())
        pusher = asyncio.create_task(self._push_loop())
        try:
            done, pending = await asyncio.wait(
                {receiver, pusher}, return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
        finally:
            logger.info("WebSocket disconnected, subscriptions=%s", self.subscriptions)

    async def _receive_loop(self) -> None:
        try:
            while True:
                raw = await self.websocket.receive_text()
                await self._handle_client_message(raw)
        except WebSocketDisconnect:
            return

    async def _handle_client_message(self, raw: str) -> None:
        try:
            payload = json.loads(raw)
            message = ClientMessage(**payload)
        except (json.JSONDecodeError, ValidationError) as exc:
            await self.send_json({"type": "error", "message": f"Invalid message: {exc}"})
            return

        if message.action == "ping":
            await self.send_json({"type": "pong"})
            return

        if message.action == "subscribe":
            if not message.ticker:
                await self.send_json({"type": "error", "message": "subscribe requires a ticker"})
                return
            if len(self.subscriptions) >= MAX_SUBSCRIPTIONS_PER_CONNECTION:
                await self.send_json({"type": "error", "message": "Subscription limit reached"})
                return
            self.subscriptions.add(message.ticker)
            await self.send_json({"type": "subscribed", "ticker": message.ticker})
            return

        if message.action == "unsubscribe" and message.ticker:
            self.subscriptions.discard(message.ticker)
            await self.send_json({"type": "unsubscribed", "ticker": message.ticker})

    async def _push_loop(self) -> None:
        interval = max(self.settings.market_poll_interval_seconds, 1.0)
        while True:
            if self.subscriptions:
                await self._push_quotes()
            await asyncio.sleep(interval)

    async def _push_quotes(self) -> None:
        tickers = list(self.subscriptions)
        for ticker in tickers:
            try:
                payload = await asyncio.to_thread(self._fetch_quote_payload, ticker)
            except Exception as exc:
                logger.warning("WS quote push failed for %s: %s", ticker, exc)
                payload = {
                    "type": "error",
                    "ticker": ticker,
                    "message": "Quote temporarily unavailable",
                }
            await self.send_json(payload)

    def _fetch_quote_payload(self, ticker: str) -> dict:
        session_factory = get_session_factory()
        db = session_factory()
        try:
            quote = market_service.get_quote(db, self.settings, ticker)
            price = quote.price
            if quote.data_status.value == "demo":
                price = _demo_jitter(ticker, price)
            return {
                "type": "quote",
                "ticker": quote.ticker,
                "data": {
                    "price": price,
                    "previous_close": quote.previous_close,
                    "change_abs": quote.change_abs,
                    "change_pct": quote.change_pct,
                    "currency": quote.currency,
                    "data_status": quote.data_status.value,
                    "source": quote.source,
                    "as_of": quote.as_of.isoformat(),
                    "poll_interval_seconds": self.settings.market_poll_interval_seconds,
                },
            }
        finally:
            db.close()
