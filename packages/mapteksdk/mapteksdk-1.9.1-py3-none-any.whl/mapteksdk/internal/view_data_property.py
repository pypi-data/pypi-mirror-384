"""Module containing data property which is a view onto another property."""
###############################################################################
#
# (C) Copyright 2023, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import typing

import numpy as np

from ..data.errors import ReadOnlyError
from .data_property import DataPropertyInterface

if typing.TYPE_CHECKING:
  from collections.abc import Callable

  import numpy.typing as npt

class ViewDataPropertyConfiguration(typing.NamedTuple):
  """Configuration for a view data property.

  A view data property provides a view of the data stored in another
  data property in a different shape.
  """
  name: str
  """Name of this data property."""
  parent_property: DataPropertyInterface
  """The data property to read values from."""
  new_shape: Callable[[], tuple[int, ...]]
  """The shape to reshape the parent property's data to."""

class ViewDataProperty(DataPropertyInterface):
  """A data property which provides a view of another property.

  A view data property does not have its own values. Instead it provides
  a view of the values of another data property with a different shape.
  For example, this can be used to provide a 2 dimensional representation
  for a property based on the default 1 dimensional flattened representation of
  multi-dimensional data provided by the C APIs.

  Notes
  -----
  As this provides a view of the values of another property, changes
  to that property change the values of the view property and vice versa.
  """
  def __init__(self, configuration: ViewDataPropertyConfiguration) -> None:
    self.__configuration = configuration
    """Configuration of this object."""
    self.__view = None
    """Backing array for the view."""

  @property
  def name(self) -> str:
    return self.__configuration.name

  @property
  def are_values_cached(self) -> bool:
    if self.__view is None:
      # The view array being None indicates the array has not been
      # accessed (or it has been invalidated), therefore it must not
      # be cached.
      return False
    if not self.__configuration.parent_property.are_values_cached:
      # If the parent property's values array is not cached, then there
      # cannot be any views onto that array.
      # This catches the case where the parent property's array is
      # invalidated, resulting in self.__view being a view of an
      # invalidated array.
      return False
    if not np.may_share_memory(self.__view, self._parent_values):
      # If the view array doesn't share memory with the parent array,
      # then the view has been invalidated and therefore there are no
      # values cached.
      return False
    return True

  @property
  def read_only(self) -> bool:
    return self.__configuration.parent_property.read_only

  @property
  def shape(self) -> tuple:
    return self.__configuration.new_shape()

  @property
  def values(self) -> np.ndarray:
    if not self.are_values_cached or self.__view.shape != self.shape:
      # If the values are not cached, generate a new view onto the
      # parent array.
      # :NOTE: The values are not considered cached if the values
      # array has been invalidated.
      self.__view = self._parent_values[:].reshape(self.shape)
    return self.__view

  @values.setter
  def values(self, new_values: npt.ArrayLike):
    if self.read_only:
      raise ReadOnlyError(f"Cannot edit '{self.name}' in read-only mode.")
    self.values[:] = new_values

  @property
  def _parent_values(self) -> np.ndarray:
    return self.__configuration.parent_property.values

  def invalidate(self):
    self.__view = None

  def save(self):
    # This property provides a view to the values of another property,
    # so there is nothing to save.
    pass
