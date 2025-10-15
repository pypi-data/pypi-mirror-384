from __future__ import annotations

import json
import sqlite3
from typing import Dict, List

import numpy as np

from code_graph_rag_mcp.db.queries import fetch_neighbors
from code_graph_rag_mcp.service import ServiceContext


def _vector_blob(vector: np.ndarray) -> bytes:
    return vector.astype(np.float32).tobytes()


async def hybrid_search(ctx: ServiceContext, query: str, k: int = 10) -> Dict[str, object]:
    embedding = ctx.indexer.embed_client.embed([query])
    blob = _vector_blob(embedding.vectors[0])

    with ctx.db.connection(read_only=True) as connection:
        rows = connection.execute(
            """
            SELECT c.id, c.node_id, c.content, c.meta, n.name, n.type, f.path,
                   vec_distance_l2(v.embedding, ?) AS score
            FROM chunk_vec v
            JOIN chunks c ON c.id = v.chunk_id
            JOIN nodes n ON n.id = c.node_id
            JOIN files f ON f.id = c.file_id
            ORDER BY score ASC
            LIMIT ?
            """,
            (sqlite3.Binary(blob), k),
        ).fetchall()

        hops = getattr(ctx.config.retrieval, "hops", 0)
        rels = getattr(ctx.config.retrieval, "rels", None)
        neighbor_map: Dict[int, List[Dict[str, object]]] = {}
        if hops and hops > 0:
            for _, node_id, *_ in rows:
                if node_id in neighbor_map:
                    continue
                neighbor_map[node_id] = fetch_neighbors(connection, node_id, hops, rels)

    results: List[Dict[str, object]] = []
    for chunk_id, node_id, content, meta_json, symbol_name, symbol_type, file_path, score in rows:
        metadata = json.loads(meta_json or "{}")
        results.append(
            {
                "chunk_id": chunk_id,
                "score": float(score),
                "content": content,
                "symbol": {
                    "name": symbol_name,
                    "type": symbol_type,
                    "file": file_path,
                },
                "metadata": metadata,
                "neighbors": neighbor_map.get(node_id, []),
            }
        )

    return {
        "query": query,
        "results": results,
        "model": embedding.model,
    }


async def symbol_lookup(ctx: ServiceContext, name: str, limit: int = 20) -> Dict[str, object]:
    pattern = f"%{name}%"
    with ctx.db.connection(read_only=True) as connection:
        rows = connection.execute(
            """
            SELECT n.id, n.name, n.type, n.meta, f.path
            FROM nodes n
            JOIN files f ON f.id = n.file_id
            WHERE n.name LIKE ?
            ORDER BY n.type, n.name
            LIMIT ?
            """,
            (pattern, limit),
        ).fetchall()

    items: List[Dict[str, object]] = []
    for node_id, symbol_name, symbol_type, meta_json, file_path in rows:
        metadata = json.loads(meta_json or "{}")
        items.append(
            {
                "id": node_id,
                "name": symbol_name,
                "type": symbol_type,
                "file": file_path,
                "metadata": metadata,
            }
        )
    return {"query": name, "matches": items}


async def explain_symbol(ctx: ServiceContext, node_id: int) -> Dict[str, object]:
    with ctx.db.connection(read_only=True) as connection:
        symbol = connection.execute(
            "SELECT n.id, n.name, n.type, n.meta, f.path, c.content, c.meta"
            " FROM nodes n"
            " LEFT JOIN chunks c ON c.node_id = n.id"
            " JOIN files f ON f.id = n.file_id"
            " WHERE n.id = ?",
            (node_id,),
        ).fetchone()
        if not symbol:
            return {"error": f"Symbol {node_id} not found"}

        edges = connection.execute(
            "SELECT rel, dst_id FROM edges WHERE src_id = ?",
            (node_id,),
        ).fetchall()

    symbol_meta = json.loads(symbol[3] or "{}")
    chunk_meta = json.loads(symbol[6] or "{}") if symbol[6] else {}

    return {
        "symbol": {
            "id": symbol[0],
            "name": symbol[1],
            "type": symbol[2],
            "file": symbol[4],
            "metadata": symbol_meta,
        },
        "chunk": {
            "content": symbol[5],
            "metadata": chunk_meta,
        },
        "edges": [
            {
                "relation": rel,
                "target_id": dst_id,
            }
            for rel, dst_id in edges
        ],
    }


__all__ = ["hybrid_search", "symbol_lookup", "explain_symbol"]
