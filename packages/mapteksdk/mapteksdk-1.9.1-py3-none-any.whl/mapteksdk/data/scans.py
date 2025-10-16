"""Scan data types.

This contains data types designed for representing data from LiDAR scanners.
Currently, this only includes the generic Scan class, but may be expanded
in the future to support other types of scans.
"""

###############################################################################
#
# (C) Copyright 2020, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import ctypes
import datetime
import logging
import typing

import numpy as np

from .base import Topology, StaticType
from .errors import DegenerateTopologyError
from .rotation import RotationMixin
from .objectid import ObjectID
from .primitives import PointProperties, CellProperties
from ..internal.data_property import DataProperty, DataPropertyConfiguration

from ..internal.lock import LockType
from ..internal.rotation import Rotation
from ..internal.singular_data_property_read_write import (
  SingularDataPropertyReadWrite,
)
from ..internal.util import cartesian_to_spherical, default_type_error_message
from ..internal.view_data_property import (ViewDataProperty,
                                           ViewDataPropertyConfiguration)

if typing.TYPE_CHECKING:
  from collections.abc import Callable, Sequence

  from ..capi import ScanApi
  from ..common.typing import (
    BooleanArray2d,
    BooleanArrayLike,
    CellArray,
    Float32Array,
    Float32ArrayLike,
    Float32Array2d,
    Float32Array2dLike,
    Point,
    PointLike,
  )

log = logging.getLogger("mapteksdk.data.scan")

_SCAN_DATE = ".Scan date"
"""Name of the attribute used to store the scan date."""
_SCAN_TIME_ZONE = ".Scan date time zone"
"""Name of the attribute used to store the scan date time zone."""
_SCAN_OPERATOR = ".Scanner operator"
"""Name of the attribute used to store the operator of the scanner."""
_SCAN_MODEL = ".Scanner name"
"""Name of the attribute used to store the model of the scanner."""
_SCAN_SERIAL_NUMBER = ".Scanner serial number"
"""Name of the attribute used to store the serial number of the scanner."""
_SCANNER_SOFTWARE = ".Scanner software name"
"""Name of the attribute used to store the scanner software."""
_SCANNER_SOFTWARE_VERSION = ".Scanner software version"
"""Name of the attribute used to store the version of the scanner software."""
_SCAN_DESCRIPTION = ".Scan description"
"""Name of the attribute used to store the description of the scan."""


class _Unknown:
  """Sentinel class indicating the point count is not known."""


class Scan(Topology, PointProperties, CellProperties, RotationMixin):
  """Class optimised for storing scans made by 3D laser scanners.

  The Cartesian points of a scan are derived from the point_ranges,
  vertical_angles and the horizontal_angles.

  When a scan is created you can populate the points instead of the
  point_ranges, vertical_angles and horizontal_angles. If you populate
  both then the point_ranges, vertical_angles and horizontal_angles will
  be ignored in favour of the points.

  When a scan is created if the dimensions parameter is not specified,
  then it is considered to have one row with point_count columns and all
  points within the scan are considered valid. This is the simplest
  method of creating a scan; however, such scans have no cells.

  If the dimensions parameter is specified to be
  (major_dimension_count, minor_dimension_count) but the
  point_validity parameter is not specified, then the points of the
  scan are expected to be arranged in a grid with the specified number
  of major and minor dimensions and all points in the grid should be finite.
  Scans created by the SDK are always row-major. The major dimension count
  should always correspond to the row count and the minor dimension count
  should always correspond to the column count.

  If the dimensions parameter is specified to be
  (major_dimension_count, minor_dimension_count) and the point_validity
  parameter is specified and contains a non-true value, then some of the
  points in the underlying cell network are considered invalid.

  Scans possess three types of properties:

  - Point properties.
  - Cell properties.
  - Cell point properties.

  Point properties are associated with the valid points.
  They start with 'point' and have point_count values - one value
  for each valid point.

  Cell properties start with 'cell' and should have cell_count values - one
  value for each cell in the scan. All cell property arrays will return a
  zero-length array before save() has been called.

  Cell point properties are a special type of cell and point properties.
  They start with 'cell_point' (with the exclusion of horizontal_angles
  and vertical_angles) and have cell_point_count values - one value for each
  point in the underlying cell network, including invalid points.

  Parameters
  ----------
  dimensions
    Iterable containing two integers representing the major and minor
    dimension counts of the cell network. If specified, the points of the scan
    are expected to be organised in a grid with the specified number
    of major and minor dimensions.
    If this is not specified, then the scan is considered to have
    one row with an unspecified number of columns. In this case, the column
    count is determined as soon as either the points, ranges, horizontal angles
    or vertical angles is set.
  point_validity
    Array of length major_dimension_count * minor_dimension_count of
    booleans. True indicates the point is valid, False indicates the
    point is invalid.
    If None (default), all points are considered valid.
  is_column_major
    Ignored when opening an existing scan.
    If False (default), the newly created scan will be row major.
    If True, the newly created scan will be column major.

  Raises
  ------
  DegenerateTopologyError
    If a value in dimensions is lower than 1.
  ValueError
    If a value in dimensions cannot be converted to an integer.
  ValueError
    If a value in point_validity cannot be converted to a bool.
  ValueError
    If point_validity does not have one value for each point.
  TypeError
    If dimensions is not iterable.
  RuntimeError
    If point_validity is specified but dimensions is not.

  Warnings
  --------
  Creating a scan using Cartesian points will result in a loss of
  precision. The final points of the scan will not be exactly equal to
  the points used to create the scan.

  See Also
  --------
  mapteksdk.data.points.PointSet : Accurate storage for Cartesian points.
  :documentation:`scan` : Help page for this class.

  Notes
  -----
  Editing the points property of a scan is only possible on new scans.
  Attempting to edit this array on a non-new scan will raise an error.
  Because scans have different behaviour when opened with project.new() versus
  project.edit(), you should never open a scan with project.new_or_edit().

  Rotating a scan does not change the horizontal_angles, vertical_angles
  or point ranges. Once save() is called the rotation will be applied
  to the cartesian points of the scan.

  Examples
  --------
  Create a scan using Cartesian coordinates. Note that when the points
  are read from the scan, they will not be exactly equal to the points
  used to create the scan.

  >>> from mapteksdk.project import Project
  >>> from mapteksdk.data import Scan
  >>> project = Project()
  >>> with project.new("scans/cartesian_scan", Scan) as new_scan:
  >>>     new_scan.points = [[1, 2, 4], [3, 5, 7], [6, 8, 9]]

  Create a scan using spherical coordinates.

  >>> import math
  >>> from mapteksdk.project import Project
  >>> from mapteksdk.data import Scan
  >>> project = Project()
  >>> with project.new("scans/spherical_scan", Scan) as new_scan:
  >>>     new_scan.point_ranges = [2, 16, 34, 12]
  >>>     new_scan.horizontal_angles = [3 * math.pi / 4, math.pi / 4,
  >>>                                   -math.pi / 4, - 3 * math.pi / 4]
  >>>     new_scan.vertical_angles = [math.pi / 4] * 4
  >>>     new_scan.max_range = 50
  >>>     new_scan.intensity = [256, 10000, 570, 12]
  >>>     new_scan.origin = [-16, 16, -16]

  Create a scan with the dimensions of the scan specified. This example
  creates a scan with four rows and five columns of points which form
  three rows and four columns of cells. Unlike the above two examples,
  this scan has cells and after save() has been called, its cell properties
  can be accessed.

  >>> import numpy as np
  >>> from mapteksdk.project import Project
  >>> from mapteksdk.data import Scan
  >>> project = Project()
  >>> dimensions = (4, 5)
  >>> # Each line represents one row of points in the scan.
  >>> ranges = [10.8, 11.2, 10.7, 10.6, 10.8,
  ...           9.3, 10.3, 10.8, 10.6, 11.1,
  ...           9.2, 10.9, 10.7, 10.7, 10.9,
  ...           9.5, 11.2, 10.6, 10.6, 11.0]
  >>> horizontal_angles = [-20, -10, 0, 10, 20,
  ...                      -20, -10, 0, 10, 20,
  ...                      -20, -10, 0, 10, 20,
  ...                      -20, -10, 0, 10, 20]
  >>> vertical_angles = [-20, -20, -20, -20, -20,
  ...                    -10, -10, -10, -10, -10,
  ...                    0, 0, 0, 0, 0,
  ...                    10, 10, 10, 10, 10]
  >>> with project.new("scans/example", Scan(dimensions=dimensions),
  ...         overwrite=True) as example_scan:
  ...     example_scan.point_ranges = ranges
  ...     example_scan.horizontal_angles = np.deg2rad(horizontal_angles)
  ...     example_scan.vertical_angles = np.deg2rad(vertical_angles)
  ...     example_scan.origin = [0, 0, 0]
  >>> # Make all cells visible.
  >>> with project.edit(example_scan.id) as edit_scan:
  >>>     edit_scan.cell_visibility[:] = True

  If the dimensions of a scan are specified, the point_validity can
  also be specified. For any value where the point_validity is false,
  values for point properties (such as point_range) are not stored.

  >>> import numpy as np
  >>> from mapteksdk.project import Project
  >>> from mapteksdk.data import Scan
  >>> project = Project()
  >>> dimensions = (5, 5)
  >>> # Each line represents one row of points in the scan.
  >>> # Note that rows containing invalid points have fewer values.
  >>> ranges = [10.7, 10.6, 10.8,
  ...           10.3, 10.8, 10.6,
  ...           9.2, 10.9, 10.7, 10.7, 10.9,
  ...           9.5, 11.2, 10.6, 10.6,
  ...           9.1, 9.4, 9.2]
  >>> horizontal_angles = [-20, -10, 0, 10, 20,
  ...                      -20, -10, 0, 10, 20,
  ...                      -20, -10, 0, 10, 20,
  ...                      -20, -10, 0, 10, 20,
  ...                      -20, -10, 0, 10, 20,]
  >>> vertical_angles = [-20, -20, -20, -20, -20,
  ...                    -10, -10, -10, -10, -10,
  ...                    0, 0, 0, 0, 0,
  ...                    10, 10, 10, 10, 10,
  ...                    20, 20, 20, 20, 20,]
  >>> point_validity = [False, False, True, True, True,
  ...                   False, True, True, True, False,
  ...                   True, True, True, True, True,
  ...                   True, True, True, True, False,
  ...                   True, True, True, False, False]
  >>> with project.new("scans/example_with_invalid", Scan(
  ...         dimensions=dimensions, point_validity=point_validity
  ...         ), overwrite=True) as example_scan:
  ...     example_scan.point_ranges = ranges
  ...     example_scan.horizontal_angles = np.deg2rad(horizontal_angles)
  ...     example_scan.vertical_angles = np.deg2rad(vertical_angles)
  ...     example_scan.origin = [0, 0, 0]
  >>> # Make all cells visible.
  >>> with project.edit(example_scan.id) as edit_scan:
  ...     edit_scan.cell_visibility[:] = True
  """
  def __init__(
    self,
    object_id: ObjectID | None=None,
    lock_type: LockType=LockType.READWRITE,
    *,
    dimensions: tuple[int, int] | None=None,
    point_validity: BooleanArrayLike | None=None,
    is_column_major=False,
  ):
    self.__point_count: int | _Unknown
    """The valid point count.

    This is _Unknown if the scan was created without dimensions.
    """

    # Derived properties unique to scans.
    self.__point_to_grid_index = None
    self.__grid_to_point_index = None
    self.__major_dimension_count: int
    self.__minor_dimension_count: Callable[[], int]

    if object_id:
      super().__init__(object_id, lock_type)
      # For existing scans, the point count is always known.
      self.__is_new_scan = False
      self._initialise_point_properties(True)
      self._initialise_cell_properties()
      self._initialise_cell_point_properties(None)
      self.__major_dimension_count = super().major_dimension_count
      # You cannot call super() in a lambda.
      minor_count = super().minor_dimension_count
      self.__minor_dimension_count = lambda: minor_count
      self.__point_count = super().point_count
    else:
      object_id = ObjectID(self._scan_api().NewScan())
      super().__init__(object_id, lock_type)
      self.__is_new_scan = True

      if point_validity is not None and dimensions is None:
        raise RuntimeError("point_validity requires dimensions to be set.")

      if dimensions is None:
        # No dimensions specified. The scan will have 1 major dimension and
        # point_count minor dimensions.
        self.__major_dimension_count = 1
        self.__minor_dimension_count = lambda: self.point_count
        self.__point_count = _Unknown()
      else:
        # Only validate the dimensions parameter for new scans. It is ignored
        # when reading a scan.
        major_count = int(dimensions[0])
        minor_count = int(dimensions[1])
        if major_count < 1 or minor_count < 1:
          raise DegenerateTopologyError(
            f"Invalid dimensions for scans: {dimensions}. "
            "Scans must contain at least one row and column.")
        self.__major_dimension_count = major_count
        self.__minor_dimension_count = lambda: minor_count

        if point_validity is None:
          self.__point_count = major_count * minor_count
        else:
          self.__point_count = np.count_nonzero(point_validity)

      self._initialise_point_properties(
        known_point_count=not isinstance(self.__point_count, _Unknown)
      )
      self._initialise_cell_properties()
      self._initialise_cell_point_properties(
        point_validity
      )

    self.__origin: SingularDataPropertyReadWrite[
      Point
    ] = SingularDataPropertyReadWrite(
      "origin",
      lambda: [],
      self.is_read_only,
      self._get_origin,
      self._set_origin
    )

    self.__max_range: SingularDataPropertyReadWrite[
      float
    ] = SingularDataPropertyReadWrite(
      "max_range",
      lambda: [],
      self.is_read_only or not self.__is_new_scan,
      self._get_max_range,
      lambda _: None
    )

    self.__is_column_major: SingularDataPropertyReadWrite[
      bool
    ] = SingularDataPropertyReadWrite(
      "is_column_major",
      lambda: [],
      self.is_read_only,
      self._get_is_column_major,
      # Save is handled elsewhere.
      lambda _: None
    )
    if self.__is_new_scan:
      self.__is_column_major.value = is_column_major

  @classmethod
  def _scan_api(cls) -> ScanApi:
    """Access the Scan C API."""
    return cls._application_api().scan

  @classmethod
  def static_type(cls) -> StaticType:
    """Return the type of scan as stored in a Project.

    This can be used for determining if the type of an object is a scan.
    """
    return cls._scan_api().ScanType()

  def _initialise_point_properties(self, known_point_count: bool):
    # pylint: disable=unnecessary-lambda-assignment
    super()._initialise_point_properties(known_point_count)

    def get_point_count():
      if isinstance(self.__point_count, _Unknown):
        return -1
      return self.__point_count

    # Initialise the point properties which are unique to scans.
    self.__ranges = DataProperty(
        lock=self._lock,
        configuration=DataPropertyConfiguration(
          name="point_ranges",
          dtype=ctypes.c_float,
          default=np.nan,
          column_count=1,
          primitive_count_function=self._modelling_api().ReadPointCount,
          cached_primitive_count_function=get_point_count,
          load_function=self._scan_api().PointRangesBeginR,
          save_function=self._scan_api().PointRangesBeginRW
        )
      )
    self.__point_intensity = DataProperty(
        lock=self._lock,
        configuration=DataPropertyConfiguration(
          name="point_intensity",
          dtype=ctypes.c_uint16,
          default=0,
          column_count=1,
          primitive_count_function=self._modelling_api().ReadPointCount,
          cached_primitive_count_function=lambda: self.point_count,
          load_function=self._scan_api().PointIntensityBeginR,
          save_function=self._scan_api().PointIntensityBeginRW
        )
      )

  def _initialise_cell_point_properties(
    self,
    initial_point_validity: BooleanArrayLike | None
  ):
    """Initialises the cell point properties which are unique to scans.

    Cell point properties have one value for each point in the underlying
    scan grid. Unlike point properties, these properties store values for
    invalid points.

    Parameters
    ----------
    known_point_count
      If the scan's point count is known. This determines if the horizontal
      and vertical angles arrays can initially be resized.
    initial_point_validity
      The initial values for the point validity array, which defines which
      points in the underlying grid are valid. This should be an
      array of booleans with major_dimension_count * minor_dimension_count
      values.
    """
    def get_cell_point_count():
      if isinstance(self.__point_count, _Unknown):
        return -1
      return self.cell_point_count

    self.__horizontal_angles = DataProperty(
        lock=self._lock,
        configuration=DataPropertyConfiguration(
          name="horizontal_angles",
          dtype=ctypes.c_float,
          default=np.nan,
          column_count=1,
          primitive_count_function=self._modelling_api().ReadCellPointCount,
          cached_primitive_count_function=get_cell_point_count,
          load_function=self._scan_api().GridHorizontalAnglesBeginR,
          save_function=self._scan_api().GridHorizontalAnglesBeginRW,
          # The horizontal angles can only be set on new scans.
          immutable=not self.__is_new_scan
        )
      )
    self.__vertical_angles = DataProperty(
        lock=self._lock,
        configuration=DataPropertyConfiguration(
          name="vertical_angles",
          dtype=ctypes.c_float,
          default=np.nan,
          column_count=1,
          primitive_count_function=self._modelling_api().ReadCellPointCount,
          cached_primitive_count_function=get_cell_point_count,
          load_function=self._scan_api().GridVerticalAnglesBeginR,
          save_function=self._scan_api().GridVerticalAnglesBeginRW,
           # The vertical angles can only be set on new scans.
          immutable=not self.__is_new_scan
        )
      )
    self.__point_validity = DataProperty(
        lock=self._lock,
        configuration=DataPropertyConfiguration(
          name="cell_point_validity",
          dtype=ctypes.c_bool,
          default=True,
          column_count=1,
          primitive_count_function=self._modelling_api().ReadCellPointCount,
          cached_primitive_count_function=lambda: self.cell_point_count,
          load_function=self._scan_api().GridPointValidReturnBeginR,
          save_function=None,
          immutable=True
        ),
        initial_values=initial_point_validity
      )
    self.__horizontal_angles_2d = ViewDataProperty(
      ViewDataPropertyConfiguration(
        "horizontal_angles_2d",
        self.__horizontal_angles,
        lambda: (self.major_dimension_count, self.minor_dimension_count)
      )
    )
    self.__vertical_angles_2d = ViewDataProperty(
      ViewDataPropertyConfiguration(
        "vertical_angles_2d",
        self.__vertical_angles,
        lambda: (self.major_dimension_count, self.minor_dimension_count)
      )
    )
    self.__cell_point_validity_2d = ViewDataProperty(
      ViewDataPropertyConfiguration(
        "cell_point_validity_2d",
        self.__point_validity,
        lambda: (self.major_dimension_count, self.minor_dimension_count)
      )
    )

  @property
  def cells(self) -> CellArray:
    # This generates the cells array by reading the cells from the
    # grid_to_point_index.
    # For example,  Given a grid to point index of:
    # [0, 1, 2, 3, -1],
    # [4, 5, 6, -1, -1],
    # [7, -1, 8, 9, 10]
    # The cells would be:
    # [[ 0,  4,  5,  1],
    #  [ 1,  5,  6,  2],
    #  [ 2,  6, -1,  3],
    #  [ 3, -1, -1, -1],
    #  [ 4,  7, -1,  5],
    #  [ 5, -1,  8,  6],
    #  [ 6,  8,  9, -1],
    #  [-1,  9, 10, -1]]
    #
    # The first column of the cells is calculated by ignoring the last
    # row and column in the grid_to_point_index (i.e. with -- representing
    # an ignored column):
    # [0,  1,  2,   3, --],
    # [4,  5,  6,  -1, --],
    # [--, --, --, --, --]
    #
    # The second column of the cells is calculated by ignoring the
    # first row and the last column:
    # [--, --, --, --, --],
    # [4,  5,  6,  -1, --],
    # [7,  -1, 8,   9, --]
    #
    # The third column of the cells is calculated by ignoring the
    # first row and column:
    # [--, --, --, --, --],
    # [--,  5, 6,  -1, -1],
    # [--, -1, 8,  9,  10]
    #
    # The fourth column of the cells is calculated by ignoring the
    # first row and the last column:
    # [--,  1,  2,  3, -1],
    # [--,  5,  6, -1, -1],
    # [--, --, --, --, --]
    grid_to_point_index = self.grid_to_point_index

    # An array full of -1. Items in the array which correspond to invalid
    # points are not set so will remain -1.
    values = np.full((self.cell_count, 4), -1, ctypes.c_int32)

    first_column = grid_to_point_index[:-1, :-1].reshape(-1)
    values[:, 0][~first_column.mask] = first_column[~first_column.mask]

    second_column = grid_to_point_index[1:, :-1].reshape(-1)
    values[:, 1][~second_column.mask] = second_column[~second_column.mask]

    third_column = grid_to_point_index[1:, 1:].reshape(-1)
    values[:, 2][~third_column.mask] = third_column[~third_column.mask]

    fourth_column = grid_to_point_index[:-1, 1:].reshape(-1)
    values[:, 3][~fourth_column.mask] = fourth_column[~fourth_column.mask]
    return values

  @property
  def point_count(self) -> int:
    """Returns the number of points.

    For scans, point_count returns the number of valid points in the
    scan. If the scan contains invalid points then this will be
    less than cell_point_count.
    """
    point_count = self.__point_count
    if isinstance(point_count, _Unknown):
      return super().point_count
    return point_count

  @property
  def point_ranges(self) -> Float32Array:
    """The distance of the points from the scan origin.

    This has one value per valid point.

    Any range value greater than max_range() will be set to max_range()
    when save() is called.

    Raises
    ------
    ReadOnlyError
      If attempting to edit while they are read-only.
    ValueError
      If new value cannot be converted to a np.array of 32-bit floats.
    ValueError
      If dimensions was passed to the constructor and the number of ranges
      is set to be not equal to the point_count.

    Warnings
    --------
    When creating a new scan, you should either set the points or the
    ranges, vertical angles and horizontal angles. If you set both,
    the points will be saved and the ranges ignored.
    """
    return self.__ranges.values

  @point_ranges.setter
  def point_ranges(self, new_ranges: Float32ArrayLike):
    self.__ranges.values = new_ranges
    if isinstance(self.__point_count, _Unknown):
      self.__point_count = self.__ranges.values.shape[0]

  @property
  def horizontal_angles(self) -> Float32Array:
    """The horizontal angles of the points from the scan origin.

    This is the azimuth of each point (including invalid points) measured
    clockwise from the Y axis.

    The horizontal angles can only be set when the scan is first created. Once
    save() has been called they become read-only.

    Raises
    ------
    ReadOnlyError
      If attempting to edit while they are read-only.
    ValueError
      If new value cannot be converted to a np.array of 32 bit floats.
    ValueError
      If dimensions was passed to the constructor and this is set to
      a value with less than cell_point_count values.

    Warnings
    --------
    When creating a new scan, you should either set the points or set the
    ranges, vertical angles and horizontal angles. If you set both,
    the points will be saved and the ranges ignored.

    Notes
    -----
    Technically this should be cell_point_horizontal_angles, however
    it has been shortened to horizontal_angles. This should
    have cell_point_count values.

    This array contains values for invalid points, however the value
    for an invalid point is unspecified and may be NAN (Not A Number).
    It is not recommended to use invalid angles in algorithms.
    """
    return self.__horizontal_angles.values

  @horizontal_angles.setter
  def horizontal_angles(self, new_angles: Float32ArrayLike):
    self.__horizontal_angles.values = new_angles
    if isinstance(self.__point_count, _Unknown):
      self.__point_count = self.__horizontal_angles.values.shape[0]

  @property
  def horizontal_angles_2d(self) -> Float32Array2d:
    """The horizontal angles arranged into a grid.

    The grid has dimensions (major_dimension_count, minor_dimension_count).

    Examples
    --------
    The 2D horizontal and vertical angles are useful for initialising the angles
    to be regularly spaced, similar to how they would be for a physical scanner.
    The following script demonstrates how this can be done.

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import Scan
    >>> import numpy as np
    >>> if __name__ == "__main__":
    ...   dimensions = (4, 6)
    ...   with Project() as project:
    ...     with project.new("scans/small_2d_scan", Scan(dimensions=dimensions)
    ...         ) as scan:
    ...       scan.vertical_angles_2d.T[:] = np.linspace(
    ...         start=-np.pi / 4, stop=np.pi / 4, num=dimensions[0])
    ...       scan.horizontal_angles_2d = np.linspace(
    ...         start=-np.pi / 4, stop=np.pi / 4, num=dimensions[1])
    ...      scan.point_ranges = 100
    """
    return self.__horizontal_angles_2d.values

  @horizontal_angles_2d.setter
  def horizontal_angles_2d(
    self,
    new_angles: Float32Array2dLike
  ):
    self.__horizontal_angles_2d.values = new_angles

  @property
  def vertical_angles(self) -> Float32Array:
    """The vertical angles of the points from the scan origin.

    This is the elevation angle in the spherical coordinate system.

    The vertical_angles can only be set when the scan is first created. Once
    save() has been called they become read-only.

    Raises
    ------
    ReadOnlyError
      If attempting to edit when the vertical angles are read-only.
    ValueError
      If new value cannot be converted to a np.array of 32 bit floats.
    ValueError
      If dimensions was passed to the constructor and this is set to
      a value with less than cell_point_count values.

    Warnings
    --------
    When creating a new scan, you should either set the points or set the
    ranges, vertical angles and horizontal angles. If you set both,
    the points will be saved and the vertical angles ignored.

    Notes
    -----
    Technically this should be cell_point_vertical_angles, however
    it has been shortened to vertical_angles. This should
    have cell_point_count values.

    This array contains values for invalid points, however the value
    for an invalid point is unspecified and may be NAN (Not A Number).
    It is not recommended to use invalid angles in algorithms.
    """
    return self.__vertical_angles.values

  @vertical_angles.setter
  def vertical_angles(self, new_angles: Float32ArrayLike):
    self.__vertical_angles.values = new_angles
    if isinstance(self.__point_count, _Unknown):
      self.__point_count = self.__vertical_angles.values.shape[0]

  @property
  def vertical_angles_2d(self) -> Float32Array2d:
    """The vertical angles arranged into a grid.

    The grid has dimensions (major_dimension_count, minor_dimension_count).

    Examples
    --------
    See examples for `horizontal_angles_2d`.
    """
    return self.__vertical_angles_2d.values

  @vertical_angles_2d.setter
  def vertical_angles_2d(self, new_angles: Float32Array2dLike):
    self.__vertical_angles_2d.values = new_angles

  @property
  def major_dimension_count(self) -> int:
    return self.__major_dimension_count

  @property
  def minor_dimension_count(self) -> int:
    return self.__minor_dimension_count()

  @property
  def row_count(self) -> int:
    """The number of rows in the underlying cell network.

    Note that this is the logical count of the rows. This will only correspond
    to the major dimension for the underlying array if is_column_major()
    returns false.
    """
    if self.is_column_major:
      return self.minor_dimension_count
    return self.major_dimension_count

  @property
  def column_count(self) -> int:
    """The number of columns in the underlying cell network.

    Note that this is the logical count of the columns. This will only
    correspond to the minor dimension for the underlying array if
    is_column_major() returns false.
    """
    if self.is_column_major:
      return self.major_dimension_count
    return self.minor_dimension_count

  @property
  def origin(self) -> Point:
    """The origin of the scan represented as a point.

    This should be set to the location of the scanner when the scan was taken
    (if known).

    When creating a scan using Cartesian coordinates, if the origin
    is not set it will default to the centroid of the points. Changing the
    origin in this case will not change the points.

    When creating a scan using point_range, horizontal_angles and
    vertical_angles the origin will default to [0, 0, 0]. Changing the
    origin in this case will cause the points to be centred around the new
    origin.

    Editing the origin will translate the scan by the difference between
    the new origin and the old origin.

    Notes
    -----
    Points which are far away from the origin may suffer precision issues.

    Examples
    --------
    Set the origin of a scan creating using ranges and angles and print
    the points. The origin is set to [1, 1, 1] so the final points are
    translated by [1, 1, 1].

    >>> import math
    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import Scan
    >>> project = Project()
    >>> with project.new("scans/angle_scan", Scan) as new_scan:
    ...     new_scan.point_ranges = [1, 1, 1, 1]
    ...     new_scan.horizontal_angles = [math.pi / 4, math.pi * 0.75,
    ...                                   -math.pi / 4, -math.pi * 0.75]
    ...     new_scan.vertical_angles = [0, 0, 0, 0]
    ...     new_scan.origin = [1, 1, 1]
    >>> with project.read("scans/angle_scan") as read_scan:
    ...     print(read_scan.points)
    [[1.70710668 1.70710688 1.00000019]
     [1.70710681 0.29289325 1.00000019]
     [0.29289332 1.70710688 1.00000019]
     [0.29289319 0.29289325 1.00000019]]

    Unlike for spherical coordinates, Cartesian coordinates are round
    tripped. This means that setting the origin in new() will not
    translate the points.

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import Scan
    >>> project = Project()
    >>> with project.new("scans/point_scan", Scan) as new_scan:
    ...     new_scan.points = [[1, 1, 1], [-1, 1, 2], [1, -1, 3], [-1, -1, 4]]
    ...     new_scan.origin = [2, 2, 2]
    >>> with project.read("scans/point_scan") as read_scan:
    ...     print(read_scan.points)
    [[ 0.99999997  1.00000006  1.00000008]
     [-1.00000002  1.0000001   2.00000059]
     [ 0.99999975 -1.00000013  2.99999981]
     [-1.00000004 -0.99999976  4.00000031]]

    However changing the origin in edit will always translate the points.
    By changing the origin from [2, 2, 2] to [-2, -2, -2] the x, y and z
    coordinates of the scan are each reduced by four.

    >>> from mapteksdk.project import Project
    >>> project = Project()
    >>> with project.edit("scans/point_scan") as edit_scan:
    ...     edit_scan.origin = [-2, -2, -2]
    >>> with project.read("scans/point_scan") as read_scan:
    ...     print(read_scan.points)
    [[-3.00000003 -2.99999994 -2.99999992]
     [-5.00000002 -2.9999999  -1.99999941]
     [-3.00000025 -5.00000013 -1.00000019]
     [-5.00000004 -4.99999976  0.00000031]]
    """
    return self.__origin.value

  @origin.setter
  def origin(self, new_origin: PointLike):
    if new_origin is None:
      self.__origin.value[:] = 0
    else:
      self.__origin.value[:] = new_origin

  @property
  def max_range(self) -> float:
    """The maximum range of the generating scanner.

    This is used to normalise the ranges to allow for more compact storage.
    Any point further away from the origin will have its range set to this
    value when save() is called.

    If this is not set when creating a new scan, it will default to the
    maximum distance of any point from the origin.

    This can only be set for new scans.

    Raises
    ------
    ReadOnlyError
      If user attempts to set when this value is read-only.
    """
    return self.__max_range.value

  @max_range.setter
  def max_range(self, new_max_range: float):
    self.__max_range.value = new_max_range

  @property
  def cell_point_validity(self) -> BooleanArray2d:
    """Which points in the underlying cell network are valid.

    A value of True indicates the point is valid and will appear in the
    points array. A value of False indicates the point is invalid and
    it will not appear in the points array.

    Invalid points are not stored and thus do not require point properties, such
    as colour to be stored for them.

    Examples
    --------
    If this is set in the constructor, point properties such as ranges
    and point_colours should have one value for each True in this
    array. This is shown in the below example:

    >>> import numpy as np
    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import Scan
    >>> project = Project()
    >>> dimensions = (5, 5)
    >>> # Each line represents one row of points in the scan.
    >>> # Note that rows containing invalid points have fewer values.
    >>> ranges = [10.7, 10.6, 10.8,
    ...           10.3, 10.8, 10.6,
    ...           9.2, 10.9, 10.7, 10.7, 10.9,
    ...           9.5, 11.2, 10.6, 10.6,
    ...           9.1, 9.4, 9.2]
    >>> horizontal_angles = [-20, -10, 0, 10, 20,
    ...                      -20, -10, 0, 10, 20,
    ...                      -20, -10, 0, 10, 20,
    ...                      -20, -10, 0, 10, 20,
    ...                      -20, -10, 0, 10, 20,]
    >>> vertical_angles = [-20, -20, -20, -20, -20,
    ...                    -10, -10, -10, -10, -10,
    ...                    0, 0, 0, 0, 0,
    ...                    10, 10, 10, 10, 10,
    ...                    20, 20, 20, 20, 20,]
    >>> red = [255, 0, 0, 255]
    >>> green = [0, 255, 0, 255]
    >>> blue = [0, 0, 255, 255]
    >>> point_colours = [red, green, blue,
    ...                  red, green, blue,
    ...                  red, green, blue, red, green,
    ...                  red, green, blue, red,
    ...                  red, green, blue]
    >>> point_validity = [False, False, True, True, True,
    ...                   False, True, True, True, False,
    ...                   True, True, True, True, True,
    ...                   True, True, True, True, False,
    ...                   True, True, True, False, False]
    >>> with project.new("scans/example_with_invalid_and_colours", Scan(
    ...         dimensions=dimensions, point_validity=point_validity
    ...         ), overwrite=True) as example_scan:
    ...     # Even though no points have been set, because point_validity was
    ...     # specified in the constructor point_count will return
    ...     # the required number of valid points.
    ...     print(f"Point count: {example_scan.point_count}")
    ...     # The scan contains invalid points, so cell_point_count
    ...     # will be lower than the point count.
    ...     print(f"Cell point count: {example_scan.cell_point_count}")
    ...     example_scan.point_ranges = ranges
    ...     example_scan.horizontal_angles = np.deg2rad(horizontal_angles)
    ...     example_scan.vertical_angles = np.deg2rad(vertical_angles)
    ...     example_scan.origin = [0, 0, 0]
    ...     example_scan.point_colours = point_colours
    Point count: 18
    Cell point count: 25

    This property can also be used to filter out angles from invalid
    points so that they are not used in algorithms. This example calculates
    the average vertical and horizontal angles for valid points for the
    scan created in the previous example. Make sure to run the previous
    example first.

    >>> import math
    >>> import numpy as np
    >>> from mapteksdk.project import Project
    >>> project = Project()
    >>> with project.read("scans/example_with_invalid_and_colours") as scan:
    ...     validity = scan.cell_point_validity
    ...     valid_vertical_angles = scan.vertical_angles[validity]
    ...     mean_vertical_angles = math.degrees(np.mean(valid_vertical_angles))
    ...     valid_horizontal_angles = scan.horizontal_angles[validity]
    ...     mean_horizontal_angles = math.degrees(np.mean(
    ...         valid_horizontal_angles))
    ...     print(f"Average vertical angle: {mean_vertical_angles}")
    ...     print(f"Average horizontal angle: {mean_horizontal_angles}")
    Average vertical angle: 0.5555580888570226
    Average horizontal angle: -1.1111082803078174
    """
    return self.__point_validity.values

  @property
  def cell_point_validity_2d(
    self
  ) -> np.ndarray[tuple[int, int], np.dtype[np.bool_]]:
    """The cell point validity arranged into a grid.

    The grid has dimensions (major_dimension_count, minor_dimension_count).

    Examples
    --------
    This property can be used to construct 2D versions of the point properties
    of the scan. The following example demonstrates this using the
    point_colours array (The colour of invalid points are set to np.ma.masked,
    which is represented as [--, --, --, --] in the output of the script).

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import Scan
    >>> import numpy as np
    >>> if __name__ == "__main__":
    ...   dimensions = (4, 6)
    ...   validity = [
    ...     True, True, True, False, True, True,
    ...     False, False, True, True, True, True,
    ...     False, True, True, True, False, False,
    ...     True, True, False, True, True, False
    ...   ]
    ...   with Project() as project:
    ...     with project.new("scans/valid_angles", Scan(
    ...         dimensions=dimensions,
    ...         point_validity=validity)) as scan:
    ...       scan.vertical_angles_2d.T[:] = np.linspace(
    ...         start=-np.pi / 4, stop=np.pi / 4, num=dimensions[0])
    ...       scan.horizontal_angles_2d = np.linspace(
    ...         start=-np.pi / 4, stop=np.pi / 4, num=dimensions[1])
    ...       scan.point_ranges = 100
    ...       point_colours_2d = np.ma.masked_all(
    ...         (scan.major_dimension_count, scan.minor_dimension_count, 4),
    ...         np.uint8
    ...       )
    ...       point_colours_2d[scan.cell_point_validity_2d] = scan.point_colours
    ...       print(point_colours_2d)
    [[[0 220 0 255]
      [0 220 0 255]
      [0 220 0 255]
      [-- -- -- --]
      [0 220 0 255]
      [0 220 0 255]]
    [[-- -- -- --]
      [-- -- -- --]
      [0 220 0 255]
      [0 220 0 255]
      [0 220 0 255]
      [0 220 0 255]]
    [[-- -- -- --]
      [0 220 0 255]
      [0 220 0 255]
      [0 220 0 255]
      [-- -- -- --]
      [-- -- -- --]]
    [[0 220 0 255]
      [0 220 0 255]
      [-- -- -- --]
      [0 220 0 255]
      [0 220 0 255]
      [-- -- -- --]]]
    """
    return self.__cell_point_validity_2d.values

  @property
  def point_intensity(self) -> np.ndarray[tuple[int], np.dtype[np.int16]]:
    """A list containing the intensity of the points.

    This contains one value for each valid point.

    Each intensity value is represented as a 16 bit unsigned integer and should
    be between 0 and 65535 (inclusive). If the value is outside of this range,
    integer overflow will occur.
    """
    return self.__point_intensity.values

  @point_intensity.setter
  def point_intensity(
    self,
    new_intensity: np.ndarray[tuple[int], np.dtype[np.int16]] | Sequence[int]
  ):
    self.__point_intensity.values = new_intensity

  @property
  def is_column_major(self) -> bool:
    """True if the scan is stored in a column major cell network.

    All scans created via the SDK will be in row-major order.
    """
    return self.__is_column_major.value

  @property
  def point_to_grid_index(self) -> np.ndarray[
    tuple[typing.Any, typing.Literal[2]],
    np.dtype[np.int64]
  ]:
    """An array which maps a point index to its location in the grid.

    This is a numpy array of shape (point_count, 2) where each row of the array
    is of the form (scan_major_dimension, scan_minor_dimension) where
    scan_major_dimension is the index of the major dimension in the scan which
    contains the point and scan_minor_dimension is the index of the column in
    the scan which contains the point.

    Examples
    --------
    The following examples assume that the scan is row-major.

    Get the row and column of the point at index seven in the scan.

    >>> row, column = scan.point_to_grid_index[7]

    Set all points in the third row (index 2) of a scan to cyan.

    >>> index = scan.point_to_grid_index[:, 0] == 2
    >>> scan.point_colours[index] = [0, 255, 255, 255]

    Set all points in the second column (index 1) of a scan to yellow.

    >>> index = scan.point_to_grid_index[:, 1] == 1
    >>> scan.point_colours[index] = [255, 255, 0, 255]
    """
    if self.__point_to_grid_index is None:
      index = np.empty((self.point_count, 2), dtype=np.int64)
      # This generates an array of indices into the cell_point_validity
      # array to the elements which are true (i.e. the valid points).
      # e.g. Given cell_point_validity = [False, True, True, False, True]
      # valid_indices would be [1, 2, 4]
      valid_indices = np.where(self.cell_point_validity)[0]
      # Convert the valid indices to row/column indices.
      index[:, 0] = valid_indices // self.minor_dimension_count
      index[:, 1] = valid_indices % self.minor_dimension_count
      self.__point_to_grid_index = index
    return self.__point_to_grid_index

  @property
  def grid_to_point_index(self) -> np.ma.MaskedArray[
    tuple[int, int],
    np.dtype[np.int64]
  ]:
    """An array which maps the row and column of a point to its index.

    This is a numpy masked array of shape (row_count, column count) where
    the value in row i and column j is the index of the point in row i and
    column j. If the point is invalid, the value will be np.ma.masked and
    attempting to index into a point property array with it will raise an
    IndexError.

    Examples
    --------
    Get the index of the point in the row index 5 and column index 7

    >>> index = scan.grid_to_point_index[5, 7]

    Set all points in the second column (index 1) of a scan to be yellow.

    >>> index = scan.grid_to_point_index[:, 1]
    >>> # Filter out invalid indices.
    >>> index = index[index != np.ma.masked]
    >>> scan.point_colours[index] = [255, 255, 0, 255]

    Set all points in the third row (index 2) of a scan to cyan.

    >>> index = scan.grid_to_point_index[2]
    >>> # Filter out invalid indices.
    >>> index = index[index != np.ma.masked]
    >>> scan.point_colours[index] = [0, 255, 255, 255]
    """
    if self.__grid_to_point_index is None:
      index = np.ma.masked_all(
        (self.major_dimension_count, self.minor_dimension_count),
        dtype=np.int64
      )
      flat_index = index[:].reshape(-1)
      flat_index[self.cell_point_validity] = np.arange(self.point_count)
      self.__grid_to_point_index = index

    return self.__grid_to_point_index

  @property
  def scan_date(self) -> datetime.datetime | None:
    """The scan date.

    This is typically the time that the scan was taken, rather than the
    time which the Scan object was created.

    If the scan date was not set, this will be None.

    The datetime returned by this property is time zone aware.

    Raises
    ------
    TypeError
      If this property is assigned to a value which is not a
      datetime.datetime object.
    ValueError
      If set to a datetime which is not time zone aware.

    Notes
    -----
    This property is backed by the ".Scan date" and ".Scan date time zone"
    object properties.

    If any of the other scan acquisition details are set, but this is
    not then this will be set to 1970-01-01.
    """
    try:
      scan_date = self.get_attribute(_SCAN_DATE)
      if not isinstance(scan_date, datetime.datetime):
        raise TypeError("Backing attribute was the wrong type.")

      time_zone = self.get_attribute(_SCAN_TIME_ZONE)
      # The type of time zone is ignored because the except block
      # will catch any errors caused by it being the wrong type.
      scan_date = scan_date.replace(tzinfo=datetime.timezone(
        datetime.timedelta(minutes=time_zone))) # type: ignore
      return scan_date
    except (KeyError, TypeError):
      # A KeyError occurs if one of the backing attributes did not exist
      # and a TypeError occurs if one of them is an unsupported type.
      return None

  @scan_date.setter
  def scan_date(self, new_date: datetime.datetime):
    try:
      utc_offset = new_date.utcoffset()
      if utc_offset is None:
        raise ValueError(
          "Scan date must be a time zone aware datetime.")
      utc_offset_minutes = utc_offset.seconds // 60
    except AttributeError as error:
      raise TypeError(
        default_type_error_message(
          "new_date",
          new_date,
          datetime.datetime
        )
      ) from error

    self.set_attribute(
      _SCAN_DATE,
      datetime.datetime,
      new_date
    )
    self.set_attribute(
      _SCAN_TIME_ZONE,
      ctypes.c_int64,
      utc_offset_minutes
    )
    self._ensure_all_details_defined()

  @property
  def operator(self) -> str:
    """The operator of the scanner when the scan was taken.

    This will be the empty string if no operator was recorded.
    """
    try:
      return str(self.get_attribute(_SCAN_OPERATOR))
    except KeyError:
      return ""

  @operator.setter
  def operator(self, value: str):
    self.set_attribute(
      _SCAN_OPERATOR,
      str,
      value
    )
    self._ensure_all_details_defined()

  @property
  def scanner_model(self) -> str:
    """The model of scanner used to take the scan.

    This will be the empty string if no model was recorded.
    """
    try:
      return str(self.get_attribute(_SCAN_MODEL))
    except KeyError:
      return ""

  @scanner_model.setter
  def scanner_model(self, value: str):
    self.set_attribute(
      _SCAN_MODEL,
      str,
      value
    )
    self._ensure_all_details_defined()

  @property
  def scanner_serial_number(self) -> str:
    """The serial number of the scanner used to take the scan.

    This will be the empty string if no serial number was recorded.
    """
    try:
      return str(self.get_attribute(_SCAN_SERIAL_NUMBER))
    except KeyError:
      return ""

  @scanner_serial_number.setter
  def scanner_serial_number(self, new_serial_number: str):
    self.set_attribute(
      _SCAN_SERIAL_NUMBER,
      str,
      new_serial_number
    )
    self._ensure_all_details_defined()

  @property
  def scanner_software(self) -> str:
    """The name of the software used to control the scanner.

    This will be the empty string if no software was recorded.
    """
    try:
      return str(self.get_attribute(_SCANNER_SOFTWARE))
    except KeyError:
      return ""

  @scanner_software.setter
  def scanner_software(self, new_software: str):
    self.set_attribute(
      _SCANNER_SOFTWARE,
      str,
      new_software
    )
    self._ensure_all_details_defined()

  @property
  def scanner_software_version(self) -> str:
    """The version of the software used to control the scanner.

    This will be the empty string if no software was recorded.
    """
    try:
      return str(self.get_attribute(_SCANNER_SOFTWARE_VERSION))
    except KeyError:
      return ""

  @scanner_software_version.setter
  def scanner_software_version(self, new_version: str):
    self.set_attribute(
      _SCANNER_SOFTWARE_VERSION,
      str,
      new_version
    )
    self._ensure_all_details_defined()

  @property
  def description(self) -> str:
    """A description of the scan.

    This will be the empty string if no description is recorded.
    """
    try:
      return str(self.get_attribute(_SCAN_DESCRIPTION))
    except KeyError:
      return ""

  @description.setter
  def description(self, new_description: str):
    self.set_attribute(
      _SCAN_DESCRIPTION,
      str,
      new_description
    )
    self._ensure_all_details_defined()

  def _ensure_all_details_defined(self):
    """Ensures that all scan details are defined.

    If even one of the Scan details field's backing field is not defined,
    then all of them will show up as "undefined" in the application.
    """
    string_attribute_names = (
      _SCAN_OPERATOR,
      _SCAN_MODEL,
      _SCAN_SERIAL_NUMBER,
      _SCANNER_SOFTWARE,
      _SCANNER_SOFTWARE_VERSION,
      _SCAN_DESCRIPTION
    )
    attribute_names = self.attribute_names()

    for attribute_name in string_attribute_names:
      if attribute_name not in attribute_names:
        self.set_attribute(attribute_name, str, "")

    if _SCAN_DATE not in attribute_names:
      # Ideally, this would set the date to sysC_DateTime::Empty(),
      # however the C API function for setting date time attributes
      # doesn't support that.
      # The Unix epoch is used for lack of a better choice.
      self.set_attribute(
        _SCAN_DATE, datetime.datetime, datetime.datetime(1970, 1, 1))

    if _SCAN_TIME_ZONE not in attribute_names:
      self.set_attribute(_SCAN_TIME_ZONE, ctypes.c_int64, 0)

  def _save_topology(self):
    if self.point_count == 0:
      message = "Object must contain at least one point."
      raise DegenerateTopologyError(message)

    if self.__is_new_scan:
      # If the user has set points, convert them to ranges and angles so
      # that they can be saved.
      if super().point_count != 0:
        if not self.__origin.are_values_cached:
          self.origin = np.mean(self.points, axis=0)

        # Ensure we have the correct number of points.
        if self.point_count != super().point_count:
          raise ValueError(
            f"Scan requires {self.point_count} valid points. "
            f"Given: {self.point_count}")

        spherical_coordinates = cartesian_to_spherical(self.points,
                                                        self.origin)
        # Bypass the setter, as the output from Cartesian_to_spherical is
        # already correctly formatted.
        self.__ranges.values = spherical_coordinates[0]

        # The above call will only generate angles for valid points,
        # however the angles arrays must have values for invalid points.
        # This allocates an array of nan and writes the valid values to
        # the locations for the valid points.
        horizontal_angles = np.full((self.cell_point_count),
                                      np.nan,
                                      ctypes.c_float)
        horizontal_angles[self.cell_point_validity] = spherical_coordinates[1]
        self.__horizontal_angles.values = horizontal_angles

        vertical_angles = np.full((self.cell_point_count),
                                  np.nan,
                                  ctypes.c_float)
        vertical_angles[self.cell_point_validity] = spherical_coordinates[2]
        self.__vertical_angles.values = vertical_angles

      self._save_scan_points()

    self.__ranges.save()

    self.__origin.save()

    self.__point_intensity.save()

    if self._rotation_cached:
      self._save_rotation(self._rotation)

    self._save_point_properties()
    self._save_cell_properties()
    self.__is_new_scan = False

  def _extra_invalidate_properties(self):
    super()._extra_invalidate_properties()
    self.__origin.invalidate()
    self.__ranges.invalidate()
    self.__horizontal_angles.invalidate()
    self.__horizontal_angles_2d.invalidate()
    self.__vertical_angles.invalidate()
    self.__vertical_angles_2d.invalidate()
    self.__point_intensity.invalidate()
    self.__point_validity.invalidate()
    self.__cell_point_validity_2d.invalidate()
    self.__max_range.invalidate()
    self._invalidate_point_properties()

  def _record_object_size_telemetry(self):
    self._record_point_telemetry()
    self._record_cell_telemetry()

  def _save_scan_points(self):
    """Saves the points of the scan.

    This combines several calls which are required to properly save the points
    of a scan and performs a few operations to ensure the saved values
    are consistent. This should only be called for new scans.

    """
    point_validity = self.cell_point_validity
    self._set_scan(self.row_count, self.column_count, self.max_range,
                   point_validity, self.point_count, self.is_column_major)
    self.__horizontal_angles.save()
    self.__vertical_angles.save()

  def _set_scan(
    self,
    row_count: int,
    col_count: int,
    max_range: float,
    validity: BooleanArrayLike,
    point_count: int,
    is_column_major: bool
  ):
    """Sets the scan.

    This allows the points, ranges, horizontal angle and vertical angles to be
    set again - after this is called you must call _save_ranges(),
    _save_vertical_angles() and _save_horizontal_angles().

    Calling this destroys all point properties (such as visibility and colour).

    Parameters
    ----------
    row_count : int
      Number of rows in the scan.
    col_count : int
      Number of columns in the scan.
    max_range : int
      Max range of the scan.
    validity : numpy.ndarray
      validity[i] = True if the ith point is valid. False otherwise.
    point_count : int
      The count of valid points in the scan.
    is_column_major : bool
      True if the scan is column major, False if the scan is row major.
    """
    c_point_validity = (ctypes.c_bool * (row_count * col_count))(*validity)

    # Set the size of the scan.
    self._scan_api().SetScan(self._lock.lock,
                      row_count,
                      col_count,
                      max_range,
                      c_point_validity,
                      point_count,
                      is_column_major)

  def _get_origin(self) -> Point:
    """Gets the scan origin from the Project."""
    return np.array(self._scan_api().GetOrigin(self._lock.lock))

  def _get_max_range(self) -> float:
    """Get the max range from the Project."""
    if self.__is_new_scan:
      return max(self.__ranges.values, default=0.0)
    return self._scan_api().OperatingRange(self._lock.lock)

  def _get_is_column_major(self) -> bool:
    """Get if the scan is column major from the Project."""
    return self._scan_api().IsColumnMajor(self._lock.lock)

  def _get_rotation(self) -> Rotation:
    """Get the local to ellipsoid transfrom from the Project."""
    transform = self._scan_api().GetLocalToEllipsoidTransform(self._lock.lock)
    return Rotation(*transform[0])

  def _set_origin(self, new_origin: Point):
    """Saves the scan origin to the Project."""
    self._scan_api().SetOrigin(
      self._lock.lock,
      new_origin[0],
      new_origin[1],
      new_origin[2]
    )

  def _save_rotation(self, new_rotation: Rotation):
    """Saves the scan rotation to the Project.

    Parameters
    ----------
    new_rotation : Rotation
      The rotation object to set the rotation to.
    """
    self._scan_api().SetLocalToEllipsoidTransform(
      self._lock.lock,
      new_rotation.quaternion,
      [0, 0, 0]
    )
