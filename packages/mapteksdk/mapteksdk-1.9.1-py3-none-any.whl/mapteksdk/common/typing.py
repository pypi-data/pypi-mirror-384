"""Classes used for type hints.

The classes defined in this module are only intended to be used for type
checking. Imports from this module should always be inside a type checking
block:

>>> import typing
>>> if typing.TYPE_CHECKING:
...     from mapteksdk.data.type_checking import Point

This prevents this module from being imported at runtime, which can cause
the script to crash if the installed numpy does not support typing.

Warnings
--------
Importing this module requires numpy 1.21.0 or newer.

Notes
-----
The unions are quoted because sphinx cannot seem to handle unquoted unions
involving type aliases.
"""
###############################################################################
#
# (C) Copyright 2022, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

# pylint: disable=unused-import
from collections.abc import Sequence, MutableSequence
import typing

import numpy as np

# :TODO: SDK-805: Currently Point and PointArray (and other similar types) are
# identical. When numpy adds support for type hinting shapes, these will
# need to be updated to be different.
# The same goes for edge/facet/cell array.
Point: typing.TypeAlias = np.ndarray[typing.Any, np.dtype[np.float64]]
"""A single point.

This type hint indicates a numpy array of shape (3,) of 64 bit floats
representing a point in the form [X, Y, Z].

Notes
-----
X corresponds to East, Y corresponds to North and Z corresponds to up.
"""


PointLike: typing.TypeAlias = "Point | Sequence[float]"
"""A value which can be converted to a single point."""


PointArray: typing.TypeAlias = np.ndarray[typing.Any, np.dtype[np.float64]]
"""An array of points.

This type hint indicates a numpy array of shape (N, 3) (where
N is the point count) of 64 bit floats.

* The 0th column contains the X coordinates of each point.
* The 1st column contains the Y coordinates of each point.
* The 2nd column contains the Z coordinates of each point.

Notes
-----
X corresponds to East, Y corresponds to North and Z corresponds to up.
"""

PointArrayLike: typing.TypeAlias = "PointArray | Sequence[Sequence[float]]"
"""Represents a value which could be converted to an array of points."""

PointArray2d: typing.TypeAlias = np.ndarray[typing.Any, np.dtype[np.float64]]
"""An array of arrays of points.

This type hint indicates a numpy array of shape (N, M, 3) (where
N is the row count and M is the column count) of 64 bit floats.
"""


PointArray2dLike: typing.TypeAlias = (
  "PointArray2d | Sequence[Sequence[Sequence[float]]]"
)
"""Represents a value which could be converted to a PointArray2d."""

Edge: typing.TypeAlias = np.ndarray[typing.Any, np.dtype[np.uint32]]
"""A single edge.

This indicates a numpy array of shape (2,) where the first item is the index
of the start point of the edge and the second is the index of the end point
of the loop.
"""


EdgeLike: typing.TypeAlias = "Edge | Sequence[int]"
"""Indicates a value which can be converted into a single edge."""


EdgeArray: typing.TypeAlias = np.ndarray[typing.Any, np.dtype[np.uint32]]
"""An array of edges.

This type hint indicates a numpy array of shape (N, 2) (where
N is the edge count) of 32 bit integers. Each row is of
the form [start, end], representing the edge between
the point with an index of start and the point with an index
of end.
"""

EdgeArrayLike: typing.TypeAlias = "EdgeArray | Sequence[Sequence[int]]"
"""Represents a value which can be converted to an edge array."""

FacetArray: typing.TypeAlias = np.ndarray[typing.Any, np.dtype[np.uint32]]
"""An array of facets.

This type hint indicates a numpy array of shape (N, 3) (where
N is the facet count) of 32 bit integers. Each row is
of the form [A, B, C], representing the triangle between
the point with an index of A, the point with an index of B
and the point with an index of C.
"""

FacetArrayLike: typing.TypeAlias = "FacetArray | Sequence[Sequence[int]]"
"""Represents a value which can be converted to a facet array."""

CellArray: typing.TypeAlias = np.ndarray[typing.Any, np.dtype[np.uint32]]
"""An array of cells.

This type hint indicates a numpy array of shape (N, 4) (where
N is the cell count) of 32 bit integers. Each row is of
the form [A, B, C, D], representing the quadrilateral between
the point with an index of A, the point with an index of B,
the point with an index of C and the point with an index of D.
"""

CellArray2d: typing.TypeAlias = np.ndarray[typing.Any, np.dtype[np.uint32]]
"""A 2D array of cells.

This type hint indicates a numpy array of shape (N, M, 4) of 32 bit integers,
where N is the row count and M is the column count. Each cell is of
the form [A, B, C, D], representing the quadrilateral between
the point with an index of A, the point with an index of B,
the point with an index of C and the point with an index of D.
"""

IndexArray: typing.TypeAlias = np.ndarray[typing.Any, np.dtype[np.uint32]]
"""An array of indices into another array."""

BlockSize: typing.TypeAlias = np.ndarray[typing.Any, np.dtype[np.float64]]
"""The size of a single block.

This type hint indicates a numpy array of shape (3,) of 64 bit floats.
This is of the form [column_size, row_size, slice_size] where column_size
is the size of the block in the column direction, row_size is
the size of the block in the row direction and slice_size is
the size of the block in the slice direction.
"""

BlockSizeArray: typing.TypeAlias = np.ndarray[typing.Any, np.dtype[np.float64]]
"""An array of block sizes.

This type hint indicates a numpy array of shape (N, 3) (where
N is the block count) of 64 bit floats. Each row is of
the form [column_size, row_size, slice_size] where column_size
is the size of the block in the column direction, row_size is
the size of the block in the row direction and slice_size is
the size of the block in the slice direction.
"""

BlockCentroids3d: typing.TypeAlias = np.ndarray[
  typing.Any, np.dtype[np.float64]]
"""A 3D array of points.

This type hints indicates a numpy array of shape (S, R, C, 3) where:
S = Slice count.
R = Row count.
C = Column count.

Each row, column, slice contains a single point.
"""

Colour: typing.TypeAlias = np.ndarray[typing.Any, np.dtype[np.uint8]]
"""A single colour.

This is an array of shape (4,) of unsigned 8 bit integers.
This is of the form [red, green, blue, alpha].

* red = 0 indicates no red, red = 255 indicates maximum red.
* green = 0 indicates no green, green = 255 indicates maximum green.
* blue = 0 indicates no blue, blue = 255 indicates maximum blue.
* alpha = 0 indicates fully transparent, alpha = 255 indicates fully
  opaque.
"""

ColourLike: typing.TypeAlias = "Colour | Sequence[int]"
"""Values which can be converted to a colour."""

ColourArray: typing.TypeAlias = np.ndarray[typing.Any, np.dtype[np.uint8]]
"""An array of colours.

This indicates an array of shape (N, 4) where N is the colour count.
Each row is of the form [red, green, blue, alpha] as described
in colour above.
"""

ColourArray3d: typing.TypeAlias = np.ndarray[typing.Any, np.dtype[np.uint8]]
"""A 2D array of colours.

This indicates an array of shape (N, M, 4) where N is the number of rows and M
is the number of columns.
"""

ColourArrayLike: typing.TypeAlias = (
  "ColourArray | Sequence[int] | Sequence[Sequence[int]] | int"
)
"""Values which can be converted to a colour array."""

ColourArray3dLike: typing.TypeAlias = (
  "ColourArray3d | Sequence[int] | Sequence[Sequence[int]] | Sequence[Sequence[Sequence[int]]]"
)
"""Values which can be converted into a 2D array of colours."""

BooleanArray: typing.TypeAlias = np.ndarray[typing.Any, np.dtype[np.bool_]]
"""An array of booleans.

This indicates an array of booleans shape (N,) where N is the count.
"""

BooleanArrayLike: typing.TypeAlias = "bool | Sequence[bool] | BooleanArray"
"""A value which can be converted to a boolean array.

A single bool will be broadcast to fill the entire array with the same value.
"""

BooleanArray2d: typing.TypeAlias = np.ndarray[typing.Any, np.dtype[np.bool_]]
"""A 2D array of booleans.

This indicates an array of booleans shape (X, Y) where:
X = Row count.
Y = Column count.
"""

BooleanArray2dLike: typing.TypeAlias = (
  "bool | Sequence[Sequence[bool]] | BooleanArray2d"
)
"""A value which can be converted to a 2D boolean array.

A single bool will be broadcast to fill the entire array with the same value.
"""

BooleanArray3d: typing.TypeAlias = np.ndarray[typing.Any, np.dtype[np.bool_]]
"""A 3D array of booleans.

This indicates an array of booleans shape (S, R, C) where:
S = Slice count.
R = Row count.
C = Column count.
"""

BooleanArray3dLike: typing.TypeAlias = (
  "bool | Sequence[Sequence[Sequence[bool]]] | BooleanArray3d"
)
"""A value which can be converted to a 3D boolean array.

A single bool will be broadcast to fill the entire array with the same value.
"""

Float32Array: typing.TypeAlias = np.ndarray[typing.Any, np.dtype[np.float64]]
"""An array of 32 bit floats.

This indicates an array of floats of shape (N,) where N is the count.
"""

Float32ArrayLike: typing.TypeAlias = (
  "FloatArray | Sequence[float] | float"
)
"""Values which can be converted to a 32 bit float array."""

Float32Array2d: typing.TypeAlias = np.ndarray[typing.Any, np.dtype[np.float64]]
"""A 2D array of 32 bit floats.

This indicates an array of floats of shape (N, M).
"""

Float32Array2dLike: typing.TypeAlias = (
  "Float32Array2d | Sequence[float] | float"
)
"""Values which can be converted to a 3D 32 bit float array."""

FloatArray: typing.TypeAlias = np.ndarray[typing.Any, np.dtype[np.float64]]
"""An array of 64 bit floats.

This indicates an array of floats of shape (N,) where N is the count.
"""

FloatArrayLike: typing.TypeAlias = (
  "FloatArray | Sequence[float] | float"
)
"""Values which can be converted to a 64 bit float array."""

StringArray: typing.TypeAlias = np.ndarray[typing.Any, np.dtype[np.str_]]
"""An array of UTF-32 strings of fixed length.

This indicates an array of shape (N,) where N is the number of strings.
The maximum string length which can be stored in such an array is:

>>> string_array: StringArray
>>> max_string_length = string_array.dtype.itemsize // 4

Attempting to store a longer string inside such an array will result
in the string being truncated to the max string length.
"""

StringArrayLike: typing.TypeAlias = "StringArray | Sequence[str]"
"""A value which can be converted into a StringArray."""

Vector3D: typing.TypeAlias = np.ndarray[typing.Any, np.dtype[np.float64]]
"""A 3D vector.

This is a numpy array of shape (3,) of the form [X, Y, Z].
"""

Vector3DLike: typing.TypeAlias = "Vector3D | Sequence[float]"
"""A value which can be converted to a vector 3D."""

Vector3DArray: typing.TypeAlias = np.ndarray[typing.Any, np.dtype[np.float64]]
"""An array of 3D vectors.

This is a numpy array of shape (N, 3) where each row is a Vector3D.
N is the count of the vectors in the array.
"""

Vector2DArray: typing.TypeAlias = np.ndarray[typing.Any, np.dtype[np.float64]]
"""An array of 2D vectors.

This is a numpy array of shape (N, 2) where each row is a Vector2D.
N is the count of the vectors in the array.
"""

Vector2DArrayLike: typing.TypeAlias = "Vector2DArray | Sequence[Sequence[float]]"
"""A value which can be converted to a vector 2D array."""

MutableIndexSequence: typing.TypeAlias = MutableSequence[int]
"""A sequence of indices into an array.

This is similar to an IndexArray, except that it is mutable similar to a list.
This allows for the index to be updated more easily.
"""
