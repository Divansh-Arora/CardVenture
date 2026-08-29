"""
PDF -> per-page text extraction.

This is deliberately page-by-page (not one flattened blob) so downstream
chunking can (a) keep source_page attribution for each generated card, and
(b) group content into coherent chunks rather than an arbitrary character
cutoff.
"""
import io
from dataclasses import dataclass

from pypdf import PdfReader


@dataclass
class PageText:
    page_number: int  # 1-indexed, matches what a human would see in a PDF viewer
    text: str


def extract_pages(pdf_bytes: bytes) -> list[PageText]:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    pages: list[PageText] = []

    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append(PageText(page_number=i, text=text))

    if not pages:
        raise ValueError(
            "Could not extract any text from this PDF. It may be a scanned "
            "image without a text layer."
        )
    return pages
