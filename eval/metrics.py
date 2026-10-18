"""Precision/recall/F1 metrics for entity detection."""
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from anonymizer.detect import Entity
from eval.generate import Sample


@dataclass(frozen=True, slots=True)
class Metrics:
    """Aggregate detection scores."""

    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1: float


def _key(entity: Entity) -> tuple[str, int, int]:
    return (entity.label, entity.start, entity.end)


def _ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def _from_counts(true_positives: int, false_positives: int, false_negatives: int) -> Metrics:
    precision = _ratio(true_positives, true_positives + false_positives)
    recall = _ratio(true_positives, true_positives + false_negatives)
    f1 = _ratio(2 * precision * recall, precision + recall)
    return Metrics(true_positives, false_positives, false_negatives, precision, recall, f1)


def compute_metrics(gold: list[Entity], predicted: list[Entity]) -> Metrics:
    """Score predictions against gold entities (exact label+span match)."""
    gold_keys = {_key(entity) for entity in gold}
    pred_keys = {_key(entity) for entity in predicted}
    return _from_counts(
        len(gold_keys & pred_keys),
        len(pred_keys - gold_keys),
        len(gold_keys - pred_keys),
    )


def evaluate(samples: Iterable[Sample], detect_fn: Callable[[str], list[Entity]]) -> Metrics:
    """Micro-average metrics over ``samples`` using ``detect_fn``."""
    true_positives = false_positives = false_negatives = 0
    for sample in samples:
        gold_keys = {_key(entity) for entity in sample.entities}
        pred_keys = {_key(entity) for entity in detect_fn(sample.text)}
        true_positives += len(gold_keys & pred_keys)
        false_positives += len(pred_keys - gold_keys)
        false_negatives += len(gold_keys - pred_keys)
    return _from_counts(true_positives, false_positives, false_negatives)
