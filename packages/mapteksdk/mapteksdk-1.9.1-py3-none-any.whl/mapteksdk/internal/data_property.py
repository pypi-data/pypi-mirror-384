"""Module containing class containing handling for per-primitive values."""
###############################################################################
#
# (C) Copyright 2022, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

from __future__ import annotations

import ctypes
from collections.abc import Callable, Sequence
import logging
import typing

import numpy as np

from .data_property_interface import DataPropertyInterface
from .lock import ReadLock, WriteLock, ObjectClosedError
from .util import array_from_pointer
from ..capi.types import T_ReadHandle, T_EditHandle
from ..data.errors import ReadOnlyError, CannotSaveInReadOnlyModeError

if typing.TYPE_CHECKING:
  import numpy.typing as npt

LOG = logging.getLogger("mapteksdk.data")

class DataPropertyConfiguration(typing.NamedTuple):
  """Class which contains the configuration of a DataProperty.

  These objects are immutable, which prevents accidental alterations to the
  configuration.
  """
  name: str
  """The name of the property.

  This is included in error messages.
  """

  dtype: type
  """The type of the data stored by the property.

  This should be a type from ctypes.
  """

  default: typing.Any | Sequence[typing.Any]
  """The default value of the property.

  This is used to fill the values array if it is expanded.

  If this is an instance of dtype, then when the values array is expanded,
  it will be filled with this value.

  If column_count != 1, this can be an iterable containing column count values.
  This allows for specifying a different default for each column. For example,
  for a colour property the default could be [red, green, blue, alpha]
  representing a default colour.
  """

  column_count: int
  """The number of columns the property's data has.

  If this is 1, the values of the property will be stored in a one dimensional
  array.
  If this is greater than 1, the values of the property will be stored in
  a two dimensional array of shape (N, column_count) where N is the value
  returned by the cached_primitive_count_function.
  """

  load_function: Callable[[T_ReadHandle], ctypes.c_void_p] | None
  """Function to get a read-only array from the Project.

  This should be a function with accepts a read handle and returns the
  pointer to the start of the array. The DataProperty class handles
  converting this to a numpy array.
  """

  save_function: Callable[[T_EditHandle], ctypes.c_void_p] | None
  """Function to get a read/write array from the Project.

  This should be a function which accepts an edit handle and returns the
  pointer to the start of the array. The DataProperty class handles
  writing the values to this array and potentially resizing it if
  set_primitive_count_function is provided.
  """

  primitive_count_function: Callable[[T_ReadHandle], int]
  """Function to read the primitive count from the Project.

  This returns the number of primitives in the object, which is used to
  determine the length of the array returned by load_function.

  Notes
  -----
  load_function is assumed to return an array of length:

  >>> primitive_count_function() * column_count

  The primitive_count_function() can be the same function for all properties
  associated with the same primitive.
  """

  cached_primitive_count_function: Callable[[], int] | None
  """Function to read the current primitive count.

  If this is None, then this object defines its own primitive count based
  on the length of the values array. The values array is allowed to resize
  (though the dimensionality and column count are still fixed by column_count)
  by assigning longer or shorter arrays to it.

  If this is a function, the values array for this property will always have
  N rows where N is the return value of this function. Attempting to assign
  the values to an array with a different number of rows will raise a
  ValueError. If the return value of this function changes, the next time the
  arrays are read they will be trimmed or padded with default values.

  Warnings
  --------
  If cached_primitive_count_function is None, then set_primitive_count_function
  should not be None.
  """

  set_primitive_count_function: Callable[
    [T_ReadHandle, int], None] | None=None
  """Function to set the primitive count for this type of primitive.

  This is used to resize the property arrays if new primitives are added to
  the object, or if primitives are removed from the object.

  If None, then the SDK will not attempt to resize the property arrays
  if this property changes length.

  If this is a function, then on save if the primitive_count_function and the
  cached_primitive_count function return different values, this will be
  called to update the primitive count.

  Notes
  -----
  This should only be a function for properties which define the primitives
  (e.g. points, edges, facets, cells, blocks or tetras); otherwise the primitive
  arrays will  be resized multiple times to the same size (which shouldn't be an
  issue but it is inefficient).

  Warnings
  --------
  If set_primitive_count_function is None, then cached_primitive_count_function
  should not be None.
  """

  is_colour_property : bool=False
  """If this property stores colour values.

  If False (default), colour-specific handling is disabled.

  If True, then row_count should be 4 and dtype should be ctypes.c_uint8.
  Colour specific handling (e.g. handling RGB vs RGBA colours) will be enabled.
  """

  immutable: bool=False
  """If this property is immutable.

  If False (default), if the lock type is read/write this property will
  accept edits to the values array.
  If True, attempting to edit the values array will always raise an error.
  """

  raise_on_error_code: Callable[[], None] | None = None
  """Function to raise an exception after failing to read a pointer.

  If not None, this function will be called if load_function returns a null
  pointer. It is expected to raise an appropriate exception.
  """


class DataProperty(DataPropertyInterface):
  """Handles caching properties of objects with per-primitive values.

  This class represents a property which is associated with a primitive.
  Typically such properties have one value for each primitive in the object.

  This handles:
  * Populating numpy arrays from the arrays returned by the C API.
  * Caching the array to avoid repeated calls to the C API.
  * If writeable, writing the changes made to the array back via the C API.
  * Resizing the arrays if the primitive count changes and this property
    determines the primitive count for the object.

  This class uses the following terms:
  primary property
    A property which makes sense on its own (e.g. points). Such properties
    define the primitive count for the object (e.g. points defines the
    point count).

  secondary property
    A property which depends on another property. The number of values in
    a secondary property is defined by a primary property (e.g. point_colours
    defines its size based on the points property).

  Parameters
  ----------
  lock
    The lock on the object which has the properties.
  configuration
    The configuration of this property.
  initial_values
    Initial values to assign to the property. This allows values to be
    assigned to read-only properties during construction.
  """
  def __init__(
      self,
      lock: ReadLock | WriteLock,
      configuration: DataPropertyConfiguration,
      initial_values: npt.ArrayLike | None=None):
    self.__lock: ReadLock | WriteLock = lock
    """The lock on the object which contains this property."""
    self.configuration: DataPropertyConfiguration = configuration
    """The configuration of this property."""

    self.__values: np.ndarray | None = None
    """Caching field for the values."""

    if initial_values is not None:
      if self.read_only:
        # If the array is immutable, bypass the setter because it would raise
        # an error.
        if self.primitive_count == -1:
          self.__set_values_variable_length_array(initial_values)
        else:
          self.__set_values_fixed_length_array(initial_values)
      else:
        self.values = initial_values

  @property
  def name(self) -> str:
    return self.configuration.name

  @property
  def are_values_cached(self) -> bool:
    return self.__values is not None

  @property
  def read_only(self) -> bool:
    if self.configuration.immutable:
      return True
    return not isinstance(self.__lock, WriteLock)

  @property
  def primitive_count(self) -> int:
    """The number of primitives in the object.

    If this is greater than zero, then this is the number of rows which
    will be in the values array.

    If this is -1, then this property defines the primitive count for this
    type of primitive. The values array can have any number of rows.
    """
    if self.configuration.cached_primitive_count_function is None:
      return -1
    return self.configuration.cached_primitive_count_function()

  @property
  def shape(self) -> tuple:
    if self.is_2d:
      return (self.primitive_count, self.column_count)
    return (self.primitive_count,)

  @property
  def column_count(self) -> int:
    """The number of values for each primitive in the values array.

    If this is 1, then the values array will be one dimensional.
    If this is greater than 1, then the values array will be two dimensional.

    Examples
    --------
    A colour has a red, green, blue and alpha component for each primitive.
    This means four values per primitive, so the column_count would be 4.

    A visibility array has one value for each primitive, so the column_count
    would be 1.
    """
    return self.configuration.column_count

  @property
  def is_2d(self) -> bool:
    """True if this property's values is a 2D array."""
    return self.column_count > 1

  @property
  def values(self) -> np.ndarray:
    if not self.are_values_cached:
      self.__values = self._load()
      self.__values.flags.writeable = not self.read_only

    if self.primitive_count != -1 and self._values_needs_resizing():
      # This can't use np.full(), because the default may be an iterable.
      new_values = self._construct_empty_array()
      new_values[:] = self.configuration.default
      old_values = typing.cast(np.ndarray, self.__values)
      # The two arrays should have the same number of columns.
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

    if self.configuration.immutable:
      raise ReadOnlyError(
        f"The '{self.name}' property does not support assignment.")

    if not isinstance(self.__lock, WriteLock):
      raise ReadOnlyError(
        f"Cannot edit '{self.name}' in read-only mode."
      )

    if self.__lock.is_closed:
      raise ObjectClosedError()

    if self.primitive_count == -1:
      self.__set_values_variable_length_array(new_values)
    else:
      self.__set_values_fixed_length_array(new_values)

  def invalidate(self):
    if self.are_values_cached:
      self.values = None

  def _load(self) -> np.ndarray:
    """Load the values from the C API.

    This returns a numpy array containing a copy of the values read from the
    C API. This does not trim or pad the array.

    Returns
    -------
    np.ndarray
      The values for this property read from the Project.
      Given M is the primitive count returned by the primitive count
      function:
      If self.column_count == 1 this will return an array of shape (M,)
      If self.column_count != 1 this will return an array of shape
      (M, self.column_count).
    """
    if self.configuration.load_function is not None:
      point_count = self.configuration.primitive_count_function(
        self.__lock.lock)
      value_count = point_count * self.column_count
      ptr = self.configuration.load_function(self.__lock.lock)

      if not ptr and self.configuration.raise_on_error_code:
        try:
          self.configuration.raise_on_error_code()
        except MemoryError as error:
          LOG.error("Failed to read the %s attribute: %s",
                    self.name, str(error))
          raise MemoryError(
            "The attribute could not fit in the Project's cache") from None
        except:
          LOG.exception("Failed to read the attribute '%s'",
                        self.name)
          raise

      # :TRICKY: This makes a copy so that the array can still be accessed
      # after the object has been closed.
      # The pointer above will be invalidated when the object is closed and thus
      # accessing it would crash the script.
      array = array_from_pointer(
        ptr,
        value_count,
        self.configuration.dtype,
      ).copy()
    else:
      array = np.empty((0,), self.configuration.dtype)

    array.setflags(write=isinstance(self.__lock, WriteLock))

    if self.is_2d:
      # Reshape the array to have the right number of columns and
      # as many rows as needed.
      # The caller handles changing the number of rows.
      array.shape = (-1, self.column_count)
    return array

  def save(self):
    if self.read_only:
      raise CannotSaveInReadOnlyModeError()

    if self.configuration.save_function is None:
      raise NotImplementedError("This property does not support saving")

    if not self.are_values_cached:
      # The values are not cached, so we don't need to save any changes.
      return

    current_count = self.values.shape[0]

    # set_primitive_count_function should only be set for primary properties
    # (e.g. points) so there should only be one call to it for each primitive
    # type when the object is saved.
    if self.configuration.set_primitive_count_function:
      # If the count hasn't changed, no need to update it.
      backend_count = self.configuration.primitive_count_function(
        self.__lock.lock)
      if backend_count != current_count:
        self.configuration.set_primitive_count_function(
          self.__lock.lock, current_count)

    value_count = current_count * self.column_count
    coords = array_from_pointer(
      self.configuration.save_function(self.__lock.lock),
      value_count,
      self.configuration.dtype)
    # :TRICKY: If a secondary property is saved before the associated primary
    # property, this will write off the end of the array, which is undefined
    # behaviour.
    coords[:] = self.values.reshape(-1)

  def _construct_empty_array(self) -> np.ndarray:
    """Construct a correctly shaped but empty properties array."""
    return np.empty(
      shape=self.shape,
      dtype=self.configuration.dtype
    )

  def _values_needs_resizing(self) -> bool:
    """True if the values array needs resizing."""
    if self.__values is not None:
      return self.__values.shape != self.shape
    return True

  def __set_values_fixed_length_array(self, new_values: npt.ArrayLike):
    """Set the values when the values array is fixed length.

    This does not check that if the values array is read-only so can be
    used internally for the initial population of a read-only values array.

    Parameters
    ----------
    new_values
      The new values for the array.

    Raises
    ------
    ValueError
      If new values cannot be broadcast to the right shape or if it cannot
      be converted to the right type.
    """
    if (isinstance(new_values, np.ndarray)
        and new_values.dtype == self.configuration.dtype
        and new_values.shape == self.shape):
      self.__values = new_values
      self.__values.flags.writeable = not self.read_only
      return

    # Backing array is effectively a pointer to the array to assign the
    # values to. This is used to ensure no changes are made to the values
    # if an error occurs (e.g. If new_values cannot be broadcast to the
    # correct shape or a value cannot be converted to the correct type).
    backing_array: np.ndarray = typing.cast(np.ndarray, self.__values)
    # If the array isn't cached or if it needs to be resized.
    if not self.are_values_cached or self._values_needs_resizing():
      # :TRICKY: Assigning the empty array directly to self.__values
      # would mean that if an error occurred then the values array
      # would be mutated to an uninitialised array.
      backing_array = self._construct_empty_array()

    try:
      backing_array[:] = new_values
      self.__values = backing_array
      self.__values.flags.writeable = not self.read_only
    except ValueError:
      if self.configuration.is_colour_property:
        # Handle RGB colours.
        backing_array[:, :3] = new_values
        backing_array[:, 3] = 255
        self.__values = backing_array
        self.__values.flags.writeable = not self.read_only
      else:
        raise

  def __set_values_variable_length_array(self, new_values: npt.ArrayLike):
    """Set the values when the array is variable length.

    Parameters
    ----------
    new_values
      The new values for the array.

    Raises
    ------
    ValueError
      If new values cannot be broadcast to the right shape or if it cannot
      be converted to the right type.
    """
    if not isinstance(new_values, np.ndarray):
      new_values = np.asarray(
        new_values,
        dtype=self.configuration.dtype)

    if not self.is_2d and new_values.ndim != 1:
      raise ValueError(
        f"Cannot assign {new_values.ndim}D array to {self.name} property. "
        "This property is 1D.")
    if self.is_2d:
      if new_values.ndim != 2:
        raise ValueError(
          f"Cannot assign {new_values.ndim}D array to {self.name} property. "
          "This property is 2D.")
      if new_values.shape[1] != self.column_count:
        raise ValueError(
          f"Cannot assign array with {new_values.shape[1]} columns to "
          f"{self.name} because it has {self.column_count} "
          "columns.")

    if new_values.dtype != self.configuration.dtype:
      # :TRICKY: This will usually make a copy even if copy is set to False.
      # e.g. If new_values.dtype is int and self.__dtype is ctypes.c_double,
      # a copy will be made.
      # e.g. If new_values.dtype is int and the values are all 0 or 1
      # and self.__dtype is ctypes.c_bool this won't make a copy, because
      # the change to the dtype can be done by interpreting the data in
      # a different way.
      new_values = np.asarray(new_values,
                              dtype=self.configuration.dtype)
    new_values.shape = self.shape
    new_values.flags.writeable = not self.read_only

    self.__values = new_values
