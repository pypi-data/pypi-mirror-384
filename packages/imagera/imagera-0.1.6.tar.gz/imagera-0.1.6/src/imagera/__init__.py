from importlib.metadata import version, PackageNotFoundError

_DIST_NAME = __package__ or "imagera"

try:
    __version__ = version(_DIST_NAME)
except PackageNotFoundError:
    __version__ = "0.0.0"
__all__ = ["__version__"]