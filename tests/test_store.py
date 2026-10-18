from anonymizer.store import MappingStore


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_save_and_get():
    store = MappingStore()
    mapping_id = store.save({"[PERSON_1]": "John"})
    assert mapping_id.startswith("map_")
    assert store.get(mapping_id) == {"[PERSON_1]": "John"}


def test_get_unknown_returns_none():
    assert MappingStore().get("map_nope") is None


def test_entry_expires_after_ttl():
    clock = Clock()
    store = MappingStore(ttl_seconds=10, clock=clock)
    mapping_id = store.save({"[PERSON_1]": "John"})
    clock.advance(9)
    assert store.get(mapping_id) is not None
    clock.advance(2)
    assert store.get(mapping_id) is None


def test_expired_entries_are_pruned():
    clock = Clock()
    store = MappingStore(ttl_seconds=5, clock=clock)
    stale_id = store.save({"[PERSON_1]": "John"})
    clock.advance(6)
    store.save({"[PERSON_2]": "Jane"})
    assert store.get(stale_id) is None


def test_saved_mapping_is_copied():
    store = MappingStore()
    original = {"[PERSON_1]": "John"}
    mapping_id = store.save(original)
    original["[PERSON_1]"] = "mutated"
    assert store.get(mapping_id) == {"[PERSON_1]": "John"}
