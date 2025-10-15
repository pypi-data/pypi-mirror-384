from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Iterable, Optional

from code_graph_rag_mcp.config.models import DatabaseConfig

LOGGER = logging.getLogger(__name__)

EXTENSION_LOAD_ORDER: list[tuple[str, str]] = [
    ("sqlite_vec_lib", "sqlite3_vec_init"),
    ("bfsvtab_lib", "sqlite3_bfsvtab_init"),
]

DEFAULT_EXTENSION_FILENAMES: dict[str, tuple[str, ...]] = {
    "sqlite_vec_lib": ("sqlite-vec0", "sqlite-vec"),
    "bfsvtab_lib": ("bfsvtab",),
}

SHARED_LIBRARY_SUFFIXES: tuple[str, ...] = (
    ".so",
    ".dylib",
    ".dll",
)


def resolve_extension_path(config: DatabaseConfig, attr: str) -> Optional[Path]:
    explicit = getattr(config, attr)
    if explicit:
        path = Path(explicit).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"SQLite extension '{attr}' not found at {path}")
        return path

    if config.extensions_dir:
        directory = Path(config.extensions_dir).expanduser().resolve()
        if not directory.exists():
            raise FileNotFoundError(f"Extensions directory {directory} does not exist")
    else:
        directory = Path(__file__).resolve().parent.parent / "native"

    if not directory.exists():
        LOGGER.debug("Extensions directory %s missing", directory)
        return None

    for stem in DEFAULT_EXTENSION_FILENAMES.get(attr, ()): 
        candidate = _find_library(directory, stem)
        if candidate:
            return candidate

    LOGGER.debug("No candidate shared library found for %s in %s", attr, directory)
    return None


def resolve_extension_paths(config: DatabaseConfig) -> Dict[str, Path]:
    resolved: Dict[str, Path] = {}
    for attr, _ in EXTENSION_LOAD_ORDER:
        path = resolve_extension_path(config, attr)
        if path:
            resolved[attr] = path
    return resolved


def load_extensions(connection, config: DatabaseConfig, require: bool = True) -> None:
    from sqlite3 import Connection

    if not isinstance(connection, Connection):
        raise TypeError("connection must be sqlite3.Connection")

    paths = resolve_extension_paths(config)
    if not paths:
        raise RuntimeError(
            "SQLite vector/BFS extensions not found. Run 'python scripts/build_sqlite_extensions.py' "
            "or configure database.extensions_dir / explicit paths."
        )

    connection.enable_load_extension(True)
    try:
        for attr, entrypoint in EXTENSION_LOAD_ORDER:
            path = paths.get(attr)
            if not path:
                continue
            LOGGER.debug("Loading SQLite extension %s from %s", attr, path)
            try:
                connection.load_extension(str(path), entrypoint)
            except TypeError:
                connection.execute("SELECT load_extension(?, ?)", (str(path), entrypoint))
    finally:
        connection.enable_load_extension(False)


def _find_library(directory: Path, stem: str) -> Optional[Path]:
    for suffix in SHARED_LIBRARY_SUFFIXES:
        candidate = directory / f"{stem}{suffix}"
        if candidate.exists():
            return candidate
    return None
