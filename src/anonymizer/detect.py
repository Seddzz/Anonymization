from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class Entity:
    """A detected entity span in text.
    
    Attributes:
        label: Entity type (e.g., "PERSON", "EMAIL", "IBAN")
        start: Inclusive character offset in the full document text
        end: Exclusive character offset in the full document text
        text: The actual matched text slice (text[start:end])
        score: Confidence 0.0-1.0 (1.0 for deterministic rule-based detectors)
        source: Which detector found it ("regex", "checksum", "ner")
    """
    label: str
    start: int
    end: int
    text: str
    score: float
    source: str


class Detector(Protocol):
    """Protocol for entity detectors.
    
    Any class implementing detect(text) -> list[Entity] can be used
    in the detection pipeline. This allows swapping detectors without
    changing the rest of the code.
    """
    def detect(self, text: str) -> list[Entity]:
        """Return entities found in the given text."""
        ...


def validate_entity_offsets(text: str, entities: list[Entity]) -> None:
    """Verify that each entity's text matches the source text at its offsets.
    
    This catches bugs where offsets drift during merging/replacement.
    Raises AssertionError if any entity doesn't match.
    """
    for e in entities:
        actual = text[e.start:e.end]
        if actual != e.text:
            raise AssertionError(
                f"Offset mismatch for {e.label}: "
                f"expected {e.text!r}, got {actual!r} at [{e.start}:{e.end}]"
            )