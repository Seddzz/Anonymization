"""Render redacted PDFs: remove PII in place and stamp replacement tokens."""
from dataclasses import dataclass
from pathlib import Path

import pymupdf as fitz

from anonymizer.anonymize import anonymize_text, replacement_table
from anonymizer.detect import Entity
from anonymizer.extract import extract_pdf

_FILL = (1.0, 1.0, 1.0)
_TEXT_COLOR = (0.055, 0.086, 0.106)


@dataclass(frozen=True, slots=True)
class PdfRedaction:
    """A redacted PDF plus the redacted text of the same run."""

    pdf_bytes: bytes
    redacted_text: str
    applied: int
    missed: int


def _entity_rects(page: "fitz.Page", entity: Entity, occurrence: int) -> list["fitz.Rect"]:
    """Find the drawing rects for an entity on a page.

    First tries an exact search; falls back to per-token searches so entities
    broken across line breaks still get covered (union of their word boxes).
    """
    rects = page.search_for(entity.text)
    if not rects:
        tokens = [token for token in entity.text.split() if len(token) >= 2]
        token_rects: list[fitz.Rect] = []
        for token in tokens:
            found = page.search_for(token)
            if found:
                token_rects.append(found[0])
        if not token_rects:
            return []
        union = fitz.Rect(token_rects[0])
        for rect in token_rects[1:]:
            union |= rect
        return [union]
    if len(rects) == 1:
        return list(rects)
    index = min(occurrence, len(rects) - 1)
    return [rects[index]]


def _fit_fontsize(rect: "fitz.Rect", label: str) -> float:
    height_limit = max(rect.height * 0.62, 3.0)
    width_limit = rect.width / max(len(label) * 0.58, 1.0)
    return max(3.0, min(11.0, height_limit, width_limit))


def redact_pdf(
    path: Path,
    entities: list[Entity],
    strategy: str = "placeholder",
) -> PdfRedaction:
    """Box out every entity in the PDF and stamp its replacement token.

    Reuses the same replacement table for the stamps and the redacted text, so
    both stay identical to the normal text pipeline.
    """
    pages = extract_pdf(path)
    full_text = "".join(page.text for page in pages)
    replacements = replacement_table(entities, strategy=strategy)
    redacted = anonymize_text(full_text, entities, strategy=strategy, replacements=replacements)

    document = fitz.open(path)
    applied = 0
    missed = 0
    occurrences: dict[tuple[int, str], int] = {}

    for page_index, page_info in enumerate(pages):
        page = document[page_index]
        page_end = page_info.start + len(page_info.text)
        page_entities = [
            entity
            for entity in entities
            if entity.start < page_end and entity.end > page_info.start
        ]
        if not page_entities:
            continue

        for entity in sorted(page_entities, key=lambda e: e.start):
            occurrence = occurrences.get((page_index, entity.text), 0)
            occurrences[(page_index, entity.text)] = occurrence + 1
            rects = _entity_rects(page, entity, occurrence)
            if not rects:
                missed += 1
                continue

            label = replacements[(entity.label, entity.text)]
            for rect in rects:
                if rect.is_empty or rect.is_infinite:
                    missed += 1
                    continue
                page.add_redact_annot(
                    rect,
                    text=label,
                    fontname="helv",
                    fontsize=_fit_fontsize(rect, label),
                    text_color=_TEXT_COLOR,
                    fill=_FILL,
                    align=fitz.TEXT_ALIGN_CENTER,
                )
                applied += 1

        try:
            page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
        except TypeError:
            page.apply_redactions()

    pdf_bytes = document.tobytes(deflate=True)
    document.close()
    return PdfRedaction(
        pdf_bytes=pdf_bytes,
        redacted_text=redacted,
        applied=applied,
        missed=missed,
    )
