"""Interface for the MDF vulcan library.

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
# pylint: disable=invalid-name
from collections.abc import Sequence
import ctypes
import pathlib
import typing

from .errors import (
  CApiUnknownError,
  CApiCorruptDataError,
)
from .types import T_ObjectHandle, T_TypeIndex, T_ReadHandle
from .util import raise_if_version_too_old
from .wrapper_base import WrapperBase

if typing.TYPE_CHECKING:
  from ..data import ObjectID, DistanceUnit
  from ..data.block_model_definition import BlockModelDefinition


SUCCESS = 0
"""Error code indicating the function call was successful."""
BUFFER_TOO_SMALL = 6
"""Error code indicating the buffer was too small."""

class VulcanApi(WrapperBase):
  """Access to the application Vulcan API.

  This should be accessed through get_application_dlls() for new code.
  """
  @staticmethod
  def method_prefix():
    return "Vulcan"

  @staticmethod
  def dll_name() -> str:
    return "mdf_vulcan"

  def capi_functions(self):
    return [
      # Functions changed in version 0.
      # Format:
      # "name" : (return_type, arg_types)
      {"VulcanErrorMessage" : (ctypes.c_char_p, []),
       "VulcanRead00tFile" : (T_ObjectHandle, [ctypes.c_char_p, ctypes.c_int32]),
       "VulcanWrite00tFile" : (ctypes.c_bool, [T_ObjectHandle, ctypes.c_char_p, ctypes.c_int32]),
       "VulcanReadBmfFile" : (T_ObjectHandle, [ctypes.c_char_p, ctypes.c_int32]),
       "VulcanWriteBmfFile" : (ctypes.c_bool, [T_ObjectHandle, ctypes.c_char_p, ctypes.c_int32]),},
      # Functions changed in version 1.
      {"VulcanCApiVersion" : (ctypes.c_uint32, None),
       "VulcanCApiMinorVersion" : (ctypes.c_uint32, None),

       # New in version 1.11
       "VulcanBlockModelDefinitionType" : (T_TypeIndex, None),
       "VulcanNewBlockModelDefinition" : (T_ObjectHandle, None),
       "VulcanImportBlockModelDefinition" : (ctypes.c_uint8, [ctypes.POINTER(T_ObjectHandle), ctypes.c_char_p, ctypes.c_int32, ]),
       "VulcanExportBlockModelDefinition" : (ctypes.c_uint8, [T_ObjectHandle, ctypes.c_char_p, ctypes.c_int32, ]),
       "VulcanReadBlockModelDefinitionJson" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint32), ]),
       "VulcanWriteBlockModelDefinitionJson" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),

       # New in version 1.12
       "VulcanSelectionFileType" : (T_TypeIndex, None),
       "VulcanNewSelectionFile" : (T_ObjectHandle, None),
       "VulcanGetSelectionFileContents" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_char_p), ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32), ]),
       "VulcanSetSelectionFileContents" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_char_p), ctypes.c_uint32, ]),
       "VulcanSelectionFileGetIsInclusive" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_bool), ]),
       "VulcanSelectionFileSetIsInclusive" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.c_bool, ]),
       }
    ]

  def BlockModelDefinitionType(self) -> T_TypeIndex:
    """Get the static type for a block model definition."""
    raise_if_version_too_old(
      "Checking if an object is a block model definition",
      self.version,
      (1, 11)
    )
    return self.dll.VulcanBlockModelDefinitionType()

  def NewBlockModelDefinition(self) -> T_ObjectHandle:
    """Create a new block model definition."""
    raise_if_version_too_old(
      "Creating a block model definition",
      self.version,
      (1, 11)
    )
    return self.dll.VulcanNewBlockModelDefinition()

  def ImportBlockModelDefinition(
    self,
    path: pathlib.Path,
    unit: DistanceUnit
  ) -> T_ObjectHandle:
    """Import a block model definition from `path`.

    Parameters
    ----------
    path
      The path to the bdf file to import.
    unit
      The unit to import the block model definition in.

    Returns
    -------
    T_ObjectHandle
      The handle of the imported block model definition.

    Raises
    ------
    FileNotFoundError
      If the file at `path` could not be found.
    CApiCorruptDataError
      If the file at `path` is corrupt.
    CApiUnknownError
      If an unknown error occurs.
    """
    raise_if_version_too_old(
      "Import block model definition",
      self.version,
      (1, 11)
    )
    handle = T_ObjectHandle()
    error_code = self.dll.VulcanImportBlockModelDefinition(
      ctypes.byref(handle),
      str(path).encode('utf-8'),
      unit.value
    )

    if error_code == 2:
      message = self.dll.VulcanErrorMessage().decode('utf-8')
      raise FileNotFoundError(
        f"Failed to import '{path}' due to the following error:\n"
        f"{message}")
    if error_code == 3:
      message = self.dll.VulcanErrorMessage().decode('utf-8')
      raise CApiCorruptDataError(
        f"Failed to import '{path}' due to the following error:\n"
        f"{message}"
      )
    if error_code != 0:
      message = self.dll.VulcanErrorMessage().decode('utf-8')
      raise CApiUnknownError(
        f"Failed to import {path} due to the following unknown error:\n"
        f"{message}")
    return handle

  def ExportBlockModelDefinition(
    self,
    definition_id: ObjectID[BlockModelDefinition],
    path: pathlib.Path,
    unit: DistanceUnit
  ):
    """Export a block model definition to `path`.

    Parameters
    ----------
    definition_id
      Object ID of the block model definition to export.
    path
      Path to export the block model definition to.
    unit
      The unit to export the block model definition using.

    Raises
    ------
    CApiUnknownError
      If an unknown error occurs.
    """
    raise_if_version_too_old(
      "Import block model definition",
      self.version,
      (1, 11)
    )
    error_code = self.dll.VulcanExportBlockModelDefinition(
      definition_id.handle,
      str(path).encode('utf-8'),
      unit.value
    )

    if error_code == 7:
      raise ValueError(
        "The connected application does not support exporting block model "
        "definitions with a unit which is not metres."
      )
    if error_code != 0:
      message = self.dll.VulcanErrorMessage().decode('utf-8')
      raise CApiUnknownError(
        f"Failed to export to {path} due to the following unknown error:\n"
        f"{message}")

  def ReadBlockModelDefinitionJson(self, read_handle: T_ReadHandle) -> str:
    """Read the block model definition json for `read_handle`."""
    raise_if_version_too_old(
      "Import block model definition",
      self.version,
      (1, 11)
    )

    buffer = ctypes.create_string_buffer(0)
    buffer_length = ctypes.c_uint32(0)

    result = self.dll.VulcanReadBlockModelDefinitionJson(
      read_handle,
      buffer,
      ctypes.byref(buffer_length)
    )

    if result != BUFFER_TOO_SMALL:
      # This should be unreachable.
      raise CApiUnknownError(
        "Failed to read block model definition."
      )

    # Buffer length should have been updated to contain the required buffer
    # length. Try again with a correctly sized buffer.
    buffer = ctypes.create_string_buffer(buffer_length.value)
    result = self.dll.VulcanReadBlockModelDefinitionJson(
      read_handle,
      buffer,
      buffer_length
    )

    if result != SUCCESS:
      message = self.dll.VulcanErrorMessage().decode('utf-8')
      raise CApiUnknownError(
        f"Failed to read block model definition due to the following unknown error:\n"
        f"{message}")

    return bytearray(buffer).decode('utf-8')

  def WriteBlockModelDefinitionJson(self, edit_handle: T_ReadHandle, json: str):
    """Set the block model definition json for `edit_handle`."""
    raise_if_version_too_old(
      "Import block model definition",
      self.version,
      (1, 11)
    )

    result = self.dll.VulcanWriteBlockModelDefinitionJson(edit_handle, json.encode('utf-8'))
    if result != SUCCESS:
      message = self.dll.VulcanErrorMessage().decode('utf-8')
      raise CApiUnknownError(
        f"Failed to read block model definition due to the following unknown error:\n"
        f"{message}")

  def SelectionFileType(self) -> ctypes.c_uint64:
    """Get the static type for selection files."""
    raise_if_version_too_old(
      "Check if an object is a selection file",
      self.version,
      (1, 12)
    )
    return self.dll.VulcanSelectionFileType()

  def NewSelectionFile(self) -> T_ObjectHandle:
    """Create a new selection file."""
    raise_if_version_too_old(
      "Create a new selection file",
      self.version,
      (1, 12)
    )
    return self.dll.VulcanNewSelectionFile()

  def GetSelectionFileContents(self, read_handle: T_ReadHandle) -> Sequence[str]:
    """Get the contents of the selection file `read_handle`."""
    raise_if_version_too_old(
      "Get the contents of a selection file",
      self.version,
      (1, 12)
    )

    buffer_count = ctypes.c_uint32(0)
    result = self.dll.VulcanGetSelectionFileContents(read_handle, None, None, ctypes.byref(buffer_count))

    if result == SUCCESS:
      # The file was empty.
      return tuple()
    if result != BUFFER_TOO_SMALL:
      # This should be unreachable.
      raise CApiUnknownError(
        "Failed to get selection file contents."
      )

    buffer_sizes = (ctypes.c_uint32 * buffer_count.value)()
    buffers = (ctypes.c_char_p * buffer_count.value)()
    result = self.dll.VulcanGetSelectionFileContents(read_handle, buffers, buffer_sizes, ctypes.byref(buffer_count))

    if result != BUFFER_TOO_SMALL:
      # This should be unreachable.
      raise CApiUnknownError(
        "Failed to get selection file contents."
      )

    for i, size in enumerate(buffer_sizes):
      buffers[i] = (" " * size).encode("utf-8")

    result = self.dll.VulcanGetSelectionFileContents(read_handle, buffers, buffer_sizes, ctypes.byref(buffer_count))
    if result != SUCCESS:
      message = self.dll.VulcanErrorMessage().decode("utf-8")
      raise CApiUnknownError(
        f"Failed to get selection file contents due to the following unknown error:\n"
        f"{message}")

    contents = []
    for item in buffers:
      contents.append(item.decode("utf-8"))
    return tuple(contents)

  def SetSelectionFileContents(self, edit_handle: T_ReadHandle, contents: Sequence[str]):
    """Set the contents of the selection file `edit_handle` to `contents`."""
    raise_if_version_too_old(
      "Get the contents of a selection file",
      self.version,
      (1, 12)
    )
    count = len(contents)

    buffers = (ctypes.c_char_p * count)()
    for i, content in enumerate(contents):
      buffers[i] = content.encode("utf-8")

    result = self.dll.VulcanSetSelectionFileContents(edit_handle, buffers, count)
    if result != SUCCESS:
      message = self.dll.VulcanErrorMessage().decode('utf-8')
      raise CApiUnknownError(
        f"Failed to set selection file contents due to the following unknown error:\n"
        f"{message}")

  def SelectionFileGetIsInclusive(self, read_handle: T_ReadHandle) -> bool:
    """Get if `read_handle` is an inclusive selection file."""
    raise_if_version_too_old(
      "Get if selection file is an inclusion file",
      self.version,
      (1, 12)
    )

    is_inclusion = ctypes.c_bool()
    result = self.dll.VulcanSelectionFileGetIsInclusive(read_handle, ctypes.byref(is_inclusion))
    if result != SUCCESS:
      message = self.dll.VulcanErrorMessage().decode('utf-8')
      raise CApiUnknownError(
        f"Failed to read if selection file is inclusive due to the following unknown error:\n"
        f"{message}")
    return is_inclusion.value

  def SelectionFileSetIsInclusive(self, edit_handle: T_ReadHandle, is_inclusive: bool):
    """Set if `edit_handle` is an inclusive selection file."""
    raise_if_version_too_old(
      "Get if selection file is an inclusion file",
      self.version,
      (1, 12)
    )

    result = self.dll.VulcanSelectionFileSetIsInclusive(edit_handle, is_inclusive)
    if result != SUCCESS:
      message = self.dll.VulcanErrorMessage().decode('utf-8')
      raise CApiUnknownError(
        f"Failed to read if selection file is inclusive due to the following unknown error:\n"
        f"{message}")
