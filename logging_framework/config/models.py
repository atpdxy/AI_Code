"""Typed configuration models for logging framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

DEFAULT_FORMAT = (
    "[%(asctime)s][%(levelname)s][%(name)s][%(threadName)s]"
    "[%(filename)s][%(funcName)s][line:%(lineno)d] %(message)s"
)
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


@dataclass(frozen=True)
class FormatterConfig:
    """Formatter settings."""

    fmt: str = DEFAULT_FORMAT
    datefmt: str = DEFAULT_DATE_FORMAT
    style: str = "%"


@dataclass(frozen=True)
class RotationConfig:
    """Rotation settings for rotating file handlers."""

    max_bytes: int = 50 * 1024 * 1024
    backup_count: int = 10
    when: str = "D"
    interval: int = 1
    utc: bool = False


@dataclass(frozen=True)
class FilterConfig:
    """Filter definition."""

    kind: str
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class HandlerConfig:
    """Handler definition."""

    kind: str
    level: str = "INFO"
    formatter: str = "default"
    filename: str = "logs/app.log"
    stream: str = "stdout"
    encoding: str = "utf-8"
    rotation: RotationConfig = field(default_factory=RotationConfig)
    filters: tuple[str, ...] = ()


@dataclass(frozen=True)
class LoggerConfig:
    """Logger definition."""

    level: str = "INFO"
    handlers: tuple[str, ...] = ("console",)
    filters: tuple[str, ...] = ()
    propagate: bool = False
    async_mode: bool = False
    queue_size: int = 10000


@dataclass(frozen=True)
class FrameworkConfig:
    """Root configuration object."""

    formatters: dict[str, FormatterConfig]
    filters: dict[str, FilterConfig]
    handlers: dict[str, HandlerConfig]
    root: LoggerConfig
    default_logger: LoggerConfig
    loggers: dict[str, LoggerConfig]


def default_framework_config() -> FrameworkConfig:
    """Returns default framework config."""
    return FrameworkConfig(
        formatters={"default": FormatterConfig()},
        filters={},
        handlers={"console": HandlerConfig(kind="console")},
        root=LoggerConfig(level="INFO", handlers=("console",), propagate=False),
        default_logger=LoggerConfig(level="INFO", handlers=("console",), propagate=False),
        loggers={},
    )
