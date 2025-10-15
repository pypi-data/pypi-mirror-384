"""
Custom logging implementation for the DW Object Detection project.
This module provides colored console logging for local development
and structured JSON logging for cloud environments.

USAGE:
Import the DwLogger class and set it as the default logger class
using logging.setLoggerClass(DwLogger).
Then create a logger object using logging.getLogger("logger_name").

NOTE: The root logger will not use this custom class as it is
initialized before the class is set.
"""

import json
import logging
import sys
import os
import io
import traceback

# Define color codes for different log levels in console output
COLORS = {
    "DEBUG": "\033[97m",  # White for DEBUG
    "INFO": "\033[94m",  # Blue for INFO
    "WARNING": "\033[93m",  # Yellow for WARNING
    "ERROR": "\033[91m",  # Red for ERROR
    "CRITICAL": "\033[41m",  # Red background for CRITICAL
    "RESET": "\033[0m",  # Reset color to default
}


class DwFormatter(logging.Formatter):
    """
    Custom formatter that adds colors to console log output.
    Also handles exception formatting with proper colors.
    """

    def format(self, record):
        if not hasattr(record, "created_from_logger"):
            record.created_from_logger = True
            record.filename = os.path.basename(record.pathname)

        log_color = COLORS.get(record.levelname, COLORS["RESET"])
        # Include %(exc_text)s in the format string to handle exceptions
        log_format = f"{log_color}[%(name)s] [%(levelname)s] [%(filename)s:%(lineno)d]: %(message)s{COLORS['RESET']}"

        # Format the main message
        formatter = logging.Formatter(log_format)

        # Override formatException to add colors
        def colored_format_exception(exc_info):
            return f"{log_color}{logging.Formatter.formatException(formatter, exc_info)}{COLORS['RESET']}"

        formatter.formatException = colored_format_exception
        return formatter.format(record)


class StackdriverFormatter(logging.Formatter):
    """
    Formatter that produces JSON-structured logs compatible with Google Cloud Logging (Stackdriver).
    Includes severity, message, logger name, and function details in the output.
    """

    def format(self, record):
        log_data = {
            "severity": record.levelname,
            "message": f"{record.filename} - {record.funcName}() line: {record.lineno} - {record.getMessage()}",
            "name": record.name,
            "function_name": f"{record.filename} - {record.funcName}() line: {record.lineno}",
        }
        return json.dumps(log_data)


class DwLogger(logging.getLoggerClass()):
    """
    Custom logger class that provides:
    - Automatic handler setup
    - Environment-aware formatting (colored for local, JSON for cloud)
    - Improved caller location tracking

    Args:
        name (str): The name of the logger instance
    """

    FILE_NAME = "dw_logger.py"

    def __init__(self, name):
        super().__init__(name)

        # Disable propagation to avoid duplicate logs
        self.propagate = False

        if not self.handlers:
            console_handler = logging.StreamHandler(sys.stderr)
            env = os.getenv("ENV")
            if env is None or env == "local":
                formatter = DwFormatter()
                default_level = logging.INFO
            elif env == "dev" or env == "develop":
                formatter = StackdriverFormatter()
                default_level = logging.INFO
            else:
                formatter = StackdriverFormatter()
                default_level = logging.WARNING

            self.setLevel(default_level)
            console_handler.setFormatter(formatter)
            self.addHandler(console_handler)

    def findCaller(self, stack_info=False, stacklevel=1):
        """
        Enhanced version of findCaller that properly skips logging infrastructure frames
        to report the actual source of the log message.

        Args:
            stack_info (bool): If True, include stack trace in the output
            stacklevel (int): Number of frames to skip when finding the caller

        Returns:
            tuple: (filename, line number, function name, stack info)
        """
        # Get current frame in the call stack
        f = logging.currentframe()
        # Move one back to skip this function's frame
        if f is not None:
            f = f.f_back
        # Save the original frame
        orig_f = f
        # Skip frames based on the stack level parameter
        while f and stacklevel > 1:
            f = f.f_back
            stacklevel -= 1
        # If we went too far, restore original frame
        if not f:
            f = orig_f

        # Default return value
        rv = "(unknown file)", 0, "(unknown function)", None

        # Traverse the call stack to find the first frame that is not internal
        while hasattr(f, "f_code"):
            co = f.f_code
            filename = os.path.normcase(co.co_filename)
            # Skip frames from logging module and this this file
            if filename == logging._srcfile or self.FILE_NAME in filename:
                f = f.f_back
                continue
            rv = (co.co_filename, f.f_lineno, co.co_name)
            break

        # Add stack trace information if requested
        if stack_info:
            with io.StringIO() as sio:
                sio.write("Stack (most recent call last):\n")
                traceback.print_stack(f, file=sio)
                sinfo = sio.getvalue()
                if sinfo[-1] == "\n":
                    sinfo = sinfo[:-1]
                rv = rv + (sinfo,)
        else:
            rv = rv + (None,)
        return rv
