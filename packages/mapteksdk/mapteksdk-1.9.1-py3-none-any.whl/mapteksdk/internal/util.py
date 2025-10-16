"""Internal utility functions used for implementing the Python SDK.

Unlike the common/util.py file these utility functions should not
be exposed to users of the SDK - they should be considered an internal
implementation details.

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

from collections.abc import Iterable
import ctypes
import sys
import typing

import numpy as np

if typing.TYPE_CHECKING:
  import numpy.typing as npt

# For wrapping native pointers
BUF_FROM_MEM = ctypes.pythonapi.PyMemoryView_FromMemory
BUF_FROM_MEM.restype = ctypes.py_object
BUF_FROM_MEM.argtypes = (ctypes.c_void_p, ctypes.c_int64, ctypes.c_int)

def array_from_pointer(ptr, value_count, ctypes_type) -> np.ndarray:
  """Create a numpy array containing data from a C array.

  The returned numpy array contains the data in the array the pointer points
  to. This does not make a copy of the data.

  Parameters
  ----------
  ptr : c_void_p
    Pointer to the start of memory location.
  byte_count : c_int64
    Number of bytes to allocate.
  numpy_type : c_int
    numpy dtype to create.

  Returns
  -------
  ndarray
    Numpy buffer array.
  """
  # define PyBUF_READ  0x100
  # define PyBUF_WRITE 0x200
  buffer = BUF_FROM_MEM(ptr, value_count * ctypes.sizeof(ctypes_type), 0x200)
  return np.frombuffer(buffer, ctypes_type)

def cartesian_to_spherical(points, origin=None):
  """Converts a list of Cartesian points to a list of spherical
  coordinates.

  Parameters
  ----------
  points : array_like
    The points to convert to Cartesian coordinates.
  origin : point
    The origin to use when calculating Cartesian coordinates.
    If not specified, the origin is taken to be [0, 0, 0]

  Returns
  -------
  numpy.ndarray
    Numpy array of 32 bit floating point numbers representing spherical
    coordinates equivalent to points. This array is of the shape
    (3, len(points)). The zeroth element is the ranges of the points,
    the first element is the alphas and the second element is the betas.
    This means the first point is the first column.

  Examples
  --------
  Get ranges of points from the origin.

  >>> from mapteksdk.internal.util import cartesian_to_spherical
  >>> points = [[1, 2, 2], [4, 0, 0], [0, 3, 4]]
  >>> sphericals = cartesian_to_spherical(points)
  >>> print(sphericals[0])
  [3., 4., 5.]

  Get the first point in the form [range, alpha, beta]

  >>> from mapteksdk.internal.util import cartesian_to_spherical
  >>> points = [[4, 4, 4], [-1, 1, 1], [-1, -1, 1]]
  >>> sphericals = cartesian_to_spherical(points)
  >>> print(sphericals[:, 0])
  [6.92820323 0.78539816 0.61547971]

  """
  if origin is None:
    origin = np.array([0, 0, 0], dtype=ctypes.c_double)
  elif not isinstance(origin, np.ndarray):
    origin = np.array(origin, dtype=ctypes.c_double)
  spherical = np.zeros((3, len(points)), dtype=ctypes.c_double)
  vector = points - origin
  # Calculate the ranges. Out is used to perform the calculation in-place.
  np.sqrt(np.square(vector[:, 0]) + np.square(vector[:, 1]) +
          np.square(vector[:, 2]), out=spherical[0])
  # Calculate the alphas.
  np.arctan2(vector[:, 0], vector[:, 1], out=spherical[1])
  # Calculate the betas.
  np.arcsin(np.divide(vector[:, 2], spherical[0], where=spherical[0] != 0),
            out=spherical[2])
  # The where spherical[0] != 0 is used to skip dividing by zero.
  return spherical

def spherical_to_cartesian(ranges, alphas, betas, origin=None):
  """Converts spherical coordinates to Cartesian coordinates.

  Parameters
  ----------
  ranges : list
    List of ranges to convert to Cartesian coordinates.
  alphas : list
    List of vertical angles to convert to Cartesian coordinates.
  betas : list
    List of horizontal angles to convert to Cartesian coordinates.
  origin : list
    The origin of the spherical coordinates. If None (default), the origin is
    assumed to be [0, 0, 0].

  Returns
  -------
  list of points
    List of Cartesian points equivalent to spherical points.

  Notes
  -----
  Ideally:
  cartesian_to_spherical(spherical_to_cartesian(ranges, alphas, betas)) =
    ranges, alphas, betas
  and spherical_to_cartesian(cartesian_to_spherical(points)) = points

  However it is unlikely to be exact due to floating point error.

  Raises
  ------
  ValueError
    If r < 0.

  """
  if not isinstance(ranges, np.ndarray):
    ranges = np.array(ranges)
  if not isinstance(alphas, np.ndarray):
    alphas = np.array(alphas)
  if not isinstance(betas, np.ndarray):
    betas = np.array(betas)
  if ranges.shape != alphas.shape or alphas.shape != betas.shape:
    raise ValueError("Ranges, alphas and betas must have same shape")
  if np.min(ranges) < 0:
    raise ValueError("All ranges must be greater than zero.")
  cartesians = np.zeros((ranges.shape[0], 3), dtype=ctypes.c_double)
  rcos = ranges * np.cos(betas)
  np.multiply(rcos, np.sin(alphas), out=cartesians[:, 0])
  np.multiply(rcos, np.cos(alphas), out=cartesians[:, 1])
  np.multiply(ranges, np.sin(betas), out=cartesians[:, 2])

  if origin is not None:
    origin = np.array(origin)
    cartesians = cartesians + origin

  return cartesians

def generate_type_string(required_type: type | Iterable[type]) -> str:
  """Converts a type or iterable of types to a string.

  Parameters
  ----------
  required_string
    type or iterable of types.
    This also supports type aliases, such as ObjectID[DataObject].

  Returns
  -------
  str
    The types converted to a string.
    If types is an iterable, this is each type converted to a string
    separated by a comma.
  """
  if sys.version_info > (3, 9):
    return str(required_type)
  # :TRICKY: Enums are both types and Iterables, so this must check
  # for type before Iterable to handle them correctly.
  if isinstance(required_type, type):
    return required_type.__name__
  if isinstance(required_type, Iterable):
    return ", ".join(item.__name__ for item in required_type)

  # The input might be a TypeAlias, for example ObjectID[PointSet].
  # This will handle simple type aliases, such as the one demonstrated
  # above.
  try:
    origin = required_type.__origin__.__name__
    args = ", ".join(arg.__name__ for arg in required_type.__args__)
    return f"{origin}[{args}]"
  except AttributeError:
    pass
  return str(required_type)

def default_type_error_message(
    argument_name: str,
    actual_value: typing.Any,
    required_type: type | Iterable[type]):
  """Provides a default message for type errors.

  Parameters
  ----------
  argument_name
    The name of the argument which was given an incorrect value.
  actual_value
    The incorrect value to given to the argument.
  required_type
    The required type of the argument or an iterable of acceptable
    types for the item.
  """
  actual_type_name = type(actual_value).__name__
  required_type_name = generate_type_string(required_type)

  return (f"Invalid value for {argument_name}: '{actual_value}' "
          f"(type: {actual_type_name}). Must be type: {required_type_name}.")

def append_rows_to_2d_array(array: np.ndarray, *rows: npt.ArrayLike):
  """Append rows to a 2D numPy array.

  Parameters
  ----------
  array
    Array to append rows to.
  rows
    Rows to append to the array. This supports both single rows, iterables of
    rows and mixtures of both.

  Returns
  -------
  new_array
    A copy of array with the rows appended.
  new_array_mask
    A boolean array which is True for rows which were added by this
    function and false for other rows.
  """
  before_count = array.shape[0]
  new_array = np.vstack((array, *rows))

  new_array_mask = np.full((new_array.shape[0]), False, dtype=np.bool_)
  new_array_mask[before_count:] = True
  return new_array, new_array_mask
