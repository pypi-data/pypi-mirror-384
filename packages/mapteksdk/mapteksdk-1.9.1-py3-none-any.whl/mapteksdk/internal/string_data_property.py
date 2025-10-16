"""Module containing class which handles string per-primitive values."""
###############################################################################
#
# (C) Copyright 2022, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

from __future__ import annotations

from collections.abc import Callable
import typing

import numpy as np

from .data_property_interface import DataPropertyInterface
from .lock import ReadLock, WriteLock, ObjectClosedError
from ..capi.types import T_ReadHandle, T_EditHandle
from ..data.errors import ReadOnlyError, CannotSaveInReadOnlyModeError

if typing.TYPE_CHECKING:
  import numpy.typing as npt
  from ..common.typing import StringArray

class StringDataPropertyConfiguration(typing.NamedTuple):
  """Configuration for a string data property.

  This contains less options than DataPropertyConfiguration because
  less functionality is implemented for string data properties.
  """
  name: str
  """The name of the property.

  This is included in error messages.
  """

  default: str
  """The default value of the property.

  This is used to fill the values array if it is expanded.
  """

  load_function: Callable[[T_ReadHandle], StringArray]
  """Function to get a read-only array from the Project.

  This should be a function with accepts a read handle and returns the
  a numpy array of strings.
  """

  save_function: Callable[[T_EditHandle, StringArray], None]
  """Function to get a read/write array from the Project.

  This should be a function which accepts an edit handle and a numpy
  array of strings and performs the save operation.
  """

  primitive_count_function: Callable[[T_ReadHandle], int]
  """Function to read the primitive count from the Project.

  This returns the number of primitives in the object, which is used to
  determine the length of the array returned by load_function.
  """

  cached_primitive_count_function: Callable[[], int] | None
  """Function to read the current primitive count.

  The values array for this property will always have N values where N is the
  return value of this function.
  If the return value of this function changes, the next time the
  array is read it will be trimmed or padded with default values.

  If None, this property defines the primitive count for the object.
  """

class StringDataProperty(DataPropertyInterface):
  """Handles caching properties of objects with per-primitive values.

  This object contains specific handling for properties with one string
  per primitive.

  See Also
  --------
  DataProperty : Handling for properties with per-primitive numeric values.

  Parameters
  ----------
  lock
    The lock on the object which has the properties.
  configuration
    The configuration of this property.
  initial_values
    The initial values for this property. This bypasses the normal check
    for setting the values, so must be a valid array.
  """
  def __init__(
      self,
      lock: ReadLock | WriteLock,
      configuration: StringDataPropertyConfiguration,
      initial_values: StringArray | None=None):
    self.__lock: ReadLock | WriteLock = lock
    """The lock on the object which contains this property."""

    self.configuration: StringDataPropertyConfiguration = configuration
    """The configuration of this property."""

    self.__values: StringArray | None = initial_values
    """Caching field for the values."""

  @property
  def name(self) -> str:
    return self.configuration.name

  @property
  def are_values_cached(self) -> bool:
    return self.__values is not None

  @property
  def read_only(self) -> bool:
    return not isinstance(self.__lock, WriteLock)

  @property
  def primitive_count(self) -> int:
    """The number of primitives in the object.

    If this is greater than zero, then this is the number of rows which
    will be in the values array.

    If this is -1, then this property defines the primitive count for this
    type of primitive. The values array can have any number of rows.
    """
    if self.configuration.cached_primitive_count_function:
      return self.configuration.cached_primitive_count_function()
    return -1

  @property
  def shape(self) -> tuple:
    return (self.primitive_count,)

  @property
  def values(self) -> StringArray:
    if not self.are_values_cached:
      if self.primitive_count == -1:
        # If the values aren't cached and the primitive count is -1, then the
        # object is currently empty.
        # Return an empty string array.
        self.__values = np.empty((0,), dtype=np.str_)
      else:
        self.__values = self.configuration.load_function(self.__lock.lock)
        self.__values.flags.writeable = not self.read_only

    if self.primitive_count != -1 and self._values_needs_resizing():
      old_values = typing.cast(np.ndarray, self.__values)
      # Pass the item size to construct empty array to ensure it is filled
      # with long enough strings.
      new_values = self._construct_empty_array(
        self._max_array_string_length(old_values))
      new_values[:] = self.configuration.default
      # Copy the existing values to the new array.
      values_to_copy = min(self.shape[0], old_values.shape[0])
      new_values[:values_to_copy] = old_values[:values_to_copy]
      new_values.flags.writeable = not self.read_only
      self.__values = new_values

    return typing.cast(np.ndarray, self.__values)

  @values.setter
  def values(self, new_values: npt.ArrayLike | None):
    # Assigning to None is allowed on a read-only property because it
    # clears the cached values of the property.
    if new_values is None:
      self.__values = None
      return

    if self.read_only:
      raise ReadOnlyError(
        f"The {self.name} property does not support assignment.")

    if self.__lock.is_closed:
      raise ObjectClosedError()

    # A dtype kind of "U" indicates UTF-32 strings.
    if (isinstance(new_values, np.ndarray)
        and new_values.dtype.kind == "U"
        and new_values.shape == self.shape):
      self.__values = new_values
      self.__values.flags.writeable = not self.read_only
      return

    if not isinstance(new_values, np.ndarray):
      new_values = np.array(new_values, dtype=np.str_)

    # This dtype is not recommended by the numpy documentation.
    if new_values.dtype.kind == "S":
      raise ValueError("Zero-terminated byte arrays are not supported.")

    # The kind could also be "O" which is an array of Python objects.
    # This will convert them into strings.
    if new_values.dtype.kind != "U":
      new_values = new_values.astype(np.str_)

    new_max_string_length = self._max_array_string_length(new_values)

    # Backing array is effectively a pointer to the array to assign the
    # values to. This is used to ensure no changes are made to the values
    # if an error occurs (e.g. If new_values cannot be broadcast to the
    # correct shape or a value cannot be converted to the correct type).
    backing_array = self.__values

    if self.primitive_count == -1:
      if new_values.ndim != 1:
        raise ValueError(
          f"Invalid number of dimensions for '{self.name}' "
          f"New array is {new_values.ndim}d, but must be 1d.")
      self.__values = new_values
    else:
      if self.are_values_cached:
        current_values = typing.cast(np.ndarray, self.__values)
        # The array will need to be resized if the new array contains
        # longer strings than can fit in the current array.
        current_max_string_length = self._max_array_string_length(
          current_values)
        if (self._values_needs_resizing()
            or new_max_string_length > current_max_string_length):
          backing_array = self._construct_empty_array(new_max_string_length)
      else:
        backing_array = self._construct_empty_array(new_max_string_length)

      assert backing_array is not None
      backing_array[:] = new_values
      self.__values = backing_array
      self.__values.flags.writeable = not self.read_only

  def invalidate(self):
    if self.are_values_cached:
      self.values = None

  def save(self):
    if self.read_only:
      raise CannotSaveInReadOnlyModeError()

    if not self.are_values_cached:
      # The values are not cached, so don't need to save any changes.
      return

    self.configuration.save_function(self.__lock.lock, self.values)

  def _max_array_string_length(self, array: StringArray) -> int:
    """Returns the maximum length string which can be stored in the array.

    This reads the maximum string length from the array's datatype.
    """
    # Numpy stores string arrays in UTF-32 because it is a fixed length
    # format (unlike UTF-8 and UTF-16). The itemsize is the number of
    # bytes allocated per string, so divide it by 4 to get the maximum
    # number of characters per string.
    return array.dtype.itemsize // 4

  def _construct_empty_array(self, max_string_length: int) -> StringArray:
    """Constructs an appropriately shaped empty array.

    Parameters
    ----------
    max_string_length
      The maximum number of characters allowed in strings in the new
      empty array.

    Returns
    -------
    np.ndarray
      Numpy array of shape self.shape containing strings which can be
      up to max_string_length long.
    """
    # A dtype of U{number} is an array which contains strings of length
    # {number}. For example, U25 indicates string of length 25.
    dtype = np.dtype(f"U{max_string_length}")
    return np.empty(self.shape, dtype)

  def _values_needs_resizing(self) -> bool:
    """True if the values array needs resizing."""
    if self.__values is not None:
      return self.__values.shape != self.shape
    return True
