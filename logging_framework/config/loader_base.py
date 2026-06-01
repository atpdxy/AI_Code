"""Base config loader definitions."""

from __future__ import annotations

import abc
from typing import Any, Mapping


class BaseConfigLoader(abc.ABC):
    """Abstract base class for config loaders."""

    @abc.abstractmethod
    def load(self) -> Mapping[str, Any]:
        """Returns raw configuration mapping."""
