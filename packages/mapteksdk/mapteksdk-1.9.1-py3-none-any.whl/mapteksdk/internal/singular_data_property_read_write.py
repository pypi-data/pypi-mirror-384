"""Module containing read-write singular data property."""
###############################################################################
#
# (C) Copyright 2023, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import typing

from ..data.errors import ReadOnlyError, CannotSaveInReadOnlyModeError
from .singular_data_property_read_only import (
  SingularDataPropertyReadOnly)

if typing.TYPE_CHECKING:
  from collections.abc import Callable

T = typing.TypeVar("T")

class SingularDataPropertyReadWrite(SingularDataPropertyReadOnly[T]):
  """An editable data property which holds a single value.

  This handles caching the value and clearing it.

  Parameters
  ----------
  name
    The name of this property.
  load_parameters
    Function which when called will return the parameters required to
    load or save the values.
    When saving this property, the current value of the property will be
    appended to the list returned by this function.
    This should raise an appropriate error if it detects that load will
    fail if passed the parameters it would return (e.g. If the parameters
    includes a lock and that lock has already been closed).
  read_only
    If the object is open for read-only and thus editing should be disabled.
  load_function
    Function which when passed the parameters returned from load_function()
    will return the current value of this property.
  save_function
    Function which when passed the parameters returned from load_function()
    and the cached value will save the cached value.
  """
  def __init__(
      self,
      name : str,
      load_parameters: Callable[[], list[typing.Any]],
      read_only: bool,
      load_function: Callable[..., T],
      save_function: Callable[..., None]):
    super().__init__(name, load_parameters, load_function)
    self.__save_function = save_function
    self.__read_only = read_only

  @property
  def read_only(self) -> bool:
    return self.__read_only

  @property
  def value(self) -> T:
    return super().value

  @value.setter
  def value(self, new_value: T):
    if self.read_only:
      raise ReadOnlyError(f"Cannot edit '{self.name}' in read-only mode.")
    # The load parameters function should fail if the lock is closed,
    # so call it here to check.
    _ = self._load_parameters()
    self._value = new_value

  def save(self):
    if self.read_only:
      raise CannotSaveInReadOnlyModeError()
    if self.are_values_cached:
      parameters = self._load_parameters()
      parameters.append(self.value)
      self.__save_function(*parameters)
