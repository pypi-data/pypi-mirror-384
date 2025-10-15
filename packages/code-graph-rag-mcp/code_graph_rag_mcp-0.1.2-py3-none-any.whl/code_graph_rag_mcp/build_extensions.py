from __future__ import annotations

import os
import platform
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Tuple

SQLITE_VEC_VERSION = "0.1.6"
SQLITE_VEC_AMALGAMATION_URL = (
    "https://github.com/asg017/sqlite-vec/releases/download/"
    f"v{SQLITE_VEC_VERSION}/sqlite-vec-{SQLITE_VEC_VERSION}-amalgamation.zip"
)
BFSVTAB_URL = "https://raw.githubusercontent.com/abetlen/sqlite3-bfsvtab-ext/main/bfsvtab.c"


class BuildError(RuntimeError):
    pass


def _download(url: str, target: Path) -> Path:
    from urllib.request import urlretrieve

    target.parent.mkdir(parents=True, exist_ok=True)
    urlretrieve(url, target)
    return target


def _detect_output_name(stem: str) -> str:
    system = platform.system().lower()
    if system == "darwin":
        return f"{stem}.dylib"
    if system == "windows":
        return f"{stem}.dll"
    return f"{stem}.so"


def _build_shared(src: Path, output: Path) -> None:
    cc = os.environ.get("CC", "cc")
    system = platform.system().lower()
    if system == "darwin":
        flags = ["-O3", "-dynamiclib", "-undefined", "dynamic_lookup", "-fPIC"]
    elif system == "windows":
        flags = ["-O2", "-shared"]
    else:
        flags = ["-O3", "-shared", "-fPIC"]

    cmd = [cc, *flags, "-o", str(output), str(src)]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:  # pragma: no cover
        raise BuildError(f"Failed to compile {src.name} with command: {' '.join(cmd)}") from exc


def _ensure_sources(
    sqlite_vec_src: Optional[Path],
    bfs_src: Optional[Path],
) -> Tuple[Path, Path, tempfile.TemporaryDirectory[str] | None]:
    temp_dir: tempfile.TemporaryDirectory[str] | None = None

    if sqlite_vec_src and bfs_src:
        header = sqlite_vec_src.with_suffix(".h")
        if not header.exists():
            raise FileNotFoundError(f"sqlite-vec header not found at {header}")
        return sqlite_vec_src, bfs_src, None

    temp_dir = tempfile.TemporaryDirectory()
    temp_path = Path(temp_dir.name)

    if sqlite_vec_src:
        vec_path = sqlite_vec_src
    else:
        archive_path = temp_path / "sqlite-vec.zip"
        _download(SQLITE_VEC_AMALGAMATION_URL, archive_path)
        with zipfile.ZipFile(archive_path) as zf:
            zf.extractall(temp_path)
        vec_path = temp_path / "sqlite-vec.c"
        header_path = temp_path / "sqlite-vec.h"
        if not header_path.exists():
            raise FileNotFoundError("sqlite-vec amalgamation missing header")

    bfs_path = bfs_src or _download(BFSVTAB_URL, temp_path / "bfsvtab.c")
    return vec_path, bfs_path, temp_dir


def build_extensions(
    output_dir: Path,
    sqlite_vec_src: Optional[Path] = None,
    bfs_src: Optional[Path] = None,
) -> Tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    vec_src, bfs_src, tmp_dir = _ensure_sources(sqlite_vec_src, bfs_src)

    try:
        vec_out = output_dir / _detect_output_name("sqlite-vec0")
        bfs_out = output_dir / _detect_output_name("bfsvtab")

        _build_shared(vec_src, vec_out)
        _build_shared(bfs_src, bfs_out)
    finally:
        if tmp_dir:
            tmp_dir.cleanup()

    return vec_out, bfs_out


__all__ = ["build_extensions", "BuildError"]
