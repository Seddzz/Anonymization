"""Tests for the anonymizer CLI, including the interactive console."""
import pymupdf as fitz
from typer.testing import CliRunner

from anonymizer import __version__
from anonymizer.cli import app

runner = CliRunner()


def make_pdf(path, text: str):
    doc = fitz.open()
    doc.new_page().insert_text((72, 72), text)
    doc.save(path)
    doc.close()
    return path


def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == __version__


def test_detect_lists_entities(tmp_path):
    document = tmp_path / "doc.txt"
    document.write_text("Email a@b.com", encoding="utf-8")
    result = runner.invoke(app, ["detect", str(document)])
    assert result.exit_code == 0
    assert "EMAIL" in result.stdout


def test_anonymize_writes_redacted_only(tmp_path):
    document = tmp_path / "doc.txt"
    document.write_text("Email a@b.com", encoding="utf-8")
    output = tmp_path / "out.txt"

    result = runner.invoke(app, ["anonymize", str(document), "-o", str(output)])

    assert result.exit_code == 0
    assert "[EMAIL_1]" in output.read_text(encoding="utf-8")
    assert not (tmp_path / "out.txt.mapping.json").exists()


def test_anonymize_fake_strategy(tmp_path):
    document = tmp_path / "doc.txt"
    document.write_text("Email a@b.com", encoding="utf-8")
    output = tmp_path / "out.txt"

    result = runner.invoke(
        app, ["anonymize", str(document), "-o", str(output), "--strategy", "fake"]
    )

    assert result.exit_code == 0
    assert "a@b.com" not in output.read_text(encoding="utf-8")


def test_detect_missing_file_fails():
    result = runner.invoke(app, ["detect", "does-not-exist.txt"])
    assert result.exit_code != 0


def test_anonymize_pdf_output(tmp_path):
    document = make_pdf(tmp_path / "invoice.pdf", "Contact john.doe@acme.org about EUR 4200.")
    output = tmp_path / "invoice_redacted.pdf"

    result = runner.invoke(app, ["anonymize", str(document), "-o", str(output)])

    assert result.exit_code == 0
    assert "In-place stamps" in result.stdout
    reopened = fitz.open(output)
    page_text = " ".join(page.get_text("text") for page in reopened)
    assert "john.doe@acme.org" not in page_text
    assert "[EMAIL_1]" in page_text
    assert not (tmp_path / "invoice_redacted.pdf.mapping.json").exists()


def test_anonymize_pdf_output_requires_pdf_input(tmp_path):
    document = tmp_path / "doc.txt"
    document.write_text("Email a@b.com", encoding="utf-8")

    result = runner.invoke(
        app, ["anonymize", str(document), "-o", str(tmp_path / "out.pdf")]
    )

    assert result.exit_code != 0
    assert "PDF output requires a PDF input" in result.output


def test_console_opens_and_exits():
    result = runner.invoke(app, [], input="4\n")
    assert result.exit_code == 0
    assert "Anonymize a document" in result.output
    assert "nemo" in result.output


def test_console_anonymize_flow(tmp_path):
    document = tmp_path / "doc.txt"
    document.write_text("Email a@b.com", encoding="utf-8")
    feed = f"1\n{document}\nn\n\n\n4\n"

    result = runner.invoke(app, [], input=feed)

    assert result.exit_code == 0
    redacted = tmp_path / "doc_redacted.txt"
    assert redacted.exists()
    assert "[EMAIL_1]" in redacted.read_text(encoding="utf-8")
    assert not (tmp_path / "doc_redacted.txt.mapping.json").exists()


def test_console_pdf_flow(tmp_path):
    document = make_pdf(tmp_path / "invoice.pdf", "Contact a@b.com now.")
    feed = f"1\n{document}\nn\n\n\n4\n"

    result = runner.invoke(app, [], input=feed)

    assert result.exit_code == 0
    output = tmp_path / "invoice_redacted.pdf"
    assert output.exists()
    reopened = fitz.open(output)
    page_text = " ".join(page.get_text("text") for page in reopened)
    assert "a@b.com" not in page_text


def test_console_engine_guide():
    result = runner.invoke(app, [], input="3\n4\n")
    assert result.exit_code == 0
    assert "uvicorn anonymizer.api:app" in result.output


def test_console_unknown_option_recovers():
    result = runner.invoke(app, [], input="99\n4\n")
    assert result.exit_code == 0
    assert "Unknown option" in result.output
