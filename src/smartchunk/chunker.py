# ==============================================================================
# chunker.py (FINAL, COMPLETE, AND CORRECTED VERSION)
# ==============================================================================

from __future__ import annotations
import re
import itertools
from typing import Iterable, List, Optional

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
# sentence-transformers is an optional dependency used only for semantic splitting.
# Import lazily so basic chunking works without the package installed.
try:  # pragma: no cover - import handling
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover - handled gracefully at runtime
    SentenceTransformer = None  # type: ignore

from .utils import Chunk, count_tokens

# --- Regular Expressions for Structure Detection ---
_HEADER_RE = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<title>.+?)\s*$")
_CODE_FENCE_RE = re.compile(r"^```.*$")
_LIST_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+).+")
_SENTENCE_END_RE = re.compile(r'(?<=[.?!])\s+')


class SmartChunker:
    """
    Structure-aware and Semantic-aware chunker for Markdown-like text.
    It identifies structural boundaries and can perform semantic splitting
    on large text blocks to maintain thematic consistency.
    """
    def __init__(self, semantic_model_name: str = 'all-MiniLM-L6-v2') -> None:
        """Initializes the chunker, loading the semantic model if needed."""
        self.model = None
        self._semantic_model_name = semantic_model_name

    def chunk(self, text: str, max_tokens: Optional[int] = None, max_chars: int = 1200, overlap_chars: int = 120, semantic: bool = False, semantic_threshold: float = 0.4) -> List[Chunk]:
        if not text.strip():
            return []
        lines = text.splitlines()
        sections = self._find_sections(lines)
        chunks: List[Chunk] = []
        counter = itertools.count(1)

        for path, (s_line, e_line) in sections:
            segs = self._segment(lines[s_line:e_line], start_offset=s_line)
            for pack in self._pack(segs, max_tokens, max_chars, semantic, semantic_threshold):
                
                text_block = pack["text"]
                
                # Intelligent Overlap Logic
                if overlap_chars > 0 and chunks:
                    is_current_pack_code = pack.get("is_code", False)
                    is_previous_chunk_code = chunks[-1].text.strip().startswith("```")

                    same_section = (
                        chunks[-1].header_path == path or
                        path.startswith(chunks[-1].header_path)
                    )
                    if not is_current_pack_code and not is_previous_chunk_code and same_section:
                        overlap_text = chunks[-1].text[-overlap_chars:]
                        text_block = overlap_text.strip() + " ... " + text_block.strip()
                
                if not text_block.strip(): continue

                chunks.append(Chunk(
                    id=f"c{next(counter):04d}",
                    text=text_block,
                    header_path=path,
                    start_line=pack["start_line"],
                    end_line=pack["end_line"],
                ))
        return chunks

    def _find_sections(self, lines: List[str]) -> List[tuple[str, tuple[int, int]]]:
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
        segs: List[dict] = []
        buf: List[str] = []
        code = False
        seg_start = start_offset

        def flush(end_line: int) -> None:
            if text := "\n".join(buf).rstrip():
                segs.append({"text": text, "start_line": seg_start + 1, "end_line": end_line, "is_code": code})

        for i, line in enumerate(lines):
            abs_i = start_offset + i
            is_fence = _CODE_FENCE_RE.match(line)
            
            if is_fence:
                if code:
                    buf.append(line)
                    flush(abs_i + 1)
                    buf = []
                    seg_start = abs_i + 1
                else:
                    flush(abs_i)
                    buf = [line]
                    seg_start = abs_i
                code = not code
                continue

            if not code and (line.strip() == "" or _LIST_RE.match(line)):
                flush(abs_i)
                buf = [line]
                seg_start = abs_i
            else:
                buf.append(line)
        flush(start_offset + len(lines))
        return segs

    def _semantic_split(self, segment: dict, threshold: float) -> Iterable[str]:
        text = segment["text"]
        if segment.get("is_code", False):
            yield text
            return

        if self.model is None:
            if SentenceTransformer is None:
                raise ImportError("sentence_transformers is required for semantic splitting")
            self.model = SentenceTransformer(self._semantic_model_name)

        sentences = [s.strip() for s in _SENTENCE_END_RE.split(text) if s.strip()]
        if len(sentences) <= 1:
            yield text
            return
            
        embeddings = self.model.encode(sentences, convert_to_tensor=True)
        
        # Move embeddings to CPU before using with NumPy
        cpu_embeddings = embeddings.cpu()

        # --- THIS IS THE FINAL, CORRECT MATH ---
        # Calculate the similarity between adjacent sentences
        # Convert to numpy array before doing the calculation
        cpu_embeddings_numpy = cpu_embeddings.numpy()

        # Compute cosine similarity between adjacent sentence embeddings
        similarities = np.diag(
            cosine_similarity(
                cpu_embeddings_numpy[:-1],
                cpu_embeddings_numpy[1:]
            )
        )
        # ----------------------------------------
        
        start_idx = 0
        for i, sim in enumerate(similarities):
            if sim < threshold:
                yield " ".join(sentences[start_idx:i+1])
                start_idx = i + 1
        
        if start_idx < len(sentences):
            yield " ".join(sentences[start_idx:])

    def _pack(self, segs: List[dict], max_tokens: Optional[int], max_chars: Optional[int], semantic: bool, threshold: float) -> Iterable[dict]:
        current_pack_text = ""
        current_pack_start = -1
        current_pack_end = -1
        is_code_pack = False

        for seg in segs:
            if seg.get("is_code"):
                is_code_pack = True

            if semantic and self._too_big(seg["text"], max_tokens, max_chars) and not seg.get("is_code"):
                if current_pack_text:
                    yield {"text": current_pack_text, "start_line": current_pack_start, "end_line": current_pack_end, "is_code": is_code_pack}
                    current_pack_text, current_pack_start, current_pack_end, is_code_pack = "", -1, -1, False

                for sub_chunk in self._semantic_split(seg, threshold):
                    yield {"text": sub_chunk, "start_line": seg["start_line"], "end_line": seg["end_line"], "is_code": False}
                continue

            if current_pack_text and self._too_big(current_pack_text + "\n\n" + seg["text"], max_tokens, max_chars):
                yield {"text": current_pack_text, "start_line": current_pack_start, "end_line": current_pack_end, "is_code": is_code_pack}
                current_pack_text, current_pack_start, current_pack_end, is_code_pack = "", -1, -1, False
            
            if not current_pack_text:
                current_pack_start = seg["start_line"]
            
            current_pack_text = (current_pack_text + "\n\n" + seg["text"]).strip()
            current_pack_end = seg["end_line"]
            if seg.get("is_code"):
                is_code_pack = True
            
        if current_pack_text:
            yield {"text": current_pack_text, "start_line": current_pack_start, "end_line": current_pack_end, "is_code": is_code_pack}

    def _too_big(self, text: str, max_tokens: Optional[int], max_chars: int) -> bool:
        if max_tokens is not None:
            return count_tokens(text) > max_tokens
        else:
            return len(text) > max_chars


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
                header_path="N/A",
                start_line=0,
                end_line=0,
            ))
        return chunks
