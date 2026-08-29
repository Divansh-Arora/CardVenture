"""
End-to-end pipeline test: pages -> filter -> chunk -> generate -> dedupe ->
quality -> final cards. Exercises the full generate_deck_cards() orchestrator
with a fake LLM that echoes back the <<PAGE n>> marker nearest each fact,
which is exactly what the real prompt asks the model to do -- letting this
test assert that source_page attribution actually reflects where in the
chunk each card's content came from, not just the chunk's first page.
"""
import json
import re

from app.services.chunking import PAGE_MARKER_RE
from app.services.content_filter import filter_pages
from app.services.pdf_service import PageText
from app.services import llm_service


def _fake_completion(cards):
    from types import SimpleNamespace

    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(cards)))]
    )


def test_source_page_reflects_true_origin_within_a_multi_page_chunk(mocker):
    """Regression test for the old bug where every card in a chunk was
    stamped with chunk.start_page regardless of which page it actually
    came from."""
    pages = [
        PageText(page_number=5, text="Osmosis is the movement of water across a membrane."),
        PageText(page_number=6, text="Diffusion is the movement of particles from high to low concentration."),
    ]

    def fake_create(*args, **kwargs):
        user_message = kwargs["messages"][1]["content"]
        # Simulate the model correctly copying the nearest preceding
        # <<PAGE n>> marker for each fact, the way the real prompt asks.
        markers = PAGE_MARKER_RE.findall(user_message)
        cards = []
        if "Osmosis" in user_message:
            cards.append(
                {
                    "question": "What is osmosis?",
                    "answer": "The movement of water across a membrane.",
                    "card_type": "definition",
                    "difficulty": "medium",
                    "topic": "Membrane Transport",
                    "explanation": None,
                    "source_page": int(markers[0]),
                }
            )
        if "Diffusion" in user_message:
            cards.append(
                {
                    "question": "What is diffusion?",
                    "answer": "The movement of particles from high to low concentration.",
                    "card_type": "definition",
                    "difficulty": "medium",
                    "topic": "Membrane Transport",
                    "explanation": None,
                    "source_page": int(markers[-1]),
                }
            )
        return _fake_completion(cards)

    mocker.patch.object(llm_service._client.chat.completions, "create", side_effect=fake_create)
    mocker.patch.object(llm_service.time, "sleep")

    cards = llm_service.generate_deck_cards(pages)

    by_question = {c["question"]: c for c in cards}
    assert by_question["What is osmosis?"]["source_page"] == 5
    assert by_question["What is diffusion?"]["source_page"] == 6


def test_hallucinated_source_page_falls_back_to_chunk_start(mocker):
    """If the model reports a page number that isn't actually in this
    chunk, that's untrustworthy -- fall back to the chunk's first page
    rather than persist a value that's definitely wrong."""
    pages = [PageText(page_number=9, text="Some fact about capacitors and charge storage.")]

    def fake_create(*args, **kwargs):
        return _fake_completion(
            [
                {
                    "question": "What stores electrical charge?",
                    "answer": "A capacitor.",
                    "card_type": "definition",
                    "difficulty": "easy",
                    "topic": "Circuits",
                    "explanation": None,
                    "source_page": 999,  # not a real page in this document
                }
            ]
        )

    mocker.patch.object(llm_service._client.chat.completions, "create", side_effect=fake_create)
    mocker.patch.object(llm_service.time, "sleep")

    cards = llm_service.generate_deck_cards(pages)
    assert cards[0]["source_page"] == 9


def test_answer_key_page_is_excluded_before_generation(mocker):
    pages = [
        PageText(page_number=1, text="Newton's second law relates force, mass, and acceleration."),
        PageText(page_number=2, text="Answer Key\n1. b\n2. a\n3. c\n4. d\n5. a\n6. b\n7. c"),
    ]

    seen_texts = []

    def fake_create(*args, **kwargs):
        user_message = kwargs["messages"][1]["content"]
        seen_texts.append(user_message)
        return _fake_completion(
            [
                {
                    "question": "What does Newton's second law relate?",
                    "answer": "Force, mass, and acceleration.",
                    "card_type": "definition",
                    "difficulty": "medium",
                    "topic": "Mechanics",
                    "explanation": None,
                    "source_page": 1,
                }
            ]
        )

    mocker.patch.object(llm_service._client.chat.completions, "create", side_effect=fake_create)
    mocker.patch.object(llm_service.time, "sleep")

    cards = llm_service.generate_deck_cards(pages)

    assert len(cards) == 1
    # The answer-key page's content should never have been sent to the model.
    assert not any("Answer Key" in t for t in seen_texts)
    assert not any(re.search(r"\b1\.\s*b\b", t) for t in seen_texts)


def test_full_pipeline_raises_when_everything_gets_filtered_out():
    import pytest

    pages = [
        PageText(page_number=1, text="Table of Contents\nChapter 1 .......... 1\nChapter 2 .......... 20\nChapter 3 .......... 45"),
    ]
    with pytest.raises(ValueError, match="table of contents|index|answer key"):
        llm_service.generate_deck_cards(pages)
