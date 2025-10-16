"""Support for cell primitives.

Cell primitives are quadrilaterals defined by four points. In Python, a cell
is represented as a numpy array containing four integers representing
the indices of the points used to define the corners of the cell. For example,
the cell [0, 1, 2, 3] indicates the quadrilateral with the 0th, 1st, 2nd and
3rd point as the four corners. Because cells are defined based on points, all
objects which inherit from CellProperties must also inherit from
PointProperties.
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
  PrimitiveAttributes, PrimitiveType, AttributeKey)
from ...internal.data_property import DataProperty, DataPropertyConfiguration

if typing.TYPE_CHECKING:
  import numpy.typing as npt

  from ...capi import ModellingApi
  from ...common.typing import CellArray, BooleanArray
  from ...internal.lock import ReadLock, WriteLock

log = logging.getLogger("mapteksdk.data")

# The following warning can be enabled if the <Primitive>Properties classes
# ended in Mixin as then pylint expects that the members are defined elsewhere.
# pylint: disable=no-member

class CellProperties:
  """Mixin class which provides spatial objects support for cell primitives.

  Functions and properties defined on this class are available on all
  classes which support cells. Inheriting classes may impose restrictions on
  the quadrilaterals which can be included in that object.
  """
  __major_dimension_count: int | None
  __minor_dimension_count: int | None
  _cells: DataProperty
  _cell_visibility: DataProperty
  _cell_selection: DataProperty
  _cell_colours: DataProperty
  __cell_attributes: PrimitiveAttributes | None

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

    def _record_size_for(self, name: str, size: int):
      raise NotImplementedError

    @classmethod
    def _type_name(cls) -> str:
      raise NotImplementedError

    @classmethod
    def _modelling_api(cls) -> ModellingApi:
      raise NotImplementedError

  def _initialise_cell_properties(self):
    """Initialises the cell properties.

    This must be called during the __init__ function of child classes.
    """
    self._cells = DataProperty(
      lock=self._lock,
      configuration=DataPropertyConfiguration(
        name="cells",
        dtype=ctypes.c_int32,
        default=0,
        column_count=4,
        primitive_count_function=self._modelling_api().ReadCellCount,
        load_function=self._modelling_api().CellToPointIndexBeginR,
        save_function=None,
        cached_primitive_count_function=lambda: self.cell_count,
        set_primitive_count_function=None,
        immutable=True,
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode
      )
    )

    self._cell_visibility = DataProperty(
      lock=self._lock,
      configuration=DataPropertyConfiguration(
        name="cell_visibility",
        dtype=ctypes.c_bool,
        default=True,
        column_count=1,
        primitive_count_function=self._modelling_api().ReadCellCount,
        cached_primitive_count_function=lambda: self.cell_count,
        load_function=self._modelling_api().CellVisibilityBeginR,
        save_function=self._modelling_api().CellVisibilityBeginRW,
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode
      )
    )

    self._cell_colours = DataProperty(
      lock=self._lock,
      configuration=DataPropertyConfiguration(
        name="cell_colours",
        dtype=ctypes.c_uint8,
        default=np.array([0, 220, 0, 255], dtype=ctypes.c_uint8),
        column_count=4,
        primitive_count_function=self._modelling_api().ReadCellCount,
        cached_primitive_count_function=lambda: self.cell_count,
        load_function=self._modelling_api().CellColourBeginR,
        save_function=self._modelling_api().CellColourBeginRW,
        is_colour_property=True,
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode
      )
    )

    self._cell_selection = DataProperty(
      lock=self._lock,
      configuration=DataPropertyConfiguration(
        name="cell_selection",
        dtype=ctypes.c_bool,
        default=False,
        column_count=1,
        primitive_count_function=self._modelling_api().ReadCellCount,
        cached_primitive_count_function=lambda: self.cell_count,
        load_function=self._modelling_api().CellSelectionBeginR,
        save_function=self._modelling_api().CellSelectionBeginRW,
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode
      )
    )

    self.__major_dimension_count = None
    self.__minor_dimension_count = None
    self.__cell_attributes = None

  @property
  def major_dimension_count(self) -> int:
    """The major dimension count of the Cell Network.

    If the inheriting object is stored in row major order, then this will
    correspond to the row count. If stored in column major order then this will
    correspond to the column count.
    """
    if self.__major_dimension_count is None:
      self.__read_cell_dimensions()
    assert self.__major_dimension_count is not None
    return self.__major_dimension_count

  @property
  def minor_dimension_count(self) -> int:
    """The major dimension count of the Cell Network.

    If the inheriting object is stored in row major order, then this will
    correspond to the column count. If stored in column major order then this
    will correspond to the row count.
    """
    if self.__minor_dimension_count is None:
      self.__read_cell_dimensions()
    assert self.__minor_dimension_count is not None
    return self.__minor_dimension_count

  @property
  def cells(self) -> CellArray:
    """This property maps the cells to the points which define them.

    Use this to refer to the points which define the four corners of
    a cell.

    This is a numpy array of shape (n, 4) where n is the cell count.
    If cells[i] is [a, b, c, d] then the four corner points of the ith cell are
    points[a], points[b], points[c] and points[d].

    Notes
    -----
    Sparse cell objects (such as Scans) may contain cells with point indices
    of -1. These represent invalid points. In the future, this may be changed
    to be a masked array instead.

    Examples
    --------
    This example creates a GridSurface object with 3 rows and 3 columns of
    points and prints the cells. Then it prints the four points which
    define the first cell (index 0).

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import GridSurface
    >>> project = Project()
    >>> with project.new("surfaces/small_square", GridSurface(
    ...         major_dimension_count=3, minor_dimension_count=3,
    ...         x_step=0.1, y_step=0.1)) as small_square:
    ...     print("Cells:")
    ...     print(small_square.cells)
    ...     print("The points which define the first cell are:")
    ...     for index in small_square.cells[0]:
    ...         print(f"Point {index}:", small_square.points[index])
    Cells:
    [[0 3 4 1]
     [1 4 5 2]
     [3 6 7 4]
     [4 7 8 5]]
    The points which define the first cell are:
    Point 0: [0. 0. 0.]
    Point 3: [0.3 0.  0. ]
    Point 4: [0.  0.1 0. ]
    Point 1: [0.1 0.  0. ]
    """
    return self._cells.values

  @property
  def cell_count(self) -> int:
    """The number of cells in the cell network.

    By default this is equal to the
    (major_dimension_count - 1) x (minor_dimension_count - 1),
    however subclasses may override this function to return different values.
    """
    return (self.major_dimension_count - 1) * (self.minor_dimension_count - 1)

  @property
  def cell_visibility(self) -> BooleanArray:
    """The visibility of the cells as a flat array.

    This array will contain cell_count booleans - one for each cell.
    True indicates the cell is visible and False indicates the cell is
    invisible.
    """
    return self._cell_visibility.values

  @cell_visibility.setter
  def cell_visibility(self, cell_visibility: npt.ArrayLike):
    self._cell_visibility.values = cell_visibility

  @property
  def cell_selection(self) -> BooleanArray:
    """The selection of the cells as a flat array.

    This array will contain cell_count booleans - one for each cell.
    True indicates the cell is selected and False indicates the cell is not
    selected.
    """
    return self._cell_selection.values

  @cell_selection.setter
  def cell_selection(self, cell_selection):
    self._cell_selection.values = cell_selection

  @property
  def cell_point_count(self) -> int:
    """The number of points in the cell network, including invalid points.

    The point_count of a cell network only counts the valid points. However,
    sparse cell networks (such as Scans) may also contain invalid points for
    which point properties are not stored. This is equal to:
    major_dimension_count * minor_dimension_count.

    If the object contains invalid points, then cell_point_count > point_count.

    See Also
    --------
    mapteksdk.data.primitives.PointProperties.point_count :
      The count of valid points in the object.
    """
    return self.major_dimension_count * self.minor_dimension_count

  @property
  def cell_attributes(self) -> PrimitiveAttributes:
    """Access custom cell attributes.

    These are arrays of values of the same type, with one value for each cell.

    Use Object.cell_attributes[attribute_name] to access a cell attribute
    called attribute_name. See PrimitiveAttributes for valid operations
    on cell attributes.

    Returns
    -------
    PrimitiveAttributes
      Access to the cell attributes.

    Raises
    ------
    ValueError
      If the type of the attribute is not supported.
    """
    if self.__cell_attributes is None:
      self.__cell_attributes = PrimitiveAttributes(
        PrimitiveType.CELL,
        # CellProperties requires that the inheriting class is Topology
        # so that self can be passed here.
        self # type: ignore
      )
    return self.__cell_attributes

  def save_cell_attribute(
      self,
      attribute_name: str | AttributeKey,
      data: npt.ArrayLike):
    """Create and/or edit the values of the cell attribute attribute_name.

    This is equivalent to Object.cell_attributes[attribute_name] = data.

    Saving a cell attribute using an AttributeKey allows for additional
    metadata to be specified.

    Parameters
    ----------
    attribute_name
      The name or key of the attribute.
    data : array_like
      An array_like of length cell_count containing the values
      for attribute_name.

    Raises
    ------
    ValueError
      If the type of the attribute is not supported.
    AmbiguousNameError
      If there is already an attribute with the same name, but with different
      metadata.
    """
    self.cell_attributes[attribute_name] = data

  def delete_cell_attribute(self, attribute_name: str | AttributeKey):
    """Delete a cell attribute.

    This is equivalent to: cell_attributes.delete_attribute(attribute_name)

    Parameters
    ----------
    attribute_name
      The name or key of the attribute.
    """
    self.cell_attributes.delete_attribute(attribute_name)

  def _invalidate_cell_properties(self):
    """Invalidates the cached cell properties.

    The next time a cell property is accessed, its values will be loaded from
    the project.
    """
    self.__major_dimension_count = None
    self.__minor_dimension_count = None
    self._cell_visibility.invalidate()
    self._cell_selection.invalidate()
    self._cell_colours.invalidate()
    self.__cell_attributes = None

  def __read_cell_dimensions(self):
    """Read the cell dimensions from the Project.

    This reads the cell dimensions from the Project and assigns them to
    __major_dimension_count and __minor_dimension_count.
    """
    dimensions = self._modelling_api().ReadCellDimensions(self._lock.lock)
    self.__major_dimension_count = dimensions[0]
    self.__minor_dimension_count = dimensions[1]

  def _save_cell_properties(self):
    """Save the cell properties.

    This must be called during save() of the inheriting object.
    This should never be called directly. To save an object, call save()
    instead.

    Raises
    ------
    CannotSaveInReadOnlyModeError
      If in read-only mode.

    Notes
    -----
    This should be called after PointProperties.save_points().
    """
    self._raise_if_save_in_read_only()
    self._cell_visibility.save()
    self._cell_selection.save()
    self._cell_colours.save()
    if self.__cell_attributes is not None:
      self.__cell_attributes.save_attributes()

  def _record_cell_telemetry(self):
    """Add size telemetry for cells to telemetry."""
    self._record_size_for("Cells", self.cell_count)

    cell_attributes = self.__cell_attributes
    if cell_attributes is not None:
      # pylint: disable=protected-access
      cell_attributes._record_telemetry()
