"""Class for parsing world files associated with image files."""
###############################################################################
#
# (C) Copyright 2024, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import typing

import numpy as np

from ..data import RasterRegistrationTwoPoint
from .rotation import Rotation
from .util import default_type_error_message

if typing.TYPE_CHECKING:
  from ..data import Raster, Surface
  from ..common.typing import PointArray, PointArray2d

class CorruptWorldFileError(Exception):
  """Exception indicating the world file is corrupt."""

class WorldFile:
  """A world file associated with an image file.

  Parameters
  ----------
  contents
    A stream containing the contents of the world file.

  Raises
  ------
  CorruptWorldFileError
    If the world file is corrupt.
  """
  def __init__(self, contents: typing.TextIO) -> None:
    if not hasattr(contents, "readlines"):
      raise TypeError(
        default_type_error_message("contents", contents, typing.TextIO)
      )
    lines = contents.readlines()
    if len(lines) != 6:
      raise CorruptWorldFileError(
        "The world file must contain six lines."
      )
    parameters = []
    for line in lines:
      try:
        parameter = float(line)
      except (ValueError, TypeError) as error:
        raise CorruptWorldFileError(
          f"Invalid line in world file: {line}"
        ) from error

      if not np.isfinite(parameter):
        raise CorruptWorldFileError(
          f"Non-finite value in world file: {parameter}"
        )

      parameters.append(parameter)

    self._parameters = tuple(parameters)
    self._x_scale = parameters[0]
    self._y_skew = parameters[1]
    self._x_skew = parameters[2]
    self._y_scale = parameters[3]
    self._x_map_top_left = parameters[4]
    self._y_map_top_left = parameters[5]

    if self._x_skew == 0 and self._y_scale == 0:
      raise CorruptWorldFileError(
        "The x skew and y scale must not both be zero.")
    if self._x_scale == 0 and self._y_scale == 0:
      raise CorruptWorldFileError(
        "The x and y scale must not both be zero."
      )

    # :HACK: Don't process world file skew factor. We force the image to be
    # square by setting the scales to the same amount.
    # If we don't do this, Axis Aligned maps will be rotated, and there'll be
    # significant green triangles on the sides of the map between the raster and
    # surface.
    # This hack matches the application code for handling world files.
    self._x_scale = -self._y_scale

  def _validate_image_size(
    self,
    image_size: tuple[typing.Any, typing.Any]
  ) -> tuple[float, float]:
    """Validate the image_size and convert it to a tuple of two floats.

    Parameters
    ----------
    image_size
      The image size as a tuple in the form (width, height).

    Returns
    -------
    tuple
      The image size converted to be a tuple of two floats.

    Raises
    ------
    ValueError
      If the image_size does not have a length of at least 2.
      If the width or height is below zero or not finite.
    TypeError
      If the width or height could not be converted to a float.
    """
    try:
      width = float(image_size[0])
      height = float(image_size[1])
    except IndexError:
      raise ValueError("Image size must be a tuple of two floats.") from None

    if width <= 0 or height <= 0:
      raise ValueError("Image width and height must be greater than 0 pixels.")
    if not np.isfinite(width) or not np.isfinite(height):
      raise ValueError("Image width and height must be finite.")
    return width, height

  def _image_points(self, image_size: tuple[float, float]) -> PointArray2d:
    """Get the image points for an image with the given size."""
    width, height = image_size

    image_points = np.empty((2, 2), dtype=np.float64)
    image_points[0] = [0, height]
    image_points[1] = [width, 0]
    return image_points

  def _world_points(self, image_size: tuple[float, float]) -> PointArray:
    """Get the world points for an image with the given size."""
    width, height = image_size

    world_points = np.empty((2, 3), dtype=np.float64)
    world_points[0] = [self._x_map_top_left, self._y_map_top_left, 0]
    world_points[1] = [
      self._x_map_top_left + width * self._x_scale + height * self._x_skew,
      self._y_map_top_left + height * self._y_scale + width * self._y_skew,
      0
    ]
    return world_points

  def _canvas_corner_points(
    self,
    image_size: tuple[int, int],
    image_points: PointArray2d,
    world_points: PointArray
  ) -> PointArray:
    """Get the canvas points required to make the surface to put the raster on.

    Parameters
    ----------
    image_size
      The size of the image to be placed on the canvas.
    image_points
      The image points to use for registration.
    world_points
      The world points to use for registration.

    Returns
    -------
    PointArray
      The four corner points of a canvas suitable for raster registration.
    """
    width, height = image_size
    # Copy world points to avoid changing the caller's copy.
    world_points = np.copy(world_points)
    world_points[:, 2] = 1

    image_vector = image_points[0] - image_points[1]
    world_vector = world_points[0] - world_points[1]

    world_to_pixel_ratio = (
      np.linalg.norm(world_vector)
      / np.linalg.norm(image_vector)
    )

    rotation = Rotation.reorientation(
      [image_vector[0], image_vector[1], 0],
      world_vector
    )

    corner_points = np.empty((4, 3), dtype=np.float64)
    corner_points[0] = [0, 0, 0]
    corner_points[1] = [width, 0, 0]
    corner_points[2] = [width, height, 0]
    corner_points[3] = [0, height, 0]

    rotated_image_point_a = rotation.rotate_vector(
      (image_points[0][0], image_points[0][1], 0))
    corner_points = rotation.rotate_vectors(corner_points)
    corner_points[:, 0] -= rotated_image_point_a[0]
    corner_points[:, 1] -= rotated_image_point_a[1]
    corner_points *= world_to_pixel_ratio
    corner_points += world_points[0]

    return corner_points

  def resize_canvas_for_raster(
    self,
    canvas: Surface,
    raster: Raster
  ):
    """Use the world file to apply `raster` to `canvas`.

    This will update the geometry of `canvas` to be an appropriately placed
    and sized rectangular surface based on the information in this world
    file and apply the raster to Surface.

    Raises
    ------
    ValueError
      If the image size and the world file information would result in the
      surface having a zero extent (i.e. The top left hand corner of the
      rectangular surface would be the same point as the bottom right
      hand corner).
    """
    try:
      image_size = (raster.width, raster.height)
      self._validate_image_size(image_size)
    except AttributeError:
      raise TypeError("The raster parameter was not a raster.") from None
    world_points = self._world_points(image_size)
    image_points = self._image_points(image_size)
    try:
      canvas_points = self._canvas_corner_points(
        image_size,
        image_points,
        world_points
      )
    except ValueError as error:
      raise ValueError(
        "The world file parameters resulted in a Surface with an extent of "
        "zero."
      ) from error

    registration = RasterRegistrationTwoPoint(
      image_points,
      world_points,
      (0, 0, 1)
    )

    try:
      canvas.points = canvas_points
      canvas.facets = [[0, 1, 3], [1, 2, 3]]
      canvas.associate_raster(raster, registration)
    except AttributeError:
      raise TypeError("The surface parameter was not a surface.") from None
