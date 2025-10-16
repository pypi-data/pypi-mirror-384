from .api import retry
from yet_another_retry import retry_handlers, exception_handlers
from importlib.metadata import version, PackageNotFoundError

__all__ = ["retry", "retry_handlers", "exception_handlers"]

try:
    __version__ = version("yet-another-retry")
except PackageNotFoundError:
    __version__ = "0.0.0+local"
