from __future__ import annotations

import asyncio
import fnmatch
import logging
from pathlib import Path
from typing import Iterable, Optional, Sequence

from watchfiles import Change, awatch

from code_graph_rag_mcp.config.models import WatcherConfig
from code_graph_rag_mcp.watcher.jobs import JobKind, WatcherJob
from code_graph_rag_mcp.watcher.queue import JobQueue

LOGGER = logging.getLogger(__name__)


class DebouncedEmitter:
    """Per-path debounce helper to avoid redundant indexing bursts."""

    def __init__(self, delay_ms: int) -> None:
        self._delay = delay_ms / 1000.0
        self._tasks: dict[Path, asyncio.Task[None]] = {}
        self._lock = asyncio.Lock()

    async def schedule(self, path: Path, coro_factory) -> None:
        async with self._lock:
            task = self._tasks.get(path)
            if task and not task.done():
                task.cancel()
            self._tasks[path] = asyncio.create_task(self._runner(path, coro_factory))

    async def _runner(self, path: Path, coro_factory) -> None:
        try:
            await asyncio.sleep(self._delay)
            await coro_factory()
        except asyncio.CancelledError:  # pragma: no cover - cancellation propagation
            raise
        finally:
            async with self._lock:
                self._tasks.pop(path, None)

    async def cancel_all(self) -> None:
        async with self._lock:
            tasks = list(self._tasks.values())
            self._tasks.clear()
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


class RepoWatcher:
    """Watch a repository path and enqueue indexing jobs."""

    def __init__(self, root: Path, queue: JobQueue, config: WatcherConfig) -> None:
        self.root = root
        self.queue = queue
        self.config = config
        self._stop_event = asyncio.Event()
        self._task: Optional[asyncio.Task[None]] = None
        self._debouncer = DebouncedEmitter(config.debounce_ms)

    async def start(self) -> None:
        if self._task is not None:
            raise RuntimeError("Watcher already started")
        self._task = asyncio.create_task(self._run())
        LOGGER.info("Started watcher for %s", self.root)

    async def stop(self) -> None:
        self._stop_event.set()
        await self._debouncer.cancel_all()
        if self._task:
            await self._task
        await self.queue.shutdown()
        LOGGER.info("Stopped watcher for %s", self.root)

    async def _run(self) -> None:
        async for changes in awatch(self.root, recursive=True, stop_event=self._stop_event):
            for change, path in changes:
                path_obj = Path(path)
                if not self._should_consider(path_obj):
                    continue
                await self._handle_change(change, path_obj)
            if self._stop_event.is_set():
                break

    async def _handle_change(self, change: Change, path: Path) -> None:
        relative = self._relative_path(path)
        if change in (Change.modified, Change.added):
            job = WatcherJob(kind=JobKind.REINDEX_PATH, path=relative)
        elif change == Change.deleted:
            job = WatcherJob(kind=JobKind.PURGE_PATH, path=relative)
        else:
            LOGGER.debug("Unhandled change %s for %s", change, path)
            return
        await self._debouncer.schedule(relative, lambda: self.queue.put(job))

    def _relative_path(self, path: Path) -> Path:
        try:
            return path.relative_to(self.root)
        except ValueError:
            return path

    def _should_consider(self, path: Path) -> bool:
        relative = str(self._relative_path(path))
        if self.config.exclude and _matches_any(relative, self.config.exclude):
            return False
        if self.config.include:
            return _matches_any(relative, self.config.include)
        return True


def _matches_any(path: str, patterns: Sequence[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


__all__ = ["RepoWatcher", "DebouncedEmitter"]
