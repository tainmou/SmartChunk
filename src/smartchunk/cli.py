
# ==============================================================================
# cli.py
#
# This script defines the main command-line interface (CLI) for SmartChunk.
# It uses the `argparse` library to handle commands and options, and `rich`
# for polished, user-friendly output.
#
# As the orchestrator, this file is responsible for:
#   1. Parsing user commands and arguments.
#   2. Calling the appropriate backend modules (parsers, chunker).
#   3. Displaying status and results to the user.
# ==============================================================================

from __future__ import annotations

import argparse
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

# --- Placeholder Functions ---
# These functions will eventually be replaced by calls to the actual logic
# in other modules (parsers.py, chunker.py). This allows you to build and
# test the CLI independently.

def run_chunk_pipeline(args):
    """Placeholder function to orchestrate the 'chunk' command."""
    console = Console()
    console.print(f"✅ [bold green]Starting 'chunk' command...[/bold green]")
    console.print(f"   - Input file: {args.file}")
    console.print(f"   - Mode: {args.mode}")
    console.print(f"   - Output file: {args.out}")
    # In the future, this function will call the parser and chunker.
    console.print("\n[bold green]Pipeline finished successfully![/bold green]")

def run_compare_pipeline(args):
    """Placeholder function to orchestrate the 'compare' command."""
    console = Console()
    console.print(f"✅ [bold blue]Starting 'compare' command...[/bold blue]")
    console.print(f"   - Input file: {args.file}")
    console.print(f"   - Mode: {args.mode}")
    console.print(f"   - Output report: {args.out}")
    # In the future, this will run both naive and smart chunking and generate a report.
    console.print("\n[bold blue]Comparison report generated successfully![/bold blue]")


# --- Main CLI Function ---

def main():
    """
    The main entry point for the SmartChunk command-line tool.
    """
    # main parser for the `smartchunk` command.
    parser = argparse.ArgumentParser(
        description="""SmartChunk: Structure-aware semantic chunking for RAG/LLMs.""",
        epilog="""Example: smartchunk chunk 'path/to/file.md' --mode markdown --out 'output.jsonl'""",
        formatter_class=argparse.RawTextHelpFormatter
    )

    # SUBPARSERS FOR COMMANDS
    # This creates the command system (e.g., `smartchunk chunk`, `smartchunk compare`).
    # `dest='command'` will store which command was used (e.g., 'chunk').
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # 'chunk' COMMAND PARSER
    chunk_parser = subparsers.add_parser("chunk", help="Process a document into smart chunks and save as JSONL.")
    chunk_parser.add_argument("file", type=str, help="Path to the input file to be chunked.")
    chunk_parser.add_argument("-m", "--mode", type=str, required=True, choices=["markdown", "html", "text"], help="The mode for parsing the file.")
    chunk_parser.add_argument("-o", "--out", type=str, required=True, help="Path to save the output .jsonl file.")
    chunk_parser.add_argument("--max-tokens", default=800, type=int, help="Maximum number of tokens per chunk. (Default: 800)")
    chunk_parser.add_argument("--overlap", default=100, type=int, help="Number of overlapping tokens between chunks. (Default: 100)")
    chunk_parser.add_argument("--min-sim", type=float, default=0.3, help="Minimum similarity threshold for semantic splitting. (Default: 0.3)")
    chunk_parser.add_argument("-d", "--dedupe", action="store_true", help="Enable the removal of near-duplicate paragraphs.")
    chunk_parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output during processing.")

    # 'compare' COMMAND PARSER
    compare_parser = subparsers.add_parser("compare", help="Compare SmartChunk against a naive splitter and generate an HTML report.")
    compare_parser.add_argument("file", type=str, help="Path to the input file to be compared.")
    compare_parser.add_argument("-m", "--mode", type=str, required=True, choices=["markdown", "html", "text"], help="The mode for parsing the file.")
    compare_parser.add_argument("-o", "--out", type=str, required=True, help="Path to save the output .html report.")
    compare_parser.add_argument("--max-tokens", default=800, type=int, help="Max tokens to use for both splitters. (Default: 800)")

    # 5. --- PARSE ARGUMENTS AND EXECUTE ---
    args = parser.parse_args()

    # This is the "routing" logic. It checks which command was used
    # and calls the corresponding function.
    if args.command == "chunk":
        run_chunk_pipeline(args)
    elif args.command == "compare":
        run_compare_pipeline(args)
    else:
        # This case should not be reached if a command is required, but it's good practice.
        parser.print_help()

# This standard Python construct ensures that the `main` function is called
# only when the script is executed directly (not when imported as a module).
if __name__ == "__main__":
    main()
