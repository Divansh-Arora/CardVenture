"""Deduplication: collapse near-duplicate cards, gated by card_type."""
from app.services.dedup import deduplicate_cards


def _card(question, answer, card_type="definition", explanation=None):
    return {
        "question": question,
        "answer": answer,
        "card_type": card_type,
        "difficulty": "medium",
        "topic": "Topic",
        "explanation": explanation,
        "source_page": 1,
    }


def test_exact_duplicate_questions_collapse_to_one():
    cards = [
        _card("What is the discriminant?", "b^2 - 4ac"),
        _card("What is the discriminant?", "b^2 - 4ac"),
    ]
    result = deduplicate_cards(cards)
    assert len(result) == 1


def test_near_duplicate_question_phrasing_collapses():
    cards = [
        _card("What is the discriminant?", "b^2 - 4ac"),
        _card(
            "What is the discriminant of a quadratic equation?",
            "b^2 - 4ac, used to determine the number of real roots",
        ),
    ]
    result = deduplicate_cards(cards)
    assert len(result) == 1
    # The more complete (longer) version should be the one kept.
    assert "quadratic" in result[0]["question"]


def test_keeps_the_more_complete_duplicate():
    short = _card("What is mitosis?", "Cell division.")
    long = _card(
        "What is mitosis?",
        "The process of cell division that produces two genetically identical daughter cells.",
        explanation="It's distinct from meiosis, which produces gametes.",
    )
    result = deduplicate_cards([short, long])
    assert len(result) == 1
    assert result[0]["answer"] == long["answer"]


def test_different_card_types_are_never_merged_even_with_similar_wording():
    definition = _card("What is entropy?", "A measure of disorder in a system.", card_type="definition")
    misconception = _card(
        "What is a common misconception about entropy?",
        "That entropy always decreases locally, when it can decrease locally as long as it increases elsewhere.",
        card_type="misconception",
    )
    result = deduplicate_cards([definition, misconception])
    assert len(result) == 2


def test_genuinely_different_cards_of_the_same_type_are_kept():
    cards = [
        _card("What is a vertex?", "A point where two edges meet."),
        _card(
            "How do you find the vertex of a parabola?",
            "Use x = -b / 2a to find the x-coordinate, then substitute back in.",
            card_type="method",
        ),
    ]
    result = deduplicate_cards(cards)
    assert len(result) == 2


def test_same_fact_different_question_phrasing_caught_via_answer_similarity():
    cards = [
        _card("What does mitosis produce?", "Two genetically identical daughter cells."),
        _card(
            "Name the result of the cell division process called mitosis.",
            "Two genetically identical daughter cells.",
        ),
    ]
    result = deduplicate_cards(cards)
    assert len(result) == 1


def test_empty_list_returns_empty_list():
    assert deduplicate_cards([]) == []


def test_short_generic_question_does_not_absorb_unrelated_long_question():
    cards = [
        _card("What is a cell?", "The basic unit of life."),
        _card(
            "What is the difference between a plant cell and an animal cell in terms of organelles present?",
            "Plant cells have a cell wall and chloroplasts; animal cells do not.",
        ),
    ]
    result = deduplicate_cards(cards)
    assert len(result) == 2
