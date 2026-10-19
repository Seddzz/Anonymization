"""fastapi TestClient-based tests for the REST surface."""
import io

import pymupdf as fitz
from fastapi.testclient import TestClient

import anonymizer.api as api
from anonymizer.api import app
from anonymizer.detect import Entity

client = TestClient(app)


def make_pdf(*page_texts: str) -> bytes:
    doc = fitz.open()
    for text in page_texts:
        page = doc.new_page()
        page.insert_text((72, 72), text)
    return doc.tobytes()


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


def test_anonymize_returns_redacted_only():
    response = client.post("/anonymize", json={"text": "Email a@b.com"})
    assert response.status_code == 200
    body = response.json()
    assert "[EMAIL_1]" in body["redacted"]
    assert "mapping_id" not in body


def test_anonymize_fake_strategy():
    response = client.post("/anonymize", json={"text": "Email a@b.com", "strategy": "fake"})
    assert response.status_code == 200
    assert "a@b.com" not in response.json()["redacted"]


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


def test_anonymize_with_ner_opt_in(monkeypatch):
    monkeypatch.setattr(api, "NerDetector", StubNer)
    monkeypatch.setattr(api, "_ner_engine", None)
    monkeypatch.setattr(api, "_ner_detector", None)

    response = client.post("/anonymize", json={"text": "Hello John Doe", "ner": True})
    assert response.status_code == 200
    assert "[PERSON_1]" in response.json()["redacted"]


def _post_file(path: str, name: str, data: bytes, **params: str):
    return client.post(path, files={"file": (name, io.BytesIO(data))}, params=params)


def test_anonymize_file_txt():
    original = "Contract with John Doe, email john.doe@acme.org dated 03/15/2024."
    response = _post_file("/anonymize-file", "note.txt", original.encode("utf-8"))
    assert response.status_code == 200
    body = response.json()
    assert body["redacted"] != original
    assert "[EMAIL_1]" in body["redacted"]


def test_anonymize_file_pdf_extracts_and_redacts():
    pdf = make_pdf("Invoice for John Doe. Contact john.doe@acme.org.")
    response = _post_file("/anonymize-file", "invoice.pdf", pdf)
    assert response.status_code == 200
    body = response.json()
    assert "[EMAIL_1]" in body["redacted"]
    assert "john.doe@acme.org" not in body["redacted"]


def test_detect_file_pdf_returns_entities():
    pdf = make_pdf("Email support@acme.org about ISTANBUL.")
    response = _post_file("/detect-file", "invoice.pdf", pdf)
    assert response.status_code == 200
    labels = [entity["label"] for entity in response.json()["entities"]]
    assert "EMAIL" in labels

def test_detect_file_txt_ner_query_param():
    response = client.post(
        "/detect-file",
        files={"file": ("a.txt", io.BytesIO(b"plain text"))},
        params={"ner": "false"},
    )
    assert response.status_code == 200


def test_upload_rejects_unknown_suffix():
    response = _post_file("/anonymize-file", "doc.exe", b"MZ...")
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_upload_rejects_empty_file():
    response = _post_file("/anonymize-file", "note.txt", b"")
    assert response.status_code == 400


def test_upload_rejects_oversized_file():
    response = client.post(
        "/anonymize-file",
        files={"file": ("big.txt", io.BytesIO(b"a" * (api.MAX_UPLOAD_BYTES + 1)))},
    )
    assert response.status_code == 413


def test_upload_rejects_scan_with_textless_page():
    doc = fitz.open()
    doc.new_page().insert_text((72, 72), "Full of names such as John Doe.")
    doc.new_page()  # empty page: no text layer -> ScannedDocumentError
    response = _post_file("/anonymize-file", "scan.pdf", doc.tobytes())
    assert response.status_code == 422


def test_anonymize_file_pdf_output_returns_redacted_pdf():
    pdf = make_pdf("Invoice for John Doe. Contact john.doe@acme.org. Total EUR 4200.")
    response = _post_file("/anonymize-file", "invoice.pdf", pdf, output="pdf")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content.startswith(b"%PDF")
    assert response.headers["x-missed-entities"] == "0"

    reopened = fitz.open(stream=response.content, filetype="pdf")
    redacted_page_text = " ".join(page.get_text("text") for page in reopened)
    assert "john.doe@acme.org" not in redacted_page_text
    assert "[EMAIL_1]" in redacted_page_text


def test_anonymize_file_pdf_output_drops_mapping_headers():
    pdf = make_pdf("Email a@b.com for review.")
    response = _post_file("/anonymize-file", "note.pdf", pdf, output="pdf")
    assert response.status_code == 200
    assert "x-mapping-id" not in response.headers


def test_anonymize_file_txt_output_pdf_rejected():
    response = _post_file("/anonymize-file", "note.txt", b"plain text", output="pdf")
    assert response.status_code == 400
    assert "PDF output" in response.json()["detail"]


def test_anonymize_file_pdf_output_fake_strategy():
    pdf = make_pdf("Contact john.doe@acme.org for the invoice.")
    response = _post_file("/anonymize-file", "invoice.pdf", pdf, output="pdf", strategy="fake")
    assert response.status_code == 200
    reopened = fitz.open(stream=response.content, filetype="pdf")
    text = " ".join(page.get_text("text") for page in reopened)
    assert "john.doe@acme.org" not in text
    assert "[EMAIL_1]" not in text  # fake strategy, not placeholders
