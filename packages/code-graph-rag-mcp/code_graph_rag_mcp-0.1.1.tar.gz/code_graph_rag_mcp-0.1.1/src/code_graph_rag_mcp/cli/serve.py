from __future__ import annotations

from pathlib import Path

import typer

from code_graph_rag_mcp.server import CodeGraphRAGServer


def serve_command(
    config_path: Path = typer.Option(Path("config.yaml"), "--config", "-c", help="Path to configuration file"),
    transport: str = typer.Option("stdio", "--transport", "-t", help="Transport protocol (stdio)"),
) -> None:
    """Start the Code GraphRAG MCP server."""
    server = CodeGraphRAGServer(config_path=config_path)
    server.run(transport=transport)
