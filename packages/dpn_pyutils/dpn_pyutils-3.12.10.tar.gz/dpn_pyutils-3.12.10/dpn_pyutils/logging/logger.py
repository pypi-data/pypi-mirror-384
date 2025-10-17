import logging
from typing import Any, Dict, Union

from dpn_pyutils.logging.init import PyUtilsLogger
from dpn_pyutils.logging.state import get_project_name


def get_logger(module_name: str) -> PyUtilsLogger:
    """
    Gets a namespaced logger based on the project name and module name
    """

    project_name = get_project_name()
    if "" == project_name:
        return get_logger_fqn(module_name)

    full_name = "{}.{}".format(project_name, module_name)

    return get_logger_fqn(full_name)


def get_logger_fqn(module_name: str) -> PyUtilsLogger:
    """
    Gets a namespaced logger based on the fully-qualified name supplied
    """

    if logging.getLoggerClass() != PyUtilsLogger:
        # Auto-initialize with basic configuration if not already initialized
        from dpn_pyutils.logging.init import initialize_logging_safe

        basic_config: Dict[str, Any] = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "basic": {
                    "()": "logging.Formatter",
                    "fmt": "%(levelname)-8s %(asctime)s %(name)s %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                }
            },
            "handlers": {
                "console": {
                    "level": "INFO",
                    "formatter": "basic",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                }
            },
            "root": {"level": "INFO", "handlers": ["console"]},
        }
        initialize_logging_safe(basic_config)

    return logging.getLogger(module_name)  # type: ignore


def get_worker_logger(
    module_name: str, worker_id: Union[int, str, None], correlation_id: Union[str, None]
) -> logging.LoggerAdapter:
    """
    Gets a worker logger with automatic worker_id and correlation_id context.

    Uses Python's LoggerAdapter pattern to inject worker context into all log calls.
    The worker_id and correlation_id will automatically appear in log messages
    when using a formatter that supports these fields.

    Args:
        module_name: The module name for the logger
        worker_id: Worker identifier (int or str)
        correlation_id: Correlation ID (typically a UUID string)

    Returns:
        LoggerAdapter that automatically includes worker context in all log calls

    Example:
        >>> log = get_worker_logger("my_module", 1, "abc-123")
        >>> log.debug("Processing task")  # Will include [worker:1][corr:abc-123] prefix
    """
    base_logger = get_logger(module_name)
    return logging.LoggerAdapter(base_logger, {"worker_id": worker_id, "correlation_id": correlation_id})
