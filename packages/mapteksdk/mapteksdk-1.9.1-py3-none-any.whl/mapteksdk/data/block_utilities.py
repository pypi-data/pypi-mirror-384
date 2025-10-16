"""Utilities related to block models."""
###############################################################################
#
# (C) Copyright 2024, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import logging
import typing

import numpy as np

from ..internal.util import default_type_error_message
from .blocks import (
  DenseBlockModel,
  SubblockedBlockModel,
)
from .block_model_definition import (
  BlockModelDefinition,
  SubblockRatio
)
from .objectid import ObjectID

if typing.TYPE_CHECKING:
  # Import Project at runtime would result in an infinite import loop.
  from mapteksdk.project import Project

  from mapteksdk.common.typing import Vector3D, BlockSizeArray
  from mapteksdk.data.block_model_definition import Variable


LOG = logging.getLogger("mapteksdk.utilities.block")

_RATIO_TO_OFFSET: dict[SubblockRatio, float] = {
  SubblockRatio.NO_SUBBLOCKS : 0,
  SubblockRatio.ONE_HALF : -0.5,
  SubblockRatio.ONE_QUARTER : -1.5,
  SubblockRatio.ONE_EIGHTH : -3.5,
  SubblockRatio.ONE_SIXTEENTH : -7.5,
}
"""Offset in blocks required to fill a subblocked model with blocks."""


def create_dense_model_from_definition(
  project: Project,
  definition_id: ObjectID[BlockModelDefinition],
  use_primary_blocks: bool=True
) -> ObjectID[DenseBlockModel]:
  """Create a dense block model from a block model definition.

  By default, this will ignore any subblocking defined in the block model
  definition.

  Parameters
  ----------
  project
    Project to use to create the dense block model.
  definition_id
    Object ID of the block model definition to use as a template for the
    dense block model.
  use_primary_blocks
    If True (default), any subblocking in the block model definition will be
    ignored.
    If False and the block model definition defines subblocks, the subblock
    size will be used instead of the primary block size. This effectively
    creates a dense block model from the subblocks defined in the definition.
  """
  _validate_parameters(definition_id)

  try:
    definition_generator = project.read(definition_id)
  except AttributeError as error:
    # This cannot use default_type_error_message because the Project class
    # can only be imported during type checking.
    raise TypeError(
      "The project parameter must be a Project object, not "
      f"{project} (Type: {type(project).__name__})"
    ) from error

  with definition_generator as definition:
    x_size, y_size, z_size = definition.block_size
    x_count, y_count, z_count = definition.block_counts

    if not use_primary_blocks:
      subblock_ratio = definition.supported_subblock_ratio
      if subblock_ratio is not SubblockRatio.NO_SUBBLOCKS:
        x_size *= subblock_ratio.value
        y_size *= subblock_ratio.value
        z_size *= subblock_ratio.value

        x_count = int(x_count / subblock_ratio.value)
        y_count = int(y_count / subblock_ratio.value)
        z_count = int(z_count / subblock_ratio.value)

    with project.new(None, DenseBlockModel(
      col_res=x_size,
      row_res=y_size,
      slice_res=z_size,
      col_count=x_count,
      row_count=y_count,
      slice_count=z_count
    )) as model:
      _populate_model(definition, model)
      return model.id


def create_subblocked_model_from_definition(
  project: Project,
  definition_id: ObjectID[BlockModelDefinition],
  use_primary_blocks: bool=True
) -> ObjectID[SubblockedBlockModel]:
  """Create a subblocked block model from a block model definition.

  By default, the returned subblocked block model will be filled with primary
  blocks.

  Parameters
  ----------
  project
    Project to use to create the subblocked block model.
  definition_id
    Object ID of the block model definition to use as a template for the
    subblocked block model.
  use_primary_blocks
    If True (default), the returned subblocked block model will be filled
    with primary blocks.
    If False, the returned subblocked block model will be filled with subblocks.
  """
  _validate_parameters(definition_id)

  try:
    definition_generator = project.read(definition_id)
  except AttributeError as error:
    # This cannot use default_type_error_message because the Project class
    # can only be imported during type checking.
    raise TypeError(
      "The project parameter must be a Project object, not "
      f"{project} (Type: {type(project).__name__})"
    ) from error

  with definition_generator as definition:
    x_size, y_size, z_size = definition.block_size
    x_count, y_count, z_count = definition.block_counts
    with project.new(None, SubblockedBlockModel(
      col_res=x_size,
      row_res=y_size,
      slice_res=z_size,
      col_count=x_count,
      row_count=y_count,
      slice_count=z_count
    )) as model:
      subblock_ratio = (
        SubblockRatio.NO_SUBBLOCKS if use_primary_blocks
        else definition.supported_subblock_ratio
      )
      _populate_subblocks(
        model,
        definition.block_size,
        definition.block_counts,
        subblock_ratio
      )
      _populate_model(definition, model)
      return model.id


def create_model_from_definition(
  project: Project,
  definition_id: ObjectID[BlockModelDefinition],
  use_primary_blocks: bool=True
) -> ObjectID[DenseBlockModel] | ObjectID[SubblockedBlockModel]:
  """Create a block model from a block model definition.

  This will create a `DenseBlockModel` if the block model definition does not
  have a subblock schema and a `SubblockedBlockModel` if the block model
  definition has one.

  Parameters
  ----------
  project
    Project to use to create the block model.
  definition_id
    Object ID of the block model definition to use as a template for the
    block model.
  use_primary_blocks
    If True (default), the returned subblocked block model will be filled
    with primary blocks.
    If False, the returned subblocked block model will be filled with subblocks.
    Has no effect if the block model definition defines a dense block model.

  Notes
  -----
  The origin of a block model is determined based on the primary block in the
  zeroth row, slice and column.

  * Block model definitions consider the far corner of this block to be the
    origin (i.e. This is the only corner which does not border any blocks).
  * Block models consider the centre of this block to be the origin.

  Because of the above disagreement, the origin of the created block model
  will not be the same as the origin of the block model definition.
  The exact adjustment which is made by this function is also affected by the
  rotation of the block model definition.
  """
  _validate_parameters(definition_id)

  try:
    definition_generator = project.read(definition_id)
  except AttributeError as error:
    # This cannot use default_type_error_message because the Project class
    # can only be imported during type checking.
    raise TypeError(
      "The project parameter must be a Project object, not "
      f"{project} (Type: {type(project).__name__})"
    ) from error

  with definition_generator as definition:
    is_dense = definition.supported_subblock_ratio == SubblockRatio.NO_SUBBLOCKS

  if is_dense:
    return create_dense_model_from_definition(
      project,
      definition_id,
      use_primary_blocks
    )
  return create_subblocked_model_from_definition(
    project,
    definition_id,
    use_primary_blocks
  )

def _validate_parameters(definition_id):
  """Validate the parameters for definition to model functions.

  Raises
  ------
  TypeError
    If project is not a `Project` or if definition_id is not the `ObjectID`
    of a `BlockModelDefinition`.
  ValueError
    If `definition_id` is an `ObjectID` but is not for a
    `BlockModelDefinition`.
  """
  if (
    not isinstance(definition_id, ObjectID)
    or not definition_id.is_a(BlockModelDefinition)
  ):
    raise TypeError(
    default_type_error_message(
      "definition_id", definition_id, ObjectID[BlockModelDefinition]
    )
  )

def _populate_model(
  definition: BlockModelDefinition,
  model: DenseBlockModel | SubblockedBlockModel
):
  """Set `model`'s property based on `definition`."""
  orientation = definition.orientation
  model.set_orientation(
    np.deg2rad(orientation[0]),
    np.deg2rad(orientation[1]),
    np.deg2rad(orientation[2]),
  )

  model.origin = _calculate_origin(definition, model)

  for variable in definition.variables():
    _add_variable(model, variable)
  return model.id


def _populate_subblocks(
    model: SubblockedBlockModel,
    primary_block_resolution: tuple[float, float, float],
    primary_block_counts: tuple[int, int, int],
    subblock_ratio: SubblockRatio
):
  """Populate the subblocks for `model`.

  This will fill the model with subblocks with the specified
  `subblock_ratio`.

  Parameters
  ----------
  primary_block_resolution
    The resolution of the primary blocks. This is in the form
    (column_resolution, row_resolution, slice_resolution).
  primary_block_counts
    The number of primary blocks in each row, column and slice.
    This is of the form (column_count, row_count, slice_count).
  subblock_ratio
    The subblock ratio which determines the number of sub blocks to primary
    blocks.
  """
  if subblock_ratio is SubblockRatio.NO_SUBBLOCKS:
    subblock_size: tuple[float, float, float] = primary_block_resolution
    subblock_counts: tuple[int, int, int] = primary_block_counts
    offset = (0, 0, 0)
  else:
    subblock_size: tuple[float, float, float] = tuple(
      size * subblock_ratio.value for size in primary_block_resolution
    ) # type: ignore
    subblock_counts: tuple[int, int, int] = tuple(
      int(count / subblock_ratio.value) for count in primary_block_counts
    ) # type: ignore
    offset_ratio = _RATIO_TO_OFFSET.get(subblock_ratio, 0.0)
    offset = tuple(size * offset_ratio for size in subblock_size)

  block_centroids: BlockSizeArray = _calculate_subblock_centroids(
    subblock_size,
    subblock_counts
  )
  block_centroids += offset
  block_sizes = np.empty_like(block_centroids, dtype=np.float64)
  block_sizes[:] = subblock_size
  model.add_subblocks(
    block_centroids=block_centroids,
    block_sizes=block_sizes
  )


def _calculate_subblock_centroids(
  block_size: tuple[float, float, float],
  block_counts: tuple[int, int, int]
) -> BlockSizeArray:
  """Calculate the centroids to add to a subblocked model.

  This returns centroids to fill the model with equally sized blocks.

  Parameters
  ----------
  block_size
    The size of each block. This determines the distance between each
    centroid.
  block_counts
    The number of blocks in each axis. This is in the form (x, y, z).
  """
  def calculate_ordinate_values(count: int, size: float):
    range_array = np.linspace(0, count - 1, count, dtype=np.float64)
    range_array *= size
    return range_array
  x_values = calculate_ordinate_values(block_counts[0], block_size[0])
  y_values = calculate_ordinate_values(block_counts[1], block_size[1])
  z_values = calculate_ordinate_values(block_counts[2], block_size[2])

  grid = np.meshgrid(
    x_values,
    y_values,
    z_values,
  )
  array = np.array(grid).T.reshape(-1, 3)
  return array


def _add_variable(
  model: DenseBlockModel | SubblockedBlockModel,
  variable: Variable
):
  """Add `variable` to `model`."""
  if variable.data_type == BlockModelDefinition.VariableType.UNKNOWN:
    LOG.warning(
      "Skipping variable: '%s'. Its data type is not supported by "
      "the SDK.",
      variable.name
    )
    return
  default = variable.default
  if default is not None:
    dtype = variable.data_type.numpy_dtype
    if dtype is str:
      dtype = np.dtype(f"U{len(str(default))}")
    values = np.full(
      (model.block_count,),
      default,
      dtype=dtype
    )
  else:
    values = np.zeros(
    (model.block_count,),
    dtype=variable.data_type.numpy_dtype
  )
  model.block_attributes[variable.name] = values


def _calculate_offset(
  model: DenseBlockModel | SubblockedBlockModel
) -> Vector3D:
  """Calculate rotated half-block offset vector.

  This is the vector between the centre and outermost corner of the primary
  block in the zeroth slice, row and column in the model.
  """
  # There is no public accessor for the rotation object.
  # pylint: disable=protected-access
  rotation = model._rotation
  half_block_offset = tuple(size / 2 for size in model.block_resolution)
  rotated_half_block_offset = rotation.rotate_vector(half_block_offset)
  return rotated_half_block_offset


def _calculate_origin(
  definition: BlockModelDefinition,
  model: DenseBlockModel | SubblockedBlockModel
) -> tuple[float, float, float]:
  """Calculate the origin to give the block model.

  Block model definitions consider the origin to be the outermost corner
  of the block in the zeroth row, column and slice.
  Block models consider the origin to be the centre of the block in the
  zeroth row, column and slice.

  Given a rotated block model, this determines what origin is required to make
  the extents exactly match those of the block model definition.
  """
  rotated_half_block_offset = _calculate_offset(model)
  return tuple(
      x + y
      for x, y in zip(
        definition.origin, rotated_half_block_offset
      )
    )
