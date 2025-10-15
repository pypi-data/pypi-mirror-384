from __future__ import annotations

from pathlib import Path

import sys
from setuptools import setup
from setuptools.command.build_py import build_py as _build_py

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from code_graph_rag_mcp.build_extensions import BuildError, build_extensions


class build_py(_build_py):  # type: ignore[misc]
    """Custom build step to compile sqlite extensions into the wheel."""

    def run(self) -> None:  # type: ignore[override]
        super().run()
        self._build_sqlite_extensions()

    def _build_sqlite_extensions(self) -> None:
        build_lib = Path(self.build_lib)
        target_dir = build_lib / "code_graph_rag_mcp" / "native"
        target_dir.mkdir(parents=True, exist_ok=True)
        try:
            build_extensions(target_dir)
        except BuildError as exc:
            raise SystemExit(f"Failed to build sqlite extensions: {exc}")


setup(cmdclass={"build_py": build_py})
