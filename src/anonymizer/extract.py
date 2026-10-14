from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF

from .exceptions import ScannedDocumentError


@dataclass(frozen=True, slots=True)
class Page:
    """A page of extracted text with its document-level offset."""
    text: str
    start: int
    page_number: int


def extract_pdf(path: Path) -> list[Page]:
    """
    Extract text from each page of a PDF with character offsets.
    
    Args:
        path: Path to PDF file
        
    Returns:
        List of Page objects, one per page, with text and start offset
        
    Raises:
        ScannedDocumentError: If any page has no text layer
        FileNotFoundError: If path doesn't exist
    """
    doc = fitz.open(path)
    pages: list[Page] = []
    offset = 0
    
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text")
        if not text.strip():
            doc.close()
            raise ScannedDocumentError(page_num)
        pages.append(Page(text=text, start=offset, page_number=page_num))
        offset += len(text)
    
    doc.close()
    return pages