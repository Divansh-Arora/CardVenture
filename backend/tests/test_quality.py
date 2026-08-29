"""Rule-based quality filter: reject thin/malformed cards, default invalid categories."""
from app.services.quality import quality_check


def _card(**overrides):
    base = {
        "question": "What is the capital of France?",
        "answer": "Paris",
        "card_type": "definition",
        "difficulty": "easy",
        "topic": "Geography",
        "explanation": "It's also the largest city in France.",
        "source_page": 3,
    }
    base.update(overrides)
    return base


def test_valid_card_passes_through():
    result = quality_check([_card()])
    assert len(result) == 1
    assert result[0]["answer"] == "Paris"


def test_too_short_question_is_rejected():
    result = quality_check([_card(question="Huh?")])
    assert result == []


def test_too_short_answer_is_rejected():
    result = quality_check([_card(answer="P")])
    assert result == []


def test_question_that_just_restates_answer_is_rejected():
    result = quality_check([_card(question="Paris", answer="Paris")])
    assert result == []


def test_invalid_card_type_defaults_to_definition():
    result = quality_check([_card(card_type="not_a_real_type")])
    assert result[0]["card_type"] == "definition"


def test_invalid_difficulty_defaults_to_medium():
    result = quality_check([_card(difficulty="impossible")])
    assert result[0]["difficulty"] == "medium"


def test_blank_explanation_becomes_none():
    result = quality_check([_card(explanation="   ")])
    assert result[0]["explanation"] is None


def test_missing_topic_becomes_none():
    result = quality_check([_card(topic=None)])
    assert result[0]["topic"] is None


def test_source_page_is_preserved():
    result = quality_check([_card(source_page=42)])
    assert result[0]["source_page"] == 42


def test_multiple_cards_only_bad_ones_are_dropped():
    cards = [_card(), _card(question="Huh?"), _card(question="What is the capital of Germany?", answer="Berlin")]
    result = quality_check(cards)
    assert len(result) == 2
