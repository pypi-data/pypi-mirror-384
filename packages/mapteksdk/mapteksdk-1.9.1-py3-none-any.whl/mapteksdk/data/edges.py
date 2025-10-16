"""Edge data types.

Data types which are based on edge primitives. This includes:

- EdgeNetwork which has discontinuous lines/polylines in single object.
- Polyline which represents an open polygon.
- Polygon which represents a closed polygon.
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
import warnings

import numpy as np

from ..internal.lock import LockType
from ..internal.singular_data_property_read_write import (
  SingularDataPropertyReadWrite)
from ..internal.util import append_rows_to_2d_array
from .base import Topology, StaticType
from .errors import DegenerateTopologyError
from .objectid import ObjectID
from .primitives import PointProperties, EdgeProperties, PointDeletionProperties

if typing.TYPE_CHECKING:
  from collections.abc import Sequence
  from ..common.typing import (
    BooleanArray,
    BooleanArrayLike,
    EdgeArray,
    EdgeArrayLike,
    IndexArray,
  )

# pylint: disable=too-many-lines
# pylint: disable=too-many-instance-attributes

# Pylint can't handle the intermediate abstract class (Edge) and incorrectly
# marks the class as not implementing abstract methods.
# See https://github.com/pylint-dev/pylint/issues/3098 for more information.
# pylint: disable=abstract-method

log = logging.getLogger("mapteksdk.data")

class Edge(Topology, EdgeProperties, PointProperties, PointDeletionProperties):
  """Base class for EdgeNetwork, Polygon and Polyline."""
  # pylint: disable=too-many-instance-attributes
  def __init__(self, object_id, lock_type=LockType.READWRITE):
    super().__init__(object_id, lock_type)
    self._initialise_point_properties(known_point_count=False)
    self.__edge_thickness = SingularDataPropertyReadWrite(
      "edge thickness",
      lambda: [self._lock.lock],
      self.is_read_only,
      self.__get_edge_thickness,
      self.__save_edge_thickness
    )

  def _extra_invalidate_properties(self):
    super()._extra_invalidate_properties()
    self._invalidate_point_properties()
    self._invalidate_edge_properties()

  def _record_object_size_telemetry(self):
    self._record_point_telemetry()
    self._record_edge_telemetry()

  def _save_topology(self):
    self.__edge_thickness.save()

  def __get_edge_thickness(self, lock) -> float:
    """Read the edge thickness."""
    return self._modelling_api().GetEdgeNetworkEdgeThickness(lock)

  def __save_edge_thickness(self, lock, thickness: float):
    return self._modelling_api().SetEdgeNetworkEdgeThickness(lock, thickness)

  @property
  def point_visibility(self) -> BooleanArray:
    return np.full((self.point_count,), True, dtype=np.bool_)

  # pylint: disable=unused-argument
  @point_visibility.setter
  def point_visibility(self, point_visibility: BooleanArrayLike):
    warnings.warn(
      DeprecationWarning(
        "Setting the point visibility of edge objects is deprecated. "
      )
    )

  @property
  def edge_thickness(self) -> float:
    """The thickness of each edge.

    Raises
    ------
    ValueError
      If set to a value which is below 1.0 or not finite.
    """
    return self.__edge_thickness.value

  @edge_thickness.setter
  def edge_thickness(self, new_thickness: float):
    actual_thickness = float(new_thickness)
    if actual_thickness < 1.0:
      raise ValueError(
        f"Unsupported edge thickness: {actual_thickness}. "
        "Edge thickness must be 1.0 or greater.")
    if not np.isfinite(actual_thickness):
      raise ValueError(
        f"Unsupported edge thickness: {actual_thickness}. "
        "Edge thickness must be finite.")
    self.__edge_thickness.value = actual_thickness

class EdgeNetwork(Edge):
  """A network of potentially disconnected lines and polylines.

  An edge network can contain multiple discontinuous lines/polylines in a
  single object. Unlike Polyline and Polygon, the user must explicitly
  set the edges.

  See Also
  --------
  :documentation:`edge-network` : Help page for this class.

  Examples
  --------
  Creating an edge network with an edge between points 0 and point 1 and a
  second edge edge between points 2 and 3.

  >>> from mapteksdk.project import Project
  >>> from mapteksdk.data import EdgeNetwork
  >>> project = Project()
  >>> with project.new("cad/edges", EdgeNetwork) as new_network:
  >>>     new_network.points = [[0, 0, 0], [1, 2, 3], [0, 0, 1], [0, 0, 2]]
  >>>     new_network.edges = [[0, 1], [2, 3]]
  """
  # pylint: disable=too-many-instance-attributes
  def __init__(self, object_id=None, lock_type=LockType.READWRITE):
    if object_id is None:
      object_id = ObjectID(self._modelling_api().NewEdgeNetwork())
    super().__init__(object_id, lock_type)
    self._initialise_edge_properties(has_immutable_edges=False)

  @property
  def edges(self) -> EdgeArray:
    return super().edges

  @edges.setter
  def edges(self, edges: EdgeArrayLike):
    self._set_edges(edges)

  def append_edges(self, *edges: EdgeArrayLike) -> BooleanArray:
    """Append new edges to the end of the edges array.

    Using this function is preferable to assigning to the edges array
    directly because it allows edges to be added to the object without
    any risk of changing existing edges by accident. The return value
    can also be used to assign edge properties for the new edges.

    Parameters
    ----------
    edges
      New edges to append to the array.

    Returns
    -------
    BooleanArray
      Boolean array which can be used to assign properties for the newly
      added edges.

    Examples
    --------
    This function can be used to add a single edge to an object:

    >>> edge_network: EdgeNetwork
    >>> # Add an edge between points 1 and 2.
    >>> edge_network.append_edges([1, 2])

    Passing multiple edges can be used to append multiple edges at once:

    >>> edge_network: EdgeNetwork
    >>> # Add an edge between points 0 and 2, another edge between points
    >>> # 1 and 2 and a third between points 2 and 3.
    >>> edge_network.append_edges([0, 2], [1, 2], [2, 3])

    This function also accepts iterables of edges, which is useful for
    copying edges between objects. For example, the following function
    will copy all of the points and edges from one object into an
    EdgeNetwork.

    >>> def concatenate_edge_networks(
    ...         source_network: EdgeNetwork | Polygon | Polyline | Surface,
    ...         destination_network: EdgeNetwork):
    ...     '''Concatenate the points and edges of two edge networks.
    ...
    ...     Parameters
    ...     ----------
    ...     source_network
    ...         Open object to read points and edges from. This can be
    ...         any object with appropriately shaped points and edges.
    ...     destination_network
    ...         Edge network open for editing to add points and edges from
    ...         source network to.
    ...     '''
    ...     # Offset to add to edges to handle the new points having different
    ...     # indices in the destination network.
    ...     offset = destination_network.point_count
    ...     destination_network.append_points(source_network.points)
    ...     destination_network.append_edges(
    ...         source_network.edges + offset
    ...     )

    The return value of this function can be used to assign edge properties
    to the newly added edges:

    >>> edge_network: EdgeNetwork
    >>> # Add an edge between points 0 and 2, another edge between points
    >>> # 1 and 2 and a third between points 2 and 3.
    >>> new_edge_indices = edge_network.append_edges([0, 2], [1, 2], [2, 3])
    >>> # Colour the three new edges blue, magenta and red.
    >>> edge_network.edge_colours[new_edge_indices] = [
    ...     [0, 0, 255, 255], [255, 0, 255, 255], [255, 0, 255]]
    """
    new_edges, new_edge_mask = append_rows_to_2d_array(self.edges, *edges)
    self.edges = new_edges
    return new_edge_mask

  # If another object requires this function, it should be converted
  # to a EdgeDeletionProperties Mixin class.
  def remove_edges(self, edge_indices: int | Sequence[int] | IndexArray):
    """Remove one or more edges from the object.

    Calling this function is preferable to altering the edges array because
    this function also removes the edge properties associated with the removed
    edges (e.g. edge colours, edge visibility, etc). Additionally, if
    after the removal of edges if any point is not part of any edge it
    will be removed as well.

    This operation is performed directly on the Project and will not be undone
    if an error occurs.

    Parameters
    ----------
    edge_indices : array_like or int
      The index of the edge to remove or a list of indices of edges to
      remove.
      Indices should only contain 32-bit unsigned integer (They should be
      greater than or equal to 0 and less than 2**32).
      Any index greater than or equal to the edge count is ignored.
      Passing an index less than zero is not supported. It will not delete
      the last edge.

    Returns
    -------
    bool
      If passed a single edge index, True if the edge was removed and False if
      it was not removed.
      If passed an iterable of edge indices, True if the object supports
      removing edges and False otherwise.

    Raises
    ------
    ReadOnlyError
      If called on an object not open for editing. This error indicates an
      issue with the script and should not be caught.

    Warnings
    --------
    Any unsaved changes to the object when this function is called are
    discarded before any edges are deleted. If you wish to keep these changes,
    call save() before calling this function.
    """
    self._invalidate_edge_properties()
    if isinstance(edge_indices, int):
      remove_request = self._remove_edge(edge_indices)
    else:
      remove_request = self._remove_edges(edge_indices)
    self._reconcile_changes()
    return remove_request

  @classmethod
  def static_type(cls) -> StaticType:
    """Return the type of edge network as stored in a Project.

    This can be used for determining if the type of an object is an edge
    network.
    """
    return cls._modelling_api().EdgeNetworkType()

  def _save_topology(self):
    self._save_point_properties()
    self._save_edge_properties()
    super()._save_topology()

class Polyline(Edge):
  """An ordered sequence of points connected by edges.

  A polyline is formed from an ordered sequence of points, where edges are
  between consecutive points. For example, the first edge is from point 0
  to point 1. The second edge is from point 1 to point 2 and so on.

  This type is also known as a continuous unclosed line, edge chain or string.

  Raises
  ------
  DegenerateTopologyError
    If the Polyline contains fewer than two points when save() is called.

  See Also
  --------
  :documentation:`polyline` : Help page for this class.

  Notes
  -----
  The edges of a polyline object are implicitly defined by the points.
  The first edge is between point 0 and point 1, the second edge is
  between point 1 and point 2 and so on. Because the edges are derived
  in this way, editing the edges of a polyline is ambiguous and
  not supported. To change the edges, edit the points instead.
  If you need to edit or remove edges from a polyline, consider using
  an EdgeNetwork instead.

  Examples
  --------
  Create a c shape.

  >>> from mapteksdk.project import Project
  >>> from mapteksdk.data import Polyline
  >>> project = Project()
  >>> with project.new("cad/c_shape", Polyline) as new_line:
  >>>     new_line.points = [[1, 1, 0], [0, 1, 0], [0, 0, 0], [1, 0, 0]]

  Create a square. Note that a Polygon would be more appropriate for
  creating a square as it would not require the last point.

  >>> from mapteksdk.project import Project
  >>> from mapteksdk.data import Polyline
  >>> project = Project()
  >>> with project.new("cad/square", Polyline) as new_line:
  >>>     new_line.points = [[0, 0, 0], [1, 0, 0], [1, 1, 0],
  >>>                        [0, 1, 0], [0, 0, 0]]
  """
  def __init__(self, object_id=None, lock_type=LockType.READWRITE):
    if object_id is None:
      object_id = ObjectID(self._modelling_api().NewEdgeChain())
    super().__init__(object_id, lock_type)
    self._initialise_edge_properties(has_immutable_edges=True)

  @property
  def edges(self) -> EdgeArray:
    # Polylines and Polygons generate their edges in Python, so the __edges
    # property never contains any values.
    edges = np.arange(self.point_count, dtype=ctypes.c_uint32)
    edges = np.repeat(edges, 2)
    edges.flags.writeable = False
    return edges[1:-1].reshape(-1, 2)

  @property
  def edge_count(self) -> int:
    if self.point_count > 0:
      return self.point_count - 1
    return 0

  @classmethod
  def static_type(cls) -> StaticType:
    """Return the type of polyline as stored in a Project.

    This can be used for determining if the type of an object is a polyline.
    """
    return cls._modelling_api().EdgeChainType()

  def _save_topology(self):
    if self.point_count < 2:
      raise DegenerateTopologyError(
        "Polyline objects must contain at least two points.")
    self._save_point_properties()
    # Reconcile changes to ensure the edge arrays are the correct length.
    self._reconcile_changes()
    self._save_edge_properties()
    super()._save_topology()

class Polygon(Edge):
  """An ordered and closed sequence of points connected by edges.

  A polygon is formed from an ordered sequence of points, with edges
  between consecutive points. For example, the first edge is between
  point 0 and point 1, the second edge is between point 1 and point 2
  and the final edge is between point N - 1 and point 0 (where N is the number
  of points).
  Unlike an Polyline, a Polygon is a closed loop of edges.

  Also known as a closed line or edge loop.

  See Also
  --------
  Edge : Parent class of Polygon
  EdgeNetwork : Class which supports editing edges.
  :documentation:`polygon` : Help page for this class.

  Notes
  -----
  The edges of a polygon are implicitly defined by the points. For a polygon
  with n edges, the first edge is between points 0 and 1, the second edge is
  between points 1 and 2, and the final edge is between points n - 1 and
  0. Because the edges are derived from the points, editing
  the edges is not supported - you should edit the points instead.
  If you need to edit or remove edges without changing points
  consider using an EdgeNetwork instead.

  Raises
  ------
  DegenerateTopologyError
    If the Polygon contains fewer than three points when save() is called.

  Examples
  --------
  Create a diamond

  >>> from mapteksdk.project import Project
  >>> from mapteksdk.data import Polygon
  >>> project = Project()
  >>> with project.new("cad/polygon_diamond", Polygon) as new_diamond:
  >>>     new_diamond.points = [[1, 0, 0], [0, 1, 0], [1, 2, 0], [2, 1, 0]]
  """
  def __init__(self, object_id=None, lock_type=LockType.READWRITE):
    if object_id is None:
      object_id = ObjectID(self._modelling_api().NewEdgeLoop())
    super().__init__(object_id, lock_type)
    self._initialise_edge_properties(has_immutable_edges=True)

  @property
  def edges(self) -> EdgeArray:
    # Polylines and Polygons generate their edges in Python, so the __edges
    # property never contains any values.
    edges = np.zeros(self.point_count * 2, dtype=ctypes.c_uint32)
    temp = np.arange(1, self.point_count, dtype=ctypes.c_uint32)
    edges[1:-1] = np.repeat(temp, 2)
    edges.flags.writeable = False
    return edges.reshape(-1, 2)

  @property
  def edge_count(self) -> int:
    return self.point_count

  @classmethod
  def static_type(cls) -> StaticType:
    """Return the type of polygon as stored in a Project.

    This can be used for determining if the type of an object is a polygon.
    """
    return cls._modelling_api().EdgeLoopType()

  def _save_topology(self):
    if self.point_count < 3:
      raise DegenerateTopologyError(
        "Polygon objects must contain at least three points.")
    self._save_point_properties()
    # Reconcile changes to ensure the edge arrays are the correct length.
    self._reconcile_changes()
    self._save_edge_properties()
    super()._save_topology()
