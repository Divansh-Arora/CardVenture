"""
Cross-chunk deduplication.

Generating cards chunk-by-chunk (instead of one call over the whole
document) means the same concept can legitimately get a card from two
adjacent chunks if it's discussed in both. This collapses near-duplicate
cards, keeping the more complete version.
"""
import re

SIMILARITY_THRESHOLD = 0.75

_STOPWORDS = {
    "what", "is", "are", "a", "an", "the", "of", "to", "in", "on", "for",
    "and", "or", "how", "does", "do", "why", "which", "when", "where",
    "explain", "define", "describe",
}


def _normalize(text: str) -> str:
    text = (text or "").lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _content_words(text: str) -> set[str]:
    return {w for w in text.split() if w not in _STOPWORDS}


def _token_similarity(a_norm: str, b_norm: str) -> float:
    """Token-containment similarity over content words (question/answer
    boilerplate like "what is the" stripped out first) rather than raw
    character diffing: two cards about the same thing are often phrased
    with different amounts of detail ("What is the discriminant?" vs "What
    is the discriminant of a quadratic equation?"), which SequenceMatcher
    on raw characters under-scores because of the length difference, while
    comparing full token sets over-scores because of shared stopwords.

    A size-ratio guard keeps this from over-merging: a short, generic
    string should not absorb a much longer, differently-framed one just
    because they share one word."""
    a_words = _content_words(a_norm)
    b_words = _content_words(b_norm)
    if not a_words or not b_words:
        return 0.0

    shorter, longer = sorted([a_words, b_words], key=len)
    if len(longer) > len(shorter) * 3:
        return 0.0

    overlap = len(a_words & b_words)
    return overlap / len(shorter)


def _pair_similarity(a: dict, b: dict) -> float:
    """A card is a (question, answer) pair, and duplicates show up in
    either half: sometimes two chunks ask the near-identical question in
    different words (question similarity catches this); sometimes they
    ask a differently-framed question that lands on the same fact, e.g.
    "What does mitosis produce?" vs "Name the result of cell division
    called mitosis." -- which share almost no question words but have
    near-identical answers (answer similarity catches this instead).
    Taking the max of the two catches both failure modes without making
    either comparison individually more aggressive."""
    q_sim = _token_similarity(_normalize(a["question"]), _normalize(b["question"]))
    a_sim = _token_similarity(_normalize(a["answer"]), _normalize(b["answer"]))
    return max(q_sim, a_sim)


def _completeness_score(card: dict) -> int:
    """Rough proxy for 'which duplicate is the better one to keep'."""
    return len(card.get("answer", "")) + len(card.get("explanation") or "")


def deduplicate_cards(cards: list[dict]) -> list[dict]:
    kept: list[dict] = []

    for card in cards:
        duplicate_index = None

        for i, existing in enumerate(kept):
            # Two cards about the same term but with different card_types
            # (e.g. a "definition" card and a "misconception" card, both
            # about photosynthesis) are intentionally different cards --
            # the generation prompt asks for systematic coverage across
            # categories, so collapsing across types would silently undo
            # that coverage. Only cards of the same category are ever
            # considered duplicates of each other.
            if card.get("card_type") != existing.get("card_type"):
                continue
            if _pair_similarity(card, existing) >= SIMILARITY_THRESHOLD:
                duplicate_index = i
                break

        if duplicate_index is None:
            kept.append(card)
        elif _completeness_score(card) > _completeness_score(kept[duplicate_index]):
            # Replace the weaker duplicate with this more complete version
            kept[duplicate_index] = card

    return kept
