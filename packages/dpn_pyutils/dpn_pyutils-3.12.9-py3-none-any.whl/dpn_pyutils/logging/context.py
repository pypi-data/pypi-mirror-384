"""
Logging Context Management

Provides thread-safe and async-safe context propagation for logging metadata
using Python's contextvars. This allows worker ID and correlation ID to be
automatically available to all modules without passing logger parameters.

Usage:
    # In worker thread, set context once:
    set_logging_context(worker_id="DataReader-0", correlation_id="uuid-here")

    # In any module, get contextual logger:
    log = get_contextual_logger(__name__)
    log.debug("This will include worker and correlation info")

    # Clean up when done:
    clear_logging_context()
"""

import logging
from contextvars import ContextVar
from typing import Optional, Tuple

from dpn_pyutils.logging import get_logger


class ContextualLoggerAdapter(logging.LoggerAdapter):
    """
    LoggerAdapter that evaluates contextvars at log time, not at creation time.

    This allows module-level logger instantiation while still getting context
    when the actual logging methods are called.
    """

    def process(self, msg, kwargs):
        """Process the log record to inject context at log time."""
        # Get current context at log time
        worker_id, correlation_id = get_logging_context()

        # Add context to the extra dict
        extra = kwargs.get("extra", {})
        extra["worker_id"] = worker_id
        extra["correlation_id"] = correlation_id
        kwargs["extra"] = extra

        return msg, kwargs


# Context variables for worker metadata
# These are thread-safe and async-safe, automatically isolated per async task
_worker_id: ContextVar[Optional[str]] = ContextVar("worker_id", default=None)
_correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


def set_logging_context(worker_id: str, correlation_id: str) -> None:
    """
    Set the logging context for the current async task or thread.

    This should be called once at the start of task processing to establish
    the worker ID and correlation ID that will be used for all subsequent
    logging calls in this context.

    Args:
        worker_id: Worker identifier (e.g., "DataReader-0")
        correlation_id: Correlation ID (typically task ID UUID)

    Example:
        >>> set_logging_context("DataReader-0", "abc-123-def-456")
        >>> log = get_contextual_logger(__name__)
        >>> log.info("Processing")  # Will include [worker:DataReader-0][corr:abc-123-def-456]
    """
    _worker_id.set(worker_id)
    _correlation_id.set(correlation_id)


def clear_logging_context() -> None:
    """
    Clear the logging context for the current async task or thread.

    This should be called after task processing is complete to ensure
    context doesn't leak between tasks.

    Example:
        >>> clear_logging_context()
    """
    _worker_id.set(None)
    _correlation_id.set(None)


def get_logging_context() -> Tuple[Optional[str], Optional[str]]:
    """
    Get the current logging context.

    Returns:
        Tuple of (worker_id, correlation_id). Either or both may be None
        if context has not been set.

    Example:
        >>> worker_id, correlation_id = get_logging_context()
        >>> print(f"Worker: {worker_id}, Correlation: {correlation_id}")
    """
    return _worker_id.get(), _correlation_id.get()


def get_contextual_logger(module_name: str) -> ContextualLoggerAdapter:
    """
    Get a logger that automatically includes worker and correlation context.

    Returns a ContextualLoggerAdapter that evaluates contextvars at log time,
    allowing module-level instantiation while still getting context when
    logging methods are called.

    This is the primary function to use throughout your codebase. It allows
    any module to get a properly contextualized logger without needing to
    pass logger instances or context parameters.

    Args:
        module_name: The module name for the logger (typically __name__)

    Returns:
        ContextualLoggerAdapter that automatically injects context at log time

    Example:
        >>> # Can be called at module level:
        >>> log = get_contextual_logger(__name__)
        >>>
        >>> # Later, when context is set and logging is called:
        >>> set_logging_context("DataReader-0", "task-123")
        >>> log.debug("Processing")  # Includes [worker:DataReader-0][corr:task-123]

        >>> # In a module called by the worker:
        >>> log = get_contextual_logger(__name__)
        >>> log.debug("Reading file")  # Also includes [worker:DataReader-0][corr:task-123]
    """
    base_logger = get_logger(module_name)
    return ContextualLoggerAdapter(base_logger, {})


def has_logging_context() -> bool:
    """
    Check if logging context is currently set.

    Returns:
        True if both worker_id and correlation_id are set, False otherwise

    Example:
        >>> if has_logging_context():
        ...     print("Context is available")
    """
    worker_id, correlation_id = get_logging_context()
    return worker_id is not None or correlation_id is not None
