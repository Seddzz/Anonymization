import pytest

from anonymizer.detect import Entity, validate_entity_offsets
from anonymizer.engine import DetectionEngine
from eval.generate import DatasetGenerator
from eval.metrics import compute_metrics, evaluate

KNOWN_LABELS = {"EMAIL", "PHONE", "ZIP", "DATE", "CARD", "IBAN"}


def test_generated_offsets_are_consistent():
    samples = DatasetGenerator(seed=0).generate(20)
    assert samples
    for sample in samples:
        validate_entity_offsets(sample.text, sample.entities)
        assert {entity.label for entity in sample.entities} <= KNOWN_LABELS


def test_generator_is_deterministic():
    first = DatasetGenerator(seed=7).generate(5)
    second = DatasetGenerator(seed=7).generate(5)
    assert [sample.text for sample in first] == [sample.text for sample in second]


def test_engine_recalls_generated_pii():
    samples = DatasetGenerator(seed=1).generate(30)
    metrics = evaluate(samples, DetectionEngine().detect_all)
    assert metrics.recall == 1.0
    assert metrics.precision == 1.0


def test_compute_metrics_perfect():
    entities = [Entity("EMAIL", 0, 5, "a@b.c", 1.0, "gold")]
    metrics = compute_metrics(entities, entities)
    assert (metrics.precision, metrics.recall, metrics.f1) == (1.0, 1.0, 1.0)


def test_compute_metrics_partial():
    gold = [
        Entity("EMAIL", 0, 5, "a@b.c", 1.0, "gold"),
        Entity("PHONE", 6, 11, "12345", 1.0, "gold"),
    ]
    predicted = [Entity("EMAIL", 0, 5, "a@b.c", 1.0, "regex")]
    metrics = compute_metrics(gold, predicted)
    assert (metrics.true_positives, metrics.false_positives) == (1, 0)
    assert metrics.false_negatives == 1
    assert metrics.precision == 1.0
    assert metrics.recall == 0.5


def test_compute_metrics_no_predictions():
    gold = [Entity("EMAIL", 0, 5, "a@b.c", 1.0, "gold")]
    metrics = compute_metrics(gold, [])
    assert (metrics.precision, metrics.recall, metrics.f1) == (0.0, 0.0, 0.0)


def test_compute_metrics_empty():
    metrics = compute_metrics([], [])
    assert (metrics.precision, metrics.recall, metrics.f1) == (0.0, 0.0, 0.0)


def test_compute_metrics_counts_false_positives():
    gold = [Entity("EMAIL", 0, 5, "a@b.c", 1.0, "gold")]
    predicted = [
        Entity("EMAIL", 0, 5, "a@b.c", 1.0, "regex"),
        Entity("ZIP", 6, 11, "12345", 1.0, "regex"),
    ]
    metrics = compute_metrics(gold, predicted)
    assert metrics.false_positives == 1
    assert metrics.precision == pytest.approx(0.5)
