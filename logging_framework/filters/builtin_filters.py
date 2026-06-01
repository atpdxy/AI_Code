"""Built-in filter implementations."""

from __future__ import annotations

import logging
import re
from typing import Iterable

from logging_framework.filters.base_filter import BaseLogFilter


class LevelFilter(BaseLogFilter):
    """Allows records with level greater than or equal to threshold."""

    def __init__(self, min_level: int) -> None:
        super().__init__()
        self._min_level = min_level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno >= self._min_level


class KeywordDenyFilter(BaseLogFilter):
    """Drops records containing any forbidden keyword."""

    def __init__(self, keywords: Iterable[str]) -> None:
        super().__init__()
        self._keywords = tuple(keyword for keyword in keywords if keyword)

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        return not any(keyword in message for keyword in self._keywords)


class RegexMaskingFilter(BaseLogFilter):
    """Masks sensitive substrings in-place using regular expressions."""

    def __init__(self, patterns: Iterable[str], replacement: str = "***") -> None:
        super().__init__()
        self._compiled_patterns = tuple(re.compile(item) for item in patterns)
        self._replacement = replacement

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for pattern in self._compiled_patterns:
            message = pattern.sub(self._replacement, message)
        record.msg = message
        record.args = ()
        return True
