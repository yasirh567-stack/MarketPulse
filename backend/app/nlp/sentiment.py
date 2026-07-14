"""Sentiment scoring: VADER (always available) with optional FinBERT.

VADER is a lexicon/rule-based scorer tuned for general (incl. social media)
text; it needs no model download and runs instantly, so it's the default and
the guaranteed-available path. FinBERT is a finance-tuned transformer that
tends to handle domain phrasing ("beat guidance", "missed on the top line")
better, but requires torch+transformers and a one-time model download — so it
is opt-in (`ENABLE_FINBERT=true`) and lazily loaded exactly once per process.

Every score returned by `SentimentEngine.score` records which model produced
it, so the UI can honestly display "VADER" vs "FinBERT" side by side instead
of implying a single ground truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from app.core.logging import get_logger
from app.schemas.common import SentimentLabel

logger = get_logger("app.nlp.sentiment")

VADER_MODEL_NAME = "vader"
VADER_MODEL_VERSION = "3.3.2"
FINBERT_MODEL_NAME = "finbert"
FINBERT_MODEL_VERSION = "ProsusAI/finbert"

# Compound-score thresholds recommended by VADER's own documentation.
BULLISH_THRESHOLD = 0.05
BEARISH_THRESHOLD = -0.05


@dataclass
class SentimentResult:
    compound: float
    label: SentimentLabel
    confidence: float | None
    model_name: str
    model_version: str


def _label_from_compound(compound: float) -> SentimentLabel:
    if compound >= BULLISH_THRESHOLD:
        return SentimentLabel.BULLISH
    if compound <= BEARISH_THRESHOLD:
        return SentimentLabel.BEARISH
    return SentimentLabel.NEUTRAL


@lru_cache(maxsize=1)
def _get_vader() -> SentimentIntensityAnalyzer:
    return SentimentIntensityAnalyzer()


def score_with_vader(text: str) -> SentimentResult:
    analyzer = _get_vader()
    scores = analyzer.polarity_scores(text or "")
    compound = scores["compound"]
    return SentimentResult(
        compound=compound,
        label=_label_from_compound(compound),
        confidence=max(scores["pos"], scores["neu"], scores["neg"]),
        model_name=VADER_MODEL_NAME,
        model_version=VADER_MODEL_VERSION,
    )


class FinBertUnavailableError(Exception):
    pass


@lru_cache(maxsize=1)
def _get_finbert_pipeline():
    """Lazily imports torch/transformers and loads FinBERT exactly once.

    Raises FinBertUnavailableError on ANY failure (missing deps, no network
    for the first download, out of memory, etc.) so callers can fall back to
    VADER instead of crashing the request.
    """
    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
    except ImportError as exc:
        raise FinBertUnavailableError("transformers/torch not installed") from exc

    try:
        tokenizer = AutoTokenizer.from_pretrained(FINBERT_MODEL_VERSION)
        model = AutoModelForSequenceClassification.from_pretrained(FINBERT_MODEL_VERSION)
        return pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)
    except Exception as exc:  # network failure, OOM, corrupted cache, etc.
        raise FinBertUnavailableError(str(exc)) from exc


def finbert_available() -> bool:
    """Cheap check used by /health — attempts the lazy load and reports
    whether it succeeded, without raising."""
    try:
        _get_finbert_pipeline()
        return True
    except FinBertUnavailableError:
        return False


def score_with_finbert(text: str) -> SentimentResult:
    clf = _get_finbert_pipeline()
    result = clf(text[:512])[0]  # FinBERT's tokenizer truncates around this length anyway
    raw_label = result["label"].lower()
    finbert_to_compound = {"positive": 1.0, "negative": -1.0, "neutral": 0.0}
    signed = finbert_to_compound.get(raw_label, 0.0) * result["score"]
    label = {
        "positive": SentimentLabel.BULLISH,
        "negative": SentimentLabel.BEARISH,
        "neutral": SentimentLabel.NEUTRAL,
    }.get(raw_label, SentimentLabel.NEUTRAL)
    return SentimentResult(
        compound=round(signed, 4),
        label=label,
        confidence=float(result["score"]),
        model_name=FINBERT_MODEL_NAME,
        model_version=FINBERT_MODEL_VERSION,
    )


class SentimentEngine:
    """Facade used by services/routers. Encapsulates the FinBERT-with-VADER-
    fallback decision so callers just ask for "the best available score"."""

    def __init__(self, enable_finbert: bool):
        self.enable_finbert = enable_finbert
        self._finbert_broken = False

    @property
    def active_model_name(self) -> str:
        if self.enable_finbert and not self._finbert_broken:
            return FINBERT_MODEL_NAME
        return VADER_MODEL_NAME

    def score(self, text: str) -> SentimentResult:
        if self.enable_finbert and not self._finbert_broken:
            try:
                return score_with_finbert(text)
            except FinBertUnavailableError as exc:
                logger.warning("FinBERT unavailable, falling back to VADER: %s", exc)
                self._finbert_broken = True
        return score_with_vader(text)

    def score_batch(self, texts: list[str]) -> list[SentimentResult]:
        """Batch entry point. FinBERT's HF pipeline batches internally when
        given a list; VADER has no meaningful batching benefit but the
        uniform signature keeps callers simple."""
        return [self.score(t) for t in texts]
