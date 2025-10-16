"""Interface for the MDF selection library.

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
import ctypes

from ..errors import ApplicationTooOldError
from .errors import CApiUnknownError
from .types import T_ObjectHandle, T_TypeIndex, T_ReadHandle
from .util import raise_if_version_too_old
from .wrapper_base import WrapperBase


class SelectionApi(WrapperBase):
  """Access to the application selection API.

  This should be accessed through get_application_dlls() for new code.
  """
  @staticmethod
  def method_prefix():
    return "Selection"

  @staticmethod
  def dll_name() -> str:
    return "mdf_selection"

  def capi_functions(self):
    return [
      # Functions changed in version 0.
      # Format:
      # "name" : (return_type, arg_types)
      {"SelectionSaveGlobalSelection" : (T_ObjectHandle, None),
       "SelectionSetGlobalSelection" : (ctypes.c_void_p, [T_ObjectHandle, ]),
       "SelectionFreeSavedSelection" : (ctypes.c_void_p, [T_ObjectHandle, ]),},
      # Functions changed in version 1.
      {"SelectionCApiVersion" : (ctypes.c_uint32, None),
       "SelectionCApiMinorVersion" : (ctypes.c_uint32, None),

       # New in API version 1.12:
       "SelectionGroupType" : (T_TypeIndex, None),
       "SelectionGetSelectionGroupContextType" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_uint8), ]),
       "SelectionSetSelectionGroupContextType" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint8, ]),
      }
    ]

  def GroupType(self) -> int:
    """Get the static type for selection group objects."""
    raise_if_version_too_old(
      "Querying type of selection groups",
      current_version=self.version,
      required_version=(1, 13)
    )
    return self.dll.SelectionGroupType()

  def GetSelectionGroupContextType(self, read_handle: T_ReadHandle) -> int:
    """Get the context type index for the selection group `read_handle`.

    If the application is newer than the SDK, this may not return a context type
    index which the SDK knows about.
    """
    raise_if_version_too_old(
      "Querying selection group context type",
      current_version=self.version,
      required_version=(1, 13)
    )

    c_index = ctypes.c_uint8()
    result = self.dll.SelectionGetSelectionGroupContextType(read_handle, ctypes.byref(c_index))
    if result != 0:
      raise CApiUnknownError("Failed to query selection group context type.")
    return c_index.value

  def SetSelectionGroupContextType(self, edit_handle: T_ReadHandle, group_context_index: int):
    """Set the context type index for the selection group `edit_handle`.

    Raises
    ------
    ApplicationTooOldError
      If `group_context_index` is not supported by the connected application.
    """
    raise_if_version_too_old(
      "Querying selection group context type",
      current_version=self.version,
      required_version=(1, 13)
    )

    result = self.dll.SelectionSetSelectionGroupContextType(edit_handle, group_context_index)
    if result == 3:
      raise ApplicationTooOldError("The application does not support the SelectionGroup's context.")
    if result != 0:
      raise CApiUnknownError("Failed to set selection group context type.")
