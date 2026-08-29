"""
Page text -> coherent chunks for card generation.

Replaces the old "take the first 60,000 characters" approach. Instead:

  1. Pages are scanned for likely section headings (a lightweight heuristic
     -- short, title-cased/all-caps/numbered lines with no trailing
     punctuation -- since raw PDF text extraction doesn't preserve font
     size/weight, this is an approximation of real layout-aware section
     detection, not a replacement for it).
  2. Pages are grouped into chunks bounded by a target character budget,
     preferring to start a new chunk at a detected heading rather than
     mid-section when possible. A page whose own text already exceeds the
     hard ceiling (dense/scanned-text pages, or pages with unusually small
     margins) is itself split into paragraph-aware sub-chunks instead of
     being emitted as one oversized chunk.
  3. Each chunk embeds an inline `<<PAGE n>>` marker before every page's
     text it contains, and records exactly which page numbers it spans.
     This lets card generation (app/services/llm_service.py) ask the model
     to copy the nearest preceding marker for each card's source_page
     instead of guessing, and lets that value be validated against the
     chunk's real page range before it's trusted (see llm_service.py).

This means a 40-page PDF becomes several focused LLM calls instead of one
call silently truncated at an arbitrary character limit -- which is the
main reason cards previously stopped covering material comprehensively
once a document got long.
"""
import re
import time
import logging
from dataclasses import dataclass, field

from app.services.pdf_service import PageText

logger = logging.getLogger(__name__)

TARGET_CHUNK_CHARS = 7000
MAX_CHUNK_CHARS = 9000  # hard ceiling before we force a break mid-page

# Marker inserted before each page's text inside a chunk so per-card source
# pages can be recovered from the model's output deterministically instead
# of trusted blindly. Deliberately distinctive so it can't collide with
# real document text.
PAGE_MARKER_RE = re.compile(r"<<PAGE (\d+)>>")


def _page_marker(page_number: int) -> str:
    return f"<<PAGE {page_number}>>"


# Headings without layout info: short lines, no trailing sentence
# punctuation, and either Title Case / ALL CAPS, OR a numbered/markdown
# heading like "1. Introduction", "Chapter 2: Overview", "2.3 Overview",
# "# Overview" -- textbook and lecture-note PDFs lean heavily on numbered
# section headers that plain istitle()/isupper() checks used to miss
# entirely, which meant chunk breaks landed mid-section far more often
# than they needed to.
_TITLE_CASE_RE = re.compile(r"^[A-Z0-9][A-Za-z0-9 ,\-:]{2,60}$")
_NUMBERED_HEADING_RE = re.compile(
    r"^(chapter\s+\d+[:.\-]?\s*.*"
    r"|\d+(\.\d+)*[.\)]?\s+[A-Za-z].{0,60}"
    r"|#{1,3}\s+.{2,60})$",
    re.IGNORECASE,
)


@dataclass
class Chunk:
    text: str
    start_page: int
    end_page: int
    page_numbers: list[int] = field(default_factory=list)
    heading: str | None = None


def _looks_like_heading(line: str) -> bool:
    line = line.strip()
    if not (3 <= len(line) <= 70):
        return False
    if line.endswith((".", ",", ";")) and not _NUMBERED_HEADING_RE.match(line):
        return False

    if _NUMBERED_HEADING_RE.match(line):
        return True

    words = line.split()
    if len(words) > 8:
        return False
    return bool(_TITLE_CASE_RE.match(line)) and (line.isupper() or line.istitle())


def _first_heading(text: str) -> str | None:
    for line in text.splitlines()[:5]:
        line = PAGE_MARKER_RE.sub("", line).strip()
        if line and _looks_like_heading(line):
            return line
    return None


def _split_oversized_page(page: PageText) -> list[tuple[int, str]]:
    """Split a single page whose text alone exceeds MAX_CHUNK_CHARS into
    paragraph-aware pieces, each still tagged with that page's number.

    Without this, a single unusually dense page (e.g. a page of small-print
    reference tables, or an extraction artifact that merges pages) used to
    slip through the "would this addition overflow the current chunk?"
    check entirely, because that check only fires when there's already
    content buffered -- a lone oversized page became one giant chunk with
    no upper bound at all.
    """
    paragraphs = [p for p in re.split(r"\n\s*\n", page.text) if p.strip()]
    if not paragraphs:
        paragraphs = [page.text]

    pieces: list[str] = []
    current = ""
    for para in paragraphs:
        candidate = f"{current}\n\n{para}" if current else para
        if len(candidate) > MAX_CHUNK_CHARS and current:
            pieces.append(current)
            current = para
        else:
            current = candidate

        # A single paragraph longer than the ceiling (rare, but possible
        # with unbroken dense text) gets hard-wrapped rather than left
        # to blow past the limit on its own.
        while len(current) > MAX_CHUNK_CHARS:
            pieces.append(current[:MAX_CHUNK_CHARS])
            current = current[MAX_CHUNK_CHARS:]

    if current:
        pieces.append(current)

    return [(page.page_number, piece) for piece in pieces]


def chunk_pages(pages: list[PageText]) -> list[Chunk]:
    start = time.perf_counter()
    chunks: list[Chunk] = []

    current_parts: list[str] = []  # already includes page markers
    current_pages: list[int] = []
    current_chars = 0

    def flush():
        nonlocal current_parts, current_pages, current_chars
        if not current_parts:
            return
        joined = "\n\n".join(current_parts)
        chunks.append(
            Chunk(
                text=joined,
                start_page=current_pages[0],
                end_page=current_pages[-1],
                page_numbers=list(current_pages),
                heading=_first_heading(joined),
            )
        )
        current_parts = []
        current_pages = []
        current_chars = 0

    # Normalize input into (page_number, text) pieces up front, splitting
    # any single oversized page before the chunk-packing loop even sees it.
    units: list[tuple[int, str]] = []
    for page in pages:
        if len(page.text) > MAX_CHUNK_CHARS:
            units.extend(_split_oversized_page(page))
        else:
            units.append((page.page_number, page.text))

    for page_number, text in units:
        marked = f"{_page_marker(page_number)}\n{text}"
        piece_heading = _first_heading(text)
        addition_len = len(marked) + (2 if current_parts else 0)  # "\n\n" join

        would_exceed = current_chars + addition_len > MAX_CHUNK_CHARS
        at_natural_break = current_chars >= TARGET_CHUNK_CHARS and piece_heading is not None

        if current_parts and (would_exceed or at_natural_break):
            flush()
            addition_len = len(marked)

        current_pages.append(page_number)
        current_parts.append(marked)
        current_chars += addition_len

    flush()
    elapsed = time.perf_counter() - start
    logger.info("chunk_pages: elapsed=%.3fs, input_pages=%d, num_chunks=%d",
                elapsed, len(pages), len(chunks))
    return chunks
