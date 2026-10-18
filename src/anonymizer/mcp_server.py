"""MCP server exposing the anonymizer's detection and redaction as tools."""
from pathlib import Path
from typing import Literal

from mcp.server.mcpserver import MCPServer

from anonymizer import __version__
from anonymizer.anonymize import anonymize_text
from anonymizer.detectors import ALL_CHECKSUM_DETECTORS, ALL_REGEX_DETECTORS, NerDetector
from anonymizer.engine import DetectionEngine
from anonymizer.extract import extract_pdf
from anonymizer.pdf_output import redact_pdf
from anonymizer.restore import restore_text
from anonymizer.store import MappingStore

server = MCPServer("anonymizer", version=__version__)

_engine = DetectionEngine()
_store = MappingStore()

_ner_detector: NerDetector | None = None
_ner_engine: DetectionEngine | None = None


def _engine_for(ner: bool) -> DetectionEngine:
    """Return a cached engine, lazily building the NER one on first use."""
    global _ner_detector, _ner_engine
    if not ner:
        return _engine
    if _ner_engine is None:
        _ner_detector = NerDetector()
        _ner_engine = DetectionEngine(
            [*ALL_REGEX_DETECTORS, *ALL_CHECKSUM_DETECTORS, _ner_detector]
        )
    return _ner_engine


@server.tool()
def detect(text: str, ner: bool = False) -> list[dict]:
    """Detect personally identifiable information in English text."""
    return [
        {
            "label": entity.label,
            "start": entity.start,
            "end": entity.end,
            "text": entity.text,
            "score": entity.score,
            "source": entity.source,
        }
        for entity in _engine_for(ner).detect_all(text)
    ]


@server.tool()
def anonymize(text: str, strategy: Literal["placeholder", "fake"] = "placeholder") -> dict:
    """Redact PII in text and return the redacted text plus a mapping id for restoration."""
    entities = _engine.detect_all(text)
    redacted, mapping = anonymize_text(text, entities, strategy=strategy)
    return {"redacted": redacted, "mapping_id": _store.save(mapping)}


@server.tool()
def restore(mapping_id: str, redacted: str) -> dict:
    """Restore original text from redacted text and its mapping id."""
    mapping = _store.get(mapping_id)
    if mapping is None:
        raise ValueError("mapping not found or expired")
    return {"text": restore_text(redacted, mapping)}


@server.tool()
def anonymize_pdf(
    input_path: str,
    strategy: Literal["placeholder", "fake"] = "placeholder",
    ner: bool = False,
    output_path: str | None = None,
    include_mapping: bool = False,
) -> dict:
    """Redact PII in a local PDF: writes a redacted PDF next to the original
    and returns the redacted text, ready to paste into any LLM or agent turn.

    The original document stays untouched on disk, so no mapping is needed;
    pass ``include_mapping=True`` only if you want the value table returned.
    """
    path = Path(input_path).expanduser().resolve()
    if path.suffix.lower() != ".pdf":
        raise ValueError("anonymize_pdf expects a .pdf file")
    if not path.exists():
        raise FileNotFoundError(f"no such file: {path}")

    text = "".join(page.text for page in extract_pdf(path))
    entities = _engine_for(ner).detect_all(text)
    result = redact_pdf(path, entities, strategy=strategy)

    destination = (
        Path(output_path).expanduser()
        if output_path
        else path.with_name(f"{path.stem}_redacted.pdf")
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(result.pdf_bytes)

    payload = {
        "redacted_pdf": str(destination),
        "redacted_text": result.redacted_text,
        "found_entities": [{"label": entity.label, "text": entity.text} for entity in entities],
        "stamped": result.applied,
        "missed": result.missed,
    }
    if include_mapping:
        payload["mapping"] = result.mapping
    return payload


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()
