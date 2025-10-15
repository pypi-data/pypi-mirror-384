from __future__ import annotations

import sqlite3
from typing import Dict, Iterable, List, Optional


def fetch_status(connection: sqlite3.Connection) -> Dict[str, int]:
    def count(table: str) -> int:
        return connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    return {
        "files": count("files"),
        "nodes": count("nodes"),
        "edges": count("edges"),
        "chunks": count("chunks"),
    }


def fetch_neighbors(
    connection: sqlite3.Connection,
    root_id: int,
    max_distance: int,
    allowed_relations: Optional[Iterable[str]] = None,
) -> List[Dict[str, object]]:
    if max_distance <= 0:
        return []

    rels = tuple(allowed_relations) if allowed_relations else None

    rows = connection.execute(
        """
        SELECT b.id, b.parent, b.distance, n.name, n.type, f.path, e.rel
        FROM bfs b
        JOIN nodes n ON n.id = b.id
        JOIN files f ON f.id = n.file_id
        LEFT JOIN edges e ON e.src_id = b.parent AND e.dst_id = b.id
        WHERE b.root = ? AND b.distance BETWEEN 1 AND ?
        ORDER BY b.distance, n.name
        """,
        (root_id, max_distance),
    ).fetchall()

    neighbors: List[Dict[str, object]] = []
    for dst_id, parent_id, distance, name, type_, file_path, relation in rows:
        if rels and relation and relation not in rels:
            continue
        neighbors.append(
            {
                "id": dst_id,
                "parent_id": parent_id,
                "distance": int(distance),
                "relation": relation,
                "name": name,
                "type": type_,
                "file": file_path,
            }
        )
    return neighbors


__all__ = ["fetch_status", "fetch_neighbors"]
