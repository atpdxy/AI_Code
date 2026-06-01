"""Config loaders for YAML, JSON, and environment variables."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from logging_framework.config.loader_base import BaseConfigLoader


class JsonConfigLoader(BaseConfigLoader):
    """Loads config from JSON file."""

    def __init__(self, file_path: str) -> None:
        self._file_path = Path(file_path)

    def load(self) -> dict[str, Any]:
        if not self._file_path.exists():
            return {}
        return json.loads(self._file_path.read_text(encoding="utf-8"))


class YamlConfigLoader(BaseConfigLoader):
    """Loads config from YAML file."""

    def __init__(self, file_path: str) -> None:
        self._file_path = Path(file_path)

    def load(self) -> dict[str, Any]:
        if not self._file_path.exists():
            return {}
        try:
            import yaml  # type: ignore
        except ModuleNotFoundError as exc:
            raise RuntimeError("PyYAML is required for YamlConfigLoader.") from exc
        content = yaml.safe_load(self._file_path.read_text(encoding="utf-8"))
        return content or {}


class EnvConfigLoader(BaseConfigLoader):
    """Loads config from environment variables.

    Supports:
    - ``LOGGING_LEVEL``
    - ``LOGGING_FORMAT``
    - ``LOGGING_DATEFMT``
    - ``LOGGING_FILE``
    - ``LOGGING_MAX_BYTES``
    - ``LOGGING_BACKUP_COUNT``
    """

    def __init__(self, prefix: str = "LOGGING_") -> None:
        self._prefix = prefix

    def load(self) -> dict[str, Any]:
        env = os.environ
        level = env.get(f"{self._prefix}LEVEL")
        fmt = env.get(f"{self._prefix}FORMAT")
        datefmt = env.get(f"{self._prefix}DATEFMT")
        file_path = env.get(f"{self._prefix}FILE")
        max_bytes = env.get(f"{self._prefix}MAX_BYTES")
        backup_count = env.get(f"{self._prefix}BACKUP_COUNT")

        result: dict[str, Any] = {}
        if fmt or datefmt:
            result.setdefault("formatters", {}).setdefault("default", {})
            if fmt:
                result["formatters"]["default"]["fmt"] = fmt
            if datefmt:
                result["formatters"]["default"]["datefmt"] = datefmt
        if level:
            result.setdefault("default_logger", {})["level"] = level
        if file_path:
            result.setdefault("handlers", {})["file"] = {
                "kind": "rotating_file",
                "filename": file_path,
                "formatter": "default",
                "level": level or "INFO",
                "rotation": {
                    "max_bytes": int(max_bytes) if max_bytes else 50 * 1024 * 1024,
                    "backup_count": int(backup_count) if backup_count else 10,
                },
            }
            result.setdefault("default_logger", {})["handlers"] = ["file", "console"]
        return result
