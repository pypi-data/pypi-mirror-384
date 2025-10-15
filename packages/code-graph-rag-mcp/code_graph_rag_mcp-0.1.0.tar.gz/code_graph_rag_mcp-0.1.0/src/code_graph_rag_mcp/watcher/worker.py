from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional

from code_graph_rag_mcp.db import operations
from code_graph_rag_mcp.service import ServiceContext
from code_graph_rag_mcp.watcher.jobs import JobKind, WatcherJob
from code_graph_rag_mcp.watcher.queue import JobQueue

LOGGER = logging.getLogger(__name__)


class WatcherWorker:
    """Consume watcher jobs and invoke the indexer/DB operations."""

    def __init__(self, queue: JobQueue, context: ServiceContext) -> None:
        self.queue = queue
        self.context = context
        self._task: Optional[asyncio.Task[None]] = None
        self._stop_requested = False

    async def start(self) -> None:
        if self._task is not None and not self._task.done():
            raise RuntimeError("Watcher worker already running")
        self._stop_requested = False
        loop = asyncio.get_running_loop()
        self._task = loop.create_task(self._run())

    async def stop(self) -> None:
        if self._task is None:
            return
        if not self._stop_requested:
            await self.queue.shutdown()
            self._stop_requested = True
        try:
            await self._task
        finally:
            self._task = None

    async def _run(self) -> None:
        while True:
            job = await self.queue.get()
            try:
                if job.kind is JobKind.SHUTDOWN:
                    LOGGER.debug("Watcher worker received shutdown signal")
                    break
                await self._process_job(job)
            except Exception:  # pragma: no cover - logging unexpected failures
                LOGGER.exception("Failed processing watcher job %s", job)
            finally:
                self.queue.task_done()

    async def _process_job(self, job: WatcherJob) -> None:
        if job.kind is JobKind.INGEST_REPO:
            LOGGER.info("Watcher worker running full ingest")
            self.context.indexer.ingest_repository(force=True)
            return

        if job.path is None:
            LOGGER.debug("Watcher job %s missing path; skipping", job)
            return

        relative = Path(job.path)
        if job.kind is JobKind.REINDEX_PATH:
            LOGGER.info("Watcher reindexing %s", relative)
            self.context.indexer.ingest_path(relative, force=True)
        elif job.kind is JobKind.PURGE_PATH:
            LOGGER.info("Watcher purging %s", relative)
            with self.context.db.connection() as connection:
                row = connection.execute(
                    "SELECT id FROM files WHERE path = ?", (str(relative),)
                ).fetchone()
                if not row:
                    return
                operations.clear_file_artifacts(connection, row[0])
                connection.execute("DELETE FROM files WHERE id = ?", (row[0],))
        else:
            LOGGER.debug("Unhandled watcher job kind %s", job.kind)


__all__ = ["WatcherWorker"]
