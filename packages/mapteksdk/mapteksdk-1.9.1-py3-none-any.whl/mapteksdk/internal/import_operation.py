"""Wrapper around the DataTransfer C API."""
###############################################################################
#
# (C) Copyright 2024, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

from contextlib import AbstractContextManager
import pathlib
import typing
import warnings

from ..data import ObjectID, CoordinateSystem, DistanceUnit
from ..data.typing import ImportedObject
from ..errors import (
  FileImportWarning,
  FileImportError,
  ImportFormatNotSupportedError,
)
from .util import default_type_error_message

if typing.TYPE_CHECKING:
  from collections.abc import Sequence

  from ..capi import DataTransferApi

class ImportOperation(AbstractContextManager):
  """Represents an operation which imports objects from a single file.

  This should always be used in a context manager to ensure that the file
  is closed and to prevent memory leaks.

  Parameters
  ----------
  path
    The path to the file to import objects from.

  Raises
  ------
  ImportFormatNotSupportedError
    If importing the file at `path` is not supported.
  FileNotFoundError
    If there is no file at `path`.
  """
  def __init__(
    self,
    path: pathlib.Path,
    *,
    data_transfer: DataTransferApi
  ) -> None:
    if not path.exists():
      # The import framework treats a non-existent file as a file which
      # contains no objects. To get a file not found error this looks
      # before it leaps.
      raise FileNotFoundError(
        f"The file '{path}' cannot be accessed or does not exist."
      )
    self.path = path
    self.__deleted = False
    self.__data_transfer = data_transfer
    try:
      self.__import_operation = self.__data_transfer.ImporterFor(str(path))
    except ValueError:
      raise ImportFormatNotSupportedError.from_path(path) from None

  def __enter__(self) -> typing.Self:
    return self

  def __exit__(
    self,
    exc_type: type[BaseException] | None,
    exc_value: BaseException | None,
    traceback
  ) -> bool | None:
    if self.__deleted:
      return
    self.__deleted = True
    self.__data_transfer.DeleteImporter(self.__import_operation)

  def supply_coordinate_system(
    self,
    coordinate_system: CoordinateSystem | None
  ):
    """Supply coordinate system to this import operation.

    This only marks the imported objects as being in the specified coordinate
    system. It does not perform any transformation on the object.
    If coordinate system is None, the importer will not set any coordinate
    system to the imported objects.

    Raises
    ------
    TypeError
      If coordinate_system is not a coordinate system.
    ValueError
      If the application does not support coordinate system.
    CApiInputNotSupportedError
      If this import operation does not support coordinate systems.
      This typically indicates developer mistakes.
    """
    if not isinstance(coordinate_system, (CoordinateSystem, type(None))):
      raise TypeError(
        default_type_error_message(
          "coordinate_system", coordinate_system, CoordinateSystem
        )
      )
    self.__data_transfer.SupplyCoordinateSystem(
      self.__import_operation,
      coordinate_system
    )

  def supply_unit(self, unit: DistanceUnit):
    """Supply unit to this import operation."""
    if not isinstance(unit, DistanceUnit):
      raise TypeError(
        default_type_error_message(
          "unit", unit, DistanceUnit
        )
      )
    self.__data_transfer.SupplyFileUnit(self.__import_operation, unit)

  def are_required_inputs_supplied(self) -> bool:
    """Query if required inputs have been supplied.

    If this returns False, then calling `import_all_objects()` will fail
    due to missing inputs.

    Calling this is optional. Most callers will know what inputs are required,
    so can skip calling this function.
    """
    return self.__data_transfer.RequiredInputsSupplied(self.__import_operation)

  def import_all_objects(self) -> Sequence[ImportedObject[typing.Any]]:
    """Import all objects from the file.

    Raises
    ------
    FileImportError
      If the import encounters an error.

    Warns
    -----
    FileImportWarning
      If the import encounters a non-fatal error.
    """
    oids: Sequence[ImportedObject[typing.Any]] = []
    warning_messages = []
    error_messages = []
    def error_callback(message: str):
      # This can't raise the error because it will be called from C++ code.
      error_messages.append(message)
    def warning_callback(message: str):
      # This can't emit the warning because it will be called from C++ code.
      warning_messages.append(message)

    with self.__data_transfer.SupplyFeedbackTo(
      self.__import_operation,
      error_callback,
      warning_callback
    ):
      try:
        while not self.__data_transfer.IsAtEndOfFile(self.__import_operation):
          handle = self.__data_transfer.GetNextObject(self.__import_operation)
          if error_messages or handle.value == 0:
            # A null handle means the import has failed but the C++ code failed
            # to provide an error message.
            raise FileImportError.from_error_message(self.path, error_messages)
          last_name = self.__data_transfer.GetLastNameHint(
            self.__import_operation)

          if not last_name:
            # If the name is blank, use the file name without the suffix.
            last_name = self.path.stem
          oids.append(ImportedObject(last_name, ObjectID(handle)))
      finally:
        if warning_messages:
          warnings.warn(
            FileImportWarning.from_warning_message(self.path, warning_messages),
            # This is usually called from library code. To avoid including that
            # in the stack trace, report the warning as coming from the caller
            # of the caller.
            stacklevel=3
          )
      return oids
