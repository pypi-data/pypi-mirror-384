"""The base classes of topological classes in a Project."""
###############################################################################
#
# (C) Copyright 2024, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations
import ctypes
import functools
import logging
import typing

import numpy as np
from pyproj.enums import WktVersion

from .data_object import DataObject, StaticType
from .appearance import Appearance
from ..coordinate_systems import CoordinateSystem, LocalTransform
from ..errors import AlreadyAssociatedError, NonOrphanRasterError
from ..objectid import ObjectID
from ..primitive_type import PrimitiveType
from ...errors import ApplicationTooOldError
from ...geometry import Extent
from ...internal.colour_map_information import ColourMapInformation
from ...internal.util import default_type_error_message
from ...internal.lock import LockType, WriteLock
from ...internal.singular_data_property_read_only import (
  SingularDataPropertyReadOnly,)
from ...internal.singular_data_property_read_write import (
  SingularDataPropertyReadWrite,)

if typing.TYPE_CHECKING:
  from collections.abc import Callable

  from pyproj import CRS

  from ..colourmaps import ColourMap
  from ..images import Raster
  from ..primitives.attribute_key import AttributeKey
  from ...capi import SdpApi

_NO_COORDINATE_SYSTEM: typing.Literal[
  "NO_COORDINATE_SYSTEM"] = "NO_COORDINATE_SYSTEM"
"""Placeholder representing the absence of a coordinate system."""

log = logging.getLogger("mapteksdk.data")


class Topology(DataObject):
  """Base class for "geometric objects" in a Project.

  This object is best thought of as the union of the following:

    - An arrangement of topological "primitives" including their location in
      space (known as their geometry).
    - The connectivity relationships between them (known as their topology).
    - The properties applied to them.

  A given geometric object may contain any number of any of the six basic
  primitives: points, edges, facets (triangles), tetras (4 sided polyhedra),
  cells (quadrilaterals) and blocks (cubes or rectangular boxes).
  However, derived classes typically enforce constraints on the type and number
  of each primitive allowed in objects of their type. For example an edge
  chain will have points and edges but not facets.
  """
  def __init__(self, object_id: ObjectID, lock_type: LockType, *,
               rollback_on_error: bool = False):
    super().__init__(
      object_id,
      lock_type,
      rollback_on_error=rollback_on_error)
    self.__extent: SingularDataPropertyReadOnly[
        Extent] = SingularDataPropertyReadOnly(
      "extent",
      lambda: [self._lock.lock],
      self.__load_extent
    )
    self.__colour_map_information: SingularDataPropertyReadWrite[
      ColourMapInformation] = SingularDataPropertyReadWrite(
        "colour_map",
        lambda: [self._lock.lock],
        self.is_read_only,
        # The partial function allows the setter to accept an extra
        # argument compared to the getter.
        self.__get_colour_map_information,
        functools.partial(
          self.__save_colour_map_information,
          reconcile_changes=self._reconcile_changes)
        )
    self.__coordinate_system: SingularDataPropertyReadWrite[
        CoordinateSystem | typing.Literal["NO_COORDINATE_SYSTEM"]
        ] = SingularDataPropertyReadWrite(
      name="coordinate_system",
      load_parameters=lambda: [self._lock.lock],
      read_only=self.is_read_only,
      load_function=self.__load_coordinate_system,
      save_function=self.__save_coordinate_system
    )
    self.__supported_appearances: SingularDataPropertyReadOnly[
        set[Appearance]] = SingularDataPropertyReadOnly(
      name="supported appearances",
      load_parameters=lambda: [self._lock.lock],
      load_function=lambda lock: {
        Appearance.from_name(name)
        for name in self._modelling_api().SupportedFeatures(lock)
        if Appearance.from_name(name) != Appearance.UNKNOWN
      }
    )
    self.__appearance: SingularDataPropertyReadWrite[
        Appearance] = SingularDataPropertyReadWrite(
      name="appearance",
      load_parameters=lambda: [self._lock.lock],
      read_only=self.is_read_only,
      load_function=lambda lock: Appearance.from_name(
        self._modelling_api().GetDisplayedFeature(lock)),
      save_function=lambda lock, appearance: self._modelling_api(
        ).SetDisplayedFeature(lock, appearance.value))

  def close(self):
    """Closes the object and saves the changes to the Project.

    Attempting to read or edit properties of an object after closing it will
    raise a ReadOnlyError.
    """
    self._invalidate_properties()
    DataObject.close(self)

  def cancel(self):
    """Cancel any pending changes to the object.

    This undoes all changes made to the object since it was opened
    (including any changes saved by save()) and then closes the object.

    After this is called, attempting to read or edit any of the properties
    on this object (other than the id) will raise an ObjectClosedError.

    Raises
    ------
    ReadOnlyError
      If the object was open for read only (i.e not for editing).
      It is not necessary to call this for a read only object as there will be
      no pending changes.
    ObjectClosedError
      If called on a closed object.
    """
    self._raise_if_read_only("cancel changes")

    assert isinstance(self._lock, WriteLock)
    self._lock.cancel()
    self._lock.close()
    self._invalidate_properties()

  @classmethod
  def static_type(cls) -> StaticType:
    """Return the type of a topology as stored in a Project.

    This can be used for determining if the type of an object is topology.
    """
    return cls._modelling_api().TopologyType()

  def _extra_invalidate_properties(self):
    self.__colour_map_information.invalidate()
    self.__coordinate_system.invalidate()
    self.__supported_appearances.invalidate()
    self.__appearance.invalidate()
    self._invalidate_colour_map()

  def _save_topology(self):
    """Save the topology of the object.

    This should save any properties defined on the implementing
    child class. This is called during _save(), which in turn is called
    during save().
    """
    raise NotImplementedError

  # Child classes of topology should implement _save_topology()
  # instead of overwriting or overriding _save_topology().
  @typing.final
  def _save(self):
    self._save_topology()
    self.__coordinate_system.save()
    # :TRICKY: Saving the colour map information must be done after saving
    # all of the topology because it may require a call to reconcile changes,
    # which could discard unsaved changes (e.g. If the colour map was saved
    # with the primitive attributes, then for Surfaces it would result in a
    # call to reconcile changes between saving the points and facets,
    # resulting in new facets and points being discarded).
    self.__colour_map_information.save()
    self.__appearance.save()
    self._reconcile_changes()

  def _reconcile_changes(self):
    """Request reconciliation of flagged changes.

    All properties need to be re-loaded after calling.
    """
    try:
      self._modelling_api().ReconcileChanges(self._lock.lock)
    except:
      log.exception("Unexpected error when trying to save changes.")
      raise

  def _record_object_size_telemetry(self):
    raise NotImplementedError

  @property
  def supported_appearances(self) -> set[Appearance]:
    """The appearances supported by this object.

    These are the valid appearances which can be assigned to appearance.

    Notes
    -----
    This can be empty for objects opened with `Project.new()` due to a
    limitation in the applications. Call `save()` to update this.
    """
    return self.__supported_appearances.value

  @property
  def appearance(self) -> Appearance:
    """The appearance used to display the object.

    Changing this enables for the same object to be visualised in different
    ways.

    Raises
    ------
    ValueError
      If set to an appearance which is not in `supported_appearances`.
    RuntimeError
      If called on a newly created object.
    """
    return self.__appearance.value

  @appearance.setter
  def appearance(self, appearance: Appearance):
    if not isinstance(appearance, Appearance):
      raise TypeError(
        default_type_error_message("appearance", appearance, Appearance)
      )
    if len(self.supported_appearances) == 0:
      raise RuntimeError(
        "Cannot set appearance for a newly created object. "
        "Call save() to update the supported appearances set."
      )
    if appearance not in self.supported_appearances:
      raise ValueError(
        f"{appearance} appearance is not supported for {self.id.type_name}."
      )
    self.__appearance.value = appearance

  @property
  def extent(self) -> Extent:
    """The axes aligned bounding extent of the object."""
    return self.__extent.value

  def get_colour_map(self) -> ObjectID[ColourMap]:
    """Return the ID of the colour map object associated with this object.

    Returns
    -------
    ObjectID
      The ID of the colour map object or null object ID if there is
      no colour map.
    """
    return self.__colour_map_information.value.colour_map_id

  def remove_colour_map(self):
    """Remove the colour map associated with this object."""
    self.__colour_map_information.value = ColourMapInformation.no_colour_map(
      PrimitiveType.POINT,
      deleted=True
    )
    # This does not query the existing colour map, so cannot include whether
    # a numeric or solid colour map was removed.
    self._record_function_call_telemetry(
      "remove_colour_map",
      "Topology"
    )

  def apply_random_tint(self):
    """Applies a random tint to the object.

    This sets a random colour to the point or block colours.

    Notes
    -----
    This includes an implicit call to save().
    """
    # This uses the C API rather than generating a random colour in Python
    # because it will correctly apply random tints to objects which do not
    # have colour arrays in Python (e.g. Text2D, Marker, Discontinuity,
    # Ribbons etc).
    self._raise_if_read_only("Apply random tint")


    # Save the changes so that any newly added primitives are coloured.
    self.save()
    if hasattr(self, "block_count"):
      # Colour scheme 4 is "Random Tint".
      self._sdp_api().ApplyBlockColourScheme(self._lock.lock, 4, "")
    else:
      self._sdp_api().ApplyPointColourScheme(self._lock.lock, 4, "")
    # The C++ code will write the colours to the RW array.
    # Python reads colours from the R arrays, so a call to reconcile changes
    # is required to make the new colours visible in Python.
    self._reconcile_changes()

  def _set_colour_map(
      self,
      attribute_key: AttributeKey,
      primitive_type: PrimitiveType,
      colour_map: ObjectID[ColourMap]):
    """Set the colour map for this object.

    This allows for derived classes and PrimitiveAttributes to set the
    colour map information.

    Parameters
    ----------
    attribute_name
      The name of the attribute to associate to the colour map.
    primitive_type
      The type of primitive the attribute has values for.
    colour_map
      The ObjectID of the colour map to use to colour by the attribute.

    Warnings
    --------
    This performs no safety checks. The caller is expected to perform
    such checks.
    """
    map_information =  ColourMapInformation.from_attribute_key(
      attribute_key,
      primitive_type,
      colour_map
    )
    self.__colour_map_information.value = map_information

  def _colour_map_information(self) -> ColourMapInformation:
    """Get the colour map information for this object.

    This allows for derived classes and PrimitiveAttributes to access the
    colour map information.

    Returns
    -------
    ColourMapInformation
      A named tuple containing the colour map information for this object.
      This will contain a null Object ID if there is no colour map
      associated with the object.
    """
    return self.__colour_map_information.value

  def _invalidate_colour_map(self):
    """Invalidates the colour map.

    It is loaded from the Project the next time it is accessed.
    """
    self.__colour_map_information.invalidate()

  def _associate_raster(self, raster_id: ObjectID[Raster], desired_index: int):
    """Associate a raster with this object.

    This should not be called directly.

    Parameters
    ----------
    raster_id
      Object ID of the raster to associate.
    desired_index
      The index to associate the raster at.

    Raises
    ------
    RuntimeError
      If the raster could not be associated with the object.
    TypeError
      If raster_id is not the ObjectID of a raster.
    AlreadyAssociatedError
      If the raster is already associated with an object.
    NonOrphanRasterError
      If the raster is not an orphan.
    """
    if not raster_id.is_a(self._modelling_api().ImageType()):
      raise TypeError(f"Cannot associate Raster of type {raster_id.type_name} "
                     "because it is not a Raster.")
    desired_index = int(desired_index)
    if desired_index < 1 or desired_index > 255:
      message = (f"Invalid raster index ({desired_index}). Raster index must "
                 "be greater than 0 and less than 255.")
      raise ValueError(message)
    if raster_id in self.rasters.values():
      message = (
        "The Raster is already associated with this Surface. To edit "
        "the registration information, edit the registration property "
        "of the Raster directly. To change the raster index, the "
        "raster must be dissociated via dissociate_raster() "
        "before calling this function.")
      raise AlreadyAssociatedError(message)
    if not raster_id.is_orphan:
      # :TRICKY: 2021-09-27 SDK-542. AssociateRaster will
      # make a clone of the Raster if it is not an orphan. This won't clone
      # the registration information, resulting in the clone being
      # associated with the Surface with no registration information.
      # Raise an error to avoid this.
      # Note that if a Raster is created with a path in project.new
      # then it is an orphan until the object is closed and no error will
      # be raised.
      parent_id = raster_id.parent
      # Use the C API functions to avoid a circular dependency with
      # containers.py.
      if parent_id.is_a((
          self._modelling_api().VisualContainerType(),
          self._modelling_api().StandardContainerType())):
        raise NonOrphanRasterError(
          "Cannot associate a raster with a Project path. "
          "Call Project.copy_object() with a destination path of None and "
          "associate the copy instead.")
      raise AlreadyAssociatedError(
        "Cannot associate Raster because it is already associated with the "
        f"{parent_id.type_name} with path: '{parent_id.path}'. "
        "To associate the Raster with this object, first dissociate it from "
        "the other object and close the other object before calling this "
        "function. Alternatively create a copy by calling "
        "Project.copy_object() with a destination path of None.")
    result = self._modelling_api().AssociateRaster(self._lock.lock,
                                         raster_id.handle,
                                         desired_index)
    result = result.value
    if result == 0:
      raise RuntimeError("Failed to associate raster.")
    return result

  @property
  def rasters(self) -> dict[int, ObjectID[Raster]]:
    """The raster associated with this object.

    This is a dictionary of raster indices and Object IDs of the raster images
    currently associated with this object.

    The keys are the raster ids and the values are the Object IDs of the
    associated rasters. Note that all raster ids are integers however they
    may not be consecutive - for example, an object may have raster ids
    0, 1, 5 and 200.

    Notes
    -----
    Rasters with higher indices appear on top of rasters with lower indices.
    The maximum possible raster id is 255.

    Removing a raster from this dictionary will not remove the raster
    association from the object. Use dissociate_raster to do this.

    Examples
    --------
    Iterate over all rasters on an object and invert the colours. Note
    that this will fail if there is no object at the path "target" and
    it will do nothing if no rasters are associated with the target.

    >>> from mapteksdk.project import Project
    >>> project = Project()
    >>> with project.read("target") as read_object:
    ...     for raster in read_object.rasters.values():
    ...         with project.edit(raster) as edit_raster:
    ...             edit_raster.pixels[:, :3] = 255 - edit_raster.pixels[:, :3]
    """
    rasters = self._modelling_api().GetAssociatedRasters(self._lock.lock)
    final_rasters: dict[int, ObjectID[Raster]] = {}
    for key, value in rasters.items():
      final_rasters[key] = ObjectID(value)
    return final_rasters

  def dissociate_raster(self, raster: Raster | ObjectID[Raster]):
    """Removes the raster from the object.

    If an error occurs after dissociating a raster resulting in save()
    not being called, the dissociation of the raster can only be undone if
    the application's API version is 1.6 or greater.

    Prior to mapteksdk 1.6:
    Dissociating a raster will not be undone if an error occurs.

    Parameters
    ----------
    raster
      The raster to dissociate.

    Returns
    -------
    bool
      True if the raster was successfully dissociated from the object,
      False if the raster was not associated with the object.

    Raises
    ------
    TypeError
      If raster is not a Raster.
    ReadOnlyError
      If this object is open for read-only.

    Notes
    -----
    This only removes the association between the Raster and the object,
    it does not clear the registration information from the Raster.

    Examples
    --------
    Dissociate the first raster found on a picked object.

    >>> from mapteksdk.project import Project
    >>> from mapteksdk import operations
    >>> project = Project()
    >>> oid = operations.object_pick(
    ...     support_label="Pick an object to remove a raster from.")
    ... with project.edit(oid) as data_object:
    ...     report = f"There were no raster to remove from {oid.path}"
    ...     for index in data_object.rasters:
    ...         data_object.dissociate_raster(data_object.rasters[index])
    ...         report = f"Removed raster {index} from {oid.path}"
    ...         break
    ... # Now that the raster is dissociated and the object is closed,
    ... # the raster can be associated with a different object.
    ... operations.write_report("Remove Raster", report)
    """
    self._raise_if_read_only("dissociate raster")

    # :TODO: 2021-04-16 SDK-471: It might be useful to cache this information
    # and do it during save.
    if not isinstance(raster, ObjectID):
      try:
        raster = raster.id
      except AttributeError as error:
        raise TypeError("raster must be a ObjectID or DataObject, "
                        f"not '{raster}' of type {type(raster)}.") from error

    # :NOTE: 2021-04-16 We can't call Raster.static_type() because importing
    # images.py into this file would result in a circular dependency.
    if not raster.is_a(self._modelling_api().ImageType()):
      raise TypeError('raster must be an object of type Raster.')

    return self._modelling_api().DissociateRaster(
      self._lock.lock, raster.handle)

  @property
  def coordinate_system(self) -> CoordinateSystem | None:
    """The coordinate system the points of this object are in.

    If the object has no coordinate system, this will be None.

    Raises
    ------
    ReadOnlyError
      If set on an object open for read-only.

    Warning
    -------
    Setting this property does not change the points.
    This is only a label stating the coordinate system the points are in.

    Examples
    --------
    Creating an edge network and setting the coordinate system to be
    WGS84. Note that setting the coordinate system does not change the points.
    It is only stating which coordinate system the points are in.

    >>> from pyproj import CRS
    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import Polygon
    >>> project = Project()
    >>> with project.new("cad/rectangle", Polygon) as new_edges:
    ...     # Coordinates are in the form [longitude, latitude]
    ...     new_edges.points = [[112, 9], [112, 44], [154, 44], [154, 9]]
    ...     new_edges.coordinate_system = CRS.from_epsg(4326)

    Often a standard map projection is not convenient or accurate for
    a given application. In such cases a local transform can be provided
    to allow coordinates to be specified in a more convenient system.
    The below example defines a local transform where the origin is
    translated 1.2 degrees north and 2.1 degree east, points are scaled to be
    twice as far from the horizontal origin and the coordinates are rotated
    45 degrees clockwise about the horizontal_origin. Note that the points
    of the polygon are specified in the coordinate system after the local
    transform has been applied.

    >>> import math
    >>> from pyproj import CRS
    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import Polygon, CoordinateSystem, LocalTransform
    >>> project = Project()
    >>> transform = LocalTransform(
    ...     horizontal_origin = [1.2, 2.1],
    ...     horizontal_scale_factor = 2,
    ...     horizontal_rotation = math.pi / 4)
    >>> system = CoordinateSystem(CRS.from_epsg(20249), transform)
    >>> with project.new("cad/rectangle_transform", Polygon) as new_edges:
    ...     new_edges.points = [[112, 9], [112, 44], [154, 44], [154, 9]]
    ...     new_edges.coordinate_system = system

    See Also
    --------
    mapteksdk.data.coordinate_systems.CoordinateSystem : Allows for a
      coordinate system to be defined with an optional local transform.
    """
    # This returns None for no coordinate system for backwards
    # compatibility.
    if self.__coordinate_system.value == _NO_COORDINATE_SYSTEM:
      return None
    return self.__coordinate_system.value

  @coordinate_system.setter
  def coordinate_system(self, value: CoordinateSystem | CRS | None):
    if value is None:
      # This handles the case where a user does:
      # left_object.coordinate_system = right_object.coordinate_system
      # when right_object doesn't have a coordinate system.
      self.remove_coordinate_system()
      return

    if not isinstance(value, CoordinateSystem):
      value = CoordinateSystem(value)
    self.__coordinate_system.value = value

  def remove_coordinate_system(self):
    """Remove the coordinate system from the object.

    This does not change the geometry of the object. It only clears
    the label which states what coordinate system the object is in.

    This has no effect if the object does not have a coordinate system.
    """
    self._raise_if_read_only("Remove coordinate system.")
    self.__coordinate_system.value = _NO_COORDINATE_SYSTEM

  def _sdp_api(self) -> SdpApi:
    """Access the Spatial Data Processing C API."""
    return self._application_api().sdp

  def __get_colour_map_information(self, lock) -> ColourMapInformation:
    """Get the colour map information for an object.

    Parameters
    ----------
    lock
      Lock on the object to get the colour map information for.

    Returns
    -------
    ColourMapInformation
      The colour map information for this object.
      If there is no colour map associated with this object,
      this will contain a null ObjectID.
    """
    read_type = self._modelling_api().GetDisplayedAttributeType(lock)

    try:
      actual_type = PrimitiveType(read_type)
    except ValueError:
      return ColourMapInformation.no_colour_map(
        PrimitiveType.POINT)

    length = self._modelling_api().GetDisplayedAttribute(
      lock,
      None,
      0)
    str_buffer = ctypes.create_string_buffer(length)
    self._modelling_api().GetDisplayedAttribute(
      lock,
      str_buffer,
      length)

    name = str_buffer.value.decode("utf-8")

    if not name:
      return ColourMapInformation.no_colour_map(actual_type)

    colour_map_handle = self._modelling_api().GetDisplayedColourMap(lock)
    colour_map_id = ObjectID(colour_map_handle)

    return ColourMapInformation.from_name(
      name, actual_type, colour_map_id
    )

  def __save_colour_map_information(
      self,
      lock,
      colour_map_info: ColourMapInformation,
      reconcile_changes: Callable[[], None]):
    """Save the colour map information for an object.

    This does nothing if the colour map information contains a null
    object ID.

    This includes an implicit call to _reconcile_changes() to ensure
    the colour map is saved correctly.

    Parameters
    ----------
    lock
      Lock on the object to save the colour map for.
    colour_map_info
      Colour map information to save for this object.
    """
    if colour_map_info.deleted:
      self._modelling_api().RemoveColourMap(self._lock.lock)
      return
    if not colour_map_info.colour_map_id:
      # There is no colour map information to save.
      return
    if not colour_map_info.attribute_key:
      # The AttributeKey was never looked up, so it must not have been edited.
      return
    # If you set the colour map and colours at the same time, the
    # colour map is not set. To avoid this, reconcile changes before
    # saving the colour map.
    reconcile_changes()

    save_functions = {
      PrimitiveType.POINT : self._modelling_api().SetDisplayedPointAttribute,
      PrimitiveType.EDGE : self._modelling_api().SetDisplayedEdgeAttribute,
      PrimitiveType.FACET : self._modelling_api().SetDisplayedFacetAttribute,
      PrimitiveType.BLOCK : self._modelling_api().SetDisplayedBlockAttribute,
      PrimitiveType.CELL : self._modelling_api().SetDisplayedBlockAttribute
    }

    save_function = save_functions[colour_map_info.primitive_type]
    save_function(
      lock,
      colour_map_info.attribute_key.to_json().encode("utf-8"),
      colour_map_info.colour_map_id.handle
    )

  def __load_extent(self, lock) -> Extent:
    """Load the extent of the object from the Project.

    Parameters
    ----------
    lock
      Lock on the object to load the extent of.

    Returns
    -------
    Extent
      The Extent of the object.
    """
    extents = (ctypes.c_double * 6)()
    self._modelling_api().ReadExtent(lock, extents)
    return Extent(
      minimum=(extents[0], extents[1], extents[2]),
      maximum=(extents[3], extents[4], extents[5]))

  def __load_coordinate_system(self, lock
      ) -> CoordinateSystem | typing.Literal["NO_COORDINATE_SYSTEM"]:
    """Load the coordinate system information from the application.

    Returns
    -------
    CoordinateSystem
      The coordinate system information for this object.
    """
    wkt, c_local_transform = self._modelling_api().GetCoordinateSystem(lock)
    if wkt != "":
      local_transform = np.empty((11,), dtype=ctypes.c_double)
      local_transform[:] = c_local_transform
      return CoordinateSystem(wkt, LocalTransform(local_transform))
    return _NO_COORDINATE_SYSTEM

  def __save_coordinate_system(
      self,
      lock,
      coordinate_system: CoordinateSystem | typing.Literal[
        "NO_COORDINATE_SYSTEM"]):
    """Save the coordinate system information to the application.

    Parameters
    ----------
    lock
      Lock on the object to save the coordinate system information.
    coordinate_system
      The coordinate system to save for the object.
      If this is NO_COORDINATE_SYSTEM, this clears the coordinate system.
    """
    if coordinate_system == _NO_COORDINATE_SYSTEM:
      try:
        self._modelling_api().ClearCoordinateSystem(lock)
      except (ApplicationTooOldError, AttributeError):
        # Clear coordinate system is not supported by the C API.
        # If this object currently doesn't have a coordinate system,
        # suppress the error - the object is in the correct state.
        # This case will be hit if the script reads that there is no
        # coordinate system but doesn't set a coordinate system.
        if self.__load_coordinate_system(lock) != _NO_COORDINATE_SYSTEM:
          raise
      return
    wkt_string = coordinate_system.crs.to_wkt(WktVersion.WKT2_2019)
    local_transform = coordinate_system.local_transform.to_numpy()

    self._modelling_api().SetCoordinateSystem(lock,
                                    wkt_string,
                                    local_transform)
