"""Shared pytest fixtures.

Each test gets a fresh, isolated SQLite file DB and a cleared settings/engine
cache, so tests never see state left over by another test. DEMO_MODE is
forced on so no test ever depends on network access to yfinance/RSS.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DEMO_MODE", "true")
os.environ.setdefault("ENABLE_FINBERT", "false")
os.environ.setdefault("ENABLE_REDDIT", "false")
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "1000")
os.environ.setdefault("MARKET_POLL_INTERVAL_SECONDS", "0.2")


@pytest.fixture()
def db_path(tmp_path) -> Iterator[str]:
    path = tmp_path / "test.db"
    yield str(path)


@pytest.fixture()
def client(db_path, monkeypatch) -> Iterator[TestClient]:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("DEMO_MODE", "true")

    from app.core.config import get_settings
    from app.database import session as db_session
    from app.database.base import Base

    get_settings.cache_clear()
    db_session.reset_engine_for_tests()
    Base.metadata.create_all(bind=db_session.get_engine())

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client

    db_session.reset_engine_for_tests()
    get_settings.cache_clear()
