# SmartChunk 🧩

**Structure-aware semantic chunking for RAG/LLMs**

SmartChunk is a **Python package + CLI** that creates higher-quality chunks for Retrieval-Augmented Generation (RAG) pipelines. Instead of breaking text blindly, SmartChunk **respects structure and meaning** — no more chopped sentences, broken code blocks, or messy lists.

The result?
👉 Better retrieval quality
👉 Lower token costs
👉 Chunks your LLM can actually understand

---

## ✨ Why SmartChunk?

Naive splitters cut text every N tokens. That causes:

* ❌ Broken headings, lists, or tables
* ❌ Incoherent fragments across paragraphs
* ❌ Duplicate/boilerplate content bloating your index

**SmartChunk fixes this** by combining structure awareness + semantic similarity.

---

## 🧠 Key Features

* **Structure-Aware Splitting**: Never slices through a heading, list, table, or fenced code block.
* **Semantic Boundary Detection**: Uses embeddings to find natural breakpoints between topics.
* **Noise & Duplication Guard**: Strips headers/footers, removes near-duplicates, normalizes whitespace.
* **Flexible & Tunable**: Control chunk size, overlap, and semantic sensitivity to fit your pipeline.
* **End-to-End Ready**: From URL → parsed → deduped → JSONL chunks in one command.

---

## ⚡ Quickstart

### 1. Install

For hackathon/demo (TestPyPI):

```bash
pip install -i https://test.pypi.org/simple/ smartchunk
```

Once published to PyPI:

```bash
pip install smartchunk
```

---

### 2. Chunk a Document

```bash
smartchunk chunk docs/README.md \
  --mode markdown \
  --max-tokens 500 \
  --overlap 100 \
  --dedupe \
  --out chunks.jsonl
```

---

### 3. Fetch & Chunk a URL

```bash
smartchunk fetch "https://en.wikipedia.org/wiki/Artificial_intelligence" \
  --semantic --dedupe --format table
```

---

### 4. Compare with a Naive Splitter

```bash
smartchunk compare docs/README.md --mode markdown --out report.html
```

Generates an **HTML report** showing naive vs SmartChunk side-by-side.

---

## 📦 Example Output

Each line in the `.jsonl` output is a coherent chunk with rich metadata:

```json
{
  "doc_id": "readme-v1",
  "chunk_id": "readme-v1-0007",
  "text": "To install the package, run `pip install smartchunk`...",
  "tokens": 612,
  "start_char": 12420,
  "end_char": 15691,
  "heading_path": ["2. Getting Started", "2.1 Installation"],
  "mode": "markdown",
  "coherence_score": 0.82
}
```

---

## 💻 CLI Overview

* `fetch` → Fetch, parse & chunk a URL in one go
* `chunk` → Chunk a local file
* `compare` → Compare SmartChunk vs naive splitter (HTML report)
* `stream` → Stream chunks from STDIN in real-time

Run `smartchunk --help` for full options.

---

## 🔑 License

MIT License. Free to use, modify, and share.

---

## (In Simple Words) 📝

SmartChunk = **“Don’t let your RAG cut sentences in half.”**
It’s the **first step** for any production-grade RAG pipeline: clean, coherent, AI-ready chunks.
