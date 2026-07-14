"""Watchlist endpoints.

No authentication is required for the initial release (per spec). Each
browser generates and persists its own anonymous identifier in localStorage;
that identifier IS the `watchlist_id` path segment here — the backend simply
gets-or-creates a Watchlist row keyed by that string. This keeps the contract
simple (`/watchlists/{watchlist_id}/items`) while leaving room to swap in real
auth later without changing the shape of the API.
"""

from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, Path

from app.api.deps import DbSession
from app.schemas.watchlist import AddWatchlistItemRequest, WatchlistItemResponse, WatchlistResponse
from app.services import watchlist_service

router = APIRouter()

OWNER_KEY_PATTERN = re.compile(r"^[A-Za-z0-9_\-]{6,64}$")


def _validate_owner_key(owner_key: str) -> str:
    if not OWNER_KEY_PATTERN.match(owner_key):
        raise HTTPException(status_code=422, detail="Invalid watchlist identifier")
    return owner_key


@router.get("/{watchlist_id}", response_model=WatchlistResponse)
def get_watchlist(db: DbSession, watchlist_id: str = Path(...)):
    owner_key = _validate_owner_key(watchlist_id)
    wl = watchlist_service.get_or_create_watchlist(db, owner_key)
    return WatchlistResponse(
        watchlist_id=wl.id,
        owner_key=wl.owner_key,
        items=[WatchlistItemResponse.model_validate(i) for i in wl.items],
    )


@router.post("/{watchlist_id}/items", response_model=WatchlistResponse, status_code=201)
def add_watchlist_item(db: DbSession, body: AddWatchlistItemRequest, watchlist_id: str = Path(...)):
    owner_key = _validate_owner_key(watchlist_id)
    wl = watchlist_service.get_or_create_watchlist(db, owner_key)
    watchlist_service.add_item(db, wl, body.ticker)
    db.refresh(wl)
    return WatchlistResponse(
        watchlist_id=wl.id,
        owner_key=wl.owner_key,
        items=[WatchlistItemResponse.model_validate(i) for i in wl.items],
    )


@router.delete("/{watchlist_id}/items/{ticker}", response_model=WatchlistResponse)
def remove_watchlist_item(db: DbSession, watchlist_id: str = Path(...), ticker: str = Path(...)):
    owner_key = _validate_owner_key(watchlist_id)
    wl = watchlist_service.get_or_create_watchlist(db, owner_key)
    watchlist_service.remove_item(db, wl, ticker)
    db.refresh(wl)
    return WatchlistResponse(
        watchlist_id=wl.id,
        owner_key=wl.owner_key,
        items=[WatchlistItemResponse.model_validate(i) for i in wl.items],
    )
