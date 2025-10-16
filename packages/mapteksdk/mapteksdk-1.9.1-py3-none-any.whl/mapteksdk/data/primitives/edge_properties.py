"""Support for edge primitives.

An edge is a line between two points. In Python, an edge is represented
as a numpy array containing two integers representing the indices of the
points the edge connects. For example, the edge [0, 1] indicates the line
between the 0th and 1st point. Because edges are defined based on points, all
objects which inherit from EdgeProperties must also inherit from
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
from ..errors import DegenerateTopologyError
from ...internal.data_property import DataProperty, DataPropertyConfiguration

if typing.TYPE_CHECKING:
  from collections.abc import Sequence

  import numpy.typing as npt

  from ...capi import ModellingApi
  from ...common.typing import EdgeArray, BooleanArray, ColourArray, IndexArray
  from ...internal.lock import ReadLock, WriteLock

log = logging.getLogger("mapteksdk.data")

# The following warning can be enabled if the <Primitive>Properties classes
# ended in Mixin as then pylint expects that the members are defined elsewhere.
# pylint: disable=no-member

class EdgeProperties:
  """Mixin class which provides spatial objects support for edge primitives.

  The edge [i, j] indicates the line is between the points Object.points[i]
  and Object.points[j].

  Functions and properties defined on this class are available on all
  classes which support edges.

  Notes
  -----
  Currently all objects which inherit from EdgeProperties also inherit
  from PointProperties to allow using the points from point properties
  to define the edges.
  """
  __edges: DataProperty
  __edge_colours: DataProperty
  __edge_selection: DataProperty
  __edge_attributes: PrimitiveAttributes | None

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

  def _initialise_edge_properties(self, has_immutable_edges: bool):
    """Initialises the edge properties.

    This must be called during the __init__ function of child classes.

    Parameters
    ----------
    has_immutable_edges
      If True, the edges of this object are derived from another primitive and
      cannot be edited.
      If False, the edges of this object can be edited if the object is open
      for editing.
    """
    self.__edges = DataProperty(
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
        immutable=has_immutable_edges,
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode
      )
    )

    self.__edge_colours = DataProperty(
      lock=self._lock,
      configuration=DataPropertyConfiguration(
        name="edge_colours",
        dtype=ctypes.c_uint8,
        default=np.array([0, 220, 0, 255], dtype=ctypes.c_uint8),
        column_count=4,
        primitive_count_function=self._modelling_api().ReadEdgeCount,
        cached_primitive_count_function=lambda: self.edge_count,
        load_function=self._modelling_api().EdgeColourBeginR,
        save_function=self._modelling_api().EdgeColourBeginRW,
        is_colour_property=True,
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode
      )
    )

    self.__edge_selection = DataProperty(
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
    )
    self.__edge_attributes = None

  @property
  def edges(self) -> EdgeArray:
    """A 2D Numpy array of edges of the form:
    [[i0, j0], [i1, j1], ..., [iN, jN]]
    where N is the number of edges and all iK and jK are valid indices
    in Object.points.

    Warnings
    --------
    For Surfaces the edges are derived from the points and facets. If any
    changes are made to the points or facets, the corresponding changes
    to the edges will not be made until save() has been called.

    Notes
    -----
    Invalid edges are removed during save().
    """
    return self.__edges.values

  def _set_edges(self, edges: npt.ArrayLike):
    """Private setter function for edges.

    Most objects implicitly define the edges based on other primitives so by
    default the setter for edges is not available.
    """
    if self.__edges.configuration.immutable:
      raise ValueError("This object does not support setting edges.")
    self.__edges.values = edges

  @property
  def edge_colours(self) -> ColourArray:
    """The colours of the edges.

    The edge colours are represented as a numpy array of RGBA colours,
    with one colour for each edge.
    """
    return self.__edge_colours.values

  @edge_colours.setter
  def edge_colours(self, edge_colours: npt.ArrayLike):
    self.__edge_colours.values = edge_colours

  @property
  def edge_selection(self) -> BooleanArray:
    """A 1D ndarray representing which edges are selected.

    edge_selection[i] = True indicates edge i is selected.
    """
    return self.__edge_selection.values

  @edge_selection.setter
  def edge_selection(self, edge_selection: npt.ArrayLike):
    self.__edge_selection.values = edge_selection

  @property
  def edge_count(self) -> int:
    """The count of edges in the object."""
    # If the edges have not been loaded or set, get the edge
    # count from the DataEngine. Otherwise derive it.
    if not self.__edges.are_values_cached:
      return self._modelling_api().ReadEdgeCount(self._lock.lock)
    return self.edges.shape[0]

  def _invalidate_edge_properties(self):
    """Invalidates the cached edge properties.

    The next time an edge property is accessed, its values will be loaded from
    the project.
    """
    self.__edges.invalidate()
    self.__edge_colours.invalidate()
    self.__edge_selection.invalidate()
    self.__edge_attributes = None

  def _save_edge_properties(self):
    """Save the edge properties.

    This must be called during save() of the inheriting object.
    This should never be called directly. To save an object, call save()
    instead.

    Raises
    ------
    CannotSaveInReadOnlyModeError
      If in read-only mode.

    Notes
    -----
    Generally this should be called after PointProperties.save_points().
    """
    self._raise_if_save_in_read_only()
    # Write all relevant properties for this primitive type.
    if not self.__edges.read_only:
      if self.edge_count == 0:
        message = "Object must contain at least one edge."
        raise DegenerateTopologyError(message)
      self.__edges.save()

    self.__edge_colours.save()

    self.__edge_selection.save()

    if self.__edge_attributes is not None:
      self.__edge_attributes.save_attributes()

  @property
  def edge_attributes(self) -> PrimitiveAttributes:
    """Access to custom edge attributes.

    These are arrays of values of the same type, with one value for each edge.

    Use Object.edge_attributes[attribute_name] to access the edge attribute
    called attribute_name. See PrimitiveAttributes for valid operations
    on edge attributes.

    Returns
    -------
    PrimitiveAttributes
      Access to the edge attributes.

    Raises
    ------
    ValueError
      If the type of the attribute is not supported.

    Warnings
    --------
    For Surfaces if you have changed the points or facets in the object,
    you must call save() before accessing the edge attributes.
    """
    if self.__edge_attributes is None:
      self.__edge_attributes = PrimitiveAttributes(
        PrimitiveType.EDGE,
        # EdgeProperties requires that the inheriting class is Topology
        # so that self can be passed here.
        self # type: ignore
      )
    return self.__edge_attributes

  def save_edge_attribute(
      self, attribute_name: str | AttributeKey, data: npt.ArrayLike):
    """Create and/or edit the values of the edge attribute attribute_name.

    This is equivalent to Object.edge_attributes[attribute_name] = data

    Saving an edge attribute using an AttributeKey allows for additional
    metadata to be specified.

    Parameters
    ----------
    attribute_name
      The name or key of the attribute.
    data
      An array_like of a base type data to store for the attribute
      per-primitive.

    Raises
    ------
    ValueError
      If the type of the attribute is not supported.
    AmbiguousNameError
      If there is already an attribute with the same name, but with different
      metadata.
    """
    self.edge_attributes[attribute_name] = data

  def delete_edge_attribute(self, attribute_name: str | AttributeKey):
    """Delete an edge attribute.

    Parameters
    ----------
    attribute_name
      The name or key of the attribute.
    """
    self.edge_attributes.delete_attribute(attribute_name)

  def _remove_edge(self, edge_index: int):
    """Remove edge at given index of edges array

    Parameters
    ----------
    edge_index
      index of edge to remove

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
    self._raise_if_read_only("remove edge")
    return self._modelling_api().RemoveEdge(self._lock.lock, edge_index)

  def _remove_edges(self, edge_indices: IndexArray | Sequence[int]):
    """Remove list of edges at given indices of edges array.

    Parameters
    ----------
    edge_indices
      1D array of uint32 indices of edges to remove

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
    self._raise_if_read_only("remove edge")
    index_count = len(edge_indices)
    array = (ctypes.c_uint32 * index_count)(*edge_indices)
    return self._modelling_api().RemoveEdges(self._lock.lock,
                                   array,
                                   index_count)

  def _record_edge_telemetry(self):
    """Add size telemetry for edges to telemetry."""
    self._record_size_for("Edges", self.edge_count)

    edge_attributes = self.__edge_attributes
    if edge_attributes is not None:
      # pylint: disable=protected-access
      edge_attributes._record_telemetry()
