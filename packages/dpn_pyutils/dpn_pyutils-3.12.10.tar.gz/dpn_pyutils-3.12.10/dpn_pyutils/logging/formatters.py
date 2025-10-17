import logging
from typing import Literal, Optional


class AppLogFormatter(logging.Formatter):
    """
    Custom logging formatter with color support and enhanced formatting.

    This formatter extends the standard logging.Formatter to provide colored console output
    and consistent log message formatting across the application. It automatically adds
    level prefixes and supports ANSI color codes for different log levels.

    The formatter includes the following information in each log message:
    - Level prefix (colored)
    - Timestamp with millisecond precision
    - Thread name for multi-threaded applications
    - Logger name for hierarchical logging identification
    - The actual log message

    Attributes:
        COLORS (dict): ANSI color codes for different log levels
        RESET_COLOR (str): ANSI code to reset color formatting
        use_colors (bool): Whether to apply color formatting to log output

    Example:
        >>> formatter = AppLogFormatter()
        >>> handler = logging.StreamHandler()
        >>> handler.setFormatter(formatter)
        >>> logger = logging.getLogger('my_app')
        >>> logger.addHandler(handler)
        >>> logger.info('This is an info message')  # Will be displayed in green
    """

    # ANSI color codes
    COLORS = {
        "DEBUG": "\x1b[36m",  # Cyan
        "INFO": "\x1b[32m",  # Green
        "WARNING": "\x1b[33m",  # Yellow
        "ERROR": "\x1b[31m",  # Red
        "CRITICAL": "\x1b[35m",  # Magenta
    }
    RESET_COLOR = "\x1b[0m"

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        style: Literal["%", "{", "$"] = "%",
        use_colors: bool = True,
        include_worker_context: bool = True,
    ) -> None:
        """
        Initialize the AppLogFormatter with custom formatting options.

        Args:
            fmt: Format string for log messages. If None, uses a default format that includes
                level prefix, timestamp with milliseconds, thread name, logger name, and message.
                The default format is: "%(levelprefix)-8s %(asctime)s.%(msecs)03d "
                "[%(threadName)s] %(name)s %(message)s"
            datefmt: Date format string for timestamps. If None, uses ISO format "%Y-%m-%d %H:%M:%S".
                Common alternatives include "%H:%M:%S" for time only or "%Y-%m-%d" for date only.
            style: Format style to use for the format string. Options are:
                - '%': Old-style formatting (default, e.g., %(levelname)s)
                - '{': New-style formatting (e.g., {levelname})
                - '$': Dollar-style formatting (e.g., $levelname)
            use_colors: Whether to enable ANSI color codes for log level prefixes in console output.
                When True, different log levels will be displayed in distinct colors:
                - DEBUG: Cyan
                - INFO: Green
                - WARNING: Yellow
                - ERROR: Red
                - CRITICAL: Magenta
            include_worker_context: Whether to include worker context in the log message.
                When True, the worker context will be included in the log message.
                The worker context is a string that is formatted as
                "[worker:<worker_id>][corr:<correlation_id>] <message>".
                The worker_id and correlation_id are typically provided by the worker context manager.

        Raises:
            ValueError: If an invalid style character is provided.

        Example:
            >>> formatter = AppLogFormatter(
            ...     fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            ...     datefmt="%H:%M:%S",
            ...     use_colors=True
            ... )
        """
        if fmt is None:
            if include_worker_context:
                fmt = (
                    "%(levelprefix)-8s "
                    "%(asctime)s.%(msecs)03d [%(threadName)s] %(worker_context)s %(name)s %(message)s"
                )
            else:
                fmt = "%(levelprefix)-8s %(asctime)s.%(msecs)03d [%(threadName)s] %(name)s %(message)s"

        if datefmt is None:
            datefmt = "%Y-%m-%d %H:%M:%S"

        super().__init__(fmt=fmt, datefmt=datefmt, style=style)
        self.use_colors = use_colors
        self.include_worker_context = include_worker_context

    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record with enhanced styling and color support.

        This method extends the parent format() method by adding a levelprefix attribute
        to the log record and applying ANSI color codes to the level prefix when colors
        are enabled. The coloring is applied only to the first line of multi-line messages.

        Args:
            record: The LogRecord instance to format. This object will be modified
                by adding a 'levelprefix' attribute containing the appropriate
                level name (DEBUG, INFO, WARNING, ERROR, or CRITICAL).

        Returns:
            str: The formatted log message with level prefix and optional color styling.
                The format follows the pattern specified during initialization.

        Note:
            The levelprefix attribute is dynamically determined based on the record's
            levelno value, ensuring consistent level name formatting across all log levels.

        Example:
            >>> import logging
            >>> formatter = AppLogFormatter(use_colors=True)
            >>> record = logging.LogRecord('test', logging.INFO, '', 0, 'Test message', (), None)
            >>> formatted = formatter.format(record)
            >>> print(formatted)  # INFO     2023-12-01 12:00:00,000 [MainThread] test Test message
        """
        record.levelprefix = self._get_level_prefix(record.levelno)

        # Always ensure worker_id and correlation_id attributes exist on the record
        # This prevents KeyError when format strings reference these attributes directly
        worker_id = getattr(record, "worker_id", None)
        correlation_id = getattr(record, "correlation_id", None)

        # Add worker context if available and enabled
        if self.include_worker_context:
            # Set the attributes on the record (empty string if None to avoid "None" in output)
            record.worker_id = worker_id if worker_id is not None else ""
            record.correlation_id = correlation_id if correlation_id is not None else ""

            context_output = []
            if worker_id is not None:
                context_output.append(f"[worker:{worker_id}]")

            if correlation_id is not None:
                context_output.append(f"[corr:{correlation_id}]")

            record.worker_context = "".join(context_output)
        else:
            # When worker context is disabled, clear these attributes to prevent them from appearing in output
            record.worker_id = ""
            record.correlation_id = ""
            record.worker_context = ""

        formatted_message = super().format(record)
        if self.use_colors and record.levelname in self.COLORS:
            color = self.COLORS[record.levelname]
            lines = formatted_message.splitlines()
            if lines:
                first_line = lines[0]
                level_prefix = getattr(record, "levelprefix", "")
                if first_line.startswith(level_prefix):
                    colored_prefix = f"{color}{level_prefix}{self.RESET_COLOR}"
                    lines[0] = first_line.replace(level_prefix, colored_prefix, 1)
                formatted_message = "\n".join(lines)
        return formatted_message

    def _get_level_prefix(self, levelno: int) -> str:
        """
        Convert a numeric log level to its corresponding string prefix.

        This method maps Python's numeric logging levels to their standard string
        representations used in log formatting. The mapping follows Python's logging
        module conventions and ensures consistent level name formatting.

        Args:
            levelno: The numeric log level as defined in the logging module.
                Common values include:
                - logging.TRACE (5)
                - logging.DEBUG (10)
                - logging.INFO (20)
                - logging.WARNING (30)
                - logging.ERROR (40)
                - logging.CRITICAL (50)

        Returns:
            str: The string representation of the log level. One of:
                'TRACE', 'DEBUG', 'INFO', 'WARNING', 'ERROR', or 'CRITICAL'.
                Defaults to 'DEBUG' for unknown level numbers.

        Example:
            >>> formatter = AppLogFormatter()
            >>> formatter._get_level_prefix(logging.INFO)
            'INFO'
            >>> formatter._get_level_prefix(logging.CRITICAL)
            'CRITICAL'
        """
        if levelno >= logging.CRITICAL:
            return "CRITICAL"
        elif levelno >= logging.ERROR:
            return "ERROR"
        elif levelno >= logging.WARNING:
            return "WARNING"
        elif levelno >= logging.INFO:
            return "INFO"
        elif levelno >= logging.DEBUG:
            return "DEBUG"
        else:
            return "TRACE"


def create_formatter(use_colors: bool = True) -> AppLogFormatter:
    """
    Create an AppLogFormatter instance with sensible default settings.

    This convenience function provides a quick way to create a formatter with the
    most commonly used configuration options. It uses the default format string
    that includes level prefix, timestamp with milliseconds, thread name, logger
    name, and message for comprehensive log formatting.

    Args:
        use_colors: Whether to enable ANSI color codes for log level prefixes.
            When True, log messages will be displayed with colored level prefixes
            in console output, making it easier to visually distinguish between
            different log levels. Default is True.

    Returns:
        AppLogFormatter: A configured formatter instance ready for use with logging handlers.
            The formatter uses the default format string and ISO timestamp format
            for consistent, readable log output.

    Example:
        >>> formatter = create_formatter(use_colors=True)
        >>> handler = logging.StreamHandler()
        >>> handler.setFormatter(formatter)
        >>> logger = logging.getLogger('my_app')
        >>> logger.addHandler(handler)
        >>> logger.warning('This warning will be displayed in yellow')
    """
    return AppLogFormatter(use_colors=use_colors)
