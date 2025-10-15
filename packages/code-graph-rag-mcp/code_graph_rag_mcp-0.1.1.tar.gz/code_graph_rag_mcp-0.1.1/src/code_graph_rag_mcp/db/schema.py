from __future__ import annotations

from typing import Iterable, List

PRAGMA_STATEMENTS: List[str] = [
    "PRAGMA journal_mode=WAL;",
    "PRAGMA synchronous=NORMAL;",
    "PRAGMA foreign_keys=ON;",
    "PRAGMA busy_timeout=3000;",
]

READ_ONLY_PRAGMAS: List[str] = [
    "PRAGMA foreign_keys=ON;",
    "PRAGMA busy_timeout=3000;",
]

SCHEMA_STATEMENTS: List[str] = [
    """
    CREATE TABLE IF NOT EXISTS files (
      id INTEGER PRIMARY KEY,
      path TEXT UNIQUE,
      lang TEXT,
      mtime_ms INTEGER,
      content_hash TEXT,
      status TEXT DEFAULT 'active',
      meta JSON
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_files_path ON files(path);
    """,
    """
    CREATE TABLE IF NOT EXISTS nodes (
      id INTEGER PRIMARY KEY,
      type TEXT,
      name TEXT,
      file_id INTEGER REFERENCES files(id) ON DELETE CASCADE,
      span_start INTEGER,
      span_end INTEGER,
      meta JSON
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_nodes_type_name ON nodes(type, name);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_nodes_file ON nodes(file_id);
    """,
    """
    CREATE TABLE IF NOT EXISTS edges (
      src_id INTEGER REFERENCES nodes(id) ON DELETE CASCADE,
      dst_id INTEGER REFERENCES nodes(id) ON DELETE CASCADE,
      rel TEXT,
      meta JSON,
      PRIMARY KEY (src_id, dst_id, rel)
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_edges_src_rel ON edges(src_id, rel);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_edges_dst_rel ON edges(dst_id, rel);
    """,
    """
    CREATE TABLE IF NOT EXISTS chunks (
      id INTEGER PRIMARY KEY,
      node_id INTEGER REFERENCES nodes(id) ON DELETE CASCADE,
      file_id INTEGER REFERENCES files(id) ON DELETE CASCADE,
      content TEXT,
      meta JSON
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_chunks_node ON chunks(node_id);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_chunks_file ON chunks(file_id);
    """,
    """
    CREATE VIEW IF NOT EXISTS graph_edges AS
      SELECT src_id AS src, dst_id AS dst FROM edges;
    """,
]


def vector_virtual_tables(dim: int) -> List[str]:
    return [
        (
            "CREATE VIRTUAL TABLE IF NOT EXISTS chunk_vec USING vec0("\
            f"chunk_id INTEGER PRIMARY KEY, embedding float[{dim}]"\
            ");"
        ),
        (
            "CREATE VIRTUAL TABLE IF NOT EXISTS symbol_vec USING vec0("\
            f"node_id INTEGER PRIMARY KEY, embedding float[{dim}]"\
            ");"
        ),
    ]


def bfs_virtual_table() -> str:
    return (
        "CREATE VIRTUAL TABLE IF NOT EXISTS bfs USING bfsvtab("\
        "tablename='graph_edges', fromcolumn='src', tocolumn='dst'"\
        ");"
    )


def schema_summary(dim: int) -> str:
    statements: Iterable[str] = [
        *PRAGMA_STATEMENTS,
        *SCHEMA_STATEMENTS,
        *vector_virtual_tables(dim),
        bfs_virtual_table(),
    ]
    return "\n".join(stmt.strip() for stmt in statements)
