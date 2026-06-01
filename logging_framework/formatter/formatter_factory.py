"""Factory helpers for creating log formatters."""

from __future__ import annotations

import logging

from logging_framework.config.models import FormatterConfig


def create_formatter(config: FormatterConfig) -> logging.Formatter:
    """Creates ``logging.Formatter`` from typed formatter config."""
    return logging.Formatter(fmt=config.fmt, datefmt=config.datefmt, style=config.style)
