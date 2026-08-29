"""Chunking: pages -> section-aware chunks, with page-marker attribution."""
from app.services.chunking import chunk_pages, _looks_like_heading, MAX_CHUNK_CHARS
from app.services.pdf_service import PageText


def test_single_short_page_becomes_one_chunk():
    pages = [PageText(page_number=1, text="Short intro paragraph about topic A.")]
    chunks = chunk_pages(pages)
    assert len(chunks) == 1
    assert chunks[0].start_page == 1
    assert chunks[0].end_page == 1
    assert chunks[0].page_numbers == [1]


def test_every_page_gets_a_marker_embedded_in_chunk_text():
    pages = [
        PageText(page_number=1, text="Content about A."),
        PageText(page_number=2, text="Content about B."),
    ]
    chunks = chunk_pages(pages)
    joined = "".join(c.text for c in chunks)
    assert "<<PAGE 1>>" in joined
    assert "<<PAGE 2>>" in joined


def test_small_pages_are_packed_into_the_same_chunk():
    pages = [PageText(page_number=i, text=f"Page {i} short content.") for i in range(1, 4)]
    chunks = chunk_pages(pages)
    assert len(chunks) == 1
    assert chunks[0].page_numbers == [1, 2, 3]


def test_chunk_never_exceeds_hard_ceiling_for_normal_pages():
    # Many medium pages that individually stay under the ceiling but
    # collectively would blow past it if not split.
    pages = [PageText(page_number=i, text="X" * 1200) for i in range(1, 10)]
    chunks = chunk_pages(pages)
    for c in chunks:
        assert len(c.text) <= MAX_CHUNK_CHARS + 200  # small slack for markers/joins


def test_oversized_single_page_is_split_rather_than_emitted_whole():
    """Regression test: a lone page whose own text exceeds MAX_CHUNK_CHARS
    used to produce one unbounded chunk, because the overflow check only
    ever fired when there was already buffered content to compare against."""
    huge_text = "\n\n".join(f"Paragraph {i} with some explanatory sentence." * 5 for i in range(60))
    assert len(huge_text) > MAX_CHUNK_CHARS
    pages = [PageText(page_number=1, text=huge_text)]

    chunks = chunk_pages(pages)

    assert len(chunks) > 1
    for c in chunks:
        assert len(c.text) <= MAX_CHUNK_CHARS + 50
        assert c.start_page == 1
        assert c.end_page == 1


def test_all_source_text_is_preserved_across_split_chunks():
    huge_text = "\n\n".join(f"Fact number {i} about the subject matter here." for i in range(400))
    pages = [PageText(page_number=1, text=huge_text)]
    chunks = chunk_pages(pages)

    # Every distinct fact should show up somewhere across the chunks --
    # splitting must not silently drop content.
    combined = "\n".join(c.text for c in chunks)
    for i in [0, 100, 200, 399]:
        assert f"Fact number {i} " in combined


def test_natural_break_prefers_heading_boundary():
    page1 = PageText(page_number=1, text="A" * 3600 + "\nMore filler text here.")
    page2 = PageText(page_number=2, text="Section Two\nContent under section two.")
    chunks = chunk_pages([page1, page2])
    # Should break before page 2 since it starts with a heading and we're
    # already past the target budget.
    assert chunks[0].end_page == 1
    assert chunks[-1].start_page == 2


def test_heading_detection_handles_numbered_and_markdown_headings():
    assert _looks_like_heading("1. Introduction")
    assert _looks_like_heading("Chapter 2: Thermodynamics")
    assert _looks_like_heading("2.3 Overview")
    assert _looks_like_heading("# Overview")
    assert _looks_like_heading("INTRODUCTION")
    assert _looks_like_heading("Quadratic Equations")


def test_heading_detection_rejects_ordinary_sentences():
    assert not _looks_like_heading("This is a normal sentence that ends with a period.")
    assert not _looks_like_heading("the cat sat on the mat")


def test_empty_page_list_returns_no_chunks():
    assert chunk_pages([]) == []
