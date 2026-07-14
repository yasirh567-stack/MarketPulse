"""Sanitization helpers for externally sourced text (news/social content).

Anything that came from an RSS feed, Reddit, or a scraped page is untrusted
input as far as the frontend is concerned. We strip all HTML/script content
before it's ever stored or rendered.
"""

from __future__ import annotations

from urllib.parse import urlparse

import bleach

_ALLOWED_TAGS: list[str] = []  # plain text only — financial headlines don't need markup


def clean_text(raw: str | None, max_length: int = 2000) -> str:
    if not raw:
        return ""
    text = bleach.clean(raw, tags=_ALLOWED_TAGS, strip=True)
    text = " ".join(text.split())  # collapse whitespace/newlines from feed XML
    return text[:max_length]


def safe_url(raw: str | None) -> str | None:
    """Only allow http(s) URLs through; reject javascript:/data: etc. to avoid
    stored-XSS-via-link and open-redirect-style issues in the frontend."""
    if not raw:
        return None
    parsed = urlparse(raw.strip())
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return None
    return raw.strip()
