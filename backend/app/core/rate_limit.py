"""API rate limiting via slowapi (in-memory token bucket per client IP).

In-memory storage is sufficient here: rate limiting only needs to survive a
single process's uptime to prevent abuse/accidental hammering of
resource-intensive routes (training, backtests, assistant queries) — it does
not need to be correct across multiple processes for this project's scope.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import get_settings

limiter = Limiter(key_func=get_remote_address, default_limits=[])


def default_rate_limit() -> str:
    return f"{get_settings().rate_limit_per_minute}/minute"
