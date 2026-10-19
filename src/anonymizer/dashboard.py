"""Interactive Nemo console — the one terminal home for the app."""
import sys
from pathlib import Path

import typer

from anonymizer import __version__, cli

LIME = "\x1b[38;2;200;255;0m"
LIME_DARK = "\x1b[38;2;130;165;0m"
DIM = "\x1b[38;2;98;113;120m"
RESET = "\x1b[0m"

_GRADIENT_TOP = (224, 255, 92)
_GRADIENT_BOTTOM = (104, 158, 0)

_GLYPHS = {
    "N": [
        "█   █",
        "██  █",
        "██  █",
        "█ █ █",
        "█  ██",
        "█  ██",
        "█   █",
    ],
    "E": [
        "█████",
        "█    ",
        "█    ",
        "████ ",
        "█    ",
        "█    ",
        "█████",
    ],
    "M": [
        "█   █",
        "██ ██",
        "█ █ █",
        "█ █ █",
        "█   █",
        "█   █",
        "█   █",
    ],
    "O": [
        " ███ ",
        "█   █",
        "█   █",
        "█   █",
        "█   █",
        "█   █",
        " ███ ",
    ],
}

_TOOLS = (
    ("detect", "anon detect <file> [--ner]"),
    ("anonymize", "anon anonymize <in> -o <out> [--strategy fake]"),
    ("inputs", ".txt and .pdf — pdf keeps its original layout"),
    ("engine", "uvicorn anonymizer.api:app --port 8000 → /docs"),
)

_DOC_SUFFIXES = (".txt", ".pdf")


def pixel_banner() -> list[str]:
    """Hermes-style big pixel NEMO: fine glyphs, doubled rows for shading."""
    rows = [
        "  ".join("".join(char * 2 for char in _GLYPHS[letter][glyph_row]) for letter in "NEMO")
        for glyph_row in range(7)
    ]
    doubled: list[str] = []
    for row in rows:
        doubled.extend([row, row])
    return doubled


def _shade(fraction: float) -> str:
    red = round(_GRADIENT_TOP[0] + (_GRADIENT_BOTTOM[0] - _GRADIENT_TOP[0]) * fraction)
    green = round(_GRADIENT_TOP[1] + (_GRADIENT_BOTTOM[1] - _GRADIENT_TOP[1]) * fraction)
    blue = round(_GRADIENT_TOP[2] + (_GRADIENT_BOTTOM[2] - _GRADIENT_TOP[2]) * fraction)
    return f"\x1b[38;2;{red};{green};{blue}m"


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
    if not sys.stdout.isatty() and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    rows = pixel_banner()
    steps = len(rows) - 1
    for index, row in enumerate(rows):
        typer.echo(_paint(row, _shade(index / steps)))
    typer.echo("")
    _ribbon_panel()
    typer.echo("")

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


def _ribbon_panel() -> None:
    """Hermes-style ribbon + Available Tools list."""
    version_text = f"nemo v{__version__}"
    tail_text = " · one-way redaction · local"
    plain_length = len(version_text) + len(tail_text) + 2
    padding = max(0, 74 - plain_length)
    left, right = padding // 2 + 1, padding - padding // 2 + 1
    dashes = "─"
    typer.echo(
        _paint(dashes * left, LIME_DARK)
        + " "
        + _paint(version_text, LIME)
        + _paint(tail_text, DIM)
        + " "
        + _paint(dashes * right, LIME_DARK)
    )
    typer.echo("")
    typer.echo(_paint(" Available Tools", DIM))
    for label, value in _TOOLS:
        typer.echo(_paint(f"   {label + ':':<11}", DIM) + _paint(value, LIME))
