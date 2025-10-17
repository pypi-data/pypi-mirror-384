"""
This module contains logging schemas
"""

import logging
from typing import Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class BaseLoggingSchema(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class FormatterSchema(BaseLoggingSchema):
    """Schema for logging formatters"""

    fmt: Optional[str] = Field(None, description="Format string for log messages")
    datefmt: Optional[str] = Field(None, description="Date format string")
    use_colors: Optional[bool] = Field(None, description="Whether to use colors in output")
    class_: Optional[str] = Field(None, alias="()", description="Custom formatter class")


class HandlerSchema(BaseLoggingSchema):
    """Schema for logging handlers"""

    class_: str = Field(..., alias="class", description="Handler class name")
    level: Optional[str] = Field(None, description="Logging level for this handler")
    formatter: Optional[str] = Field(None, description="Formatter to use")
    stream: Optional[str] = Field(None, description="Stream for StreamHandler")
    filename: Optional[str] = Field(None, description="Filename for FileHandler")
    mode: Optional[str] = Field(None, description="File mode for FileHandler")
    encoding: Optional[str] = Field(None, description="Encoding for FileHandler")


class LoggerSchema(BaseLoggingSchema):
    """Schema for individual logger configuration"""

    level: Optional[str] = Field(None, description="Logging level")
    handlers: Optional[list[str]] = Field(None, description="List of handler names")
    propagate: Optional[bool] = Field(None, description="Whether to propagate to parent loggers")


class RootLoggerSchema(BaseLoggingSchema):
    """Schema for root logger configuration"""

    level: Optional[str] = Field(None, description="Root logging level")
    handlers: Optional[list[str]] = Field(None, description="List of handler names for root logger")
    propagate: Optional[bool] = Field(None, description="Whether to propagate")


class LoggingSchema(BaseLoggingSchema):
    """Schema for Python logging configuration dictionary"""

    version: Literal[1] = Field(1, description="Logging config schema version (must be 1)")
    disable_existing_loggers: Optional[bool] = Field(False, description="Whether to disable existing loggers")
    logging_project_name: Optional[str] = Field(None, description="Project name for logging")
    formatters: Optional[Dict[str, FormatterSchema]] = Field(
        None, description="Logging formatters configuration"
    )
    handlers: Optional[Dict[str, HandlerSchema]] = Field(None, description="Logging handlers configuration")
    loggers: Optional[Dict[str, LoggerSchema]] = Field(None, description="Logger configurations by name")
    root: Optional[RootLoggerSchema] = Field(None, description="Root logger configuration")


class LogRecord(logging.LogRecord):
    """Extended LogRecord with worker context fields"""

    worker_id: str | None
    correlation_id: str | None
    worker_context: str
