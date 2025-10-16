"""Common functions used by the SDK specifically for use with C API modules.

Warnings
--------
Vendors and clients should not develop scripts or applications against
this module. The contents may change at any time without warning.

"""
###############################################################################
#
# (C) Copyright 2020, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import ctypes
import logging

from ..errors import ApplicationTooOldError
from .errors import (
  CApiError,
  CApiFunctionNotSupportedError,
  CApiDllLoadFailureError,
  CApiUnknownError,
  NoConnectedApplicationError,
  MultipleApplicationConnectionsError,
  CApiCorruptDataError,
  CApiWarning,
  CApiUnknownWarning,
)


logger = logging.getLogger("mapteksdk.capi.util")


def get_string(target_handle, dll_function) -> str | None:
  """Read a string from a C API function.

  This works for C API functions which return a string
  and have a function signature of the form: Tint32u (handle, *buffer, size).

  Parameters
  ----------
  target_handle : c_uint64, T_ObjectHandle, T_NodePathHandle, etc
    Suitable type of native handle (), supporting
    a *.value property.
  dll_function : function
    A function of Tint32u (handle, *buffer, size).

  Returns
  -------
  str
    Result as string or None on failure (e.g. not supported by dll).

  """
  try:
    value_size = 64
    while value_size > 0:
      value_buffer = ctypes.create_string_buffer(value_size)
      result_size = dll_function(target_handle, value_buffer, value_size)
      if result_size is None:
        # probably not supported by dll version
        return None
      value_size = -1 if result_size <= value_size else result_size
    return value_buffer.value.decode("utf-8")
  except OSError:
    result = None
  return result

def raise_if_version_too_old(feature, current_version, required_version):
  """Raises a CapiVersionNotSupportedError if current_version is less
  than required_version.

  Parameters
  ----------
  feature : str
    The feature name to include in the error message.
  current_version : tuple
    The current version of the C Api.
  required_version : tuple
    The version of the C Api required to access the new feature.

  Raises
  ------
  ApplicationTooOldError
    If current_version < required_version.

  """
  if current_version < required_version:
    logger.info(
      "%s is not supported in C Api version: %s. Requires version: %s.",
      feature,
      current_version,
      required_version
    )
    raise ApplicationTooOldError.with_default_message(feature)

__all__ = [
  # These errors must be importable from here for backwards compatibility.
  "CApiError",
  "CApiFunctionNotSupportedError",
  "CApiDllLoadFailureError",
  "CApiUnknownError",
  "NoConnectedApplicationError",
  "MultipleApplicationConnectionsError",
  "CApiCorruptDataError",
  "CApiWarning",
  "CApiUnknownWarning",
  "get_string",
  "raise_if_version_too_old",
]
