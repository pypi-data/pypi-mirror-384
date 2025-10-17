#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

if sys.version_info < (3, 12):
    raise SystemError("dpn_pyutils requires Python version >= 3.12")

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

__all__ = [
    "PyUtilsLogger",
    "get_logger_fqn",
    "get_logger",
    "get_worker_logger",
    "initialize_logging",
    "initialize_logging_safe",
    "is_logging_initialized",
    "get_project_name",
    "is_initialized",
    "reset_state",
]
