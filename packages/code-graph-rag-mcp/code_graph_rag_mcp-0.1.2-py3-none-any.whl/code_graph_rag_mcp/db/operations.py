from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, Optional, Sequence, Tuple

import sqlite3

from code_graph_rag_mcp.models.graph import Chunk, Relation, Symbol

JsonType = Optional[str]


def upsert_file(
    connection: sqlite3.Connection,
    path: Path,
    lang: str,
    mtime_ms: int,
    content_hash: str,
    metadata: Optional[dict] = None,
) -> Tuple[int, bool]:
    cursor = connection.execute(
        "SELECT id, content_hash FROM files WHERE path = ?",
        (str(path),),
    )
    row = cursor.fetchone()
    meta_json = json.dumps(metadata or {})
    if row:
        file_id, existing_hash = row
        changed = existing_hash != content_hash
        connection.execute(
            "UPDATE files SET lang = ?, mtime_ms = ?, content_hash = ?, status = 'active', meta = ? WHERE id = ?",
            (lang, mtime_ms, content_hash, meta_json, file_id),
        )
        return file_id, changed

    connection.execute(
        "INSERT INTO files(path, lang, mtime_ms, content_hash, status, meta) VALUES (?, ?, ?, ?, 'active', ?)",
        (str(path), lang, mtime_ms, content_hash, meta_json),
    )
    file_id = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    return int(file_id), True


def mark_file_deleted(connection: sqlite3.Connection, path: Path) -> None:
    connection.execute(
        "UPDATE files SET status = 'deleted' WHERE path = ?",
        (str(path),),
    )


def clear_file_artifacts(connection: sqlite3.Connection, file_id: int) -> None:
    chunk_ids = [row[0] for row in connection.execute("SELECT id FROM chunks WHERE file_id = ?", (file_id,))]
    if chunk_ids:
        placeholders = ",".join(["?"] * len(chunk_ids))
        connection.execute(
            f"DELETE FROM chunk_vec WHERE chunk_id IN ({placeholders})",
            chunk_ids,
        )
    connection.execute("DELETE FROM chunks WHERE file_id = ?", (file_id,))
    connection.execute("DELETE FROM nodes WHERE file_id = ?", (file_id,))


def insert_symbols(
    connection: sqlite3.Connection,
    file_id: int,
    symbols: Iterable[Symbol],
) -> Dict[str, int]:
    mapping: Dict[str, int] = {}
    for symbol in symbols:
        meta_json = json.dumps(symbol.metadata)
        cursor = connection.execute(
            "INSERT INTO nodes(type, name, file_id, span_start, span_end, meta) VALUES (?, ?, ?, ?, ?, ?)",
            (
                symbol.kind.value,
                symbol.name,
                file_id,
                symbol.span_start,
                symbol.span_end,
                meta_json,
            ),
        )
        node_id = int(cursor.lastrowid)
        mapping[symbol.metadata["id"]] = node_id
    return mapping


def insert_relations(
    connection: sqlite3.Connection,
    node_mapping: Dict[str, int],
    relations: Iterable[Relation],
) -> None:
    for relation in relations:
        src = node_mapping.get(relation.source)
        dst = node_mapping.get(relation.target)
        if src is None or dst is None:
            continue
        meta_json = json.dumps(relation.metadata)
        connection.execute(
            "INSERT OR REPLACE INTO edges(src_id, dst_id, rel, meta) VALUES (?, ?, ?, ?)",
            (src, dst, relation.kind.value, meta_json),
        )


def insert_chunks(
    connection: sqlite3.Connection,
    file_id: int,
    node_mapping: Dict[str, int],
    chunks: Iterable[Chunk],
) -> Tuple[Sequence[int], Sequence[str]]:
    chunk_ids = []
    contents = []
    for chunk in chunks:
        node_id = node_mapping.get(chunk.symbol_id)
        if node_id is None:
            continue
        meta_json = json.dumps(chunk.metadata)
        cursor = connection.execute(
            "INSERT INTO chunks(node_id, file_id, content, meta) VALUES (?, ?, ?, ?)",
            (
                node_id,
                file_id,
                chunk.content,
                meta_json,
            ),
        )
        chunk_ids.append(int(cursor.lastrowid))
        contents.append(chunk.content)
    return chunk_ids, contents


def insert_chunk_vectors(
    connection: sqlite3.Connection,
    chunk_ids: Sequence[int],
    vectors,
) -> None:
    for chunk_id, vector in zip(chunk_ids, vectors):
        blob = memoryview(vector.astype("float32").tobytes())
        connection.execute(
            "INSERT OR REPLACE INTO chunk_vec(chunk_id, embedding) VALUES (?, ?)",
            (chunk_id, blob),
        )
