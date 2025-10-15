from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict

import anyio
from mcp import stdio_server
from mcp.server import NotificationOptions, Server
from mcp.types import ListToolsResult

from code_graph_rag_mcp.config.loader import load_config
from code_graph_rag_mcp.config.models import ServerConfig
from code_graph_rag_mcp.db import DatabaseManager, bootstrap_database
from code_graph_rag_mcp.handlers import (
    explain_symbol,
    hybrid_search,
    ingest_repo,
    purge_path,
    refresh_path,
    status,
    symbol_lookup,
)
from code_graph_rag_mcp.indexer import Indexer
from code_graph_rag_mcp.service import ServiceContext
from code_graph_rag_mcp.tools import tool_list
from code_graph_rag_mcp.watcher import JobKind, JobQueue, RepoWatcher, WatcherJob, WatcherWorker

LOGGER = logging.getLogger(__name__)


class CodeGraphRAGServer:
    """MCP server wiring for the Code GraphRAG pipeline."""

    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path
        self.config: ServerConfig = load_config(config_path)
        bootstrap_database(self.config.database, self.config.embed)

        root = self.config.watch.dir.expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        db_manager = DatabaseManager(self.config.database, self.config.embed)
        indexer = Indexer(root, db_manager, self.config.parser, self.config.chunk, self.config.embed)
        self.context = ServiceContext(
            config=self.config,
            root=root,
            db=db_manager,
            indexer=indexer,
        )

        self._job_queue: JobQueue | None = None
        self._watcher: RepoWatcher | None = None
        self._worker: WatcherWorker | None = None

        self.server = Server(
            name=self.config.project,
            instructions="Local-first code graph + embeddings server",
            lifespan=self._lifespan,
        )

        self._tool_handlers: Dict[str, Callable[[ServiceContext, Dict[str, Any]], Awaitable[Dict[str, Any]]]] = {
            "ingest_repo": self._handle_ingest_repo,
            "refresh_path": self._handle_refresh_path,
            "purge_path": self._handle_purge_path,
            "hybrid_search": self._handle_hybrid_search,
            "symbol_lookup": self._handle_symbol_lookup,
            "explain_symbol": self._handle_explain_symbol,
            "status": self._handle_status,
        }

        self._register_handlers()

    @asynccontextmanager
    async def _lifespan(self, _server: Server):
        LOGGER.info("Starting CodeGraphRAG server lifespan")

        queue = JobQueue()
        watcher = RepoWatcher(self.context.root, queue, self.config.watch)
        worker = WatcherWorker(queue, self.context)

        self._job_queue = queue
        self._watcher = watcher
        self._worker = worker

        watcher_started = False

        await worker.start()
        await queue.put(WatcherJob(kind=JobKind.INGEST_REPO))

        try:
            await watcher.start()
            watcher_started = True
        except FileNotFoundError:
            LOGGER.warning("Watch path %s missing; file watcher disabled", self.context.root)

        try:
            yield self.context
        finally:
            LOGGER.info("Shutting down CodeGraphRAG server lifespan")
            if watcher_started:
                await watcher.stop()
            else:
                await queue.shutdown()
            await worker.stop()
            self._job_queue = None
            self._watcher = None
            self._worker = None

    def _register_handlers(self) -> None:
        @self.server.list_tools()
        async def _list_tools(_request=None) -> ListToolsResult:
            tools = tool_list()
            return ListToolsResult(tools=tools)

        @self.server.call_tool()
        async def _call_tool(tool_name: str, arguments: Dict[str, Any]):
            request_context = self.server.request_context
            service: ServiceContext = request_context.lifespan_context
            handler = self._tool_handlers.get(tool_name)
            if handler is None:
                raise ValueError(f"Unknown tool {tool_name}")
            return await handler(service, arguments)

    async def run_stdio_async(self) -> None:
        notification_options = NotificationOptions(tools_changed=False)
        init_options = self.server.create_initialization_options(notification_options)
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream, init_options)

    def run(self, transport: str = "stdio") -> None:
        transport = transport or "stdio"
        if transport != "stdio":
            raise ValueError(f"Unsupported transport '{transport}'. Only 'stdio' is implemented.")
        anyio.run(self.run_stdio_async)

    async def _handle_ingest_repo(self, ctx: ServiceContext, arguments: Dict[str, Any]):
        force = bool(arguments.get("force", True))
        return await ingest_repo(ctx, force=force)

    async def _handle_refresh_path(self, ctx: ServiceContext, arguments: Dict[str, Any]):
        path = arguments.get("path")
        if not path:
            raise ValueError("Missing 'path' argument")
        force = bool(arguments.get("force", False))
        result = await refresh_path(ctx, path, force=force)
        return result

    async def _handle_purge_path(self, ctx: ServiceContext, arguments: Dict[str, Any]):
        path = arguments.get("path")
        if not path:
            raise ValueError("Missing 'path' argument")
        return await purge_path(ctx, path)

    async def _handle_hybrid_search(self, ctx: ServiceContext, arguments: Dict[str, Any]):
        query = arguments.get("query")
        if not query:
            raise ValueError("Missing 'query' argument")
        k = int(arguments.get("k", 10))
        return await hybrid_search(ctx, query, k=k)

    async def _handle_symbol_lookup(self, ctx: ServiceContext, arguments: Dict[str, Any]):
        name = arguments.get("name")
        if not name:
            raise ValueError("Missing 'name' argument")
        limit = int(arguments.get("limit", 20))
        return await symbol_lookup(ctx, name, limit=limit)

    async def _handle_explain_symbol(self, ctx: ServiceContext, arguments: Dict[str, Any]):
        node_id = arguments.get("node_id")
        if node_id is None:
            raise ValueError("Missing 'node_id' argument")
        return await explain_symbol(ctx, int(node_id))

    async def _handle_status(self, ctx: ServiceContext, _arguments: Dict[str, Any]):
        return await status(ctx)


def create_server(config_path: Path | None = None) -> CodeGraphRAGServer:
    return CodeGraphRAGServer(config_path=config_path)


__all__ = ["CodeGraphRAGServer", "create_server"]
