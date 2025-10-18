"""
Absfuyu: Logger
---------------
Custom Logger Module

Version: 5.12.0
Date updated: 17/10/2025 (dd/mm/yyyy)

Usage:
------
>>> from absfuyu.logger import logger, LogLevel
>>> logger.setLevel(LogLevel.DEBUG)
>>> logger.debug("This logs!")
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = [
    # logger
    "logger",
    "compress_for_log",
    # log level
    "LogLevel",
]


# Library
# ---------------------------------------------------------------------------
import logging
import math
from logging.handlers import RotatingFileHandler as _RFH
from logging.handlers import TimedRotatingFileHandler as _TRFH
from pathlib import Path
from typing import Any, Optional, Union


# Setup
# ---------------------------------------------------------------------------
class LogLevel:
    """
    ``logging``'s log level wrapper + custom log level
    """

    TRACE: int = logging.DEBUG - 5
    DEBUG: int = logging.DEBUG
    INFO: int = logging.INFO
    WARNING: int = logging.WARNING
    ERROR: int = logging.ERROR
    CRITICAL: int = logging.CRITICAL
    EXTREME: int = logging.CRITICAL + 10


class _LogFormat:
    """Some log format styles"""

    FULL = "[%(asctime)s] [%(process)-d] [%(module)s] [%(name)s] [%(funcName)s] [%(levelname)-s] %(message)s"  # Time|ProcessID|Module|Name|Function|LogType|Message
    SHORT = "[%(module)s] [%(name)s] [%(funcName)s] [%(levelname)-s] %(message)s"  # Module|Name|Function|LogType|Message
    CONSOLE = "%(asctime)s [%(levelname)5s] %(funcName)s:%(lineno)3d: %(message)s"  # Time|LogType|Function|LineNumber|Message
    FILE = "%(asctime)s [%(levelname)5s] %(filename)s:%(funcName)s:%(lineno)3d: %(message)s"  # Time|LogType|FileName|Function|LineNumber|Message


# Create a custom logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

# Create handlers
## Console log handler
console_handler = logging.StreamHandler()
console_handler.setLevel(LogLevel.TRACE)  # Minimum log level
console_handler.setFormatter(
    logging.Formatter(_LogFormat.CONSOLE, datefmt="%Y-%m-%d %H:%M:%S")
)
# logger.addHandler(console_handler)
logger.addHandler(logging.NullHandler())


# Functions
# ---------------------------------------------------------------------------
def _compress_list_for_print(iterable: list, max_visible: Optional[int] = 5) -> str:
    """
    Compress the list to be more log-readable

    iterable: list
    max_visible: Maximum items can be printed on screen (Minimum: 3)
    """

    if max_visible is None or max_visible <= 2:
        max_visible = 5

    if len(iterable) <= max_visible:
        return str(iterable)
    else:
        # logger.debug(f"Max vis: {max_visible}")
        if max_visible % 2 == 0:
            cut_idx_1 = math.floor(max_visible / 2) - 1
            cut_idx_2 = math.floor(max_visible / 2)
        else:
            cut_idx_1 = cut_idx_2 = math.floor(max_visible / 2)

        # logger.debug(f"Cut pos: {(cut_idx_1, cut_idx_2)}")
        # temp = [iterable[:cut_idx_1], ["..."], iterable[len(iterable)-cut_idx_2:]]
        # out = list(chain.from_iterable(temp))
        # out = [*iterable[:cut_idx_1], "...", *iterable[len(iterable)-cut_idx_2:]] # Version 2
        out = f"{str(iterable[:cut_idx_1])[:-1]}, ..., {str(iterable[len(iterable) - cut_idx_2 :])[1:]}"  # Version 3
        # logger.debug(out)
        return f"{out} [Len: {len(iterable)}]"


def _compress_string_for_print(text: str, max_visible: Optional[int] = 120) -> str:
    """
    Compress the string to be more log-readable

    text: str
    max_visible: Maximum text can be printed on screen (Minimum: 5)
    """

    if max_visible is None or max_visible <= 5:
        max_visible = 120

    text = text.replace("\n", " ")  # Remove new line
    # logger.debug(text)

    if len(text) <= max_visible:
        return str(text)
    else:
        cut_idx = math.floor((max_visible - 3) / 2)
        temp = f"{text[:cut_idx]}...{text[len(text) - cut_idx :]}"
        return f"{temp} [Len: {len(text)}]"


def compress_for_log(object_: Any, max_visible: Optional[int] = None) -> str:
    """
    Compress the object to be more log-readable

    :param object_: Object
    :param max_visible: Maximum objects can be printed on screen
    :returns: Compressed log output
    :rtype: str
    """

    if isinstance(object_, list):
        return _compress_list_for_print(object_, max_visible)

    elif isinstance(object_, (set, tuple)):
        return _compress_list_for_print(list(object_), max_visible)

    elif isinstance(object_, dict):
        temp = [{k: v} for k, v in object_.items()]
        return _compress_list_for_print(temp, max_visible)

    elif isinstance(object_, str):
        return _compress_string_for_print(object_, max_visible)

    else:
        try:
            return _compress_string_for_print(str(object_), max_visible)
        except Exception:
            return object_  # type: ignore


# Class
# ---------------------------------------------------------------------------
class _CustomLogger:
    """
    Custom logger [W.I.P]

    Create a custom logger
    *Useable but maybe unstable*
    """

    def __init__(
        self,
        name: str,
        cwd: Union[str, Path] = ".",
        log_format: Optional[str] = None,
        *,
        save_log_file: bool = False,
        separated_error_file: bool = False,
        timed_log: bool = False,
        date_log_format: Optional[str] = None,
        error_log_size: int = 1_000_000,  # 1 MB
    ) -> None:
        """
        :param name: Custom logger name
        :param cwd: Current working directory
        :param log_format: Log format
        :param save_log_file: Save logs to log file (default: False)
        :param separated_error_file: Save error logs into a separated file (Default: False)
        :param timed_log: Split log file every day. Requirement: `save_log_file = True` (Default: False)
        :param date_log_format: Date format in log
        :param error_log_size: Error log file max size (Default: 1 MB)
        """
        self._cwd = Path(cwd)
        self.log_folder = self._cwd.joinpath("logs")
        self.log_folder.mkdir(
            exist_ok=True, parents=True
        )  # Does not throw exception when folder existed
        self.name = name
        self.log_file = self.log_folder.joinpath(f"{name}.log")

        # Create a custom logger
        try:
            self.logger = logging.getLogger(self.name)
        except Exception:
            try:
                self.logger = logging.getLogger(__name__)
            except Exception:
                self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)

        if date_log_format is None:
            _date_format = "%Y-%m-%d %H:%M:%S"
        else:
            _date_format = date_log_format

        ## Console log handler
        if log_format is None:
            # Time|LogType|Function|LineNumber|Message
            _log_format = (
                "%(asctime)s [%(levelname)5s] %(funcName)s:%(lineno)3d: %(message)s"
            )
        else:
            _log_format = log_format
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)  # Minimum log level
        _console_log_format = _log_format  # Create formatters and add it to handlers
        _console_formatter = logging.Formatter(
            _console_log_format, datefmt=_date_format
        )
        console_handler.setFormatter(_console_formatter)
        self._console_handler = console_handler
        self.logger.addHandler(self._console_handler)  # Add handlers to the logger

        ## Log file handler
        if save_log_file:
            if log_format is None:
                # Time|LogType|FileName|Function|LineNumber|Message
                _log_format = "%(asctime)s [%(levelname)5s] %(filename)s:%(funcName)s:%(lineno)3d: %(message)s"
            else:
                _log_format = log_format
            file_handler = logging.FileHandler(
                self.log_file, mode="a", encoding="utf-8"
            )
            file_handler.setLevel(logging.DEBUG)
            _file_log_format = _log_format
            _file_formatter = logging.Formatter(_file_log_format, datefmt=_date_format)
            file_handler.setFormatter(_file_formatter)
            self._file_handler = file_handler
            self.logger.addHandler(self._file_handler)

            if timed_log:
                ## Time handler (split log every day)
                time_handler = _TRFH(
                    self.log_folder.joinpath(f"{self.name}_timed.log"),
                    when="midnight",
                    interval=1,
                    encoding="utf-8",
                )
                time_handler.setLevel(logging.DEBUG)
                time_handler.setFormatter(_file_formatter)
                self._time_handler = time_handler
                self.logger.addHandler(self._time_handler)
                # |   Value  |    Type of interval   |
                # |:--------:|:---------------------:|
                # |     S    |        Seconds        |
                # |     M    |        Minutes        |
                # |     H    |         Hours         |
                # |     D    |          Days         |
                # |     W    |  Week day (0=Monday)  |
                # | midnight | Roll over at midnight |

        ## Error and above log handler
        if separated_error_file:
            if log_format is None:
                # Time|LogType|FileName|Function|LineNumber|Message
                _log_format = "%(asctime)s [%(levelname)5s] %(filename)s:%(funcName)s:%(lineno)3d: %(message)s"
            else:
                _log_format = log_format
            error_handler = _RFH(
                self.log_folder.joinpath(f"{self.name}_error.log"),
                maxBytes=error_log_size,
                backupCount=1,
                encoding="utf-8",
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(_log_format)  # type: ignore
            self._error_handler = error_handler
            self.logger.addHandler(self._error_handler)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"

    def __repr__(self) -> str:
        return self.__str__()

    @staticmethod
    def _add_logging_level(
        level_name: str, level_num: int, method_name: Optional[str] = None
    ):
        """
        Comprehensively adds a new logging level to the `logging` module and the
        currently configured logging class.

        `level_name` becomes an attribute of the `logging` module with the value
        `level_num`. `method_name` becomes a convenience method for both `logging`
        itself and the class returned by `logging.getLoggerClass()` (usually just
        `logging.Logger`). If `method_name` is not specified, `level_name.lower()` is
        used.

        To avoid accidental clobberings of existing attributes, this method will
        raise an `AttributeError` if the level name is already an attribute of the
        `logging` module or if the method name is already present
        """
        # Original code: https://stackoverflow.com/a/35804945/1691778
        if not method_name:
            method_name = level_name.lower()

        if hasattr(logging, level_name):
            raise AttributeError(f"{level_name} already defined in logging module")
        if hasattr(logging, method_name):
            raise AttributeError(f"{method_name} already defined in logging module")
        if hasattr(logging.getLoggerClass(), method_name):
            raise AttributeError(f"{method_name} already defined in logger class")

        # This method was inspired by the answers to Stack Overflow post
        # http://stackoverflow.com/q/2183233/2988730, especially
        # http://stackoverflow.com/a/13638084/2988730
        def logForLevel(self, message, *args, **kwargs):
            if self.isEnabledFor(level_num):
                self._log(level_num, message, args, **kwargs)

        def logToRoot(message, *args, **kwargs):
            logging.log(level_num, message, *args, **kwargs)

        logging.addLevelName(level_num, level_name)
        setattr(logging, level_name, level_num)
        setattr(logging.getLoggerClass(), method_name, logForLevel)
        setattr(logging, method_name, logToRoot)

    def add_log_level(self, level_name: str, level_num: int):
        __class__._add_logging_level(level_name, level_num)  # type: ignore
        if level_num < logging.DEBUG:
            self._console_handler.setLevel(level_num)
            self.logger.setLevel(level_num)
