"""Restore redacted text using a placeholder-to-original mapping."""


def restore_text(redacted_text: str, mapping: dict[str, str]) -> str:
    """Replace every placeholder in ``redacted_text`` with its original value.

    Replacements are applied longest-placeholder-first so that a shorter key is
    never substituted inside a longer one (e.g. ``[PERSON_1]`` before
    ``[PERSON_10]``).
    """
    restored = redacted_text
    for placeholder in sorted(mapping, key=len, reverse=True):
        restored = restored.replace(placeholder, mapping[placeholder])
    return restored
