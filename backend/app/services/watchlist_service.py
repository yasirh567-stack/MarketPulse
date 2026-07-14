from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.watchlist import Watchlist, WatchlistItem


def get_or_create_watchlist(db: Session, owner_key: str) -> Watchlist:
    row = db.scalar(select(Watchlist).where(Watchlist.owner_key == owner_key))
    if row is not None:
        return row
    row = Watchlist(owner_key=owner_key)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def add_item(db: Session, watchlist: Watchlist, ticker: str) -> WatchlistItem:
    ticker = ticker.upper()
    existing = db.scalar(
        select(WatchlistItem).where(
            WatchlistItem.watchlist_id == watchlist.id, WatchlistItem.ticker == ticker
        )
    )
    if existing is not None:
        return existing
    item = WatchlistItem(watchlist_id=watchlist.id, ticker=ticker)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def remove_item(db: Session, watchlist: Watchlist, ticker: str) -> bool:
    ticker = ticker.upper()
    existing = db.scalar(
        select(WatchlistItem).where(
            WatchlistItem.watchlist_id == watchlist.id, WatchlistItem.ticker == ticker
        )
    )
    if existing is None:
        return False
    db.delete(existing)
    db.commit()
    return True
