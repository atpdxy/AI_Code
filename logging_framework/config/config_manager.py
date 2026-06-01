"""Configuration management and typed parsing."""

from __future__ import annotations

import copy
import threading
from typing import Any, Callable, Iterable

from logging_framework.config.loader_base import BaseConfigLoader
from logging_framework.config.models import (
    FilterConfig,
    FormatterConfig,
    FrameworkConfig,
    HandlerConfig,
    LoggerConfig,
    RotationConfig,
    default_framework_config,
)

ConfigSubscriber = Callable[[FrameworkConfig], None]


def _deep_merge(base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    """Recursively merges ``update`` into ``base``."""
    merged = copy.deepcopy(base)
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def _parse_rotation(raw: dict[str, Any] | None) -> RotationConfig:
    raw = raw or {}
    return RotationConfig(
        max_bytes=int(raw.get("max_bytes", 50 * 1024 * 1024)),
        backup_count=int(raw.get("backup_count", 10)),
        when=str(raw.get("when", "D")),
        interval=int(raw.get("interval", 1)),
        utc=bool(raw.get("utc", False)),
    )


def _parse_formatter(raw: dict[str, Any]) -> FormatterConfig:
    return FormatterConfig(
        fmt=str(raw.get("fmt", FormatterConfig().fmt)),
        datefmt=str(raw.get("datefmt", FormatterConfig().datefmt)),
        style=str(raw.get("style", "%")),
    )


def _parse_filter(raw: dict[str, Any]) -> FilterConfig:
    kind = str(raw.get("kind", "keyword_deny"))
    options = raw.get("options", {})
    if not isinstance(options, dict):
        raise ValueError("Filter options must be a dictionary.")
    return FilterConfig(kind=kind, options=options)


def _parse_handler(raw: dict[str, Any]) -> HandlerConfig:
    return HandlerConfig(
        kind=str(raw.get("kind", "console")),
        level=str(raw.get("level", "INFO")),
        formatter=str(raw.get("formatter", "default")),
        filename=str(raw.get("filename", "logs/app.log")),
        stream=str(raw.get("stream", "stdout")),
        encoding=str(raw.get("encoding", "utf-8")),
        rotation=_parse_rotation(raw.get("rotation")),
        filters=tuple(raw.get("filters", ())),
    )


def _parse_logger(raw: dict[str, Any]) -> LoggerConfig:
    return LoggerConfig(
        level=str(raw.get("level", "INFO")),
        handlers=tuple(raw.get("handlers", ("console",))),
        filters=tuple(raw.get("filters", ())),
        propagate=bool(raw.get("propagate", False)),
        async_mode=bool(raw.get("async_mode", False)),
        queue_size=int(raw.get("queue_size", 10000)),
    )


def parse_framework_config(raw: dict[str, Any]) -> FrameworkConfig:
    """Converts raw dictionary to typed framework config."""
    defaults = default_framework_config()

    formatters_raw = raw.get("formatters", {})
    handlers_raw = raw.get("handlers", {})
    filters_raw = raw.get("filters", {})
    loggers_raw = raw.get("loggers", {})

    formatters = {
        "default": defaults.formatters["default"],
        **{name: _parse_formatter(item) for name, item in formatters_raw.items()},
    }
    filters = {name: _parse_filter(item) for name, item in filters_raw.items()}
    handlers = {
        "console": defaults.handlers["console"],
        **{name: _parse_handler(item) for name, item in handlers_raw.items()},
    }
    loggers = {name: _parse_logger(item) for name, item in loggers_raw.items()}

    root = _parse_logger(raw.get("root", {}))
    default_logger = _parse_logger(raw.get("default_logger", {}))

    return FrameworkConfig(
        formatters=formatters,
        filters=filters,
        handlers=handlers,
        root=root,
        default_logger=default_logger,
        loggers=loggers,
    )


class ConfigManager:
    """Loads and stores framework config with subscribe/reload support."""

    def __init__(self, loaders: Iterable[BaseConfigLoader] | None = None) -> None:
        self._loaders = tuple(loaders or ())
        self._lock = threading.RLock()
        self._subscribers: list[ConfigSubscriber] = []
        self._raw_config: dict[str, Any] = {}
        self._config = default_framework_config()
        self.reload()

    def subscribe(self, callback: ConfigSubscriber) -> None:
        with self._lock:
            self._subscribers.append(callback)

    def get_config(self) -> FrameworkConfig:
        with self._lock:
            return self._config

    def get(self, path: str, default: Any = None) -> Any:
        """Returns a raw configuration value by dotted path.

        The logging framework keeps a typed ``FrameworkConfig`` for runtime
        logger behavior, while application modules may also need custom
        sections such as ``kb.embedding_model``. This method exposes those raw
        values without forcing every domain config into logging models.
        """
        with self._lock:
            current: Any = self._raw_config
            for part in path.split("."):
                if not isinstance(current, dict) or part not in current:
                    return default
                current = current[part]
            return copy.deepcopy(current)

    def get_section(self, section: str) -> dict[str, Any]:
        """Returns a copy of a raw top-level configuration section."""
        value = self.get(section, {})
        return value if isinstance(value, dict) else {}

    def reload(self) -> FrameworkConfig:
        with self._lock:
            merged: dict[str, Any] = {}
            for loader in self._loaders:
                loaded = dict(loader.load())
                merged = _deep_merge(merged, loaded)
            self._raw_config = copy.deepcopy(merged)
            self._config = parse_framework_config(merged)
            for callback in self._subscribers:
                callback(self._config)
            return self._config
