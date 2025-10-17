from importlib.metadata import PackageNotFoundError, version

from .tfc_client import TFCClient

__title__ = "theforecastingcompany"
try:
    __version__ = version(__title__)
except PackageNotFoundError:
    __version__ = "unknown"  # for direct src imports
__all__ = ["__version__", "__title__", "TFCClient"]
