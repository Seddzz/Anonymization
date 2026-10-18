"""Generate synthetic English documents with ground-truth PII for evaluation."""
import re
from dataclasses import dataclass

from faker import Faker

from anonymizer.detect import Entity

SLOT = re.compile(r"\{([A-Z]+)\}")

_IBANS = [
    "GB82WEST12345698765432",
    "DE89370400440532013000",
    "FR1420041010050500013M02606",
]

TEMPLATES = [
    "Please email {EMAIL} or call {PHONE} before {DATE}.",
    "Ship the order to ZIP {ZIP}; invoice {CARD} on {DATE}.",
    "For payment transfer to {IBAN}. Questions? Email {EMAIL}.",
    "Reach {EMAIL} or {PHONE}. Billing ZIP {ZIP}.",
    "Refund for card {CARD} was created on {DATE}.",
    "Update records: {PHONE}, {EMAIL}, ZIP {ZIP}.",
]


def _luhn_check_digit(prefix: str) -> str:
    """Return the check digit that makes ``prefix`` + digit Luhn-valid.

    Independent implementation (an oracle for the detector, not a copy).
    """
    for digit in "0123456789":
        number = [int(c) for c in prefix + digit]
        total = 0
        for i, value in enumerate(reversed(number)):
            if i % 2 == 1:
                value *= 2
                if value > 9:
                    value -= 9
            total += value
        if total % 10 == 0:
            return digit
    raise RuntimeError("no valid Luhn check digit found")


@dataclass(frozen=True, slots=True)
class Sample:
    """A generated document and the entities it contains."""

    text: str
    entities: list[Entity]


class DatasetGenerator:
    """Generate synthetic documents with known PII spans."""

    def __init__(self, seed: int = 0) -> None:
        self._fake = Faker("en_US")
        Faker.seed(seed)
        self._iban_index = 0

    def _value(self, label: str) -> str:
        fake = self._fake
        if label == "EMAIL":
            return fake.email()
        if label == "PHONE":
            return fake.numerify("(###) ###-####")
        if label == "ZIP":
            return fake.numerify("#####")
        if label == "DATE":
            return fake.date_object().strftime("%m/%d/%Y")
        if label == "CARD":
            prefix = fake.numerify("###############")
            return prefix + _luhn_check_digit(prefix)
        if label == "IBAN":
            iban = _IBANS[self._iban_index % len(_IBANS)]
            self._iban_index += 1
            return iban
        raise ValueError(f"unknown label: {label}")

    def _build(self, template: str) -> Sample:
        parts: list[str] = []
        entities: list[Entity] = []
        offset = 0
        last = 0
        for match in SLOT.finditer(template):
            literal = template[last : match.start()]
            parts.append(literal)
            offset += len(literal)

            label = match.group(1)
            value = self._value(label)
            entities.append(Entity(label, offset, offset + len(value), value, 1.0, "gold"))
            parts.append(value)
            offset += len(value)
            last = match.end()

        parts.append(template[last:])
        return Sample(text="".join(parts), entities=entities)

    def generate(self, count: int = 1) -> list[Sample]:
        """Return ``count`` generated samples."""
        return [self._build(self._fake.random_element(TEMPLATES)) for _ in range(count)]
