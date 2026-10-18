"""Fake surrogate generation for the ``fake`` redaction strategy."""
from collections.abc import Callable

from faker import Faker


def _digits(length: int) -> Callable[[Faker], str]:
    return lambda fake: fake.numerify("#" * length)


FAKE_PROVIDERS: dict[str, Callable[[Faker], str]] = {
    "PERSON": lambda f: f.name(),
    "ORGANIZATION": lambda f: f.company(),
    "LOCATION": lambda f: f.city(),
    "EMAIL": lambda f: f.email(),
    "PHONE": lambda f: f.phone_number(),
    "IBAN": lambda f: f.iban(),
    "CARD": lambda f: f.credit_card_number(),
    "ZIP": lambda f: f.postcode(),
    "DATE": lambda f: f.date(),
    "SSN": lambda f: f.ssn(),
    "SIREN": _digits(9),
    "SIRET": _digits(14),
    "NIR": _digits(15),
}


class FakeGenerator:
    """Produce realistic-looking surrogates per entity label.

    Pass ``seed`` to make output reproducible (useful for tests).
    """

    def __init__(self, seed: int | None = None, locale: str = "en_US") -> None:
        self._fake = Faker(locale)
        if seed is not None:
            Faker.seed(seed)

    def generate(self, label: str) -> str:
        """Return a fake value for ``label``, falling back to a word."""
        provider = FAKE_PROVIDERS.get(label)
        if provider is None:
            return self._fake.word()
        return provider(self._fake)
