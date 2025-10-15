from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
from typing import Iterable, Optional

from code_graph_rag_mcp.chunker import ChunkBuilder
from code_graph_rag_mcp.config.models import ChunkConfig, EmbedConfig, ParserConfig
from code_graph_rag_mcp.db import DatabaseManager
from code_graph_rag_mcp.db import operations
from code_graph_rag_mcp.embedding import EmbeddingClient
from code_graph_rag_mcp.models.graph import ParseResult
from code_graph_rag_mcp.parsers import ParserContext, registry
from code_graph_rag_mcp.parsers.detect import language_for_path
from code_graph_rag_mcp.parsers.python import PythonAdapter
from code_graph_rag_mcp.parsers.typescript import TypeScriptAdapter

LOGGER = logging.getLogger(__name__)

SUPPORTED_ENCODINGS = ("utf-8", "utf-16", "latin-1")


class Indexer:
    def __init__(
        self,
        root: Path,
        db_manager: DatabaseManager,
        parser_config: Optional[ParserConfig] = None,
        chunk_config: Optional[ChunkConfig] = None,
        embed_config: Optional[EmbedConfig] = None,
    ) -> None:
        self.root = root
        self.db_manager = db_manager
        self.parser_config = parser_config or ParserConfig()
        self.chunk_builder = ChunkBuilder(chunk_config or ChunkConfig())
        self.embed_client = EmbeddingClient(embed_config)
        self._configure_adapters()

    def _configure_adapters(self) -> None:
        registry.register(TypeScriptAdapter("typescript", self.chunk_builder))
        registry.register(TypeScriptAdapter("javascript", self.chunk_builder))
        registry.register(PythonAdapter(self.chunk_builder))

    def ingest_repository(self, force: bool = False) -> None:
        paths = self._collect_paths()
        for path in paths:
            try:
                self.ingest_path(path, force=force)
            except Exception as exc:  # pragma: no cover - ingestion failure logged
                LOGGER.exception("Failed to ingest %s: %s", path, exc)

    def ingest_path(self, relative_path: Path, force: bool = False) -> None:
        absolute_path = relative_path if relative_path.is_absolute() else self.root / relative_path
        if not absolute_path.exists():
            LOGGER.info("Path %s missing; marking deleted", relative_path)
            with self.db_manager.connection() as connection:
                operations.mark_file_deleted(connection, relative_path)
            return

        language = language_for_path(relative_path)
        if language is None:
            LOGGER.debug("Skipping unsupported file %s", relative_path)
            return

        adapter = registry.get(language)
        if adapter is None:
            LOGGER.warning("No parser configured for language %s", language)
            return

        content = self._read_file(absolute_path)
        if content is None:
            LOGGER.warning("Unable to read file %s", absolute_path)
            return

        mtime_ms = int(absolute_path.stat().st_mtime_ns / 1_000_000)
        content_hash = hashlib.sha256(content.encode("utf-8", errors="ignore")).hexdigest()

        with self.db_manager.connection() as connection:
            file_id, changed = operations.upsert_file(
                connection,
                relative_path,
                language,
                mtime_ms,
                content_hash,
                metadata={"size": len(content), "abs_path": str(absolute_path)},
            )
            if not changed and not force:
                LOGGER.debug("Skipping unchanged file %s", relative_path)
                return

            operations.clear_file_artifacts(connection, file_id)

            context = ParserContext(root_path=self.root, file_path=absolute_path, content=content)
            parse_result = adapter.parse(context)

            node_mapping = operations.insert_symbols(connection, file_id, parse_result.symbols)
            operations.insert_relations(connection, node_mapping, parse_result.relations)
            chunk_ids, chunk_texts = operations.insert_chunks(connection, file_id, node_mapping, parse_result.chunks)

        if not chunk_ids:
            return

        embeddings = self.embed_client.embed(chunk_texts)
        with self.db_manager.connection() as connection:
            operations.insert_chunk_vectors(connection, chunk_ids, embeddings.vectors)

    def _collect_paths(self) -> Iterable[Path]:
        for path in self.root.rglob("*"):
            if path.is_file():
                relative = path.relative_to(self.root)
                if language_for_path(relative):
                    yield relative

    def _read_file(self, path: Path) -> Optional[str]:
        for encoding in SUPPORTED_ENCODINGS:
            try:
                return path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue
            except OSError:
                return None
        return None


__all__ = ["Indexer"]
