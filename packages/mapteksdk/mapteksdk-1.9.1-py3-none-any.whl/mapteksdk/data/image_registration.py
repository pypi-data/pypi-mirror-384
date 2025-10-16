"""Raster registration algorithms.

This module contains classes which implement the `RasterRegistration`
interface. This allows them to define how a `Raster` is displayed
on a `DataObject` subclass.
"""
###############################################################################
#
# (C) Copyright 2023, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import ctypes
import typing

import numpy as np

from ..capi import Sdp, SdpApi
from ..internal.lock import ObjectClosedError, LockType
from .base import Topology
from .errors import RegistrationTypeNotSupportedError
from .facets import Surface
from .image_registration_interface import RasterRegistration
from .objectid import ObjectID

if typing.TYPE_CHECKING:
  import sys
  import numpy.typing as npt

  from .images import Raster
  from ..common.typing import (
    Vector2DArray,
    Vector2DArrayLike,
    PointArray,
    PointArrayLike,
    Vector3D,
    Vector3DLike
  )

  if sys.version_info >= (3, 11):
    from typing import Self
  else:
    Self = typing.Any


def _check_raster_and_topology_validity(
    topology: typing.Any, raster: typing.Any):
  """Check a raster can be associated to the given topology.

  This checks that the raster and topology object are both the correct type
  and open for editing.

  Parameters
  ----------
  topology
    Topology object to check if it is in a valid state for raster association.
  raster
    Raster object to check if it is in a valid state for raster association.

  Raises
  ------
  TypeError
    If topology is not a Topology subclass, or if raster is not a Raster.
  ReadOnlyError
    If topology or raster are open for read-only.
  ObjectClosedError
    If topology or raster are closed.
  """
  if isinstance(raster, ObjectID):
    raise TypeError("raster must be a Raster opened for read/write not "
                    "an ObjectID.")
  if not isinstance(topology, Topology):
    raise TypeError("Cannot associate raster to object of type "
                    f"{type(topology)} because it is not a Topology object.")
  # pylint: disable=protected-access
  raster._raise_if_read_only("associate raster with a surface")
  topology._raise_if_read_only("associate a raster")
  # pylint: disable=protected-access;
  if raster.closed:
    raise ObjectClosedError(
      "Cannot set registration information on a closed raster.")


class RasterRegistrationNone(RasterRegistration):
  """Class representing no raster registration is present.

  Notes
  -----
  This is always considered valid, so raise_if_valid will never raise
  an error for this object.
  """
  def __eq__(self, other: typing.Any) -> bool:
    return isinstance(other, RasterRegistrationNone)

  @property
  def is_valid(self) -> bool:
    return True

  def raise_if_invalid(self):
    return

  def copy(self) -> Self:
    return type(self)()

  def _save(self):
    # No raster registration means nothing to save.
    pass

  @classmethod
  def _load(cls, raster: Raster) -> Self:
    registration = cls()
    registration.raster = raster
    return registration

class RasterRegistrationUnsupported(RasterRegistration):
  """Class representing a raster registration which is not supported.

  If you would like an unsupported registration method to be supported then
  use request support.

  Notes
  -----
  This is always considered invalid so raise_if_valid will always raise
  an error.
  """
  def __eq__(self, other: typing.Any) -> bool:
    return isinstance(other, RasterRegistrationUnsupported)

  @property
  def is_valid(self) -> bool:
    return False

  def raise_if_invalid(self):
    raise ValueError("Cannot perform operations on unsupported registration.")

  def copy(self) -> Self:
    return type(self)()

  def _save(self):
    # Doing nothing ensures Python is not making any changes to the
    # unsupported registration.
    pass

  @classmethod
  def _load(cls, raster: Raster) -> Self:
    registration = cls()
    registration.raster = raster
    return registration

class PointPairRegistrationBase(RasterRegistration):
  """Base class for registration objects which use image/world point pairs.
  """
  @classmethod
  def minimum_point_pairs(cls) -> int:
    """The minimum number of world / image point pairs required.

    Returns
    -------
    int
      The minimum number of world / image point pairs required.
    """
    raise NotImplementedError

  def raise_if_invalid(self):
    if self.world_points.shape[0] < self.minimum_point_pairs():
      raise ValueError(f"{type(self).__name__} requires at least "
                       f"{self.minimum_point_pairs()} world points. "
                       f"Given: {self.world_points.shape[0]}")
    if self.image_points.shape[0] < self.minimum_point_pairs():
      raise ValueError(f"{type(self).__name__} requires at least "
                       f"{self.minimum_point_pairs()} image points. "
                       f"Given: {self.image_points.shape[0]}")
    if self.image_points.shape[0] != self.world_points.shape[0]:
      raise ValueError("Image points and world points must contain the "
                       "same number of points. "
                       f"Image points contains: {self.image_points.shape[0]}, "
                       f"World points contains: {self.world_points.shape[0]}. ")
    if not np.all(np.isfinite(self.world_points)):
      raise ValueError(
        "World points contained a non-finite value."
      )
    if not np.all(np.isfinite(self.image_points)):
      raise ValueError(
        "Image points contained a non-finite value."
      )

  @property
  def image_points(self) -> Vector2DArray:
    """The points on the image used to map the raster onto an object.

    This is a numpy array of points in image coordinates where [0, 0] is the
    bottom left hand corner of the image and [width - 1, height - 1] is the top
    right hand corner of the image.

    Each of these points should match one of the world points. If the
    raster is mapped onto an object, the pixel at image_points[i] will
    be placed at world_points[i] on the surface.

    Raises
    ------
    ValueError
      If set to a value which cannot be converted to a two dimensional array
      containing two dimensional points or if any value in the array cannot
      be converted to a floating point number.
    TypeError
      If set to a value which cannot be converted to a numpy array.
    """
    return self.__image_points

  @image_points.setter
  def image_points(self, value: Vector2DArrayLike | None):
    if value is None:
      value = np.zeros((0, 2), dtype=ctypes.c_double)
    if not isinstance(value, np.ndarray):
      value = np.array(value, dtype=ctypes.c_double)
    if value.dtype != ctypes.c_double:
      value = value.astype(ctypes.c_double)
    if len(value.shape) != 2:
      raise ValueError(f"Image points must be two dimensional, not "
                       f"{len(value.shape)} dimensional.")
    if value.shape[1] != 2:
      raise ValueError(f"Each image point must have two dimensions, not "
                       f"{value.shape[1]} dimensions.")

    self.__image_points = value

  @property
  def world_points(self) -> PointArray:
    """The world points used to map the raster onto an object.

    This is a numpy array of points in world coordinates.

    Each of these points should match one of the image points. If the
    raster is mapped onto an object, the pixel at image_points[i] will
    be placed at world_points[i] on the surface.

    Raises
    ------
    ValueError
      If set to a value which cannot be converted to a two dimensional array
      containing three dimensional points or if any value in the array cannot
      be converted to a floating point number.
    TypeError
      If set to a value which cannot be converted to a numpy array.
    """
    return self.__world_points

  @world_points.setter
  def world_points(self, value: PointArrayLike | None):
    if value is None:
      value = np.zeros((0, 3), dtype=ctypes.c_double)
    if not isinstance(value, np.ndarray):
      value = np.array(value, dtype=ctypes.c_double)
    if value.dtype != ctypes.c_double:
      value = value.astype(ctypes.c_double)
    if len(value.shape) != 2:
      raise ValueError(f"World points must be two dimensional, not "
                       f"{len(value.shape)} dimensional.")
    if value.shape[1] != 3:
      raise ValueError(f"Each world point must have 3 dimensions, not "
                       f"{value.shape[1]} dimensions.")

    self.__world_points = value

  def _register(
      self, raster: Raster, topology: Topology, desired_index: int):
    # pylint: disable=protected-access
    # Support for these registration types is currently only implemented for
    # surfaces.
    if not isinstance(topology, Surface):
      raise RegistrationTypeNotSupportedError(type(self))
    _check_raster_and_topology_validity(topology, raster)
    if self.raster is not None:
      # This registration is already used by another object, so create
      # a copy. This ensures two objects don't share registration
      # information so changing the registration of one will not
      # change the registration of the other.
      copy = self.copy()
      return copy._register(raster, topology, desired_index)
    actual_index = topology._associate_raster(raster.id, desired_index)
    raster.registration = self
    return actual_index

class RasterRegistrationTwoPoint(PointPairRegistrationBase):
  """Represents a simple two-point raster registration.

  This simple registration uses two points and an orientation to project a
  raster onto an object (typically a Surface).

  Parameters
  ----------
  image_points
    The image points to assign to the object. See the property for more details.
  world_points
    The world points to assign to the object. See the property for more details.
  orientation
    The orientation to assign to the object. See the property for more details.

  See Also
  --------
  mapteksdk.data.facets.Surface.associate_raster : Pass a
    RasterRegistrationTwoPoint and a raster to this function to associate the
    raster with a surface.
  """
  def __init__(
      self,
      image_points: Vector2DArrayLike | None=None,
      world_points: PointArrayLike | None=None,
      orientation: Vector3DLike | None=None):
    super().__init__()
    self.image_points = image_points
    self.world_points = world_points
    self.orientation = orientation

  @classmethod
  def minimum_point_pairs(cls) -> int:
    return 2

  def raise_if_invalid(self):
    super().raise_if_invalid()
    if not np.all(np.isfinite(self.orientation)):
      raise ValueError("Orientation must be finite. "
                       f"Orientation: {self.orientation}")
    if np.all(np.isclose(self.orientation, 0)):
      raise ValueError("Orientation must not be a zero vector.")

  def copy(self) -> Self:
    self.raise_if_invalid()
    return type(self)(
      image_points=np.copy(self.image_points),
      world_points=np.copy(self.world_points),
      orientation=np.copy(self.orientation)
    )

  def _save(self):
    image_points = self.image_points
    world_points = self.world_points
    orientation = self.orientation
    if image_points.shape[0] != world_points.shape[0]:
      raise ValueError("Image points and world points must contain the "
                       "same number of points. "
                       f"Image points contains: {image_points.shape[0]}, "
                       f"World points contains: {world_points.shape[0]}. ")
    raster = self.raster
    if raster is None:
      raise RuntimeError(
        "Cannot save registration not associated with a raster.")
    # pylint: disable=protected-access
    raster._modelling_api().RasterSetControlTwoPoint(raster._lock.lock,
                                         image_points,
                                         world_points,
                                         orientation)

  @classmethod
  def _load(cls, raster: Raster) -> Self:
    # pylint: disable=protected-access
    registration = raster._modelling_api().RasterGetRegistration(
      raster._lock.lock)
    c_image_points, c_world_points, point_count, c_orientation = registration

    image_points = np.empty((point_count * 2), dtype=ctypes.c_double)
    image_points[:] = c_image_points
    image_points.shape = (point_count, 2)
    image_points.flags.writeable = not raster.is_read_only

    world_points = np.empty((point_count * 3), dtype=ctypes.c_double)
    world_points[:] = c_world_points
    world_points.shape = (point_count, 3)
    world_points.flags.writeable = not raster.is_read_only

    orientation = np.empty((3,), ctypes.c_double)
    orientation[:] = c_orientation
    orientation.flags.writeable = not raster.is_read_only

    registration = cls(image_points, world_points, orientation)
    registration.raster = raster
    return registration

  def __eq__(self, other: typing.Any) -> bool:
    if not isinstance(other, RasterRegistrationTwoPoint):
      return False

    return bool(np.all(np.isclose(self.image_points, other.image_points))
            and np.all(np.isclose(self.world_points, other.world_points))
            and np.all(np.isclose(self.orientation, other.orientation)))

  def __repr__(self) -> str:
    return (
      "RasterRegistrationTwoPoint("
      f"image_points={repr(self.image_points)},"
      f"world_points={repr(self.world_points)},"
      f"orientation={repr(self.orientation)}"
      ")"
    )

  @property
  def orientation(self) -> Vector3D:
    """The orientation vector used to map the raster onto an object.

    This is a numpy array of shape (3,) of the form [X, Y, Z] representing
    the direction from which the raster is projected onto the object. The
    components may all be nan for certain raster associations which do
    not use projections (eg: panoramic image onto a scan).

    If this is [0, 0, 1] the raster is projected onto the object from the
    positive z direction (above).
    [0, 0, -1] would project the raster onto the object from the negative
    z direction (below).

    Raises
    ------
    ValueError
      If set to a value which cannot be converted to a numpy array of
      shape (3,) or if any value in the array cannot be converted to
      a floating point number.
    TypeError
      If set to a value which cannot be converted to a numpy array.
    """
    return self.__orientation

  @orientation.setter
  def orientation(self, value: Vector3DLike | None):
    if value is None:
      value = np.full((3,), np.nan, dtype=ctypes.c_double)
    if not isinstance(value, np.ndarray):
      value = np.array(value, dtype=ctypes.c_double)
    if value.dtype != ctypes.c_double:
      value = value.astype(ctypes.c_double)
    if value.shape != (3,):
      raise ValueError("Orientation must have shape (3,), not: "
                       f"{value.shape}")
    self.__orientation = value

class RasterRegistrationMultiPoint(PointPairRegistrationBase):
  """Represents a multi-point raster registration.

  Represents a raster registration which uses eight or more points to
  project a raster onto an object (typically a Surface).

  Parameters
  ----------
  image_points
    The image points to assign to the object. See the property for more details.
  world_points
    The world points to assign to the object. See the property for more details.

  See Also
  --------
  mapteksdk.data.facets.Surface.associate_raster : Pass a
    RasterRegistrationMultiPoint and a raster to this function to associate the
    raster with a surface.

  Notes
  -----
  Though the minimum points required for multi point registration is eight,
  in most cases twelve or more points are required to get good results.
  """
  def __init__(
      self,
      image_points: Vector2DArrayLike | None=None,
      world_points: PointArrayLike | None=None):
    super().__init__()
    self.image_points = image_points
    self.world_points = world_points

  @staticmethod
  def _sdp() -> SdpApi:
    """Access the Spatial Data Processing C API."""
    return Sdp()

  @classmethod
  def minimum_point_pairs(cls) -> int:
    return 8

  def copy(self) -> Self:
    self.raise_if_invalid()
    return type(self)(
      image_points=np.copy(self.image_points),
      world_points=np.copy(self.world_points)
    )

  def __eq__(self, other: typing.Any) -> bool:
    if not isinstance(other, RasterRegistrationMultiPoint):
      return False

    return bool(np.all(np.isclose(self.image_points, other.image_points))
            and np.all(np.isclose(self.world_points, other.world_points)))

  def _save(self):
    image_points = self.image_points
    world_points = self.world_points
    if image_points.shape[0] != world_points.shape[0]:
      raise ValueError("Image points and world points must contain the "
                       "same number of points. "
                       f"Image points contains: {image_points.shape[0]}, "
                       f"World points contains: {world_points.shape[0]}. ")
    raster = self.raster
    if raster is None:
      raise RuntimeError(
        "Cannot save registration not associated with a raster.")
    # pylint: disable=protected-access
    self._sdp().RasterSetControlMultiPoint(
      raster._lock.lock,
      world_points,
      image_points
    )

  @classmethod
  def _load(cls, raster: Raster) -> Self:
    # pylint: disable=protected-access
    registration = raster._modelling_api().RasterGetRegistration(
      raster._lock.lock)
    c_image_points, c_world_points, point_count, _ = registration

    image_points = np.empty((point_count * 2), dtype=ctypes.c_double)
    image_points[:] = c_image_points
    image_points.shape = (point_count, 2)
    image_points.flags.writeable = not raster.is_read_only

    world_points = np.empty((point_count * 3), dtype=ctypes.c_double)
    world_points[:] = c_world_points
    world_points.shape = (point_count, 3)
    world_points.flags.writeable = not raster.is_read_only

    registration = cls(image_points, world_points)
    registration.raster = raster
    return registration


class RasterRegistrationOverride(RasterRegistration):
  """Provide the world to image point pairs directly.

  This is useful when importing data from a source where the registration
  algorithm has already been applied and the world / image point pairs
  for the registration are provided in a graphics-card ready form.

  Parameters
  ----------
  image_points
    The image points to use to register the raster to the surface.

  Notes
  -----
  Unlike the other registration methods provided by the SDK, if this one
  is used the image points cannot be recalculated when points are added /
  removed from the Surface. This means if the points or facets of the surface
  are changed, the raster must be discarded.

  Warnings
  --------
  If a raster associated with this registration type is inserted into
  a container, then attempting to read the raster's registration will
  give RasterRegistrationNone.
  """
  def __init__(self, image_points: npt.ArrayLike) -> None:
    super().__init__()
    self.__image_points = np.array(image_points, copy=True)
    self.__image_points.flags.writeable = False

  @property
  def image_points(self) -> np.ndarray:
    """The image points used to register this raster to the surface.

    This is an array of shape (point_count, 2).
    surface.point_to_raster_coordinate_override[i] is the point on the image
    which corresponds with surface.points[i].
    The image point is normalised based on the size of the image.
    (0.0, 0.0) is the bottom left corner of the raster, and (1.0, 1.0) is
    the top right corner.
    """
    return self.__image_points

  def raise_if_invalid(self):
    if np.any(self.image_points < 0.0):
      raise ValueError("All image points must be greater than 0.0.")
    if np.any(self.image_points > 1.0):
      raise ValueError("All image points must be less than 1.0.")

  def copy(self) -> Self:
    raise RuntimeError(
      "RasterRegistrationOverride does not support being associated with "
      "multiple Surfaces. Copying the registration is not supported.")

  def __eq__(self, other: typing.Any) -> bool:
    if not isinstance(other, RasterRegistrationOverride):
      return False

    return bool(np.all(np.isclose(self.image_points, other.image_points)))

  def _save(self):
    # Saving this type of registration is handled by the Surface,
    # not the Raster.
    pass

  @classmethod
  def _load(cls, raster: Raster) -> Self:
    raster_id = raster.id
    parent_id = raster_id.parent
    # Including facets.py here would introduce a circular dependency.
    if not parent_id:
      raise ValueError("This object does not have a raster override.")
    # pylint: disable=protected-access
    if not parent_id.is_a(raster._modelling_api().FacetNetworkType()):
      raise ValueError("This object does not have a raster override.")
    surface_id: ObjectID[Surface] = parent_id # type: ignore
    with Surface(surface_id, LockType.READ) as surface:
      raster_index = None
      for index, oid in surface.rasters.items():
        if oid == raster_id:
          raster_index = index
          break
      if raster_index is None:
        raise ValueError("This object does not have a raster override.")
      try:
        # pylint: disable=protected-access
        override_coordinates = surface._get_raster_override_values(raster_index)
      except KeyError as error:
        raise ValueError(
          "This object does not have a raster override.") from error

      registration = cls(image_points=override_coordinates)
      registration.raster = raster
      return registration

  def _register(
      self, raster: Raster, topology: Topology, desired_index: int):
    # pylint: disable=protected-access
    # Support for this registration type is currently only implemented for
    # surfaces.
    if not isinstance(topology, Surface):
      raise RegistrationTypeNotSupportedError(type(self))
    _check_raster_and_topology_validity(topology, raster)
    if not isinstance(raster.registration, RasterRegistrationNone):
      # The Python SDK cannot clear the registration type from the raster.
      # This makes it impossible to change the registration type from
      # any other type to RasterRegistrationOverride.
      raise ValueError(
        "Cannot override existing registration information for raster."
      )
    if self.raster is not None:
      # This registration is already used by another object, so create
      # a copy. This ensures two objects don't share registration
      # information so changing the registration of one will not
      # change the registration of the other.
      copy = self.copy()
      return copy._register(raster, topology, desired_index)
    raster.registration = self
    actual_index = topology._associate_raster(raster.id, desired_index)

    backing_array = topology._get_raster_override_values(desired_index)
    backing_array[:] = self.image_points
    return actual_index
