"""Geotechnical data types.

Currently this only includes discontinuities, however in the future it may
be expanded to contain other geotechnical objects such as stereonets.
"""
###############################################################################
#
# (C) Copyright 2020, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import ctypes
import enum
import math
import logging

import numpy as np

from .base import Topology, StaticType
from .errors import DegenerateTopologyError
from .objectid import ObjectID
from ..internal.data_property import DataProperty, DataPropertyConfiguration
from ..internal.two_sided_colouring_mixin import TwoSidedColouringMixin
from ..internal.util import default_type_error_message
from ..internal.lock import LockType

log = logging.getLogger("mapteksdk.data")

class Polarity(enum.Enum):
  """Enum representing the polarity of a Discontinuity."""
  UNKNOWN = 0
  """The polarity of the discontinuity is unknown.

  This is the default polarity for newly created discontinuities.
  """
  UPRIGHT = 1
  """The discontinuity is upright.

  This indicates that the discontinuity is upright relative to the orientation
  the rocks were originally deposited in.
  """
  OVERTURNED = -1
  """The discontinuity is overturned.

  This indicates that the discontinuity is overturned relative to the
  orientation the rocks were originally deposited in.
  """

  def flip(self):
    """Flip the polarity value.

    This returns the opposite polarity.

    Returns
    -------
    Polarity
      The opposite polarity.
      If called on Polarity.OVERTURNED, this is Polarity.UPRIGHT.
      If called on Polarity.UPRIGHT, this is Polarity.OVERTURNED.
      If called on Polarity.UNKNOWN, this is Polarity.UNKNOWN.
    """
    to_flipped_polarity = {
      Polarity.UNKNOWN : Polarity.UNKNOWN,
      Polarity.OVERTURNED : Polarity.UPRIGHT,
      Polarity.UPRIGHT : Polarity.OVERTURNED
    }

    return to_flipped_polarity[self]

class Discontinuity(Topology, TwoSidedColouringMixin):
  """A discontinuity (Also known as a tangent plane).

  These are generally used to mark a change in the physical or chemical
  characteristics in soil or rock mass.

  Discontinuities with similar properties are often placed in special
  containers known as discontinuity sets.

  Raises
  ------
  DegenerateTopologyError
    If on save, there are fewer than three points in the object.

  See Also
  --------
  :documentation:`discontinuity` : Help page for this class.

  Examples
  --------
  The simplest way to define a discontinuity is to define the planar points.
  This example defines a discontinuity using points in the plane with the
  equation 3x - y + 2z + 4 = 0. The other properties are automatically
  derived from the points used to define the discontinuity.

  >>> from mapteksdk.project import Project
  >>> from mapteksdk.data import Discontinuity
  >>> points = [[1, 1, -3], [-1, 2, 0.5], [-2, -2, 0],
  ...           [0, -2, -3], [-4, 0, 4], [2, 2, -4]]
  >>> project = Project()
  >>> with project.new("geotechnical/3x-y+2z+4", Discontinuity) as plane:
  ...     plane.planar_points = points
  >>> with project.read(plane.id) as read_plane:
  ...     print("Dip: ", read_plane.dip)
  ...     print("Dip direction: ", read_plane.dip_direction)
  ...     print("Location: ", read_plane.location)
  ...     print("Area: ", read_plane.area)
  ...     print("Length: ", read_plane.length)
  Dip:  1.0068536854342678
  Dip direction:  1.8925468811915387
  Location:  [-0.66666667  0.16666667 -0.91666667]
  Area:  28.062430400804566
  Length:  10.198039027185569

  A discontinuity can also be defined by setting the dip, dip direction
  and location. This is less preferable than the other methods because the
  discontinuity will not have a length or area.

  >>> import math
  >>> from mapteksdk.project import Project
  >>> from mapteksdk.data import Discontinuity
  >>> project = Project()
  >>> with project.new("geotechnical/simple", Discontinuity) as plane:
  ...     plane.dip = math.pi / 4
  ...     plane.dip_direction = math.pi / 2
  ...     plane.location = [4, 2, 1]
  >>> with project.read(plane.id) as read_plane:
  ...     print("Points", read_plane.planar_points)
  ...     print("Area: ", read_plane.area)
  ...     print("Length: ", read_plane.length)
  Points [[3.29289322 2.         1.70710678]
  [4.35355339 1.1339746  0.64644661]
  [4.35355339 2.8660254  0.64644661]]
  Area:  nan
  Length:  nan

  when creating a new discontinuity, it possible to define the planar points
  and the dip, dip direction and location. This causes the points to be
  projected onto the plane defined by the dip and dip direction and to be
  translated to be centred at the specified location. In the below example,
  though the points are originally centred around the origin and in
  the XY plane they are translated to be centred around the new centre
  and to be in the new plane.

  >>> import math
  >>> from mapteksdk.project import Project
  >>> from mapteksdk.data import Discontinuity
  >>> points = [[-1, -1, 0], [1, -1, 0], [-1, 1, 0], [1, 1, 0]]
  >>> project = Project()
  >>> with project.new("geotechnical/both", Discontinuity) as plane:
  ...     plane.planar_points = points
  ...     plane.dip = math.pi / 4
  ...     plane.dip_direction = math.pi / 2
  ...     plane.location = [4, 2, 1]
  >>> with project.read(plane.id) as read_plane:
  ...     print("Points", read_plane.planar_points)
  ...     print("Dip: ", read_plane.dip)
  ...     print("Dip direction: ", read_plane.dip_direction)
  ...     print("Location: ", read_plane.location)
  ...     print("Area: ", read_plane.area)
  ...     print("Length: ", read_plane.length)
  Points [[3.29289322 3.         1.70710678]
   [3.29289322 1.         1.70710678]
   [4.70710678 3.         0.29289322]
   [4.70710678 1.         0.29289322]]
  Dip:  0.7853981633974482
  Dip direction:  1.5707963267948966
  Location:  [4. 2. 1.]
  Area:  4.0
  Length:  2.8284271247461907
  """
  # :TRICKY: Though Discontinuities have points and facets, they do
  # not implement PointProperties and FacetProperties because they
  # do not support many of the operations those classes define.
  def __init__(self, object_id=None, lock_type=LockType.READWRITE):
    if not object_id:
      object_id = ObjectID(self._modelling_api().NewTangentPlane())
    super().__init__(object_id, lock_type)
    # :NOTE: Discontinuities do not edit the points by writing to the RW arrays,
    # so save() is never called on this property and thus it does not need
    # the save function defined.
    self.__points = DataProperty(
      lock=self._lock,
      configuration=DataPropertyConfiguration(
        name="points",
        dtype=ctypes.c_double,
        default=np.nan,
        column_count=3,
        primitive_count_function=self._modelling_api().ReadPointCount,
        cached_primitive_count_function=None,
        load_function=self._modelling_api().PointCoordinatesBeginR,
        save_function=None,
        set_primitive_count_function=None,
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode
      )
    )

    # The facets of a discontinuity are derived from the points and thus
    # are read-only.
    self.__facets = DataProperty(
      lock=self._lock,
      configuration=DataPropertyConfiguration(
        name="facets",
        dtype=ctypes.c_int32,
        default=0,
        column_count=3,
        primitive_count_function=self._modelling_api().ReadFacetCount,
        load_function=self._modelling_api().FacetToPointIndexBeginR,
        save_function=None,
        cached_primitive_count_function=None,
        set_primitive_count_function=None,
        immutable=True,
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode
      )
    )

    # The planar colour is the first colour in the point colours array.
    # Any further values are ignored.
    self.__planar_colour = DataProperty(
      lock=self._lock,
      configuration=DataPropertyConfiguration(
        name="point_colours",
        dtype=ctypes.c_uint8,
        default=np.array([0, 220, 0, 255], dtype=ctypes.c_uint8),
        column_count=4,
        primitive_count_function=self._modelling_api().ReadPointCount,
        cached_primitive_count_function=lambda: 1,
        load_function=self._modelling_api().PointColourBeginR,
        save_function=self._modelling_api().PointColourBeginRW,
        is_colour_property=True,
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode
      )
    )
    self.__dip = None
    self.__dip_direction = None
    self.__length = None
    self.__area = None
    self.__location = None
    self.__polarity = None

  @classmethod
  def static_type(cls) -> StaticType:
    return cls._modelling_api().TangentPlaneType()

  @property
  def planar_points(self):
    """The points used to define the discontinuity.

    This is an array of floats of shape (n, 3) where n is the
    planar_point_count. These points are coplanar.

    When set the first three of these points are used to define the dip
    and dip direction. If the first three points are collinear, the resulting
    discontinuity object will be empty.
    """
    return self.__points.values

  @planar_points.setter
  def planar_points(self, new_points):
    self.__points.values = new_points

  @property
  def planar_point_count(self):
    """The number of points used to visualize the discontinuity."""
    if self.__points.are_values_cached:
      return self.__points.values.shape[0]
    return self._modelling_api().ReadPointCount(self._lock.lock)

  @property
  def planar_facets(self):
    """The facets used to visualise the discontinuity.

    These are derived from the points and do not support direct assignment.

    If you change planar_points, the corresponding changes to the
    planar_facets will not occur until save() is called.
    """
    return self.__facets.values

  @property
  def planar_facet_count(self):
    """The count of facets used to visualise the discontinuity."""
    return self.planar_facets.shape[0]

  @property
  def planar_colour(self):
    """The colour of the facets. This is a single value used for all facets.

    The alpha value has no effect. This is provided as an RGBA colour for
    consistency.
    """
    return self.__planar_colour.values[0]

  @planar_colour.setter
  def planar_colour(self, new_colour):
    self.__planar_colour.values[0] = new_colour

  @property
  def has_two_sided_colouring(self) -> bool:
    # Technically, a tangent plane only has two sided colouring when viewed
    # with the "basic" feature. From a data perspective, two sided colouring
    # is always enabled, so always return True from this function.
    return True

  # Disable saving whether the discontinuity has a front or back colour
  # because which it has is defined by the Polarity. If these are
  # saved, the visualisation gets out of sync with the data.
  @property
  def _should_save_has_front_colour(self) -> bool:
    return False

  @property
  def _should_save_has_back_colour(self) -> bool:
    return False

  @property
  def dip(self) -> float:
    """The dip of the discontinuity.

    This is the angle in radians the discontinuity is rotated by in the
    dip direction.

    The dip and dip direction, taken together, define the plane the
    discontinuity lies in. If they are changed, upon save() the planar_points
    will be projected to lie on the new plane.

    Raises
    ------
    ValueError
      If set to an value which cannot be converted to a float, or is
      below zero or greater than pi / 2.

    Warnings
    --------
    Dip values close to zero cause issues with calculating the dip
    direction which can result in unintuitive behaviour.
    """
    if self.__dip is None:
      self._get_orientation()
    return self.__dip # type: ignore

  @dip.setter
  def dip(self, new_dip: float):
    dip = float(new_dip)
    if dip < 0 or dip > math.pi / 2:
      raise ValueError(f"Invalid dip: {dip}. Dip must be in [0, {math.pi / 2}]")
    self.__dip = dip

  @property
  def dip_direction(self) -> float:
    """The dip direction of the discontinuity.

    This is the angle in radians around the z axis which the plane is rotated
    by dip radians.

    The dip and dip direction, taken together, define the plane the
    discontinuity lies in. If they are changed, upon save() the planar_points
    will be projected to lie on the new plane.

    Raises
    ------
    ValueError
      If set to a value which cannot be converted to a float, or is
      below zero or greater than or equal to 2 * pi.

    Notes
    -----
    For completely horizontal discontinuities, this may be NaN.
    """
    if self.__dip_direction is None:
      self._get_orientation()
    return self.__dip_direction # type: ignore

  @dip_direction.setter
  def dip_direction(self, new_direction: float):
    direction = float(new_direction)
    if direction < 0 or direction >= math.pi * 2:
      raise ValueError(f"Invalid dip direction: {direction}. "
                       f"Dip direction must be in [0, {math.pi * 2})")
    self.__dip_direction = direction

  @property
  def strike(self):
    """The strike of the discontinuity.

    This is the angle in radians to the y axis of the line of intersection
    between the discontinuity plane and the horizontal plane (XY plane).

    This is derived from the dip direction. Changing the dip direction
    will change the strike and vice versa.

    Raises
    ------
    ValueError
      If set to a value which cannot be converted to a float, or is
      below zero or greater than or equal to 2 * pi.

    Notes
    -----
    For completely horizontal discontinuities, this may be NaN.
    """
    strike = self.dip_direction - math.pi / 2
    if strike < 0:
      strike += math.pi * 2
    return strike

  @strike.setter
  def strike(self, strike):
    new_strike = float(strike)
    if strike < 0 or strike >= math.pi * 2:
      raise ValueError(f"Invalid strike: {strike}. "
                       f"Strike must be in [0, {math.pi * 2})")
    dip_direction = new_strike + math.pi / 2
    if dip_direction >= math.pi * 2:
      dip_direction -= math.pi * 2
    self.dip_direction = dip_direction

  @property
  def plunge(self):
    """The plunge angle of the discontinuity.

    This is derived from the dip - changing the dip will change the plunge
    and vice versa.

    Raises
    ------
    ValueError
      If set to a value which cannot be converted to a float, or is
      below zero or greater than pi / 2.

    Notes
    -----
    The dip and plunge for a discontinuity always add up to pi / 2.
    """
    return (math.pi / 2) - self.dip

  @plunge.setter
  def plunge(self, plunge):
    new_plunge = float(plunge)
    if new_plunge < 0 or new_plunge > math.pi / 2:
      raise ValueError(f"Invalid plunge: {plunge}. "
                       f"Plunge must be in [0, {math.pi / 2})")
    self.dip = (math.pi / 2) - new_plunge

  @property
  def trend(self):
    """The trend of the discontinuity in radians.

    This is derived from the dip direction. Changing the dip direction
    will change the trend and vice versa.

    Raises
    ------
    ValueError
      If set to a value which cannot be converted to a float, or is
      below zero or greater than or equal to pi * 2.
    """
    trend = self.dip_direction + math.pi
    if trend >= math.pi * 2:
      trend -= math.pi * 2
    return trend

  @trend.setter
  def trend(self, trend):
    new_trend = float(trend)
    if new_trend < 0 or new_trend >= math.pi * 2:
      raise ValueError(f"Invalid trend: {trend}. "
                       f"Trend must be in [0, {math.pi * 2})")
    dip_direction = new_trend - math.pi
    if dip_direction < 0:
      dip_direction += math.pi * 2
    self.dip_direction = dip_direction

  @property
  def polarity(self) -> Polarity:
    """The polarity of the Discontinuity.

    See the enum for more details on the meaning of each polarity value.

    If the discontinuity's polarity is known and it is displayed
    using the "Simple" display type, the front of the discontinuity will
    be coloured planar_colour and the back will be coloured back_colour.

    Examples
    --------
    Create a discontinuity with "upright" polarity. When viewed in
    "simple" mode, the discontinuity will appear as a disk at [0, 0, 0].
    The front of the disk will be coloured dark green and the back of
    the disk will be coloured grey (The planar colour determines the
    front colour and the back colour determines the back colour).

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import Discontinuity, Polarity
    >>> if __name__ == "__main__":
    ...   project = Project()
    ...   path = "geotechnical/upright"
    ...   with project.new(path, Discontinuity) as new_plane:
    ...     new_plane.planar_points = [[0, 0, 0], [1, 0, 0], [0, 1, 0]]
    ...     new_plane.polarity = Polarity.UPRIGHT
    ...     new_plane.planar_colour = [0, 165, 15, 255]
    ...     new_plane.back_colour = [67, 67, 67]
    ...   with project.read(new_plane.id) as read_plane:
    ...     print(read_plane.planar_points)
    ...     print(read_plane.planar_facets)
    ...     print(read_plane.polarity)
    ...     print(read_plane.planar_colour)
    """
    if self.__polarity is None:
      self.__polarity = Polarity(
        self._modelling_api().TangentPlaneGetPolarity(self._lock.lock)
      )
    return self.__polarity

  @polarity.setter
  def polarity(self, new_polarity: Polarity):
    if not isinstance(new_polarity, Polarity):
      raise TypeError(
        default_type_error_message(
          "polarity",
          new_polarity,
          Polarity
        )
      )
    self.__polarity = new_polarity

  @property
  def length(self):
    """The length of the discontinuity.

    This is the diameter of the smallest sphere capable of containing all
    of the points.

    Notes
    -----
    For empty discontinuities, the length will be NaN.
    """
    if self.__length is None:
      self.__length = self._modelling_api().TangentPlaneGetLength(self._lock.lock)
    return self.__length

  @property
  def location(self):
    """The location of the discontinuity in the form [X, Y, Z].

    By default, this is the mean of the points used to construct the
    discontinuity.

    Notes
    -----
    For empty discontinuities, this will be NaN.
    """
    if self.__location is None:
      self.__location = self._modelling_api().TangentPlaneGetLocation(self._lock.lock)
    return self.__location

  @location.setter
  def location(self, new_location):
    self.location[:] = new_location

  @property
  def area(self):
    """The scaled area of the discontinuity.

    Changes to the area will not occur until save() is called. This may not
    be exactly equal to the area of the planar facets.
    """
    if self.__area is None:
      self.__area = self._modelling_api().TangentPlaneGetArea(self._lock.lock)
    return self.__area

  def flip_polarity(self):
    """Flips the polarity of the discontinuity.

    See the documentation on the Polarity enum for the effect of flipping
    the polarity of an enum.
    """
    # Assign to the backing field to bypass the validation because the
    # value should already be valid.
    self.__polarity = self.polarity.flip()

  def _extra_invalidate_properties(self):
    super()._extra_invalidate_properties()
    self.__points.invalidate()
    self.__facets.invalidate()
    self.__planar_colour.invalidate()
    self._invalidate_two_sided_colouring_properties()
    self.__dip = None
    self.__dip_direction = None
    self.__length = None
    self.__location = None
    self.__area = None
    self.__polarity = None

  def _record_object_size_telemetry(self):
    # There is no meaningful size to record.
    return

  def _save_topology(self):
    if self.planar_point_count < 3:
      raise DegenerateTopologyError(
        "Discontinuities require at least three points to define the plane.")

    if self.__points.are_values_cached:
      self._modelling_api().SetTangentPlaneFromPoints(self._lock.lock,
                                            self.planar_points)

    if self.__dip is not None or self.__dip_direction is not None:
      self._modelling_api().TangentPlaneSetOrientation(self._lock.lock,
                                             self.dip,
                                             self.dip_direction)

    if self.__location is not None:
      self._modelling_api().TangentPlaneSetLocation(self._lock.lock, *self.location)

    if self.__polarity is not None:
      self._modelling_api().TangentPlaneSetPolarity(
        self._lock.lock, self.__polarity.value)

    if self.__planar_colour.are_values_cached:
      colour = (ctypes.c_uint8 * 4)()
      colour[:] = self.planar_colour
      # As only the first point colour is used, set using uniform point colour.
      self._modelling_api().SetUniformPointColour(self._lock.lock,
                                        colour)

    self._save_two_sided_colouring()

  def _get_orientation(self):
    """Retrieves the dip and dip direction from the project.

    They are stored in __dip and __dip_direction.
    """
    orientation = self._modelling_api().TangentPlaneGetOrientation(self._lock.lock)
    # Make sure not to overwrite values set by the setter.
    if self.__dip is None:
      self.__dip = orientation[0]
    if self.__dip_direction is None:
      self.__dip_direction = orientation[1]
