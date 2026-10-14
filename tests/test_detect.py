from dataclasses import FrozenInstanceError

import pytest

from anonymizer.detect import Entity, validate_entity_offsets


def test_entity_offsets_match():
    """Test that validate_entity_offsets passes for correct entities."""
    text = "John Doe lives in Paris"
    entities = [
        Entity("PERSON", 0, 8, "John Doe", 1.0, "regex"),
        Entity("LOC", 18, 23, "Paris", 1.0, "regex"),
    ]
    validate_entity_offsets(text, entities)  # should not raise


def test_entity_offsets_mismatch_raises():
    """Test that validate_entity_offsets catches mismatches."""
    text = "John Doe"
    entities = [Entity("PERSON", 0, 8, "Jane Doe", 1.0, "regex")]
    with pytest.raises(AssertionError) as exc_info:
        validate_entity_offsets(text, entities)
    assert "Offset mismatch" in str(exc_info.value)


def test_entity_immutable():
    """Test that Entity is frozen (immutable)."""
    e = Entity("PERSON", 0, 4, "John", 1.0, "regex")
    with pytest.raises(FrozenInstanceError):
        e.label = "ORG"


def test_entity_fields():
    """Test Entity has all required fields with correct types."""
    e = Entity("EMAIL", 10, 25, "test@example.com", 0.95, "regex")
    assert e.label == "EMAIL"
    assert e.start == 10
    assert e.end == 25
    assert e.text == "test@example.com"
    assert e.score == 0.95
    assert e.source == "regex"