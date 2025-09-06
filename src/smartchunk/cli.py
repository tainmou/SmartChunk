# ==============================================================================
# cli.py
#
# SmartChunk CLI (Typer + Rich)
# - chunk: batch mode (file in, chunks out)
# - stream: realtime mode (stdin in, chunks out continuously)
# - compare: SmartChunker vs NaiveChunker (summary tables)
# ==============================================================================

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.table import Table

from .chunker import SmartChunker, NaiveChunker
from . import parsers  # parse_markdown / parse_html / parse_text

# ──────────────────────────────────────────────────────────────────────────────
# Ensure UTF-8 stdout on Windows (avoid mojibake/encode errors)
# ──────────────────────────────────────────────────────────────────────────────
if os.name == "nt":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        # Best effort; continue with whatever encoding is available
        pass

# Typer app + Rich console
app = typer.Typer(
    help="SmartChunk: structure-aware chunking for RAG pipelines.",
    add_completion=False,
)
console = Console()


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────
def _normalize_text(raw_text: str, mode: str) -> str:
    """Apply minimal parsing/cleanup based on input mode."""
    mode = (mode or "markdown").lower()
    if mode == "html":
        return parsers.parse_html(raw_text)
    if mode == "text":
        return parsers.parse_text(raw_text)
    # default: markdown
    return parsers.parse_markdown(raw_text)


def _write_output(output_file: Path, chunks: List, fmt: str) -> None:
    """Write chunks to a file (UTF-8)."""
    fmt = fmt.lower()
    if fmt == "jsonl":
        lines = [json.dumps(c.__dict__, ensure_ascii=False) for c in chunks]
        payload = "\n".join(lines) + "\n"
    elif fmt == "json":
        payload = json.dumps([c.__dict__ for c in chunks], ensure_ascii=False, indent=2) + "\n"
    else:
        console.print(
            "[bold red]Error:[/bold red] 'table' format is for console only. "
            "Use --format json|jsonl when writing to a file."
        )
        raise typer.Exit(1)

    output_file.write_text(payload, encoding="utf-8")
    console.print(f"✅ Saved [bold]{len(chunks)}[/bold] chunks → [green]{output_file}[/green]")


def _print_output(chunks: List, fmt: str) -> None:
    """Print chunks to console."""
    fmt = fmt.lower()
    if fmt == "jsonl":
        for c in chunks:
            console.print(json.dumps(c.__dict__, ensure_ascii=False))
        return

    if fmt == "json":
        console.print(json.dumps([c.__dict__ for c in chunks], ensure_ascii=False, indent=2))
        return

    # table
    table = Table(title=f"Chunks ({len(chunks)})")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Header Path", overflow="fold")
    table.add_column("Lines", justify="right")
    table.add_column("Chars", justify="right")
    for c in chunks:
        table.add_row(c.id, c.header_path, f"{c.start_line}-{c.end_line}", str(len(c.text)))
    console.print(table)


# ──────────────────────────────────────────────
# Batch mode
# ──────────────────────────────────────────────
@app.command()
def chunk(
    file: Path = typer.Argument(..., exists=True, readable=True, help="Input file"),
    mode: str = typer.Option("markdown", help="Input type: markdown | html | text"),
    max_tokens: Optional[int] = typer.Option(None, help="Max tokens per chunk (optional)"),
    max_chars: int = typer.Option(1200, help="Max characters per chunk"),
    overlap: int = typer.Option(120, help="Overlap in characters between chunks"),
    out_format: str = typer.Option("table", "--format", "-f", help="Output: table | json | jsonl"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write output to file (UTF-8)"),
) -> None:
    """Chunk a file and print/save chunks."""
    console.print(f"✨ Processing: [bold cyan]{file.name}[/bold cyan] (mode={mode})")
    raw_text = file.read_text(encoding="utf-8", errors="ignore")
    text = _normalize_text(raw_text, mode)

    chunks = SmartChunker().chunk(
        text,
        max_tokens=max_tokens,
        max_chars=max_chars,
        overlap_chars=overlap,
    )

    if output:
        _write_output(output, chunks, out_format)
    else:
        _print_output(chunks, out_format)


# ──────────────────────────────────────────────
# Compare mode (Smart vs Naive)
# ──────────────────────────────────────────────
@app.command()
def compare(
    file: Path = typer.Argument(..., exists=True, readable=True, help="Input file"),
    mode: str = typer.Option("markdown", help="Input type: markdown | html | text"),
    max_chars: int = typer.Option(1200, help="Max characters per chunk"),
) -> None:
    """
    Compare SmartChunker with a naive fixed-size chunker and show table summaries.
    """
    console.print(f"🔬 Comparing on: [bold cyan]{file.name}[/bold cyan] (mode={mode})")
    raw_text = file.read_text(encoding="utf-8", errors="ignore")
    text = _normalize_text(raw_text, mode)

    smart = SmartChunker().chunk(text, max_chars=max_chars)
    naive = NaiveChunker().chunk(text, max_chars=max_chars)

    console.print("\n[bold green]=== SmartChunker ===[/bold green]")
    _print_output(smart, "table")
    console.print("\n[bold red]=== NaiveChunker ===[/bold red]")
    _print_output(naive, "table")

    console.print(
        f"\n[bold]Summary:[/bold] SmartChunker produced [green]{len(smart)}[/green] "
        f"structured chunks; NaiveChunker produced [red]{len(naive)}[/red] fixed chunks."
    )


# ──────────────────────────────────────────────
# Streaming mode (stdin → chunks as they arrive)
# ──────────────────────────────────────────────
@app.command()
def stream(
    mode: str = typer.Option("markdown", help="Input type: markdown | html | text"),
    max_tokens: Optional[int] = typer.Option(None, help="Max tokens per chunk (optional)"),
    max_chars: int = typer.Option(800, help="Max characters per chunk"),
    overlap: int = typer.Option(100, help="Overlap in characters"),
    out_format: str = typer.Option("jsonl", "--format", "-f", help="Output: jsonl | table"),
    flush_factor: float = typer.Option(1.5, help="Emit when buffer ≥ max_chars * factor"),
) -> None:
    """
    Stream chunks from STDIN in near-real-time.

    Examples (PowerShell):
      Get-Content README.md | smartchunk stream --format jsonl
      type README.md | smartchunk stream --format table
    """
    console.rule("[bold]SmartChunk streaming[/bold]")

    buffer: list[str] = []
    carry_text = ""   # un-emitted tail from last batch
    emitted = 0

    def emit(text_block: str, final: bool = False) -> None:
        nonlocal emitted, carry_text
        if not text_block.strip():
            return

        processed = _normalize_text(text_block, mode)
        chunks = SmartChunker().chunk(
            processed,
            max_tokens=max_tokens,
            max_chars=max_chars,
            overlap_chars=overlap,
        )
        if not chunks:
            return

        # keep the last partial chunk as carry unless this is the final flush
        to_emit = chunks if final or len(chunks) == 1 else chunks[:-1]
        carry_text = "" if final else chunks[-1].text

        if out_format.lower() == "jsonl":
            for c in to_emit:
                # print to stdout (already UTF-8)
                print(json.dumps(c.__dict__, ensure_ascii=False))
                emitted += 1
        else:
            t = Table(title=f"New chunks (+{len(to_emit)})")
            t.add_column("id", style="cyan")
            t.add_column("chars", justify="right")
            t.add_column("preview", overflow="fold")
            for c in to_emit:
                preview = (c.text[:100] + "…") if len(c.text) > 100 else c.text
                t.add_row(c.id, str(len(c.text)), preview.replace("\n", " "))
            console.print(t)
            emitted += len(to_emit)

    try:
        for line in sys.stdin:
            buffer.append(line)
            current = carry_text + "".join(buffer)

            # flush when buffer is big enough OR empty line (paragraph break)
            if len(current) >= int(max_chars * flush_factor) or line.strip() == "":
                emit(current, final=False)
                buffer.clear()

        # final flush
        final_block = carry_text + "".join(buffer)
        emit(final_block, final=True)
        console.print(f"[green]Streaming complete.[/green] Emitted {emitted} chunks.")
    except KeyboardInterrupt:
        final_block = carry_text + "".join(buffer)
        emit(final_block, final=True)
        console.print(f"[yellow]Interrupted.[/yellow] Emitted {emitted} chunks.")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
