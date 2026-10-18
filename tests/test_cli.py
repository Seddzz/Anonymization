from typer.testing import CliRunner

from anonymizer import __version__
from anonymizer.cli import app

runner = CliRunner()


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


def test_anonymize_writes_redacted_and_mapping(tmp_path):
    document = tmp_path / "doc.txt"
    document.write_text("Email a@b.com", encoding="utf-8")
    output = tmp_path / "out.txt"

    result = runner.invoke(app, ["anonymize", str(document), "-o", str(output)])

    assert result.exit_code == 0
    assert "[EMAIL_1]" in output.read_text(encoding="utf-8")
    assert (tmp_path / "out.txt.mapping.json").exists()


def test_anonymize_then_restore_round_trip(tmp_path):
    original = "Email a@b.com from us"
    document = tmp_path / "doc.txt"
    document.write_text(original, encoding="utf-8")
    output = tmp_path / "out.txt"
    runner.invoke(app, ["anonymize", str(document), "-o", str(output)])

    restored = tmp_path / "restored.txt"
    result = runner.invoke(
        app,
        [
            "restore",
            str(output),
            "--mapping",
            str(tmp_path / "out.txt.mapping.json"),
            "-o",
            str(restored),
        ],
    )

    assert result.exit_code == 0
    assert restored.read_text(encoding="utf-8") == original


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
