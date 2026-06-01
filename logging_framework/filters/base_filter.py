"""Base logging filter definition."""

from __future__ import annotations

import abc
import logging


class BaseLogFilter(logging.Filter, metaclass=abc.ABCMeta):
    """Base class for custom framework filters."""

    @abc.abstractmethod
    def filter(self, record: logging.LogRecord) -> bool:
        """Returns ``True`` when log record is allowed."""
