"""Support for facet primitives.

A facet is a triangle defined by three points. In Python, a facet is
represented as a numpy array containing three integers representing the
indices of the points which make up the three corners of the triangle.
For example, the facet [0, 1, 2] indicates the triangle defined by the
0th, 1st and 2nd points. Because facets are defined based on points, all
objects which inherit from FacetProperties must also inherit from
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
from ...internal.util import append_rows_to_2d_array

if typing.TYPE_CHECKING:
  import numpy.typing as npt

  from ...capi import ModellingApi
  from ...common.typing import FacetArray, BooleanArray, ColourArray, IndexArray
  from ...internal.lock import ReadLock, WriteLock

log = logging.getLogger("mapteksdk.data")

# The following warning can be enabled if the <Primitive>Properties classes
# ended in Mixin as then pylint expects that the members are defined elsewhere.
# pylint: disable=no-member

class FacetProperties:
  """Mixin class which provides spatial objects support for facet primitives.

  A facet is a triangle drawn between three points. For example, the
  facet [i, j, k] is the triangle drawn between object.points[i],
  object.points[j] and object.points[k].

  Functions and properties defined on this class are available on all
  classes which support facets.
  """
  __facets: DataProperty
  __facet_colours: DataProperty
  __facet_selection: DataProperty
  __facet_attributes: PrimitiveAttributes | None

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

  def _initialise_facet_properties(self):
    """Initialises the facet properties.

    This must be called during the __init__ function of child classes.
    """
    self.__facets = DataProperty(
      lock=self._lock,
      configuration=DataPropertyConfiguration(
        name="facets",
        dtype=ctypes.c_int32,
        default=0,
        column_count=3,
        primitive_count_function=self._modelling_api().ReadFacetCount,
        load_function=self._modelling_api().FacetToPointIndexBeginR,
        save_function=self._modelling_api().FacetToPointIndexBeginRW,
        cached_primitive_count_function=None,
        set_primitive_count_function=self._modelling_api().SetFacetCount,
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode
      )
    )

    self.__facet_colours = DataProperty(
      lock=self._lock,
      configuration=DataPropertyConfiguration(
        name="facet_colours",
        dtype=ctypes.c_uint8,
        default=np.array([0, 220, 0, 255], dtype=ctypes.c_uint8),
        column_count=4,
        primitive_count_function=self._modelling_api().ReadFacetCount,
        cached_primitive_count_function=lambda: self.facet_count,
        load_function=self._modelling_api().FacetColourBeginR,
        save_function=self._modelling_api().FacetColourBeginRW,
        is_colour_property=True,
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode
      )
    )

    self.__facet_selection = DataProperty(
      lock=self._lock,
      configuration=DataPropertyConfiguration(
        name="facet_selection",
        dtype=ctypes.c_bool,
        default=False,
        column_count=1,
        primitive_count_function=self._modelling_api().ReadFacetCount,
        cached_primitive_count_function=lambda: self.facet_count,
        load_function=self._modelling_api().FacetSelectionBeginR,
        save_function=self._modelling_api().FacetSelectionBeginRW,
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode
      )
    )

    self.__facet_attributes = None

  @property
  def facets(self) -> FacetArray:
    """A 2D numpy array of facets in the object.

    This is of the form: [[i0, j0, k0], [i1, j1, k1], ..., [iN, jN, kN]] where
    N is the number of facets. Each i, j and k value is the index of the point
    in Objects.points for the point used to define the facet.
    """
    return self.__facets.values

  @facets.setter
  def facets(self, facets: npt.ArrayLike):
    self.__facets.values = facets

  def append_facets(self, *facets) -> BooleanArray:
    """Append new facets to the end of the facets array.

    Using this function is preferable to assigning to the facets array
    directly because it allows facets to be added to the object without
    any risk of changing existing facets by accident. The return value
    can also be used to assign facet properties for the new facets.

    Parameters
    ----------
    facets
      New facets to append to the array.

    Returns
    -------
    BooleanArray
      Boolean array which can be used to assign properties for the newly
      added facets.

    Examples
    --------
    This function can be used to add a single facet to an object:

    >>> surface: Surface
    >>> # Add a facet connecting points 0, 1 and 2.
    >>> surface.append_facets([0, 1, 2])

    Passing multiple facets can be used to append multiple facets at once:

    >>> surface: Surface
    >>> # Add a facet between points 0, 1 and 2 and another between points
    >>> # 1 and 2 and 3.
    >>> surface.append_facets([0, 1, 2], [1, 2, 3])

    This function also accepts iterables of facets, so the following is
    functionally identical to the previous example:

    >>> surface: Surface
    >>> # Add a facet between points 0, 1 and 2 and another between points
    >>> # 1 and 2 and 3.
    >>> surface.append_facets([[0, 1, 2], [1, 2, 3]])

    The return value of this function can be used to assign facet properties
    to the newly added facets:

    >>> surface: Surface
    >>> new_facet_indices = surface.append_facets([0, 1, 2], [1, 2, 3])
    >>> # Colour the two new facets blue and magenta.
    >>> surface.facet_colours[new_facet_indices] = [
    ...     [0, 0, 255, 255], [255, 0, 255, 255]]
    """
    new_facets, new_facet_mask = append_rows_to_2d_array(self.facets, *facets)
    self.facets = new_facets
    return new_facet_mask

  @property
  def facet_colours(self) -> ColourArray:
    """A 2D numpy array containing the colours of the facets."""
    return self.__facet_colours.values

  @facet_colours.setter
  def facet_colours(self, facet_colours: npt.ArrayLike):
    self.__facet_colours.values = facet_colours

  @property
  def facet_selection(self) -> BooleanArray:
    """A 1D numpy array representing which facets are selected.

    If object.facet_selection[i] = True then the ith facet
    is selected.
    """
    return self.__facet_selection.values

  @facet_selection.setter
  def facet_selection(self, facet_selection: npt.ArrayLike):
    self.__facet_selection.values = facet_selection

  @property
  def facet_count(self) -> int:
    """The number of facets in the object."""
    if not self.__facets.are_values_cached:
      return self._modelling_api().ReadFacetCount(self._lock.lock)
    return self.facets.shape[0]

  def _invalidate_facet_properties(self):
    """Invalidates the cached facet properties.

    The next time a facet property is accessed, its values will be loaded from
    the project.
    """
    self.__facets.invalidate()
    self.__facet_colours.invalidate()
    self.__facet_selection.invalidate()
    self.__facet_attributes = None

  # If another class is added which needs this function it should be
  # converted into a FacetDeletionProperties mixin class.
  def remove_facets(self, facet_indices: npt.ArrayLike) -> bool:
    """Remove one or more facets from the object.

    Calling this function is preferable to altering the facets array because
    this function also removes the facet properties associated with the removed
    facets (e.g. facet colours, facet visibility, etc). Additionally,
    after the removal any points or edges which are not part of a facet
    will be removed from the object.

    This operation is performed directly on the Project and will not be undone
    if an error occurs.

    Parameters
    ----------
    facet_indices
      The index of the facet to remove or a list of indices of facets to
      remove.
      Indices should only contain 32-bit unsigned integer (They should be
      greater than or equal to 0 and less than 2**32).
      Any index greater than or equal to the facet count is ignored.
      Passing an index less than zero is not supported. It will not delete
      the last facet.

    Returns
    -------
    bool
      If passed a single facet index, True if the facet was removed
      and False if it was not removed.
      If passed an iterable of facet indices, True if the object supports
      removing facets and False otherwise.

    Raises
    ------
    ReadOnlyError
      If called on an object not open for editing. This error indicates an
      issue with the script and should not be caught.

    Warnings
    --------
    Any unsaved changes to the object when this function is called are
    discarded before any facets are deleted. If you wish to keep these changes,
    call save() before calling this function.
    """
    self._invalidate_facet_properties()
    if isinstance(facet_indices, int):
      result = self._remove_facet(facet_indices)
    else:
      if not isinstance(facet_indices, np.ndarray):
        facet_indices = np.array(facet_indices, dtype=np.uint32)
      result = self._remove_facets(facet_indices)
    self._reconcile_changes()
    return result

  def _save_facet_properties(self):
    """Save the facet properties.

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
    # Write all relevant properties for this primitive type
    if self.facet_count == 0:
      message = "Object must contain at least one facet"
      raise DegenerateTopologyError(message)

    self.__facets.save()
    self.__facet_colours.save()
    self.__facet_selection.save()

    if self.__facet_attributes is not None:
      self.__facet_attributes.save_attributes()

  @property
  def facet_attributes(self) -> PrimitiveAttributes:
    """Access the custom facet attributes.

    These are arrays of values of the same type, with one value for each facet.

    Use Object.facet_attributes[attribute_name] to access a facet attribute
    called attribute_name. See PrimitiveAttributes for valid operations
    on facet attributes.

    Returns
    -------
    PrimitiveAttributes
      Access to the facet attributes.

    Raises
    ------
    ValueError
      If the type of the attribute is not supported.
    """
    if self.__facet_attributes is None:
      self.__facet_attributes = PrimitiveAttributes(
        PrimitiveType.FACET,
        # FacetProperties requires that the inheriting class is Topology
        # so that self can be passed here.
        self # type: ignore
      )
    return self.__facet_attributes

  def save_facet_attribute(
      self,
      attribute_name: str | AttributeKey,
      data: npt.ArrayLike):
    """Create new and/or edit the values of the facet attribute attribute_name.

    This is equivalent to Object.facet_attributes[attribute_name] = data.

    Saving a facet attribute using an AttributeKey allows for additional
    metadata to be specified.

    Parameters
    ----------
    attribute_name
      The name or key of the attribute.
    data
      Data for the associated attribute. This should be a ndarray of shape
      (facet_count,). The ith entry in this array is the value of this
      primitive attribute for the ith facet.

    Raises
    ------
    ValueError
      If the type of the attribute is not supported.
    AmbiguousNameError
      If there is already an attribute with the same name, but with different
      metadata.
    """
    self.facet_attributes[attribute_name] = data

  def delete_facet_attribute(self, attribute_name: str | AttributeKey):
    """Delete a facet attribute.

    This is equivalent to: facet_attributes.delete_attribute(attribute_name)

    Parameters
    ----------
    attribute_name
      The name or key of the attribute.
    """
    self.facet_attributes.delete_attribute(attribute_name)

  def _remove_facet(self, facet_index: int):
    """Remove facet at given index of facet array.

    Parameters
    ----------
    facet_index
      Index of facet to remove.

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
    self._raise_if_read_only("remove facet")
    return self._modelling_api().RemoveFacet(self._lock.lock,
                                   facet_index)

  def _remove_facets(
      self, facet_indices: IndexArray):
    """Remove list of facets at given indices of facets array.

    Parameters
    ----------
    facet_indices
      1D array of uint32 indices of facets to remove.

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
    self._raise_if_read_only("remove facets")
    index_count = len(facet_indices)
    array = (ctypes.c_uint32 * index_count)(*facet_indices)
    return self._modelling_api().RemoveFacets(
      self._lock.lock, array, index_count)

  def _record_facet_telemetry(self):
    """Add size telemetry for facets to telemetry."""
    self._record_size_for("Facets", self.facet_count)

    facet_attributes = self.__facet_attributes
    if facet_attributes is not None:
      # pylint: disable=protected-access
      facet_attributes._record_telemetry()
