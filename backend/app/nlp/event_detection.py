"""Transparent, rule-based event detection over headlines.

This is intentionally simple keyword/phrase matching rather than a trained
classifier: every detection is fully explainable ("matched keywords: X, Y"),
which matters more here than marginal recall gains from a black-box model.
Detections are never presented as causally certain — they're "this headline
mentions a category," not "this category caused the price move."
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# category -> keyword/phrase list (case-insensitive substring match on title+summary)
EVENT_KEYWORDS: dict[str, list[str]] = {
    "earnings": [
        "earnings",
        "quarterly revenue",
        "quarterly results",
        "eps",
        "beat estimates",
        "missed estimates",
    ],
    "guidance": [
        "guidance",
        "outlook",
        "forecast raised",
        "forecast cut",
        "raises guidance",
        "cuts guidance",
        "lowered its full-year",
    ],
    "acquisition": ["acquisition", "acquire", "merger", "takeover", "agreed to acquire"],
    "lawsuit": ["lawsuit", "sued", "litigation", "class action"],
    "investigation": ["investigation", "probe", "regulator", "inquiry", "subpoena"],
    "product_launch": ["unveils", "launches", "announces new", "new product", "product line"],
    "executive_departure": [
        "steps down",
        "resigns",
        "departs",
        "departure",
        "ceo exit",
        "executive left",
    ],
    "analyst_upgrade": ["upgrades", "upgraded to", "raises price target", "buy rating"],
    "analyst_downgrade": ["downgrades", "downgraded to", "cuts price target", "sell rating"],
    "dividend": ["dividend"],
    "stock_split": ["stock split"],
    "macro": [
        "federal reserve",
        "interest rate",
        "inflation report",
        "jobs report",
        "export controls",
        "tariff",
    ],
}


@dataclass
class EventMatch:
    category: str
    matched_keywords: list[str]
    confidence: float


def detect_events(title: str, summary: str = "") -> list[EventMatch]:
    """Returns zero or more category matches for a headline. Confidence is a
    simple, transparent function of how many distinct keywords matched (not a
    learned probability) — capped at 0.95 so it never reads as certainty."""
    haystack = f"{title} {summary}".lower()
    matches: list[EventMatch] = []
    for category, keywords in EVENT_KEYWORDS.items():
        hits = [kw for kw in keywords if re.search(rf"\b{re.escape(kw)}\b", haystack)]
        if hits:
            confidence = min(0.5 + 0.15 * len(hits), 0.95)
            matches.append(
                EventMatch(category=category, matched_keywords=hits, confidence=confidence)
            )
    return matches
