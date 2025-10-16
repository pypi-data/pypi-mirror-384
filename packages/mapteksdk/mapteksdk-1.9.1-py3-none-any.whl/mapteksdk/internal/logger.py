"""Logging for the Python SDK.

Warnings
--------
Vendors and clients should not develop scripts or applications against
this package. The contents may change at any time without warning.
"""
###############################################################################
#
# (C) Copyright 2020, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
import os
import sys

LOGGING_CONFIGURED = False

def _generate_file_handler(
    file_path: str | None,
    file_log_level: int,
    formatter: logging.Formatter
  ) -> RotatingFileHandler | logging.FileHandler:
  """Generate the file handler for logging to a file.

  Parameters
  ----------
  file_path
    Path to the log file to use, or None to use the default location.
    If the default location is used, the logs will be sent when the
    "Request Support" function of the Workbench is used.
    This is ignored when running the tests.
  file_log_level
    The level to log to files at.
  formatter
    Formatter to use for log messages.

  Returns
  -------
  RotatingFileHandler | logging.FileHandler | None
    A RotatingFileHandler if not running tests.
    A FileHandler if running tests.
    None if not running tests and the user's appdata directory was not
    available.
  """
  # This environment variable should only be set when testing.
  test_log_path = os.getenv('MDF_SDK_TEST_LOG_LOCATION')
  is_testing = False

  if test_log_path is None:
    # The environment variable wasn't set, so we aren't testing.
    if file_path is None:
      user_appdata = os.getenv('APPDATA')
      if not user_appdata:
        # Follow the XDG Base Directory Specification, if APPDATA isn't set.
        user_appdata = os.getenv(
          'XDG_STATE_HOME',
          os.path.join(os.path.expanduser('~'), '.local', 'state'))
      test_log_path = os.path.join(
        user_appdata, 'Maptek', 'pythonsdk', 'log.txt')
    else:
      test_log_path = file_path
  else:
    # The environment variable was set, so this is testing.
    is_testing = True

  # Make the file and any containing folders.
  os.makedirs(os.path.dirname(test_log_path), exist_ok=True)
  with open(test_log_path, 'a', encoding="utf-8"):
    os.utime(test_log_path, None)

  if is_testing:
    # Tests do not use a rotating log file to avoid creating multiple log
    # files on the test machines.
    # The mode is w to ensure the log is overwritten each time on
    # developer machines.
    file_handler = logging.FileHandler(
      test_log_path,
      mode="w"
    )
  else:
    # Use a rotating file handler to prevent the log file from growing too
    # large. When the log file exceeds 5 megabytes it will be renamed
    # log.txt.1 and a new log.txt file will be started.
    # Up to 15 log files will be kept, however only the most recent
    # is sent with support requests.
    file_handler = RotatingFileHandler(
      test_log_path,
      maxBytes=5000000, # 5 megabytes.
      backupCount=15)
  file_handler.setLevel(file_log_level)
  file_handler.setFormatter(formatter)
  return file_handler


def configure_log(logger: logging.Logger,
                  file_path: str | None=None,
                  file_log_level: int=logging.INFO,
                  console_log_level: int=logging.WARNING,
                  use_file: bool=True,
                  use_console: bool=False,
                  propagate: bool=False):
  r"""Configure the logger instance.

  Set-up handlers for writing to a log file and the console. If this is called
  multiple times, all calls but the first will be ignored.

  Parameters
  ----------
  logger
    The logger to configure.
  file_path
    The full path to the log file.
    If None (default), then the log file will be written into the default
    location.
  file_log_level
    Minimum log level for logging to disk. This is INFO by default.
  console_log_level
    Minimum log level for logging to the console. This is WARNING by default.
  use_file
    If the script should write log messages to the log file.
    Setting this to False will cause file_path to be ignored.
  use_console
    If the script should write log messages to the console.
  propagate
    True if the log entries should be propagated to the root logger.
    This will cause all log entries to be logged twice, once by the
    passed logger and once by the root logger.

  Warnings
  --------
  If file_path is not None, or use_file is False, then the Python SDK logs
  will not be sent when you use the "Request Support" option in Maptek
  Workbench. This may limit Maptek's ability to provide support.

  Notes
  -----
  If the file path is not specified, the log is saved to:
  AppData\\\Roaming\\\Maptek\\\pythonsdk\\\log.txt.
  """
  # pylint: disable=global-statement
  global LOGGING_CONFIGURED
  if LOGGING_CONFIGURED:
    # Configuring logging more than once can result in the log file being
    # deleted and recreated, losing any prior logging.
    # This is particularly problematic during testing as a rotating log
    # handler is not used in that case.
    return
  LOGGING_CONFIGURED = True

  if __debug__:
    # This constant is true if Python was not started with an -O option.
    #
    # Therefore this is the default behaviour, so we should reconsider if this
    # is useful.
    file_log_level = logging.DEBUG
    console_log_level = logging.WARNING
    use_console = True

  # The handlers won't receive messages if the loggers level is higher than
  # the handler's level.
  if use_console:
    logger.setLevel(min(file_log_level, console_log_level))
  else:
    logger.setLevel(file_log_level)

  formatter = logging.Formatter(
    '%(asctime)s | %(name)s | %(levelname)s | %(message)s')

  if use_file:
    file_handler = _generate_file_handler(
      file_path, file_log_level, formatter)
    logger.addHandler(file_handler)

  if use_console:
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

  logger.propagate = propagate
