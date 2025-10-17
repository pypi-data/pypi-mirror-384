import warnings

# trunk-ignore-all(flake8/F401)
# trunk-ignore-all(ruff/F401)
from .logging.init import PyUtilsLogger  # type: ignore
from .logging.logger import get_logger_fqn as get_fqn_logger  # type: ignore
from .logging.logger import get_logger  # type: ignore
from .logging.init import initialize_logging  # type: ignore

#
# DEPRECATED: This module is deprecated and will be removed in future releases.
#

# Issue deprecation warning when module is imported
warnings.warn(
    "dpn_pyutils.common module is deprecated and will be removed in future releases. "
    "Please migrate to using dpn_pyutils.logging directly.",
    DeprecationWarning,
    stacklevel=2
)
