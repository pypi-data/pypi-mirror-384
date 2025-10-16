"""Geometry types used in the Python SDK.

This does not cover the common geometry types of points, vectors and
facets which are represented with numpy arrays rather than distinct
types/classes.
"""
###############################################################################
#
# (C) Copyright 2023, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

from __future__ import annotations

import itertools
import typing

import numpy as np

if typing.TYPE_CHECKING:
  # This requires numpy 1.20 or later to be used.
  import numpy.typing as npt


class Plane:
  """A plane in 3D defined by the equation Ax + By + Cz + D = 0.
  """

  # pylint: disable=invalid-name;reason=Names are common to the domain and
  # would be unnecessarily wordy otherwise.
  def __init__(self, a: float, b: float, c: float, d: float):
    self.coefficient_a = a
    self.coefficient_b = b
    self.coefficient_c = c
    self.coefficient_d = d

  def __eq__(self, other):
    return (
    self.coefficient_a == other.coefficient_a and
    self.coefficient_b == other.coefficient_b and
    self.coefficient_c == other.coefficient_c and
    self.coefficient_d == other.coefficient_d)

  def __repr__(self) -> str:
    return f'Plane({self.coefficient_a}, {self.coefficient_b}, ' + \
      f'{self.coefficient_c}, {self.coefficient_d})'

  @property
  def normal(self) -> npt.ArrayLike:
    """The normal of the plane.

    This is not normalised (i.e. its length is not guaranteed to be 1).
    """
    return (self.coefficient_a, self.coefficient_b, self.coefficient_c)

  def translated(self, vector: npt.ArrayLike) -> Plane:
    """Return a new Plane translated by the given vector.

    Parameters
    ----------
    vector
      The vector by which the plane will be translated.

    Returns
    -------
    Plane
      A new plane that has been translated from the current plane by vector.

    Warnings
    --------
    Vector must not contain NaNs.
    Vector must be a 3D vector (consist of 3 components).
    """
    point = self._closest_point_on_plane_to((0.0, 0.0, 0.0))
    return self.from_normal_and_point(self.normal, point + vector)

  def _closest_point_on_plane_to(self, point: npt.ArrayLike) -> npt.ArrayLike:
    """Find the point on the plane closest to a specified point.

    Parameters
    ----------
    point
      The specified point.

    Returns
    -------
    npt.ArrayLike
      The closest point on the plane to the specified point.
    """
    # The closest point is calculated as:
    #    closest_point = specified_point + t * normal
    # Where
    #    t = -F ( specified_point ) / ( || normal || ^2)
    # And
    #    F(point) = A * point.x + B * point.y + C * point.z + D
    # With
    #    A, B, C, D being the coefficients of hte plane.
    f = (self.coefficient_a * point[0] + self.coefficient_b * point[1] +
         self.coefficient_c * point[2] + self.coefficient_d)

    normal = np.asarray(self.normal)
    t = -f / (normal  * normal ).sum()
    return np.asarray(point) + normal * t

  @classmethod
  def from_normal_and_point(cls, normal: npt.ArrayLike, point: npt.ArrayLike):
    """Construct a plane using a normal vector and point on the plane.

    Parameters
    ----------
    normal
      The normal vector of the plane.
      The magnitude (also known as length) of this vector must be non-zero.
    point
      A point on the plane.

    Warnings
    --------
    The length of the normal vector must not be zero.
    The normal or point must not contain NaNs.
    The point must be 3D point (consist of 3 components).
    """
    normal = np.asarray(normal)
    normalised_normal = normal / np.linalg.norm(normal)

    return cls(normalised_normal[0],
               normalised_normal[1],
               normalised_normal[2],
               -np.dot(normalised_normal, point))

  @classmethod
  def from_three_points(cls,
                        point1: npt.ArrayLike,
                        point2: npt.ArrayLike,
                        point3: npt.ArrayLike):
    """Construct a plane using three points and the right-hand rule.

    The plane normal is in the direction of Cross(point2 - point1,
    point3 - point1) and normal's magnitude (also known as length) must be
    non-zero.

    Parameters
    ----------
    point1
      The first point.
    point2
      The second point.
    point3
      The third point.

    Warnings
    --------
    The given points must be 3D points (consist of 3 components).
    The given points must not contain NaNs.
    The given points must not all be colinear.
    The length of the normal vector produced from the points must not be zero.
    """
    # Convert points to numpy arrays.
    point1 = np.asarray(point1)
    point2 = np.asarray(point2)
    point3 = np.asarray(point3)

    normal = np.cross(point2 - point1, point3 - point1)
    normalised_normal = normal / np.linalg.norm(normal)

    return cls(normalised_normal[0],
               normalised_normal[1],
               normalised_normal[2],
               -np.dot(normalised_normal, point1))

  @classmethod
  def xy(cls, z: float = 0):
    """Return a plane whose normal lines along the axis Z.

    The plane passes through (0, 0, z).

    Parameters
    ----------
    z
      The z-coordinate of the plane.

    Warnings
    --------
    The z should not be NaN.
    """
    return cls(0, 0, 1, -z)

  @classmethod
  def yz(cls, x: float = 0):
    """Return a plane whose normal lines along the axis X.

    The plane passes through (0, 0, 0).

    Parameters
    ----------
    x
      The x-coordinate of the plane.

    Warnings
    --------
    The x should not be NaN.
    """
    return cls(1, 0, 0, -x)

  @classmethod
  def xz(cls, y: float = 0):
    """Return a plane whose normal lines along the axis Y.

    The plane passes through (0, 0, 0).

    Parameters
    ----------
    y
      The y-coordinate of the plane.

    Warnings
    --------
    The y should not be NaN.
    """
    return cls(0, -1, 0, y)


class Extent:
  """A multidimensional, axially-aligned "intervals" or "extents".

  This extent is bound to a volume in 3D space.

  This is also known as a Axis-Aligned Bounding Box (AABB).

  Attributes
  ----------
  minimum
    Point representing minimum values in the form [x, y, z].
  maximum
    Point representing maximum values in the form [x, y, z].
  """
  def __init__(
      self,
      minimum: tuple[float, float, float],
      maximum: tuple[float, float, float]):
    self.minimum = minimum
    self.maximum = maximum

    if any(
      not np.isfinite(ordinate)
      for ordinate in itertools.chain(minimum, maximum)
    ):
      raise ValueError(
        "All extent ordinates must be finite."
      )

    if not all(lower <= upper for lower, upper in zip(minimum, maximum)):
      # This raises an error to inform the caller that they made a mistake.
      #
      # It may seem tempting to automatically fix the values by taking the min
      # and max of the pairs. However, if such a mistake was made it is
      # possible that another was made as well. For example, one of the inputs
      # may have came from the wrong source (property/variable).
      raise ValueError('minimum must be less than or equal to maximum.')

    assert len(self.minimum) == len(self.maximum)

  def __repr__(self) -> str:
    return f"Extent({self.minimum}, {self.maximum})"

  def __eq__(self, value: object) -> bool:
    if not isinstance(value, Extent):
      return False
    return (
      np.allclose(self.minimum, value.minimum)
      and np.allclose(self.maximum, value.maximum)
    )

  def __contains__(self, value: tuple[float, float, float] | Extent):
    """Return true if value is contained within the extent.

    An extent is contained within another extent if:

    - Its lower bound is greater than or equal to the other extent's lower
      bound.
    - Its upper bound is less than or equal to the other extent's upper bound.
    """
    if isinstance(value, Extent):
      def within_1d_extent(value, lower, upper):
        """Return True if value is within lower and upper or is lower or upper.
        """
        return lower <= value <= upper

      return all([
        # Check along the X-axis.
        within_1d_extent(value.minimum[0], self.minimum[0], self.maximum[0]),
        within_1d_extent(value.maximum[0], self.minimum[0], self.maximum[0]),

        # Check along the Y-axis.
        within_1d_extent(value.minimum[1], self.minimum[1], self.maximum[1]),
        within_1d_extent(value.maximum[1], self.minimum[1], self.maximum[1]),

        # Check along the Z-axis.
        within_1d_extent(value.minimum[2], self.minimum[2], self.maximum[2]),
        within_1d_extent(value.maximum[2], self.minimum[2], self.maximum[2]),
      ])

    return all(a >= b for a, b in zip(value, self.minimum)) and \
        all(a <= b for a, b in zip(value, self.maximum))

  @property
  def centre(self) -> tuple[float, float, float]:
    """Returns the center of the extent.

    Returns
    -------
    point
      Point representing the center of the extent.
    """
    assert len(self.minimum) == len(self.maximum)
    midpoints = [
      (minimum + maximum) / 2.0
      for minimum, maximum in zip(self.minimum, self.maximum)
    ]

    # The temporary conversion to a list causes mypy to think this tuple
    # is of type tuple[float, ...] (i.e. It forgets how long the tuple is).
    return tuple(midpoints) # type: ignore

  @property
  def length(self) -> float:
    """The length is the maximum of the X, Y or Z dimension.

    Returns
    -------
    float
      Maximum width of the extent.
    """
    assert len(self.minimum) == len(self.maximum)
    lengths = [
      maximum - minimum
      for minimum, maximum in zip(self.minimum, self.maximum)
    ]
    return max(lengths)

  @property
  def span(self) -> tuple[float, float, float]:
    """The span of the extent in each direction."""
    return tuple(
      max - min for max, min in zip(self.maximum, self.minimum)
    ) # type: ignore

  def as_numpy(self) -> np.ndarray:
    """Returns the extent as a numpy array.

    Returns
    -------
    np.array
      The extent representing as a numpy array.
    """
    return np.array(self.minimum + self.maximum)

  def overlaps(self, other: Extent) -> bool:
    """Return True if this extent and the other overlap.

    The extents overlap if they share space which includes if:

    - They extend over each other and partially cover the same space.
    - One extent overlaps another by being inside of the other.
    - The two extents come into contact with one another at a single point.
    - The two extents come into contact with one another along a line.
    - The two extents come into contact in a two dimensional rectangular area,
      similar to two boxes placed next to each other. No part of either extent
      is inside of the other extent, but both extents are touching.

    Parameters
    ----------
    other
      The extent to check if it overlaps with this extent.
    """

    return all([
      # Check the overlap for the X-axis.
      self.minimum[0] <= other.maximum[0],
      self.maximum[0] >= other.minimum[0],

      # Check the overlap for the Y-axis.
      self.minimum[1] <= other.maximum[1],
      self.maximum[1] >= other.minimum[1],

      # Check the overlap for the Z-axis.
      self.minimum[2] <= other.maximum[2],
      self.maximum[2] >= other.minimum[2],
    ])
