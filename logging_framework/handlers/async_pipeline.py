"""Asynchronous logging pipeline based on queue listener."""

from __future__ import annotations

import logging
import logging.handlers
import queue
from typing import Iterable


class AsyncLogPipeline:
    """Owns queue handler and queue listener for async logging."""

    def __init__(self, handlers: Iterable[logging.Handler], queue_size: int) -> None:
        self._target_handlers = tuple(handlers)
        self._queue: queue.Queue[logging.LogRecord] = queue.Queue(maxsize=queue_size)
        self._queue_handler = logging.handlers.QueueHandler(self._queue)
        self._listener = logging.handlers.QueueListener(
            self._queue, *self._target_handlers, respect_handler_level=True
        )
        self._started = False

    @property
    def queue_handler(self) -> logging.handlers.QueueHandler:
        return self._queue_handler

    def start(self) -> None:
        if not self._started:
            self._listener.start()
            self._started = True

    def stop(self) -> None:
        if self._started:
            self._listener.stop()
            self._started = False
        for handler in self._target_handlers:
            handler.close()
