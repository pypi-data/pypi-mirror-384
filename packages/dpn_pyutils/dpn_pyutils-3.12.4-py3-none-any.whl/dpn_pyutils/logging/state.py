"""
Logging state management module.

This module manages the global state for the logging system, providing
clean access to shared state variables through explicit methods.
"""


class LoggingState:
    """Manages global logging state."""

    def __init__(self):
        self._project_name: str = ""
        self._initialized: bool = False

    def get_project_name(self) -> str:
        """Get the current logging project name."""
        return self._project_name

    def set_project_name(self, name: str) -> None:
        """Set the logging project name."""
        self._project_name = name

    def is_initialized(self) -> bool:
        """Check if logging has been initialized."""
        return self._initialized

    def set_initialized(self, initialized: bool) -> None:
        """Set the initialization status."""
        self._initialized = initialized

    def reset(self) -> None:
        """Reset all state to defaults."""
        self._project_name = ""
        self._initialized = False


# Global state instance
_state = LoggingState()


def get_project_name() -> str:
    """Get the current logging project name."""
    return _state.get_project_name()


def set_project_name(name: str) -> None:
    """Set the logging project name."""
    _state.set_project_name(name)


def is_initialized() -> bool:
    """Check if logging has been initialized."""
    return _state.is_initialized()


def set_initialized(initialized: bool) -> None:
    """Set the initialization status."""
    _state.set_initialized(initialized)


def reset_state() -> None:
    """Reset all logging state to defaults. Useful for testing."""
    _state.reset()
