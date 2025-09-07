SmartChunk 🧩
Structure-aware semantic chunking for RAG/LLMs.

SmartChunk is a command-line tool that produces higher-quality chunks for RAG pipelines by respecting document structure and meaning. It stops your RAG system from cutting sentences, code blocks, and lists in half, leading to better retrieval quality and lower token costs.

Key Features
🧠 Structure-Aware Splitting: Understands Markdown, HTML, and plain-text structure. It never splits in the middle of a heading, list, table, or fenced code block.

✂️ Semantic Boundary Detection: Uses sentence embeddings to find natural "low-similarity valleys" between sentences, ensuring that splits happen at logical topic boundaries, not at arbitrary token counts.

✨ Noise & Duplication Guard: Strips boilerplate content (like headers/footers), collapses near-duplicate paragraphs, and normalizes whitespace to produce clean, high-signal chunks.

Quickstart
Get started in under 60 seconds.

1. Installation
Install the package directly from TestPyPI (during the hackathon). Make sure you are using Python 3.10+.

pip install -i [https://test.pypi.org/simple/](https://test.pypi.org/simple/) smartchunk

2. Chunk a Document
Run the chunk command to process a file and generate a JSONL output.

smartchunk chunk docs/README.md \
  --mode markdown \
  --max-tokens 700 \
  --dedupe \
  --out out/chunks.jsonl

3. Compare with a Naive Splitter
Use the compare command to generate an HTML report that visually shows the difference between SmartChunk and a standard token-based splitter.

smartchunk compare docs/README.md --mode markdown --out report.html

Example Output
The output is a .jsonl file, where each line is a JSON object representing a single, coherent chunk.

{
  "doc_id": "readme-v1",
  "chunk_id": "readme-v1-0007",
  "text": "To install the package, run `pip install smartchunk`. This will add the `smartchunk` command to your path...",
  "tokens": 612,
  "start_char": 12420,
  "end_char": 15691,
  "heading_path": ["2. Getting Started", "2.1 Installation"],
  "mode": "markdown",
  "coherence_score": 0.82
}

CLI Usage
chunk command
usage: smartchunk chunk [-h] --mode {markdown,html,text} [--max-tokens MAX_TOKENS] [--overlap OVERLAP] [--min-sim MIN_SIM] [--dedupe] --out OUT FILE

Arguments:
  FILE                  Path to the input file.

Options:
  --mode                File type (markdown, html, text).
  --max-tokens          Maximum number of tokens per chunk. (Default: 800)
  --out                 Path to save the output JSONL file.
  --dedupe              Enable near-duplicate paragraph removal.
  ... and more

License
This project is licensed under the MIT License. See the LICENSE file for details.

(IN SIMPLE:-)
SmartChunk 🧩
An intelligent, structure-aware, and semantic-aware chunking tool for RAG pipelines.

SmartChunk is an end-to-end command-line tool that transforms raw web content or local files into high-quality, AI-ready data chunks. It's designed to be the essential first step in any production-grade RAG pipeline.

Key Features

📡 End-to-End Pipeline: Go from a URL to structured, intelligent chunks with a single command.

🧠 Structure-Aware Parsing: Understands HTML, Markdown, and text. It correctly parses document structure, preserving headers, code blocks, lists, and tables.

✂️ Semantic Splitting: Uses sentence embeddings to find natural topic boundaries in large text blocks, ensuring chunks are thematically coherent.

✨ Noise & Duplication Guard: Intelligently extracts the main content from web pages, discarding ads and boilerplate. The --dedupe flag removes near-duplicate chunks.

⚙️ Tunable & Flexible: Fine-tune chunking with controls for size, overlap, and semantic sensitivity.

Quickstart

1. Installation

pip install smartchunk

(Once you've published to PyPI)

2. Fetch and Chunk a URL
Run the fetch command on any URL to see the full pipeline in action.

smartchunk fetch "[https://en.wikipedia.org/wiki/Artificial_intelligence](https://en.wikipedia.org/wiki/Artificial_intelligence)" --semantic --dedupe --format table

3. Chunk a Local File
Process local HTML, Markdown, or text files with the same intelligent engine.

smartchunk chunk my_document.md --mode markdown --max-tokens 500 --overlap 100

4. Compare with a Naive Splitter
See the dramatic difference between SmartChunk and a standard character-based splitter.

smartchunk compare langchain/demo.html --mode html

License

This project is licensed under the MIT License. See the LICENSE file for details.


