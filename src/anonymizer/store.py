"""In-memory mapping store with TTL-based expiry."""
import secrets
import time
from collections.abc import Callable


class MappingStore:
    """Store placeholder-to-original mappings under short-lived ids.

    Entries expire after ``ttl_seconds`` so sensitive mappings are not kept
    in memory indefinitely. A custom ``clock`` can be injected for testing.
    """

    def __init__(
        self,
        ttl_seconds: int = 900,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._ttl = ttl_seconds
        self._clock = clock
        self._items: dict[str, tuple[dict[str, str], float]] = {}

    def save(self, mapping: dict[str, str]) -> str:
        """Store a copy of ``mapping`` and return its id."""
        self._prune()
        mapping_id = "map_" + secrets.token_hex(4)
        self._items[mapping_id] = (dict(mapping), self._clock() + self._ttl)
        return mapping_id

    def get(self, mapping_id: str) -> dict[str, str] | None:
        """Return the mapping for ``mapping_id``, or ``None`` if absent/expired."""
        self._prune()
        item = self._items.get(mapping_id)
        if item is None:
            return None
        mapping, _expires_at = item
        return dict(mapping)

    def _prune(self) -> None:
        now = self._clock()
        expired = [key for key, (_, expires_at) in self._items.items() if now >= expires_at]
        for key in expired:
            del self._items[key]
