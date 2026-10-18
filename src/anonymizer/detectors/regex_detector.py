"""Regex-based entity detectors."""
import re

from anonymizer.detect import Entity


class RegexDetector:
    """Base class for regex-based detectors."""
    
    def __init__(
        self,
        label: str,
        pattern: re.Pattern,
        source: str = "regex",
        group: int = 0,
    ):
        self.label = label
        self.pattern = pattern
        self.source = source
        self.group = group  # which capture group to use (0 = full match)
    
    def detect(self, text: str) -> list[Entity]:
        entities = []
        for match in self.pattern.finditer(text):
            matched_text = match.group(self.group)
            start = match.start(self.group)
            end = match.end(self.group)
            entities.append(Entity(
                label=self.label,
                start=start,
                end=end,
                text=matched_text,
                score=1.0,
                source=self.source
            ))
        return entities


# ============================================================
# Regex patterns for English PII
# ============================================================

# Email: user@domain.com, first.last@company.org, test+tag@domain.co.uk, etc.
# Use capturing group: (?:^|\s) matches leading whitespace/start, group 1 is the email
# Domain: subdomains separated by dots, TLD 2-6 chars (prevents "comextra" matching)
EMAIL_PATTERN = re.compile(
    r"(?:^|\s)"                    # start of string or whitespace
    r"([a-zA-Z0-9._%+-]+@"         # local part + @
    r"[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*"  # domain: subdomains (no leading dot)
    r"\.[a-zA-Z]{2,6})"            # TLD: 2-6 letters
    r"\b"                          # word boundary
)

# US Phone: (555) 123-4567, 555-123-4567, +1 555 123 4567, 555.123.4567, 5551234567
# Optional +1, optional parens around area code, separators: space, dash, dot, or none
# Word boundary at end prevents partial match on 555-123-45678
PHONE_PATTERN = re.compile(
    r"(?:\+1[\s.-]?)?"           # optional +1 with separator
    r"(?:\(\d{3}\)|\d{3})"       # area code: (555) or 555
    r"[\s.-]?"                    # optional separator
    r"\d{3}"                      # exchange
    r"[\s.-]?"                    # optional separator
    r"\d{4}"                      # subscriber
    r"\b"                         # word boundary
)

# US ZIP: 12345 or 12345-6789
# Must be at word boundary, not preceded by digit-dash, not followed by digit/dash
ZIP_PATTERN = re.compile(r"(?<!\d-)\b\d{5}(?:-\d{4})?(?![-\d])")

# Dates: 03/15/2024, March 15, 2024, 15 March 2024, Jan 1, 2000
# MM/DD/YYYY with valid month 01-12 | Month DD, YYYY | DD Month YYYY
MONTH = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)
# MM/DD/YYYY - month 01-12, day 01-31
DATE_PATTERN = re.compile(
    rf"(?:0[1-9]|1[0-2])/(?:0[1-9]|[12]\d|3[01])/\d{{4}}"  # MM/DD/YYYY valid
    rf"|(?:{MONTH}\s+\d{{1,2}},\s+\d{{4}})"                  # Month DD, YYYY
    rf"|(?:\d{{1,2}}\s+{MONTH}\s+\d{{4}})"                   # DD Month YYYY
)


# Detector instances (export these)
email_detector = RegexDetector("EMAIL", EMAIL_PATTERN, group=1)
phone_detector = RegexDetector("PHONE", PHONE_PATTERN)
zip_detector = RegexDetector("ZIP", ZIP_PATTERN)
date_detector = RegexDetector("DATE", DATE_PATTERN)


# Convenience: all regex detectors
ALL_REGEX_DETECTORS = [
    email_detector,
    phone_detector,
    zip_detector,
    date_detector,
]


def detect_all_regex(text: str) -> list[Entity]:
    """Run all regex detectors on text and return combined entities."""
    entities = []
    for detector in ALL_REGEX_DETECTORS:
        entities.extend(detector.detect(text))
    return entities