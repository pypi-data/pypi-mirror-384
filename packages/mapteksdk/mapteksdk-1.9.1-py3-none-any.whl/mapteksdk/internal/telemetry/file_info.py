"""Functions for querying information about a file.

This information is recorded in a telemetry event.

Warnings
--------
Vendors and clients should not develop scripts or applications against
this package. The contents may change at any time without warning.
"""
###############################################################################
#
# (C) Copyright 2025, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import hashlib
from inspect import stack
from os.path import basename
import typing

class FileInformation(typing.NamedTuple):
  """Information about a file."""
  name: str
  """The file's name."""
  file_hash: str
  """The file's hash."""


def _get_source_file_path() -> str:
  """Get the path to the currently running script.

  Raises
  ------
  StopIteration
    If Python is running in an interpreter rather than a script file.
  """
  return next(
    frame.filename for frame in stack()[::-1]
    if not frame.filename.startswith('<')
  )


def _get_script_hash(path: str) -> str:
  """Get the hash of the script at path."""
  file_hash = hashlib.sha256()
  with open(path, "rb") as script:
    chunk = script.read(1024)
    while chunk != b"":
      file_hash.update(chunk)
      chunk = script.read(1024)
  return file_hash.hexdigest()


def get_script_information() -> FileInformation:
  """Get information on the currently running script."""
  try:
    source_file_path = _get_source_file_path()
  except StopIteration:
    # The stack didn't include any files with paths.
    # This must be being run from the interpreter and not a script.
    return FileInformation("<Interpreter>", "N/A")
  file_hash = _get_script_hash(source_file_path)
  return FileInformation(basename(source_file_path), file_hash)
