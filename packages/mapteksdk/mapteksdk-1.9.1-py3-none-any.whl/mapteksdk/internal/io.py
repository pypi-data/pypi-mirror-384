"""Helper functions for io operations.
"""
###############################################################################
#
# (C) Copyright 2024, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

from collections.abc import Sequence
import os
import pathlib

def validate_path(
  path: str | os.PathLike,
  expected_extension: str | Sequence[str]
) -> pathlib.Path:
  """Convert `path` to a pathlib Path and validate it has `expected_extension`.

  Parameters
  ----------
  path
    The path to convert and validate.
  expected_extension
    The expected file extension. This should include the dot.
    If a sequence, then this will accept any of the extensions in the sequence.

  Returns
  -------
  pathlib.Path
    `path` converted to a pathlib path.

  Raises
  ------
  ValueError
    If the file extension does not match `expected_extension`.
    The comparison is done case-insensitively.
  """
  if not isinstance(path, pathlib.Path):
    path = pathlib.Path(path)
  if isinstance(expected_extension, str):
    actual_extensions = (expected_extension,)
  else:
    actual_extensions = (
      extension.casefold() for extension in expected_extension
    )
  if path.suffix.casefold() not in actual_extensions:
    raise ValueError(
      f"Failed to import '{path}'. The extension was '{path.suffix}'. "
      f"Expected the extension to be '{expected_extension}'."
    )
  return path
