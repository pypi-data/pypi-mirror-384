# SPDX-FileCopyrightText: 2025 German Aerospace Center <amiris@dlr.de>
#
# SPDX-License-Identifier: Apache-2.0

"""Holds AMIRIS-Py specific logging methods."""

import logging as log
from enum import Enum


class LogLevels(Enum):
    """Levels for Logging."""

    PRINT = 100
    CRITICAL = log.CRITICAL
    ERROR = log.ERROR
    WARN = log.WARNING
    INFO = log.INFO
    DEBUG = log.DEBUG


def log_critical(exception: Exception) -> Exception:
    """Logs a critical error with the exception's message and returns the exception for raising it.

    Does **not** raise the exception, i.e. the command must be preceded by a `raise`.
    Example: `raise log_critical(MyException("My error message"))`

    Args:
        exception: to extract the error message from

    Returns:
        the given exception
    """
    log.critical(str(exception))
    return exception


def log_error(exception: Exception) -> Exception:
    """Logs an error with the exception's message and returns the exception for raising.

    Does **not** raise the exception, i.e. the command must be preceded by a `raise`.
    Example: `raise log_error(MyException("My error message"))`

    Args:
        exception: to extract the error message from

    Returns:
        the given exception
    """
    log.error(str(exception))
    return exception


def set_up_logger(log_level: str, log_file_name: str = None) -> None:
    """Uses existing logger or sets up logger."""
    if not log.getLogger().hasHandlers():
        _set_up_new_logger(log_level, log_file_name)
    log.addLevelName(LogLevels.PRINT.value, LogLevels.PRINT.name)


def _set_up_new_logger(log_level: str, log_file_name: str = None) -> None:
    """Sets up root logger which always writes to console and optionally to file.

    Args:
        log_level: the logging level to apply
        log_file_name: optional - if provided, logs will also be written to file
    """
    log_level = LogLevels[log_level.upper()]
    if log_level is LogLevels.DEBUG:
        formatter_string = (
            "%(asctime)s.%(msecs)03d — %(levelname)s — %(module)s:%(funcName)s:%(lineno)d — %(message)s"  # noqa
        )
    else:
        formatter_string = "%(asctime)s — %(levelname)s — %(message)s"  # noqa

    log_formatter = log.Formatter(formatter_string, "%H:%M:%S")
    root_logger = log.getLogger()
    root_logger.setLevel(log_level.name)

    if log_file_name:
        file_handler = log.FileHandler(log_file_name, mode="w")
        file_handler.setFormatter(log_formatter)
        root_logger.addHandler(file_handler)

    console_handler = log.StreamHandler()
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)


def log_and_print(message: str) -> None:
    """Logs given message with the highest priority, thus ensures it is printed to console.

    Args:
        message: to be logged and printed
    """
    log.log(LogLevels.PRINT.value, message)
