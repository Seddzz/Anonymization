"""Tests for checksum detectors."""

from anonymizer.detect import validate_entity_offsets
from anonymizer.detectors.checksum import (
    CardDetector,
    IBANDetector,
    NIRDetector,
    SIRENDetector,
    SIRETDetector,
    detect_all_checksum,
    validate_iban,
    validate_luhn,
    validate_nir,
)

# ============================================================
# IBAN TESTS
# ============================================================
# Valid IBANs (from official examples)
IBAN_VALID = [
    "GB29 NWBK 6016 1331 9268 19",   # UK
    "DE89 3704 0044 0532 0130 00",   # Germany
    "FR14 2004 1010 0505 0001 3M02 606",  # France
    "ES91 2100 0418 4502 0005 1332",  # Spain
    "IT60 X054 2811 1010 0000 0123 456",  # Italy
]

# Invalid IBANs (one char changed, wrong checksum, wrong format)
IBAN_INVALID = [
    "GB29 NWBK 6016 1331 9268 18",   # wrong checksum (last digit)
    "DE89 3704 0044 0532 0130 01",   # wrong checksum
    "XX29 NWBK 6016 1331 9268 19",   # invalid country code
    "GB29 NWBK 6016 1331 9268",      # too short
    "GB29 NWBK 6016 1331 9268 19X",  # extra char
]


# ============================================================
# LUHN TESTS (Credit Card, SIREN, SIRET)
# ============================================================
# Valid Luhn numbers (known test numbers)
LUHN_VALID = [
    "4111 1111 1111 1111",   # Visa test
    "5555 5555 5555 5557",   # Mastercard test (correct check digit)
    "3782 8224 6310 005",    # Amex test
    "6011 1111 1111 1117",   # Discover test
    "4242 4242 4242 4242",   # Visa test
]

# Invalid Luhn numbers (one digit changed)
LUHN_INVALID = [
    "4111 1111 1111 1112",   # wrong check digit
    "5555 5555 5555 5555",   # wrong check digit
    "3782 8224 6310 006",    # wrong check digit
    "6011 1111 1111 1118",   # wrong check digit
    "1234 5678 9012 345",    # too short (15 digits)
]


# SIREN valid (9 digits, Luhn valid)
SIREN_VALID = [
    "123 456 782",  # Luhn valid
    "732 829 320",  # Luhn valid
    "382 123 453",  # Luhn valid
    "999 999 998",  # Luhn valid
    "456 789 015",  # Luhn valid
]

SIREN_INVALID = [
    "123 456 783",  # wrong check digit
    "732 829 321",  # wrong check digit
    "382 123 454",  # wrong check digit
    "123 456 78",   # too short
    "abc def ghi",  # not digits
]


# SIRET valid (14 digits = SIREN 9 + NIC 5, Luhn valid on full 14)
SIRET_VALID = [
    "123 456 782 000 02",  # SIREN valid + NIC 5 digits + check (3 3 3 3 2)
    "732 829 320 000 09",
    "382 123 453 000 05",
    "999 999 998 000 01",
    "456 789 015 000 09",
]

SIRET_INVALID = [
    "123 456 783 000 02",  # SIREN part invalid
    "123 456 782 000 03",  # wrong check digit on full
    "123 456 78 000 02",   # SIREN too short
    "123 456 782 00 02",   # too short
    "abc def ghi jklmn",   # not digits
]


# ============================================================
# NIR TESTS (French SSN)
# ============================================================
# Valid NIRs (structure: sex(1) year(2) month(2) dept(2/3) commune(3) order(3) key(2))
# Dept: 01-95, 2A, 2B, 971-976 (overseas)
# Key = 97 - (first13 % 97)
NIR_VALID = [
    "1 84 03 75 056 123 08",  # Male, 1984, Mar, Paris, key=08
    "2 90 12 2A 001 456 18",  # Female, 1990, Dec, Corsica 2A, key=18
    "1 00 01 971 100 001 69", # Male, 2000, Jan, overseas 971, key=69
    "2 99 06 13 002 789 56",  # Female, 1999, Jun, Bouches-du-Rhone, key=56
    "1 75 09 59 003 321 41",  # Male, 1975, Sep, Nord, key=41
]

NIR_INVALID = [
    "1 84 03 75 056 123 09",  # wrong key
    "2 90 12 2A 001 456 19",  # wrong key
    "3 84 03 75 056 123 08",  # invalid sex (not 1 or 2)
    "1 84 13 75 056 123 08",  # invalid month
    "1 84 03 75 056 123",     # too short
]


# ============================================================
# TEST HELPERS
# ============================================================
def run_detector_tests(detector, positive_cases, negative_cases, label):
    """Test detector against positive and negative cases."""
    for text in positive_cases:
        entities = detector.detect(text)
        assert len(entities) >= 1, f"{label}: should detect in '{text}'"
        for e in entities:
            assert e.label == label
            assert e.source == "checksum"
            assert e.score == 1.0
        validate_entity_offsets(text, entities)
    
    for text in negative_cases:
        entities = detector.detect(text)
        assert len(entities) == 0, f"{label}: should not detect in '{text}'"


# ============================================================
# UNIT TESTS FOR VALIDATION FUNCTIONS
# ============================================================
class TestIBANValidation:
    def test_validate_iban_valid(self):
        for iban in IBAN_VALID:
            assert validate_iban(iban.replace(" ", "")), f"Should be valid: {iban}"
    
    def test_validate_iban_invalid(self):
        for iban in IBAN_INVALID:
            assert not validate_iban(iban.replace(" ", "")), f"Should be invalid: {iban}"


class TestLuhnValidation:
    def test_validate_luhn_valid(self):
        for num in LUHN_VALID:
            assert validate_luhn(num.replace(" ", "")), f"Should be valid: {num}"
    
    def test_validate_luhn_invalid(self):
        for num in LUHN_INVALID:
            assert not validate_luhn(num.replace(" ", "")), f"Should be invalid: {num}"


class TestNIRValidation:
    def test_validate_nir_valid(self):
        for nir in NIR_VALID:
            assert validate_nir(nir.replace(" ", "")), f"Should be valid: {nir}"
    
    def test_validate_nir_invalid(self):
        for nir in NIR_INVALID:
            assert not validate_nir(nir.replace(" ", "")), f"Should be invalid: {nir}"


# ============================================================
# DETECTOR TESTS
# ============================================================
class TestIBANDetector:
    def test_positive(self):
        run_detector_tests(IBANDetector(), IBAN_VALID, [], "IBAN")
    
    def test_negative(self):
        run_detector_tests(IBANDetector(), [], IBAN_INVALID, "IBAN")


class TestCardDetector:
    def test_positive(self):
        run_detector_tests(CardDetector(), LUHN_VALID, [], "CARD")
    
    def test_negative(self):
        run_detector_tests(CardDetector(), [], LUHN_INVALID, "CARD")


class TestSIRENDetector:
    def test_positive(self):
        run_detector_tests(SIRENDetector(), SIREN_VALID, [], "SIREN")
    
    def test_negative(self):
        run_detector_tests(SIRENDetector(), [], SIREN_INVALID, "SIREN")


class TestSIRETDetector:
    def test_positive(self):
        run_detector_tests(SIRETDetector(), SIRET_VALID, [], "SIRET")
    
    def test_negative(self):
        run_detector_tests(SIRETDetector(), [], SIRET_INVALID, "SIRET")


class TestNIRDetector:
    def test_positive(self):
        run_detector_tests(NIRDetector(), NIR_VALID, [], "NIR")
    
    def test_negative(self):
        run_detector_tests(NIRDetector(), [], NIR_INVALID, "NIR")


class TestCombined:
    def test_detect_all_checksum(self):
        """Test combined detection on mixed text."""
        text = (
            "IBAN: GB29 NWBK 6016 1331 9268 19. "
            "Card: 4111 1111 1111 1111. "
            "SIREN: 123 456 782. "
            "NIR: 1 84 03 75 056 123 08."
        )
        entities = detect_all_checksum(text)
        
        labels = {e.label for e in entities}
        assert "IBAN" in labels
        assert "CARD" in labels
        assert "SIREN" in labels
        assert "NIR" in labels
        
        validate_entity_offsets(text, entities)
    
    def test_no_false_positives_on_clean_text(self):
        text = "This is a normal sentence without any structured IDs."
        entities = detect_all_checksum(text)
        assert len(entities) == 0