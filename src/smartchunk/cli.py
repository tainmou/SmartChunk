# ==============================================================================
# cli.py
#
# Defines the main command-line interface (CLI) for SmartChunk using Typer.
# It orchestrates the process by parsing user input and calling the
# appropriate chunking logic.
# ==============================================================================

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .chunker import NaiveChunker, SmartChunker

# Initialize the Typer app and Rich console
app = typer.Typer(
    help="SmartChunk: A structure-aware chunking tool for RAG pipelines.",
    add_completion=False
)
console = Console()


@app.command()
def chunk(
    file: Path = typer.Argument(..., exists=True, readable=True, help="Input file (Markdown/plain text)"),
    max_tokens: Optional[int] = typer.Option(None, help="Max tokens per chunk (requires tiktoken)"),
    max_chars: int = typer.Option(1200, help="Max characters per chunk"),
    overlap: int = typer.Option(120, help="Overlap in characters between chunks"),
    out_format: str = typer.Option("table", "--format", help="Output format: table | json | jsonl"),
    output_file: Optional[Path] = typer.Option(None, "--output", "-o", help="Write output to a specified file (UTF-8)"),
) -> None:
    """
    Chunks a document using the structure-aware SmartChunker.
    """
    console.print(f"✨ Processing file: [bold cyan]{file.name}[/bold cyan] with SmartChunker")
    text = file.read_text(encoding="utf-8", errors="ignore")

    chunks = SmartChunker().chunk(
        text,
        max_tokens=max_tokens,
        max_chars=max_chars,
        overlap_chars=overlap,
    )

    # --- Output Handling ---
    if output_file:
        _write_output(output_file, chunks, out_format)
    else:
        _print_output(chunks, out_format)


@app.command()
def compare(
    file: Path = typer.Argument(..., exists=True, readable=True, help="Input file to compare chunkers on"),
    max_chars: int = typer.Option(1200, help="Max characters per chunk for comparison"),
) -> None:
    """
    Compares the output of SmartChunker vs. a NaiveChunker on the same file.
    """
    console.print(f"🔬 Comparing chunkers on: [bold cyan]{file.name}[/bold cyan]")
    text = file.read_text(encoding="utf-8", errors="ignore")

    # Run both chunkers
    smart_chunks = SmartChunker().chunk(text, max_chars=max_chars)
    naive_chunks = NaiveChunker().chunk(text, max_chars=max_chars)

    # Print a summary table for SmartChunker
    console.print("\n[bold green]=== SmartChunker Output ===[/bold green]")
    _print_output(smart_chunks, "table")

    # Print a summary table for NaiveChunker
    console.print("\n[bold red]=== NaiveChunker Output ===[/bold red]")
    _print_output(naive_chunks, "table")

    console.print(f"\n[bold]Summary:[/bold] SmartChunker produced [green]{len(smart_chunks)}[/green] structured chunks, while NaiveChunker produced [red]{len(naive_chunks)}[/red] simple chunks.")


# --- Helper functions for output ---

def _write_output(output_file: Path, chunks: list, format: str):
    """Writes the chunk output to a file."""
    if format == "jsonl":
        lines = [json.dumps(c.__dict__, ensure_ascii=False) for c in chunks]
        payload = "\n".join(lines) + "\n"
    elif format == "json":
        payload = json.dumps([c.__dict__ for c in chunks], ensure_ascii=False, indent=2) + "\n"
    else:
        console.print("[bold red]Error:[/bold red] Table output can only be printed to the console, not saved to a file.")
        raise typer.Exit(1)

    output_file.write_text(payload, encoding="utf-8")
    console.print(f"✅ Successfully saved {len(chunks)} chunks to [bold green]{output_file}[/bold green]")


def _print_output(chunks: list, format: str):
    """Prints the chunk output to the console."""
    if format == "jsonl":
        for c in chunks:
            console.print(json.dumps(c.__dict__, ensure_ascii=False))
    elif format == "json":
        console.print(json.dumps([c.__dict__ for c in chunks], ensure_ascii=False, indent=2))
    else:  # "table"
        table = Table(title=f"Chunks ({len(chunks)})")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Header Path", overflow="fold")
        table.add_column("Lines", justify="right")
        table.add_column("Chars", justify="right")
        for c in chunks:
            table.add_row(c.id, c.header_path, f"{c.start_line}–{c.end_line}", str(len(c.text)))
        console.print(table)

