"""Module containing abstract base class for handling per-primitive values."""
###############################################################################
#
# (C) Copyright 2022, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import typing

import numpy as np

if typing.TYPE_CHECKING:
  import numpy.typing as npt

class DataPropertyInterface:
  """Base class for properties with one value per-primitive.

  Classes which implement this interface represent a property with one value
  for each primitive of a particular type.

  Implementing classes are expected to handle:
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
  """
  @property
  def name(self) -> str:
    """The name of this property.

    This is included in error messages to identify which property the
    error occurred in.
    """
    raise NotImplementedError("Must be implemented in child classes.")

  @property
  def are_values_cached(self) -> bool:
    """True if the values have been cached.

    If this returns False, then accessing the values property will cause the
    values to be read from the Project.
    """
    raise NotImplementedError("Must be implemented in child classes.")

  @property
  def read_only(self) -> bool:
    """If this property is read-only.

    If True:

    * Attempting to assign a new array to the values property will raise
      a ReadOnlyError.
    * Attempting to assign to an element in the values property will raise
      a ValueError.

    If False, edits to the values property will not raise an error.

    Notes
    -----
    This will return True if the object is not open for editing.
    """
    raise NotImplementedError("Must be implemented in child classes.")

  @property
  def shape(self) -> tuple:
    """The shape of the values array.

    One item in the returned tuple may be a -1 indicating that the
    size in that dimension is not specified.
    """
    raise NotImplementedError("Must be implemented in child classes.")

  @property
  def values(self) -> np.ndarray:
    """The values of this property.

    When read, if the values are not already cached, they will be read from
    the Project.

    Also, if the backing array's shape does not match self.shape, the
    values array will be resized when the values are accessed.
    """
    raise NotImplementedError("Must be implemented in child classes.")

  @values.setter
  def values(self, new_values: npt.ArrayLike):
    raise NotImplementedError("Must be implemented in child classes.")

  def invalidate(self):
    """Clears the cached array if it exists."""
    raise NotImplementedError("Must be implemented in child classes.")

  def save(self):
    """Save the values back to the application.

    If the number of values in a property depends on another property,
    it should be saved after that property to ensure that the arrays are
    resized properly (e.g. the point colours must be saved after the points).

    Raises
    ------
    CannotSaveInReadOnlyModeError
      If this property is read-only and save is called.
    """
    raise NotImplementedError("Must be implemented in child classes.")
