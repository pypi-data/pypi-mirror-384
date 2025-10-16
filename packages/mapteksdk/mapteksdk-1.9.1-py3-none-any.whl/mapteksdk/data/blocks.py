"""Block model data types.

Block models are objects constructed entirely from block primitives. There
are different kinds of block models, however only DenseBlockModels and
SubblockedBlockModels are currently supported.
"""
###############################################################################
#
# (C) Copyright 2020, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

from collections.abc import Sequence
import ctypes
import logging
import typing
import warnings

import numpy as np

from .base import Topology, StaticType
from .errors import DegenerateTopologyError, StaleDataError
from .objectid import ObjectID
from .primitives import BlockProperties
from .primitives.block_properties import BlockDeletionProperties
from ..internal.data_property import DataProperty, DataPropertyConfiguration
from ..internal.lock import LockType
from ..internal.mapping_view import MappingView
from ..internal.view_data_property import (
  ViewDataProperty,
  ViewDataPropertyConfiguration,
)

if typing.TYPE_CHECKING:
  from collections.abc import Mapping

  from .primitives.attribute_key import AttributeKey
  from .primitives.primitive_attributes import PrimitiveAttributes
  from ..common.typing import (
    BlockCentroids3d,
    BlockSizeArray,
    BooleanArray3d,
    BooleanArray3dLike,
  )

log = logging.getLogger("mapteksdk.data.blocks")

class InvalidBlockCentroidError(ValueError):
  """Error raised for block centroids which lie outside of the block model."""


class InvalidBlockSizeError(ValueError):
  """Error raised for invalid block sizes."""


def _validate_block_model_parameters(
    *,
    x_res: float | None=None,
    y_res: float | None=None,
    z_res: float | None=None,
    x_count: int | None=None,
    y_count: int | None=None,
    z_count: int | None=None,
    col_count: int | None=None,
    row_count: int | None=None,
    slice_count: int | None=None,
    col_res: float | None=None,
    row_res: float | None=None,
    slice_res: float | None=None):
  """Validates the parameters used to create a block model.

  Parameters
  ----------
  *_res : float
    The resolution parameters.
  *_count : int
    The count parameters.

  Returns
  -------
  tuple
    Tuple of parameters suitable to be unpacked into the Modelling
    function for creating a block model.

  Notes
  -----
  This is designed to be used for dense regular and dense subblocked
  block models. In the future it may be useful to use this with
  other types of block models which have the same parameters
  (e.g. sparse block models.). If it is used for this, the new type
  should not have the x_*, y_* and z_* parameters in its constructor
  and it should pass None to those parameters of this function.

  This function is unlikely to be applicable to HARP block models.
  """
  deprecated_arg_tuple = [x_res, y_res, z_res, x_count, y_count, z_count]
  if any(value is not None for value in deprecated_arg_tuple):
    if any(value is None for value in deprecated_arg_tuple):
      # :TODO: 2021-09-14 SDK-588: Change this to raise
      # a DegenerateTopologyError.
      message = ("*_res and *_count default arguments are deprecated "
                "and will be removed in a future version.")
      warnings.warn(DeprecationWarning(message))
    message = (
      "The *_res and *_count arguments are deprecated. "
      "They should be changed to the following:\n"
      "x_res -> col_res\n"
      "y_res -> row_res\n"
      "z_res -> slice_res\n"
      "x_count -> col_count\n"
      "y_count -> row_count\n"
      "z_count -> slice_count\n")
    warnings.warn(DeprecationWarning(message))
    col_res = x_res if x_res is not None else 1
    row_res = y_res if y_res is not None else 1
    slice_res = z_res if z_res is not None else 1
    col_count = x_count if x_count is not None else 1
    row_count = y_count if y_count is not None else 1
    slice_count = z_count if z_count is not None else 1

  # This is unpacked into the constructor so the order must
  # match the order the arguments should be passed into
  # the block network constructors.
  arg_tuple = (col_res, row_res, slice_res,
               col_count, row_count, slice_count)
  if None in arg_tuple:
    raise ValueError(
      "col_count, row_count, slice_count, "
      "col_res, row_res, slice_res must be specified. "
      f"Resolutions: ({col_res}, {row_res}, {slice_res}) "
      f"Counts: ({col_count}, {row_count}, {slice_count})")

  # Create new block model
  if col_res <= 0 or row_res <= 0 or slice_res <= 0: # type: ignore
    raise ValueError("*_res arguments must be greater than 0. "
                      f"Given: ({col_res}, {row_res}, {slice_res})")

  if col_count <= 0 or row_count <= 0 or slice_count <= 0: # type: ignore
    raise ValueError("*_count arguments must be greater than 0. "
                      f"Given: ({col_count}, {row_count}, {slice_count})")

  return arg_tuple

# =========================================================================
#
#                        DENSE BLOCK MODEL
#
# =========================================================================
class DenseBlockModel(Topology, BlockProperties):
  """A block model with equally sized blocks arranged in a regular 3D grid.

  A dense block model consists of blocks which are the same size arranged in a
  three dimensional grid structure. The block model is dense because it does
  not allow 'holes' in the model - every region in the grid must contain a
  block.

  For example, a dense block model with an col_res of 1, a row_res of 2
  and a slice_res of 3 means all of the blocks in the model are
  1 by 2 by 3 metres in size.
  If the dense block model's col_count was 10, the row_count
  was 15 and the slice_count was 5 then the model would consist of
  10 * 15 * 5 = 750 blocks each of which is 1x2x3 meters. These blocks
  would be arranged in a grid with 10 columns, 15 rows and 5 slices with
  no gaps.

  The blocks of a dense block model are defined at creation and cannot be
  changed.

  Parameters
  ----------
  col_count : int
    The number of columns of blocks in the block model.
    In the block model coordinate system, this is the number of blocks
    in the X direction.
    Must be greater than zero.
  row_count : int
    The number of rows of blocks in the block model.
    In the block model coordinate system, this is the number of blocks
    in the Y direction.
    Must be greater than zero.
  slice_count : int
    The number of slices of blocks in the block model.
    In the block model coordinate system, this is the number of blocks
    in the Z direction.
    Must be greater than zero.
  col_res : float
    The size of each block in the direction of the columns of the model.
    In the block model coordinate system, this is the size of the blocks
    in the X direction.
    Must be greater than zero.
  row_res : float
    The size each of block in the direction of the rows of the model.
    In the block model coordinate system, this is the size of the blocks
    in the Y direction.
    Must be greater than zero.
  slice_res : float
    The size of each block in the direction of the slices of the model.
    In the block model coordinate system, this is the size of the blocks
    in the Z direction.
    Must be greater than zero.
  x_res : float
    A deprecated alias for col_res. Kept for backwards compatibility.
  y_res  : float
    A deprecated alias for row_res. Kept for backwards compatibility.
  z_res : float
    A deprecated alias for slice_res. Kept for backwards compatibility.
  x_count : int
    A deprecated alias for col_count. Kept for backwards compatibility.
  y_count : int
    A deprecated alias for row_count. Kept for backwards compatibility.
  z_count : int
    A deprecated alias for slice_count. Kept for backwards compatibility.

  Raises
  ------
  ValueError
    If col_res, row_res, slice_res, col_count, row_count or slice_count are less
    than or equal to zero.
  TypeError
    If col_res, row_res, slice_res, col_count, row_count or slice_count is not
    numeric.
  TypeError
    If col_count, row_count or slice_count are numeric but not integers.

  See Also
  --------
  :documentation:`dense-block-model` : Help page for dense block model.

  Notes
  -----
  Parameters should only be passed for new block models.

  Examples
  --------
  Create a block model as described above and make every second block invisible.

  >>> from mapteksdk.project import Project
  >>> from mapteksdk.data import DenseBlockModel
  >>> project = Project()
  >>> with project.new("blockmodels/model", DenseBlockModel(
  ...         col_res=1, row_res=2, slice_res=3,
  ...         col_count=10, row_count=15, slice_count=5) as new_model:
  >>>     new_model.block_visibility[0::2] = True
  >>>     new_model.block_visibility[1::2] = False

  Note that the with statement can be made less verbose through the use
  of dictionary unpacking, as shown below.

  >>> from mapteksdk.project import Project
  >>> from mapteksdk.data import DenseBlockModel
  >>> project = Project()
  >>> parameters = {
  ...     "col_res" : 1, "row_res" : 2, "slice_res" : 3,
  ...     "col_count" : 10, "row_count" : 15, "slice_count" : 5,
  ... }
  >>> with project.new("blockmodels/model", DenseBlockModel(**parameters)
  ...         ) as new_model:
  >>>     new_model.block_visibility[0::2] = True
  >>>     new_model.block_visibility[1::2] = False
  """
  def __init__(
    self,
    object_id: ObjectID[DenseBlockModel] | None=None,
    lock_type: LockType=LockType.READWRITE,
    x_res: float | None=None,
    y_res: float | None=None,
    z_res: float | None=None,
    x_count: int | None=None,
    y_count: int | None=None,
    z_count: int | None=None,
    *,
    col_count: int | None=None,
    row_count: int | None=None,
    slice_count: int | None=None,
    col_res: float | None=None,
    row_res: float | None=None,
    slice_res: float | None=None):
    if object_id is None:
      arg_tuple = _validate_block_model_parameters(
        x_res=x_res, y_res=y_res, z_res=z_res,
        x_count=x_count, y_count=y_count, z_count=z_count,
        col_res=col_res, row_res=row_res, slice_res=slice_res,
        col_count=col_count, row_count=row_count, slice_count=slice_count)

      try:
        object_id = ObjectID(self._modelling_api().NewBlockNetworkDense(
          *arg_tuple))
      except ctypes.ArgumentError as error:
        raise TypeError("All resolutions must be numeric and all counts "
                        "must be integers. "
                        f"Resolutions: ({col_res}, {row_res}, {slice_res}) "
                        f"Counts: ({col_count}, {row_count}, {slice_count})"
                        ) from error

    super().__init__(object_id, lock_type)
    self._initialise_block_properties(has_immutable_blocks=True)

    self.__block_visibility_3d = ViewDataProperty(
      ViewDataPropertyConfiguration(
        "Block visibility 3D",
        self._block_visibility,
        lambda: (self.slice_count, self.row_count, self.column_count),
      )
    )
    self.__block_selection_3d = ViewDataProperty(
      ViewDataPropertyConfiguration(
        "Block selection 3D",
        self._block_selection,
        lambda: (self.slice_count, self.row_count, self.column_count),
      )
    )
    self.__block_centroids_3d = ViewDataProperty(
      ViewDataPropertyConfiguration(
        "Block visibility 3D",
        self._block_centroids,
        lambda: (self.slice_count, self.row_count, self.column_count, 3),
      )
    )

    if object_id is None:
      error_msg = 'Cannot create dense block model'
      log.error(error_msg)
      raise RuntimeError(error_msg)

  @classmethod
  def static_type(cls) -> StaticType:
    """Return the type of dense block model as stored in a Project.

    This can be used for determining if the type of an object is a dense
    block model.
    """
    return cls._modelling_api().BlockNetworkDenseType()

  @property
  def block_count(self) -> int:
    # This is row count * column count * slice count.
    return int(np.prod(self._cached_block_dimensions()))

  @property
  def block_centroids_3d(self) -> BlockCentroids3d:
    """Access block centroids by slice, row, column instead of index.

    This is a view on the block_centroids array reshaped into three dimensions
    such that block_centroids_3d[slice, row, column] is the centroid of the
    block in the specified specified slice, row and column.
    """
    return self.__block_centroids_3d.values

  @property
  def block_visibility_3d(self) -> BooleanArray3d:
    """Access block visibility by slice, row, column instead of index.

    This is a view of the block visibility reshaped into three dimensions
    such that block_visibility_3d[slice, row, column] gives the visibility for
    the block in the specified slice, row and column.

    Raises
    ------
    ValueError
      If set using a value which cannot be converted to a bool.
    ValueError
      If set to a value which cannot be broadcast to the right shape.

    Examples
    --------
    Make a 10x10x10 block model and make every block in the 4th row invisible,
    excluding blocks in the 0th slice.

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import DenseBlockModel
    >>> project = Project()
    >>> with project.new("blockmodels/visibility_3d", DenseBlockModel(
    ...         col_count=10, row_count=10, slice_count=10,
    ...         col_res=1, row_res=1, slice_res=0.5)) as new_blocks:
    ...     new_blocks.block_visibility_3d[:, 5, :] = False
    ...     new_blocks.block_visibility_3d[0, :, :] = True
    """
    return self.__block_visibility_3d.values

  @block_visibility_3d.setter
  def block_visibility_3d(self, new_visibility: BooleanArray3dLike):
    self.block_visibility_3d[:] = new_visibility

  @property
  def block_selection_3d(self) -> BooleanArray3d:
    """Access block selection by slice, row, column instead of index.

    This is a view of the block selection reshaped into three dimensions
    such that block_selection_3d[slice, row, column] is the visibility for
    the block in the specified slice, row and column.

    Raises
    ------
    ValueError
      If set using a value which cannot be converted to a bool.
    ValueError
      If set to a value which cannot be broadcast to the right shape.
    """
    return self.__block_selection_3d.values

  @block_selection_3d.setter
  def block_selection_3d(self, new_selection: BooleanArray3dLike):
    self.block_selection_3d[:] = new_selection

  @property
  def block_attributes_3d(self
      ) -> Mapping[AttributeKey | str, np.ndarray]:
    """Access block attributes by slice, row and column instead of index.

    This is a mapping of the block attributes reshaped into three dimensions
    such that block_attributes_3d[name][slice, row, column] is the attribute
    value for name in the specified slice, row and column.

    To assign to the a 3D block attributes array, you must use a slice.
    For example, to assign all values:

    >>> model.block_attributes_3d[name][:] = new_values
    """
    def get_item(owner: PrimitiveAttributes, key: str | AttributeKey):
      return owner[key].reshape(
        (self.slice_count, self.row_count, self.column_count))
    # PrimitiveAttributes are mappings of AttributeKey, but you can also get
    # the attributes by string names. This causes the type mismatch below.
    # It is easier to ignore the type mismatch than to resolve it.
    return MappingView(
      owner=self.block_attributes,
      get_item=get_item # type: ignore
    ) # type: ignore

  def _save_topology(self):
    self._save_block_properties()

  def _extra_invalidate_properties(self):
    super()._extra_invalidate_properties()
    self._invalidate_block_properties()
    self.__block_centroids_3d.invalidate()
    self.__block_visibility_3d.invalidate()
    self.__block_selection_3d.invalidate()

  def _record_object_size_telemetry(self):
    self._record_block_telemetry()

# =========================================================================
#
#                        DENSE SUBLOCKED BLOCK MODEL
#
# =========================================================================

class SubblockedBlockModel(
    Topology, BlockDeletionProperties):
  """A dense subblocked block model.

  Each primary block can contain subblocks allowing for the model to hold
  greater detail in areas of greater interest and less detail in areas of
  less interest.

  Block attributes, such as block_visibility and block_colour, have one value
  per subblock. A subblocked block model is empty when created and contains
  no blocks. Use the add_subblocks function to add additional subblocks to the
  model.

  Note that it is possible for a subblocked block model to include invalid
  subblocks. For example, subblocks which are outside of the extents of the
  block model. These blocks will not be displayed in the viewer.

  If interoperability with Vulcan is desired, the subblock sizes should always
  be a multiple of the primary block sizes (the resolution defined on
  construction) and you should be careful to ensure subblocks do not intersect
  each other.

  Parameters
  ----------
  col_count : int
    The number of columns of blocks in the block model.
    In the block model coordinate system, this is the number of blocks
    in the X direction.
    Must be greater than zero.
  row_count : int
    The number of rows of blocks in the block model.
    In the block model coordinate system, this is the number of blocks
    in the Y direction.
    Must be greater than zero.
  slice_count : int
    The number of slices of blocks in the block model.
    In the block model coordinate system, this is the number of blocks
    in the Z direction.
    Must be greater than zero.
  col_res : float
    The size of each block in the direction of the columns of the model.
    In the block model coordinate system, this is the size of the blocks
    in the X direction.
    Must be greater than zero.
  row_res : float
    The size each of block in the direction of the rows of the model.
    In the block model coordinate system, this is the size of the blocks
    in the Y direction.
    Must be greater than zero.
  slice_res : float
    The size of each block in the direction of the slices of the model.
    In the block model coordinate system, this is the size of the blocks
    in the Z direction.
    Must be greater than zero.
  x_res : float
    A deprecated alias for col_res. Kept for backwards compatibility.
  y_res  : float
    A deprecated alias for row_res. Kept for backwards compatibility.
  z_res : float
    A deprecated alias for slice_res. Kept for backwards compatibility.
  x_count : int
    A deprecated alias for col_count. Kept for backwards compatibility.
  y_count : int
    A deprecated alias for row_count. Kept for backwards compatibility.
  z_count : int
    A deprecated alias for slice_count. Kept for backwards compatibility.

  Raises
  ------
  ValueError
    If col_res, row_res, slice_res, col_count, row_count or slice_count are less
    than or equal to zero.
  TypeError
    If col_res, row_res, slice_res, col_count, row_count or slice_count is not
    numeric.
  TypeError
    If col_count, row_count or slice_count are numeric but not integers.

  See Also
  --------
  :documentation:`subblocked-block-model` : Help page for subblocked models.

  Notes
  -----
  Parameters should only be passed for new block models.

  Examples
  --------
  Creating a subblocked block model with two parent blocks, one of which
  is completely filled by a single subblock and another which is split into
  three subblocks. Each subblock is made invisible individually. Though
  the block model has two primary blocks, it has four subblocks so four
  values are required for the visibility.

  >>> from mapteksdk.project import Project
  >>> from mapteksdk.data import SubblockedBlockModel
  >>> centroids = [[0, 0, 0], [-1, 3, 0], [1, 3, 0], [0, 5, 0]]
  >>> sizes = [[4, 4, 4], [2, 2, 4], [2, 2, 4], [4, 2, 4]]
  >>> visibility = [True, True, False, False]
  >>> project = Project()
  >>> with project.new("blockmodels/subblocked_model", SubblockedBlockModel(
  ...         col_count=1, row_count=2, slice_count=1,
  ...         col_res=4, row_res=4, slice_res=4)) as new_blocks:
  ...     new_blocks.add_subblocks(centroids, sizes)
  ...     new_blocks.block_visibility = visibility
  """
  def __init__(self, object_id=None, lock_type=LockType.READWRITE,
               x_res=None, y_res=None, z_res=None,
               x_count=None, y_count=None, z_count=None, *,
               row_count=None, col_count=None, slice_count=None,
               row_res=None, col_res=None, slice_res=None):
    if object_id is None:
      arg_tuple = _validate_block_model_parameters(
        x_res=x_res, y_res=y_res, z_res=z_res,
        x_count=x_count, y_count=y_count, z_count=z_count,
        col_res=col_res, row_res=row_res, slice_res=slice_res,
        col_count=col_count, row_count=row_count, slice_count=slice_count)

      try:
        object_id = ObjectID(
          self._modelling_api().NewBlockNetworkSubblocked(*arg_tuple))
      except ctypes.ArgumentError as error:
        raise TypeError("All resolutions must be numeric and all counts "
                        "must be integers. "
                        f"Resolutions: ({col_res}, {row_res}, {slice_res}) "
                        f"Counts: ({col_count}, {row_count}, {slice_count})"
                        ) from error

    super().__init__(object_id, lock_type)
    self._initialise_block_properties(has_immutable_blocks=False)

  @classmethod
  def static_type(cls) -> StaticType:
    """Return the type of subblocked block model as stored in a Project.

    This can be used for determining if the type of an object is a subblocked
    block model.
    """
    return cls._modelling_api().BlockNetworkSubblockedType()

  def add_subblocks(self, block_centroids, block_sizes,
                    use_block_coordinates=True):
    """Adds an array of subblocks to the subblocked block model.

    By default the block_centroids should be in block model coordinates
    rather than world coordinates. See convert_to_world_coordinates() for
    more information.

    Parameters
    ----------
    block_centroid : array_like
      An array of block centroids of the new blocks. This is of the form:
      [x, y, z].
    block_sizes : array_like
      An array of block sizes of the new blocks, each containing three floats.
      This is of the form: [x_size, y_size, z_size].
    use_block_coordinates : bool
      If True (default) then the coordinates of the block centroids will be
      interpreted as block model coordinates (They will be passed through
      convert_to_world_coordinates()).
      If False, then the coordinates of the block centroids will be interpreted
      as world coordinates.

    Raises
    ------
    InvalidBlockSizeError
      If any block_size is less than zero or greater than the primary block
      size.
    InvalidBlockCentroidError
      If any block_centroid is not within the block model.
    ReadOnlyError
      If called when in read-only mode.

    Warnings
    --------
    By default this function assumes the input is in the "block model coordinate
    system" (see convert_to_world_coordinates()). The [0, 0, 0] in
    this coordinate system is located in the centre of the primary block
    in the 0th row, column and slice. This "half-block offset" means that the
    block centroids are offset by half a block relative to the bottom corner of
    the block model.

    Notes
    -----
    Calling this function in a loop is very slow. You should calculate all of
    the subblocks and pass them to this function in a single call.

    Examples
    --------
    The block centroids are specified in block model coordinates relative
    to the bottom left hand corner of the block model. In the below example,
    the block model is rotated around all three axes and translated
    away from the origin. By specifying the centroids in block model
    coordinates, the centroids remain simple.
    The output shows the resulting block centroids of the model. To get
    the same model with use_block_coordinates=False these are the centroids
    which would be required. As you can see they are significantly more
    complicated.

    >>> import math
    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import SubblockedBlockModel, Axis
    >>> centroids = [[-1.5, -1, -1], [-0.5, -1, -1], [-1, 1, -1],
    ...              [-1.5, -1, 1], [-0.5, -1, 1], [-1, 1, 1],
    ...              [-1.5, -1, 3], [-0.5, -1, 3], [-1, 1, 3]]
    >>> sizes = [[1, 2, 2], [1, 2, 2], [2, 2, 2],
    ...          [1, 2, 2], [1, 2, 2], [2, 2, 2],
    ...          [1, 2, 2], [1, 2, 2], [2, 2, 2]]
    >>> project = Project()
    >>> with project.new("blockmodels/transformed", SubblockedBlockModel(
    ...         col_count=1, row_count=2, slice_count=3,
    ...         col_res=4, row_res=4, slice_res=4)) as new_blocks:
    ...     new_blocks.origin = [94, -16, 12]
    ...     new_blocks.rotate(math.pi / 3, Axis.X)
    ...     new_blocks.rotate(-math.pi / 4, Axis.Y)
    ...     new_blocks.rotate(math.pi * 0.75, Axis.Z)
    ...     new_blocks.add_subblocks(centroids, sizes)
    ...     print(new_blocks.block_centroids)
    [[ 95.95710678 -16.64693601  11.96526039]
     [ 95.45710678 -15.86036992  12.32763283]
     [ 94.70710678 -16.09473435  10.42170174]
     [ 94.54289322 -17.87168089  12.67236717]
     [ 94.04289322 -17.08511479  13.03473961]
     [ 93.29289322 -17.31947922  11.12880852]
     [ 93.12867966 -19.09642576  13.37947395]
     [ 92.62867966 -18.30985966  13.74184639]
     [ 91.87867966 -18.54422409  11.8359153 ]]

    Specifying the block centroids in world coordinates is useful when
    the centroids are already available in world coordinates. This example
    shows copying the blocks from the model created in the previous example
    into a new model. Notice that the origin and rotations are the same for
    the copy. If this were not the case the centroids would likely lie
    outside of the block model and would not appear in the viewer.

    >>> import math
    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import SubblockedBlockModel, Axis
    >>> project = Project()
    >>> with project.new("blockmodels/transformed_copy", SubblockedBlockModel(
    ...         col_count=1, row_count=2, slice_count=3,
    ...         col_res=4, row_res=4, slice_res=4)) as new_blocks:
    ...     new_blocks.origin = [94, -16, 12]
    ...     new_blocks.rotate(math.pi / 3, Axis.X)
    ...     new_blocks.rotate(-math.pi / 4, Axis.Y)
    ...     new_blocks.rotate(math.pi * 0.75, Axis.Z)
    ...     with project.read("blockmodels/transformed") as read_blocks:
    ...         new_blocks.add_subblocks(read_blocks.block_centroids,
    ...                                  read_blocks.block_sizes,
    ...                                  use_block_coordinates=False)
    """
    self._raise_if_read_only("add subblocks")

    # Adding subblocks invalidates the block to grid index.
    self._delete_cached_block_to_grid_index()

    if not isinstance(block_centroids, np.ndarray):
      block_centroids = np.array(block_centroids, dtype=ctypes.c_double)

    if not isinstance(block_sizes, np.ndarray):
      block_sizes = np.array(block_sizes, dtype=ctypes.c_double)

    # Make sure the block centroids are sensible.
    if len(block_centroids.shape) != 2:
      raise InvalidBlockCentroidError(
        f"Invalid shape for block centroids: {block_centroids.shape}. "
        f"Must have 2 dimensions, not {len(block_centroids.shape)}.")
    if block_centroids.shape[1] != 3:
      raise InvalidBlockCentroidError(
        f"Invalid shape for block centroids: {block_centroids.shape}. "
        f"Must have 3 elements per centroid, not {block_centroids.shape[1]}")

    # Make sure the block sizes are sensible.
    if len(block_sizes.shape) != 2:
      raise InvalidBlockSizeError(
        f"Invalid shape for block sizes: {block_sizes.shape}. "
        f"Must have 2 dimensions, not {len(block_sizes.shape)}.")
    if block_sizes.shape[1] != 3:
      raise InvalidBlockSizeError(
        f"Invalid shape for block sizes: {block_sizes.shape}. "
        f"Must have 3 elements per block, not {block_sizes.shape[1]}")

    # We must make sure that block sizes and block centroids are the same
    # length as otherwise there will be blocks without sizes/centroids
    # which could cause odd behaviour if this function is called
    # multiple times.
    if block_sizes.shape[0] > block_centroids.shape[0]:
      log.warning(
        "add_subblocks() was called with %s block sizes "
        "and %s block centroids. The additional block sizes will be ignored.",
        block_sizes.shape[0],
        block_centroids.shape[0])
      block_sizes = block_sizes[:block_centroids.shape[0]]
    elif block_sizes.shape[0] < block_centroids.shape[0]:
      log.warning(
        "add_subblocks() was called with %s block sizes and "
        "%s block centroids. The additional block centroids will be ignored.",
        block_sizes.shape[0],
        block_centroids.shape[0])
      block_centroids = block_centroids[:block_sizes.shape[0]]

    # Ensure all block sizes are valid.
    if np.any(block_sizes <= 0):
      raise InvalidBlockSizeError(
        "All subblock sizes must be greater than zero.")
    if np.any(block_sizes > self.block_resolution):
      raise InvalidBlockSizeError(
        "A subblock cannot be larger than the primary block size.")

    if use_block_coordinates:
      # Ensure all of the centroids are valid.
      block_centroid_min = -0.5 * self.block_resolution
      block_centroid_max = (np.array(self._cached_block_dimensions()[::-1]) \
        - 0.5) * self.block_resolution
      if np.any(block_centroids < block_centroid_min):
        raise InvalidBlockCentroidError(
          "One or more block centroids are outside of the block model extent. "
          f"All block centroids must be greater than: {block_centroid_min}. "
          "(You may have forgotten the half-block offset).")
      if np.any(block_centroids > block_centroid_max):
        raise InvalidBlockCentroidError(
          "One or more block centroids are outside of the block model extent. "
          f"All block centroids must be lower than: {block_centroid_max} "
          "(You may have forgotten the half-block offset).")

      # Adjust the blocks based on the rotation of the model and
      # the origin.
      block_centroids = self.convert_to_world_coordinates(block_centroids)

    try:
      new_block_centroids = np.vstack((self.block_centroids, block_centroids))
      new_block_sizes = np.vstack((self.block_sizes, block_sizes))
    except Exception as exception:
      # Due to the above error checking, this shouldn't happen.
      log.error(exception)
      raise

    self._set_block_centroids(new_block_centroids)
    self._set_block_sizes(new_block_sizes)

  def rotate(self, angle, axis):
    inverse_rotation = self._rotation.invert_rotation()
    super().rotate(angle, axis)
    if self.block_centroids.shape[0] != 0:
      self._adjust_centroids_for_rotation(inverse_rotation, self._rotation)

  def set_rotation(self, angle, axis):
    inverse_rotation = self._rotation.invert_rotation()
    super().set_rotation(angle, axis)
    if self.block_centroids.shape[0] != 0:
      self._adjust_centroids_for_rotation(inverse_rotation, self._rotation)

  def set_orientation(self, dip, plunge, bearing):
    inverse_rotation = self._rotation.invert_rotation()
    super().set_orientation(dip, plunge, bearing)
    if self.block_centroids.shape[0] != 0:
      self._adjust_centroids_for_rotation(inverse_rotation, self._rotation)

  def _save_topology(self):
    self._save_block_properties()

  def _extra_invalidate_properties(self):
    super()._extra_invalidate_properties()
    self._invalidate_block_properties()

  def _record_object_size_telemetry(self):
    self._record_block_telemetry()

# =========================================================================
#
#                        SPARSE REGULAR BLOCK MODEL
#
# =========================================================================
class SparseBlockModel(
    Topology, BlockDeletionProperties):
  """A sparse regular block model.

  Similar to a dense block model, all blocks are the same size. The primary
  difference is a sparse block model allows for areas in the model
  extent to be empty (i.e. They do not contain any blocks).

  This allows for more compact storage for block models where a large
  proportion of the blocks do not contain data because blocks which do not
  contain data do not need to be stored. For block models in which
  most blocks contain data, a dense block model will provide more
  efficient storage.

  Parameters
  ----------
  col_count : int
    The number of columns of blocks in the block model.
    In the block model coordinate system, this is the number of blocks
    in the X direction.
    Must be greater than zero.
  row_count : int
    The number of rows of blocks in the block model.
    In the block model coordinate system, this is the number of blocks
    in the Y direction.
    Must be greater than zero.
  slice_count : int
    The number of slices of blocks in the block model.
    In the block model coordinate system, this is the number of blocks
    in the Z direction.
    Must be greater than zero.
  col_res : float
    The size of each block in the direction of the columns of the model.
    In the block model coordinate system, this is the size of the blocks
    in the X direction.
    Must be greater than zero.
  row_res : float
    The size each of block in the direction of the rows of the model.
    In the block model coordinate system, this is the size of the blocks
    in the Y direction.
    Must be greater than zero.
  slice_res : float
    The size of each block in the direction of the slices of the model.
    In the block model coordinate system, this is the size of the blocks
    in the Z direction.
    Must be greater than zero.

  Examples
  --------
  The following example demonstrates creating a simple sparse block
  model and adding it to a new view.

  >>> from mapteksdk.project import Project
  >>> from mapteksdk.data import SparseBlockModel, ObjectID
  >>> from mapteksdk.operations import open_new_view
  >>> def create_simple_model(project: Project, path: str
  ...     ) -> ObjectID[SparseBlockModel]:
  ...   '''Create a simple sparse block model.
  ...
  ...   The created sparse block model has three rows, slices and columns
  ...   however only the corner and centre blocks exist.
  ...
  ...   The central block is coloured red and the corner blocks are coloured
  ...   orange.
  ...
  ...   Parameters
  ...   ----------
  ...   project
  ...     The Project to use to create the sparse block model.
  ...   path
  ...     The path to create the sparse block model at.
  ...
  ...   Returns
  ...   -------
  ...   ObjectID
  ...     ObjectID of the newly created sparse block model.
  ...   '''
  ...   with project.new(path, SparseBlockModel(
  ...       row_count=3, slice_count=3, col_count=3,
  ...       row_res=1.5, col_res=1.25, slice_res=1.75
  ...       )) as model:
  ...     model.block_indices = [
  ...       [0, 0, 0], [2, 0, 0], [0, 2, 0], [0, 0, 2],
  ...       [2, 2, 0], [0, 2, 2], [2, 0, 2], [2, 2, 2],
  ...       [1, 1, 1]
  ...     ]
  ...     # Nine block indices means there are nine blocks in the model,
  ...     # so only nine colours need to be provided.
  ...     model.block_colours = [
  ...       [255, 165, 0, 255], [255, 165, 0, 255], [255, 165, 0, 255],
  ...       [255, 165, 0, 255], [255, 165, 0, 255], [255, 165, 0, 255],
  ...       [255, 165, 0, 255], [255, 165, 0, 255], [255, 0, 0, 255]
  ...     ]
  ...   return model.id
  ...
  >>> if __name__ == "__main__":
  ...   with Project() as main_project:
  ...     oid = create_simple_model(main_project, "block models/simple")
  ...     open_new_view(oid)
  """
  def __init__(self, object_id=None, lock_type=LockType.READWRITE,
               *,
               row_count=None, col_count=None, slice_count=None,
               row_res=None, col_res=None, slice_res=None):
    if object_id is None:
      arg_tuple = _validate_block_model_parameters(
        x_res=None, y_res=None, z_res=None,
        x_count=None, y_count=None, z_count=None,
        col_res=col_res, row_res=row_res, slice_res=slice_res,
        col_count=col_count, row_count=row_count, slice_count=slice_count)

      try:
        object_id = ObjectID(self._modelling_api().NewBlockNetworkSparse(
          *arg_tuple))
      except ctypes.ArgumentError as error:
        raise TypeError("All resolutions must be numeric and all counts "
                        "must be integers. "
                        f"Resolutions: ({col_res}, {row_res}, {slice_res}) "
                        f"Counts: ({col_count}, {row_count}, {slice_count})"
                        ) from error

    super().__init__(object_id, lock_type)
    self._initialise_block_properties(has_immutable_blocks=True)
    self.__block_indices = DataProperty(
      self._lock,
      configuration=DataPropertyConfiguration(
        name="block_indices",
        dtype=ctypes.c_uint32,
        default=0,
        column_count=3,
        load_function=self._modelling_api().BlockIndicesBeginR,
        save_function=self._modelling_api().BlockIndicesBeginRW,
        primitive_count_function=self._modelling_api().ReadBlockCount,
        cached_primitive_count_function=None,
        set_primitive_count_function=self._modelling_api().SetBlockCount,
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode
      ))

  @classmethod
  def static_type(cls) -> StaticType:
    return cls._modelling_api().BlockNetworkSparseType()

  @property
  def block_indices(self) -> np.ndarray:
    """Maps block indices to the row, column and slice containing the block.

    This is an array of shape (block_count, 3) where the ith row contains
    the [slice, row, column] of the ith block in the model.

    Changing the block_indices will change the block centroids. The changes
    will not be propagated to the centroids until save() is called.

    Warnings
    --------
    If any block is outside of the model (i.e. The slice is greater than
    the slice_count, the row is greater than the row count or the column
    is greater than the column count), the block will be silently removed
    when save() is called.

    Block indices can contain duplicate indices resulting in the model
    containing duplicate blocks (i.e. Two blocks with the same centroid
    and size).

    Notes
    -----
    This array is the same as the block_to_grid_index, except the 0th
    and 2nd columns have been swapped.

    * The block_indices stores the mapping as [slice, row, column].
    * The block_to_grid_index stores the mapping as [column, row, slice].
    """
    return self.__block_indices.values

  @block_indices.setter
  def block_indices(self, new_indices: Sequence[Sequence[int]]):
    self.__block_indices.values = new_indices

  @property
  def block_count(self):
    if self.__block_indices.are_values_cached:
      return self.__block_indices.values.shape[0]
    return self._modelling_api().ReadBlockCount(self._lock.lock)

  @property
  def block_centroids(self):
    if not self.is_read_only and self.__block_indices.are_values_cached:
      raise StaleDataError(
        "The block centroids may be stale. Call save() after editing "
        "block indices to update the centroids."
      )
    return super().block_centroids

  @property
  def block_sizes(self) -> BlockSizeArray:
    # All blocks in a sparse block model are the same size, so the sizes
    # array can be generated in Python.
    sizes = np.empty((self.block_count, 3), np.float64)
    sizes[:] = self.block_resolution
    sizes.flags.writeable = False
    return sizes

  def _save_topology(self):
    if self.block_count == 0:
      message = "Object must contain at least one block"
      raise DegenerateTopologyError(message)
    self.__block_indices.save()
    self._save_block_properties()

  def _extra_invalidate_properties(self):
    super()._extra_invalidate_properties()
    self.__block_indices.invalidate()
    self._invalidate_block_properties()

  def _record_object_size_telemetry(self):
    self._record_block_telemetry()
