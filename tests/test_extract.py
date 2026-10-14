import base64

import fitz  # PyMuPDF
import pytest

from anonymizer.exceptions import ScannedDocumentError
from anonymizer.extract import extract_pdf


def create_pdf(texts: list[str]) -> bytes:
    """Create a PDF in memory with given page texts."""
    doc = fitz.open()
    for t in texts:
        page = doc.new_page()
        page.insert_text((72, 72), t)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_extract_pdf_normal(tmp_path):
    """Test extraction from a normal multi-page PDF."""
    pdf_bytes = create_pdf(["Page one content", "Page two content"])
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(pdf_bytes)
    
    pages = extract_pdf(pdf_path)
    
    assert len(pages) == 2
    assert pages[0].text.rstrip() == "Page one content"
    assert pages[0].start == 0
    assert pages[0].page_number == 1
    assert pages[1].text.rstrip() == "Page two content"
    assert pages[1].start == len(pages[0].text)
    assert pages[1].page_number == 2


def create_empty_pdf() -> bytes:
    """Create a valid empty PDF (0 pages) - minimal valid PDF structure."""
    # Minimal valid PDF with 0 pages (base64 encoded)
    # This is a valid PDF that opens but has no pages
    empty_pdf_b64 = (
        "JVBERi0xLjQKJcOkw7zDtsOQKjAgb2JqCjw8L1R5cGUvQ2F0YWxvZy9QYWdlcyAyIDAgUiA+PgplbmRvYmoKMiAwIG9iago8PC9UeXBlL1BhZ2VzL0NvdW50IDAvS2lkcyBbXSA+PgplbmRvYmoKeHJlZgowIDMKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwMDEwIDAwMDAwIG4gCjAwMDAwMDAwNzkgMDAwMDAgbiAKdHJhaWxlcgo8PC9TaXplIDMvUm9vdCAxIDAgUj4+CiUJRU9G"
    )
    return base64.b64decode(empty_pdf_b64)


def test_extract_pdf_empty(tmp_path):
    """Test extraction from empty PDF (0 pages)."""
    pdf_bytes = create_empty_pdf()
    pdf_path = tmp_path / "empty.pdf"
    pdf_path.write_bytes(pdf_bytes)
    
    pages = extract_pdf(pdf_path)
    assert pages == []


def test_extract_pdf_scanned_page(tmp_path):
    """Test that scanned page (no text) raises ScannedDocumentError."""
    doc = fitz.open()
    # Page 1: normal
    page1 = doc.new_page()
    page1.insert_text((72, 72), "Has text")
    # Page 2: blank (no text layer)
    doc.new_page()
    pdf_bytes = doc.tobytes()
    doc.close()
    
    pdf_path = tmp_path / "scanned.pdf"
    pdf_path.write_bytes(pdf_bytes)
    
    with pytest.raises(ScannedDocumentError) as exc_info:
        extract_pdf(pdf_path)
    assert exc_info.value.page_number == 2


def test_extract_pdf_offsets_are_correct(tmp_path):
    """Test that start offsets accumulate correctly."""
    pdf_bytes = create_pdf(["A", "BB", "CCC"])
    pdf_path = tmp_path / "offsets.pdf"
    pdf_path.write_bytes(pdf_bytes)
    
    pages = extract_pdf(pdf_path)
    
    assert pages[0].start == 0
    assert pages[1].start == len(pages[0].text)
    assert pages[2].start == len(pages[0].text) + len(pages[1].text)