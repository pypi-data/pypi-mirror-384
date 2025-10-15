from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field


class WatcherConfig(BaseModel):
    dir: Path = Field(default_factory=lambda: Path.cwd())
    debounce_ms: int = 300
    include: List[str] = Field(default_factory=lambda: ["**/*.ts", "**/*.tsx", "**/*.js", "**/*.py"])
    exclude: List[str] = Field(default_factory=lambda: ["**/node_modules/**", "**/.git/**", "**/dist/**"])


class ParserConfig(BaseModel):
    languages: List[str] = Field(default_factory=lambda: ["ts", "py"])
    tree_sitter_bundles: Optional[Path] = None


class ChunkConfig(BaseModel):
    function_tokens: List[int] = Field(default_factory=lambda: [100, 500])
    class_tokens: List[int] = Field(default_factory=lambda: [500, 2000])
    file_chunk: bool = True


class EmbedConfig(BaseModel):
    model: str = "embedding-gemma-512"
    dim: int = 512
    quantize: int = 8
    endpoint: Optional[str] = Field(default=None, description="Override embeddings endpoint")


class RetrievalConfig(BaseModel):
    k: int = 40
    hops: int = 2
    rels: List[str] = Field(default_factory=lambda: ["defines", "calls", "imports", "belongs_to", "inherits"])
    weights: dict[str, float] = Field(default_factory=lambda: {"semantic": 0.7, "graph": 0.3})


class DatabaseConfig(BaseModel):
    sqlite_path: Path = Field(default=Path("data/code.sqlite"))
    extensions_dir: Optional[Path] = None
    sqlite_vec_lib: Optional[Path] = None
    bfsvtab_lib: Optional[Path] = None
    ensure_parent: bool = True

    @property
    def resolved_path(self) -> Path:
        return self.sqlite_path.expanduser().resolve()


class ServerConfig(BaseModel):
    project: str = "code-graphrag"
    watch: WatcherConfig = Field(default_factory=WatcherConfig)
    parser: ParserConfig = Field(default_factory=ParserConfig)
    chunk: ChunkConfig = Field(default_factory=ChunkConfig)
    embed: EmbedConfig = Field(default_factory=EmbedConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)

    @property
    def sqlite_path(self) -> Path:
        return self.database.resolved_path


DEFAULT_CONFIG = ServerConfig()
