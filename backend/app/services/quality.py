"""
Quality check pass.

Rule-based rather than a second LLM call: for a one-week solo build, an
extra model round-trip per deck to "review" cards it just wrote adds real
latency and cost for a check that mostly catches the same failure modes
(too short, missing fields, malformed category) that clean rules already
catch cheaply. Noted in the README as the natural next step if this needs
to scale further.
"""
from app.models import CardType, Difficulty

MIN_QUESTION_CHARS = 8
MIN_ANSWER_CHARS = 3
VALID_TYPES = {t.value for t in CardType}
VALID_DIFFICULTIES = {d.value for d in Difficulty}


def quality_check(cards: list[dict]) -> list[dict]:
    passed = []
    for card in cards:
        question = (card.get("question") or "").strip()
        answer = (card.get("answer") or "").strip()

        if len(question) < MIN_QUESTION_CHARS or len(answer) < MIN_ANSWER_CHARS:
            continue  # too thin to be a useful card
        if question.rstrip("?.!").lower() == answer.rstrip("?.!").lower():
            continue  # question just restates the answer

        card_type = card.get("card_type")
        if card_type not in VALID_TYPES:
            card_type = CardType.definition.value

        difficulty = card.get("difficulty")
        if difficulty not in VALID_DIFFICULTIES:
            difficulty = Difficulty.medium.value

        passed.append(
            {
                "question": question,
                "answer": answer,
                "explanation": (card.get("explanation") or "").strip() or None,
                "card_type": card_type,
                "difficulty": difficulty,
                "topic": (card.get("topic") or "").strip() or None,
                "source_page": card.get("source_page"),
            }
        )
    return passed
