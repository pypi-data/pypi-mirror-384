from __future__ import annotations

from typing import Dict

from mcp import types

TOOL_SCHEMAS: Dict[str, types.Tool] = {
    "ingest_repo": types.Tool(
        name="ingest_repo",
        description="Ingest the entire repository, rebuilding the symbol graph and embeddings.",
        inputSchema={
            "type": "object",
            "properties": {
                "force": {
                    "type": "boolean",
                    "description": "Force reindex even if files appear unchanged.",
                    "default": True,
                }
            },
            "additionalProperties": False,
        },
        outputSchema={
            "type": "object",
            "properties": {
                "status": {"type": "object"},
            },
            "required": ["status"],
        },
    ),
    "refresh_path": types.Tool(
        name="refresh_path",
        description="Reindex a specific file path relative to the repository root.",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative file path to refresh",
                },
                "force": {
                    "type": "boolean",
                    "description": "Force reindex even if cached metadata matches",
                    "default": False,
                },
            },
            "required": ["path"],
            "additionalProperties": False,
        },
        outputSchema={
            "type": "object",
            "properties": {
                "status": {"type": "object"},
                "path": {"type": "string"},
            },
            "required": ["status", "path"],
        },
    ),
    "purge_path": types.Tool(
        name="purge_path",
        description="Remove a file and its graph artifacts from the database.",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative file path to purge",
                }
            },
            "required": ["path"],
            "additionalProperties": False,
        },
        outputSchema={
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "path": {"type": "string"},
            },
            "required": ["status", "path"],
        },
    ),
    "hybrid_search": types.Tool(
        name="hybrid_search",
        description="Perform hybrid semantic search over code chunks using vectors and graph metadata.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query string"},
                "k": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 100,
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        outputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "results": {"type": "array"},
                "model": {"type": "string"},
            },
            "required": ["query", "results", "model"],
        },
    ),
    "symbol_lookup": types.Tool(
        name="symbol_lookup",
        description="Lookup symbols by name substring.",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Symbol name fragment"},
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of matches",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 100,
                },
            },
            "required": ["name"],
            "additionalProperties": False,
        },
        outputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "matches": {"type": "array"},
            },
            "required": ["query", "matches"],
        },
    ),
    "explain_symbol": types.Tool(
        name="explain_symbol",
        description="Retrieve symbol metadata, owning chunk, and outgoing edges.",
        inputSchema={
            "type": "object",
            "properties": {
                "node_id": {
                    "type": "integer",
                    "description": "Database node id for the symbol",
                }
            },
            "required": ["node_id"],
            "additionalProperties": False,
        },
        outputSchema={
            "type": "object",
            "properties": {
                "symbol": {"type": "object"},
                "chunk": {"type": ["object", "null"]},
                "edges": {"type": "array"},
            },
            "required": ["symbol", "edges"],
        },
    ),
    "status": types.Tool(
        name="status",
        description="Report repository indexing status and extension readiness.",
        inputSchema={"type": "object", "properties": {}, "additionalProperties": False},
        outputSchema={
            "type": "object",
            "properties": {
                "project": {"type": "string"},
                "root": {"type": "string"},
                "counts": {"type": "object"},
                "supported_languages": {"type": "array"},
                "extensions": {"type": "object"},
            },
            "required": ["project", "counts"],
        },
    ),
}


def tool_list() -> list[types.Tool]:
    return list(TOOL_SCHEMAS.values())


__all__ = ["TOOL_SCHEMAS", "tool_list"]
