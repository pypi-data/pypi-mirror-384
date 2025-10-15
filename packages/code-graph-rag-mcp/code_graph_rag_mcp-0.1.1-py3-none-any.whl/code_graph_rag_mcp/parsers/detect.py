from __future__ import annotations

from pathlib import Path
from typing import Optional

EXT_TO_LANGUAGE = {
    ".ts": "typescript",
    ".tsx": "tsx",
    ".js": "javascript",
    ".jsx": "jsx",
    ".py": "python",
}


def language_for_path(path: Path) -> Optional[str]:
    suffix = path.suffix.lower()
    lang = EXT_TO_LANGUAGE.get(suffix)
    if lang == "tsx":
        return "typescript"
    if lang == "jsx":
        return "javascript"
    return lang


__all__ = ["language_for_path"]
