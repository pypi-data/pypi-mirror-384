"""Module containing code for loading DLLs.

Warnings
--------
Vendors and clients should not develop scripts or applications against
this module. The contents may change at any time without warning.
"""
###############################################################################
#
# (C) Copyright 2024, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import pathlib

from .errors import (
  MultipleApplicationConnectionsError,
  NoConnectedApplicationError,
)
from .mdf_dlls import MdfDlls

_Dlls: MdfDlls | None=None
"""The currently loaded or unloaded DLLs."""

def enable_dll_loading(dll_path: pathlib.Path) -> MdfDlls:
  """Enable loading application DLLs from `dll_path`.

  The caller can disable loading DLLs from this application by exiting
  a context manager on the returned object.

  Raises
  ------
  MultipleApplicationConnectionsError
    If called before disposing the returned object or if called with
    a different `dll_path` after disposing of the returned object.
  FileNotFoundError
    If the application DLLs cannot be found.
  """
  # pylint: disable=global-statement
  global _Dlls
  if _Dlls is not None:
    if _Dlls.can_load_dlls:
      raise MultipleApplicationConnectionsError(
        "Cannot connect to an application because the script is already "
        "connected to an application."
      )
    if dll_path != _Dlls.dll_path:
      raise MultipleApplicationConnectionsError(
        "Cannot connect to multiple different applications in one script"
      )
  dlls = MdfDlls(dll_path)
  _Dlls = dlls
  return dlls

def get_application_dlls() -> MdfDlls:
  """Get the currently registered application DLLs.

  Raises
  ------
  NoConnectedApplicationError
    If the script is not currently connected to an application.

  Notes
  -----
  Ideally, this function would not be necessary because the caller of
  `enable_dll_loading()` would pass the returned object to everything which
  needed it (In fact, once such a change could be made this entire module
  could be deleted).
  """
  dlls = _Dlls
  if dlls is None:
    raise NoConnectedApplicationError(
      "This function cannot be accessed because the script has not connected "
      "to an application. Use the Project() constructor to connect to an "
      "application."
    )
  if not dlls.can_load_dlls:
    raise NoConnectedApplicationError(
      "This function cannot be accessed because the script has disconnected "
      "from the application. Ensure all functions which require a "
      "connected application are inside of the Project's `with` block.")
  return dlls
