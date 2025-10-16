"""Errors thrown by C API modules.

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

from ..errors import ApplicationTooOldError

class CApiError(Exception):
  """Base class for errors raised by the C API. This class should not be
  raised directly - raise a subclass instead.

  """


CApiFunctionNotSupportedError = ApplicationTooOldError
"""Alias for FunctionNotSupportedError.

This preserves backwards compatibility, though this is internal so no one
should have been catching this exception.
"""


class CApiDllLoadFailureError(CApiError):
  """Error raised when one of the DLLs fails to load."""


class CApiUnknownError(CApiError):
  """Error raised when an unknown error occurs in the CAPI."""


class NoConnectedApplicationError(CApiError):
  """Error raised when not connected to an application"""


class MultipleApplicationConnectionsError(CApiError):
  """Error raised when attempting to connect to two different applications.

  Connecting to two different applications within the same script is impossible
  because Python cannot effectively unload every DLL required to connect
  an application (It can't unload DLLs implicitly loaded as dependencies of
  the explicitly loaded DLLs). Thus, attempting to connect to a second
  application results in a mix of incompatible DLLs from the two
  applications.

  """


class CApiCorruptDataError(CApiError):
  """Error indicating the C API encountered corrupt data."""


class CApiWarning(Warning):
  """Base class for warnings emitted from the C APIs."""


class CApiUnknownWarning(CApiWarning):
  """A C API function returned an unknown error, but it was not fatal.

  This is emitted in place of CApiUnknownError when the error is non-fatal.
  """
