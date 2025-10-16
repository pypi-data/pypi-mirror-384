"""Support for block primitives.

Block primitives are three dimensional cubes or rectangular prisms defined by
a centroid and a block size. Given a block with centroid [0, 0, 0] and size
[2, 4, 8] then the block will be the rectangular prism centred at [0, 0, 0]
and 2 metres by 4 metres by 8 metres in size.

"""
###############################################################################
#
# (C) Copyright 2020, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import ctypes
import logging
import typing

import numpy as np

from .primitive_attributes import (
  PrimitiveAttributes,
  PrimitiveType,
  AttributeKey
)
from ..rotation import RotationMixin
from ..errors import DegenerateTopologyError
from ...internal.data_property import DataProperty, DataPropertyConfiguration
from ...internal.rotation import Rotation

if typing.TYPE_CHECKING:
  import numpy.typing as npt

  from ...capi import ModellingApi
  from ...common.typing import (
    Point, PointArray, BlockSizeArray, BooleanArray, ColourArray,
    IndexArray, BlockSize)
  from ...internal.lock import ReadLock, WriteLock


log = logging.getLogger("mapteksdk.data")

# The following warning can be enabled if the <Primitive>Properties classes
# ended in Mixin as then pylint expects that the members are defined elsewhere.
# pylint: disable=no-member

class BlockProperties(RotationMixin):
  """Mixin class which provides spatial object support for block primitives.

  Functions and properties defined on this class are available on all
  classes which support blocks.
  """
  _block_visibility: DataProperty
  __block_colours: DataProperty
  _block_centroids: DataProperty
  __block_dimensions: tuple[int, int, int] | None
  _block_selection: DataProperty
  __block_sizes: DataProperty
  __block_attributes: PrimitiveAttributes | None
  __origin: Point | None
  __block_resolution: BlockSize | None
  __block_to_grid_index: IndexArray | None

  # Properties the inheriting object is expected to provide.
  # These are in a type checking block to ensure the child class implementation
  # is called instead of this implementation.
  if typing.TYPE_CHECKING:
    _lock: WriteLock | ReadLock

    @property
    def is_read_only(self) -> bool:
      """True if this object was opened in read-only mode."""
      raise NotImplementedError

    def _raise_if_read_only(self, operation: str):
      raise NotImplementedError

    def _raise_if_save_in_read_only(self):
      raise NotImplementedError

    def _invalidate_properties(self):
      raise NotImplementedError

    def _reconcile_changes(self):
      raise NotImplementedError

    def _record_size_for(self, name: str, size: int):
      raise NotImplementedError

    @classmethod
    def _type_name(cls) -> str:
      raise NotImplementedError

    @classmethod
    def _modelling_api(cls) -> ModellingApi:
      raise NotImplementedError

  def _initialise_block_properties(self, has_immutable_blocks: bool):
    """Initialises the block properties.

    This must be called during the __init__ function of child classes.

    Parameters
    ----------
    has_immutable_blocks
      If False, the block centroid and size arrays can be edited if the object
      is open for editing.
      If True, the block centroid and size arrays cannot be edited, even
      when the object is open for editing.
    """
    if has_immutable_blocks:
      # pylint: disable=unnecessary-lambda-assignment
      get_block_count = lambda: self.block_count
      set_block_count = None
    else:
      get_block_count = None
      set_block_count = self._modelling_api().SetBlockCount

    # :TRICKY: The block centroids and block sizes arrays must be the same
    # length. This sets up block centroids to be the primary property and
    # block sizes to be the secondary property. This is simpler than handling
    # there being two primary properties. Especially because new blocks can
    # only be added via the add_subblock() function so the two arrays should
    # always be the same length.
    self._block_centroids = DataProperty(
      lock=self._lock,
      configuration=DataPropertyConfiguration(
        name="block_centroids",
        dtype=ctypes.c_double,
        default=np.nan,
        column_count=3,
        primitive_count_function=self._modelling_api().ReadBlockCount,
        load_function=self._modelling_api().BlockCentroidsBeginR,
        save_function=self._modelling_api().BlockCentroidsBeginRW,
        cached_primitive_count_function=get_block_count,
        set_primitive_count_function=set_block_count,
        immutable=has_immutable_blocks,
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode
      )
    )

    self.__block_sizes = DataProperty(
      lock=self._lock,
      configuration=DataPropertyConfiguration(
        name="block_sizes",
        dtype=ctypes.c_float,
        default=np.nan,
        column_count=3,
        primitive_count_function=self._modelling_api().ReadBlockCount,
        load_function=self._modelling_api().BlockSizesBeginR,
        save_function=self._modelling_api().BlockSizesBeginRW,
        cached_primitive_count_function=lambda: self.block_count,
        set_primitive_count_function=None,
        immutable=has_immutable_blocks,
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode
      )
    )

    self._block_visibility = DataProperty(
      lock=self._lock,
      configuration=DataPropertyConfiguration(
        name="block_visibility",
        dtype=ctypes.c_bool,
        default=True,
        column_count=1,
        primitive_count_function=self._modelling_api().ReadBlockCount,
        cached_primitive_count_function=lambda: self.block_count,
        load_function=self._modelling_api().BlockVisibilityBeginR,
        save_function=self._modelling_api().BlockVisibilityBeginRW,
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode
      )
    )

    self.__block_colours = DataProperty(
      lock=self._lock,
      configuration=DataPropertyConfiguration(
        name="block_colours",
        dtype=ctypes.c_uint8,
        default=np.array([0, 226, 0, 255], dtype=ctypes.c_uint8),
        column_count=4,
        primitive_count_function=self._modelling_api().ReadBlockCount,
        cached_primitive_count_function=lambda: self.block_count,
        load_function=self._modelling_api().BlockColourBeginR,
        save_function=self._modelling_api().BlockColourBeginRW,
        is_colour_property=True,
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode
      )
    )

    self._block_selection = DataProperty(
      lock=self._lock,
      configuration=DataPropertyConfiguration(
        name="block_selection",
        dtype=ctypes.c_bool,
        default=False,
        column_count=1,
        primitive_count_function=self._modelling_api().ReadBlockCount,
        cached_primitive_count_function=lambda: self.block_count,
        load_function=self._modelling_api().BlockSelectionBeginR,
        save_function=self._modelling_api().BlockSelectionBeginRW,
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode
      )
    )

    self.__origin = None
    self.__block_resolution = None
    self.__block_dimensions = None
    self.__block_attributes = None
    self.__block_to_grid_index = None

  @property
  def block_count(self) -> int:
    """The count of blocks in the model."""
    if self._block_centroids.are_values_cached:
      # The block count may have changed so base it on the number of centroids.
      # This should be the same as returning the number of block sizes.
      return self.block_centroids.shape[0]
    # The block count has not been changed, so read the it from the
    # object.
    return self._modelling_api().ReadBlockCount(self._lock.lock)

  @property
  def block_resolution(self) -> BlockSize:
    """The resolution of the block model.

    The array [col_res, row_res and slice_res]. These are the same values
    as used to create the block model. Once the block model has been created,
    these values cannot be changed.

    """
    if self.__block_resolution is None:
      self.__block_resolution = self._get_block_resolution()
    return self.__block_resolution

  @property
  def col_res(self) -> int:
    """The number of columns of blocks in the model.

    This is the col_res parameter passed into the constructor.
    """
    return self.block_resolution[0]

  @property
  def row_res(self) -> int:
    """The number of rows of blocks in the model.

    This is the row resolution (row_res) passed into the constructor.
    """
    return self.block_resolution[1]

  @property
  def slice_res(self) -> int:
    """The number of slices of blocks in the model.

    This is the slice resolution (slice_res) passed into the constructor.
    """
    return self.block_resolution[2]

  @property
  def block_centroids(self) -> PointArray:
    """An array of the centre points of each block in the model.

    This is an ndarray of shape (block_count, 3) of the form:
    [[x1, y1, z1], [x2, y2, z2], ..., [xN, yN, zN]]
    where N is the block_count.

    """
    return self._block_centroids.values

  def _set_block_centroids(self, new_centroids: npt.ArrayLike):
    """Edit the centroids of the blocks.

    If set to None, they will be loaded from the Project when next requested.

    Raises
    ------
    ReadOnlyError
      If blocks are not settable.
    """
    self._block_centroids.values = new_centroids

  @property
  def block_sizes(self) -> BlockSizeArray:
    """An array of the sizes of each block in the model

    This is represented as an ndarray of shape (block_count, 3).
    Each row represents the size of one block in the form
    [column_size, row_size, slice_size] where column_size, row_size and
    slice_size are positive numbers.

    This means that the extent for the block with index i is calculated as:
    (block_centroids[i] - block_sizes[i] / 2,
    block_centroids[i] + block_sizes[i] / 2)

    Notes
    -----
    For DenseBlockModels, all block_sizes are the same.
    """
    return self.__block_sizes.values

  def _set_block_sizes(self, block_sizes: npt.ArrayLike):
    self.__block_sizes.values = block_sizes

  @property
  def block_colours(self) -> ColourArray:
    """An array of the colours of each block in the model.

    This is represented as a ndarray of shape (block_count, 4) where each row i
    represents the colour of the ith block in the model in the form
    [Red, Green, Blue, Alpha].

    When setting block colours, you may omit the Alpha component.
    """
    return self.__block_colours.values

  @block_colours.setter
  def block_colours(self, block_colours: npt.ArrayLike):
    self.__block_colours.values = block_colours

  @property
  def slice_count(self) -> int:
    """The number of slices in the block model.

    This is the number of blocks in the Z direction of the block model's
    coordinate system. Note that it only corresponds with the direction of the
    Z-axis if the block model is not rotated.
    This is the slice_count value passed to the constructor.
    """
    return self._cached_block_dimensions()[0]

  @property
  def row_count(self) -> int:
    """The number of rows in the block model.

    This is the number of blocks in the Y direction of the block model's
    coordinate system. Note that it only corresponds with the direction of the
    Y-axis if the block model is not rotated.
    This is the row_count value passed to the constructor.
    """
    return self._cached_block_dimensions()[1]

  @property
  def column_count(self) -> int:
    """The number of columns in the underlying block model.

    This is the number of blocks in the X direction of the block model's
    coordinate system. Note that it only corresponds with the direction of the
    X-axis if the block model is not rotated.
    This is the column_count value passed to the constructor.
    """
    return self._cached_block_dimensions()[2]

  @property
  def col_count(self) -> int:
    """Alias for column count.

    This exists so that the property can be referred to by the same name
    as the argument in the constructor.
    """
    return self.column_count

  @property
  def block_selection(self) -> BooleanArray:
    """An array which indicates which blocks are selected.

    This is represented as an ndarray of bools with shape:
    (block_count,). True indicates the block is selected; False indicates it
    is not selected.

    Notes
    -----
    In mapteksdk version 1.0, block_selection returned a 3D ndarray. To
    get the same functionality, see block_selection_3d property of dense
    block models.
    """
    return self._block_selection.values

  @block_selection.setter
  def block_selection(self, block_selection: npt.ArrayLike):
    self._block_selection.values = block_selection

  @property
  def block_visibility(self) -> BooleanArray:
    """An array which indicates which blocks are visible.

    This is represented as an ndarray of bools with shape: (block_count,).
    True indicates the block is visible, False indicates it is not visible.

    Notes
    -----
    In mapteksdk version 1.0 block_visibility returned a 3D ndarray. To
    get the same functionality, see block_visibility_3d property of dense
    block models.
    """
    return self._block_visibility.values

  @block_visibility.setter
  def block_visibility(self, block_visibility: npt.ArrayLike):
    self._block_visibility.values = block_visibility

  @property
  def origin(self) -> Point:
    """The origin of the block model represented as a point.

    Setting the origin will translate the entire block model to be
    centred around the new origin.

    Warnings
    --------
    The origin is located in the centre of the block in the 0th row,
    0th column and 0th slice. Thus the origin is offset by half a block
    relative to the bottom corner of the block model.

    Notes
    -----
    For DenseBlockModels the resulting changes to the block_centroids will
    not occur until save is called.
    For SubblockedBlockModels the resulting changes to the block_centroids
    are immediately available, however changing the origin of such a model
    is slower.

    Examples
    --------
    Changing the origin will change the block model centroids, in this case
    by translating them by 1 unit in the X direction, 2 units in the Y direction
    and 3 units in the Z direction. Note that as this is a DenseBlockModel,
    the model needs to be saved (in this case via closing ending the with block)
    before the changes to the centroids will occur.

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import DenseBlockModel
    >>> project = Project()
    >>> with project.new("blockmodels/model", DenseBlockModel(
    ...         col_res=2, row_res=3, slice_res=4,
    ...         col_count=2, row_count=2, slice_count=2)) as new_model:
    ...     new_model.origin = [1, 2, 3]
    >>> with project.edit("blockmodels/model") as edit_model:
    ...     print(edit_model.block_centroids)
    [[1, 2, 3], [3, 2, 3], [1, 5, 3], [3, 5, 3], [1, 2, 7], [3, 2, 7],
    [1, 5, 7], [3, 5, 7]]
    """
    if self.__origin is None:
      transform = self._get_block_transform()
      self.__origin = transform[1]
      # If the rotation has been changed, don't overwrite it.
      if not self._rotation_cached:
        self._rotation = Rotation(*transform[0])
    return self.__origin

  @origin.setter
  def origin(self, new_origin: npt.ArrayLike):
    self._raise_if_read_only("set origin")
    old_origin = self.origin.copy()
    if new_origin is None:
      # Clear the cached origin.
      self.__origin = new_origin
    else:
      self.origin[:] = new_origin
      if (not self._block_centroids.read_only
          and self.block_centroids.shape[0] != 0):
        adjustment = old_origin - self.origin
        new_centroids = self.block_centroids - adjustment
        self._set_block_centroids(new_centroids)

  @property
  def block_to_grid_index(self) -> IndexArray:
    """A mapping of the blocks to the primary blocks.

    This is an ndarray with the int dtype containing the mapping of the blocks
    to the row, column and slice their centroid lies within. This has shape
    (N, 3) where N is the block_count and each item is of the form
    [column, row, slice].

    This means that the column, row and slice of the block centred at
    block_centroids[i] is block_to_grid_index[i].

    Notes
    -----
    For DenseBlockModels, there is only one block per grid cell and thus
    each item of the array will be unique.
    """
    if self.__block_to_grid_index is None:
      block_coordinates = self.convert_to_block_coordinates(
        self.block_centroids)
      # np.rint by default maintains the type of the input array, in this
      # case double. It would return an array of floats with integer values.
      # To get the result as an array of integers without an extra copy,
      # allocate an appropriately sized array of integers and store
      # the results in it.
      # np.rint rounds all of the results to integers so the "unsafe" cast
      # should be safe.
      index = np.empty_like(block_coordinates, dtype=np.uint32)
      np.rint(
        block_coordinates / self.block_resolution,
        out=index,
        casting="unsafe")
      self.__block_to_grid_index = index
    return self.__block_to_grid_index

  def _delete_cached_block_to_grid_index(self):
    self.__block_to_grid_index = None

  def grid_index(
      self,
      start: npt.ArrayLike | int,
      stop: npt.ArrayLike | int | None=None
      ) -> BooleanArray:
    """Index block properties via row, slice and column instead of index.

    Generates a boolean index for accessing block properties by row, column and
    slice instead of by block. The boolean index will include all subblocks
    between primary block start (inclusive) and primary block stop (exclusive),
    or all subblocks within primary block start if stop is not specified.

    Parameters
    ----------
    start
      An array_like containing three elements - [column, row, slice].
      The returned boolean index will include all blocks in a greater column,
      row and slice.
      If this is an integer, that integer is interpreted as the column,
      row and slice.
    end
      An array_like containing three elements - [column, row, slice].
      If None (Default) this is start + 1 (The resulting index will
      contain all blocks within primary block start).
      If not None, the boolean index will include all blocks between
      start (inclusive) and end (exclusive).
      If this is an integer, that integer is interpreted as the column,
      row and slice index.

    Returns
    -------
    ndarray
      A boolean index into the block property arrays. This is an array
      of booleans of shape (block_count,). If element i is True then
      subblock i is within the range specified by start and stop. If
      False it is not within that range.

    Raises
    ------
    TypeError
      If start or stop are invalid types.
    ValueError
      If start or stop are incorrect shapes.

    Examples
    --------
    These examples require a block model to be at "blockmodels/target"

    This example selects all subblocks within the primary block in column 0,
    row 0 and slice 0:

    >>> from mapteksdk.project import Project
    >>> project = Project()
    >>> with project.edit("blockmodels/target") as edit_model:
    ...     index = edit_model.grid_index([0, 0, 0])
    ...     edit_model.block_selection[index] = True

    By passing two values to grid index, it is possible to operate on
    all subblocks within a range of subblocks. This example passes
    [0, 2, 2] and [4, 5, 6] meaning all subblocks which have
    0 <= column < 4 and 2 <= row < 5 and 2 <= slice < 6 will be selected
    by grid_index. By passing this index to block visibility, all subblocks
    within those primary blocks are made invisible.

    >>> from mapteksdk.project import Project
    >>> project = Project()
    >>> with project.edit("blockmodels/target") as edit_model:
    ...     index = edit_model.grid_index([0, 2, 2], [4, 5, 6])
    ...     edit_model.block_visibility[index] = False
    """
    if stop is None:
      return np.all(self.block_to_grid_index == start, axis=1)
    index = self.block_to_grid_index
    # Ignore the type checking warning on the below lines because this
    # line can raise a type checking for certain array-likes (e.g. strings)
    # This is intended functionality and the error is documented.
    pre = index >= start # type: ignore
    post = index < stop # type: ignore
    return np.all(np.logical_and(pre, post), axis=1)

  def convert_to_block_coordinates(self, world_coordinates: npt.ArrayLike
      ) -> PointArray:
    """Converts points in world coordinates to points in block coordinates.

    The block coordinate system for a particular model is defined such that
    [0, 0, 0] is the centre of the block in row 0, column 0 and slice 0.
    The X axis is aligned with the columns, the Y axis is aligned with the
    rows and the Z axis is aligned with the slices of the model. This makes
    the centre of the primary block in column i, row j and slice k to be:
    [column_res * i, row_res * j, slice_res * k].

    This function performs no error checking that the points lies within the
    model.

    Parameters
    ----------
    world_coordinates : array_like
      Points in world coordinates to convert to block coordinates.

    Returns
    -------
    numpy.ndarray
      Numpy array containing world_coordinates converted to be in
      block_coordinates.

    Raises
    ------
    ValueError
      If world_coordinates has an invalid shape.

    Notes
    -----
    If a block model has origin = [0, 0, 0] and has not been rotated,
    then the block and world coordinate systems are identical.

    Block models of differing size, origin or rotation will have different
    block coordinate systems.
    """
    # Make a copy to convert to block coordinates.
    block_coordinates = np.array(world_coordinates)
    if len(block_coordinates.shape) != 2 or block_coordinates.shape[1] != 3:
      raise ValueError(f"Invalid shape for points array: "
                       f"{block_coordinates.shape}. Shape must be (n, 3) "
                       "where n is the number of points to convert.")

    block_coordinates -= self.origin
    block_coordinates = self._rotation.invert_rotation().rotate_vectors(
      block_coordinates)

    return block_coordinates

  def convert_to_world_coordinates(self, block_coordinates: npt.ArrayLike
      ) -> PointArray:
    """Converts points in block coordinates to points in world coordinates.

    This is the inverse of the transformation performed by
    convert_to_block_coordinates.

    Parameters
    ----------
    block_coordinates
      Points in block coordinates to convert to world coordinates.

    Returns
    -------
    numpy.ndarray
      Numpy array containing block_coordinates converted to world_coordinates.

    Raises
    ------
    ValueError
      If block_coordinates has an invalid shape.

    Notes
    -----
    Block models of differing size, origin or rotation will have different
    block coordinate systems.
    """
    world_coordinates: PointArray = np.array(block_coordinates)
    if len(world_coordinates.shape) != 2 or world_coordinates.shape[1] != 3:
      raise ValueError(f"Invalid shape for points array: "
                       f"{world_coordinates.shape}. Shape must be (n, 3) "
                       "where n is the number of points to convert.")

    world_coordinates = self._rotation.rotate_vectors(world_coordinates)
    world_coordinates += self.origin

    return world_coordinates

  def _adjust_centroids_for_rotation(
      self, inverse_rotation: Rotation, new_rotation: Rotation):
    """Adjusts the centroids based on changes to rotations.

    This also takes into account the origin of the block model.
    The old rotation is undone and then the new rotation applied.

    Parameters
    ----------
    inverse_rotation : Rotation
      Rotation to undo the previous rotation on the block model.
    new_rotation : Rotation
      The new rotation of the block model.
    """
    centroids = self.block_centroids - self.origin
    centroids = inverse_rotation.rotate_vectors(centroids)
    new_centroids = new_rotation.rotate_vectors(centroids)
    new_centroids += self.origin
    self._set_block_centroids(new_centroids)

  def _invalidate_block_properties(self):
    """Invalidates the cached block properties.

    The next time a block property is accessed, its values will be loaded from
    the project.
    """
    self._block_visibility.invalidate()
    self.__block_colours.invalidate()
    self._block_centroids.invalidate()
    self.__block_dimensions = None
    self._block_selection.invalidate()
    self.__block_sizes.invalidate()
    self.__block_attributes = None
    self.__origin = None
    self._delete_cached_block_to_grid_index()

  def _save_block_properties(self):
    """Save the block properties.

    This must be called during save() of the inheriting object.
    This should never be called directly. To save an object, call save()
    instead.

    Raises
    ------
    CannotSaveInReadOnlyModeError
      If in read-only mode.
    """
    self._raise_if_save_in_read_only()
    if not self._block_centroids.read_only:
      block_count = self.block_count
      if block_count == 0:
        message = "Object must contain at least one block"
        raise DegenerateTopologyError(message)
      self._block_centroids.save()
      self.__block_sizes.save()

    self._block_selection.save()
    self._block_visibility.save()
    self.__block_colours.save()

    if self.__origin is not None or self._rotation_cached:
      # Uses the getter instead of the variable because otherwise
      # if the rotation was set and the origin was not set (or vice
      # versa) the uncached value would be set to default.
      # By using the getter, uncached values are loaded from the
      # Project and saved back to ensure they aren't changed.
      self._save_transform(*self._rotation.quaternion, *self.origin)

    if self.__block_attributes is not None:
      self.__block_attributes.save_attributes()

  def save_block_attribute(
      self, attribute_name: str | AttributeKey, data: npt.ArrayLike):
    """Create a new block attribute with the specified name and data.

    Saving a block attribute using an AttributeKey allows for additional
    metadata to be specified.

    Parameters
    ----------
    attribute_name
      The name or key of the attribute.
    data
      Data for the associated attribute. This should be a ndarray of shape
      (block_count,). The ith entry in this array is the value of this
      primitive attribute for the ith block.

    Raises
    ------
    ValueError
      If the type of the attribute is not supported.
    AmbiguousNameError
      If there is already an attribute with the same name, but with different
      metadata.
    """
    self.block_attributes[attribute_name] = data

  def delete_block_attribute(self, attribute_name: str | AttributeKey):
    """Delete a block attribute.

    Parameters
    ----------
    attribute_name
      The name or key of the attribute.
    """
    self.block_attributes.delete_attribute(attribute_name)

  @property
  def block_attributes(self) -> PrimitiveAttributes:
    """Access block attributes.

    block_model.block_attributes["Blocktastic"] will return the block attribute
    called "Blocktastic".

    Returns
    -------
    PrimitiveAttributes
      Access to the block attributes.
    """
    if self.__block_attributes is None:
      self.__block_attributes = PrimitiveAttributes(
        PrimitiveType.BLOCK,
        # BlockProperties requires that the inheriting class is Topology
        # so that self can be passed here.
        self # type: ignore
      )
    return self.__block_attributes

  def _cached_block_dimensions(self) -> tuple[int, int, int]:
    """Read the block dimensions from the model and cache the result.

    Returns
    -------
    tuple
      The number of slices, rows and columns in the block model.
    """
    if self.__block_dimensions is None:
      self.__block_dimensions = self._get_block_dimensions()
    return self.__block_dimensions

  def _get_rotation(self) -> Rotation:
    quaternion, origin = self._get_block_transform()
    # If the origin has been changed, don't overwrite it.
    if self.__origin is None:
      self.__origin = origin
    return Rotation(*quaternion)

  def _get_block_dimensions(self) -> tuple[int, int, int]:
    """Read the block dimensions for this object.

    Returns
    -------
    tuple
      The tuple (slice_count, row_count, column_count).
    """
    dimensions = (ctypes.c_uint32 * 3)()
    self._modelling_api().ReadBlockDimensions(self._lock.lock,
                                    dimensions)
    return tuple(dimensions)

  def _get_block_resolution(self) -> BlockSize:
    """Read the block resolutions for this object.

    Returns
    -------
    ndarray
      ndarray of the form [x_res, y_res, z_res].
    """
    resolution = (ctypes.c_double * 3)()
    self._modelling_api().ReadBlockSize(self._lock.lock, resolution)
    return np.array(resolution, ctypes.c_double)

  def _get_block_transform(self) -> tuple[np.ndarray[
      typing.Any, np.dtype[np.float64]], Point]:
    """Get the current block transform.

    If this object is open for read-only, the returned numpy arrays will
    not be writeable.

    Returns
    -------
    tuple
      A tuple containing the origin and quaternion
      (ndarray, ndarray) > ([q0, q1, q2, q3], [x, y, z]).
    """
    origin = (ctypes.c_double * 3)()
    quaternion = (ctypes.c_double * 4)()
    self._modelling_api().ReadBlockTransform(self._lock.lock,
                                   quaternion,
                                   origin)

    writeable = not self.is_read_only

    quaternion_array = np.array(quaternion, dtype=ctypes.c_double)
    quaternion_array.flags.writeable = writeable
    origin_array = np.array(origin, dtype=ctypes.c_double)
    origin_array.flags.writeable = writeable

    return quaternion_array, origin_array

  def _save_transform(
      self,
      q0: float, q1: float, q2: float, q3: float,
      x: float, y: float, z: float):
    """Changes the origin and rotation of the block model.

    Parameters
    ----------
    q0
      The first component of the quaternion.
    q1
      The second component of the quaternion.
    q2
      The third component of the quaternion.
    q3
      The fourth component of the quaternion.
    x
      The x component of the origin of the block model.
    y
      The y component of the origin of the block model.
    z
      The z component of the origin of the block model.

    Raise
    -----
    Exception if in read-only mode
    """
    # pylint: disable=invalid-name
    # pylint: disable=too-many-arguments
    # Set the rotation and origin
    self._modelling_api().SetBlockTransform(
      self._lock.lock, q0, q1, q2, q3, x, y, z)

  def _record_block_telemetry(self):
    """Add size telemetry for blocks to telemetry."""
    self._record_size_for("Blocks", self.block_count)

    block_attributes = self.__block_attributes
    if block_attributes is not None:
      # pylint: disable=protected-access
      block_attributes._record_telemetry()

# Pylint can't handle the intermediate abstract class (BlockDeletionProperties)
# and incorrectly marks the class as not implementing abstract methods.
# See https://github.com/pylint-dev/pylint/issues/3098 for more information.
# pylint: disable=abstract-method
class BlockDeletionProperties(BlockProperties):
  """BlockProperties with an extra functions for deleting blocks.

  Classes which inherit from BlockDeletionProperties instead of BlockProperties
  support everything BlockProperties supports and the removal of blocks.
  """
  def remove_block(self, index: int):
    """Deletes the block at the specified index.

    This operation is performed directly on the project to ensure that
    all properties (such as block_visibility and block_attributes) for the
    deleted block are deleted as well.

    Does nothing if requested to delete a non-existent block.

    Parameters
    ----------
    index
      Index of the block to the delete. This index should be greater than
      or equal to 0 and less than block_count.

    Raises
    ------
    ReadOnlyError
      If called on an object not open for editing. This error indicates an
      issue with the script and should not be caught.

    Warnings
    --------
    Any unsaved changes to the object when this function is called are
    discarded before the block is deleted. If you wish to keep these changes,
    call save() before calling this function.
    """
    self._raise_if_read_only("remove blocks")
    if index < 0 or index >= self.block_count:
      return

    # Discard unsaved changes.
    self._invalidate_properties()
    self._modelling_api().RemoveBlock(self._lock.lock, index)
    # Save to ensure this is left in a consistent state.
    self._reconcile_changes()
