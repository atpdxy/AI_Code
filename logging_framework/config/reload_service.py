"""Background config reload polling service."""

from __future__ import annotations

import threading
import time

from logging_framework.config.config_manager import ConfigManager


class ConfigReloadService:
    """Periodically invokes ``ConfigManager.reload`` in background thread."""

    def __init__(self, config_manager: ConfigManager, interval_seconds: float = 5.0) -> None:
        self._config_manager = config_manager
        self._interval = interval_seconds
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="ConfigReloadService")
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            self._config_manager.reload()
            time.sleep(self._interval)
