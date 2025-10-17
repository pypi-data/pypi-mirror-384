"""This module contains constants used throughout the packing_packages package.

It includes constants for file extensions, encoding, and other configuration values.
"""

from typing import Literal

__all__ = (
    "EXTENSIONS_CONDA",
    "EXTENSIONS_PYPI",
)

EXTENSIONS_CONDA: tuple[Literal["tar.bz2"], Literal["conda"]] = (
    "tar.bz2",
    "conda",
)
"""Extensions for conda packages.

These are the extensions used by conda packages.
"""

EXTENSIONS_PYPI: tuple[Literal["whl"], Literal["tar.gz"]] = (
    "whl",
    "tar.gz",
)
"""Extensions for PyPI packages.

These are the extensions used by PyPI packages.
"""
