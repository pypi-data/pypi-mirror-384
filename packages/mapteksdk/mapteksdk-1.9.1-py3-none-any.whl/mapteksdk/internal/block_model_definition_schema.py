"""Schema for the JSON representation of block model definitions."""
###############################################################################
#
# (C) Copyright 2024, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import json
import typing

import numpy as np

if typing.TYPE_CHECKING:
  from collections.abc import MutableSequence

  class _JsonPoint(typing.TypedDict):
    """A point as represented in JSON."""
    X: float
    Y: float
    Z: float


  class _BlockSchema(typing.TypedDict):
    """The size of the parent or child blocks."""
    Description: str
    Min: _JsonPoint
    Max: _JsonPoint


  class _Extent(typing.TypedDict):
    """The extent of the block model."""
    Min: _JsonPoint
    Max: _JsonPoint


  class _Orientation(typing.TypedDict):
    """The orientation of the block model."""
    Dip: float
    Plunge: float
    Bearing: float


  class _Variable(typing.TypedDict):
    """A variable in the block model."""
    Name: str
    Type: str
    Description: str
    Default: str


class _DefinitionSchema(typing.TypedDict):
  """Typed dict representing the JSON for a block model definition."""
  Origin: _JsonPoint
  """The origin of the block model."""
  Schemas: MutableSequence[_BlockSchema]
  """Schemas which define the block sizes.

  The first schema is the parent block schema and all other schemas are
  subblock schemas.
  """
  Extent: _Extent
  """The Extent of the block model.

  The block counts are derived from the size of the blocks as per the schema
  and the extent.
  """
  Orientation: _Orientation
  """The rotation of the block model."""
  Variables: MutableSequence[_Variable]
  """The variables which should be defined on the block model."""


class InternalBlockModelDefinition:
  """Wraps around the JSON representation to provide a convenient interface.

  This hides the complexities of converting to and from JSON from the
  BlockModelDefinition class.
  """
  def __init__(self, schema: _DefinitionSchema) -> None:
    self.__schema = schema

  @classmethod
  def from_json(cls, data: str) -> typing.Self:
    """Read the block model definition from JSON."""
    schema = _DefinitionSchema(json.loads(data))
    return cls(schema)

  @classmethod
  def blank_definition(cls) -> typing.Self:
    """Create a blank block model definition.

    All properties are defaulted to NaN.
    """
    schema: _DefinitionSchema = {
      "Origin" : {
        "X" : 0.0,
        "Y" : 0.0,
        "Z" : 0.0
      },
      "Extent" : {
        "Max" : {
          "X" : np.nan,
          "Y" : np.nan,
          "Z" : np.nan
        },
        "Min" : {
          "X" : np.nan,
          "Y" : np.nan,
          "Z" : np.nan
        }
      },
      "Orientation" : {
        "Dip" : 0,
        "Plunge" : 0,
        "Bearing" : 90
      },
      "Schemas" : [],
      "Variables" : []
    }
    return cls(schema)

  def to_json(self) -> str:
    """Convert this object into JSON.

    Raises
    ------
    RuntimeError
      If any of the properties in the block model contain a NaN or infinite
      value.
    """
    schema = self.__schema
    try:
      return json.dumps(schema, allow_nan=False)
    except ValueError as error:
      raise RuntimeError(
        "Failed to write block model definition to JSON. "
        "One or more properties contained an invalid value."
      ) from error

  @property
  def is_subblocked(self):
    """If the model is subblocked."""
    return len(self.__schema["Schemas"]) == 2

  @property
  def origin(self) -> tuple[float, float, float]:
    """Get the origin of the definition.

    Editing the returned array will not change the origin stored in this
    object.
    """
    origin = self.__schema["Origin"]
    return self._json_point_to_tuple(origin)

  @origin.setter
  def origin(self, new_origin: tuple[float, float, float]):
    self.__schema["Origin"] = self._tuple_to_json(new_origin)

  @property
  def block_size(self) -> tuple[float, float, float]:
    """The primary block size."""
    block_size_schemas = self.__schema["Schemas"]

    if len(block_size_schemas) == 0:
      return (np.nan, np.nan, np.nan)

    # The first schema is always the parent schema.
    primary_schema = block_size_schemas[0]
    max_size = primary_schema["Max"]
    return self._json_point_to_tuple(max_size)

  @property
  def subblock_size(self) -> tuple[float, float, float]:
    """The subblock size.

    For dense block models, the subblock size is the block size.
    This returns the minimum block size for the last block size schema.
    This matches the behaviour of the edit block model definition panel in
    GeologyCore.
    """
    block_size_schemas = self.__schema["Schemas"]

    if len(block_size_schemas) == 0:
      return (np.nan, np.nan, np.nan)

    # The last schema is the subblock schema.
    child_schema = block_size_schemas[-1]
    min_size = child_schema["Min"]
    return self._json_point_to_tuple(min_size)

  @property
  def block_counts(self) -> tuple[int, int, int]:
    """The number of primary blocks in each dimension.

    The returned tuple is in the form: (X, Y, Z)
    Where X is the number of blocks in the model's X direction,
    Y is the number of blocks in the model's Y direction
    and Z is the number of blocks in the model's Z direction.
    """
    parent_block_size = self.block_size
    extent = self.extent

    if any(np.isnan(ordinate) or ordinate == 0 for ordinate in extent):
      # The block counts haven't been set yet, so there must be no blocks.
      return (0, 0, 0)

    return (
      int(extent[0] // parent_block_size[0]),
      int(extent[1] // parent_block_size[1]),
      int(extent[2] // parent_block_size[2]),
    )

  @property
  def orientation(self) -> tuple[float, float, float]:
    """The orientation of the model.

    The returned tuple is of the form: (dip, plunge, bearing).
    """
    orientation = self.__schema["Orientation"]
    return (orientation["Dip"], orientation["Plunge"], orientation["Bearing"])

  @orientation.setter
  def orientation(self, new_orientation: tuple[float, float, float]):
    if len(new_orientation) != 3:
      raise ValueError(
        "Orientation should have three components, "
        f"but it had: {len(new_orientation)}")
    new_orientation = (
      float(new_orientation[0]),
      float(new_orientation[1]),
      float(new_orientation[2])
    )
    if any(x < -360 or x > 360 for x in new_orientation):
      raise ValueError(
        "Orientation must be between -360 and 360 (inclusive)"
      )

    orientation = self.__schema["Orientation"]
    orientation["Dip"] = new_orientation[0]
    orientation["Plunge"] = new_orientation[1]
    orientation["Bearing"] = new_orientation[2]

  @property
  def extent(self) -> tuple[float, float, float]:
    """The extent covered by the definition."""
    extent = self.__schema["Extent"]
    min_point = extent["Min"]
    max_point = extent["Max"]

    x_range = max_point["X"] - min_point["X"]
    y_range = max_point["Y"] - min_point["Y"]
    z_range = max_point["Z"] - min_point["Z"]

    if any(np.isnan(ordinate) for ordinate in (x_range, y_range, z_range)):
      # The block counts haven't been set yet, so there must be no blocks.
      return (0, 0, 0)

    return (x_range, y_range, z_range)

  @property
  def variables(self) -> MutableSequence[_Variable]:
    """The variables defined by this block model definition."""
    return self.__schema["Variables"]

  def set_regular_block_size(
    self,
    new_block_size: tuple[float, float, float],
    subblock_ratio: float=1.0
  ):
    """Set the block and subblock size with a regular subblocking ratio.

    The subblocks have size new_block_size * subblock_ratio in every
    dimension.

    Parameters
    ----------
    new_block_size
      The size of the primary blocks.
    subblock_ratio
      The ratio of the size of the parent blocks to the child blocks.
      If 1.0 (default), then the block model will be dense.

    Raises
    ------
    ValueError
      If child_block_ratio is less than or equal to 0.0 or greater than 1.0.
    """
    if subblock_ratio <= 0 or subblock_ratio > 1.0:
      raise ValueError("Subblock ratio must not be below 0 or greater than 1.")

    child_block_size: tuple[float, float, float] | None
    if not np.isclose(subblock_ratio, 1.0):
      child_block_size = tuple(
        ordinate * subblock_ratio for ordinate in new_block_size
      ) # type: ignore
    else:
      child_block_size = None

    self.set_block_size(new_block_size, child_block_size)

  def set_block_size(
    self,
    block_size: tuple[float, float, float],
    subblock_size: tuple[float, float, float] | None
  ):
    """Set the primary and subblock size.

    For best compatibility, use set_block_size_regular() instead.

    Parameters
    ----------
    block_size
      The new primary block size.
    subblock_size
      The new subblock size.
      If None, the model will be set to have no subblocks.

    Raises
    ------
    ValueError
      If `subblock_size` is less than the parent block size in any dimension.
    """
    actual_block_size: _JsonPoint = self._tuple_to_json(block_size)
    actual_subblock_size: _JsonPoint | None = (
      self._tuple_to_json(subblock_size) if subblock_size is not None
      else None)
    if actual_subblock_size and any(
        primary < sub for primary, sub # type: ignore
        in zip(actual_block_size.values(), actual_subblock_size.values())):
      raise ValueError(
        f"Invalid subblock size: {actual_subblock_size}. All subblocks must "
        "be  smaller than the primary blocks which have size: "
        f"{actual_block_size}")
    if any(
        block_size <= 0 for block_size # type: ignore
        in actual_block_size.values()):
      raise ValueError(
        f"Invalid block size : {actual_block_size}. All ordinates must be "
        "greater than zero."
      )
    if actual_subblock_size and any(
        subblock_size <= 0 for subblock_size # type: ignore
        in actual_subblock_size.values()):
      raise ValueError(
        f"Invalid block size : {actual_block_size}. All ordinates must be "
        "greater than zero."
      )

    block_size_schemas: list[_BlockSchema] = []
    block_size_schemas.append(
      {
        "Description" : "",
        "Max" : actual_block_size.copy(),
        "Min" : actual_block_size.copy()
      }
    )

    if actual_subblock_size is not None:
      block_size_schemas.append(
        {
          "Description" : "",
          "Max" : actual_block_size.copy(),
          "Min" : actual_subblock_size.copy()
        }
      )

    # Query the block counts before updating the schema to ensure the block
    # count is not changed.
    block_counts = self.block_counts
    self.__schema["Schemas"] = block_size_schemas
    self._set_extent(self._calculate_extent(self.block_size, block_counts))

  def set_block_counts(self, new_counts: tuple[int, int, int]):
    """Set the block counts.

    Raises
    ------
    RuntimeError
      If the block count is set before setting the block sizes.
    TypeError
      If new_counts is not a sequence.
    ValueError
      If new_counts does not have enough elements or if any element is not
      an integer.
    """
    if any(np.isnan(ordinate) for ordinate in self.block_size):
      raise RuntimeError(
        "Cannot set the block count before the block size for newly created "
        "block model definition."
      )
    if len(new_counts) < 3:
      raise ValueError(
        "Block counts requires one value for X, Y and Z."
      )
    new_counts = (int(new_counts[0]), int(new_counts[1]), int(new_counts[2]))
    if any(count <= 0 for count in new_counts):
      raise ValueError(
        "Block counts must be above 0 in every dimension."
      )
    self._set_extent(self._calculate_extent(new_counts, self.block_size))

  def _calculate_extent(
    self,
    block_count: tuple[float, float, float],
    block_size: tuple[float, float, float]
  ) -> tuple[float, float, float]:
    """Calculate the extent for the given block count and block size."""
    # Both parameters are three tuples so we can guarantee this will return
    # a three tuple.
    return tuple(
      size * count for size, count in zip(block_size, block_count)
    ) # type: ignore

  def _set_extent(self, new_extent: tuple[float, float, float]):
    """Set the extent.

    Typically it is more robust to set the extent indirectly by setting the
    block count and sizes.
    """
    json_extent: _Extent = {
      "Min" : self._tuple_to_json((0, 0, 0)),
      "Max" : self._tuple_to_json(new_extent)
    }
    self.__schema["Extent"] = json_extent

  def _tuple_to_json(
    self,
    float_tuple: tuple[float, float, float]
  ) -> _JsonPoint:
    """Convert a three float tuple into a _JsonPoint.

    Raises
    ------
    ValueError
      If the input contains less than three ordinates or if any ordinate
      is a string which cannot be converted into a float.
    TypeError
      If any ordinate is a type which cannot be converted into a float.
    """
    if len(float_tuple) < 3:
      raise ValueError("Points require values for X, Y and Z.")
    return {
      "X" : float(float_tuple[0]),
      "Y" : float(float_tuple[1]),
      "Z" : float(float_tuple[2])
    }

  def _json_point_to_tuple(
      self, point: _JsonPoint) -> tuple[float, float, float]:
    """Convert a _JsonPoint to a three float tuple."""
    return (point["X"], point["Y"], point["Z"])
