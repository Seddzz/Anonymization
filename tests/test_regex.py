"""Tests for regex detectors - 5 positive + 5 negative per pattern."""

from anonymizer.detect import validate_entity_offsets
from anonymizer.detectors.regex_detector import (
    date_detector,
    detect_all_regex,
    email_detector,
    phone_detector,
    zip_detector,
)

# ============================================================
# EMAIL
# ============================================================
EMAIL_POSITIVE = [
    "user@example.com",
    "john.doe@company.org",
    "test+tag@domain.co.uk",
    "user_name@sub.domain.com",
    "a@b.io",
]

EMAIL_NEGATIVE = [
    "notanemail",
    "@no-local-part.com",
    "no-at-sign.com",
    "missing@tld",
    "myemail@domain.comextra",  # embedded in word without separator
]


# ============================================================
# PHONE (US)
# ============================================================
PHONE_POSITIVE = [
    "(555) 123-4567",
    "555-123-4567",
    "555.123.4567",
    "+1 555 123 4567",
    "5551234567",
]

PHONE_NEGATIVE = [
    "123-4567",           # missing area code
    "555-123-456",        # too short
    "555-123-45678",      # too long
    "abc-def-ghij",       # letters
    "555) 123-4567",      # unmatched paren
]


# ============================================================
# US ZIP
# ============================================================
ZIP_POSITIVE = [
    "12345",
    "12345-6789",
    "90210",
    "00000",
    "12345-0000",
]

ZIP_NEGATIVE = [
    "1234",          # too short
    "123456",        # too long
    "12345-678",     # short extension
    "12345-67890",   # long extension
    "abcde",         # letters
]


# ============================================================
# DATES
# ============================================================
DATE_POSITIVE = [
    "03/15/2024",
    "12/31/1999",
    "March 15, 2024",
    "15 March 2024",
    "Jan 1, 2000",
]

DATE_NEGATIVE = [
    "15/03/2024",      # DD/MM/YYYY (not US format)
    "2024/03/15",      # YYYY/MM/DD
    "March 2024",      # missing day
    "03/15/24",        # 2-digit year
    "not a date",
]


# ============================================================
# TEST HELPERS
# ============================================================
def run_detector_tests(detector, positive_cases, negative_cases, label):
    """Test detector against positive and negative cases."""
    # Positive cases - should detect
    for text in positive_cases:
        entities = detector.detect(text)
        assert len(entities) >= 1, f"{label}: should detect in '{text}'"
        for e in entities:
            assert e.label == label
            assert e.source == "regex"
            assert e.score == 1.0
        validate_entity_offsets(text, entities)
    
    # Negative cases - should NOT detect
    for text in negative_cases:
        entities = detector.detect(text)
        assert len(entities) == 0, f"{label}: should not detect in '{text}'"


# ============================================================
# TESTS
# ============================================================
class TestEmailDetector:
    def test_positive(self):
        run_detector_tests(email_detector, EMAIL_POSITIVE, [], "EMAIL")
    
    def test_negative(self):
        run_detector_tests(email_detector, [], EMAIL_NEGATIVE, "EMAIL")


class TestPhoneDetector:
    def test_positive(self):
        run_detector_tests(phone_detector, PHONE_POSITIVE, [], "PHONE")
    
    def test_negative(self):
        run_detector_tests(phone_detector, [], PHONE_NEGATIVE, "PHONE")


class TestZipDetector:
    def test_positive(self):
        run_detector_tests(zip_detector, ZIP_POSITIVE, [], "ZIP")
    
    def test_negative(self):
        run_detector_tests(zip_detector, [], ZIP_NEGATIVE, "ZIP")


class TestDateDetector:
    def test_positive(self):
        run_detector_tests(date_detector, DATE_POSITIVE, [], "DATE")
    
    def test_negative(self):
        run_detector_tests(date_detector, [], DATE_NEGATIVE, "DATE")


class TestCombined:
    def test_detect_all_regex(self):
        """Test combined detection on mixed text."""
        text = (
            "Contact John at john@example.com or (555) 123-4567. "
            "Lives in 90210. Date: 03/15/2024."
        )
        entities = detect_all_regex(text)
        
        labels = {e.label for e in entities}
        assert "EMAIL" in labels
        assert "PHONE" in labels
        assert "ZIP" in labels
        assert "DATE" in labels
        
        validate_entity_offsets(text, entities)
    
    def test_no_false_positives_on_clean_text(self):
        """Clean text should have no detections."""
        text = "This is a normal sentence without any PII."
        entities = detect_all_regex(text)
        assert len(entities) == 0