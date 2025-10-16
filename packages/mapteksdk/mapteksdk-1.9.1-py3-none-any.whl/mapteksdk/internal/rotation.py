"""Rotation represented using quaternions.

This module provides a simple implementation of rotations using
quaternions. Currently it only contains the functionality required
for rotating markers.

Warnings
--------
Vendors and clients should not develop scripts or applications against
this package. The contents may change at any time without warning.

"""
###############################################################################
#
# (C) Copyright 2020, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import math
import typing

import numpy as np

from .util import default_type_error_message

if typing.TYPE_CHECKING:
  from collections.abc import Sequence

  from ..common.typing import Vector3D, Vector3DArray

def _angle_between(first: np.ndarray, second: np.ndarray) -> float:
  """Calculate the angle between two vectors.

  Parameters
  ----------
  first
    The first vector. It should have shape (3,) and dtype float.
  second
    The second vector. It should have shape (3,) and dtype float.
  """
  first_length = np.linalg.norm(first)
  if first_length != 0:
    first /= first_length
  second_length = np.linalg.norm(second)
  if second_length != 0:
    second /= second_length
  dot_product = np.dot(first, second)
  dot_product = np.clip(dot_product, -1, 1)
  return np.arccos(dot_product)


class Rotation:
  """Class which represents rotations.

  Rotations are represented as quaternions - four floating point
  numbers Q0, Q1, Q2 and Q3.

  Parameters
  ----------
  q0
    First element of the rotation. Q0 = cos(angle / 2).
    Default value is 1.
  q1
    Second element of the rotation. Q1 = sin(angle / 2) * AxisX.
    Default value is 0.
  q2
    Third element of the rotation. Q2 = sin(angle / 2) * AxisY.
    Default value is 0.
  q3
    Fourth element of the rotation. Q3 = sin(angle / 2) * AxisZ.
    Default value is 0.

  Notes
  -----
  Quaternions are a way for representing rotations which is very efficient
  for computers. It is recommended to use the functions in this class instead
  of directly working with quaternions.

  """

  def __init__(
      self, q0: float=1.0, q1: float=0.0, q2: float=0.0, q3: float=0.0):
    self.q0: float = q0
    self.q1: float = q1
    self.q2: float = q2
    self.q3: float = q3

  @classmethod
  def axis_rotation(cls, angle: float, axis: Sequence[float]) -> typing.Self:
    """Returns a quaternion representing a rotation of angle
    radians around the specified axis.

    Parameters
    ----------
    angle
      The radians to rotate by. Positive indicates clockwise,
      negative indicates anticlockwise.(When looking in the
      direction of axis)
    axis
      A list containing three numbers representing the axis
      to rotate around. This is normalized before any calculations.

    Returns
    -------
    Rotation
      Rotation representing a rotation by the specified angle around the
      specified axis.

    Raises
    ------
    ValueError
      If axis does not have a length of 3.

    Notes
    -----
    Generally axis will either be [0, 0, 1], [0, 1, 0] or [0, 0, 1]
    representing the x, y and z axes respectively.

    """
    if len(axis) != 3:
      raise ValueError(f"Invalid Axis : {axis}.")

    x, y, z = axis

    # Normalize the axis.
    # If the axis is not normalized odd behaviours can be observed.
    # For example four rotations of 90 degrees not being
    # equivalent to one rotation of 360 degrees.
    axis_length = math.sqrt(x * x + y * y + z * z)
    if not math.isclose(axis_length, 1):
      x = x / axis_length
      y = y / axis_length
      z = z / axis_length

    sin_scalar = math.sin(angle / 2)
    result = cls()
    result.q0 = math.cos(angle / 2)
    result.q1 = sin_scalar * x
    result.q2 = sin_scalar * y
    result.q3 = sin_scalar * z

    return result

  @classmethod
  def create_from_orientation(
      cls,
      dip: float,
      plunge: float,
      bearing: float) -> typing.Self:
    """Converts dip, plunge and bearing into a Rotation object.

    Parameters
    ----------
    dip
      Relative rotation of the Y axis around the X axis in radians.
      This should be between -pi and pi (inclusive).
    plunge
      Relative rotation of the X axis around the Y axis in radians.
      This should be between -pi / 2 and pi / 2 (exclusive).
    bearing
      Absolute bearing of the X axis around the Z axis in radians.
      This should be between -pi and pi (inclusive).

    Returns
    -------
    Rotation
      Rotation equivalent to the passed dip, plunge and bearing.

    """
    # pylint: disable=too-many-locals;reason=The extra locals make it easier.
    # Based on code in: mdf/src/vulcan/api/Orientation.C
    dq0 = math.cos(-dip / 2)
    dq1 = math.sin(-dip / 2)

    pq0 = math.cos(-plunge / 2)
    pq2 = math.sin(-plunge / 2)

    bq0 = math.cos(-(bearing - (math.pi / 2)) / 2)
    bq3 = math.sin(-(bearing - (math.pi / 2)) / 2)

    dpq0 = pq0 * dq0
    dpq1 = pq0 * dq1
    dpq2 = pq2 * dq0
    dpq3 = -pq2 * dq1

    q0 = bq0 * dpq0 - bq3 * dpq3
    q1 = bq0 * dpq1 - bq3 * dpq2
    q2 = bq0 * dpq2 + bq3 * dpq1
    q3 = bq0 * dpq3 + bq3 * dpq0

    result = cls(q0, q1, q2, q3)
    result.normalize()

    return result

  @classmethod
  def create_from_heading_pitch_roll(
      cls,
      heading: float,
      pitch: float,
      roll: float) -> typing.Self:
    """Construct a rotation from heading, pitch and roll.

    Parameters
    ----------
    heading
      Angle in radians of the rotation about the -z axis.
      This should be between 0 and 2 * pi radians (inclusive).
    pitch
      Angle in radians of the rotation about the x axis.
      This should be between -pi / 2 and pi / 2 radians (inclusive).
    roll
      Angle in radians of the rotation about the y axis.
      This should be between -pi / 2 and pi / 2 radians (inclusive).

    Returns
    -------
    Rotation
      Rotation object representing a rotation of heading radians about the -z
      axis, then pitch radians about the x axis and then roll angles about
      the y axis.
    """
    # pylint: disable=too-many-locals;reason=The extra locals make it easier.
    if not 0 <= heading <= np.pi * 2:
      raise ValueError(f"Invalid heading: {heading}. 0 <= heading <= 2 * pi.")
    if not (-np.pi / 2) <= pitch <= (np.pi / 2):
      raise ValueError(f"Invalid pitch: {pitch}. -pi / 2 <= pitch <= pi / 2.")
    if not (-np.pi / 2) <= roll <= (np.pi / 2):
      raise ValueError(f"Invalid roll: {roll}. -pi / 2 <= roll <= pi / 2.")

    # Based on code in: mdf/src/geometry/api/Rotation.C
    rq0 = np.cos(roll / 2)
    rq2 = np.sin(roll / 2)
    pq0 = np.cos(pitch / 2)
    pq1 = np.sin(pitch / 2)
    hq0 = np.cos(heading / 2)
    hq3 = -np.sin(heading / 2)

    prq0 = pq0 * rq0
    prq1 = pq1 * rq0
    prq2 = pq0 * rq2
    prq3 = pq1 * rq2

    q0 = hq0 * prq0 - hq3 * prq3
    q1 = hq0 * prq1 - hq3 * prq2
    q2 = hq0 * prq2 + hq3 * prq1
    q3 = hq0 * prq3 + hq3 * prq0

    result = cls(q0, q1, q2, q3)
    result.normalize()
    return result

  @classmethod
  def create_from_look_and_up_direction(
    cls,
    look_direction: Sequence[float],
    up_direction: Sequence[float],
  ) -> typing.Self:
    """Construct a rotation from orientation vectors.

    The resulting rotation considers the transformation of taking the -Z axis
    to the specified look direction and the +Y axis to the up direction.

    Neither look_direction nor Rotation need to be normalised and only the
    component of Rotation orthogonal to look_direction is considered.

    Parameters
    ----------
    look_direction
      A list containing three numbers representing a vector forming the look
      direction. This does not need to be normalised.
    up_direction
      A list containing three numbers representing a vector forming the up
      direction. This does not need to be normalised.

    Returns
    -------
    Rotation
      Rotation object representing a rotation from orientation vectors.
    """
    if np.isnan(look_direction).all():
      nan = float("NaN")
      return cls(nan, nan, nan, nan)

    if not np.any(look_direction):
      return cls()  # Return the identity (i.e. no rotation).

    # Populate the rotation from the look vector.
    angle_z = _angle_between(look_direction, (0, 0, -1))
    if angle_z == 0.0:
      return cls()  # Return the identity (i.e. no rotation).

    axis = np.cross(look_direction, (0, 0, -1))
    if not np.any(axis):
      axis = (0, 1, 0)  # The unit Y vector.
    rotation = cls.axis_rotation(angle_z, axis)

    # Apply the up vector.
    up = rotation.rotate_vector(up_direction)
    up[2] = 0.0  # Throw away component not orthogonal to look vector.

    if np.any(up):
      # Rotate our transformed up vector to (0, 1, 0)
      angle_y = _angle_between(up.copy(), (0, 1, 0))
      if angle_y != 0.0:
        axis = np.cross(up, (0, 1, 0))
        if not np.any(axis):
          axis = (0, 0, -1)
        axis_rotation = cls.axis_rotation(angle_y, axis)
        axis_rotation.rotate(rotation)
        rotation = axis_rotation

    return rotation.invert_rotation()

  @classmethod
  def reorientation(
    cls,
    from_vector: Sequence[float],
    to_vector: Sequence[float]
  ) -> typing.Self:
    """Returns a rotation which rotates `from_vector` to `to_vector`."""
    from_ = np.empty((3,), np.float64)
    from_[:] = from_vector[:3]
    to = np.empty((3,), dtype=np.float64)
    to[:] = to_vector[:3]

    if not np.isfinite(from_).all() or not np.isfinite(to).all():
      raise ValueError(
        "Cannot reorient a vector containing a non-finite value."
      )

    if not np.any(from_) or not np.any(to):
      raise ValueError(
        "Cannot reorient a zero vector."
      )

    axis = np.cross(from_, to)
    if axis.any():
      angle = _angle_between(from_, to)
      return cls.axis_rotation(angle, axis)

    if np.dot(from_, to) > 0:
      # The vectors are in the same direction.
      # Return the identity rotation.
      return cls()

    # The vectors are anti-parallel (They go in opposite directions).
    # Pick an axis orthogonal to one of the vectors.
    axis = np.cross(from_, (1, 0, 0))
    if not axis.any():
      # The vector is parallel to the x axis, so this must use the y
      # axis instead.
      axis = np.cross(from_, (0, 1, 0))
    return cls.axis_rotation(np.pi, axis)

  def normalize(self):
    """Normalizes the quaternion if needed."""
    length = self.q0 * self.q0 + self.q1 * self.q1
    length += self.q2 * self.q2 + self.q3 * self.q3
    length = math.sqrt(length)

    if not math.isclose(length, 1):
      # If the length is close to 1, don't bother normalizing.
      self.q0 = self.q0 / length
      self.q1 = self.q1 / length
      self.q2 = self.q2 / length
      self.q3 = self.q3 / length

  def invert_rotation(self) -> Rotation:
    """Returns a Rotation which undoes this rotation."""
    return Rotation(self.q0, -self.q1, -self.q2, -self.q3)

  @property
  def quaternion(self) -> tuple[float, float, float, float]:
    """Returns the quaternion representing this rotation as a tuple.

    Returns
    -------
    tuple
      The tuple (q0, q1, q2, q3).

    """
    return (self.q0, self.q1, self.q2, self.q3)

  @property
  def orientation(self) -> tuple[float, float, float]:
    """Returns the orientation representing this rotation as a tuple.

    Note that unlike quaternion, each time this function is called the
    orientation is recalculated from the quaternions.

    Returns
    -------
    tuple
      The tuple (dip, plunge, bearing)

    """
    # Code based on mdf/src/vulcan/api/Orientation.C
    x_axis = np.array([1.0, 0.0, 0.0], dtype=np.float64)
    y_axis = np.array([0.0, 1.0, 0.0], dtype=np.float64)
    z_axis = np.array([0.0, 0.0, 1.0], dtype=np.float64)

    # Ignore the type because mypy can't detect that a numpy array of 64 bit
    # floats is compatible with a sequence of floats.
    x_axis_dash_dash = self.rotate_vector(x_axis) # type: ignore
    x_axis_dash_dash = x_axis_dash_dash / np.linalg.norm(x_axis_dash_dash)
    y_axis_dash_dash = self.rotate_vector(y_axis) # type: ignore
    y_axis_dash_dash = y_axis_dash_dash / np.linalg.norm(y_axis_dash_dash)

    y_axis_dash = np.cross(z_axis, x_axis_dash_dash)
    y_length = np.linalg.norm(y_axis_dash)
    if y_length != 0:
      y_axis_dash = y_axis_dash / np.linalg.norm(y_axis_dash)

    x_axis_dash = np.cross(y_axis_dash, z_axis)
    x_length = np.linalg.norm(x_axis_dash)
    if x_length != 0:
      x_axis_dash = x_axis_dash / np.linalg.norm(x_axis_dash)

    # The dip is the rotation angle which takes the transformed X axis back
    # to the XY plane.
    dip = np.arccos(np.clip(np.dot(y_axis_dash_dash, y_axis_dash), -1.0, 1.0))
    # Clip ensures the value is between -1 and 1 so the result will not
    # be NaN.

    # Adjust the sign based on the z component.
    if -y_axis_dash_dash[2] < 0:
      dip = -abs(dip)
    elif -y_axis_dash_dash[2] > 0:
      dip = abs(dip)
    else:
      dip = 0

    # Plunge is the rotation angle which takes the transformed X axis
    # back to the XY plane.
    plunge = np.arccos(np.clip(np.dot(x_axis_dash_dash,
                                      x_axis_dash), -1.0, 1.0))

    # Adjust the sign.
    if x_axis_dash_dash[2] < 0:
      plunge = -abs(plunge)
    elif x_axis_dash_dash[2] > 0:
      plunge = abs(plunge)
    else:
      plunge = 0

    # Bearing is the final Z axis rotation angle that aligns the
    # twice-transformed X axis back to the world axis.
    bearing = math.atan2(x_axis_dash[0], x_axis_dash[1])

    return (dip, plunge, bearing)

  @property
  def heading_pitch_roll(self) -> tuple[float, float, float]:
    """Get heading pitch and roll for this rotation.

    Returns
    -------
    tuple
      A tuple containing three floats. This is of the form
      (heading, pitch, roll) where heading, pitch and roll
      are in radians.
    """
    def sign(value: float) -> int:
      """Return the sign of value.

      Parameters
      ----------
      value
        The value to return the sign of.

      Returns
      -------
      int
        -1 if value < 0
        1 if value > 0
        0 if value == 0
      """
      if value < 0:
        return -1
      if value > 0:
        return 1
      return 0

    # Based on code in: mdf/src/geometry/api/Rotation.C
    x_axis = np.array([1, 0, 0])
    y_axis = np.array([0, 1, 0])
    z_axis = np.array([0, 0, 1])

    x_axis_dash_dash = self.rotate_vector(x_axis)
    y_axis_dash_dash = self.rotate_vector(y_axis)
    x_axis_dash = np.cross(y_axis_dash_dash, z_axis)
    y_axis_dash = np.cross(z_axis, x_axis_dash)

    roll = _angle_between(x_axis_dash_dash, x_axis_dash)
    roll *= sign(-x_axis_dash_dash[2])

    pitch = _angle_between(y_axis_dash_dash, y_axis_dash)
    pitch *= sign(y_axis_dash_dash[2])

    heading = np.arctan2(y_axis_dash[0], y_axis_dash[1])
    if heading < 0:
      heading += np.pi * 2

    return heading, pitch, roll

  @property
  def angle(self) -> float:
    """Returns the angle of the rotation. If multiple rotations have
    been performed, this is the magnitude as if only one rotation had been
    performed to get the rotation to its current state.

    Returns
    -------
    double
      The magnitude of the the rotation in radians.

    """
    return 2 * math.acos(self.q0)

  def rotate(self, rhs: Rotation):
    """Rotates this rotation by another rotation.

    Parameters
    ----------
    rhs
      Rotation to apply to this Rotation.

    """
    lq0, lq1, lq2, lq3 = self.q0, self.q1, self.q2, self.q3
    rq0, rq1, rq2, rq3 = rhs.q0, rhs.q1, rhs.q2, rhs.q3

    new_q0 = lq0 * rq0 - (lq1 * rq1 + lq2 * rq2 + lq3 * rq3)
    new_q1 = (lq0 * rq1 + lq1 * rq0) + (lq2 * rq3 - lq3 * rq2)
    new_q2 = (lq0 * rq2 + lq2 * rq0) + (lq3 * rq1 - lq1 * rq3)
    new_q3 = (lq0 * rq3 + lq3 * rq0) + (lq1 * rq2 - lq2 * rq1)

    self.q0 = new_q0
    self.q1 = new_q1
    self.q2 = new_q2
    self.q3 = new_q3

    self.normalize()

  def rotate_by_axis(self, angle: float, axis: list[float]):
    """Rotates by angle radians around the specified axis.

    Parameters
    ----------
    angle : float
      The radians to rotate by. Positive indicates clockwise,
      negative indicates anticlockwise (When looking in the
      direction of axis).
    axis : list
      List of length 3 representing Axis to rotate around.

    Notes
    ----
    Generally axis will either be [1, 0, 0], [0, 1, 0] or [0, 0, 1]
    representing the x, y and z axes respectively.

    """
    quaternion = self.axis_rotation(angle, axis)

    self.rotate(quaternion)

  def __rotation_helper(
      self, x: typing.Any, y: typing.Any, z: typing.Any):
    """Helper used to rotate things used by rotate_vector and rotate_vectors.

    Parameters
    ----------
    x
      X component(s) of the thing to rotate. Must support addition, subtraction
      and multiplication.
    y
      Y component(s) of the thing to rotate. Must support addition, subtraction
      and multiplication.
    z
      Z component(s) of the thing to rotate. Must support addition, subtraction
      and multiplication.

    Returns
    -------
    tuple
      Tuple containing x, y and z rotated by this rotation.

    """
    q0 = self.q1 * x + self.q2 * y + self.q3 * z
    q1 = self.q0 * x + (self.q2 * z - self.q3 * y)
    q2 = self.q0 * y + (self.q3 * x - self.q1 * z)
    q3 = self.q0 * z + (self.q1 * y - self.q2 * x)

    result_x = q0 * self.q1 + q1 * self.q0 - q2 * self.q3 + q3 * self.q2
    result_y = q0 * self.q2 + q1 * self.q3 + q2 * self.q0 - q3 * self.q1
    result_z = q0 * self.q3 - q1 * self.q2 + q2 * self.q1 + q3 * self.q0

    return result_x, result_y, result_z


  def rotate_vector(self, vector: Sequence[float]) -> Vector3D:
    """Rotates a vector by this Rotation and returns the rotated vector.

    This is not normalized so may need to be normalized before use.

    Parameters
    ----------
    vector
      Vector to rotate.

    Returns
    -------
    numpy.ndarray
      The rotated vector.

    Raises
    ------
    ValueError
      If vector does not have three components.

    """
    if len(vector) != 3:
      raise ValueError("Vectors must have three components.")
    x = vector[0]
    y = vector[1]
    z = vector[2]

    return np.array(self.__rotation_helper(x, y, z))

  def rotate_vectors(
      self, vectors: Vector3DArray) -> Vector3DArray:
    """As rotate_vector, however it can rotate multiple vectors at the same
    time.

    Parameters
    ----------
    vectors
      A numpy array of shape (n, 3) consisting of n vectors to rotate about
      the origin

    Returns
    -------
    np.ndarray
      vectors rotated by this rotation.

    Raises
    ------
    TypeError
      If vectors is not an ndarray.
    ValueError
      If vectors is not the correct shape.

    """
    if not isinstance(vectors, np.ndarray):
      raise TypeError(default_type_error_message("vectors",
                                                 vectors,
                                                 np.ndarray))

    if len(vectors.shape) != 2:
      raise ValueError("vectors must have 2 dimensions, not: "
                       f"{len(vectors.shape)}.")

    if vectors.shape[1] != 3:
      raise ValueError("Vectors must have three components, not: "
                       f"{vectors.shape[1]}.")

    x = vectors[:, 0]
    y = vectors[:, 1]
    z = vectors[:, 2]

    return np.column_stack(self.__rotation_helper(x, y, z))
