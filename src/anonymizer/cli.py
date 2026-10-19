"""Command-line interface for the anonymizer."""
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer

from anonymizer import __version__
from anonymizer.anonymize import anonymize_text
from anonymizer.detect import Entity
from anonymizer.detectors import ALL_CHECKSUM_DETECTORS, ALL_REGEX_DETECTORS, NerDetector
from anonymizer.engine import DetectionEngine
from anonymizer.extract import extract_pdf
from anonymizer.pdf_output import redact_pdf

app = typer.Typer(help="Anonymize English documents: detect and redact.")

engine = DetectionEngine()


class Strategy(StrEnum):
    placeholder = "placeholder"
    fake = "fake"


_ner_detector: NerDetector | None = None
_ner_engine: DetectionEngine | None = None


def engine_for(ner: bool) -> DetectionEngine:
    """Return the base engine, or lazily build the NER-enabled one."""
    global _ner_detector, _ner_engine
    if not ner:
        return engine
    if _ner_engine is None:
        _ner_detector = NerDetector()
        _ner_engine = DetectionEngine(
            [*ALL_REGEX_DETECTORS, *ALL_CHECKSUM_DETECTORS, _ner_detector]
        )
    return _ner_engine


def read_text(path: Path) -> str:
    """Read a document's full text, extracting text layers from PDFs."""
    if path.suffix.lower() == ".pdf":
        return "".join(page.text for page in extract_pdf(path))
    return path.read_text(encoding="utf-8")


def print_entities(entities: list[Entity]) -> None:
    if not entities:
        typer.echo("No entities found.")
        return
    for entity in entities:
        typer.echo(
            f"{entity.label:<14} {entity.start:>5}:{entity.end:<5} "
            f"{entity.source:<9} {entity.score:.2f}  {entity.text}"
        )


@app.callback(invoke_without_command=True)
def console(ctx: typer.Context) -> None:
    """Open the interactive Nemo console when no subcommand is given."""
    if ctx.invoked_subcommand is None:
        from anonymizer.dashboard import run_console

        run_console()


def anonymize_document(
    path: Path,
    output: Path,
    strategy: Strategy,
    engine_override: DetectionEngine | None = None,
) -> None:
    """Redact ``path`` into ``output`` (PDF in -> PDF out, txt stays text)."""
    text = read_text(path)
    entities = (engine_override or engine).detect_all(text)

    if output.suffix.lower() == ".pdf":
        if path.suffix.lower() != ".pdf":
            raise typer.BadParameter("A PDF output requires a PDF input document.")
        result = redact_pdf(path, entities, strategy=strategy.value)
        output.write_bytes(result.pdf_bytes)
        typer.echo(f"Redacted {len(entities)} entities -> {output}")
        typer.echo(f"In-place stamps: {result.applied}   Skipped: {result.missed}")
        if result.missed:
            typer.echo(
                "Some entities could not be located on the page layout; review the output."
            )
    else:
        redacted = anonymize_text(text, entities, strategy=strategy.value)
        output.write_text(redacted, encoding="utf-8")
        typer.echo(f"Redacted {len(entities)} entities -> {output}")


@app.command()
def detect(
    path: Annotated[Path, typer.Argument(help="Input file (.txt or .pdf).")],
    ner: Annotated[
        bool, typer.Option("--ner/--no-ner", help="Add the transformer NER pass.")
    ] = False,
) -> None:
    """Detect and list entities in a document."""
    print_entities(engine_for(ner).detect_all(read_text(path)))


@app.command()
def anonymize(
    path: Annotated[Path, typer.Argument(help="Input file (.txt or .pdf).")],
    output: Annotated[Path, typer.Option("-o", "--output", help="Redacted output path.")],
    strategy: Annotated[
        Strategy, typer.Option("--strategy", help="Redaction strategy.")
    ] = Strategy.placeholder,
    ner: Annotated[
        bool, typer.Option("--ner/--no-ner", help="Add the transformer NER pass.")
    ] = False,
) -> None:
    """Redact a document into a clean output file."""
    anonymize_document(path, output, strategy, engine_for(ner))


@app.command()
def version() -> None:
    """Print the anonymizer version."""
    typer.echo(__version__)
