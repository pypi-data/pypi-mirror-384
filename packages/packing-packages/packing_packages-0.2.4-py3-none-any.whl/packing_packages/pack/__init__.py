"""Packing packages for distribution and installation.

This module provides functionality to pack conda environments and their
dependencies into a specified directory.

.. code-block:: bash

    $ python -m packing_packages pack --help

    or

    $ packing-packages pack --help

"""

from ._core import packing_packages

__all__ = ("packing_packages",)
