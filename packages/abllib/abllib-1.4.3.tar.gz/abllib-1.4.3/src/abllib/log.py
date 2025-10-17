"""A module containing the logger creation"""

from __future__ import annotations

import atexit
import logging
import sys
from enum import Enum
from typing import Literal

from abllib import error
from abllib._storage import InternalStorage

DEFAULT_LOG_LEVEL = logging.INFO

class LogLevel(Enum):
    """An enum holding log levels"""

    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    ALL = 1
    NOTSET = logging.NOTSET

    @staticmethod
    def from_str(log_level: str) -> LogLevel:
        """Return the matching LogLevel enum value from the given string"""

        match log_level.lower():
            case "all":
                return LogLevel.ALL
            case "debug":
                return LogLevel.DEBUG
            case "info":
                return LogLevel.INFO
            case "warning":
                return LogLevel.WARNING
            case "error":
                return LogLevel.ERROR
            case "critical":
                return LogLevel.CRITICAL
            case _:
                raise error.NameNotFoundError(f"'{log_level}' isn't a known log level")

    def __eq__(self, other):
        return self is other or self.value == other

    def __ne__(self, other):
        return self is not other and self.value != other

    # for more details look here:
    # https://stackoverflow.com/a/72664895/15436169
    def __hash__(self):
        return hash(self.value)

def initialize(log_level: Literal[LogLevel.CRITICAL]
                          | Literal[LogLevel.ERROR]
                          | Literal[LogLevel.WARNING]
                          | Literal[LogLevel.INFO]
                          | Literal[LogLevel.DEBUG]
                          | Literal[LogLevel.ALL]
                          | int
                          | None = None):
    """
    Initialize the custom logging module.

    This disables all log output. Use the add_<*>_handler functions to complete the setup.

    This function removes any previous logging setup, also overwriting the root logger formatter.
    """

    logging.disable()

    root_logger = get_logger()

    # remove existing handlers
    if "_log.handlers" in InternalStorage:
        for handler in InternalStorage["_log.handlers"]:
            root_logger.removeHandler(handler)

            # remove atexit function
            if isinstance(handler, logging.FileHandler):
                atexit.unregister(handler.close)
                handler.close()

    if log_level is None:
        InternalStorage["_log.level"] = DEFAULT_LOG_LEVEL
        root_logger.setLevel(DEFAULT_LOG_LEVEL)
        return

    if not isinstance(log_level, (int, LogLevel)):
        raise TypeError(f"Expected log_level to be of type {int | LogLevel}, but got {type(log_level)}")

    if log_level == LogLevel.NOTSET:
        raise ValueError("LogLevel.NOTSET is not allowed.")

    if isinstance(log_level, LogLevel):
        log_level = log_level.value

    assert isinstance(log_level, int)

    InternalStorage["_log.level"] = log_level
    root_logger.setLevel(log_level)

def add_console_handler() -> None:
    """
    Add a console handler to the root logger.

    This configures all loggers to also print to sys.stdout.
    """

    if "_log.level" not in InternalStorage:
        raise error.NotInitializedError("log.initialize() needs to be called first")

    logging.disable(0)

    stream_handler = logging.StreamHandler(sys.stdout)

    stream_handler.setLevel(InternalStorage["_log.level"])

    stream_handler.setFormatter(_get_formatter())

    get_logger().addHandler(stream_handler)

    # add logger to storage
    if "_log.handlers" not in InternalStorage:
        InternalStorage["_log.handlers"] = []
    InternalStorage["_log.handlers"].append(stream_handler)

def add_file_handler(filename: str = "latest.log", filemode: Literal["w"] | Literal["a"] = "w") -> None:
    """
    Add a file handler to the root logger.

    This configures all loggers to also print to a given file, or 'latest.log' if not provided.
    """

    if "_log.level" not in InternalStorage:
        raise error.NotInitializedError("log.initialize() needs to be called first")

    logging.disable(0)

    # needs to be imported here to prevent circular import
    # pylint: disable-next=cyclic-import, import-outside-toplevel
    from abllib.fs import absolute
    file_handler = logging.FileHandler(filename=absolute(filename), encoding="utf-8", mode=filemode, delay=True)

    file_handler.setLevel(InternalStorage["_log.level"])

    file_handler.setFormatter(_get_formatter())

    get_logger().addHandler(file_handler)

    atexit.register(file_handler.close)

    # add logger to storage
    if "_log.handlers" not in InternalStorage:
        InternalStorage["_log.handlers"] = []
    InternalStorage["_log.handlers"].append(file_handler)

def get_logger(name: str | None = None) -> logging.Logger:
    """
    Return a logger with the given name, or the root logger if name is None.

    If a logger doesn't yet exist, it is created and then returned.
    """

    if name is None:
        return logging.getLogger()

    if not isinstance(name, str):
        raise TypeError(f"Expected logger name to be of type {str}, but got {type(name)}")

    return logging.getLogger(name)

def get_loglevel() -> Literal[LogLevel.CRITICAL] \
                      | Literal[LogLevel.ERROR] \
                      | Literal[LogLevel.INFO] \
                      | Literal[LogLevel.WARNING] \
                      | Literal[LogLevel.DEBUG] \
                      | Literal[LogLevel.ALL] \
                      | None:
    """Return the current LogLevel"""

    return InternalStorage["_log.level"] if "_log.level" in InternalStorage else None

def _get_formatter():
    dt_fmt = r"%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter("[{asctime}] [{levelname:<8}] {name}: {message}", dt_fmt, style="{")
    return formatter
