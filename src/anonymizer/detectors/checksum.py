"""Checksum-validated entity detectors."""
import re

from anonymizer.detect import Entity


class ChecksumDetector:
    """Base class for checksum-validated detectors."""
    
    def __init__(self, label: str, pattern: re.Pattern, source: str = "checksum"):
        self.label = label
        self.pattern = pattern
        self.source = source
    
    def detect(self, text: str) -> list[Entity]:
        entities = []
        for match in self.pattern.finditer(text):
            candidate = match.group().replace(" ", "").replace("-", "")
            if self.validate(candidate):
                entities.append(Entity(
                    label=self.label,
                    start=match.start(),
                    end=match.end(),
                    text=match.group(),
                    score=1.0,  # checksum validation = deterministic
                    source=self.source
                ))
        return entities
    
    def validate(self, candidate: str) -> bool:
        """Override in subclass to implement checksum validation."""
        raise NotImplementedError


# ============================================================
# IBAN: International Bank Account Number
# Algorithm: Move first 4 chars to end, letters→numbers (A=10..Z=35), mod 97 == 1
# ============================================================
# Allow spaces between groups of 4, last group can be 1-4 chars
IBAN_PATTERN = re.compile(
    r"\b[A-Z]{2}\d{2}"                  # country + check digits
    r"(?:[ ]?[A-Z0-9]{4}){1,6}"         # groups of 4
    r"(?:[ ]?[A-Z0-9]{1,4})"            # final group (1-4 chars)
    r"\b"
)


def validate_iban(iban: str) -> bool:
    """Validate IBAN using mod 97 algorithm."""
    if len(iban) < 4:
        return False
    
    # Move first 4 characters to the end
    rearranged = iban[4:] + iban[:4]
    
    # Convert letters to numbers (A=10, B=11, ..., Z=35)
    numeric = ""
    for ch in rearranged:
        if ch.isalpha():
            numeric += str(ord(ch.upper()) - ord('A') + 10)
        else:
            numeric += ch
    
    # Compute mod 97
    try:
        return int(numeric) % 97 == 1
    except ValueError:
        return False


class IBANDetector(ChecksumDetector):
    def __init__(self):
        super().__init__("IBAN", IBAN_PATTERN)
    
    def validate(self, candidate: str) -> bool:
        return validate_iban(candidate)


# ============================================================
# Credit Card: Luhn algorithm (mod 10)
# ============================================================
CARD_PATTERN = re.compile(r"\b(?:\d[ -]*?){13,19}\b")


def validate_luhn(number: str) -> bool:
    """Validate using Luhn algorithm (mod 10)."""
    # Remove spaces and dashes
    digits = [int(d) for d in number if d.isdigit()]
    if len(digits) < 2:
        return False
    
    # Double every second digit from right (starting from second-to-last)
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:  # every second digit from right
            d = d * 2
            if d > 9:
                d -= 9
        total += d
    
    return total % 10 == 0


class CardDetector(ChecksumDetector):
    def __init__(self):
        super().__init__("CARD", CARD_PATTERN)
    
    def validate(self, candidate: str) -> bool:
        return validate_luhn(candidate)


# ============================================================
# SIREN (9 digits) / SIRET (14 digits): French company IDs, Luhn
# ============================================================
SIREN_PATTERN = re.compile(r"\b\d{3}[ .]?\d{3}[ .]?\d{3}\b")
# SIRET: 14 digits = SIREN(9) + NIC(5). Formats: 3 3 3 5 or 3 3 3 3 2
SIRET_PATTERN = re.compile(
    r"\b\d{3}[ .]?\d{3}[ .]?\d{3}[ .]?\d{5}\b"      # 3 3 3 5
    r"|\b\d{3}[ .]?\d{3}[ .]?\d{3}[ .]?\d{3}[ .]?\d{2}\b"  # 3 3 3 3 2
)


class SIRENDetector(ChecksumDetector):
    def __init__(self):
        super().__init__("SIREN", SIREN_PATTERN)
    
    def validate(self, candidate: str) -> bool:
        return validate_luhn(candidate)


class SIRETDetector(ChecksumDetector):
    def __init__(self):
        super().__init__("SIRET", SIRET_PATTERN)
    
    def validate(self, candidate: str) -> bool:
        return validate_luhn(candidate)


# ============================================================
# NIR: French social security number (15 digits)
# Last 2 digits = 97 - (first 13 digits mod 97)
# Corsica: 2A→19, 2B→18 before calculation
# Overseas: 971-976 (treated as 97 in validation)
# ============================================================
# Pattern: S(1) YY(2) MM(2) DD(2/3) CCC(3) OOO(3) KK(2)
# DD: 01-95, 2A, 2B, 97(1-6 for overseas)
# Allow flexible spaces anywhere
NIR_PATTERN = re.compile(
    r"\b[12]"                               # sex
    r"(?:[ ]?\d){2}"                        # year (2 digits)
    r"(?:[ ]?\d){2}"                        # month (2 digits)
    r"(?:[ ]?(?:0[1-9]|[1-8]\d|9[0-5]|2[AB]|97[1-6]))"  # dept (2-3 chars)
    r"(?:[ ]?\d){3}"                        # commune (3 digits)
    r"(?:[ ]?\d){3}"                        # order (3 digits)
    r"(?:[ ]?\d){2}"                        # key (2 digits)
    r"\b"
)


def validate_nir(nir: str) -> bool:
    """Validate French NIR (social security number)."""
    # Remove spaces
    nir = nir.replace(" ", "")
    
    # Length: 15 for metropolitan, 16 for overseas (971-976)
    if len(nir) not in (15, 16):
        return False
    
    # First char must be 1 or 2 (sex)
    if nir[0] not in ('1', '2'):
        return False
    
    # Handle Corsica: replace 2A→19, 2B→18 in department positions
    # NIR: S(1) YY(2) MM(2) DD(2/3) ...
    # Department starts at index 5 (0-indexed)
    dept_start = 5
    dept = nir[dept_start:dept_start+2]
    if dept == '2A':
        nir = nir[:dept_start] + '19' + nir[dept_start+2:]
    elif dept == '2B':
        nir = nir[:dept_start] + '18' + nir[dept_start+2:]
    elif dept == '97' and len(nir) == 16:
        # Overseas: 971-976, use 97 for calculation
        nir = nir[:dept_start] + '97' + nir[dept_start+3:]
    
    # Take first 13 digits (after Corsica/overseas replacement)
    try:
        first_13 = int(nir[:13])
    except ValueError:
        return False
    
    # Compute key: 97 - (first_13 % 97)
    key = 97 - (first_13 % 97)
    
    # Compare with last 2 digits
    try:
        given_key = int(nir[13:15])
    except ValueError:
        return False
    
    return key == given_key


class NIRDetector(ChecksumDetector):
    def __init__(self):
        super().__init__("NIR", NIR_PATTERN)
    
    def validate(self, candidate: str) -> bool:
        return validate_nir(candidate)


# ============================================================
# Export all checksum detectors
# ============================================================
ALL_CHECKSUM_DETECTORS = [
    IBANDetector(),
    CardDetector(),
    SIRENDetector(),
    SIRETDetector(),
    NIRDetector(),
]


def detect_all_checksum(text: str) -> list[Entity]:
    """Run all checksum detectors on text and return combined entities."""
    entities = []
    for detector in ALL_CHECKSUM_DETECTORS:
        entities.extend(detector.detect(text))
    return entities