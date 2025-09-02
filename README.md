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
