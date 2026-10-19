"""Interactive Nemo console — the one terminal home for the app."""
import sys
from pathlib import Path

import typer

from anonymizer import __version__, cli

LIME = "\x1b[38;2;200;255;0m"
LIME_DARK = "\x1b[38;2;130;165;0m"
DIM = "\x1b[38;2;98;113;120m"
RESET = "\x1b[0m"

_GLYPHS = {
    "N": ["█   █", "██  █", "█ █ █", "█  ██", "█   █"],
    "E": ["█████", "█    ", "████ ", "█    ", "█████"],
    "M": ["█   █", "██ ██", "█ █ █", "█   █", "█   █"],
    "O": [" ███ ", "█   █", "█   █", "█   █", " ███ "],
}

_DOC_SUFFIXES = (".txt", ".pdf")


def pixel_banner() -> list[str]:
    """Big two-by pixels NEMO, mirrored rows for a gradient-like shading."""
    rows = [
        "  ".join("".join(char * 2 for char in _GLYPHS[letter][row]) for letter in "NEMO")
        for row in range(5)
    ]
    doubled: list[str] = []
    for row in rows:
        doubled.extend([row, row])
    return doubled


def _paint(text: str, color: str = "") -> str:
    if color and sys.stdout.isatty():
        return f"{color}{text}{RESET}"
    return text


def _header(title: str) -> None:
    typer.echo("")
    typer.echo(_paint(f"── {title}", LIME))


def _ask_path(label: str, suffixes: tuple[str, ...] = _DOC_SUFFIXES) -> Path | None:
    path = Path(typer.prompt(label)).expanduser()
    if not path.exists():
        typer.echo(_paint(f"  ✗ Not found: {path}", LIME))
        return None
    if path.suffix.lower() not in suffixes:
        expected = " or ".join(suffixes)
        typer.echo(_paint(f"  ✗ Only {expected} files are accepted here.", LIME))
        return None
    return path


def _ask_strategy() -> cli.Strategy:
    raw = ""
    while raw not in ("placeholder", "fake"):
        raw = typer.prompt("Strategy", default="placeholder").strip().lower()
    return cli.Strategy(raw)


def _flow_anonymize() -> None:
    path = _ask_path("Document path (.txt/.pdf)")
    if path is None:
        return
    ner = typer.confirm("Use transformer NER? (downloads the model on first use)", default=False)
    strategy = _ask_strategy()
    default_out = path.with_name(f"{path.stem}_redacted{path.suffix}")
    output = Path(typer.prompt("Output path", default=str(default_out))).expanduser()
    try:
        cli.anonymize_document(path, output, strategy, cli.engine_for(ner))
    except Exception as exc:
        typer.echo(_paint(f"  ✗ {exc}", LIME))


def _flow_detect() -> None:
    path = _ask_path("Document path (.txt/.pdf)")
    if path is None:
        return
    ner = typer.confirm("Use transformer NER? (downloads the model on first use)", default=False)
    cli.print_entities(cli.engine_for(ner).detect_all(cli.read_text(path)))


def _guide_engine() -> None:
    _header("Engine quickstart")
    typer.echo(_paint("  Python:", DIM))
    typer.echo("    python -m uvicorn anonymizer.api:app --port 8000")
    typer.echo(_paint("  Docker:", DIM))
    typer.echo("    docker compose up --build")
    typer.echo("")
    typer.echo(_paint("  Swagger UI", DIM) + "  →  http://localhost:8000/docs")
    typer.echo(_paint("  Health", DIM) + "     →  http://localhost:8000/health")
    typer.echo(_paint("  Docs + assistant", DIM) + "  →  http://localhost:3000")
    _header("Homebrew docs: `cd web && npm run dev` for the site that talks to the engine")


_HANDLERS = {
    "1": lambda: (_header("Anonymize a document"), _flow_anonymize()),
    "2": lambda: (_header("Detect entities"), _flow_detect()),
    "3": _guide_engine,
}


def run_console() -> None:
    shading = (LIME, LIME_DARK)
    for index, row in enumerate(pixel_banner()):
        typer.echo(_paint(row, shading[index % 2]))
    typer.echo("")
    typer.echo(_paint(f" nemo v{__version__}", LIME) + _paint(" · one-way redaction · local", DIM))
    typer.echo("")
    typer.echo(_paint(" Available Tools", DIM))
    typer.echo(_paint("   detect:    ", DIM) + "regex + checksum layers (+ optional NER)")
    typer.echo(_paint("   anonymize: ", DIM) + "placeholder | fake strategies")
    typer.echo(_paint("   inputs:    ", DIM) + ".txt and .pdf — pdf keeps its original layout")
    typer.echo(_paint("   engine:    ", DIM) + "uvicorn anonymizer.api:app --port 8000 (REST)")

    while True:
        typer.echo("")
        typer.echo(_paint("  1) Anonymize a document    3) Engine quickstart", DIM))
        typer.echo(_paint("  2) Detect entities         4) Exit", DIM))
        try:
            choice = typer.prompt("nemo ›").strip()
        except (KeyboardInterrupt, EOFError):
            typer.echo("")
            break
        if choice in ("4", "q", "quit", "exit"):
            break
        handler = _HANDLERS.get(choice)
        if handler is None:
            typer.echo(_paint(f"  ✗ Unknown option '{choice}'", LIME))
        else:
            handler()
