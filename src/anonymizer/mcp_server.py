"""MCP server exposing the anonymizer's detection and redaction as tools."""
from typing import Literal

from mcp.server.mcpserver import MCPServer

from anonymizer import __version__
from anonymizer.anonymize import anonymize_text
from anonymizer.engine import DetectionEngine
from anonymizer.restore import restore_text
from anonymizer.store import MappingStore

server = MCPServer("anonymizer", version=__version__)

_engine = DetectionEngine()
_store = MappingStore()


@server.tool()
def detect(text: str) -> list[dict]:
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
        for entity in _engine.detect_all(text)
    ]


@server.tool()
def anonymize(text: str, strategy: Literal["placeholder", "fake"] = "placeholder") -> dict:
    """Redact PII and return the redacted text plus a mapping id for restoration."""
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


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()
