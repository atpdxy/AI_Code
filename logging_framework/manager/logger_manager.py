"""Logger manager responsible for logger lifecycle and registry."""

from __future__ import annotations

import logging
import threading

from logging_framework.config.config_manager import ConfigManager
from logging_framework.config.models import FrameworkConfig, LoggerConfig
from logging_framework.core.logger_wrapper import LoggerWrapper
from logging_framework.handlers.async_pipeline import AsyncLogPipeline
from logging_framework.handlers.handler_factory import HandlerFactory, create_runtime_filter

_ROOT_LOGGER_NAME = "logging_framework.root"


class LoggerManager:
    """Creates and manages named loggers in a thread-safe registry."""

    def __init__(self, config_manager: ConfigManager | None = None) -> None:
        self._lock = threading.RLock()
        self._config_manager = config_manager or ConfigManager()
        self._config = self._config_manager.get_config()
        self._handler_factory = HandlerFactory(self._config.formatters, self._config.filters)
        self._loggers: dict[str, LoggerWrapper] = {}
        self._async_pipelines: dict[str, AsyncLogPipeline] = {}
        self._root_logger = self._create_root_logger()
        self._config_manager.subscribe(self._on_config_update)

    def get_logger(self, name: str) -> LoggerWrapper:
        """Returns existing logger by name, or creates a new one."""
        wrapper = self._loggers.get(name)
        if wrapper is not None:
            return wrapper
        with self._lock:
            wrapper = self._loggers.get(name)
            if wrapper is not None:
                return wrapper
            created = self._build_logger(name)
            self._loggers[name] = created
            self._root_logger.info("logger_created name=%s", name)
            return created

    def get_root_logger(self) -> LoggerWrapper:
        return self._root_logger

    def remove_logger(self, name: str) -> None:
        with self._lock:
            wrapper = self._loggers.pop(name, None)
            if wrapper is None:
                return
            self._stop_pipeline(name)
            wrapper.clear_handlers()
            self._root_logger.info("logger_removed name=%s", name)

    def list_logger_names(self) -> list[str]:
        with self._lock:
            return sorted(self._loggers.keys())

    def shutdown(self) -> None:
        """Stops pipelines and closes all managed handlers."""
        with self._lock:
            for name in list(self._async_pipelines.keys()):
                self._stop_pipeline(name)
            for wrapper in self._loggers.values():
                wrapper.clear_handlers()
            self._root_logger.clear_handlers()

    def _on_config_update(self, config: FrameworkConfig) -> None:
        with self._lock:
            self._config = config
            self._handler_factory = HandlerFactory(config.formatters, config.filters)
            self._apply_logger_config(self._root_logger, config.root, _ROOT_LOGGER_NAME)
            for name, wrapper in self._loggers.items():
                logger_config = config.loggers.get(name, config.default_logger)
                self._apply_logger_config(wrapper, logger_config, name)
            self._root_logger.info("manager_reconfigured")

    def _create_root_logger(self) -> LoggerWrapper:
        raw = logging.getLogger(_ROOT_LOGGER_NAME)
        wrapper = LoggerWrapper(raw)
        self._apply_logger_config(wrapper, self._config.root, _ROOT_LOGGER_NAME)
        return wrapper

    def _build_logger(self, name: str) -> LoggerWrapper:
        raw = logging.getLogger(name)
        wrapper = LoggerWrapper(raw)
        logger_config = self._config.loggers.get(name, self._config.default_logger)
        self._apply_logger_config(wrapper, logger_config, name)
        return wrapper

    def _apply_logger_config(
        self, wrapper: LoggerWrapper, logger_config: LoggerConfig, logger_name: str
    ) -> None:
        self._stop_pipeline(logger_name)
        wrapper.clear_handlers()
        self._clear_logger_filters(wrapper)

        wrapper.set_level(logger_config.level.upper())
        wrapper.raw.propagate = logger_config.propagate

        handlers = []
        for handler_name in logger_config.handlers:
            handler_config = self._config.handlers.get(handler_name)
            if handler_config is None:
                raise ValueError(f"Handler '{handler_name}' was not found in configuration.")
            handlers.append(self._handler_factory.create_handler(handler_name, handler_config))

        if logger_config.async_mode and handlers:
            pipeline = AsyncLogPipeline(handlers=handlers, queue_size=logger_config.queue_size)
            pipeline.start()
            wrapper.add_handler(pipeline.queue_handler)
            self._async_pipelines[logger_name] = pipeline
        else:
            wrapper.replace_handlers(handlers)

        for filter_name in logger_config.filters:
            filter_config = self._config.filters.get(filter_name)
            if filter_config is None:
                raise ValueError(f"Filter '{filter_name}' was not found in configuration.")
            wrapper.add_filter(create_runtime_filter(filter_config))

    def _stop_pipeline(self, logger_name: str) -> None:
        pipeline = self._async_pipelines.pop(logger_name, None)
        if pipeline is not None:
            pipeline.stop()

    @staticmethod
    def _clear_logger_filters(wrapper: LoggerWrapper) -> None:
        for item in list(wrapper.raw.filters):
            wrapper.remove_filter(item)
