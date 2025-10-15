"""Utilities for chunked/pieced Parquet IO operations."""

from importlib.metadata import PackageNotFoundError, version as pkg_version

from .saver import PieceSaver
from .reader import PieceReader
from .sorter import PieceSorter

__all__ = [
    "PieceSaver",
    "PieceReader",
    "PieceSorter",
    "__version__",
]


try:
    __version__ = pkg_version("parcake")
except PackageNotFoundError:
    __version__ = "0.0.0"
