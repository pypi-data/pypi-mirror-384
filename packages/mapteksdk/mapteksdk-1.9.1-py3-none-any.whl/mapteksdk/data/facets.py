"""Facet data types.

This contains objects which use facet primitives. Currently there is only one
such data type (Surface).
"""
###############################################################################
#
# (C) Copyright 2020, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import ctypes
import functools
import logging
import typing

import numpy as np

from ..internal.data_property import DataProperty, DataPropertyConfiguration
from ..internal.lock import LockType
from ..internal.two_sided_colouring_mixin import TwoSidedColouringMixin
from .base import Topology, StaticType
from .objectid import ObjectID
from .primitives import (PointProperties, EdgeProperties, FacetProperties,
                         PointDeletionProperties)

if typing.TYPE_CHECKING:
  from .images import Raster
  from .image_registration_interface import RasterRegistration

# pylint: disable=too-many-lines
# pylint: disable=too-many-instance-attributes
log = logging.getLogger("mapteksdk.data")

class Surface(Topology, PointProperties, PointDeletionProperties, EdgeProperties,
              FacetProperties, TwoSidedColouringMixin):
  """Surfaces are represented by triangular facets defined by three points.

  This means a square or rectangle is represented by two facets, a cube
  is represented as twelve facets (six squares, each made of two facets).
  More complicated surfaces may require hundreds, thousands or more facets
  to be represented.

  Defining a surface requires the points and the facets to be defined - the
  edges are automatically populated when the object is saved. A facet
  is a three element long list where each element is the index of a point,
  for example the facet [0, 1, 4] would indicate the facet is the triangle
  between points 0, 1 and 4.

  See Also
  --------
  :documentation:`surface` : Help page for this class.

  Notes
  -----
  The edges of a facet network are derived from the points and facets and
  cannot be directly set.

  Examples
  --------
  Creating a pyramid with a square base.

  >>> from mapteksdk.project import Project
  >>> from mapteksdk.data import Surface
  >>> project = Project()
  >>> with project.new("surfaces/pyramid", Surface) as new_pyramid:
  >>>     new_pyramid.points = [[0, 0, 0], [2, 0, 0], [2, 2, 0],
  >>>                           [0, 2, 0], [1, 1, 1]]
  >>>     new_pyramid.facets = [[0, 1, 2], [0, 2, 3], [0, 1, 4], [1, 2, 4],
  >>>                           [2, 3, 4], [3, 0, 4]]
  """
  # pylint: disable=too-many-instance-attributes
  def __init__(
      self,
      object_id: ObjectID[Surface] | None=None,
      lock_type: LockType=LockType.READWRITE):
    is_new = not object_id
    if is_new:
      object_id = ObjectID(self._modelling_api().NewFacetNetwork())
      assert object_id

    super().__init__(object_id, lock_type)

    self._initialise_point_properties(False)
    self._initialise_edge_properties(has_immutable_edges=True)
    self._initialise_facet_properties()
    self.__raster_coordinates_overrides: dict[int, DataProperty] = {}
    """Dictionary of raster indices to coordinate override properties.

    The key is the raster index and the value is a DataProperty which
    contains the raster coordinate override array.

    A raster only has an override array if it is registered to the surface
    using RasterRegistrationOverride.
    """

  @classmethod
  def static_type(cls) -> StaticType:
    """Return the type of surface as stored in a Project.

    This can be used for determining if the type of an object is a surface.
    """
    return cls._modelling_api().FacetNetworkType()

  def associate_raster(
      self,
      raster: Raster,
      registration: RasterRegistration,
      desired_index: int=1):
    """Associates a raster to the surface using the specified registration.

    The RasterRegistration object passed to registration defines how the
    raster pixels are draped onto the surface.

    This edits both the surface and the raster so both objects must be
    open for read/write to call this function.

    Parameters
    ----------
    raster
      An open raster to associate with the surface.
    registration
      Registration object to use to associate the raster with the surface.
      As of 1.6, if the registration is used to associate a different
      raster to an object, then a copy of the registration will be
      made before associating the raster to the surface.
    desired_index
      The desired raster index for the raster. Rasters with higher
      indices appear on top of rasters with lower indices. This is
      1 by default.
      This must be between 1 and 255 (inclusive).

    Returns
    -------
    int
      The raster index of the associated raster.
      If the raster is already associated with the object this will be
      the index given when it was first associated.

    Raises
    ------
    ValueError
      If the registration object is invalid.
    ValueError
      If the raster index cannot be converted to an integer.
    ValueError
      If the raster index is less than 1 or greater than 255.
    ReadOnlyError
      If the raster or the surface are open for read-only.
    RuntimeError
      If the raster could not be associated with the surface.
    TypeError
      If raster is not a Raster object.
    AlreadyAssociatedError
      If the Raster is already associated with this object or another object.
    NonOrphanRasterError
      If the Raster is not an orphan.

    Notes
    -----
    If an error occurs after associating a colour map resulting in save()
    not being called, the colour map association can only be undone if
    the application's API version is 1.6 or greater.

    Prior to mapteksdk 1.6:
    Associating a colour map will not be undone if an error occurs.

    Examples
    --------
    This example shows creating a simple square-shaped surface and associates
    a raster displaying cyan and white horizontal stripes to cover the surface.
    In particular note that the call to this function is inside both
    the with statements for creating the surface and creating the raster.
    And as the raster is immediately associated with an object there is no
    need to provide a path for it.

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import Surface, Raster, RasterRegistrationTwoPoint
    >>> project = Project()
    >>> with project.new("surfaces/simple-rows", Surface) as new_surface:
    ...     new_surface.points = [[-10, -10, 0], [10, -10, 0],
    ...                           [-10, 10, 0], [10, 10, 0]]
    ...     new_surface.facets = [[0, 1, 2], [1, 2, 3]]
    ...     new_surface.facet_colours = [[200, 200, 0], [25, 25, 25]]
    ...     with project.new(None, Raster(width=32, height=32
    ...             )) as new_raster:
    ...         image_points = [[0, 0], [new_raster.width,
    ...                                  new_raster.height]]
    ...         world_points = [[-10, -10, 0], [10, 10, 0]]
    ...         orientation = [0, 0, 1]
    ...         new_raster.pixels[:] = 255
    ...         new_raster.pixels_2d[::2] = [0, 255, 255, 255]
    ...         registration = RasterRegistrationTwoPoint(
    ...             image_points, world_points, orientation)
    ...         new_surface.associate_raster(new_raster, registration)

    A raster cannot be associated with more than one surface. Instead,
    to associate a raster with multiple surfaces the raster must be copied
    and then the copy is associated with each surface. The below
    example uses this to create six square surfaces side by side, each
    with a 2x2 black and white chess board pattern raster applied to them.

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import Surface, Raster, RasterRegistrationTwoPoint
    >>> project = Project()
    >>> width = 32
    >>> height = 32
    >>> raster_path = "images/base_raster"
    >>> # Create a raster with a path.
    >>> with project.new(raster_path, Raster(width=width, height=height
    ...         )) as base_raster:
    ...     # This is a 2x2 chess black and white chess board pattern.
    ...     base_raster.pixels[:] = 255
    ...     base_raster.pixels_2d[0:16, 0:16] = [0, 0, 0, 255]
    ...     base_raster.pixels_2d[16:32, 16:32] = [0, 0, 0, 255]
    >>> # Create six surfaces each with a copy of the raster applied.
    >>> for i in range(6):
    ...     with project.new(f"checkered_surface_{i}", Surface) as surface:
    ...         surface.points = [[-10, -10, 0], [10, -10, 0],
    ...                           [-10, 10, 0], [10, 10, 0]]
    ...         surface.points[:, 0] += i * 20
    ...         surface.facets = [[0, 1, 2], [1, 2, 3]]
    ...         image_points = [[0, 0], [width, height]]
    ...         world_points = [surface.points[0], surface.points[3]]
    ...         orientation = [0, 0, 1]
    ...         registration = RasterRegistrationTwoPoint(
    ...             image_points, world_points, orientation)
    ...         # A copy of the raster is associated.
    ...         raster_id = project.copy_object(raster_path, None)
    ...         with project.edit(raster_id) as raster:
    ...             surface.associate_raster(raster, registration)
    """
    # pylint: disable=protected-access
    try:
      return registration._register(raster, self, desired_index)
    except AttributeError:
      # An AttributeError means it didn't have an _register() function,
      # so it must not be a RasterRegistration object.
      # This try-catch is preferable to isinstance, because it means
      # RasterRegistration does not need to be imported into this
      # file.
      raise TypeError("Registration must be RasterRegistration, "
                      f"not {type(registration)}") from None

  def _extra_invalidate_properties(self):
    super()._extra_invalidate_properties()
    self._invalidate_point_properties()
    self._invalidate_edge_properties()
    self._invalidate_facet_properties()
    self._invalidate_raster_override_properties()

  def _record_object_size_telemetry(self):
    self._record_point_telemetry()
    self._record_edge_telemetry()
    self._record_facet_telemetry()

  def clear_two_sided_colouring(self):
    """Clear the two sided colouring for the Surface.

    This sets has_two_sided_colouring to False. The back of
    the surface will no longer be coloured the back_colour.

    This has no effect if has_two_sided_colouring is already false.

    Notes
    -----
    This does not change the back colour.
    """
    self._clear_two_sided_colouring()

  def _invalidate_properties(self):
    self._invalidate_point_properties()
    self._invalidate_edge_properties()
    self._invalidate_facet_properties()
    self._invalidate_two_sided_colouring_properties()

  def _save_topology(self):
    self._save_point_properties()
    self._save_edge_properties()
    self._save_facet_properties()
    self._save_two_sided_colouring()
    self.__save_raster_overrides()

  def _get_raster_override_values(self, raster_index: int) -> np.ndarray:
    """Get raster override values for the specified raster index.

    Parameters
    ----------
    raster_index
      Index of the raster to get override values for.

    Returns
    -------
    ndarray
      The image points associated with the specified raster.

    Warnings
    --------
    This will trigger undefined behaviour if called on a raster index
    which is not a raster associated with using RasterRegistrationOverride.
    """
    try:
      return self.__raster_coordinates_overrides[raster_index].values
    except KeyError:
      new_overrides = self.__generate_override_property(raster_index)
      self.__raster_coordinates_overrides[
        raster_index] = new_overrides
      return new_overrides.values

  def __save_raster_overrides(self):
    """Save the image points used by RasterRegistrationOverride."""
    for _, override_property in self.__raster_coordinates_overrides.items():
      override_property.save()

  def _invalidate_raster_override_properties(self):
    """Invalidates the raster coordinate override properties."""
    self.__raster_coordinates_overrides = {}

  def __generate_override_property(self, raster_index: int) -> DataProperty:
    """Generate the DataProperty for an raster coordinate override array.

    This does not add the property to self.__raster_coordinates_overrides.

    Parameters
    ----------
    raster_index
      The index of the raster which the override points are for.

    Returns
    -------
    DataProperty
      Data property which allows for accessing the raster coordinate
      override array with the specified raster index.
    """
    return DataProperty(
      lock=self._lock,
      configuration=DataPropertyConfiguration(
        name="point_to_raster_coordinate_override",
        dtype=ctypes.c_float,
        default=float("nan"),
        column_count=2,
        primitive_count_function=self._modelling_api().ReadPointCount,
        cached_primitive_count_function=lambda: self.point_count,
        load_function=functools.partial(
          self._modelling_api().SurfacePointToRasterCoordinateOverrideR,
          raster_index=raster_index),
        save_function=functools.partial(
          self._modelling_api().SurfacePointToRasterCoordinateOverrideRW,
          raster_index=raster_index),
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode
      )
    )
