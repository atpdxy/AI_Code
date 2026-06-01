"""Protocol contracts for framework extension points."""

from __future__ import annotations

from typing import Any, Mapping, Protocol


class ConfigLoader(Protocol):
    """Loads logging configuration from one source."""

    def load(self) -> Mapping[str, Any]:
        """Returns raw config dictionary."""


class RuntimeFilterFactory(Protocol):
    """Factory protocol that creates a logging filter."""

    def create(self) -> Any:
        """Returns a filter instance."""
