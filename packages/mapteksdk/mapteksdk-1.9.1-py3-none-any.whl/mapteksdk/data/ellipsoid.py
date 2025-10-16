"""Module containing the Ellipsoid class.
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

from .base import Topology, StaticType
from .objectid import ObjectID
from .rotation import RotationMixin
from ..internal.data_property import DataProperty, DataPropertyConfiguration
from ..internal.lock import LockType
from ..internal.rotation import Rotation

if typing.TYPE_CHECKING:
  import numpy.typing as npt

class Ellipsoid(Topology, RotationMixin):
  """A closed quadratic surface.

  Examples
  --------
  The following example demonstrates creating an ellipsoid which has the
  following properties:
  * It is centred at (1.5, 1.5, 1.5)
  * The semi-major axis length is 1.75
  * The major axis length is 1.5
  * The minor axis length 1.0
  * The bearing is 45 degrees.
  * The plunge is 15 degrees.
  * The dip is -30 degrees.

  >>> from mapteksdk.project import Project
  >>> from mapteksdk.data import Ellipsoid
  >>> import numpy as np
  >>> if __name__ == "__main__":
  ...   with Project() as project:
  ...     with project.new("geomodel/example", Ellipsoid) as ellipsoid:
  ...       ellipsoid.centre = (1.5, 1.5, 1.5)
  ...       ellipsoid.size = (1.75, 1.5, 1.0)
  ...       ellipsoid.set_orientation(
  ...         np.deg2rad(-30),
  ...         np.deg2rad(15),
  ...         np.deg2rad(45)
  ...       )
  ...       ellipsoid.colour = [255, 165, 0, 255]
  """
  def __init__(self, object_id=None, lock_type=LockType.READWRITE):
    if not object_id:
      object_id = ObjectID(self._modelling_api().NewEllipsoid())
    super().__init__(object_id, lock_type)
    self.__size: tuple[float, float, float] | None = None
    self.__centre: np.ndarray | None = None
    # Ellipsoids use the point colours to set the colour of the object.
    # This has save_function set to None because to save the colour of
    # the ellipsoid requires setting the uniform point colour rather than
    # writing to PointColourBeginRW.
    self.__point_colours = DataProperty(
      lock=self._lock,
      configuration=DataPropertyConfiguration(
        name="point_colours",
        dtype=ctypes.c_uint8,
        default=np.array([0, 220, 0, 255], dtype=ctypes.c_uint8),
        column_count=4,
        primitive_count_function=self._modelling_api().ReadPointCount,
        cached_primitive_count_function=lambda: 1,
        load_function=self._modelling_api().PointColourBeginR,
        save_function=None,
        is_colour_property=True,
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode
      )
    )

  @property
  def size(self) -> tuple[float, float, float]:
    """Get the size of the ellipsoid.

    This is a tuple containing three floats representing the size of
    the ellipsoid in the form:
    (semi-major, major, minor)

    Raises
    ------
    ValueError
      If set to an iterable which does not contain three floats, or
      if any of the floats are less than or equal to zero, NaN
      or infinite.
    """
    if self.__size is None:
      self.__size = self._modelling_api().GetEllipsoidSize(self._lock.lock)
    return self.__size

  @size.setter
  def size(self, new_size: Iterable[float]):
    self._raise_if_read_only("edit ellipsoid size")
    if len(new_size) != 3:
      raise ValueError(
        "Invalid value for new size. "
        f"It must contain 3 items, not {new_size}"
      )
    actual_new_size = (
      float(new_size[0]), float(new_size[1]), float(new_size[2]))

    if (any(x <= 0 for x in actual_new_size)
        or any(not np.isfinite(x) for x in actual_new_size)):
      raise ValueError(
        "Cannot set size to negative number."
        f"Sizes: {new_size[0]}, {new_size[1]}, {new_size[2]}"
      )

    self.__size = actual_new_size

  @property
  def centre(self) -> np.ndarray:
    """The centre point of the ellipsoid."""
    if self.__centre is None:
      centre = np.empty((3,), ctypes.c_double)
      centre[:] = self._modelling_api().GetEllipsoidCentre(self._lock.lock)
      centre.flags.writeable = not self.is_read_only
      self.__centre = centre
    return self.__centre

  @centre.setter
  def centre(self, new_centre: npt.ArrayLike):
    self._raise_if_read_only("setting ellipsoid centre")
    centre = np.empty((3,), ctypes.c_double)
    centre[:] = new_centre
    self.__centre = centre

  @property
  def colour(self) -> np.ndarray:
    """The colour of the discontinuity.

    This is represented as a numpy array of shape (4,) of the
    form (Red, Green, Blue, Alpha) where each component is
    between 0 and 255.
    """
    return self.__point_colours.values[0]

  @colour.setter
  def colour(self, new_colour: npt.ArrayLike):
    self.__point_colours.values = new_colour

  @property
  def orientation(self):
    heading, pitch, roll = self._rotation.heading_pitch_roll
    return (-roll, pitch, heading)

  def set_orientation(self, dip, plunge, bearing):
    self.set_heading_pitch_roll(bearing, plunge, -dip)

  @classmethod
  def static_type(cls) -> StaticType:
    return cls._modelling_api().EllipsoidType()

  def _get_rotation(self):
    return Rotation(*self._modelling_api().GetEllipsoidRotation(self._lock.lock))

  def _extra_invalidate_properties(self):
    super()._extra_invalidate_properties()
    self.__size = None
    self.__centre = None
    self.__point_colours.invalidate()

  def _record_object_size_telemetry(self):
    # There is no meaningful size to record.
    return

  def _save_topology(self):
    if self.__size is not None:
      major, semi_major, minor = self.size
      self._modelling_api().SetEllipsoidSize(self._lock.lock, major, semi_major, minor)
    if self.__centre is not None:
      x, y, z = self.centre
      self._modelling_api().SetEllipsoidCentre(self._lock.lock, x, y, z)
    if self._rotation_cached:
      q0, q1, q2, q3 = self._rotation.quaternion
      self._modelling_api().SetEllipsoidRotation(self._lock.lock, q0, q1, q2, q3)
    if self.__point_colours.are_values_cached:
      c_colour = (ctypes.c_uint8 * 4)()
      c_colour[:] = self.colour
      self._modelling_api().SetUniformPointColour(self._lock.lock, c_colour)
