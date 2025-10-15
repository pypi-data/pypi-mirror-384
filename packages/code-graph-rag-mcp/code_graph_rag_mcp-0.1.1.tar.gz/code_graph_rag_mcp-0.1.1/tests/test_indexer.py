from __future__ import annotations

from pathlib import Path

import pytest

from code_graph_rag_mcp.config.models import ChunkConfig, DatabaseConfig, EmbedConfig, ParserConfig, ServerConfig, WatcherConfig
from code_graph_rag_mcp.db import DatabaseManager, bootstrap_database
from code_graph_rag_mcp.handlers.search import hybrid_search, symbol_lookup
from code_graph_rag_mcp.indexer import Indexer
from code_graph_rag_mcp.service import ServiceContext


def _create_context(repo: Path, db_path: Path, extensions_dir: Path) -> ServiceContext:
    db_config = DatabaseConfig(sqlite_path=db_path, extensions_dir=extensions_dir)
    embed_config = EmbedConfig()
    bootstrap_database(db_config, embed_config)
    manager = DatabaseManager(db_config, embed_config)
    indexer = Indexer(repo, manager, ParserConfig(), ChunkConfig(), embed_config)
    config = ServerConfig(
        watch=WatcherConfig(dir=repo),
        database=db_config,
        embed=embed_config,
        parser=ParserConfig(),
        chunk=ChunkConfig(),
    )
    return ServiceContext(config=config, root=repo, db=manager, indexer=indexer)


def test_ingest_repository_creates_records(tmp_path: Path, sample_repo: Path, extensions_dir: Path) -> None:
    db_path = tmp_path / "code.sqlite"
    context = _create_context(sample_repo, db_path, extensions_dir)

    context.indexer.ingest_repository(force=True)

    with context.db.connection(read_only=True) as connection:
        file_count = connection.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        chunk_count = connection.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        vector_count = connection.execute("SELECT COUNT(*) FROM chunk_vec").fetchone()[0]

    assert file_count == 2
    assert chunk_count > 0
    assert vector_count == chunk_count


@pytest.mark.asyncio
async def test_hybrid_search_and_symbol_lookup(tmp_path: Path, sample_repo: Path, extensions_dir: Path) -> None:
    db_path = tmp_path / "code.sqlite"
    context = _create_context(sample_repo, db_path, extensions_dir)
    context.indexer.ingest_repository(force=True)

    search = await hybrid_search(context, "increment", k=5)
    assert search["results"], "Expected at least one hybrid search result"
    assert search["results"][0]["neighbors"], "Expected neighbor expansion from BFS"

    lookup = await symbol_lookup(context, "Greeter", limit=5)
    assert any(item["name"].startswith("Greeter") for item in lookup["matches"]), "Symbol lookup missing Greeter"
