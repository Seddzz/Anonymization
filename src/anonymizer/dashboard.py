"""Interactive Nemo console — the one terminal home for the app."""
import sys
from pathlib import Path

import typer

from anonymizer import __version__, cli

LIME = "\x1b[38;2;200;255;0m"
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
    return ["  ".join(_GLYPHS[letter][row] for letter in "NEMO") for row in range(5)]


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
    sidecar = typer.confirm("Write a mapping sidecar for restoration?", default=False)
    default_out = path.with_name(f"{path.stem}_redacted{path.suffix}")
    output = Path(typer.prompt("Output path", default=str(default_out))).expanduser()
    try:
        cli.anonymize_document(path, output, strategy, sidecar, cli.engine_for(ner))
    except Exception as exc:
        typer.echo(_paint(f"  ✗ {exc}", LIME))


def _flow_detect() -> None:
    path = _ask_path("Document path (.txt/.pdf)")
    if path is None:
        return
    ner = typer.confirm("Use transformer NER? (downloads the model on first use)", default=False)
    cli.print_entities(cli.engine_for(ner).detect_all(cli.read_text(path)))


def _flow_restore() -> None:
    redacted = _ask_path("Redacted document")
    if redacted is None:
        return
    mapping = _ask_path("Mapping sidecar path", suffixes=(".json",))
    if mapping is None:
        return
    default_out = redacted.with_name(f"{redacted.stem}_restored{redacted.suffix}")
    output = Path(typer.prompt("Output path", default=str(default_out))).expanduser()
    try:
        cli.restore(redacted, mapping=mapping, output=output)
    except Exception as exc:
        typer.echo(_paint(f"  ✗ {exc}", LIME))


def _guide_mcp() -> None:
    _header("Agent (MCP) setup")
    typer.echo("Point your local agent at the bundled MCP server:")
    typer.echo("")
    typer.echo(_paint("  Claude Code:", DIM))
    typer.echo("    claude mcp add nemo -- python -m anonymizer.mcp_server")
    typer.echo(_paint("  Codex CLI (add to ~/.codex/config.toml):", DIM))
    typer.echo('    [mcp_servers.nemo]')
    typer.echo('    command = "python"')
    typer.echo('    args = ["-m", "anonymizer.mcp_server"]')
    typer.echo(_paint("  Cursor / others:", DIM))
    typer.echo('    command = "python", args = ["-m", "anonymizer.mcp_server"]')
    typer.echo("")
    typer.echo(_paint("  Tip: use this venv's python, e.g. .venv\\Scripts\\python (Windows).", DIM))
    typer.echo(_paint("  Then, in the agent:", DIM))
    typer.echo('    "Use the anonymize_pdf tool on invoice.pdf, then summarize the redacted text."')
    typer.echo(_paint("  The redacted PDF lands next to the original — no mapping needed.", DIM))


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
    "3": lambda: (_header("Restore from mapping"), _flow_restore()),
    "4": _guide_mcp,
    "5": _guide_engine,
}


def run_console() -> None:
    for row in pixel_banner():
        typer.echo(_paint(row, LIME))
    typer.echo(_paint(f" nemo · {__version__} — everything runs on your machine", DIM))

    while True:
        typer.echo("")
        typer.echo(_paint("  1) Anonymize a document    4) Agent (MCP) setup", DIM))
        typer.echo(_paint("  2) Detect entities         5) Engine quickstart", DIM))
        typer.echo(_paint("  3) Restore from mapping    6) Exit", DIM))
        try:
            choice = typer.prompt("nemo ›").strip()
        except (KeyboardInterrupt, EOFError):
            typer.echo("")
            break
        if choice in ("6", "q", "quit", "exit"):
            break
        handler = _HANDLERS.get(choice)
        if handler is None:
            typer.echo(_paint(f"  ✗ Unknown option '{choice}'", LIME))
        else:
            handler()
