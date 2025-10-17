import logging
import logging.config
from pathlib import Path
from typing import Dict

from dpn_pyutils.logging.schemas import LoggingSchema
from dpn_pyutils.logging.state import (
    is_initialized,
    set_initialized,
    set_project_name,
)


class PyUtilsLogger(logging.Logger):
    """
    Overwrites the configured logging class with additional log methods
    """

    TRACE: int = logging.DEBUG - 5

    def trace(self, msg, *args, **kwargs) -> None:
        """
        Enter a log entry at the TRACE level
        """
        self.log(PyUtilsLogger.TRACE, msg, *args, **kwargs)


def initialize_logging(logging_config: Dict) -> None:
    """
    Initialises logging for the entire system
    """
    # Extract logging_project_name before dictConfig modifies the config
    if "logging_project_name" in logging_config:
        set_project_name(logging_config["logging_project_name"])

    # Add the TRACE level to our log
    logging.addLevelName(PyUtilsLogger.TRACE, "TRACE")
    logging.setLoggerClass(PyUtilsLogger)

    # Check to see if the file path for any file configuration
    # exists and if not, try to create the path
    for handler in logging_config["handlers"]:
        for key in logging_config["handlers"][handler]:
            if key.lower() == "filename" and logging_config["handlers"][handler][key] is not None:
                file_path = Path(logging_config["handlers"][handler][key])
                if not file_path.parent.exists():
                    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove logging_project_name from config before passing to dictConfig
    # to prevent it from interfering with the logging system
    config_for_dict = logging_config.copy()
    config_for_dict.pop("logging_project_name", None)

    logging.config.dictConfig(config_for_dict)


def initialize_logging_from_file(logging_config_file: str) -> None:
    """
    Initialize logging configuration and exception handling.
    This function sets up better exceptions for improved error messages,
    initializes logging based on a configuration file, and captures warnings.
    """

    if is_initialized():
        return

    import logging
    from pathlib import Path

    import better_exceptions

    from dpn_pyutils.file import read_file_json

    # Initialize exception management and load config
    better_exceptions.hook()

    if not Path(logging_config_file).exists():
        raise FileNotFoundError(f"Logging configuration file not found: {logging_config_file}")

    config_data = read_file_json(Path(logging_config_file))
    validated = LoggingSchema.model_validate(config_data)
    initialize_logging(validated.model_dump(exclude_none=True, by_alias=True))
    logging.captureWarnings(True)
    set_initialized(True)


def initialize_logging_safe(logging_config: Dict) -> None:
    """
    Safely initializes logging with fallback to basic console logger.
    Never raises exceptions - always provides working logging.
    """
    try:
        initialize_logging(logging_config)
    except Exception:
        # Fall back to basic console logging
        basic_config = {
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
        initialize_logging(basic_config)


def is_logging_initialized() -> bool:
    """
    Returns whether logging has been initialized
    """
    return is_initialized()
