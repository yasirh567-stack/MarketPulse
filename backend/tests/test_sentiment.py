"""Sentiment scoring tests covering the finance-language cases called out in
the spec: bullish, bearish, neutral, negated, and ambiguous phrasing."""

from app.nlp.sentiment import score_with_vader
from app.schemas.common import SentimentLabel


def test_bullish_headline_scores_positive():
    result = score_with_vader(
        "Shares surged after the company reported excellent results and a positive outlook."
    )
    assert result.label == SentimentLabel.BULLISH
    assert result.compound > 0


def test_bearish_headline_scores_negative():
    result = score_with_vader(
        "Company posts massive losses and warns of bankruptcy risk amid fraud investigation."
    )
    assert result.label == SentimentLabel.BEARISH
    assert result.compound < 0


def test_neutral_headline_scores_neutral():
    result = score_with_vader(
        "The company will report quarterly earnings on Thursday after market close."
    )
    assert result.label == SentimentLabel.NEUTRAL


def test_negated_statement_flips_sentiment():
    positive = score_with_vader("The results were good.")
    negated = score_with_vader("The results were not good.")
    assert negated.compound < positive.compound
    assert negated.label != SentimentLabel.BULLISH


def test_mixed_signal_headline_is_not_classified_bullish():
    # "beat estimates but cut guidance" mixes good and bad news — a lexicon
    # scorer like VADER (unlike FinBERT) has no notion of "beat"/"cut" as
    # finance-specific signals, so it should not read this as confidently
    # bullish; the model-comparison feature exists precisely to surface
    # cases like this where a finance-tuned model might disagree.
    result = score_with_vader("The company beat estimates but cut its full-year guidance.")
    assert result.label != SentimentLabel.BULLISH


def test_every_score_records_model_provenance():
    result = score_with_vader("Shares rose after the announcement.")
    assert result.model_name == "vader"
    assert result.model_version
