"""Logger wrapper that encapsulates runtime logger operations."""

from __future__ import annotations

import logging
from typing import Iterable


class LoggerWrapper:
    """Thin wrapper around ``logging.Logger`` with stable management API."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    @property
    def name(self) -> str:
        return self._logger.name

    @property
    def raw(self) -> logging.Logger:
        return self._logger

    def set_level(self, level: int | str) -> None:
        self._logger.setLevel(level)

    def set_formatter(self, formatter: logging.Formatter) -> None:
        """Applies one formatter to all attached handlers."""
        for handler in self._logger.handlers:
            handler.setFormatter(formatter)

    def add_handler(self, handler: logging.Handler) -> None:
        self._logger.addHandler(handler)

    def remove_handler(self, handler_name: str) -> None:
        """Removes handler by matching ``handler.name``."""
        for handler in list(self._logger.handlers):
            if handler.name == handler_name:
                self._logger.removeHandler(handler)
                handler.close()

    def replace_handlers(self, handlers: Iterable[logging.Handler]) -> None:
        self.clear_handlers()
        for handler in handlers:
            self._logger.addHandler(handler)

    def clear_handlers(self) -> None:
        for handler in list(self._logger.handlers):
            self._logger.removeHandler(handler)
            handler.close()

    def add_filter(self, log_filter: logging.Filter) -> None:
        self._logger.addFilter(log_filter)

    def remove_filter(self, log_filter: logging.Filter) -> None:
        self._logger.removeFilter(log_filter)

    def log(self, level: int, message: str, *args: object, **kwargs: object) -> None:
        self._logger.log(level, message, *args, **kwargs)

    def debug(self, message: str, *args: object, **kwargs: object) -> None:
        self._logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args: object, **kwargs: object) -> None:
        self._logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args: object, **kwargs: object) -> None:
        self._logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args: object, **kwargs: object) -> None:
        self._logger.error(message, *args, **kwargs)

    def exception(self, message: str, *args: object, **kwargs: object) -> None:
        self._logger.exception(message, *args, **kwargs)

    def critical(self, message: str, *args: object, **kwargs: object) -> None:
        self._logger.critical(message, *args, **kwargs)
