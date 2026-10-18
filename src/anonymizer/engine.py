"""Detection engine: run all detectors and merge their results."""
from collections.abc import Iterable

from anonymizer.detect import Detector, Entity, validate_entity_offsets
from anonymizer.detectors import ALL_CHECKSUM_DETECTORS, ALL_REGEX_DETECTORS

# When two entities overlap, the most trustworthy source wins.
# checksum = structural proof, regex = deterministic pattern, ner = probabilistic guess.
SOURCE_PRIORITY = {
    "checksum": 3,
    "regex": 2,
    "ner": 1,
}


def _rank(entity: Entity) -> tuple[int, int, float]:
    """Score an entity for overlap resolution: priority, then length, then confidence."""
    return (
        SOURCE_PRIORITY.get(entity.source, 0),
        entity.end - entity.start,
        entity.score,
    )


class DetectionEngine:
    """Runs a set of detectors and resolves their overlapping spans."""

    def __init__(self, detectors: Iterable[Detector] | None = None):
        if detectors is None:
            detectors = [*ALL_REGEX_DETECTORS, *ALL_CHECKSUM_DETECTORS]
        self.detectors: list[Detector] = list(detectors)

    def detect_all(self, text: str) -> list[Entity]:
        """Run every detector, resolve overlaps, and validate the offsets."""
        raw: list[Entity] = []
        for detector in self.detectors:
            raw.extend(detector.detect(text))

        resolved = self.resolve_overlaps(raw)
        validate_entity_offsets(text, resolved)
        return resolved

    def resolve_overlaps(self, entities: list[Entity]) -> list[Entity]:
        """Return non-overlapping entities, preferring higher-ranked spans."""
        ordered = sorted(entities, key=lambda e: e.start)

        resolved: list[Entity] = []
        for entity in ordered:
            if resolved and entity.start < resolved[-1].end:
                if _rank(entity) > _rank(resolved[-1]):
                    resolved[-1] = entity
            else:
                resolved.append(entity)
        return resolved
