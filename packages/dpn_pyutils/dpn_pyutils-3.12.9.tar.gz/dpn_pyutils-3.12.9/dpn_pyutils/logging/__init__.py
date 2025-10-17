#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

if sys.version_info < (3, 12):
    raise SystemError("dpn_pyutils requires Python version >= 3.12")

from dpn_pyutils.logging.formatters import AppLogFormatter
from dpn_pyutils.logging.handlers import TimedFileHandler
from dpn_pyutils.logging.init import (
    PyUtilsLogger,
    initialize_logging,
    initialize_logging_safe,
    is_logging_initialized,
)
from dpn_pyutils.logging.logger import get_logger, get_logger_fqn, get_worker_logger
from dpn_pyutils.logging.state import (
    get_project_name,
    is_initialized,
    reset_state,
)
from dpn_pyutils.logging.context import (
    ContextualLoggerAdapter,
    clear_logging_context,
    get_contextual_logger,
    get_logging_context,
    has_logging_context,
    set_logging_context,
)

__all__ = [
    # Main classes
    "PyUtilsLogger",
    # Logger retrieval
    "get_logger_fqn",
    "get_logger",
    "get_worker_logger",
    # Initialization and state
    "initialize_logging",
    "initialize_logging_safe",
    "is_logging_initialized",
    "get_project_name",
    "is_initialized",
    "reset_state",
    # Handlers
    "TimedFileHandler",
    # Formatters
    "AppLogFormatter",
    # Context management
    "set_logging_context",
    "clear_logging_context",
    "get_logging_context",
    "has_logging_context",
    "get_contextual_logger",
    "ContextualLoggerAdapter",
]
