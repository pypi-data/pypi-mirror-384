from __future__ import annotations

import asyncio
import logging
from collections import deque
from typing import Deque, Optional

from code_graph_rag_mcp.watcher.jobs import JobKind, WatcherJob

LOGGER = logging.getLogger(__name__)


class JobQueue:
    """Async queue with basic coalescing for watcher jobs."""

    def __init__(self, maxsize: int = 0) -> None:
        self._queue: asyncio.Queue[WatcherJob] = asyncio.Queue(maxsize=maxsize)
        self._recent: Deque[str] = deque(maxlen=256)

    async def put(self, job: WatcherJob) -> None:
        if self._should_skip(job):
            LOGGER.debug("Skipping duplicate job %s", job)
            return
        await self._queue.put(job)
        self._record(job)

    async def get(self) -> WatcherJob:
        return await self._queue.get()

    def task_done(self) -> None:
        self._queue.task_done()

    def _should_skip(self, job: WatcherJob) -> bool:
        key = self._key(job)
        return key in self._recent

    def _record(self, job: WatcherJob) -> None:
        key = self._key(job)
        if key:
            self._recent.append(key)

    @staticmethod
    def _key(job: WatcherJob) -> str:
        path = str(job.path) if job.path else "*"
        return f"{job.kind}:{path}"

    async def shutdown(self) -> None:
        await self._queue.put(WatcherJob(kind=JobKind.SHUTDOWN))


__all__ = ["JobQueue"]
