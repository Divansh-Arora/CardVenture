"""PDF -> per-page text extraction."""
import pytest

from app.services.pdf_service import extract_pages


def test_extracts_text_per_page(make_pdf):
    pdf_bytes = make_pdf(["Page one content here.", "Page two content here."])
    pages = extract_pages(pdf_bytes)
    assert len(pages) == 2
    assert pages[0].page_number == 1
    assert "Page one" in pages[0].text
    assert pages[1].page_number == 2
    assert "Page two" in pages[1].text


def test_raises_value_error_for_pdf_with_no_extractable_text():
    # A structurally valid but blank/imageless PDF -- pypdf will return no
    # text at all, which should surface as a clear, catchable error rather
    # than an empty deck silently proceeding.
    import io
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    c.showPage()
    c.save()

    with pytest.raises(ValueError):
        extract_pages(buffer.getvalue())
