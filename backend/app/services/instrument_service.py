from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.instrument import Instrument
from app.providers.demo_data import is_demo_ticker


def get_or_create_instrument(db: Session, ticker: str, name: str | None = None) -> Instrument:
    ticker = ticker.upper()
    row = db.scalar(select(Instrument).where(Instrument.ticker == ticker))
    if row is not None:
        return row
    row = Instrument(
        ticker=ticker,
        name=name or ticker,
        is_demo=is_demo_ticker(ticker),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
