from app.database.session import get_session_factory
from app.services.instrument_service import get_or_create_instrument


def test_get_or_create_instrument_is_idempotent(client):
    db = get_session_factory()()
    try:
        first = get_or_create_instrument(db, "aapl", name="Apple Inc.")
        second = get_or_create_instrument(db, "AAPL")
        assert first.id == second.id
        assert first.ticker == "AAPL"
        assert first.is_demo is True
    finally:
        db.close()
