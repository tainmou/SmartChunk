from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .chunker import SmartChunker

# Ensure UTF-8 stdout on Windows consoles (avoids UnicodeEncodeError with emojis, etc.)
if os.name == "nt":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

app = typer.Typer(help="SmartChunk: structure-aware chunking for RAG")
console = Console()


@app.command()
def chunk(
    file: Path = typer.Argument(..., exists=True, readable=True, help="Input file (Markdown/plain text)"),
    max_tokens: Optional[int] = typer.Option(None, help="Max tokens per chunk"),
    max_chars: int = typer.Option(1200, help="Max characters per chunk"),
    overlap: int = typer.Option(120, help="Overlap in characters"),
    out: str = typer.Option("table", help="table|json|jsonl"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write output to file (UTF-8)"),
) -> None:
    """
    Chunk a Markdown/text file and print or save chunks.
    """
    text = file.read_text(encoding="utf-8", errors="ignore")
    chunks = SmartChunker().chunk(
        text,
        max_tokens=max_tokens,
        max_chars=max_chars,
        overlap_chars=overlap,
    )

    if out == "jsonl":
        lines = [json.dumps(c.__dict__, ensure_ascii=False) for c in chunks]
        payload = "\n".join(lines) + "\n"
        if output:
            # Use UTF-8 (no BOM). If you want WinPS to auto-detect, switch to "utf-8-sig".
            output.write_text(payload, encoding="utf-8")
        else:
            for line in lines:
                print(line)

    elif out == "json":
        payload = json.dumps([c.__dict__ for c in chunks], ensure_ascii=False, indent=2) + "\n"
        if output:
            output.write_text(payload, encoding="utf-8")
        else:
            print(payload, end="")

    else:  # table
        table = Table(title=f"Chunks ({len(chunks)})")
        table.add_column("id", style="cyan")
        table.add_column("header_path", overflow="fold")
        table.add_column("lines", justify="right")
        table.add_column("chars", justify="right")
        for c in chunks:
            table.add_row(c.id, c.header_path, f"{c.start_line}-{c.end_line}", str(len(c.text)))
        console.print(table)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
