"""Ribbon data types.

These are similar to edge data types. The primary difference is the lines
connecting the points have a width and an angle.
"""
###############################################################################
#
# (C) Copyright 2022, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

from collections.abc import Iterable
import ctypes
import typing

import numpy as np

from .base import StaticType
from .edges import Polyline, Polygon
from .errors import StaleDataError
from .objectid import ObjectID
from ..internal.data_property import DataProperty, DataPropertyConfiguration
from ..internal.lock import LockType
from ..internal.two_sided_colouring_mixin import TwoSidedColouringMixin

if typing.TYPE_CHECKING:
  from collections.abc import Callable

  from ..capi import ModellingApi
  from ..common.typing import (
    ColourArray,
    ColourArrayLike,
    Colour,
    ColourLike,
    FloatArray,
    FloatArrayLike,
    Vector3DArray,
  )
  from ..internal.lock import ReadLock, WriteLock

class _RibbonMixin:
  """Mixin class which adds ribbon properties to an edge object.

  This assumes the inheriting class inherits from PointProperties.
  """
  # Properties the inheriting object is expected to provide:
  is_read_only: bool
  point_count: int
  _are_points_cached: bool
  _lock: WriteLock | ReadLock
  _modelling_api: Callable[[], ModellingApi]
  _reconcile_changes: Callable[[], None]
  _invalidate_properties: Callable[[], None]

  def _define_ribbon_properties(self):
    """Define the ribbon-specific properties.

    This must be called in the inheriting class's __init__() method
    after calling super().__init__().
    This defines the backing for the point_angles, point_width and
    point_normals properties.
    """
    self.__point_angles = DataProperty(
      lock=self._lock,
      configuration=DataPropertyConfiguration(
        name="point_angles",
        dtype=ctypes.c_double,
        default=0.0,
        column_count=1,
        load_function=self._modelling_api().PointAnglesBeginR,
        save_function=self._modelling_api().PointAnglesBeginRW,
        primitive_count_function=self._modelling_api().ReadPointCount,
        cached_primitive_count_function=lambda: self.point_count,
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode
      )
    )
    self.__point_width = DataProperty(
      lock=self._lock,
      configuration=DataPropertyConfiguration(
        name="point_width",
        dtype=ctypes.c_double,
        default=10.0,
        column_count=1,
        load_function=self._modelling_api().PointWidthsBeginR,
        save_function=self._modelling_api().PointWidthsBeginRW,
        primitive_count_function=self._modelling_api().ReadPointCount,
        cached_primitive_count_function=lambda: self.point_count,
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode
      )
    )
    self.__point_normals = DataProperty(
      lock=self._lock,
      configuration=DataPropertyConfiguration(
        name="point_normals",
        dtype=ctypes.c_double,
        default=np.nan,
        column_count=3,
        load_function=self._modelling_api().PointNormalsBeginR,
        save_function=None,
        primitive_count_function=self._modelling_api().ReadPointCount,
        cached_primitive_count_function=lambda: self.point_count,
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode,
        immutable=True
      )
    )
    # The front colour is the first colour in the point colours array.
    # Any further values are ignored.
    self.__front_colour = DataProperty(
      lock=self._lock,
      configuration=DataPropertyConfiguration(
        name="point_colours",
        dtype=ctypes.c_uint8,
        default=np.array([0, 220, 0, 255], dtype=ctypes.c_uint8),
        column_count=4,
        primitive_count_function=self._modelling_api().ReadPointCount,
        cached_primitive_count_function=lambda: 1,
        load_function=self._modelling_api().PointColourBeginR,
        # This is saved externally to DataProperty.
        save_function=None,
        is_colour_property=True,
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode
      )
    )

  def _invalidate_ribbon_properties(self):
    """Invalidate the ribbon properties.

    This should be called in the inheriting object's _invalidate_properties()
    function.
    """
    self.__point_width.invalidate()
    self.__point_angles.invalidate()
    self.__point_normals.invalidate()
    self.__front_colour.invalidate()

  def _check_safe_to_save_ribbon_properties(self):
    """Raises an error if the ribbon properties can't be saved.

    This will raise an error if any point_width is less than zero.
    The setter for point_width also raises this error, however it is
    possible to assign negative values into the point_width array directly
    thus bypassing the error.

    This must be called before _save_ribbon_properties() because saving
    a negative width value may cause the application to crash.
    """
    # Ensure the point width is greater than zero.
    if self.__point_width.are_values_cached:
      if np.any(self.point_widths < 0):
        raise ValueError("Point width must be less than zero.")

  def _save_ribbon_properties(self):
    """Save the ribbon properties.

    This must be called in the inheriting object's save() function
    after calling save_point_properties().
    """
    self.__point_width.save()
    self.__point_angles.save()
    if self.__front_colour.are_values_cached:
      colour = (ctypes.c_uint8 * 4)()
      colour[:] = self.front_colour
      # As only the first point colour is used, set using uniform point colour.
      self._modelling_api().SetUniformPointColour(self._lock.lock,
                                        colour)
    self._reconcile_changes()

  @property
  def point_angles(self) -> FloatArray:
    """The angles of the ribbon at each point."""
    return self.__point_angles.values

  @point_angles.setter
  def point_angles(self, new_angles: FloatArrayLike):
    self.__point_angles.values = new_angles

  @property
  def point_widths(self) -> FloatArray:
    """The width of the ribbon at each point.

    Raises
    ------
    ValueError
      If any value in point_width is negative.
    """
    return self.__point_width.values

  @point_widths.setter
  def point_widths(self, new_width: FloatArrayLike):
    if isinstance(new_width, Iterable) and any(float(x) < 0 for x in new_width):
      raise ValueError("Width must be greater than zero.")
    self.__point_width.values = new_width

  @property
  def point_normals(self) -> Vector3DArray:
    """The point normals at each point.

    This is a unit vector for each point indicating the normal to the
    ribbon at that point.

    Raises
    ------
    StaleDataError
      If the object is open for editing and either the points or
      the point_angles have been read since the last time the object was saved.
      Call save() or close the object after editing the point normals
      or point angles to stop this error from being raised.

    Notes
    -----
    The point normals are derived from the points and the point_angles.
    If either the points or the point_angles are changed, the values
    of this array are only recalculated when save() is called.

    Though the point normals array only needs to be recalculated if
    the points or point_angles are edited, only reading them will trigger
    a StaleDataError to be raised if the object is open for editing.
    This is because it is not practical for the SDK to verify that the
    array has been edited.
    """
    if (not self.is_read_only
        and (self._are_points_cached
             or self.__point_angles.are_values_cached)):
      raise StaleDataError(
        "The point normals array may be stale. "
        "Close and re-open the object or call save() to update it."
      )
    return self.__point_normals.values

  @property
  def front_colour(self) -> Colour:
    """The colour used for the front of the ribbon.

    The front of a ribbon is coloured using the front_colour and the
    back of the ribbon is coloured using the back_colour.

    Notes
    -----
    The front of the ribbon can also be coloured by setting the point_colours,
    however only the first colour will be used by the viewer. It is preferable
    to always set the front colour of the ribbon.

    If both the point_colours and the front_colour is set, the point_colours
    will be ignored and the front_colour will be used.
    """
    return self.__front_colour.values[0]

  @front_colour.setter
  def front_colour(self, new_colour: ColourLike):
    self.__front_colour.values[0] = new_colour


class RibbonChain(Polyline, _RibbonMixin, TwoSidedColouringMixin):
  """A Polyline, except each edge has a width and angle.

  Examples
  --------
  Creates a ribbon chain with uniform 1m width which undergoes a 180 degree
  rotation from the first point of the ribbon to the last.

  >>> from mapteksdk.project import Project
  >>> from mapteksdk.data import RibbonChain
  >>> import numpy as np
  >>> if __name__ == "__main__":
  ...   with Project() as project:
  ...     point_count = 20
  ...     with project.new("loops/example_open_loop", RibbonChain) as ribbon:
  ...       ribbon.points = np.full((point_count, 3), 0, dtype=np.float64)
  ...       ribbon.points[:, 1] = range(point_count)
  ...       ribbon.point_angles = np.linspace(
  ...         -np.pi / 2, np.pi / 2, point_count)
  ...       ribbon.point_width = 1.0

  Assigning an array to the point width can be done to change the width
  of the ribbon at each point. For example, the following example is the
  same as the above except that the point width goes from 0.5m at
  the zeroth point to 2.5m at the final point.

  >>> from mapteksdk.project import Project
  >>> from mapteksdk.data import RibbonChain
  >>> import numpy as np
  >>> if __name__ == "__main__":
  ...   with Project() as project:
  ...     point_count = 20
  ...     with project.new("loops/example_open_loop_2", RibbonChain) as ribbon:
  ...       ribbon.points = np.full((point_count, 3), 0, dtype=np.float64)
  ...       ribbon.points[:, 1] = range(point_count)
  ...       ribbon.point_angles = np.linspace(
  ...         -np.pi / 2, np.pi / 2, point_count)
  ...       ribbon.point_width = np.linspace(0.5, 2.5, 20)
  """
  def __init__(self, object_id=None, lock_type=LockType.READWRITE):
    # Set object id before calling Polyline's __init__ method to ensure
    # that it does not create a new Polyline instead of a RibbonChain.
    if not object_id:
      object_id = ObjectID(self._modelling_api().NewRibbonChain())
    super().__init__(object_id, lock_type)
    self._define_ribbon_properties()

  @classmethod
  def static_type(cls) -> StaticType:
    """Return the type of edge network as stored in a Project.

    This can be used for determining if the type of an object is an edge
    network.
    """
    return cls._modelling_api().RibbonChainType()

  @property
  def point_colours(self) -> ColourArray:
    """The point colours array.

    Warnings
    --------
    RibbonChains colour the entire ribbon using the first value in
    point_colours. The other values are ignored. You should colour
    the ribbon using the front_colour property instead.
    """
    # All this overwrite does is change the documentation.
    return super().point_colours

  @point_colours.setter
  def point_colours(self, point_colours: ColourArrayLike):
    # :TRICKY: This must also overwrite the setter otherwise point_colours
    # cannot be set on the child class.
    # :NOTE: super() doesn't support setters.
    # super().point_colours = point_colours
    # is invalid syntax. See https://github.com/python/cpython/issues/59170.
    Polyline.point_colours.fset(self, point_colours) # type: ignore

  def _extra_invalidate_properties(self):
    super()._extra_invalidate_properties()
    self._invalidate_ribbon_properties()
    self._invalidate_two_sided_colouring_properties()

  def _save_topology(self):
    self._check_safe_to_save_ribbon_properties()
    super()._save_topology()
    self._save_two_sided_colouring()
    self._save_ribbon_properties()


class RibbonLoop(Polygon, _RibbonMixin, TwoSidedColouringMixin):
  """A Polygon, except each edge has a width and angle.

  Examples
  --------
  The following example creates a square ribbon loop with the ribbon making
  a 180 degree twist.

  >>> from mapteksdk.project import Project
  >>> from mapteksdk.data import RibbonLoop
  >>> import numpy as np
  >>> if __name__ == "__main__":
  ...   with Project() as project:
  ...     point_count = 20
  ...     with project.new("loops/example_closed_loop", RibbonLoop) as ribbon:
  ...       ribbon.points = [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]]
  ...       ribbon.point_angles = [
  ...         -np.pi / 2, -np.pi / 4, np.pi / 4, np.pi / 2
  ...       ]
  ...       ribbon.point_width = 0.1
  """
  def __init__(self, object_id=None, lock_type=LockType.READWRITE):
    # Set object id before calling Polyline's __init__ method to ensure
    # that it does not create a new Polyline instead of a RibbonLoop.
    if not object_id:
      object_id = ObjectID(self._modelling_api().NewRibbonLoop())
    super().__init__(object_id, lock_type)
    self._define_ribbon_properties()

  @classmethod
  def static_type(cls) -> StaticType:
    """Return the type of edge network as stored in a Project.

    This can be used for determining if the type of an object is an edge
    network.
    """
    return cls._modelling_api().RibbonLoopType()

  @property
  def point_colours(self) -> ColourArray:
    """The point colours array.

    Warnings
    --------
    RibbonLoops colour the entire ribbon using the first value in
    point_colours. The other values are ignored. You should colour
    the ribbon using the front_colour property instead.
    """
    # All this overwrite does is change the documentation.
    return super().point_colours

  @point_colours.setter
  def point_colours(self, point_colours: ColourArrayLike):
    # :TRICKY: This must also overwrite the setter otherwise point_colours
    # cannot be set on the child class.
    # :NOTE: super() doesn't support setters.
    # super().point_colours = point_colours
    # is invalid syntax. See https://github.com/python/cpython/issues/59170.
    Polygon.point_colours.fset(self, point_colours) # type: ignore

  def _extra_invalidate_properties(self):
    super()._extra_invalidate_properties()
    self._invalidate_ribbon_properties()
    self._invalidate_two_sided_colouring_properties()

  def _save_topology(self):
    self._check_safe_to_save_ribbon_properties()
    super()._save_topology()
    self._save_two_sided_colouring()
    self._save_ribbon_properties()
