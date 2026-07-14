"""Retrieval-based market assistant — no LLM required.

Answers are built entirely from rows already stored in the database (recent
news, detected events, aggregated sentiment, latest quote). TF-IDF + cosine
similarity ranks which of those rows are most relevant to the user's
question; a small set of deterministic templates then turns the ranked
evidence into a readable answer with citations. Because every sentence is
either a template or a direct quote/field from a stored row, the assistant
cannot fabricate a citation, price, or headline that doesn't exist.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.services import event_service, market_service, news_service, sentiment_service

NEGATIVE_EVENT_CATEGORIES = {"lawsuit", "investigation", "analyst_downgrade", "executive_departure"}


@dataclass
class EvidenceItem:
    kind: str  # "news" | "event"
    title: str
    url: str | None
    published_at: datetime
    extra: dict


@dataclass
class AssistantAnswer:
    ticker: str
    question: str
    answer: str
    citations: list[dict]
    disclaimer: str
    data_sufficient: bool


DISCLAIMER = (
    "This answer summarizes recent, correlated information retrieved for this ticker — it is "
    "not proof of causality and is not financial advice."
)


def _gather_evidence(db: Session, settings: Settings, ticker: str) -> list[EvidenceItem]:
    articles = news_service.fetch_and_store_news(db, settings, ticker, limit=20)
    events = event_service.get_recent_events(db, ticker, limit=20)

    items: list[EvidenceItem] = []
    for a in articles:
        items.append(
            EvidenceItem(
                kind="news",
                title=a.title,
                url=a.url,
                published_at=a.published_at,
                extra={"summary": a.summary or "", "source": a.source},
            )
        )
    for e in events:
        items.append(
            EvidenceItem(
                kind="event",
                title=f"[{e.category.replace('_', ' ').title()}] {e.headline}",
                url=e.source_url,
                published_at=e.published_at,
                extra={"category": e.category, "confidence": e.confidence},
            )
        )
    return sorted(items, key=lambda i: i.published_at, reverse=True)


def _rank_by_similarity(
    question: str, items: list[EvidenceItem], top_n: int = 5
) -> list[EvidenceItem]:
    if not items:
        return []
    corpus = [f"{i.title} {i.extra.get('summary', '')}" for i in items]
    vectorizer = TfidfVectorizer(stop_words="english", max_features=2000)
    try:
        doc_matrix = vectorizer.fit_transform(corpus + [question])
    except ValueError:
        return items[:top_n]  # empty vocabulary (e.g. question is all stopwords)
    question_vec = doc_matrix[-1]
    doc_vecs = doc_matrix[:-1]
    similarities = cosine_similarity(question_vec, doc_vecs).flatten()
    ranked = sorted(zip(items, similarities, strict=True), key=lambda t: t[1], reverse=True)
    return [item for item, score in ranked[:top_n] if score > 0] or items[:top_n]


def _classify_question(question: str) -> str:
    q = question.lower()
    if re.search(r"\brisk", q):
        return "risks"
    if re.search(r"sentiment.*(negative|worse|worsen|decline|drop)|more negative", q):
        return "sentiment_trend"
    if re.search(r"most relevant|which event|main event", q):
        return "top_event"
    return "why_moving"


def answer_question(db: Session, settings: Settings, ticker: str, question: str) -> AssistantAnswer:
    ticker = ticker.upper()
    evidence = _gather_evidence(db, settings, ticker)
    question_type = _classify_question(question)

    if question_type == "risks":
        risk_items = [
            e
            for e in evidence
            if e.kind == "event" and e.extra.get("category") in NEGATIVE_EVENT_CATEGORIES
        ]
        ranked = risk_items[:5] if risk_items else _rank_by_similarity(question, evidence)
        if not risk_items:
            body = (
                "No lawsuit, investigation, downgrade, or executive-departure events were "
                f"detected in {ticker}'s recent stored headlines. "
            )
            if evidence:
                body += "The most topically related recent items are listed below for context."
            else:
                body += (
                    "There is not enough recent stored news for this ticker to answer confidently."
                )
        else:
            categories = ", ".join(
                sorted({e.extra["category"].replace("_", " ") for e in risk_items})
            )
            body = (
                f"Recent headlines for {ticker} flag the following risk-related "
                f"categories: {categories}."
            )
        return _build_answer(ticker, question, body, ranked, bool(evidence))

    if question_type == "sentiment_trend":
        timeline = sentiment_service.aggregate_timeline(db, ticker, limit_buckets=30)
        if len(timeline) < 2:
            body = (
                f"There isn't enough recent sentiment history stored for {ticker} "
                "to assess a trend yet."
            )
            return _build_answer(
                ticker, question, body, _rank_by_similarity(question, evidence), bool(timeline)
            )
        recent_avg = sum(p["avg_compound"] for p in timeline[-3:]) / min(3, len(timeline))
        older_avg = sum(p["avg_compound"] for p in timeline[:-3]) / max(len(timeline) - 3, 1)
        delta = recent_avg - older_avg
        if delta < -0.05:
            body = (
                f"Yes — recent average sentiment for {ticker} ({recent_avg:.2f}) is lower than "
                f"the earlier period in the stored window ({older_avg:.2f}), a shift of "
                f"{delta:+.2f} on the compound scale."
            )
        elif delta > 0.05:
            body = (
                f"No — sentiment for {ticker} has actually improved recently ({recent_avg:.2f} vs. "
                f"{older_avg:.2f} earlier in the stored window, {delta:+.2f})."
            )
        else:
            body = (
                f"Sentiment for {ticker} has been roughly stable recently ({recent_avg:.2f} vs. "
                f"{older_avg:.2f} earlier, {delta:+.2f})."
            )
        return _build_answer(ticker, question, body, _rank_by_similarity(question, evidence), True)

    if question_type == "top_event":
        ranked = _rank_by_similarity(
            question, [e for e in evidence if e.kind == "event"] or evidence
        )
        if not ranked:
            body = f"No detected events are currently stored for {ticker}."
            return _build_answer(ticker, question, body, [], False)
        top = ranked[0]
        body = (
            f'The most relevant recent item for {ticker} is: "{top.title}" '
            f"({top.published_at.date().isoformat()})."
        )
        return _build_answer(ticker, question, body, ranked, True)

    # default: "why is this stock moving?"
    ranked = _rank_by_similarity(question, evidence)
    try:
        quote = market_service.get_quote(db, settings, ticker)
        change_note = (
            f"{ticker} is currently priced at {quote.price:.2f} {quote.currency}, "
            f"{'up' if (quote.change_pct or 0) >= 0 else 'down'} {abs(quote.change_pct or 0):.2f}% "
            f"from the previous close ({quote.data_status.value} data)."
        )
    except Exception:
        change_note = f"Current price data for {ticker} is unavailable right now."

    if not evidence:
        body = (
            f"{change_note} There is not enough recent stored news or event data to "
            "explain the move further."
        )
        return _build_answer(ticker, question, body, [], False)

    top_titles = "; ".join(f'"{e.title}"' for e in ranked[:3])
    body = f"{change_note} The most topically relevant recent items are: {top_titles}."
    return _build_answer(ticker, question, body, ranked, True)


def _build_answer(
    ticker: str, question: str, body: str, ranked: list[EvidenceItem], data_sufficient: bool
) -> AssistantAnswer:
    citations = [
        {
            "title": e.title,
            "url": e.url,
            "published_at": e.published_at.isoformat(),
            "kind": e.kind,
        }
        for e in ranked
    ]
    return AssistantAnswer(
        ticker=ticker,
        question=question,
        answer=body,
        citations=citations,
        disclaimer=DISCLAIMER,
        data_sufficient=data_sufficient,
    )
