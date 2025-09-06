# ==============================================================================
# chunker.py
#
# Contains the core logic for both the structure-aware SmartChunker and the
# simple NaiveChunker for comparison.
# ==============================================================================

from __future__ import annotations
import re
import itertools
from typing import Iterable, List, Optional
from .utils import Chunk, count_tokens

# --- Regular Expressions for Structure Detection ---
_HEADER_RE = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<title>.+?)\s*$")
_CODE_FENCE_RE = re.compile(r"^```.*$")
_LIST_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+).+")


class SmartChunker:
    """
    Structure-aware chunker for Markdown-like text.
    It identifies structural boundaries (headers, code, lists) and packs
    text segments respecting a size budget.
    """
    def chunk(self, text: str, max_tokens: Optional[int] = None, max_chars: int = 1200, overlap_chars: int = 120) -> List[Chunk]:
        if not text.strip():
            return []
        lines = text.splitlines()
        sections = self._find_sections(lines)
        chunks: List[Chunk] = []
        counter = itertools.count(1)

        for path, (s_line, e_line) in sections:
            segs = self._segment(lines[s_line:e_line], start_offset=s_line)
            for pack in self._pack(segs, max_tokens, max_chars):
                # Add overlap from the previous chunk if requested
                if overlap_chars > 0 and chunks:
                    overlap_text = chunks[-1].text[-overlap_chars:] + "\n\n"
                    text_block = overlap_text + pack["text"]
                else:
                    text_block = pack["text"]

                chunks.append(Chunk(
                    id=f"c{next(counter):04d}",
                    text=text_block,
                    header_path=path,
                    start_line=pack["start_line"],
                    end_line=pack["end_line"],
                ))
        return chunks

    def _find_sections(self, lines: List[str]) -> List[tuple[str, tuple[int, int]]]:
        """Identifies header-based sections and their line spans."""
        # ... (Your existing logic is good and remains unchanged)
        headers = []
        for i, line in enumerate(lines):
            m = _HEADER_RE.match(line)
            if m:
                headers.append({"level": len(m.group("hashes")), "title": m.group("title").strip(), "start": i})
        if not headers:
            headers = [{"level": 1, "title": "Document", "start": 0}]
        for idx, h in enumerate(headers):
            h["end"] = headers[idx + 1]["start"] if idx + 1 < len(headers) else len(lines)

        stack, result = [], []
        for h in headers:
            while stack and stack[-1]["level"] >= h["level"]:
                stack.pop()
            stack.append(h)
            path = " / ".join(x["title"] for x in stack)
            result.append((path, (h["start"], h["end"])))
        return result

    def _segment(self, lines: List[str], start_offset: int) -> List[dict]:
        """Segments text based on structural boundaries like blank lines, lists, and code fences."""
        # ... (Your existing logic is good and remains unchanged)
        segs: List[dict] = []
        buf: List[str] = []
        code = False
        seg_start = start_offset

        def flush(end_line: int):
            if text := "\n".join(buf).rstrip():
                segs.append({"text": text, "start_line": seg_start + 1, "end_line": end_line})

        for i, line in enumerate(lines):
            abs_i = start_offset + i
            if _CODE_FENCE_RE.match(line):
                code = not code
                buf.append(line)
                continue
            if not code and (line.strip() == "" or _LIST_RE.match(line)):
                flush(abs_i)
                buf = [line]
                seg_start = abs_i
            else:
                buf.append(line)
        flush(start_offset + len(lines))
        return segs

    def _pack(self, segs: List[dict], max_tokens: Optional[int], max_chars: Optional[int]) -> Iterable[dict]:
        """Packs segments into chunks that respect the size budget."""
        # ... (Your existing logic is good and remains unchanged)
        if not segs: return
        cur, start = [], segs[0]["start_line"]
        for seg in segs:
            candidate = ("\n".join(cur) + "\n" + seg["text"]).strip() if cur else seg["text"]
            if self._too_big(candidate, max_tokens, max_chars) and cur:
                yield {"text": "\n".join(cur).strip(), "start_line": start, "end_line": seg["start_line"] - 1}
                cur, start = [seg["text"]], seg["start_line"]
            else:
                cur.append(seg["text"])
        if cur:
            yield {"text": "\n".join(cur).strip(), "start_line": start, "end_line": segs[-1]["end_line"]}

    def _too_big(self, text: str, max_tokens: Optional[int], max_chars: int) -> bool:
        """Checks if a text block exceeds the size budget."""
        if max_tokens is not None and count_tokens(text) > max_tokens:
            return True
        if len(text) > max_chars:
            return True
        return False


class NaiveChunker:
    """
    A simple chunker that splits text by a fixed number of characters.
    Used for comparison to demonstrate the value of SmartChunker.
    """
    def chunk(self, text: str, max_chars: int = 1200) -> List[Chunk]:
        """Splits text into simple, character-based chunks."""
        chunks = []
        counter = itertools.count(1)
        for i in range(0, len(text), max_chars):
            chunk_text = text[i:i + max_chars]
            chunks.append(Chunk(
                id=f"n{next(counter):04d}",
                text=chunk_text,
                header_path="N/A",  # Naive chunker has no structural awareness
                start_line=0,       # Line numbers are not tracked
                end_line=0,
            ))
        return chunks