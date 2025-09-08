"""SmartChunk package public API and version handling."""

from importlib import metadata as importlib_metadata
from pathlib import Path
import re

from .chunker import SmartChunker
from .utils import Chunk

__all__ = ["SmartChunker", "Chunk"]


def _determine_version() -> str:
    """Return the package version.

    This first tries to obtain the installed package version via
    ``importlib.metadata``. If the package is not installed (for example when
    running from a source checkout), it falls back to reading the version from
    ``pyproject.toml``. If that also fails, ``"0.0.0"`` is returned.
    """

    try:  # Preferred path: package is installed
        return importlib_metadata.version("smartchunk")
    except importlib_metadata.PackageNotFoundError:
        pass

    try:  # Fallback: read pyproject.toml directly
        pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
        match = re.search(
            r'^version\s*=\s*"([^"\']+)"',
            pyproject.read_text(),
            re.MULTILINE,
        )
        if match:
            return match.group(1)
    except Exception:
        pass

    return "0.0.0"


__version__ = _determine_version()

  

