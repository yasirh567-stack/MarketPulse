from app.nlp.event_detection import detect_events


def _categories(title: str, summary: str = "") -> set[str]:
    return {m.category for m in detect_events(title, summary)}


def test_earnings_keyword_detected():
    assert "earnings" in _categories("Company Reports Quarterly Earnings Above Estimates")


def test_acquisition_keyword_detected():
    assert "acquisition" in _categories("Company Announces Acquisition of Smaller Rival")


def test_analyst_upgrade_not_confused_with_acquisition():
    # Regression test: "Upgrades ... to Buy" previously false-matched the
    # acquisition category via the substring "to buy" inside the old keyword
    # list; it must only match analyst_upgrade now.
    cats = _categories("Analyst Upgrades Company to Buy, Cites Strong Momentum")
    assert "analyst_upgrade" in cats
    assert "acquisition" not in cats


def test_word_boundary_avoids_partial_word_false_positive():
    # "product lineup" must not match the "product line" keyword.
    cats = _categories(
        "Company Reports Strong Demand", "Growth continued across its product lineup."
    )
    assert "product_launch" not in cats


def test_product_launch_keyword_detected_on_real_phrase():
    assert "product_launch" in _categories("Company Unveils New Product Line at Annual Event")


def test_no_match_returns_empty():
    assert _categories("The sky was clear today with mild temperatures") == set()


def test_confidence_is_bounded_and_never_certain():
    matches = detect_events(
        "Company Reports Earnings, Raises Guidance, Announces Dividend and Stock Split"
    )
    assert matches
    for m in matches:
        assert 0 < m.confidence <= 0.95
