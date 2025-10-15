import typer

from code_graph_rag_mcp.cli.init_db import init_db_command
from code_graph_rag_mcp.cli.serve import serve_command

app = typer.Typer(help="Code GraphRAG MCP server utilities")

app.command()(init_db_command)
app.command(name="serve")(serve_command)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
