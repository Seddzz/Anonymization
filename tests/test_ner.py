import pytest

from anonymizer.detect import validate_entity_offsets
from anonymizer.detectors.ner import NerDetector


@pytest.fixture(scope="module")
def ner_detector():
    return NerDetector()

def test_ner_detects_person_loc_org(ner_detector):
    text = "Marcus Aurelius visited New York City to meet with Acme Corp."
    entities = ner_detector.detect(text)

    # Check offsets match exact text slices
    validate_entity_offsets(text, entities)

    # Verify entity labels
    labels = {e.label for e in entities}
    assert "PERSON" in labels
    assert "LOCATION" in labels
    assert "ORGANIZATION" in labels


def test_ner_empty_text(ner_detector):
    assert ner_detector.detect("") == []
    assert ner_detector.detect("   ") == []


def test_ner_entity_attributes(ner_detector):
    text = "John Doe works at Google."
    entities = ner_detector.detect(text)

    validate_entity_offsets(text, entities)
    for e in entities:
        assert e.source == "ner"
        assert 0.0 <= e.score <= 1.0
        assert e.start < e.end