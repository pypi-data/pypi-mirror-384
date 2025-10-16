"""Overwrite modes for functions."""
###############################################################################
#
# (C) Copyright 2023, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import enum

class OverwriteMode(enum.Enum):
  """Enumeration indicating how to handle existing objects.

  Each overwrite mode provides a different mechanism for handling the case
  of there already being an object at the destination.
  """
  ERROR = 0
  """Do not overwrite existing objects.

  If there is already an object at the destination path, then an error
  will be raised and the object at the destination path will be left
  unchanged.
  """
  OVERWRITE = 1
  """Overwrite existing objects.

  If there is already an object at the destination path, then that
  object will be removed from that path and the new object will
  be placed at the specified path.
  """
  UNIQUE_NAME = 2
  """Use a unique name to avoid overwriting existing objects.

  If there is already an object at the destination path, the destination
  path will be suffixed with an integer to create a new, unique name
  and the object will be placed at that path instead.
  """
