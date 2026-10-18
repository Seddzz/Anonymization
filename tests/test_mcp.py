"""Tests for the MCP tool surface, including the PDF redaction tool."""
import asyncio
from pathlib import Path

import fitz  # PyMuPDF
import pytest
from mcp.server.mcpserver.exceptions import UnexpectedToolError

from anonymizer.mcp_server import anonymize, anonymize_pdf, detect, restore, server


def make_pdf(path: Path, text: str) -> Path:
    doc = fitz.open()
    doc.new_page().insert_text((72, 72), text)
    doc.save(path)
    doc.close()
    return path


def test_tools_are_registered():
    tools = asyncio.run(server.list_tools())
    names = {tool.name for tool in tools}
    assert {"detect", "anonymize", "restore", "anonymize_pdf"} <= names


def test_detect_returns_entities():
    entities = detect("Email a@b.com")
    assert any(entity["label"] == "EMAIL" for entity in entities)


def test_anonymize_and_restore_round_trip():
    result = anonymize("Email a@b.com from us")
    assert "[EMAIL_1]" in result["redacted"]
    restored = restore(result["mapping_id"], result["redacted"])
    assert restored["text"] == "Email a@b.com from us"


def test_anonymize_fake_strategy():
    result = anonymize("Email a@b.com", strategy="fake")
    assert "a@b.com" not in result["redacted"]


def test_restore_unknown_mapping_raises():
    with pytest.raises(ValueError, match="mapping not found"):
        restore("map_nope", "x")


def test_call_tool_returns_json():
    result = asyncio.run(server.call_tool("detect", {"text": "Email a@b.com"}))
    assert result.is_error is False
    text = "".join(item.text for item in result.content)
    assert "EMAIL" in text


def test_call_tool_unknown_mapping_raises():
    with pytest.raises(UnexpectedToolError):
        asyncio.run(
            server.call_tool("restore", {"mapping_id": "map_nope", "redacted": "x"})
        )


def test_anonymize_pdf_writes_redacted_file(tmp_path):
    original = make_pdf(tmp_path / "invoice.pdf", "Contact john.doe@acme.org about EUR 4200.")

    result = anonymize_pdf(str(original))

    redacted_path = Path(result["redacted_pdf"])
    assert redacted_path == tmp_path / "invoice_redacted.pdf"
    assert redacted_path.exists()
    assert redacted_path.read_bytes().startswith(b"%PDF")

    assert "[EMAIL_1]" in result["redacted_text"]
    assert "john.doe@acme.org" not in result["redacted_text"]
    assert result["found"] == {"EMAIL": 1}
    serialized = str(result)
    assert "john.doe@acme.org" not in serialized
    assert result["stamped"] >= 1
    assert result["missed"] == 0
    assert "mapping" not in result

    reopened = fitz.open(redacted_path)
    page_text = " ".join(page.get_text("text") for page in reopened)
    assert "john.doe@acme.org" not in page_text


def test_anonymize_pdf_include_mapping(tmp_path):
    original = make_pdf(tmp_path / "invoice.pdf", "Email a@b.com now.")
    result = anonymize_pdf(str(original), include_mapping=True)
    assert result["mapping"]["[EMAIL_1]"] == "a@b.com"


def test_anonymize_pdf_custom_output_path(tmp_path):
    original = make_pdf(tmp_path / "doc.pdf", "Email a@b.com now.")
    target = tmp_path / "out" / "clean.pdf"
    result = anonymize_pdf(str(original), output_path=str(target))
    assert target.exists()
    assert result["redacted_pdf"] == str(target)


def test_anonymize_pdf_rejects_non_pdf(tmp_path):
    plain = tmp_path / "note.txt"
    plain.write_text("Email a@b.com", encoding="utf-8")
    with pytest.raises(ValueError, match="expects a .pdf"):
        anonymize_pdf(str(plain))


def test_anonymize_pdf_rejects_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        anonymize_pdf(str(tmp_path / "ghost.pdf"))


def test_call_tool_pdf_round_trip(tmp_path):
    original = make_pdf(tmp_path / "note.pdf", "Email a@b.com from us.")
    result = asyncio.run(server.call_tool("anonymize_pdf", {"input_path": str(original)}))
    assert result.is_error is False
    text = "".join(item.text for item in result.content)
    assert "[EMAIL_1]" in text
    assert "a@b.com" not in text
