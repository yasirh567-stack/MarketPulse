"""Pydantic models for validated WebSocket client messages.

Every inbound message is parsed through one of these before being acted on —
unvalidated dict access on client input is how you end up with a crash (or
worse) from a malformed frame.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, field_validator

TICKER_PATTERN = re.compile(r"^[A-Za-z.\-]{1,10}$")


class ClientMessage(BaseModel):
    action: str  # "subscribe" | "unsubscribe" | "ping"
    ticker: str | None = None

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        if v not in {"subscribe", "unsubscribe", "ping"}:
            raise ValueError("action must be one of: subscribe, unsubscribe, ping")
        return v

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip().upper()
        if not TICKER_PATTERN.match(v):
            raise ValueError("Invalid ticker symbol")
        return v
