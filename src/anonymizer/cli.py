"""Command-line interface for the anonymizer."""
import json
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer

from anonymizer import __version__
from anonymizer.anonymize import anonymize_text
from anonymizer.detect import Entity
from anonymizer.engine import DetectionEngine
from anonymizer.extract import extract_pdf
from anonymizer.restore import restore_text

app = typer.Typer(help="Anonymize English documents: detect, redact, and restore.")

engine = DetectionEngine()


class Strategy(StrEnum):
    placeholder = "placeholder"
    fake = "fake"


def _read_text(path: Path) -> str:
    """Read a document's full text, extracting text layers from PDFs."""
    if path.suffix.lower() == ".pdf":
        return "".join(page.text for page in extract_pdf(path))
    return path.read_text(encoding="utf-8")


def _print_entities(entities: list[Entity]) -> None:
    if not entities:
        typer.echo("No entities found.")
        return
    for entity in entities:
        typer.echo(
            f"{entity.label:<14} {entity.start:>5}:{entity.end:<5} "
            f"{entity.source:<9} {entity.score:.2f}  {entity.text}"
        )


@app.command()
def detect(
    path: Annotated[Path, typer.Argument(help="Input file (.txt or .pdf).")],
) -> None:
    """Detect and list entities in a document."""
    text = _read_text(path)
    _print_entities(engine.detect_all(text))


@app.command()
def anonymize(
    path: Annotated[Path, typer.Argument(help="Input file (.txt or .pdf).")],
    output: Annotated[Path, typer.Option("-o", "--output", help="Redacted output path.")],
    strategy: Annotated[
        Strategy, typer.Option("--strategy", help="Redaction strategy.")
    ] = Strategy.placeholder,
    sidecar: Annotated[
        bool,
        typer.Option(
            "--mapping/--no-mapping",
            help="Write the mapping sidecar for later restoration.",
        ),
    ] = True,
) -> None:
    """Redact a document and optionally write a mapping sidecar next to the output."""
    text = _read_text(path)
    entities = engine.detect_all(text)
    redacted, mapping = anonymize_text(text, entities, strategy=strategy.value)

    output.write_text(redacted, encoding="utf-8")
    typer.echo(f"Redacted {len(entities)} entities -> {output}")
    if sidecar:
        mapping_path = output.with_suffix(output.suffix + ".mapping.json")
        mapping_path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
        typer.echo(f"Mapping -> {mapping_path} (sensitive: contains original values)")


@app.command()
def restore(
    path: Annotated[Path, typer.Argument(help="Redacted file to restore.")],
    mapping: Annotated[Path, typer.Option("--mapping", help="Mapping sidecar (.json).")],
    output: Annotated[
        Path | None, typer.Option("-o", "--output", help="Restored output.")
    ] = None,
) -> None:
    """Restore original text from a redacted file and its mapping."""
    redacted = path.read_text(encoding="utf-8")
    mapping_dict = json.loads(mapping.read_text(encoding="utf-8"))
    restored = restore_text(redacted, mapping_dict)
    if output is None:
        typer.echo(restored)
    else:
        output.write_text(restored, encoding="utf-8")
        typer.echo(f"Restored -> {output}")


@app.command()
def version() -> None:
    """Print the anonymizer version."""
    typer.echo(__version__)
