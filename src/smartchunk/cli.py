# ==============================================================================
# cli.py (FINAL, COMPLETE, AND POLISHED VERSION)
#
# SmartChunk CLI (Typer + Rich)
# - fetch:  Complete end-to-end pipeline (URL -> Chunks)
# - chunk:  Batch mode (file in, chunks out)
# - stream: Realtime mode (stdin in, chunks out continuously)
# - compare: SmartChunker vs NaiveChunker (summary tables)
# ==============================================================================

from __future__ import annotations
import json
import os
import sys
import logging
from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.table import Table

from .chunker import SmartChunker, NaiveChunker
from . import parsers
from .fetcher import fetch_article_text

# ──────────────────────────────────────────────────────────────────────────────
# Boilerplate and Helpers (No changes here)
# ──────────────────────────────────────────────────────────────────────────────
if os.name == "nt":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

app = typer.Typer(
    help="SmartChunk: End-to-end pipeline for fetching, parsing, and chunking content for RAG.",
    add_completion=False,
)
console = Console()


@app.callback()
def main(
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        help="Log level (e.g. DEBUG, INFO, WARNING, ERROR)",
    ),
) -> None:
    logging.basicConfig(level=getattr(logging, log_level.upper(), logging.INFO))

def _normalize_text(raw_text: str, mode: str) -> str:
    mode = (mode or "markdown").lower()
    if mode == "html":
        return parsers.parse_html(raw_text)
    if mode == "text":
        return parsers.parse_text(raw_text)
    return parsers.parse_markdown(raw_text)

def _write_output(output_file: Path, chunks: List, fmt: str) -> None:
    fmt = fmt.lower()
    if fmt == "jsonl":
        lines = [json.dumps(c.__dict__, ensure_ascii=False) for c in chunks]
        payload = "\n".join(lines) + "\n"
    elif fmt == "json":
        payload = json.dumps([c.__dict__ for c in chunks], ensure_ascii=False, indent=2) + "\n"
    else:
        console.print("[bold red]Error:[/bold red] 'table' format is for console only.")
        raise typer.Exit(1)
    output_file.write_text(payload, encoding="utf-8")
    console.print(f"✅ Saved [bold]{len(chunks)}[/bold] chunks → [green]{output_file}[/green]")

def _print_output(chunks: List, fmt: str) -> None:
    fmt = fmt.lower()
    if fmt == "jsonl":
        for c in chunks: console.print(json.dumps(c.__dict__, ensure_ascii=False))
        return
    if fmt == "json":
        console.print(json.dumps([c.__dict__ for c in chunks], ensure_ascii=False, indent=2))
        return
    table = Table(title=f"Chunks ({len(chunks)})")
    table.add_column("ID", style="cyan")
    table.add_column("Header Path", overflow="fold")
    table.add_column("Lines", justify="right")
    table.add_column("Chars", justify="right")
    for c in chunks: table.add_row(c.id, c.header_path, f"{c.start_line}-{c.end_line}", str(len(c.text)))
    console.print(table)


# ──────────────────────────────────────────────
# --- NEW GOATED FETCH COMMAND ---
# ──────────────────────────────────────────────
@app.command()
def fetch(
    url: str = typer.Argument(..., help="URL of the article to fetch and chunk."),
    max_tokens: Optional[int] = typer.Option(None, help="Max tokens per chunk (optional)"),
    max_chars: int = typer.Option(1200, help="Max characters per chunk"),
    overlap: int = typer.Option(120, help="Overlap in characters between chunks"),
    semantic: bool = typer.Option(False, "--semantic", help="Enable semantic splitting."),
    semantic_threshold: float = typer.Option(0.4, help="Similarity threshold for semantic splitting."),
    semantic_model: str = typer.Option(
        "all-MiniLM-L6-v2",
        "--semantic-model",
        help="SentenceTransformer model to use for semantic splitting.",
    ),
    out_format: str = typer.Option("table", "--format", "-f", help="Output: table | json | jsonl"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write output to file (UTF-8)"),
) -> None:
    """
    Fetch, parse, and chunk content directly from a URL in one go.
    """
    console.print(f"📡 Fetching content from: [bold blue]{url}[/bold blue]")
    html_content = fetch_article_text(url)
    if not html_content:
        console.print("[bold red]Error:[/bold red] Could not retrieve content from the URL.")
        raise typer.Exit(1)
        
    console.print("🧹 Cleaning and parsing HTML...")
    text = _normalize_text(html_content, mode="html")

    console.print("🧠 Chunking content with SmartChunk AI...")
    chunker = SmartChunker(semantic_model_name=semantic_model)
    chunks = chunker.chunk(
        text,
        max_tokens=max_tokens,
        max_chars=max_chars,
        overlap_chars=overlap,
        semantic=semantic,
        semantic_threshold=semantic_threshold,
    )

    console.print(f"🏆 Found and processed [bold green]{len(chunks)}[/bold green] high-quality chunks.")
    
    if output:
        _write_output(output, chunks, out_format)
    else:
        _print_output(chunks, out_format)

# ──────────────────────────────────────────────
# Existing Commands (with stream updated)
# ──────────────────────────────────────────────
@app.command()
def chunk(
    file: Path = typer.Argument(..., exists=True, readable=True, help="Input file"),
    mode: str = typer.Option("markdown", help="Input type: markdown | html | text"),
    max_tokens: Optional[int] = typer.Option(None, help="Max tokens per chunk (optional)"),
    max_chars: int = typer.Option(1200, help="Max characters per chunk"),
    overlap: int = typer.Option(120, help="Overlap in characters between chunks"),
    semantic: bool = typer.Option(False, "--semantic", help="Enable semantic splitting."),
    semantic_threshold: float = typer.Option(0.4, help="Similarity threshold for semantic splitting."),
    semantic_model: str = typer.Option(
        "all-MiniLM-L6-v2",
        "--semantic-model",
        help="SentenceTransformer model to use for semantic splitting.",
    ),
    out_format: str = typer.Option("table", "--format", "-f", help="Output: table | json | jsonl"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write output to file (UTF-8)"),
) -> None:
    """Chunk a local file and print/save chunks."""
    console.print(f"✨ Processing: [bold cyan]{file.name}[/bold cyan] (mode={mode})")
    raw_text = file.read_text(encoding="utf-8", errors="ignore")
    text = _normalize_text(raw_text, mode)
    chunker = SmartChunker(semantic_model_name=semantic_model)
    chunks = chunker.chunk(
        text,
        max_tokens=max_tokens,
        max_chars=max_chars,
        overlap_chars=overlap,
        semantic=semantic,
        semantic_threshold=semantic_threshold,
    )
    if output: _write_output(output, chunks, out_format)
    else: _print_output(chunks, out_format)

@app.command()
def compare(
    file: Path = typer.Argument(..., exists=True, readable=True, help="Input file"),
    mode: str = typer.Option("markdown", help="Input type: markdown | html | text"),
    max_chars: int = typer.Option(1200, help="Max characters per chunk"),
) -> None:
    """Compare SmartChunker with a naive fixed-size chunker."""
    console.print(f"🔬 Comparing on: [bold cyan]{file.name}[/bold cyan] (mode={mode})")
    raw_text = file.read_text(encoding="utf-8", errors="ignore")
    text = _normalize_text(raw_text, mode)
    smart = SmartChunker().chunk(text, max_chars=max_chars)
    naive = NaiveChunker().chunk(text, max_chars=max_chars)
    console.print("\n[bold green]=== SmartChunker ===[/bold green]")
    _print_output(smart, "table")
    console.print("\n[bold red]=== NaiveChunker ===[/bold red]")
    _print_output(naive, "table")
    console.print(f"\n[bold]Summary:[/bold] SmartChunker produced [green]{len(smart)}[/green] chunks; NaiveChunker produced [red]{len(naive)}[/red] chunks.")

@app.command()
def stream(
    mode: str = typer.Option("markdown", help="Input type: markdown | html | text"),
    max_tokens: Optional[int] = typer.Option(None, help="Max tokens per chunk (optional)"),
    max_chars: int = typer.Option(800, help="Max characters per chunk"),
    overlap: int = typer.Option(100, help="Overlap in characters"),
    semantic: bool = typer.Option(False, "--semantic", help="Enable semantic splitting."),
    semantic_threshold: float = typer.Option(0.4, help="Similarity threshold for semantic splitting."),
    semantic_model: str = typer.Option(
        "all-MiniLM-L6-v2",
        "--semantic-model",
        help="SentenceTransformer model to use for semantic splitting.",
    ),
    out_format: str = typer.Option("jsonl", "--format", "-f", help="Output: jsonl | table"),
    flush_factor: float = typer.Option(1.5, help="Emit when buffer ≥ max_chars * factor"),
) -> None:
    """Stream chunks from STDIN in near-real-time."""
    console.rule("[bold]SmartChunk streaming[/bold]")
    buffer: list[str] = []
    carry_text = ""
    emitted = 0
    chunker = SmartChunker(semantic_model_name=semantic_model)
    def emit(text_block: str, final: bool = False) -> None:
        nonlocal emitted, carry_text
        if not text_block.strip(): return
        processed = _normalize_text(text_block, mode)
        chunks = chunker.chunk(processed, max_tokens=max_tokens, max_chars=max_chars, overlap_chars=overlap, semantic=semantic, semantic_threshold=semantic_threshold)
        if not chunks: return
        to_emit = chunks if final or len(chunks) == 1 else chunks[:-1]
        carry_text = "" if final else chunks[-1].text
        if out_format.lower() == "jsonl":
            for c in to_emit:
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
            if len(current) >= int(max_chars * flush_factor) or line.strip() == "":
                emit(current, final=False)
                buffer.clear()
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

