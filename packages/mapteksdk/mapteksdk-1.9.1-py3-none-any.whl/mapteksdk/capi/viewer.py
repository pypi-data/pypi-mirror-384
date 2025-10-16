"""Interface for the MDF viewer library.

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

# pylint: disable=line-too-long
# pylint: disable=invalid-name;reason=Names match C++ names.
import ctypes
import enum

from .types import T_ObjectHandle
from .wrapper_base import WrapperBase



class ViewerErrorCodes(enum.IntEnum):
  """The "null" error code"""
  NO_ERROR = 0

  """A generic error has occurred. This means the error does not fit into a
  more specific category of error or simply does not make sense to try to
  distinguish from another. For example a developer error where the error
  is with calling the function.
  """
  GENERIC_ERROR = 1

  """The provided buffer for a string was too small."""
  STRING_BUFFER_TOO_SMALL = 2

  """The view no longer exists. This is often a sign the view has been closed.
  """
  VIEW_NO_LONGER_EXISTS = 3


class ViewerApi(WrapperBase):
  """Access to the application viewer API.

  This should be accessed through get_application_dlls() for new code.
  """
  @staticmethod
  def method_prefix():
    return "Viewer"

  @staticmethod
  def dll_name() -> str:
    return "mdf_viewer"

  def capi_functions(self):
    return [
      # Functions changed in version 0.
      # Format:
      # "name" : (return_type, arg_types)
      {"ViewerInitialise" : (None, None),
       "ViewerCreateNewViewObject" : (T_ObjectHandle, None),
       "ViewerCreateNewDynamicObject" : (T_ObjectHandle, [ctypes.c_char_p, ]),
       "ViewerGetServerName" : (None, [T_ObjectHandle, ctypes.c_char_p, ctypes.c_uint64, ]),},
      # Functions changed in version 1.
      {"ViewerCApiVersion" : (ctypes.c_uint32, None),
       "ViewerCApiMinorVersion" : (ctypes.c_uint32, None),

       # The following were new in 1.3.
       "ViewerErrorCode" : (ctypes.c_uint32, None),
       "ViewerErrorMessage" : (ctypes.c_char_p, None),
      },
    ]

  def ErrorCode(self):
    """Return the last known error code returned by the viewer library.

    Raises
    ------
    CApiUnknownError
      If an error occurs.

    """

    if self.version < (1, 3):
      # Let us assume this was called when a function signalled that there was
      # an error.
      return ViewerErrorCodes.GENERIC_ERROR

    return ViewerErrorCodes(self.dll.ViewerErrorCode())

  def ErrorMessage(self):
    """Return the last known error message. This is specific to the viewer library.

    It is unspecified what this returns if there has been no error.
    """
    if self.version < (1, 3):
      return 'Unknown error - This application does not provide error information.'

    return self.dll.ViewerErrorMessage().decode('utf-8')
