"""Gaincraft HDR image processing toolkit."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("gaincraft")
except PackageNotFoundError:
    __version__ = "0+unknown"
