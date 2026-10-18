"""Anonymizer: replace detected entities with stable placeholders."""
from anonymizer.detect import Entity, validate_entity_offsets


def anonymize_text(text: str, entities: list[Entity]) -> tuple[str, dict[str, str]]:
    """Replace each entity span with a stable placeholder.

    Returns ``(redacted_text, mapping)`` where ``mapping`` maps each placeholder
    to its original value. Placeholders are numbered per label, and the same
    ``(label, value)`` pair always receives the same placeholder, so repeated
    values stay consistent and the mapping stays small.

    ``entities`` must be non-overlapping (the DetectionEngine guarantees this).
    """
    validate_entity_offsets(text, entities)

    counters: dict[str, int] = {}
    placeholder_by_value: dict[tuple[str, str], str] = {}
    mapping: dict[str, str] = {}

    # Assign placeholders in document order for deterministic numbering.
    for entity in sorted(entities, key=lambda e: e.start):
        key = (entity.label, entity.text)
        if key not in placeholder_by_value:
            counters[entity.label] = counters.get(entity.label, 0) + 1
            placeholder = f"[{entity.label}_{counters[entity.label]}]"
            placeholder_by_value[key] = placeholder
            mapping[placeholder] = entity.text

    # Splice right-to-left so earlier offsets stay valid while editing.
    redacted = text
    for entity in sorted(entities, key=lambda e: e.start, reverse=True):
        placeholder = placeholder_by_value[(entity.label, entity.text)]
        redacted = redacted[: entity.start] + placeholder + redacted[entity.end :]

    return redacted, mapping
