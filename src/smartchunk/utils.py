from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

# Optional token counting via tiktoken; fallback heuristic if unavailable
try:
    import tiktoken  # type: ignore
    _enc = tiktoken.get_encoding("cl100k_base")
    def count_tokens(s: str) -> int:
        return len(_enc.encode(s))
except Exception:  # pragma: no cover
    def count_tokens(s: str) -> int:  # type: ignore
        return int(max(1, len(s.split())) * 1.3)

@dataclass
class Chunk:
    id: str
    text: str
    header_path: str
    start_line: int
    end_line: int
