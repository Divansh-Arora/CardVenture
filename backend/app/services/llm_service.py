"""
Card generation via NVIDIA Nemotron (OpenAI-compatible endpoint) — run per
content chunk instead of once over a truncated blob, and prompted to
systematically cover seven card categories rather than whatever the model
happens to produce.

generate_deck_cards() is the full pipeline:

    pages -> filter_pages -> chunk_pages -> generate per chunk -> merge
          -> deduplicate_cards -> quality_check -> final deck
"""
import json
import re
import time
import logging

from openai import OpenAI

from app.config import settings
from app.services.pdf_service import PageText
from app.services.content_filter import filter_pages
from app.services.chunking import chunk_pages, Chunk
from app.services.dedup import deduplicate_cards
from app.services.quality import quality_check

logger = logging.getLogger(__name__)

_client = OpenAI(
    base_url=settings.nvidia_base_url,
    api_key=settings.nvidia_api_key,
)

# Small delay between chunk calls to stay comfortably under NVIDIA's
# free-tier rate limit (commonly ~40 requests/minute) even for large PDFs
# with many chunks.
SECONDS_BETWEEN_CALLS = 1.6

SYSTEM_PROMPT = """You are an expert teacher creating flashcards from one section of a larger document.

The text you're given has inline markers like <<PAGE 7>> showing where each
original page starts. Use them ONLY to fill in source_page (see below) --
never mention them in a question or answer, and never treat a marker line
itself as content.

Generate 5-8 high-quality flashcards that capture the most important
concepts in this section. Prioritize cards that test understanding over
rote memorization. Use these categories when relevant (skip any that don't
apply -- do not invent content):

- definition: key terms and what they mean
- formula: any formula, equation, or notation, with what each symbol means
- relationship: how two or more concepts connect or depend on each other
- method: a procedure or step-by-step approach described in the text
- worked_example: a concrete example applying a concept, ideally with numbers/steps
- misconception: a common mistake or confusion this material would clarify
- edge_case: an exception, boundary condition, or "what if" scenario

Rules:
- Each card needs: question, answer, card_type (one of the categories
  above, exactly as spelled), difficulty ("easy", "medium", or "hard"),
  topic (a short 2-5 word label for what this card is about), explanation
  (1 sentence of extra context beyond the answer itself, or null if the
  answer is already fully self-contained), and source_page (the integer
  from the single nearest <<PAGE n>> marker before the content this card
  is based on -- copy that number exactly, do not calculate or guess one).
- Avoid vague or trivial cards. Avoid duplicating the same fact twice.
- Only use this section's content -- do not reference material that isn't here.
- Respond with ONLY a JSON array, no other text, no markdown code fences.
- question: concise and direct; avoid unnecessary wording.
- answer: concise, maximum 2 sentences.
- explanation: maximum 1 short sentence.
- topic: exactly 2-5 words.
- Do not add unnecessary detail or repetition.
- Keep each card focused on one key learning point.

Example:
[
  {"question": "What is the discriminant of a quadratic equation?", "answer": "b^2 - 4ac", "card_type": "formula", "difficulty": "medium", "topic": "Quadratic Equations", "explanation": "It determines the number and type of roots the equation has.", "source_page": 42}
]
"""


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _resolve_source_page(reported, valid_pages: set[int], fallback: int) -> int:
    """The model is asked to copy a <<PAGE n>> marker verbatim rather than
    compute a page number itself, but it can still misreport (wrong type,
    a stray number, a page from a different chunk it mis-remembers, etc).
    Trusting an unvalidated value would just swap "always chunk.start_page"
    for "occasionally a hallucinated page" -- neither is real attribution.
    So the reported value is only trusted if it's actually one of the pages
    this chunk contains; anything else falls back to the chunk's first page,
    which is always correct at worst to a few-page granularity.
    """
    try:
        page = int(reported)
    except (TypeError, ValueError):
        return fallback
    return page if page in valid_pages else fallback


def _generate_cards_for_chunk(chunk: Chunk) -> list[dict]:
    completion = _client.chat.completions.create(
        model=settings.nvidia_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": chunk.text},
        ],
        temperature=0.4,
        max_tokens=1200,
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    )

    raw = completion.choices[0].message.content
    finish_reason = completion.choices[0].finish_reason
    cleaned = _strip_code_fences(raw)

    if not raw:
        logger.warning(
            "Chunk (pages %d-%d) returned empty response; finish_reason=%s",
            chunk.start_page,
            chunk.end_page,
            finish_reason,
        )
        return []

    try:
        cards = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning(
            "Chunk (pages %d-%d) returned non-JSON output; finish_reason=%s, "
            "content_length=%d, content_preview=%r",
            chunk.start_page,
            chunk.end_page,
            finish_reason,
            len(raw),
            raw[:500],
        )
        return []

    if not isinstance(cards, list):
        return []

    valid_pages = set(chunk.page_numbers) or {chunk.start_page}
    for card in cards:
        card["source_page"] = _resolve_source_page(
            card.get("source_page"), valid_pages, fallback=chunk.start_page
        )

    return cards


def generate_deck_cards(pages: list[PageText]) -> list[dict]:
    """Full pipeline: pages -> filter -> chunks -> per-chunk generation ->
    merge -> dedupe -> quality check -> final card list ready to persist."""
    total_start = time.perf_counter()
    input_page_count = len(pages)
    logger.info("generate_deck_cards: input_pages=%d", input_page_count)

    filter_start = time.perf_counter()
    filtered = filter_pages(pages)
    filter_elapsed = time.perf_counter() - filter_start
    logger.info("filter_pages: elapsed=%.3fs, dropped_pages=%d, kept_pages=%d",
                filter_elapsed, len(filtered.dropped_pages), len(filtered.kept))

    if filtered.dropped_pages:
        logger.info(
            "Skipped %d non-instructional page(s) before generation: %s",
            len(filtered.dropped_pages),
            filtered.dropped_reasons,
        )

    if not filtered.kept:
        raise ValueError(
            "This document only contains pages that look like a table of "
            "contents, index, or answer key -- no instructional content to "
            "generate cards from."
        )

    chunk_start = time.perf_counter()
    chunks = chunk_pages(filtered.kept)
    chunk_elapsed = time.perf_counter() - chunk_start
    logger.info("chunk_pages: elapsed=%.3fs, num_chunks=%d", chunk_elapsed, len(chunks))

    if not chunks:
        raise ValueError("No content could be chunked from this document.")

    all_cards: list[dict] = []
    total_nvidia_time = 0.0
    for i, chunk in enumerate(chunks):
        chunk_num = i + 1
        logger.info("nvidia_request: chunk=%d, page_range=%d-%d, start",
                    chunk_num, chunk.start_page, chunk.end_page)
        nvidia_start = time.perf_counter()
        try:
            all_cards.extend(_generate_cards_for_chunk(chunk))
        except Exception:
            logger.exception(
                "Card generation failed for chunk pages %s-%s",
                chunk.start_page,
                chunk.end_page,
            )
        nvidia_elapsed = time.perf_counter() - nvidia_start
        total_nvidia_time += nvidia_elapsed
        logger.info("nvidia_request: chunk=%d, page_range=%d-%d, elapsed=%.3fs",
                    chunk_num, chunk.start_page, chunk.end_page, nvidia_elapsed)
        if i < len(chunks) - 1:
            time.sleep(SECONDS_BETWEEN_CALLS)

    logger.info("nvidia_total: elapsed=%.3fs, num_chunks=%d, total_cards=%d",
                total_nvidia_time, len(chunks), len(all_cards))

    dedup_start = time.perf_counter()
    deduplicated = deduplicate_cards(all_cards)
    dedup_elapsed = time.perf_counter() - dedup_start
    logger.info("deduplicate_cards: elapsed=%.3fs, input_cards=%d, output_cards=%d",
                dedup_elapsed, len(all_cards), len(deduplicated))

    quality_start = time.perf_counter()
    final_cards = quality_check(deduplicated)
    quality_elapsed = time.perf_counter() - quality_start
    logger.info("quality_check: elapsed=%.3fs, input_cards=%d, output_cards=%d",
                quality_elapsed, len(deduplicated), len(final_cards))

    if not final_cards:
        raise ValueError(
            "No usable cards were produced from this document after quality checks."
        )

    total_elapsed = time.perf_counter() - total_start
    logger.info("generate_deck_cards: total_elapsed=%.3fs, input_pages=%d, num_chunks=%d, final_cards=%d",
                total_elapsed, input_page_count, len(chunks), len(final_cards))

    return final_cards
