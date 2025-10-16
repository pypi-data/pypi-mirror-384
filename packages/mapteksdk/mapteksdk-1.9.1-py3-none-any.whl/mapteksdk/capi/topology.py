"""Interface for the MDF topology library.

Warnings
--------
Vendors and clients should not develop scripts or applications against
this module. The contents may change at any time without warning.

"""
###############################################################################
#
# (C) Copyright 2023, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

# pylint: disable=line-too-long
# pylint: disable=invalid-name;reason=Names match C++ names.
import ctypes
import math

from .errors import CApiUnknownError
from .wrapper_base import WrapperBase


class Triple(ctypes.Structure):
  """A struct that represents a triple index using three uint32s"""
  _fields_ = (("a", ctypes.c_uint32),
              ("b", ctypes.c_uint32),
              ("c", ctypes.c_uint32))

  def __str__(self):
    return f"({self.a}, {self.b}, {self.c})"


class Point(ctypes.Structure):
  """A struct that represents a geoS_Point space using three doubles.

  Parameters
  ----------
  x
    The x coordinate of the point.
  y
    The y coordinate of the point.
  z
    The z coordinate of the point.

  Raises
  ------
  ValueError
    If x, y or z are NaN.
  """
  _fields_ = (("x", ctypes.c_double),
              ("y", ctypes.c_double),
              ("z", ctypes.c_double))

  def __init__(self, x, y, z) -> None:
    if any(math.isnan(i) for i in (x, y, z)):
      raise ValueError(
        f"Point cannot contain NaN. Point: ({x}, {y}, {z})")
    super().__init__(x, y, z)

  def __str__(self):
    return f"({self.x}, {self.y}, {self.z})"


class TopologyApi(WrapperBase):
  """Access to the application topology API.

  This should be accessed through get_application_dlls() for new code.
  """
  @staticmethod
  def method_prefix():
    return "Topology"

  @staticmethod
  def dll_name() -> str:
    return "mdf_topology"

  def capi_functions(self):
    return [
      # Functions changed in version 0.
      # Format:
      # "name" : (return_type, arg_types)
      {
        "TopologyRegisterPointSetToSurface" : (
          ctypes.c_bool,
          [
            ctypes.POINTER(Point),
            ctypes.POINTER(Triple),
            ctypes.POINTER(Triple),
            ctypes.POINTER(Point),
            ctypes.POINTER(Point),
            ctypes.POINTER(ctypes.c_double),
            ctypes.POINTER(ctypes.c_uint32),
          ]
        ),
        "TopologyCheckFacetNetworkValidity" : (
          ctypes.c_uint8,
          [
            ctypes.POINTER(Point),
            ctypes.POINTER(Triple),
            ctypes.POINTER(Triple),
            ctypes.c_bool,
          ]
        ),
        "TopologyClassifyPointsInSolid" : (
          None,
          [
            ctypes.POINTER(Point),
            ctypes.POINTER(Triple),
            ctypes.POINTER(Triple),
            ctypes.POINTER(Point),
            ctypes.POINTER(Point),
            ctypes.c_bool,
          ]
        ),
        "TopologyClassifyPointsAboveOrBelowSurface" : (
          None,
          [
            ctypes.POINTER(Point),
            ctypes.POINTER(Triple),
            ctypes.POINTER(Triple),
            ctypes.POINTER(Point),
            ctypes.POINTER(Point),
            ctypes.c_uint8,
          ]
        ),
      },
      # Functions changed in version 1.
      {
        "TopologyCApiVersion" : (ctypes.c_uint32, None),
        "TopologyCApiMinorVersion" : (ctypes.c_uint32, None),
      }
    ]

  def RegisterPointSetToSurface(
      self,
      surface_points,
      surface_facet_to_point_index,
      point_set_to_register):
    """Register a point set to a facet network surface.

    Parameters
    ----------
    surface_points: typing.Iterable[typing.Iterable[float]]
      An iterable containing three dimensional points (iterables containing
      three floating point numbers) representing the points on the surface
      to project point_set_to_register onto.
    surface_facet_to_point_index: typing.Iterable[typing.Iterable[int]]
      An iterable containing iterables of three integers. Each inner
      iterable represents which points make up each facet of the surface.
    point_set_to_register:
      An iterable containing three dimensional points (iterables containing
      three floating point numbers) representing the points to project onto
      the surface.

    Returns
    -------
    registered_z_values: ctypes.Array[ctypes.c_double]
      The adjusted z coordinates required to project point_set_to_register
      onto the surface. This has the same length as point_set_to_register.
    point_to_projected_facet_map: ctypes.Array[ctypes.c_uint32]
      Which facet each point in point_set_to_register was projected onto.
      This has the same length as point_set_to_register.

    Raises
    ------
    ValueError
      If surface_points or point_set_to_register contains a NaN.

    Warnings
    --------
    This will encounter an infinite loop if point_set_to_register contains
    a NaN.

    Notes
    -----
    This returns the ctypes types to avoid an extra copy when converting
    the output into a NumPy array.

    Examples
    --------
    The following example demonstrates using this function to project
    two points onto a surface with four points and two facets.

    >>> surface_points = ((0, 0, 20), (0, 10, 20), (10, 10, 20), (10, 0, 20))
    >>> surface_facet_to_point_index = ((0, 1, 2), (2, 3, 0))
    >>> point_set_to_register = ((5, 5, 5), (5, 1, 0))
    >>> z_values, point_to_projected_facet = Topology(
    ...     ).RegisterPointSetToSurface(
    ...         surface_points,
    ...         surface_facet_to_point_index,
    ...         point_set_to_register)
    """
    def create_triple_with_limit(a, b, c, limit):
      """Create a triple with error checking.

      Parameters
      ----------
      a
        First element of the triple.
      b
        Second element of the triple.
      c
        Third element of the triple.
      limit
        An error will be raised if a, b or c are greater than or equal to
        the limit.

      Returns
      -------
      Triple
        Triple constructed from a, b and c

      Raises
      ------
      ValueError
        If a, b or c were greater than or equal to the limit.
      """
      if any(i >= limit for i in (a, b, c)):
        raise ValueError(
          f"Invalid point index in facet. All indices must be less than {limit}. "
          f"Indices: ({a}, {b}, {c})")
      return Triple(a, b, c)

    c_surface_points = (Point * len(surface_points))(
      *(Point(x, y, z) for x, y, z in surface_points))
    c_surface_facets = (Triple * len(surface_facet_to_point_index))(
      *(create_triple_with_limit(a, b, c, len(surface_points)
                                 ) for a, b, c in surface_facet_to_point_index))
    c_point_set_to_register = (Point * len(point_set_to_register))(
      *(Point(x, y, z) for x, y, z in point_set_to_register))
    registered_z_values = (ctypes.c_double * len(point_set_to_register))(
      *(z for _, _, z in point_set_to_register)
    )
    point_to_projected_facet_map = (ctypes.c_uint32 * len(point_set_to_register))()

    success = self.dll.TopologyRegisterPointSetToSurface(
      c_surface_points,
      c_surface_facets,
      ctypes.byref(c_surface_facets[0],
                   ctypes.sizeof(Triple) * len(c_surface_facets)),
      c_point_set_to_register,
      ctypes.byref(c_point_set_to_register[0],
                   ctypes.sizeof(Point) * len(c_point_set_to_register)),
      registered_z_values,
      point_to_projected_facet_map)

    if not success:
      raise CApiUnknownError("Failed to project points onto surface.")

    return registered_z_values, point_to_projected_facet_map
