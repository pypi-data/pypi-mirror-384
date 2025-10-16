"""The filled polygon class."""
###############################################################################
#
# (C) Copyright 2023, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

from collections.abc import MutableMapping, Sequence, MutableSequence
import ctypes
import typing

import numpy as np

from .base import Topology, StaticType
from .errors import DegenerateTopologyError, StaleDataError
from .objectid import ObjectID
from .primitives.primitive_attributes import (
  PrimitiveAttributes, PrimitiveType, AttributeKey)
from ..internal.data_property import DataProperty, DataPropertyConfiguration
from ..internal.mapping_view import MutableMappingView
from ..internal.lock import LockType, ObjectClosedError
from ..internal.util import append_rows_to_2d_array

if typing.TYPE_CHECKING:
  import numpy.typing as npt

  from ..common.typing import (
    PointLike, PointArray, PointArrayLike,
    EdgeLike, EdgeArray, EdgeArrayLike,
    BooleanArray, BooleanArrayLike, Colour, IndexArray, MutableIndexSequence
  )


class Loop:
  """A loop of points in a FilledPolygon.

  Do not construct this class directly. Instead access it via the
  FilledPolygon.loops property.

  This allows for accessing the point and edge properties associated with a
  particular loop of points.

  Notes
  -----
  The properties of this class return copies of the property arrays. This
  means assigning directly to the values returned from the properties will not
  mutate the original arrays.
  """
  def __init__(
      self,
      owner: FilledPolygon,
      point_indices: MutableIndexSequence,
      edge_indices: MutableIndexSequence) -> None:
    self.__owner = owner
    self.__point_indices: MutableIndexSequence | None = point_indices
    """Backing sequence for self._point_indices.

    This should only be accessed inside of self._point_indices.
    None indicates this object has been invalidated.
    """
    self.__edge_indices: MutableIndexSequence | None = edge_indices
    """Backing sequence for self._edge_indices.

    This should only be accessed inside of self._edge_indices.
    None indicates this object has been invalidated.
    """

  @property
  def _owner(self) -> FilledPolygon:
    """The filled polygon this loop is part of.

    Raises
    ------
    ObjectClosedError
      If the owning object is closed.
    """
    if self.__owner.closed:
      raise ObjectClosedError(
        "The FilledPolygon this loop is part of is closed.")
    return self.__owner

  @property
  def _point_indices(self) -> MutableIndexSequence:
    """The point indices in the FilledPolygon which make up this loop.

    This should be used instead of the backing field to avoid accessing points
    after the loop has been invalidated.

    Raises
    ------
    StaleDataError
      If this object has been invalidated.
    """
    if self.__point_indices is None:
      raise StaleDataError(
        "This loop has been invalidated."
      )
    return self.__point_indices

  @property
  def _edge_indices(self) -> MutableIndexSequence:
    """The edge indices in the FilledPolygon which make up this loop.

    This should be used instead of the backing field to avoid accessing points
    after the loop has been invalidated.

    Raises
    ------
    StaleDataError
      If this object has been invalidated.
    """
    if self.__edge_indices is None:
      raise StaleDataError(
        "This loop has been invalidated."
      )
    return self.__edge_indices

  @property
  def point_count(self) -> int:
    """Count of the points in this loop.

    Raises
    ------
    StaleDataError
      If this loop has been invalidated due to the owning object being closed,
      or due to a point being deleted.
    """
    return len(self._point_indices)

  @property
  def edge_count(self) -> int:
    """Count of the edges in this loop.

    Raises
    ------
    StaleDataError
      If this loop has been invalidated due to the owning object being closed,
      or due to a point being deleted.
    """
    return len(self._edge_indices)

  @property
  def points(self) -> PointArray:
    """A copy of the points in the loop.

    Raises
    ------
    ObjectClosedError
      If the FilledPolygon this loop is a part of is closed.
    StaleDataError
      If this loop has been invalidated due to the removal of a point.
    """
    return self._owner.points[self._point_indices]

  @property
  def edges(self) -> EdgeArray:
    """A copy of the edges in the loop.

    Raises
    ------
    ObjectClosedError
      If the FilledPolygon this loop is a part of is closed.
    StaleDataError
      If this loop has been invalidated due to the removal of a point.
    """
    return self._owner.edges[self._edge_indices]

  @property
  def point_selection(self) -> BooleanArray:
    """A copy of the point selection information for the loop.

    Setting this property to a sequence of length self.point_count will set
    the point selection for the points in this loop without affecting the
    point selection of points in different loops.

    Raises
    ------
    ObjectClosedError
      If the FilledPolygon this loop is a part of is closed.
    StaleDataError
      If this loop has been invalidated due to the removal of a point.
    """
    return self._owner.point_selection[self._point_indices]

  @point_selection.setter
  def point_selection(self, new_selection: BooleanArrayLike):
    self._owner.point_selection[self._point_indices] = new_selection

  @property
  def edge_selection(self) -> BooleanArray:
    """A copy of the edge selection information for the loop.

    Setting this property to a sequence of length self.edge_count will set
    the edge selection for the edges in this loop without affecting the
    edge selection of edges in different loops.

    Raises
    ------
    ObjectClosedError
      If the FilledPolygon this loop is a part of is closed.
    StaleDataError
      If this loop has been invalidated due to the removal of a point.
    """
    return self._owner.edge_selection[self._edge_indices]

  @edge_selection.setter
  def edge_selection(self, new_selection: BooleanArrayLike):
    self._owner.edge_selection[self._edge_indices] = new_selection

  @property
  def point_attributes(self) -> MutableMapping[AttributeKey, np.ndarray]:
    """Access the point attributes for the loop.

    This returns a mapping which allows for basic operations on the point
    attributes.

    Raises
    ------
    ObjectClosedError
      If the FilledPolygon this loop is a part of is closed.
    StaleDataError
      If this loop has been invalidated due to the removal of a point.
    """
    filled_polygon = self._owner
    indices = self._point_indices

    def set_item(
        owner: PrimitiveAttributes, key: AttributeKey, value: np.ndarray):
      if key not in owner:
        value = np.array(value)
        owner[key] = np.zeros((owner.primitive_count,), dtype=value.dtype)
      owner[key][self._point_indices] = value

    return MutableMappingView(
      owner=filled_polygon.point_attributes,
      get_item=lambda owner, key: owner[key][indices],
      set_item=set_item # type: ignore It quacks like a duck!
    )

  @property
  def edge_attributes(self) -> MutableMapping[AttributeKey, np.ndarray]:
    """Access the edge attributes for the loop.

    This returns a mapping which allows for basic operations on the edge
    attributes.

    Raises
    ------
    ObjectClosedError
      If the FilledPolygon this loop is a part of is closed.
    StaleDataError
      If this loop has been invalidated due to the removal of a point.
    """
    filled_polygon = self._owner
    indices = self._edge_indices

    def set_item(
        owner: PrimitiveAttributes, key: AttributeKey, value: np.ndarray):
      if key not in owner:
        value = np.array(value)
        owner[key] = np.zeros((owner.primitive_count,), dtype=value.dtype)
      owner[key][self._edge_indices] = value

    return MutableMappingView(
      owner=filled_polygon.edge_attributes,
      get_item=lambda owner, key: owner[key][indices],
      set_item=set_item # type: ignore It quacks like a duck!
    )

  def _invalidate(self):
    """Invalidate this loop.

    This causes accessing any of the properties of this object to raise a
    StaleDataError. This is useful for cases where the loops must be
    completely regenerated after a change.
    """
    self.__point_indices = None
    self.__edge_indices = None

  def append_points(self, points: PointLike | PointArrayLike):
    """Append a point to the end of the current loop.

    This updates the edges

    Parameters
    ----------
    point
      A single point to append to the loop, or an array of points to append.

    Raises
    ------
    ObjectClosedError
      If the FilledPolygon this loop is a part of is closed.
    StaleDataError
      If this loop has been invalidated due to the removal of a point.
    """
    owner = self._owner
    point_indices = self._point_indices
    edge_indices = self._edge_indices

    previous_last_point_index = point_indices[-1]
    previous_last_edge_index = edge_indices[-1]

    # pylint: disable=protected-access
    # Append points is protected because users will probably make a mistake
    # if they call it directly.
    point_mask = owner._append_points(points)
    new_point_indices = point_mask.nonzero()[0]

    # Given new_point_indices = [D, E, F]
    # new_point_indices[:-1] = [D, E]
    # new_point_indices[1:] = [E, F]
    # This gives new edges as:
    # [D, E], [E, F]
    new_edges = [
      [start, end] for start, end in zip(
        new_point_indices[:-1], new_point_indices[1:])
    ]
    # Add the edge required to close the loop.
    # It connects the last newly added point to the first point in the loop.
    new_edges.append([new_point_indices[-1], point_indices[0]])
    edge_mask = owner._append_edges(new_edges)
    # The edge which connected the previous last point to the first point must
    # be adjusted so that it connects the previous last point to the first new
    # point.
    owner.edges[previous_last_edge_index] = [
      previous_last_point_index, new_point_indices[0]]

    # Update this object so that it handles the new edges.
    point_indices.extend(new_point_indices)
    edge_indices.extend(edge_mask.nonzero()[0])

  def remove_points(self, point_indices: int | Sequence[int]):
    """Remove one or more points from this loop.

    This will invalidate the properties of the FilledPolygon object, requiring
    values to be re-read from the application. Any unsaved changes will be
    lost.

    Parameters
    ----------
    point_indices
      A sequence of point indices to remove, or a single point index to remove.
      This is based on the index of the point in this loop.
      i.e. An index of zero indicates the first point in this loop.

    Raises
    ------
    DegenerateTopologyError
      If the remove operation would result in this loop containing less than
      3 points.

    Raises
    ------
    ObjectClosedError
      If the FilledPolygon this loop is a part of is closed.
    StaleDataError
      If this loop has been invalidated due to the removal of a point.
    """
    owner = self._owner
    current_indices = self._point_indices
    indices_to_delete = point_indices if isinstance(
      point_indices, Sequence) else [point_indices]
    current_point_count = len(current_indices)
    remove_count = len(indices_to_delete)
    count_after_removal = current_point_count - remove_count
    if count_after_removal < 3:
      raise DegenerateTopologyError(
        f"Cannot remove {remove_count} points. The operation would result "
        f"in loop containing {count_after_removal} points, which is less "
        "than 3 points."
      )

    # pylint: disable=protected-access
    owner._remove_points(
      [current_indices[index] for index in indices_to_delete]
    )


# :NOTE: FilledPolygon does not inherit from PointProperties and EdgeProperties
# because it does not support all of the properties they define
# (e.g. point_colours, point_visibility and edge_colours).
class FilledPolygon(Topology):
  """A filled polygon which can have holes in it.

  A FilledPolygon is defined by a series of loops. Each loop
  is defined as 'additive' or 'subtractive'. The inside of an additive
  loop are filled, whereas the inside of a subtractive loop are
  not. Whether a loop is additive or subtractive is defined by the
  following rules:

  1. The outermost loop is always additive.
  2. Any loop inside of an additive loop is subtractive.
  3. Any loop outside of a subtractive loop is additive.

  This means that for each point has edges connecting it to precisely two
  other points. The filled polygon supports duplicate points,
  so if a subtractive loop would otherwise share a point with an
  additive loop, the object will contain duplicate points (i.e.
  Two different points with the same x, y and z ordinates).

  Notes
  -----
  If two loops overlap, with neither fully contained inside
  the other, the Python SDK will not issue an error, however, whether
  either loop is additive or subtractive is not defined.

  Examples
  --------
  Instead of assigning to the points property of a FilledPolygon, the
  points are added via the add_loop() function. This accepts a list of
  ordered points representing the loop to add to the object. This
  is demonstrated by the following script:

  >>> from mapteksdk.project import Project
  >>> from mapteksdk.data import FilledPolygon
  >>> with Project() as project, project.new(
  ...         "cad/example_filled_polygon", FilledPolygon) as filled_polygon:
  ...     # The outermost loop is additive.
  ...     filled_polygon.add_loop(
  ...         [[-10, -10, 0], [10, -10, 0], [10, 10, 0], [-10, 10, 0]]
  ...     )
  ...     # This loop is contained within the previous one, which is
  ...     # additive, so it is subtractive.
  ...     filled_polygon.add_loop(
  ...         [[-5, -5, 0], [5, -5, 0], [5, 5, 0], [-5, 5, 0]]
  ...     )
  ...     # This loop is contained within the previous one, which is
  ...     # subtractive, so it is additive.
  ...     filled_polygon.add_loop(
  ...         [[-2.5, -2.5, 0], [2.5, -2.5, 0], [2.5, 2.5, 0], [-2.5, 2.5, 0]]
  ...     )
  ...     # Set the filled parts of the object to be plum coloured.
  ...     filled_polygon.fill_colour = [221, 160, 221, 255]
  """
  __POINTS = 0
  """Index of the property which stores the points."""
  __EDGES = 1
  """Index of the property which stores the edges."""
  __POINT_SELECTION = 2
  """Index of the property which stores the point selection."""
  __EDGE_SELECTION = 3
  """Index of the property which stores the edge selection."""

  def __init__(
      self,
      object_id: ObjectID | None=None,
      lock_type: LockType=LockType.READWRITE,
      *,
      rollback_on_error: bool = False):
    if object_id is None:
      object_id = ObjectID(self._modelling_api().NewEdgeLoopArea())
    super().__init__(object_id, lock_type, rollback_on_error=rollback_on_error)
    self.__data_properties: dict[int, DataProperty] = {
      self.__POINTS : DataProperty(
        lock=self._lock,
        configuration=DataPropertyConfiguration(
          name="points",
          dtype=ctypes.c_double,
          default=np.nan,
          column_count=3,
          primitive_count_function=self._modelling_api().ReadPointCount,
          cached_primitive_count_function=None,
          load_function=self._modelling_api().PointCoordinatesBeginR,
          save_function=self._modelling_api().PointCoordinatesBeginRW,
          set_primitive_count_function=self._modelling_api().SetPointCount,
          raise_on_error_code=self._modelling_api().RaiseOnErrorCode
        )
      ),
      self.__POINT_SELECTION: DataProperty(
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
      ),
      self.__EDGES : DataProperty(
        lock=self._lock,
        configuration=DataPropertyConfiguration(
          name="edges",
          dtype=ctypes.c_int32,
          default=0,
          column_count=2,
          primitive_count_function=self._modelling_api().ReadEdgeCount,
          load_function=self._modelling_api().EdgeToPointIndexBeginR,
          save_function=self._modelling_api().EdgeToPointIndexBeginRW,
          cached_primitive_count_function=None,
          set_primitive_count_function=self._modelling_api().SetEdgeCount,
          immutable=False,
          raise_on_error_code=self._modelling_api().RaiseOnErrorCode
        )
      ),
      self.__EDGE_SELECTION : DataProperty(
        lock=self._lock,
        configuration=DataPropertyConfiguration(
          name="edge_selection",
          dtype=ctypes.c_bool,
          default=False,
          column_count=1,
          primitive_count_function=self._modelling_api().ReadEdgeCount,
          cached_primitive_count_function=lambda: self.edge_count,
          load_function=self._modelling_api().EdgeSelectionBeginR,
          save_function=self._modelling_api().EdgeSelectionBeginRW,
          raise_on_error_code=self._modelling_api().RaiseOnErrorCode
        )
      ),
    }
    self.__point_attributes: PrimitiveAttributes | None = None
    self.__edge_attributes: PrimitiveAttributes | None = None
    self.__loops: MutableSequence[Loop] | None = None
    """Backing field for the loops which make up this object.

    This should be accessed internally via the _loops property, which ensures
    that the loops are cached.
    This should be accessed externally via the loops property, which returns
    an immutable copy.
    """

    # Saving the point colours requires saving the uniform point colours,
    # which is not supported as a save_function() for DataProperty.
    # :TODO: SDK-851: This would be better implemented as a
    # SingularDataPropertyReadWrite.
    self.__point_colours = DataProperty(
      lock=self._lock,
      configuration=DataPropertyConfiguration(
        name="point_colours",
        dtype=ctypes.c_uint8,
        default=np.array([0, 220, 0, 255], dtype=ctypes.c_uint8),
        column_count=1,
        primitive_count_function=self._modelling_api().ReadPointCount,
        cached_primitive_count_function=lambda: 4,
        load_function=self._modelling_api().PointColourBeginR,
        save_function=None,
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode
      )
    )

  @classmethod
  def static_type(cls) -> StaticType:
    return cls._modelling_api().EdgeLoopAreaType()

  def _extra_invalidate_properties(self):
    for data_property in self.__data_properties.values():
      data_property.invalidate()
    self.__point_attributes = None
    self.__edge_attributes = None
    self.__point_colours.invalidate()
    if self.__loops:
      for loop in self.__loops:
        # pylint: disable=protected-access
        loop._invalidate()
      self.__loops = None

  def _record_object_size_telemetry(self):
    # Ideally, this object would inherit from PointProperties so that it can
    # use _record_point_telemetry().
    self._record_size_for("Points", self.point_count)

  def _save_topology(self):
    if self.edge_count < 3:
      raise DegenerateTopologyError(
        "FilledPolygon requires at least three edges."
      )
    for data_property in self.__data_properties.values():
      data_property.save()
    if self.__point_attributes is not None:
      self.__point_attributes.save_attributes()
    if self.__edge_attributes is not None:
      self.__edge_attributes.save_attributes()
    if self.__point_colours.are_values_cached:
      c_colour = (ctypes.c_uint8 * 4)()
      c_colour[:] = self.__point_colours.values
      self._modelling_api().SetUniformPointColour(self._lock.lock, c_colour)
      self._modelling_api().SetUniformEdgeColour(self._lock.lock, c_colour)

  def _remove_points(self, point_indices: Sequence[int]):
    """Remove the points at the given indices of the points array.

    This will also update the edges array to ensure that each loop is still
    fully connected. However, it is the caller's responsibility to ensure
    that the deletion will not result in any loops with less than three
    points.

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
    This will clear any unsaved changes and reconcile changes.
    """
    self._invalidate_properties()
    self._raise_if_read_only("remove points")
    index_count = len(point_indices)
    array = (ctypes.c_uint32 * index_count)(*point_indices)
    result = self._modelling_api().RemovePoints(
      self._lock.lock, array, index_count)
    self._reconcile_changes()
    return result

  @property
  def _loops(self) -> MutableSequence[Loop]:
    """Internal sequence of loops.

    This should not be accessed by scripts. This is used internally by the
    class.
    """
    if self.__loops is None:
      self.__loops = self.__generate_loops()
    return self.__loops

  @property
  def loops(self) -> Sequence[Loop]:
    """The sequence of loops which define the object.

    Raises
    ------
    DegenerateTopologyError
      If the object is degenerate.
    """
    # Return an immutable copy.
    return tuple(self._loops)

  def remove_loop(self, loop_index: int):
    """Delete the loop with the specified index.

    This deletes all of the points which makes up that loop.

    Parameters
    ----------
    loop_index
      The index of the loop to delete in the loops sequence for this object.

    Raises
    ------
    IndexError
      If there is no loop with the give index.
    DegenerateTopologyError
      If attempting to delete the only loop in the object.

    Notes
    -----
    Calling this function will discard any unsaved changes and invalidate all
    of the properties for this object.
    """
    loop = self.loops[loop_index]
    if len(self.loops) == 1:
      raise DegenerateTopologyError(
        "Cannot delete the only loop in the object."
      )
    self._remove_points(loop._point_indices)

  @property
  def points(self) -> PointArray:
    """Flat view of the points which make up the FilledPolygon.

    This contains all of the points in each loop contained within
    the filled polygon. Similar to the points properties of other
    objects, properties with one value per point (e.g. point_selection)
    have the index based on this array.
    """
    return self.__data_properties[self.__POINTS].values

  def _append_points(
      self,
      new_points: PointLike | PointArrayLike) -> BooleanArray:
    """Append new points to the points array.

    Appending to the end of the array ensures that the point property arrays
    can be updated by appending default values to the end of the array.

    Parameters
    ----------
    new_points
      A single point or an array of points to append to the points array.

    Returns
    -------
    BooleanArray
      An array with one boolean for each point after the append operation.
      If index i is True, then point i was added by this function.
      If index i is False, then point i was not added by this function.
    """
    point_property = self.__data_properties[self.__POINTS]
    new_array, mask = append_rows_to_2d_array(
      point_property.values,
      new_points
    )
    point_property.values = new_array
    return mask

  def _append_edges(self, new_edges: EdgeLike | EdgeArrayLike) -> BooleanArray:
    """Append new edges to the edges array.

    Appending to the end of the array ensures that the point property arrays
    can be updated by appending default values to the end of the array.

    Parameters
    ----------
    new_edges
      A single edge or an array of edges to append to the edges.

    Returns
    -------
    BooleanArray
      An array with one boolean for each point after the append operation.
      If index i is True, then point i was added by this function.
      If index i is False, then point i was not added by this function.
    """
    edge_property = self.__data_properties[self.__EDGES]
    new_array, mask = append_rows_to_2d_array(
      edge_property.values,
      new_edges
    )
    edge_property.values = new_array
    return mask

  @property
  def point_count(self) -> int:
    """The number of points in the FilledPolygon.

    Unlike PointSet and most other objects with points, a FilledPolygon
    may include duplicate points.
    """
    points_property = self.__data_properties[self.__POINTS]
    if not points_property.are_values_cached:
      return self._modelling_api().ReadPointCount(self._lock.lock)
    return points_property.values.shape[0]

  @property
  def point_selection(self) -> BooleanArray:
    """Point selection array.

    This has one value per point in the array. The point at points[i]
    is selected if point_selection[i] is True.
    """
    return self.__data_properties[self.__POINT_SELECTION].values

  @point_selection.setter
  def point_selection(self, new_selection: BooleanArrayLike):
    self.__data_properties[self.__POINT_SELECTION].values = new_selection

  @property
  def point_attributes(self) -> PrimitiveAttributes:
    """Access to the custom point attributes.

    Each point attribute has one value for each point. Note that unlike
    most other objects with points, a FilledPolygon can contain duplicate
    points. These duplicate points can have different values for
    a point attribute, which can cause issues in certain algorithms.
    """
    if self.__point_attributes is None:
      self.__point_attributes = PrimitiveAttributes(
        PrimitiveType.POINT,
        self
      )
    return self.__point_attributes

  @property
  def edges(self) -> EdgeArray:
    """The edges which make up the FilledPolygon.

    This contains all of the edges of each loop which makes up the filled
    Polygon. Similar to the edges properties of other
    objects, properties with one value per edge (e.g. edge_selection)
    have the index based on this array.
    """
    return self.__data_properties[self.__EDGES].values

  @property
  def edge_count(self) -> int:
    """The number of edges in the FilledPolygon."""
    edges_property = self.__data_properties[self.__EDGES]
    if not edges_property.are_values_cached:
      return self._modelling_api().ReadPointCount(self._lock.lock)
    return edges_property.values.shape[0]

  @property
  def edge_selection(self) -> BooleanArray:
    """Edge selection array.

    This has one value per edge in the array. The point at edges[i]
    is selected if edge_selection[i] is True.
    """
    return self.__data_properties[self.__EDGE_SELECTION].values

  @edge_selection.setter
  def edge_selection(self, new_selection: BooleanArrayLike):
    self.__data_properties[self.__EDGE_SELECTION].values = new_selection

  @property
  def edge_attributes(self) -> PrimitiveAttributes:
    """Access to the custom edge attributes.

    Each edge attribute has one value for each edge.
    """
    if self.__edge_attributes is None:
      self.__edge_attributes = PrimitiveAttributes(
        PrimitiveType.EDGE,
        self
      )
    return self.__edge_attributes

  @property
  def fill_colour(self) -> Colour:
    """The fill colour of the Polygon.

    The colour used to colour the contents of "additive" loops which
    make up the FilledPolygon object.
    """
    return self.__point_colours.values

  @fill_colour.setter
  def fill_colour(self, new_colour: npt.ArrayLike):
    if self.closed:
      raise ObjectClosedError()
    try:
      self.__point_colours.values = new_colour
    except ValueError:
      # Try to set the colour as an RGB colour.
      self.__point_colours.values[:3] = new_colour

  def point_to_loop(self, index: int) -> Loop:
    """Find the loop which contains the point with the given index.

    This is useful for performing an operation on all of the points in the
    same loop as the point with the given index.

    Parameters
    ----------
    index
      Index of the point in the points array to find the loop of.
      This does not support negative indices.

    Returns
    -------
    Loop
      The Loop object which this loop is a part of.

    Raises
    ------
    IndexError
      If there is no point with the specified index.
    """
    if index < 0 or index >= self.point_count:
      raise IndexError(f"No point with index: {index}")
    for loop in self.loops:
      # pylint: disable=protected-access
      if index in loop._point_indices:
        return loop
    # This should be unreachable.
    raise IndexError(f"No point with index: {index}")

  def edge_to_loop(self, index: int) -> Loop:
    """Find the loop which contains the edge with the given index.

    This is useful for performing an operation on all of the edges in the
    same loop as the edge with the given index.

    Parameters
    ----------
    index
      Index of the edge in the edges array to find the loop of.
      This does not support negative indices.

    Returns
    -------
    Loop
      The Loop object which this loop is a part of.

    Raises
    ------
    IndexError
      If there is no edge with the specified index.
    """
    if index < 0 or index >= self.edge_count:
      raise IndexError(f"No edge with index: {index}")
    for loop in self.loops:
      # pylint: disable=protected-access
      if index in loop._edge_indices:
        return loop
    # This should be unreachable.
    raise IndexError(f"No edge with index: {index}")

  def add_loop(
      self, new_points: PointArrayLike
      ) -> Loop:
    """Add a new loop to the object.

    It is the caller's responsibility to ensure that the new loop
    does not overlap with any other loops in the object (including
    itself). The new edges are automatically derived from the given points.

    Parameters
    ----------
    new_points
      The points which define the new loop.

    Returns
    -------
    Loop
      The newly added loop.

    Examples
    --------
    The return values of this function can be used to access and set the
    properties of the newly added points and edges.

    >>> filled_polygon: FilledPolygon
    >>> loop = filled_polygon.add_loop(
    ...     [[0, 0, 0], [10, 0, 0], [0, 10, 0]]
    ... )
    >>> # Read the newly added points.
    >>> new_points = loop.points
    >>> # Read the newly added edges.
    >>> new_edges = loop.edges
    >>> # Select the newly added points.
    >>> loop.point_selection = True
    >>> # Select the newly added edges.
    >>> loop.edge_selection = True
    """
    if len(new_points) < 3:
      raise DegenerateTopologyError(
        "new_points must contain at least 3 points.")
    loops = self._loops

    offset = self.point_count
    edges = self.__generate_loop_edges(len(new_points))
    edges += offset

    point_mask = self._append_points(new_points)
    edge_mask = self._append_edges(edges)

    loop = Loop(
      owner=self,
      point_indices=list(point_mask.nonzero()[0]),
      edge_indices=list(edge_mask.nonzero()[0])
    )
    loops.append(loop)
    return loop

  def __generate_loop_edges(self, point_count: int) -> EdgeArray:
    """Generate edges for a loop with point_count points.

    Parameters
    ----------
    point_count
      The edges for a loop with point_count points

    Returns
    -------
    EdgeArray
      Numpy array of edges. This is of the form:
      [[0, 1], [1, 2], ..., [N-1, N], [N, 0]]
      where N is the point_count.
    """
    edges = np.zeros(point_count * 2, dtype=np.uint32)
    temp = np.arange(1, point_count, dtype=np.uint32)
    edges[1:-1] = np.repeat(temp, 2)
    return edges.reshape(-1, 2)

  def __generate_loops(self) -> MutableSequence[Loop]:
    """Generate the loops for this object.

    This is based entirely on the edges array for this object.

    Returns
    -------
    MutableSequence[Loop]
      A mutable sequence of loops representing this object.
    """
    invalid_index = self.point_count

    def generate_next_point_and_edges(
        edges: EdgeArray) -> tuple[IndexArray, IndexArray]:
      """Generate an array containing the next point in the loop and the edge.

      This assumes that every point is connected to precisely two
      other points by edges. This is not sensitive to whether these
      edges are outgoing or ingoing.

      For example, given an object with the following edges:

      >>> [
      >>>      [1, 2], [5, 6], [9, 10], [4, 5], [10, 8], [2, 3],
      >>>      [0, 1], [3, 0], [8, 9], [6, 7], [7, 4]
      >>> ]

      This would return:

      >>> (
      ...   [1, 2, 3, 0, 5, 6, 7, 4, 9, 10, 8],
      ...   [0, 5, 7, 6, 1, 9, 10, 3, 2, 4, 8]
      ... )

      The first array indicates that point 0 is connected to point
      1, which is connected to point 2, which is connected to
      point 3, which is connected to point 0 and so on for the rest
      of the points.

      The second array indicates that it is edge 0 that connects
      points 1 and 2, edge 5 that connects edges 2 and 3 and so on
      for the rest of the points.

      Parameters
      ----------
      edges
        Edges to generate the next points and edges arrays for.
        Each point must be connected to exactly two other points via
        an edge.

      Returns
      -------
      next_point
        Array of the index of the next point in the loop.
      edge_indices
        Array of which edge was used to determine the next point in the loop.

      Warnings
      --------
      If any point is connected to more or less than two points, the returned
      array will contain invalid indices.
      """
      next_point = np.full((len(edges),), invalid_index, dtype=int)
      edge_indices = np.full((len(edges),), invalid_index, dtype=int)
      for index, (start, end) in enumerate(edges):
        if next_point[start] == invalid_index:
          next_point[start] = end
          edge_indices[start] = index
        elif next_point[end] == invalid_index:
          next_point[end] = start
          edge_indices[end] = index
        else:
          raise DegenerateTopologyError(
            "The FilledPolygon object contains a degenerate loop."
          )
      return next_point, edge_indices

    edges = self.edges
    loops: Sequence[Loop] = []
    if len(edges) == 0:
      return loops

    # The next points and the edges which connect them.
    next_points, edges_used = generate_next_point_and_edges(edges)

    # Set of indices of points which have not been assigned a loop.
    unused: set[int] = set(i for i in range(self.point_count))

    # The current point.
    current_point = 0

    # The indices of the points and edges in the current loop.
    point_indices = []
    edge_indices = []

    while True:
      if current_point not in unused:
        # The loop has returned to the start point.
        # Add it to the result.
        loops.append(Loop(self, point_indices, edge_indices))
        if len(unused) > 0:
          # There are more loops. Start with the lowest index
          # unused point for the next loop.
          current_point = next(iter(unused))
          point_indices = []
          edge_indices = []
          continue
        break

      unused.remove(current_point)

      # Add the point and edge to the current loop.
      point_indices.append(current_point)
      edge_indices.append(edges_used[current_point])

      # Move to the next point.
      current_point = next_points[current_point]

    return loops
