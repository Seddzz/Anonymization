from anonymizer.anonymize import anonymize_text
from anonymizer.detect import Entity
from anonymizer.restore import restore_text


def test_restore_single():
    assert restore_text("Hi [PERSON_1]", {"[PERSON_1]": "John"}) == "Hi John"


def test_restore_multiple():
    text = "[EMAIL_1] and [PERSON_1]"
    mapping = {"[EMAIL_1]": "a@b.com", "[PERSON_1]": "John"}
    assert restore_text(text, mapping) == "a@b.com and John"


def test_restore_empty_mapping():
    assert restore_text("unchanged", {}) == "unchanged"


def test_restore_prefers_longer_placeholder():
    mapping = {"[PERSON_1]": "A", "[PERSON_10]": "B"}
    assert restore_text("x [PERSON_10] y [PERSON_1]", mapping) == "x B y A"


def test_round_trip_anonymize_then_restore():
    text = "Email a@b.com from John Doe"
    entities = [
        Entity("EMAIL", 6, 13, "a@b.com", 1.0, "regex"),
        Entity("PERSON", 19, 27, "John Doe", 1.0, "ner"),
    ]
    redacted, mapping = anonymize_text(text, entities)
    assert restore_text(redacted, mapping) == text
