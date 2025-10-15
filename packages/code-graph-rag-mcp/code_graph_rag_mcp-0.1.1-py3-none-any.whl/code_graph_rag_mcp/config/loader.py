from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import yaml

from code_graph_rag_mcp.config.models import DEFAULT_CONFIG, ServerConfig

ENV_CONFIG_PATH = "CODE_GRAPH_RAG_CONFIG"
ENV_OVERRIDES: Dict[str, str] = {
    "watch.dir": "CODE_GRAPH_RAG_WATCH_DIR",
    "watch.debounce_ms": "CODE_GRAPH_RAG_WATCH_DEBOUNCE_MS",
    "database.sqlite_path": "CODE_GRAPH_RAG_DB_PATH",
    "database.extensions_dir": "CODE_GRAPH_RAG_EXTENSIONS_DIR",
    "database.sqlite_vec_lib": "CODE_GRAPH_RAG_SQLITE_VEC",
    "database.bfsvtab_lib": "CODE_GRAPH_RAG_BFSVTAB",
    "embed.endpoint": "CODE_GRAPH_RAG_EMBED_ENDPOINT",
    "embed.model": "CODE_GRAPH_RAG_EMBED_MODEL",
    "embed.dim": "CODE_GRAPH_RAG_EMBED_DIM",
    "embed.quantize": "CODE_GRAPH_RAG_EMBED_QUANTIZE",
    "retrieval.k": "CODE_GRAPH_RAG_RETRIEVAL_K",
    "retrieval.hops": "CODE_GRAPH_RAG_RETRIEVAL_HOPS",
}


def _apply_env_overrides(data: Dict[str, Any]) -> None:
    for path, env in ENV_OVERRIDES.items():
        value = os.environ.get(env)
        if value is None:
            continue

        cursor = data
        keys = path.split(".")
        for key in keys[:-1]:
            cursor = cursor.setdefault(key, {})

        leaf = keys[-1]
        if leaf in {"dim", "quantize", "k", "hops", "debounce_ms"}:
            try:
                cursor[leaf] = int(value)
                continue
            except ValueError:
                pass

        cursor[leaf] = value


def load_config(config_path: Path | None = None) -> ServerConfig:
    env_config = os.environ.get(ENV_CONFIG_PATH)
    path = Path(env_config).expanduser() if env_config else Path(config_path or "config.yaml").expanduser()

    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            loaded: Any = yaml.safe_load(handle) or {}
            config_data: Dict[str, Any] = dict(loaded)
    else:
        config_data = {}

    _apply_env_overrides(config_data)

    return ServerConfig.model_validate(config_data) if config_data else DEFAULT_CONFIG
