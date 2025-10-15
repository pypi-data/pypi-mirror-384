# Code GraphRAG MCP Server

This module implements the local-first Code GraphRAG MCP server described in `../docs/code-graph-rag-mcp.md`. The spec covers the full architecture: repository watcher, Tree-sitter based symbol extraction, AST-aligned chunking, EmbeddingGemma integration, SQLite (`sqlite-vec`, `bfsvtab`) storage, and MCP tools for ingest/search/status.

## Next Steps
- Port the spec content into actionable tasks (schema, watcher, parsers, retrieval).
- Initialize the codebase structure (`src/`, `tests/`, configuration) following the deliverables checklist.

Refer back to the spec for detailed requirements and pseudo-code snippets.

## SQLite Extensions
- Wheels built from this project bundle sqlite-vec and bfsvtab automatically; no manual steps are required after `pip install`.
- To rebuild native libraries locally (for development or alternative platforms), run `python scripts/build_sqlite_extensions.py`.
- Override inputs via `--sqlite-vec-src` / `--bfsvtab-src`, and customize discovery with `DATABASE.extensions_dir` in the config.

## Quick Start
- Run directly with `uvx` (recommended for MCP manifests):
  ```bash
  uvx code-graph-rag-mcp serve --config /path/to/config.yaml
  ```
  The published wheel bundles `sqlite-vec` and `bfsvtab`, so no manual build step is required.
- To override the repo or database locations via environment variables, add them in the MCP manifest `env` block (see “Environment Overrides”).
- A minimal `config.yaml` might look like:
  ```yaml
  watch:
    dir: "/workspace/repo"
  database:
    sqlite_path: "/workspace/data/code.sqlite"
  ```

## Development
- Create and activate a virtualenv: `python -m venv .venv && source .venv/bin/activate`.
- Install dependencies: `pip install -e .[dev]`.
- Rebuild native extensions (if you need local copies): `python scripts/build_sqlite_extensions.py`.
- Initialize the database: `code-graph-rag-mcp init-db --config config.yaml` (optional).
- Launch the server over stdio: `code-graph-rag-mcp serve`.

## Testing
- Run the pytest suite (includes building extensions in a temp dir): `pytest`.

## Runtime Features
- File watcher + job queue keeps the database in sync with repo changes.
- Hybrid search returns BFS neighbor context using configurable hop depth.
## Environment Overrides
- `CODE_GRAPH_RAG_CONFIG`: optional path to override the default `config.yaml`.
- `CODE_GRAPH_RAG_WATCH_DIR`, `CODE_GRAPH_RAG_DB_PATH`, `CODE_GRAPH_RAG_EXTENSIONS_DIR`, etc., adjust watcher and database settings at runtime.
- `CODE_GRAPH_RAG_SQLITE_VEC` / `CODE_GRAPH_RAG_BFSVTAB` can point to custom extension locations if you don’t want to use the bundled binaries.
- Embedding overrides: `CODE_GRAPH_RAG_EMBED_MODEL`, `CODE_GRAPH_RAG_EMBED_ENDPOINT`, `CODE_GRAPH_RAG_EMBED_DIM`, `CODE_GRAPH_RAG_EMBED_QUANTIZE`.
- Retrieval overrides: `CODE_GRAPH_RAG_RETRIEVAL_K`, `CODE_GRAPH_RAG_RETRIEVAL_HOPS`.

The MCP manifest’s `env` block is the recommended place to set these.
