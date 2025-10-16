"""Module containing read-only singular data property."""
###############################################################################
#
# (C) Copyright 2023, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
  from collections.abc import Callable

T = typing.TypeVar("T")

NOT_CACHED = None
"""Placeholder indicating that a property is not cached."""

# :TODO: Can this share an interface with DataProperty?
class SingularDataPropertyReadOnly(typing.Generic[T]):
  """A read-only data property which holds a single value.

  This handles caching the value and clearing it.

  Parameters
  ----------
  name
    The name of this property.
  load_parameters
    Function which when called will return a list of parameters
    to pass to load_function.
  load_function
    Function which when passed the parameters returned by
    load_parameters will load the value.
  """
  def __init__(
      self,
      name : str,
      load_parameters: Callable[[], list[typing.Any]],
      load_function: Callable[..., T]):
    self.__name = name
    self._load_parameters = load_parameters
    self.__load_function = load_function
    self._value: T | None = NOT_CACHED

  @property
  def name(self) -> str:
    """The name of this property.

    This is included in error messages to identify which property the
    error occurred in.
    """
    return self.__name

  @property
  def are_values_cached(self) -> bool:
    """True if the values have been cached.

    If this returns False, then accessing the values property will cause the
    values to be read from the Project.
    """
    return self._value is not NOT_CACHED

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
    This will return True if the object is open for reading only.
    """
    return True

  def invalidate(self):
    """Clears the cached array if it exists."""
    self._value = None

  def save(self):
    """Save the values back to the application via the C API.

    If the number of values in a property depends on another property,
    it should be saved after that property to ensure that the arrays are
    resized properly (e.g. the point colours must be saved after the points).

    Raises
    ------
    CannotSaveInReadOnlyModeError
      If this property is read-only and save is called.
    """

  @property
  def value(self) -> T:
    """The value stored in this property.

    This will load the value from the application if it is not cached.

    Returns
    -------
    Any
      The value stored in this property.
    """
    if self._value is NOT_CACHED:
      self._value = self.__load_function(*self._load_parameters())
    assert self._value is not None
    return self._value
