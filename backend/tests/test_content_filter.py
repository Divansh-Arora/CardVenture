"""Content filter: drop answer-key / index / TOC pages before chunking."""
from app.services.content_filter import filter_pages
from app.services.pdf_service import PageText


def _page(n, text):
    return PageText(page_number=n, text=text)


def test_keeps_ordinary_instructional_page():
    pages = [_page(1, "Photosynthesis converts light energy into chemical energy stored in glucose.")]
    result = filter_pages(pages)
    assert result.kept == pages
    assert result.dropped_pages == []


def test_drops_page_headed_answer_key():
    text = "Answer Key\n1. b\n2. a\n3. d\n4. c\n5. a\n6. b\n7. d"
    pages = [_page(1, "Real content about cells."), _page(2, text)]
    result = filter_pages(pages)
    assert [p.page_number for p in result.kept] == [1]
    assert result.dropped_pages == [2]
    assert "answer" in result.dropped_reasons[2].lower()


def test_drops_page_headed_table_of_contents():
    text = "Table of Contents\nChapter 1 .......... 1\nChapter 2 .......... 15\nChapter 3 .......... 42"
    pages = [_page(1, text)]
    result = filter_pages(pages)
    assert result.kept == []
    assert result.dropped_pages == [1]


def test_drops_index_style_page_by_line_density_without_heading():
    lines = [f"Term{i}, {10 + i}" for i in range(20)]
    text = "\n".join(lines)
    pages = [_page(1, text)]
    result = filter_pages(pages)
    assert result.dropped_pages == [1]
    assert "index" in result.dropped_reasons[1].lower()


def test_drops_answer_key_style_page_by_line_density_without_heading():
    lines = [f"{i}. {'abcd'[i % 4]}" for i in range(1, 25)]
    text = "\n".join(lines)
    pages = [_page(1, text)]
    result = filter_pages(pages)
    assert result.dropped_pages == [1]


def test_does_not_drop_short_pages_below_density_threshold_minimum():
    # Fewer than MIN_LINES_FOR_DENSITY_CHECK lines -- too little evidence
    # to classify as an answer key even though every line matches.
    text = "1. b\n2. a"
    pages = [_page(1, text)]
    result = filter_pages(pages)
    assert result.kept == pages


def test_does_not_drop_page_merely_mentioning_the_word_answer_in_body_text():
    text = (
        "The answer to this question depends on several factors including "
        "temperature, pressure, and the presence of a catalyst in the reaction."
    )
    pages = [_page(1, text)]
    result = filter_pages(pages)
    assert result.kept == pages


def test_preserves_relative_order_of_kept_pages():
    pages = [
        _page(1, "Intro content about biology and cells and organisms."),
        _page(2, "Answer Key\n1. a\n2. b\n3. c\n4. d\n5. a\n6. b\n7. c"),
        _page(3, "More content about mitochondria and energy production."),
    ]
    result = filter_pages(pages)
    assert [p.page_number for p in result.kept] == [1, 3]
