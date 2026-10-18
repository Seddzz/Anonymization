from fastapi.testclient import TestClient

import anonymizer.api as api
from anonymizer.api import app
from anonymizer.detect import Entity

client = TestClient(app)


class StubNer:
    """Stand-in for NerDetector so tests never download the model."""

    def detect(self, text: str) -> list[Entity]:
        index = text.find("John Doe")
        if index < 0:
            return []
        return [Entity("PERSON", index, index + 8, "John Doe", 0.99, "ner")]


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_detect_finds_entities():
    response = client.post("/detect", json={"text": "Email a@b.com"})
    assert response.status_code == 200
    labels = [entity["label"] for entity in response.json()["entities"]]
    assert "EMAIL" in labels


def test_anonymize_then_restore_round_trip():
    text = "Email a@b.com from John"
    anonymized = client.post("/anonymize", json={"text": text})
    assert anonymized.status_code == 200
    body = anonymized.json()
    assert "[EMAIL_1]" in body["redacted"]

    restored = client.post(
        "/restore",
        json={"mapping_id": body["mapping_id"], "redacted": body["redacted"]},
    )
    assert restored.status_code == 200
    assert restored.json()["text"] == text


def test_anonymize_fake_strategy():
    response = client.post("/anonymize", json={"text": "Email a@b.com", "strategy": "fake"})
    assert response.status_code == 200
    assert "a@b.com" not in response.json()["redacted"]


def test_restore_unknown_mapping_id_returns_404():
    response = client.post("/restore", json={"mapping_id": "map_nope", "redacted": "x"})
    assert response.status_code == 404


def test_anonymize_invalid_strategy_returns_422():
    response = client.post("/anonymize", json={"text": "x", "strategy": "nope"})
    assert response.status_code == 422


def test_cors_allows_local_dev_origin():
    response = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_cors_rejects_unknown_origin():
    response = client.get("/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in response.headers


def test_detect_ignores_names_without_ner():
    response = client.post("/detect", json={"text": "John Doe"})
    assert response.status_code == 200
    assert response.json()["entities"] == []


def test_detect_with_ner_opt_in(monkeypatch):
    monkeypatch.setattr(api, "NerDetector", StubNer)
    monkeypatch.setattr(api, "_ner_engine", None)
    monkeypatch.setattr(api, "_ner_detector", None)

    response = client.post("/detect", json={"text": "John Doe", "ner": True})

    assert response.status_code == 200
    entities = response.json()["entities"]
    assert any(entity["label"] == "PERSON" and entity["source"] == "ner" for entity in entities)


def test_anonymize_with_ner_opt_in_round_trip(monkeypatch):
    monkeypatch.setattr(api, "NerDetector", StubNer)
    monkeypatch.setattr(api, "_ner_engine", None)
    monkeypatch.setattr(api, "_ner_detector", None)

    text = "Hello John Doe"
    anonymized = client.post("/anonymize", json={"text": text, "ner": True})
    assert anonymized.status_code == 200
    body = anonymized.json()
    assert "[PERSON_1]" in body["redacted"]

    restored = client.post(
        "/restore",
        json={"mapping_id": body["mapping_id"], "redacted": body["redacted"]},
    )
    assert restored.json()["text"] == text
