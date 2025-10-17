from pathlib import Path


class FileOperationError(Exception):
    """
    Exception raised for file operation errors.

    Attributes:
        file_path (Path): The path of the file that caused the exception.

    """

    def __init__(self, file_path: Path, message: str):
        """
        Initialize a FileOperationError instance.

        Args:
            file_path (Path): The path of the file that caused the exception.
            message (str): The error message.

        """
        self.file_path = file_path
        super().__init__(message)


class FileSaveError(FileOperationError):
    """
    Exception raised when there is an error saving a file.
    """
    pass


class FileOpenError(FileOperationError):
    """
    Exception raised when there is an error opening a file.
    """
    pass


class FileNotFoundError(FileOperationError):
    """
    Exception raised when a file is not found during a file operation.
    """
    pass
