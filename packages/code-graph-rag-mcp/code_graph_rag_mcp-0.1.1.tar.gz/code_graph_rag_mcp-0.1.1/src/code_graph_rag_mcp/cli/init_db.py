from pathlib import Path

import typer

from code_graph_rag_mcp.config.loader import load_config
from code_graph_rag_mcp.db.bootstrap import bootstrap_database


def init_db_command(
    config_path: Path = typer.Option(
        Path("config.yaml"),
        "--config",
        "-c",
        help="Path to configuration file",
    )
) -> None:
    """Initialize the SQLite database and load required extensions."""
    config = load_config(config_path)
    bootstrap_database(config.database, config.embed)
    typer.echo(f"Database initialized at {config.database.sqlite_path}")
