"""Mixin for adding two sided colouring to an object."""
###############################################################################
#
# (C) Copyright 2022, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import ctypes
import typing

import numpy as np

if typing.TYPE_CHECKING:
  from ..capi import ModellingApi

  from .lock import ReadLock, WriteLock

class TwoSidedColouringMixin:
  """Add two sided colouring to a DataObject subclass."""
  __back_colour: np.ndarray | None = None
  __has_front_colour: bool | None = None
  __has_back_colour: bool | None = None

  if typing.TYPE_CHECKING:
    _lock: WriteLock | ReadLock

    @classmethod
    def _modelling_api(cls) -> ModellingApi:
      raise NotImplementedError

  @property
  def _has_front_colour(self) -> bool:
    """If the object has a front colour.

    If True, the front of facets will be coloured using point, edge,
    facet, etc colours.
    If False, the front of facets will be coloured the back colour.
    """
    if self.__has_front_colour is None:
      self.__has_front_colour = self._modelling_api().HasTopologyFrontColour(
        self._lock.lock)
    return self.__has_front_colour

  @property
  def _should_save_has_front_colour(self) -> bool:
    """If self._has_front_colour should be saved.

    By default, this is true if whether the object has a front colour
    is cached. If this is True, on save if the object has a front colour will
    be saved. Child classes can overwrite this to control if this is saved.
    """
    return self.__has_front_colour is not None

  @property
  def _has_back_colour(self) -> bool:
    """If the object has a back colour.

    If True, the back of facets will be coloured using point, edge,
    facet, etc colours.
    If False, the back of facets will be coloured the back colour.
    """
    if self.__has_back_colour is None:
      self.__has_back_colour = self._modelling_api().HasTopologyBackColour(
        self._lock.lock
      )
    return self.__has_back_colour

  @property
  def _should_save_has_back_colour(self) -> bool:
    """If self._has_back_colour should be saved.

    By default, this is true if whether the object has a front colour
    is cached. If this is True, on save if the object has a back colour will
    be saved. Child classes can overwrite this to control if this is saved.
    """
    return self.__has_back_colour is not None

  @property
  def has_two_sided_colouring(self) -> bool:
    """True if this surface has two sided colouring.

    If this is True, the point, edge and facet colours are used to colour
    the "front" of the surface, and the back colour is used to colour
    the "back" of the surface.

    If this is False, the point, edge and facet colours are used to colour
    both the back and the front of the surface.

    Examples
    --------
    This property can be used to check if an object uses two sided
    colouring. The following example uses this property to write a
    report on the picked object stating whether it has two sided
    colouring:

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.operations import object_pick, write_report
    >>> if __name__ == "__main__":
    ...   with Project() as project:
    ...     oid = object_pick(
    ...       label="Pick an object to query two sided colouring.")
    ...     title = f"Does '{oid.path}' use two sided colouring?"
    ...     with project.read(oid) as read_object:
    ...       try:
    ...         write_report(title, str(read_object.has_two_sided_colouring))
    ...       except AttributeError:
    ...         write_report(title, "Unknown")
    """
    # There are four possibilities:
    # +--------------+--------------+---------------------+
    # | back colour  | front colour | two sided colouring |
    # +==============+==============+=====================+
    # | False        | False        | False*              |
    # +--------------+--------------+---------------------+
    # | True         | False        | True                |
    # +--------------+--------------+---------------------+
    # | False        | True         | True                |
    # +--------------+--------------+---------------------+
    # | True         | True         | False               |
    # +--------------+--------------+---------------------+
    # * If an object has neither a front or back colour, then it doesn't have
    #   two sided colouring because both sides are coloured
    #   the back colour. This state isn't expected to be possible.
    return self._has_back_colour != self._has_front_colour

  @property
  def back_colour(self) -> np.ndarray:
    """The colour used to colour the back of the object.

    The back colour is represented by an RGB colour instead of a
    RGBA colour. The back colour cannot be transparent, so it does
    not have an alpha component.

    Setting the back colour will set has_two_sided_colouring to True.

    Notes
    -----
    The default back colour is red (220, 0, 0).

    The back colour can still be read if has_two_sided_colouring is False,
    however it will not be used to visualise the object.

    Examples
    --------
    Setting the back colour sets the object to use two sided colouring
    (if it is not using it already). The following example demonstrates this
    by creating a square with one facet coloured yellow, one facet coloured
    cyan and the back of both facets coloured grey.

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import Surface
    >>> if __name__ == "__main__":
    ...   with Project() as project:
    ...     with project.new("surfaces/two_sided", Surface) as surface:
    ...       surface.points = [
    ...         [-5, -5, 0], [5, -5, 0], [5, 5, 0], [-5, 5, 0]
    ...       ]
    ...       surface.facets = [[0, 1, 2], [0, 2, 3]]
    ...       surface.facet_colours = [
    ...         [255, 255, 0, 255], [0, 255, 255, 255]
    ...       ]
    ...       surface.back_colour = [127, 127, 127]
    """
    if self.__back_colour is None:
      self.__back_colour = np.array(
        self._modelling_api().GetNaturalColour(self._lock.lock),
        dtype=ctypes.c_uint8
      )
    return self.__back_colour

  @back_colour.setter
  def back_colour(self, new_colour):
    if self.__back_colour is None:
      # The back colour isn't cached, so allocate an appropriately
      # sized empty array and copy the new values in.
      # Don't assign the empty colours to the backing field until after
      # the new values have been copied in to avoid an error causing the
      # back colour to be set to an empty array.
      colour = np.empty((3,), dtype=ctypes.c_uint8)
      colour[:] = new_colour
      self.__back_colour = colour
      self.__has_front_colour = True
      self.__has_back_colour = False
    else:
      # The back colour is cached. Copy the new values into the array.
      self.__back_colour[:] = new_colour

  def _clear_two_sided_colouring(self):
    """Disables two-sided colouring for the object.

    After this is called, has_two_sided_colouring will return False. No
    side of the object will be coloured the back colour.

    To re-enable two sided colouring, assign a colour to the back colour.

    This is protected because some classes which support two sided colouring
    (e.g. Discontinuity) do not support one sided colouring.

    Notes
    -----
    This does not change the back colour.
    """
    self.__has_back_colour = True
    self.__has_front_colour = True

  def _invalidate_two_sided_colouring_properties(self):
    """Invalidate the two sided colouring.

    This must be called during the inheriting class's invalidate properties
    function.
    """
    self.__back_colour = None
    self.__has_front_colour = None
    self.__has_back_colour = None

  def _save_two_sided_colouring(self):
    """Save the two sided colouring information.

    This must be called during the inheriting class's save function.
    """
    if self.__back_colour is not None:
      self._modelling_api().SetNaturalColour(self._lock.lock, self.back_colour)
    if self._should_save_has_back_colour:
      self._modelling_api().TopologySetHasBackColour(
        self._lock.lock, self._has_back_colour)
    if self._should_save_has_front_colour:
      self._modelling_api().TopologySetHasFrontColour(
        self._lock.lock, self._has_front_colour)
