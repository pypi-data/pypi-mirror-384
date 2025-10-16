"""Interface for the MDF data transfer library.

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

# pylint: disable=line-too-long
# pylint: disable=invalid-name;reason=Names match C++ names.
from contextlib import AbstractContextManager
import ctypes
import functools
import typing
import warnings

from pyproj.enums import WktVersion

from .errors import (
  CApiUnknownError,
  CApiUnknownWarning,
  CApiError,
)
from .types import T_ObjectHandle
from .util import raise_if_version_too_old
from .wrapper_base import WrapperBase

if typing.TYPE_CHECKING:
  from collections.abc import Callable

  from ..data import DistanceUnit, CoordinateSystem


_CALLBACK = ctypes.CFUNCTYPE(None, ctypes.c_char_p)


class CApiInputNotSupportedError(CApiError):
  """Error indicating an input to an import operation is not supported."""


class dtfS_ImportOperation(ctypes.c_void_p):
  """Struct representing an import operation.

  This is an opaque object which can be passed to C API functions.
  """


class _FeedbackHandle(AbstractContextManager):
  """A handle on the feedback callbacks for a dtfS_ImportOperation.

  This ensures that the callbacks are not garbage collected until the
  __exit__() function of this object is called.

  Parameters
  ----------
  warning_callback
    The callback to call when a warning occurs.
  error_handle
    The callback to call when an error occurs.
  """
  def __init__(
    self,
    warning_callback: Callable[[str], None],
    error_callback: Callable[[str], None]
  ) -> None:
    def raw_callback(message: bytes, callback: Callable[[str], None]):
      callback(message.decode("utf-8"))

    self.warning_handle = _CALLBACK(functools.partial(raw_callback, callback=warning_callback))
    """The handle to the warning callback suitable to pass to C APIs.

    This will be None after the context manager has been exited.
    """
    self.error_handle = _CALLBACK(functools.partial(raw_callback, callback=error_callback))
    """The handle to the error callback suitable to pass to C APIs.

    This will be None after the context manager has been exited.
    """

  def __enter__(self) -> typing.Self:
    return self

  def __exit__(
    self,
    exc_type: type[BaseException] | None,
    exc_value: BaseException | None,
    traceback
  ) -> bool | None:
    self.warning_handle = None
    self.error_handle = None


class DataTransferApi(WrapperBase):
  """Access to the application data transfer API.

  This should be accessed through get_application_dlls() for new code.
  """
  @staticmethod
  def dll_name() -> str:
    return "mdf_datatransfer"

  @staticmethod
  def method_prefix():
    return "DataTransfer"

  def capi_functions(self):
    return [
      # Functions changed in version 0.
      # Format:
      # "name" : (return_type, arg_types)
      {},
      # Functions changed in version 1.
      {"DataTransferCApiVersion" : (ctypes.c_uint32, None),
       "DataTransferCApiMinorVersion" : (ctypes.c_uint32, None),
       "DataTransferImporterFor" : (dtfS_ImportOperation, [ctypes.c_char_p, ]),
       "DataTransferDeleteImporter" : (None, [dtfS_ImportOperation, ]),
       "DataTransferIsAtEndOfFile" : (ctypes.c_bool, [dtfS_ImportOperation, ]),
       "DataTransferGetNextObject" : (T_ObjectHandle, [dtfS_ImportOperation, ]),
       "DataTransferSupplyFileUnit" : (ctypes.c_uint8, [dtfS_ImportOperation, ctypes.c_uint32, ]),
       "DataTransferSupplyCoordinateSystem" : (ctypes.c_uint8, [dtfS_ImportOperation, ctypes.c_char_p, ctypes.POINTER(ctypes.c_double), ]),
       "DataTransferGetLastNameHint" : (ctypes.c_uint8, [dtfS_ImportOperation, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint32), ]),
       "DataTransferRequiredInputsSupplied" : (ctypes.c_uint8, [dtfS_ImportOperation, ctypes.POINTER(ctypes.c_bool), ]),
      }
    ]

  def CApiVersion(self):
    """Returns the API version for the datatransfer DLL."""
    raise_if_version_too_old("Data transfer", self.version, (1, 12))

    return self.dll.DataTransferCApiVersion()

  def CApiMinorVersion(self):
    """Returns the minor API version for the datatransfer DLL."""
    raise_if_version_too_old("Data transfer", self.version, (1, 12))

    return self.dll.DataTransferCApiMinorVersion()

  def ImporterFor(self, path: str) -> dtfS_ImportOperation:
    """Get an import operation for the file at path.

    Raises
    ------
    ValueError
      If importing the file at path is not supported.
    """
    raise_if_version_too_old("Data transfer", self.version, (1, 12))
    result: dtfS_ImportOperation = self.dll.DataTransferImporterFor(path.encode("utf-8"))
    if result.value in (0, None):
      raise ValueError(f"Importing file at {path} is not supported.")
    return result

  def DeleteImporter(self, importer: dtfS_ImportOperation):
    """Delete an import operation."""
    raise_if_version_too_old("Data transfer", self.version, (1, 12))
    self.dll.DataTransferDeleteImporter(importer)

  def IsAtEndOfFile(self, importer: dtfS_ImportOperation):
    """True if there are no more objects to import from `importer`."""
    raise_if_version_too_old("Data transfer", self.version, (1, 12))
    return self.dll.DataTransferIsAtEndOfFile(importer)

  def SupplyFeedbackTo(
    self,
    importer: dtfS_ImportOperation,
    error_callback: Callable[[str], None],
    warning_callback: Callable[[str], None]
  ) -> AbstractContextManager:
    """Make `importer` supply feedback using `error_callback` and `warning_callback`.

    Parameters
    ----------
    importer
      The importer which should supply feedback.
      This should be called before any objects are imported from the importer.
    error_callback
      The callback to call when an error occurs. This should accept a string
      and not return anything.
    warning_callback
      The callback to call when a warning occurs. This should accept a string
      and not return anything.

    Returns
    -------
    AbstractContextManager
      A context manager which will disable the warning and error callbacks when
      its __exit__() function is called (e.g. when the with block is exited).
      Importing an object with `importer` will raise an `OSError` if the
      context manager is exited before the import.
    """
    raise_if_version_too_old("Data transfer", self.version, (1, 12))
    feedback_handle = _FeedbackHandle(warning_callback, error_callback)

    result = self.dll.DataTransferSupplyFeedbackTo(
      importer,
      feedback_handle.error_handle,
      feedback_handle.warning_handle
    )
    if result != 0:
      warnings.warn(
        CApiUnknownWarning(
          "Failed to get feedback from import. Warnings and errors will not "
          f"be reported. Error code: {result}"
        )
      )
    return feedback_handle

  def GetNextObject(self, importer: dtfS_ImportOperation) -> T_ObjectHandle:
    """Import the next object from `importer`"""
    raise_if_version_too_old("Data transfer", self.version, (1, 12))
    return self.dll.DataTransferGetNextObject(importer)

  def SupplyFileUnit(self, importer: dtfS_ImportOperation, unit: DistanceUnit):
    """Supply `unit` as the unit for `importer`."""
    raise_if_version_too_old("Data transfer", self.version, (1, 12))
    result = self.dll.DataTransferSupplyFileUnit(
      importer,
      unit.value
    )

    if result == 3:
      raise ValueError(
        f"The application does not support: {unit}."
      )
    if result == 6:
      raise CApiInputNotSupportedError(
        "The import operation does not require a unit."
      )
    if result != 0:
      self.log.info("Failed to supply file unit. Error: %s", result)
      raise CApiUnknownError(
        "Failed to supply file unit."
      )

  def SupplyCoordinateSystem(self, importer: dtfS_ImportOperation, coordinate_system: CoordinateSystem | None):
    """Supply `coordinate_system` as the coordinate system for `importer`."""
    raise_if_version_too_old("Data transfer", self.version, (1, 12))
    try:
      if coordinate_system is not None:
        wkt = coordinate_system.crs.to_wkt(WktVersion.WKT2_2019).encode("utf-8")
        local_transform = (ctypes.c_double * 11)()
        local_transform[:] = coordinate_system.local_transform.to_numpy()
      else:
        wkt = None
        local_transform = None
    except AttributeError:
      raise TypeError(
        "Coordinate system was not a coordinate system"
      ) from None
    result = self.dll.DataTransferSupplyCoordinateSystem(
      importer,
      wkt,
      local_transform
    )

    if result == 3:
      raise ValueError(
        "The application could not parse the coordinate system."
      )
    if result == 4:
      raise CApiUnknownError(
        "Failed to find PROJ. The application may not support coordinate "
        "systems or the installation may be corrupt."
      )
    if result == 6:
      raise CApiInputNotSupportedError(
        "The import operation does not require a coordinate system."
      )
    if result != 0:
      self.log.info("Failed to supply coordinate system. Error: %s", result)
      raise CApiUnknownError(
        "Failed to supply coordinate system."
      )

  def GetLastNameHint(self, importer: dtfS_ImportOperation) -> str:
    """Get the name hint for the last object imported from `importer`."""
    raise_if_version_too_old("Data transfer", self.version, (1, 12))
    # 16 characters should be enough for most object names.
    buffer_length = ctypes.c_uint32(16)
    buffer = ctypes.create_string_buffer(buffer_length.value)
    result = self.dll.DataTransferGetLastNameHint(importer, buffer, buffer_length)
    if result == 0:
      # 16 characters was enough. Return the decoded name.
      return bytearray(buffer).decode("utf-8")[:buffer_length.value]
    if result != 5:
      raise CApiUnknownError("Failed to read the name of imported object.")

    # Buffer length has been set to the required buffer length.
    # Resize the buffer and retry getting the name hint.
    buffer = ctypes.create_string_buffer(buffer_length.value)
    result = self.dll.DataTransferGetLastNameHint(importer, buffer, buffer_length)
    if result != 0:
      raise CApiUnknownError("Failed to read the name of imported object.")
    return bytearray(buffer).decode("utf-8")[:buffer_length.value]

  def RequiredInputsSupplied(
    self,
    importer: dtfS_ImportOperation
  ) -> bool:
    """Returns True is `importer` has all required inputs supplied."""
    raise_if_version_too_old("Data transfer", self.version, (1, 12))

    required_inputs_supplied = ctypes.c_bool()
    result = self.dll.DataTransferRequiredInputsSupplied(importer, ctypes.byref(required_inputs_supplied))
    if result != 0:
      raise CApiUnknownError("Failed to determine if required inputs supplied.")
    return required_inputs_supplied.value
