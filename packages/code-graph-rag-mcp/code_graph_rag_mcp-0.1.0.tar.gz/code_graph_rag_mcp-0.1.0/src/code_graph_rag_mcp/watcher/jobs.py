from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional


class JobKind(str, Enum):
    INGEST_REPO = "ingest_repo"
    REINDEX_PATH = "reindex_path"
    PURGE_PATH = "purge_path"
    SHUTDOWN = "shutdown"


@dataclass(slots=True, frozen=True)
class WatcherJob:
    kind: JobKind
    path: Optional[Path] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def with_metadata(self, **kwargs: Any) -> "WatcherJob":
        data = {**self.metadata, **kwargs}
        return WatcherJob(kind=self.kind, path=self.path, metadata=data)


__all__ = ["JobKind", "WatcherJob"]
