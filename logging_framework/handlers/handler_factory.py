"""Factory for creating logging handlers and filters."""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path

from logging_framework.config.models import FilterConfig, FormatterConfig, HandlerConfig
from logging_framework.filters.builtin_filters import (
    KeywordDenyFilter,
    LevelFilter,
    RegexMaskingFilter,
)
from logging_framework.formatter.formatter_factory import create_formatter


def create_runtime_filter(filter_config: FilterConfig) -> logging.Filter:
    """Creates built-in filter from config."""
    kind = filter_config.kind
    options = filter_config.options
    if kind == "level":
        return LevelFilter(int(options.get("min_level", logging.INFO)))
    if kind == "keyword_deny":
        return KeywordDenyFilter(tuple(options.get("keywords", ())))
    if kind == "regex_mask":
        return RegexMaskingFilter(
            tuple(options.get("patterns", ())),
            replacement=str(options.get("replacement", "***")),
        )
    raise ValueError(f"Unsupported filter type: {kind}")


class HandlerFactory:
    """Builds handler instances from typed config."""

    def __init__(self, formatters: dict[str, FormatterConfig], filters: dict[str, FilterConfig]) -> None:
        self._formatters = formatters
        self._filters = filters

    def create_handler(self, handler_name: str, config: HandlerConfig) -> logging.Handler:
        handler = self._build_handler(config)
        handler.name = handler_name
        handler.setLevel(config.level.upper())

        formatter_config = self._formatters.get(config.formatter, self._formatters["default"])
        handler.setFormatter(create_formatter(formatter_config))

        for filter_name in config.filters:
            filter_config = self._filters.get(filter_name)
            if filter_config is None:
                continue
            handler.addFilter(create_runtime_filter(filter_config))

        return handler

    def _build_handler(self, config: HandlerConfig) -> logging.Handler:
        kind = config.kind
        if kind == "console":
            stream = sys.stderr if config.stream.lower() == "stderr" else sys.stdout
            return logging.StreamHandler(stream)
        if kind == "file":
            self._ensure_log_dir(config.filename)
            return logging.FileHandler(config.filename, encoding=config.encoding)
        if kind == "rotating_file":
            self._ensure_log_dir(config.filename)
            return RotatingFileHandler(
                config.filename,
                maxBytes=config.rotation.max_bytes,
                backupCount=config.rotation.backup_count,
                encoding=config.encoding,
            )
        if kind == "timed_rotating_file":
            self._ensure_log_dir(config.filename)
            return TimedRotatingFileHandler(
                config.filename,
                when=config.rotation.when,
                interval=config.rotation.interval,
                backupCount=config.rotation.backup_count,
                encoding=config.encoding,
                utc=config.rotation.utc,
            )
        raise ValueError(f"Unsupported handler type: {kind}")

    @staticmethod
    def _ensure_log_dir(filename: str) -> None:
        path = Path(filename)
        if path.parent:
            path.parent.mkdir(parents=True, exist_ok=True)
