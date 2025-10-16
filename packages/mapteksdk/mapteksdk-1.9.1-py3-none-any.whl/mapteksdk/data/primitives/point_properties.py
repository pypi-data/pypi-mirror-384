"""Support for point primitives.

A point is a 3D location in space. In Python, they are represented as a
numpy array containing three 64-bit floating point numbers, representing
the location relative to the origin. For example, the point [X, Y, Z]
is X metres away from the origin in the x direction (typically east),
Y metres away from the origin in the y direction (typically north)
and Z metres away from the origin in the z direction (typically up).

Points are typically used to define other primitives, such as edges, facets
and cells.

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

import numpy as np

from .primitive_attributes import (
  PrimitiveAttributes, PrimitiveType, AttributeKey)
from ..errors import DegenerateTopologyError, AppendPointsNotSupportedError
from ...internal.data_property import DataProperty, DataPropertyConfiguration
from ...internal.util import append_rows_to_2d_array

if typing.TYPE_CHECKING:
  import numpy.typing as npt

  from ...capi import ModellingApi
  from ...common.typing import (
    PointArray,
    BooleanArray,
    BooleanArrayLike,
    ColourArray,
    FloatArray,
    PointLike,
    PointArrayLike,
  )
  from ...internal.lock import ReadLock, WriteLock


log = logging.getLogger("mapteksdk.data")

# The following warning can be enabled if the <Primitive>Properties classes
# ended in Mixin as then pylint expects that the members are defined elsewhere.
# pylint: disable=no-member

class PointProperties:
  """Mixin class which provides spatial objects support for point primitives.

  A point is represented as a numpy array of length 3 of the form
  [x, y, z] where x, y and z are floating point numbers.
  For example, the point [1, 2, 3.5] is 1 metre away from the origin in the X
  direction (East in a standard view), 2 units away from the origin in the
  Y direction (North in a standard view) and 3.5 units away from the origin in
  the z direction.
  If one of the elements of a point is negative, this indicates its
  distance from the origin is in the opposite direction. For example,
  the point [-1, 0, 0] is 1 unit away from the origin in the direction
  opposite to the East arrow.

  Functions and properties defined on this class are available on all
  classes which support points.
  """
  _points: DataProperty
  _point_colours: DataProperty
  _point_selection: DataProperty
  _point_visibility: DataProperty
  __point_attributes: PrimitiveAttributes | None
  __point_z: FloatArray | None

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

  def _initialise_point_properties(self, known_point_count: bool):
    """Initialises the point properties.

    This must be called during the __init__ function of child classes.

    Parameters
    ----------
    known_point_count
      If True, this subclass's point count is immutable. Attempting to add or
      remove points by assigning longer or shorter arrays to the points property
      will raise a ValueError. The subclass must overwrite self.point_count
      to always return a fixed value.
      If False, this subclass's point count is mutable. Assigning longer or
      shorter arrays to the points property will change the point count and
      the arrays of other point properties will be resized the next time they
      are accessed. The subclass typically won't overwrite self.point_count in
      this case.
    """
    if known_point_count:
      # pylint: disable=unnecessary-lambda-assignment
      get_point_count = lambda: self.point_count
      set_point_count = None
    else:
      get_point_count = None
      set_point_count = self._modelling_api().SetPointCount

    self._points = DataProperty(
      lock=self._lock,
      configuration=DataPropertyConfiguration(
        name="points",
        dtype=ctypes.c_double,
        default=np.nan,
        column_count=3,
        primitive_count_function=self._modelling_api().ReadPointCount,
        cached_primitive_count_function=get_point_count,
        load_function=self._modelling_api().PointCoordinatesBeginR,
        save_function=self._modelling_api().PointCoordinatesBeginRW,
        set_primitive_count_function=set_point_count,
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode
      )
    )

    self._point_colours = DataProperty(
      lock=self._lock,
      configuration=DataPropertyConfiguration(
        name="point_colours",
        dtype=ctypes.c_uint8,
        default=np.array([0, 220, 0, 255], dtype=ctypes.c_uint8),
        column_count=4,
        primitive_count_function=self._modelling_api().ReadPointCount,
        cached_primitive_count_function=lambda: self.point_count,
        load_function=self._modelling_api().PointColourBeginR,
        save_function=self._modelling_api().PointColourBeginRW,
        is_colour_property=True,
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode
      )
    )

    self._point_visibility = DataProperty(
      lock=self._lock,
      configuration=DataPropertyConfiguration(
        name="point_visibility",
        dtype=ctypes.c_bool,
        default=True,
        column_count=1,
        primitive_count_function=self._modelling_api().ReadPointCount,
        cached_primitive_count_function=lambda: self.point_count,
        load_function=self._modelling_api().PointVisibilityBeginR,
        save_function=self._modelling_api().PointVisibilityBeginRW,
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode
      )
    )

    self._point_selection = DataProperty(
      lock=self._lock,
      configuration=DataPropertyConfiguration(
        name="point_selection",
        dtype=ctypes.c_bool,
        default=False,
        column_count=1,
        primitive_count_function=self._modelling_api().ReadPointCount,
        cached_primitive_count_function=lambda: self.point_count,
        load_function=self._modelling_api().PointSelectionBeginR,
        save_function=self._modelling_api().PointSelectionBeginRW,
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode
      )
    )

    self.__point_attributes = None
    self.__point_z = None

  @property
  def points(self) -> PointArray:
    """The three dimensional points in the object.

    This is a numpy array of shape (N, 3) where N is the point count. This
    is of the form:
    [[x1, y1, z1], [x2, y2, z2], ..., [xN, yN, zN]]

    To get the ith point:

    >>> point_i = point_set.points[i]

    Similarly, to get the x, y and z coordinates of the ith point:

    >>> x, y, z = point_set.points[i]

    Raises
    ------
    AttributeError
      If attempting to set the points on an object which does not support
      setting points.

    Examples
    --------
    Create a new point set and set the points:

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import PointSet
    >>> project = Project()
    ... with project.new("cad/test_points", PointSet) as new_points:
    ...     new_points.points = [[0, 0, 0], [1, 0, 0], [1, 1, 0],
    ...                          [0, 1, 0], [0, 2, 2], [0, -1, 3]]

    Print the second point from the point set defined above.

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import PointSet
    >>> project = Project()
    >>> with project.read("cad/test_points") as read_points:
    ...     print(read_points.points[2])
    [1., 1., 0.]

    Then set the 2nd point to [1, 2, 3]:

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import PointSet
    >>> project = Project()
    >>> with project.edit("cad/test_points") as edit_points:
    ...     edit_points.points[2] = [1, 2, 3]

    Iterate over all of the points and print them.

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import PointSet
    >>> project = Project()
    >>> with project.read("cad/test_points") as read_points:
    >>>     for point in read_points.points:
    >>>         print(point)
    [0., 0., 0.]
    [1., 0., 0.]
    [1., 2., 3.]
    [0., 1., 0.]
    [0., 2., 2.]
    [0., -1., 3.]

    Print all points with y > 0 using numpy. Note that index has one
    element for each point which will be true if that point has y > 0
    and false otherwise. This is then used to retrieve the points with
    y > 0.

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import PointSet
    >>> project = Project()
    >>> with project.read("cad/test_points") as read_points:
    ...     index = read_points.points[:, 1] > 0
    ...     print(read_points.points[index])
    [[1. 2. 3.]
     [0. 1. 0.]
     [0. 2. 2.]]

    To add a new point to a PointSet, the numpy row_stack function can be
    used. This is demonstrated by the following example which creates
    a point set and then opens it for editing and adds an extra point.
    The original points are coloured blue and the new point is coloured red.

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import PointSet
    >>> import numpy as np
    >>> if __name__ == "__main__":
    ...   with Project() as project:
    ...     with project.new("cad/append_single_example", PointSet
    ...         ) as point_set:
    ...       point_set.points = [
    ...         [-1, -1, 0], [1, -1, 0], [-1, 1, 0], [1, 1, 0]
    ...       ]
    ...       point_set.point_colours = [0, 0, 255, 255]
    ...     with project.edit(point_set.id) as edit_set:
    ...       edit_set.points = np.vstack((edit_set.points, [0, 0, 1]))
    ...       edit_set.point_colours[-1] = [255, 0, 0, 255]

    The row stack function can also be used to add multiple points to
    an object at once, as demonstrated in the following example:

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import PointSet
    >>> import numpy as np
    >>> if __name__ == "__main__":
    ...   original_points = [[-1, -1, 1], [1, -1, 1], [-1, 1, 1], [1, 1, 1]]
    ...   new_points = [[-1, -1, 2], [1, -1, 2], [-1, 1, 2], [1, 1, 2]]
    ...       with Project() as project:
    ...     with project.new("cad/append_multiple_example", PointSet
    ...         ) as point_set:
    ...       point_set.points = original_points
    ...       point_set.point_colours = [0, 0, 255, 255]
    ...     with project.edit(point_set.id) as edit_set:
    ...       original_point_count = edit_set.point_count
    ...       edit_set.points = np.vstack((edit_set.points, new_points))
    ...       new_point_count = edit_set.point_count
    ...       edit_set.point_colours[
    ...         original_point_count:new_point_count] = [255, 0, 0, 255]

    The row stack function can combine more than two point arrays if
    required by adding additional arrays to the tuple passed to the function.
    This is demonstrated by the following example, which creates a new
    point set containing the points from the point sets in the previous
    two examples plus a third set of points defined in the script.
    Make sure to run the previous two examples before running this one.

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import PointSet
    >>> import numpy as np
    >>> if __name__ == "__main__":
    ...   extra_points = [[-2, -2, 3], [2, -2, 3], [-2, 2, 3], [2, 2, 3]]
    ...   with Project() as project:
    ...     with project.new("cad/triple_point_stack", PointSet) as new_set, \\
    ...         project.read("cad/append_single_example") as single_set, \\
    ...         project.read("cad/append_multiple_example") as multiple_set:
    ...       new_set.points = np.vstack((
    ...         extra_points,
    ...         single_set.points,
    ...         multiple_set.points
    ...       ))
    """
    return self._points.values

  @points.setter
  def points(self, points: npt.ArrayLike):
    self._points.values = points

  @property
  def point_z(self) -> FloatArray:
    """The Z coordinates of the points.

    Raises
    ------
    ValueError
      If set using a string which cannot be converted to a float.
    ValueError
      If set to a value which cannot be broadcast to the right shape.
    TypeError
      If set using a value which cannot be converted to a float.
    """
    if self.__point_z is None or \
        not np.may_share_memory(self.points, self.__point_z):
      self.__point_z = self.points[:][:, 2]
    return self.__point_z

  @point_z.setter
  def point_z(self, new_z: npt.ArrayLike):
    self.point_z[:] = new_z

  def append_points(self, *points: PointLike | PointArrayLike) -> BooleanArray:
    """Append points to the object.

    Using this function is preferable to assigning to the points array
    directly because it allows points to be added to the object without
    any risk of changing existing points by accident. The return value
    can also be used to assign point properties for the new points.

    Parameters
    ----------
    points
      Points to append to the object.

    Returns
    -------
    BooleanArray
      Boolean array which can be used to assign properties for the newly
      added points.

    Raises
    ------
    AppendPointsNotSupportedError
      If the object does not support appending points.
      This is raised for GridSurfaces, and non-new Scans.

    Examples
    --------
    This function can be used to add a single point to an object:

    >>> point_set: PointSet
    >>> point_set.append_points([1.5, -1.5, 2.25])

    Passing multiple points can be used to append multiple points at once:

    >>> point_set: PointSet
    >>> point_set.append_points([3.1, 1.1, 4.1], [2.2, 7.2, 1.2])

    This function also accepts iterables of points, so the following is
    functionally identical to the previous example:

    >>> point_set: PointSet
    >>> point_set.append_points([[3.1, 1.1, 4.1], [2.2, 7.2, 1.2]])

    The return value of this function can be used to assign point properties
    to the newly added points:

    >>> point_set: PointSet
    >>> new_point_indices = point_set.append_points(
    ...     [3.1, 1.1, 4.1], [2.2, 7.2, 1.2])
    >>> # Colour the two new points blue and magenta.
    >>> point_set.point_colours[new_point_indices] = [
    ...     [0, 0, 255, 255], [255, 0, 255, 255]]
    """
    new_points, new_point_mask = append_rows_to_2d_array(self.points, *points)
    try:
      self.points = new_points
    except ValueError as error:
      # This should only be hit if the points array is a fixed length
      # so cannot be resized.
      raise AppendPointsNotSupportedError(
        "This object does not support appending primitives."
      ) from error

    return new_point_mask

  @property
  def point_colours(self) -> ColourArray:
    """The colour of each point in RGBA.

    This is a numpy array of shape (N, 4) where N is the point count.

    Examples
    --------
    To get the colour of the ith point:

    >>> point_i_colour = point_set.point_colours[i]

    To get the red, green, blue and alpha components of the ith point:

    >>> red, green, blue, alpha = point_set.point_colours[i]
    """
    return self._point_colours.values

  @point_colours.setter
  def point_colours(self, point_colours: npt.ArrayLike):
    self._point_colours.values = point_colours

  @property
  def point_visibility(self) -> BooleanArray:
    """An array which indicates which points are visible.

    This is an array of booleans of shape (N,) where N is the point count. If
    the ith element in this array is True, then the ith point is visible. If the
    ith element in this array is False, then the ith point is invisible.

    Warns
    -----
    DeprecationWarning
      Setting the point visibility on `Polygons`, `Polylines`, `EdgeNetwork`,
      `RibbonLoop` and `RibbonChain` objects is deprecated because it
      has no visible affect. For such objects, all points are always visible.

    Examples
    --------
    To get if the ith point is visible:

    >>> point_i_visible = point_set.point_visibility[i]

    The point visibility can be used to filter the arrays of other per-point
    properties down to only include the values of visible points. The following
    snippet demonstrates getting the colours of only the visible points in
    an object:

    >>> visible_colours = point_set.point_colours[point_set.point_visibility]
    """
    return self._point_visibility.values

  @point_visibility.setter
  def point_visibility(self, point_visibility: BooleanArrayLike):
    self._point_visibility.values = point_visibility

  @property
  def point_selection(self) -> BooleanArray:
    """An array which indicates which points have been selected.

    This is an array of booleans of shape (N,) where N is the point count. If
    the ith element in this array is True, then the ith point is selected. If
    the ith element in this array is False, then the ith point is not selected.

    Examples
    --------
    To get if the ith point is selected:

    >>> point_i_selected = point_set.point_selection[i]

    The point selection can be used to filter the arrays of other per-point
    properties down to only include the values of selected points. The following
    snippet demonstrates getting the colours of only the selected points in
    an object:

    >>> selected_colours = point_set.point_colours[point_set.point_selection]
    """
    return self._point_selection.values

  @point_selection.setter
  def point_selection(self, point_selection: npt.ArrayLike):
    self._point_selection.values = point_selection

  @property
  def point_count(self) -> int:
    """The number of points in this object."""
    # If points haven't been loaded, load point count from
    # the Project. Otherwise derive it.
    if not self._points.are_values_cached:
      return self._modelling_api().ReadPointCount(self._lock.lock)
    return self.points.shape[0]

  @property
  def _are_points_cached(self) -> bool:
    """Allow subclasses to query if the points are cached."""
    return self._points.are_values_cached

  def _invalidate_point_properties(self):
    """Invalidates the cached point properties.

    The next time a point property is accessed, its values will be loaded from
    the project.
    """
    self._points.invalidate()
    self._point_colours.invalidate()
    self._point_selection.invalidate()
    self._point_visibility.invalidate()
    self.__point_attributes = None
    self.__point_z = None

  def _save_point_properties(self):
    """Save the point properties.

    This must be called during save() of the inheriting object.
    This should never be called directly. To save an object, call save()
    instead.

    Raises
    ------
    CannotSaveInReadOnlyModeError
      If in read-only mode.
    """
    self._raise_if_save_in_read_only()
    # Write all relevant properties for this primitive type.
    if not self._points.read_only:
      if self.point_count == 0:
        message = "Object must contain at least one point."
        raise DegenerateTopologyError(message)
      self._points.save()
    self._point_colours.save()
    self._point_visibility.save()
    self._point_selection.save()

    if self.__point_attributes is not None:
      self.__point_attributes.save_attributes()

  @property
  def point_attributes(self) -> PrimitiveAttributes:
    """Access the custom point attributes.

    These are arrays of values of the same type, with one value for each point.

    Use Object.point_attributes[attribute_name] to access the point attribute
    called attribute_name. See PrimitiveAttributes for valid operations
    on point attributes.

    Returns
    -------
    PrimitiveAttributes
      Access to the point attributes.

    Raises
    ------
    ValueError
      If the type of the attribute is not supported.
    """
    if self.__point_attributes is None:
      self.__point_attributes = PrimitiveAttributes(
        PrimitiveType.POINT,
        # PointProperties requires that the inheriting class is Topology
        # so that self can be passed here.
        self # type: ignore
      )
    return self.__point_attributes

  def save_point_attribute(
      self, attribute_name: str | AttributeKey, data: npt.ArrayLike):
    """Create and/or edit the values of the point attribute attribute_name.

    This is equivalent to Object.point_attributes[attribute_name] = data.

    Saving a point attribute using an AttributeKey allows for additional
    metadata to be specified.

    Parameters
    ----------
    attribute_name
      The name or key of the attribute.
    data
      An array_like of length point_count containing the values
      for attribute_name.

    Raises
    ------
    ValueError
      If the type of the attribute is not supported.
    AmbiguousNameError
      If there is already an attribute with the same name, but with different
      metadata.
    """
    self.point_attributes[attribute_name] = data

  def delete_point_attribute(self, attribute_name: str | AttributeKey):
    """Delete a point attribute by name.

    This is equivalent to: point_attributes.delete_attribute(attribute_name)

    Parameters
    ----------
    attribute_name
      The name or key of the attribute.
    """
    self.point_attributes.delete_attribute(attribute_name)

  def _record_point_telemetry(self):
    """Add size telemetry for points to telemetry."""
    self._record_size_for("Points", self.point_count)

    point_attributes = self.__point_attributes
    if point_attributes is not None :
      # pylint: disable=protected-access
      point_attributes._record_telemetry()

# pylint: disable=too-few-public-methods
class PointDeletionProperties:
  """Mixin class which adds functionality for removing points.

  This is intended to be used in addition to PointProperties. It is a separate
  class because not all objects which have points support remove_points.
  """
  # Properties the inheriting object is expected to provide:
  if typing.TYPE_CHECKING:
    _lock: WriteLock | ReadLock

    def _raise_if_read_only(self, operation: str):
      raise NotImplementedError

    def _invalidate_properties(self):
      raise NotImplementedError

    def _reconcile_changes(self):
      raise NotImplementedError

    @classmethod
    def _modelling_api(cls) -> ModellingApi:
      raise NotImplementedError

  def remove_points(self, point_indices: int | Sequence[int]):
    """Remove one or more points from the object.

    Calling this function is preferable to altering the points array because
    this function also removes the point properties associated with the removed
    points (e.g. point colours, point visibility, etc).

    This operation is performed directly on the Project and will not be undone
    if an error occurs.

    Parameters
    ----------
    point_indices
      The index of the point to remove or a list of indices of points to
      remove.
      Indices should only contain 32-bit unsigned integer (They should be
      greater than or equal to 0 and less than 2**32).
      Any index greater than or equal to the point count is ignored.
      Passing an index less than zero is not supported. It will not delete
      the last point.


    Returns
    -------
    bool
      If passed a single point index, True if the point was removed
      and False if it was not removed.
      If passed an iterable of point indices, True if the object supports
      removing points and False otherwise.

    Raises
    ------
    ReadOnlyError
      If called on an object not open for editing. This error indicates an
      issue with the script and should not be caught.

    Warnings
    --------
    Any unsaved changes to the object when this function is called are
    discarded before any points are deleted. If you wish to keep these changes,
    call save() before calling this function.

    Examples
    --------
    Deleting a point through this function is preferable over removing the
    point from the points array because this function also deletes the
    properties associated with the deleted points. For example, all points
    will remain the same colour after the deletion operation, which points
    are visible will remain the same, etc. This is shown in the following
    script:

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import PointSet
    >>> project = Project()
    >>> red = [255, 0, 0, 255]
    >>> blue = [0, 0, 255, 255]
    >>> with project.new("cad/deletion_example", PointSet) as point_set:
    ...     point_set.points = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]]
    ...     point_set.point_colours = [red, red, blue, blue]
    ...     point_set.point_attributes["attribute"] = [0, 1, 2, 3]
    >>> with project.edit(point_set.id) as edit_set:
    ...     edit_set.remove_points((1, 2))
    ...     print("points\\n", edit_set.points)
    ...     print("colours\\n", edit_set.point_colours)
    ...     print("attribute\\n", edit_set.point_attributes["attribute"])
    points
     [[0. 0. 0.]
     [1. 1. 0.]]
    colours
     [[255   0   0 255]
     [  0   0 255 255]]
    attribute
     [0 3]
    """
    self._invalidate_properties()
    if isinstance(point_indices, int):
      result = self._remove_point(point_indices)
    else:
      if not isinstance(point_indices, Sequence):
        point_indices = list(point_indices)
      result = self._remove_points(point_indices)
    self._reconcile_changes()
    return result

  def _remove_point(self, point_index: int):
    """Flag single Point index for removal when the lock is closed.

    Parameters
    ----------
    point_index
      Index of point to remove.

    Returns
    -------
    bool
      True if successful.

    Raises
    ------
    ReadOnlyError
      If called on an object not open for editing. This error indicates an
      issue with the script and should not be caught.

    Notes
    -----
    Changes will not be reflected until the object is saved or
    _reconcile_changes() is called.
    """
    self._raise_if_read_only("remove points")
    return self._modelling_api().RemovePoint(self._lock.lock,
                                   point_index)

  def _remove_points(self, point_indices: Sequence[int]):
    """Remove list of points at given indices of point array.

    Parameters
    ----------
    point_indices
      1D array of uint32 indices of points to remove.

    Returns
    -------
    bool
      True if successful.

    Raises
    ------
    ReadOnlyError
      If called on an object not open for editing. This error indicates an
      issue with the script and should not be caught.

    Notes
    -----
    Changes will not be reflected until the object is saved or
    _reconcile_changes() is called.
    """
    self._raise_if_read_only("remove points")
    index_count = len(point_indices)
    array = (ctypes.c_uint32 * index_count)(*point_indices)
    return self._modelling_api().RemovePoints(
      self._lock.lock, array, index_count)
