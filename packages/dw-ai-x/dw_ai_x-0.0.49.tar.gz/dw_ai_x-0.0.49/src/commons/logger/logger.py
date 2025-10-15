"""
Logging Configuration Module

This module provides a centralized logging configuration setup for the ANAS Traffic Forecasting system.
It handles both local development and cloud production environments, ensuring consistent logging
across the application.

The module uses Python's built-in logging module and integrates with Google Cloud Logging
for production environments.
"""

import io
import json
import logging
import os
import traceback
from datetime import datetime
from google.cloud import logging as gcloud_logging


# Define color codes for different log levels in console output
COLORS = {
    "DEBUG": "\033[97m",  # White for DEBUG
    "INFO": "\033[94m",  # Blue for INFO
    "WARNING": "\033[93m",  # Yellow for WARNING
    "ERROR": "\033[91m",  # Red for ERROR
    "CRITICAL": "\033[41m",  # Red background for CRITICAL
    "RESET": "\033[0m",  # Reset color to default
}


class SingleRecordFormatter(logging.Formatter):
    """
    Formatter that formats a single record.

    Target format: (timestamp) - (level) - (message) - (traceback)
    """

    def __init__(
        self,
        fmt: str = "%(asctime)s - %(levelname)s - %(message)s",
        is_cloud: bool = False,
    ):
        super().__init__(fmt)

        self.is_cloud = is_cloud

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the record for cloud logging.

        > If the record is from the cloud, format the record for cloud logging.
        > If the record is from the local, format the record for local logging.

        Args:
            record (logging.LogRecord): The record to format

        Returns:
            str: The formatted message
        """

        # In the Cloud, we use JSON format,
        # because it is automatically parsed by the Cloud Logging agent.
        if self.is_cloud:
            log_record = {
                "severity": record.levelname,
                "message": f"{record.levelname} - {record.filename}:{record.lineno} - {record.getMessage()}",
                "logger": record.name,
                "timestamp": datetime.fromtimestamp(record.created).strftime(
                    "%Y-%m-%d %H:%M:%S.%f"
                )[:-3],
                "caller": f"{record.filename}:{record.lineno}",
            }

            if record.exc_info:
                log_record["traceback"] = "".join(
                    traceback.format_exception(*record.exc_info)
                )
            return json.dumps(log_record)

        # In the local, we use a more readable format.
        log_color = (
            COLORS.get(record.levelname, COLORS["RESET"]) if not self.is_cloud else ""
        )
        message = f"{log_color}[{datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}] - {record.levelname} - {record.filename}:{record.lineno} - {record.getMessage()}"

        if record.exc_info:
            tb = "".join(traceback.format_exception(*record.exc_info))
            message += "\n### TRACEBACK ###\n\n" + tb + "\n### END TRACEBACK ###\n"

        message += f"{COLORS['RESET']}" if not self.is_cloud else ""
        return message


class Logger(logging.getLoggerClass()):
    """
    Custom logger class that provides:
    - Automatic handler setup
    - Environment-aware formatting (colored for local, JSON for cloud)
    - Improved caller location tracking
    """

    def __init__(self, name: str, level: int | str = logging.INFO) -> None:
        super().__init__(name)

        self.FILE_NAME = __file__

        # Disable propagation to avoid duplicate logs
        self.propagate = False

        # Set the level to INFO
        self.setLevel(level)

        # Check if the environment is cloud
        self.is_cloud = os.getenv("IS_CLOUD_ENV") == "true"

        # Configure the handlers
        self.configure_handlers(level)

    def configure_handlers(self, level: int | str = logging.INFO) -> None:
        """
        Configure the handlers for the logger
        """

        self.handlers = []

        # Initialize default handler and formatter
        formatter = SingleRecordFormatter(is_cloud=self.is_cloud)
        handler = logging.StreamHandler()

        # TODO: Commented out for testing purposes
        # if self.is_cloud:
        #     client = gcloud_logging.Client()
        #     handler = gcloud_logging.handlers.CloudLoggingHandler(client)

        handler.setFormatter(formatter)
        handler.setLevel(level)
        self.addHandler(handler)

    def error(self, msg, *args, **kwargs):
        """
        Enhanced error method that includes caller location and stack trace
        """

        # Remove the exc_info argument from the kwargs
        kwargs.pop("exc_info", None)

        if self.isEnabledFor(logging.ERROR):
            self._log(logging.ERROR, msg, exc_info=True, args=args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """
        Enhanced critical method that includes caller location and stack trace
        """

        # Remove the exc_info argument from the kwargs
        kwargs.pop("exc_info", None)

        if self.isEnabledFor(logging.CRITICAL):
            self._log(logging.CRITICAL, msg, exc_info=True, args=args, **kwargs)

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
        rv = (f"{self.FILE_NAME}", 0, "(unknown function)", None)

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


class LoggerFactory:
    """
    Factory class for creating logger instances.
    It handles both local and Google Cloud formatting based on ENV.
    """

    @classmethod
    def get_logger(cls) -> logging.Logger:
        """
        Get a logger instance with the given name and level.
        """

        if os.getenv("OVERRIDE_ROOT_LOGGER") == "true":
            # Remove existing handlers from root logger
            root_logger = logging.getLogger()
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)

            # Create a new root logger with our custom class
            logger = Logger("root")

            # Replace the root logger in the logging module
            logging.root = logger
        else:
            logger = Logger(os.getenv("COMPONENT_NAME", "system"))

        return logger


# Singleton logger instance
logger = LoggerFactory.get_logger()
