"""
Drop non-instructional pages before they ever reach chunking/generation.

Textbook and lecture-note PDFs routinely include pages that are not
teachable material: tables of contents, back-of-book answer keys /
solution keys, and alphabetical indexes. Left in, these produced junk
cards -- e.g. a page that's just "12. b   13. a   14. d" turned into a
flashcard whose question was effectively "What is 12?" with no context,
and an index page turned into cards like "What page is entropy on?".

This is a pre-chunking filter (not part of quality_check) because it acts
on whole pages before their text is ever merged into a chunk -- by the
time content reaches quality_check, it's already been generated into
question/answer pairs and there's no page-level context left to filter on.
"""
import re
from dataclasses import dataclass

from app.services.pdf_service import PageText

_ANSWER_KEY_HEADING_RE = re.compile(
    r"^(answer key|answers?|solutions?|solution key|selected answers)s?\s*[:\-]?\s*"
    r"(to (the )?(exercises|problems|questions))?$",
    re.IGNORECASE,
)
_TOC_HEADING_RE = re.compile(r"^(table of contents|contents)$", re.IGNORECASE)
_INDEX_HEADING_RE = re.compile(r"^index$", re.IGNORECASE)

# "12. b", "3) True", "14.  C.", "7 - False" -- a short numbered token
# with little else on the line, typical of an answer key entry.
_ANSWER_LINE_RE = re.compile(
    r"^\(?\d{1,3}\)?[\.\)\-]\s*[A-Za-z0-9](\.|\))?\s*$"
)

# "Photosynthesis, 45, 102" / "Newton's laws ... 12-14" -- term followed by
# one or more page-number references, typical of an index entry.
_INDEX_LINE_RE = re.compile(
    r"^[A-Za-z][A-Za-z0-9\s\-'&]{1,60},?\s*\d{1,4}(\s*[-–,]\s*\d{1,4})*$"
)

# "..........42" / dot-leader lines typical of a table of contents.
_TOC_LINE_RE = re.compile(r"^.{2,80}\.{4,}\s*\d{1,4}$")

MIN_LINES_FOR_DENSITY_CHECK = 6
DENSITY_THRESHOLD = 0.55  # share of lines that must match the pattern


@dataclass
class FilterResult:
    kept: list[PageText]
    dropped_pages: list[int]
    dropped_reasons: dict[int, str]


def _heading_says_noninstructional(first_lines: list[str]) -> str | None:
    for raw in first_lines:
        line = raw.strip()
        if not line:
            continue
        if _ANSWER_KEY_HEADING_RE.match(line):
            return "answer key heading"
        if _TOC_HEADING_RE.match(line):
            return "table of contents heading"
        if _INDEX_HEADING_RE.match(line):
            return "index heading"
        # Only the first non-empty line counts as "the heading" -- stop
        # looking once we've checked it so body text further down the page
        # can't accidentally match one of these narrow phrases.
        break
    return None


def _line_density_reason(lines: list[str]) -> str | None:
    non_empty = [l.strip() for l in lines if l.strip()]
    if len(non_empty) < MIN_LINES_FOR_DENSITY_CHECK:
        return None

    answer_matches = sum(1 for l in non_empty if _ANSWER_LINE_RE.match(l))
    index_matches = sum(1 for l in non_empty if _INDEX_LINE_RE.match(l))
    toc_matches = sum(1 for l in non_empty if _TOC_LINE_RE.match(l))

    total = len(non_empty)
    if answer_matches / total >= DENSITY_THRESHOLD:
        return "answer-key-like line density"
    if index_matches / total >= DENSITY_THRESHOLD:
        return "index-like line density"
    if toc_matches / total >= DENSITY_THRESHOLD:
        return "table-of-contents-like line density"
    return None


def _classify(page: PageText) -> str | None:
    """Returns a drop reason string, or None if the page should be kept."""
    lines = page.text.splitlines()

    reason = _heading_says_noninstructional(lines[:3])
    if reason:
        return reason

    return _line_density_reason(lines)


def filter_pages(pages: list[PageText]) -> FilterResult:
    kept: list[PageText] = []
    dropped_pages: list[int] = []
    dropped_reasons: dict[int, str] = {}

    for page in pages:
        reason = _classify(page)
        if reason:
            dropped_pages.append(page.page_number)
            dropped_reasons[page.page_number] = reason
        else:
            kept.append(page)

    return FilterResult(kept=kept, dropped_pages=dropped_pages, dropped_reasons=dropped_reasons)
