"""This package provides a set of functions to manage logging in Python applications.

It includes functions to enable or disable the default logging handler, catch the default handler,
get child loggers, and retrieve the root logger. It also provides constants for different logging levels.
"""

from logging import CRITICAL, DEBUG, ERROR, INFO, NOTSET, WARNING

from ._logging import (
    catch_default_handler,
    disable_default_handler,
    enable_default_handler,
    get_child_logger,
    get_handler,
    get_root_logger,
)

__all__ = (
    "catch_default_handler",
    "disable_default_handler",
    "enable_default_handler",
    "get_child_logger",
    "get_handler",
    "get_root_logger",
    "CRITICAL",
    "DEBUG",
    "ERROR",
    "INFO",
    "NOTSET",
    "WARNING",
)
