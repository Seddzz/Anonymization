import pytest

from anonymizer.anonymize import anonymize_text
from anonymizer.detect import Entity


def test_single_entity():
    text = "Hello John Doe!"
    entities = [Entity("PERSON", 6, 14, "John Doe", 1.0, "ner")]
    redacted, mapping = anonymize_text(text, entities)
    assert redacted == "Hello [PERSON_1]!"
    assert mapping == {"[PERSON_1]": "John Doe"}


def test_multiple_labels():
    text = "Email a@b.com from John"
    entities = [
        Entity("EMAIL", 6, 13, "a@b.com", 1.0, "regex"),
        Entity("PERSON", 19, 23, "John", 1.0, "ner"),
    ]
    redacted, mapping = anonymize_text(text, entities)
    assert redacted == "Email [EMAIL_1] from [PERSON_1]"
    assert mapping == {"[EMAIL_1]": "a@b.com", "[PERSON_1]": "John"}


def test_repeated_value_reuses_placeholder():
    text = "John met John"
    entities = [
        Entity("PERSON", 0, 4, "John", 1.0, "ner"),
        Entity("PERSON", 9, 13, "John", 1.0, "ner"),
    ]
    redacted, mapping = anonymize_text(text, entities)
    assert redacted == "[PERSON_1] met [PERSON_1]"
    assert mapping == {"[PERSON_1]": "John"}


def test_numbering_is_per_label():
    text = "a b"
    entities = [
        Entity("X", 0, 1, "a", 1.0, "regex"),
        Entity("Y", 2, 3, "b", 1.0, "regex"),
    ]
    _, mapping = anonymize_text(text, entities)
    assert set(mapping) == {"[X_1]", "[Y_1]"}


def test_adjacent_spans():
    text = "ab"
    entities = [
        Entity("X", 0, 1, "a", 1.0, "regex"),
        Entity("X", 1, 2, "b", 1.0, "regex"),
    ]
    redacted, _ = anonymize_text(text, entities)
    assert redacted == "[X_1][X_2]"


def test_empty_input():
    assert anonymize_text("", []) == ("", {})


def test_text_without_entities_is_unchanged():
    text = "nothing to redact here"
    redacted, mapping = anonymize_text(text, [])
    assert redacted == text
    assert mapping == {}


def test_bad_offsets_raise():
    text = "John Doe"
    entities = [Entity("PERSON", 0, 8, "Jane Doe", 1.0, "ner")]
    with pytest.raises(AssertionError):
        anonymize_text(text, entities)
