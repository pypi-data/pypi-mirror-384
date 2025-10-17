import logging
from datetime import datetime

from dpn_pyutils.logging.formatters import AppLogFormatter


class TimedFileHandler(logging.FileHandler):
    """A file handler that creates timestamped log files.

    This handler extends logging.FileHandler to support dynamic filename
    generation using datetime formatting. The filename parameter should be
    a strftime format string that will be formatted with the current datetime
    when the handler is created.

    Attributes:
        use_colors (bool): Whether to use colors in log formatting when
            used with AppLogFormatter.
    """

    use_colors: bool = False

    def __init__(self, filename, mode="a", encoding=None, delay=False, use_colors=False):
        """Initialize the TimedFileHandler.

        Args:
            filename (str): A strftime format string for the log filename.
                Will be formatted with current datetime (e.g., "%Y-%m-%d_%H-%M-%S.log").
            mode (str, optional): File opening mode. Defaults to "a" (append).
            encoding (str, optional): File encoding. Defaults to None.
            delay (bool, optional): Whether to delay file opening. Defaults to False.
            use_colors (bool, optional): Whether to enable colors in formatting. Defaults to False.
        """
        filename = datetime.now().strftime(filename)
        super().__init__(filename, mode, encoding, delay)
        self.use_colors = use_colors

    def setFormatter(self, fmt: logging.Formatter | None) -> None:
        """Set the formatter for this handler.

        If the formatter is an AppLogFormatter with color support, synchronizes
        the use_colors setting with the handler's setting.

        Args:
            fmt (logging.Formatter | None): The formatter to set. Can be None to remove formatting.
        """
        if isinstance(fmt, AppLogFormatter) and fmt is not None and hasattr(fmt, "use_colors"):
            fmt.use_colors = self.use_colors

        super().setFormatter(fmt)
