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
from . import parsers  # markdown/html/text helpers

# Ensure UTF-8 stdout on Windows (avoid mojibake/encode errors)
if os.name == "nt":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

app = typer.Typer(help="SmartChunk: structure-aware semantic chunking for RAG")
console = Console()


# ──────────────────────────────────────────────
# Standard batch mode
# ──────────────────────────────────────────────
@app.command()
def chunk(
    file: Path = typer.Argument(..., exists=True, readable=True, help="Input file"),
    mode: str = typer.Option("markdown", help="Input type: markdown|html|text"),
    max_tokens: Optional[int] = typer.Option(None, help="Max tokens per chunk"),
    max_chars: int = typer.Option(1200, help="Max characters per chunk"),
    overlap: int = typer.Option(120, help="Overlap in characters"),
    out: str = typer.Option("table", help="Output format: table|json|jsonl"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write output to file (UTF-8)"),
) -> None:
    """Chunk a file and print/save chunks."""
    raw_text = file.read_text(encoding="utf-8", errors="ignore")

    if mode == "html":
        text = parsers.parse_html(raw_text)
    elif mode == "text":
        text = parsers.parse_text(raw_text)
    else:  # markdown default
        print(text)

    chunks = SmartChunker().chunk(
        text,
        max_tokens=max_tokens,
        max_chars=max_chars,
        overlap_chars=overlap,
    )

    if out == "jsonl":n
        lines = [json.dumps(c.__dict__, ensure_ascii=False) for c in chunks]
        payload = "\n".join(lines) + "\n"
        if output:
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


# ──────────────────────────────────────────────
# Real-time streaming mode
# ──────────────────────────────────────────────
@app.command()
def stream(
    mode: str = typer.Option("markdown", help="Input type: markdown|html|text"),
    max_tokens: Optional[int] = typer.Option(None, help="Max tokens per chunk"),
    max_chars: int = typer.Option(800, help="Max characters per chunk"),
    overlap: int = typer.Option(100, help="Overlap in characters"),
    out: str = typer.Option("jsonl", help="Output format: jsonl|table"),
    flush_factor: float = typer.Option(1.5, help="Emit when buffer >= max_chars * factor"),
) -> None:
    """
    Stream chunks from STDIN in real-time.
    Example:
        type README.md | smartchunk stream --out jsonl
    """
    console.rule("[bold]SmartChunk streaming[/bold]")
    buffer: list[str] = []
    carry_text = ""
    emitted = 0

    def emit_chunks(text_block: str, final: bool = False) -> None:
        nonlocal emitted, carry_text
        if not text_block.strip():
            return

        if mode == "html":
            processed = parsers.parse_html(text_block)
        elif mode == "text":
            processed = parsers.parse_text(text_block)
        else:
            processed = parsers.parse_markdown(text_block)

        chunks = SmartChunker().chunk(
            processed,
            max_tokens=max_tokens,
            max_chars=max_chars,
            overlap_chars=overlap,
        )
        if not chunks:
            return

        to_emit = chunks if final or len(chunks) == 1 else chunks[:-1]
        carry_text = "" if final else chunks[-1].text

        if out == "jsonl":
            for c in to_emit:
                print(json.dumps(c.__dict__, ensure_ascii=False))
                emitted += 1
        else:
            table = Table(title=f"New chunks (+{len(to_emit)})")
            table.add_column("id", style="cyan")
            table.add_column("chars", justify="right")
            table.add_column("preview", overflow="fold")
            for c in to_emit:
                preview = (c.text[:100] + "…") if len(c.text) > 100 else c.text
                table.add_row(c.id, str(len(c.text)), preview.replace("\n", " "))
            console.print(table)

    try:
        for line in sys.stdin:
            buffer.append(line)
            current = carry_text + "".join(buffer)

            if len(current) >= int(max_chars * flush_factor) or line.strip() == "":
                emit_chunks(current, final=False)
                buffer.clear()

        final_block = carry_text + "".join(buffer)
        emit_chunks(final_block, final=True)
        console.print(f"[green]Streaming complete.[/green] Emitted {emitted} chunks.")
    except KeyboardInterrupt:
        final_block = carry_text + "".join(buffer)
        emit_chunks(final_block, final=True)
        console.print(f"[yellow]Interrupted.[/yellow] Emitted {emitted} chunks.")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
