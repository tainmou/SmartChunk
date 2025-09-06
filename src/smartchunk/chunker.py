# src/smartchunk/chunker.py
from __future__ import annotations
import re
import itertools
from typing import Iterable, List, Optional
from .utils import Chunk, count_tokens

_HEADER_RE = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<title>.+?)\s*$")
_CODE_FENCE_RE = re.compile(r"^```.*$")
_LIST_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+).+")

class SmartChunker:
    """
    Structure-aware chunker for Markdown-like text.
    Steps:
      1) Parse headers to form sections and header paths.
      2) Segment on blank lines/list items/code fences (outside code).
      3) Pack segments under a size budget (tokens or chars).
      4) Optional sliding overlap.
    """
    def __init__(self, model_tokens: Optional[int] = None):
        self.model_tokens = model_tokens

    def chunk(
        self,
        text: str,
        max_tokens: Optional[int] = None,
        max_chars: Optional[int] = 1200,
        overlap_tokens: int = 0,
        overlap_chars: int = 120,
    ) -> List[Chunk]:
        if not text.strip():
            return []
        lines = text.splitlines()
        sections = self._find_sections(lines)
        chunks: List[Chunk] = []
        counter = itertools.count(1)

        for path, (s_line, e_line) in sections:
            segs = self._segment(lines[s_line:e_line], start_offset=s_line)
            for pack in self._pack(segs, max_tokens, max_chars):
                # add overlap from previous chunk if requested
                if (overlap_tokens or overlap_chars) and chunks:
                    back = chunks[-1].text
                    overlap = self._tail_overlap(back, overlap_tokens, overlap_chars)
                    text_block = overlap + pack["text"]
                    start_line = min(chunks[-1].end_line, pack["start_line"]) - overlap.count("\n")
                else:
                    text_block = pack["text"]
                    start_line = pack["start_line"]

                chunks.append(Chunk(
                    id=f"c{next(counter):04d}",
                    text=text_block,
                    header_path=path,
                    start_line=start_line,
                    end_line=pack["end_line"],
                ))
        return chunks

    # ---------- internals ----------
    def _find_sections(self, lines: List[str]) -> List[tuple[str, tuple[int, int]]]:
        headers = []
        for i, line in enumerate(lines):
            m = _HEADER_RE.match(line)
            if m:
                headers.append({"level": len(m.group("hashes")),
                                "title": m.group("title").strip(),
                                "start": i})
        if not headers:
            headers = [{"level": 1, "title": "Document", "start": 0}]
        for idx, h in enumerate(headers):
            h["end"] = headers[idx + 1]["start"] if idx + 1 < len(headers) else len(lines)

        stack = []
        result = []
        for h in headers:
            while stack and stack[-1]["level"] >= h["level"]:
                stack.pop()
            stack.append(h)
            path = " / ".join(x["title"] for x in stack)
            result.append((path, (h["start"], h["end"])))
        return result

    def _segment(self, lines: List[str], start_offset: int) -> List[dict]:
        segs: List[dict] = []
        buf: List[str] = []
        code = False
        seg_start = start_offset

        def flush(end_line: int) -> None:
            if not buf:
                return
            text = "\n".join(buf).rstrip()
            if text:
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
        if not segs:
            return []
        cur: List[str] = []
        start = segs[0]["start_line"]
        for seg in segs:
            candidate = ("\n".join(cur) + "\n" + seg["text"]).strip() if cur else seg["text"]
            if self._too_big(candidate, max_tokens, max_chars) and cur:
                yield {"text": "\n".join(cur).strip(), "start_line": start, "end_line": seg["start_line"] - 1}
                cur = [seg["text"]]
                start = seg["start_line"]
            else:
                cur.append(seg["text"])
        if cur:
            yield {"text": "\n".join(cur).strip(), "start_line": start, "end_line": segs[-1]["end_line"]}

    def _too_big(self, text: str, max_tokens: Optional[int], max_chars: Optional[int]) -> bool:
        if max_tokens is not None and count_tokens(text) > max_tokens:
            return True
        if max_chars is not None and len(text) > max_chars:
            return True
        return False

    def _tail_overlap(self, text: str, overlap_tokens: int, overlap_chars: int) -> str:
        if overlap_tokens:
            tok = count_tokens(text)
            if tok <= overlap_tokens:
                return text + "\n\n"
            ratio = overlap_tokens / max(1, tok)
            n = max(1, int(len(text) * ratio))
            return text[-n:] + "\n\n"
        if overlap_chars:
            return text[-overlap_chars:] + "\n\n"
        return ""
