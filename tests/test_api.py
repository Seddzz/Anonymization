from fastapi.testclient import TestClient

from anonymizer.api import app

client = TestClient(app)


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
