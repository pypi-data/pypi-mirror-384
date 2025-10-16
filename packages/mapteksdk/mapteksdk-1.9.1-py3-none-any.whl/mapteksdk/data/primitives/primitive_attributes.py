"""Access to primitive attributes.

Unlike object attributes, which have one value for the entire object,
primitive attributes have one value for each primitive of a particular type.
For example, a point primitive attribute has one value for each point and
a block primitive attribute has one value for each block.

Users of the SDK should never need to construct these objects directly.
Instead, they should be accessed via the point_attributes, edge_attributes,
facet_attributes, cell_attributes and block_attributes properties.
"""
###############################################################################
#
# (C) Copyright 2020, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

from collections.abc import MutableMapping, Sequence
import ctypes
from functools import partial
import logging
import typing

import numpy as np

from .attribute_key import AttributeKey
from .colour_scheme import ColourScheme
from ..colourmaps import NumericColourMap, StringColourMap
from ..errors import AmbiguousNameError
from ..objectid import ObjectID
from ..primitive_type import PrimitiveType
from ...capi.types import T_ReadHandle, T_EditHandle
from ...internal.data_property import DataProperty, DataPropertyConfiguration
from ...internal.data_property_interface import DataPropertyInterface
from ...internal.string_data_property import (
  StringDataProperty, StringDataPropertyConfiguration)
from ...internal.telemetry import data_type_to_string
from ...internal.util import default_type_error_message

if typing.TYPE_CHECKING:
  import numpy.typing as npt

  from mapteksdk.capi import ModellingApi, SdpApi
  from mapteksdk.data import Topology
  from mapteksdk.data.colourmaps import ColourMap

log = logging.getLogger("mapteksdk.data")

class PrimitiveAttributes(MutableMapping[AttributeKey, np.ndarray]):
  """Provides access to the attributes for a given primitive type on an object.

  A primitive attribute is an attribute with one value for each primitive
  of a particular type. For example, if an object contains ten points
  then a point primitive attribute would have ten values - one for each
  point. Primitive attributes can be accessed by name using the [] operator
  (This is similar to accessing a dictionary). This class supports
  most (but not all) functions supported by a dictionary.

  Parameters
  ----------
  primitive_type
    The type of primitive these attributes have one value for.

  owner_object
    The object that the attributes are from.

  Warnings
  --------
  Primitive attributes set through the Python SDK may not appear in the user
  interface of Maptek applications.

  Edge and facet primitive attributes are not well supported by Maptek
  applications. You can read and write values from/to them via the SDK,
  however they are not visible from the application side.

  Notes
  -----
  It is not recommended to create PrimitiveAttribute objects directly.
  Instead use the properties in the See Also section.

  See Also
  --------
  mapteksdk.data.primitives.point_properties.PointProperties.point_attributes
    : Access per-point primitive attributes.
  mapteksdk.data.primitives.edge_properties.EdgeProperties.edge_attributes
    : Access per-edge primitive attributes.
  mapteksdk.data.primitives.facet_properties.FacetProperties.facet_attributes
    : Access per-facet primitive attributes.
  mapteksdk.data.primitives.cell_properties.CellProperties.cell_attributes
    : Access per-cell primitive attributes.
  mapteksdk.data.primitives.block_properties.BlockProperties.block_attributes
    : Access per-block primitive attributes.

  Examples
  --------
  Create a point primitive attribute of type string called "temperature".
  Note that new_set.point_attributes["temperature"][i] is the value
  associated with new_set.points[i] (so point[0] has the attribute "Hot",
  point[1] has the attribute "Warm" and point[2] has the attribute["Cold"]).

  >>> from mapteksdk.project import Project
  >>> from mapteksdk.data import PointSet
  >>> project = Project()
  >>> with project.new("cad/points", PointSet) as new_set:
  >>>     new_set.points = [[1, 1, 0], [2, 0, 1], [3, 2, 0]]
  >>>     new_set.point_attributes["temperature"] = ["Hot", "Warm", "Cold"]

  Colour the point set created in the previous example with a colour map
  such that points with attribute "Hot" are red, "Warm" are orange and
  "Cold" are blue.

  >>> from mapteksdk.project import Project
  >>> from mapteksdk.data import StringColourMap
  >>> project = Project()
  >>> with project.new("legends/heatMap", StringColourMap) as new_legend:
  >>>     new_legend.legend = ["Hot", "Warm", "Cold"]
  >>>     new_legend.colours = [[255, 0, 0], [255, 165, 0], [0, 0, 255]]
  >>> with project.edit("cad/points") as edit_set:
  >>>     edit_set.point_attributes.set_colour_map("temperature", new_legend)
  """

  __attribute_table: dict[int, type | None] = {
    0: None, 1: ctypes.c_bool, 2: ctypes.c_uint8, 3: ctypes.c_int8,
    4: ctypes.c_uint16, 5: ctypes.c_int16, 6: ctypes.c_uint32,
    7: ctypes.c_int32, 8: ctypes.c_uint64, 9: ctypes.c_int64,
    10: ctypes.c_float, 11: ctypes.c_double, 12: ctypes.c_char_p,
  }
  """Map type id to the corresponding ctypes type.

  This maps the type id returned by the C API to the corresponding
  ctypes type to use to get the R or RW function for an attribute
  of that type from the __type_to_function_r and __type_to_function_rw
  dictionaries.
  """

  __type_to_function_r: dict[type, str] = {
      ctypes.c_float: '{}AttributeFloat32BeginR',
      ctypes.c_double: '{}AttributeFloat64BeginR',
      ctypes.c_int64: '{}AttributeInt64sBeginR',
      ctypes.c_uint64: '{}AttributeInt64uBeginR',
      ctypes.c_int32: '{}AttributeInt32sBeginR',
      ctypes.c_uint32: '{}AttributeInt32uBeginR',
      ctypes.c_int16: '{}AttributeInt16sBeginR',
      ctypes.c_uint16: '{}AttributeInt16uBeginR',
      ctypes.c_int8: '{}AttributeInt8sBeginR',
      ctypes.c_uint8: '{}AttributeInt8uBeginR',
      ctypes.c_bool: '{}AttributeBoolBeginR',
      ctypes.c_char_p: '{}AttributeStringBeginR',
    }
  """Maps ctypes type for a primitive attribute to the R function.

  The name does not include the primitive type. To get the final name,
  format in the primitive name.
  """

  __type_to_function_rw: dict[type, str] = {
      ctypes.c_float: '{}AttributeFloat32BeginRW',
      ctypes.c_double: '{}AttributeFloat64BeginRW',
      ctypes.c_int64: '{}AttributeInt64sBeginRW',
      ctypes.c_uint64: '{}AttributeInt64uBeginRW',
      ctypes.c_int32: '{}AttributeInt32sBeginRW',
      ctypes.c_uint32: '{}AttributeInt32uBeginRW',
      ctypes.c_int16: '{}AttributeInt16sBeginRW',
      ctypes.c_uint16: '{}AttributeInt16uBeginRW',
      ctypes.c_int8: '{}AttributeInt8sBeginRW',
      ctypes.c_uint8: '{}AttributeInt8uBeginRW',
      ctypes.c_bool: '{}AttributeBoolBeginRW',
      ctypes.c_char_p: '{}AttributeStringBeginRW',
  }
  """Maps ctypes type for a primitive attribute to the R function.

  The name does not include the primitive type. To get the final name,
  format in the primitive name.
  """
  __telemetry_type_name = "PrimitiveAttribute"

  def __init__(self, primitive_type: PrimitiveType, owner_object: Topology):
    self.primitive_type: PrimitiveType = primitive_type
    """The type of primitive the attributes are associated with."""
    self.owner: Topology = owner_object
    """The object the attributes are read and set to."""
    self.__attributes: dict[AttributeKey, DataPropertyInterface] = {}
    """Dictionary of attribute keys to the data property."""
    self.__deleted_attributes: list[AttributeKey] = []
    """List of deleted attribute names."""

    # Populate the attribute metadata. This will load the name and
    # type of each attribute, but not the values, so this should be
    # fast.
    for name in self._load_names():
      key = AttributeKey.from_json(name)
      dtype = self._load_type_of_attribute(name)
      if dtype is None:
        # Don't log the warning for point to raster coordinate properties.
        # These are set by RasterRegistrationOverride.
        if name.startswith("P2RCoords"):
          continue
        log.warning(
          "Failed to read type of attribute: '%s'. It will be skipped.",
          name)
        continue
      self.__attributes[key] = self._load_attribute_metadata(key, dtype)

  @property
  def names(self) -> Sequence[str]:
    """Returns the names of the attributes.

    This can be used to iterate over all of the attributes for this
    primitive type.

    Returns
    -------
    Sequence[str]
      The names of the attributes associated with this primitive.

    Raises
    ------
    RuntimeError
      If an attribute is deleted while iterating over names.

    Examples
    --------
    Iterate over all attributes and print their values. This assumes
    there is a object with points at cad/points.

    >>> from mapteksdk.project import Project
    >>> project = Project()
    >>> with project.edit("cad/points") as point_set:
    ...     for name in point_set.point_attributes.names:
    ...         print(point_set.point_attributes[name])
    """
    return [key.display_name for key in self.keys()]

  def __getitem__(self, name: str | AttributeKey) -> np.ndarray:
    """Allows access to the attributes.

    object.point_attributes[name] will return the point attribute with the
    specified name.

    Parameters
    ----------
    name : str | AttributeKey
      Name or key of the primitive attribute to get the value of.

    Returns
    -------
    ndarray
      numpy array of length number_of_primitives containing the values for the
      specified primitive attribute.

    Raises
    ------
    KeyError
      If there is no primitive attribute with the specified name.
    """
    if not isinstance(name, AttributeKey):
      key = self.get_key_by_name(name)
    else:
      key = name
    values = self.__attributes[key].values
    self._record_read_attribute_telemetry(values.dtype)
    return values

  def __setitem__(self, name: str | AttributeKey, value: npt.ArrayLike):
    """Allows attributes to be set.

    object.point_attributes[name] = value will set the point attribute
    of the specified name to value. Note that value should be an array-like
    with one element for each primitive of the specified primitive type.
    If the value is too short it will be padded until it is the correct length,
    and if it is too long it will be silently truncated.

    Parameters
    ----------
    name
      The name of the attribute to set.
    value
      An array_like of values of the same type with length = number of
      primitives of this type in the object.

    Raises
    ------
    ValueError
      If name is not a string, starts or ends with whitespace or
      is empty.
    AmbiguousNameError
      If there is already a primitive attribute with the same name, but
      different metadata.
    """
    key = self._get_or_create_key(name)

    try:
      self._try_update_existing_attribute(key, value)
    except KeyError:
      self._add_new_attribute(key, value)

  def __delitem__(self, name: str | AttributeKey):
    self.delete_attribute(name)

  def __contains__(self, name: object) -> bool:
    """Implementation of the in operator for primitive attributes."""
    if isinstance(name, str):
      try:
        _ = self.get_key_by_name(name)
        return True
      except KeyError:
        return False
    elif isinstance(name, AttributeKey):
      return name in self.__attributes
    else:
      return False

  def __len__(self) -> int:
    return len(self.__attributes)

  def __iter__(self):
    return iter(self.__attributes)

  def delete_attribute(self, name: AttributeKey | str):
    """Deletes the attribute with name, if it exists.

    This method does not throw an exception if the attribute does not exist.

    Parameters
    ----------
    name
      The name of the primitive attribute to delete.

    Raises
    ------
    ValueError
      If the deleted attribute is associated with a colour map.
    TypeError
      If the key is not a string or AttributeKey.
    """
    if isinstance(name, AttributeKey):
      if name not in self.__attributes:
        # There is no attribute with the specified key. Nothing to
        # delete.
        return
      key = name
    elif isinstance(name, str):
      try:
        key = self.get_key_by_name(name)
      except KeyError:
        # There is no attribute with the specified name. Nothing to
        # delete.
        return
    else:
      raise TypeError(
        default_type_error_message(
          "name",
          name,
          AttributeKey | str
        )
      )
    colour_map_key = self.colour_map_key
    if colour_map_key is not None and colour_map_key == key:
      raise ValueError(
        f"Cannot delete {key.name}. It is associated with a colour map."
      )
    self.__deleted_attributes.append(key)
    data_property = self.__attributes.pop(key, None)
    if data_property:
      # pylint: disable=protected-access
      self._record_delete_attribute_telemetry(
        data_property.values.dtype
      )

  @property
  def colour_map(self) -> ObjectID[ColourMap] | None:
    """Get the colour map used to colour the primitives.

    This returns the colour map passed into set_colour_map.

    Returns
    -------
    ObjectID
      Object id of the colour map associated with this object.
    None
      If no colour map is associated with this object.
    """
    # pylint: disable=protected-access
    colour_map_information = self.owner._colour_map_information()
    if not colour_map_information.is_valid():
      return None
    if colour_map_information.primitive_type == self.primitive_type:
      return colour_map_information.colour_map_id
    return None

  @property
  def colour_map_key(self) -> AttributeKey | None:
    """Returns the key of the attribute the colour map is associated with.

    The key contains extra metadata beyond the name of the attribute.

    Returns
    -------
    key
      The key of the primitive attribute associated with the colour map.
    None
      If no colour map is associated with this primitive type.
    """
    # pylint: disable=protected-access
    colour_map_information = self.owner._colour_map_information()
    if not colour_map_information.is_valid():
      return None
    if colour_map_information.primitive_type == self.primitive_type:
      if colour_map_information.attribute_key is None:
        try:
          # Try to update the colour map information to know what the key is.
          colour_map_information.attribute_key = self.get_key_by_name(
            colour_map_information.attribute_name
          )
        except KeyError:
          return None
      return colour_map_information.attribute_key
    return None

  @property
  def colour_map_attribute(self) -> str | None:
    """Returns the name of the attribute the colour map is associated with.

    Returns
    -------
    string
      Name of attribute associated with the colour map.
    None
      If no colour map is associated with this primitive.
    """
    key = self.colour_map_key
    if key is not None:
      return key.name
    return None

  def set_colour_map(
      self,
      attribute: str | AttributeKey,
      colour_map: ObjectID[ColourMap] | ColourMap):
    """Set the colour map for this type of primitive.

    Only one colour map can be associated with an object at a time.
    Attempting to associate another colour map will discard the currently
    associated colour map.

    Parameters
    ----------
    attribute
      The name or key of the attribute to colour by.
    colour_map
      Object id of the colour map to use for this object. You can also pass
      the colour map directly.

    Raises
    ------
    ValueError
      If colour map is an invalid type.
    RuntimeError
      If this object's primitive type is not point.

    Warnings
    --------
    Associating a colour map to edge, facet or cell attributes is not currently
    supported by the viewer. Attempting to do so will raise a RuntimeError.

    Notes
    -----
    Changed in mapteksdk 1.5:

    * Prior to 1.5, this function included an implicit call to save()
    * Prior to 1.5, it was not defined which colour map (if any) would be
      kept if this was called for multiple different primitive types.

    """
    # pylint: disable=protected-access
    if self.primitive_type not in (PrimitiveType.POINT, PrimitiveType.BLOCK):
      name = self.primitive_type.name.lower() + " attributes"
      raise RuntimeError(f"Setting a colour map to {name} is not supported.")

    if isinstance(attribute, AttributeKey):
      key = attribute
    else:
      key = self.get_key_by_name(attribute)

    if colour_map is None:
      # Passing None invalidates the colour map.
      self.owner._invalidate_colour_map()
      return
    if isinstance(colour_map, (NumericColourMap, StringColourMap)):
      colour_map_id = colour_map.id
    elif isinstance(colour_map, ObjectID):
      if colour_map.is_a((NumericColourMap, StringColourMap)):
        colour_map_id = colour_map
      else:
        raise ValueError(
          f"Invalid colour map object id. It was a {colour_map.type_name}. "
          "It must be a NumericColourMap or a StringColourMap.")
    else:
      raise ValueError(
          f"Invalid colour map: {colour_map} of type: {type(colour_map)}")

    self.owner._set_colour_map(
      key,
      self.primitive_type,
      colour_map_id
    )
    self._record_set_colour_map_telemetry(
      colour_map_id
    )

  def apply_colour_scheme(
    self,
    attribute: AttributeKey | str,
    colour_scheme: ColourScheme
  ):
    """Colour the object via `attribute` using `colour_scheme`.

    Unlike assigning a colour map, this assigns the colours into the
    associated primitive colours array, overwriting any existing
    primitive colours. This means the colouring will not be updated
    if `attribute` is updated.

    This includes an implicit call to save.

    Parameters
    ----------
    attribute
      The primitive attribute to colour by.
    colour_scheme
      The colour scheme to use.

    Raises
    ------
    KeyError
      If `attribute` does not refer to an existing attribute.

    Notes
    -----
    This has no visible affect for cell attributes because
    (as of writing 2024-08-12), no Maptek Application supports visualising
    cell colours.
    """
    if isinstance(attribute, AttributeKey):
      key = attribute
    else:
      key = self.get_key_by_name(attribute)

    if key not in self:
      raise KeyError(f"The '{key.name}' attribute does not exist.")

    if not isinstance(colour_scheme, ColourScheme):
      raise TypeError(
        default_type_error_message(
          "colour_scheme",
          colour_scheme,
          ColourScheme
        )
      )

    # pylint: disable=protected-access
    self.owner._raise_if_read_only("Set colour scheme")

    # Save any changes so that the C++ code can see the attribute which
    # this is colouring by.
    self.owner.save()
    self.__apply_colour_scheme(colour_scheme, key)
    # The C++ code will write the colours to the RW array.
    # Python reads colours from the R arrays, so a call to reconcile changes
    # is required to make the new colours visible in Python.
    self.owner._reconcile_changes()
    # pylint: disable=protected-access
    self._record_colour_scheme_telemetry()

  def __apply_colour_scheme(
    self,
    colour_scheme: ColourScheme,
    key: AttributeKey
  ):
    """Internal application of a colour scheme."""
    if self.primitive_type == PrimitiveType.POINT:
      apply_colour_scheme = self._sdp_api().ApplyPointColourScheme
    elif self.primitive_type == PrimitiveType.EDGE:
      apply_colour_scheme = self._sdp_api().ApplyEdgeColourScheme
    elif self.primitive_type == PrimitiveType.FACET:
      apply_colour_scheme = self._sdp_api().ApplyFacetColourScheme
    elif self.primitive_type == PrimitiveType.CELL:
      apply_colour_scheme = self._sdp_api().ApplyCellColourScheme
    elif self.primitive_type == PrimitiveType.BLOCK:
      apply_colour_scheme = self._sdp_api().ApplyBlockColourScheme
    else:
      raise RuntimeError(
      "Unreachable code reached. "
      f"Invalid primitive type: {self.primitive_type}"
    )
    apply_colour_scheme(
      # pylint: disable=protected-access
      self.owner._lock.lock,
      colour_scheme.value,
      key.to_json()
    )

  @property
  def primitive_count(self) -> int:
    """The number of primitives of the given type in the object.

    Returns
    -------
    int
      Number of points, edges, facets or blocks. Which is returned depends
      on primitive type given when this object was created.

    Raises
    ------
    ValueError
      If the type of primitive is unsupported.
    """
    if self.primitive_type == PrimitiveType.POINT:
      assert hasattr(self.owner, "point_count")
      return getattr(self.owner, "point_count", 0)
    if self.primitive_type == PrimitiveType.EDGE:
      assert hasattr(self.owner, "edge_count")
      return getattr(self.owner, "edge_count", 0)
    if self.primitive_type == PrimitiveType.FACET:
      assert hasattr(self.owner, "facet_count")
      return getattr(self.owner, "facet_count", 0)
    if self.primitive_type == PrimitiveType.BLOCK:
      assert hasattr(self.owner, "block_count")
      return getattr(self.owner, "block_count", 0)
    if self.primitive_type == PrimitiveType.CELL:
      assert hasattr(self.owner, "cell_count")
      return getattr(self.owner, "cell_count", 0)
    raise ValueError(f'Unexpected primitive type {self.primitive_type!r}')

  def _saved_primitive_count(self, lock: T_ReadHandle) -> int:
    """The number of primitives of the given type read from the application.

    Unlike primitive_count, this reads the value directly from the
    application. This means it can be used to determine the length
    of primitive arrays returned from the application.

    Returns
    -------
    int
      The number of primitives in the object in the Project.
    """
    primitive_count_functions = {
      PrimitiveType.POINT : self._modelling_api().ReadPointCount,
      PrimitiveType.EDGE : self._modelling_api().ReadEdgeCount,
      PrimitiveType.FACET : self._modelling_api().ReadFacetCount,
      PrimitiveType.CELL : self._modelling_api().ReadCellCount,
      PrimitiveType.BLOCK : self._modelling_api().ReadBlockCount
    }

    try:
      return primitive_count_functions[self.primitive_type](lock)
    except KeyError:
      # Intentionally suppress the internal error because it isn't
      # relevant to the caller.
      # pylint: disable=raise-missing-from
      raise ValueError(f'Unexpected primitive type {self.primitive_type!r}')

  def save_attributes(self):
    """Saves changes to the attributes to the Project.

    This should not need to be explicitly called - it is called during save()
    and close() of an inheriting object. It is not recommended to call this
    function directly.
    """
    # Delete the attributes which were deleted.
    for deleted in self.__deleted_attributes:
      self._delete_attribute(deleted.to_json())
    self.__deleted_attributes = []
    # Set the existing attributes.
    for value in self.__attributes.values():
      value.save()

  def type_of_attribute(self, name: str) -> type:
    """Returns the ctype of the specified attribute."""
    if self[name].dtype.kind in {'U', 'S'}:
      return ctypes.c_char_p
    return np.ctypeslib.as_ctypes_type(self[name].dtype)

  def get_key_by_name(self, name: str) -> AttributeKey:
    """Get the AttributeKey for the attribute with the specified name.

    Parameters
    ----------
    name: str
      The name of the attribute to get.

    Returns
    -------
    AttributeKey
      The key of the attribute with the specified name.

    Raises
    ------
    KeyError
      If no attribute with the specified name exists.
    """
    for key in self.__attributes:
      if key.display_name == name:
        return key
    raise KeyError(f"No attribute with name: '{name}'")

  def _get_or_create_key(self, name: str | AttributeKey) -> AttributeKey:
    """Get existing key or create a new key.

    Raises
    ------
    ValueError
      If name is an invalid name for a primitive attribute.
    """
    if isinstance(name, str):
      if name.strip() != name:
        raise ValueError(
          "Name must not contain leading or trailing whitespace. "
          f"Invalid primitive attribute name: '{name}'."
        )
      if name == "":
        raise ValueError("Name must not be empty.")
      try:
        # If there is already an attribute with the specified name,
        # assign to that one.
        key = self.get_key_by_name(name)
      except KeyError:
        # There is no attribute with this name. Create a new one.
        key = AttributeKey(name)
    elif isinstance(name, AttributeKey):
      key = name
    else:
      raise ValueError(f"Invalid type for name: {type(name)}")
    return key

  def _modelling_api(self) -> ModellingApi:
    # pylint: disable=protected-access
    return self.owner._modelling_api()

  def _sdp_api(self) -> SdpApi:
    """Access the Spatial Data Processing C API."""
    # pylint: disable=protected-access
    return self.owner._sdp_api()

  def _try_update_existing_attribute(
    self,
    key: AttributeKey,
    value: npt.ArrayLike
  ):
    """Update the values of the `key` attribute if it exists.

    Raises
    ------
    KeyError
      If the attribute with `key` does not exist.
    AmbiguousNameError
      If there exists an attribute with the same name as `key`, but with
      different metadata.
    """
    try:
      attribute = self.__attributes[key]
      attribute.values = value
      dtype = attribute.values.dtype
      # pylint: disable=protected-access
      self._record_edit_attribute_telemetry(dtype)
    except KeyError:
      try:
        existing_key = self.get_key_by_name(key.name)
        if existing_key != key:
          raise AmbiguousNameError(
            f"Cannot add {key.to_json()}. There is already an attribute with "
            f"that name ({existing_key.to_json()})"
          ) from None
      except KeyError:
        pass
      raise

  def _add_new_attribute(
    self,
    key: AttributeKey,
    value: npt.ArrayLike
  ):
    """Add a new primitive attribute.

    This will replace any existing attribute with the given key.
    This does not check for the attribute name being ambiguous.
    """
    if not isinstance(value, np.ndarray):
      array = np.array(value)
    else:
      array = value

    if key.data_type is not None:
      # Use the metadata data type if possible.
      dtype = key.data_type
    else:
      # Maps the data type of the numpy array to its corresponding type in
      # ctypes.
      if array.dtype.kind in {'U', 'S', 'O'}:
        dtype = ctypes.c_char_p
      else:
        dtype = np.ctypeslib.as_ctypes_type(array.dtype)

    metadata = self._load_attribute_metadata(
      key, dtype
    )
    metadata.values = array
    # Don't add the metadata to the dictionary until after the values
    # have been assigned. This avoids creating a blank attribute
    # if an error occurs while assigning the values.
    self.__attributes[key] = metadata
    # pylint: disable=protected-access
    self._record_add_attribute_telemetry(dtype)

  def _load_attribute_metadata(
      self,
      name: AttributeKey,
      dtype: type) -> DataPropertyInterface:
    """Load metadata for a primitive attribute by name.

    Parameters
    ----------
    name
      Name of the attribute to load metadata for.
    dtype
      The ctypes type of the attribute to load metadata for.

    Returns
    -------
    DataPropertyInterface
      Object which can be used to read and save the values for the attribute
      with the specified name and type.
    """
    if dtype is ctypes.c_char_p:
      return self.__load_string_attribute_metadata(name)
    return self.__load_numeric_attribute_metadata(name, dtype)

  def __load_numeric_attribute_metadata(
      self,
      name: AttributeKey,
      dtype: type) -> DataProperty:
    """Load metadata for a numeric primitive attribute by name.

    Parameters
    ----------
    name
      Name of the attribute to load metadata for.
    dtype
      The ctypes type of the attribute to load metadata for. This must
      not be ctypes.c_char_p.

    Returns
    -------
    DataProperty
      Object which can be used to read and save the values for the attribute
      with the specified name and type.
    """
    # pylint: disable=protected-access
    def load_attribute(lock, function_name: str, attribute_name: str):
      return getattr(self._modelling_api(), function_name)(
        lock, attribute_name.encode("utf-8"))
    def save_attribute(lock, function_name, attribute_name):
      return getattr(self._modelling_api(), function_name)(
        lock, attribute_name.encode("utf-8"))

    # DataProperty requires the save and load functions to accept
    # a single argument (the lock) and return the R or RW array.
    # Primitive attributes require an extra argument, the attribute name,
    # these partials set the attribute name to be this attribute's name
    # so that DataProperty can call the function without specifying
    # the extra arguments.
    load_function_name = self.__type_to_function_r[dtype].format(
      self.primitive_type._to_string()
    )
    load_function = partial(
      load_attribute,
      function_name=load_function_name,
      attribute_name=name.to_json()
    )

    save_function_name = self.__type_to_function_rw[dtype].format(
      self.primitive_type._to_string()
    )
    save_function = partial(
      save_attribute,
      function_name=save_function_name,
      attribute_name=name.to_json()
    )

    default = 0

    return DataProperty(
      self.owner._lock,
      DataPropertyConfiguration(
        name="name",
        dtype=dtype,
        default=default,
        column_count=1,
        load_function=load_function,
        save_function=save_function,
        primitive_count_function=self._saved_primitive_count,
        cached_primitive_count_function=lambda: self.primitive_count,
        set_primitive_count_function=None,
        is_colour_property=False,
        immutable=False,
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode
      )
    )

  def __load_string_attribute_metadata(self, name: AttributeKey):
    """Load metadata for a string primitive attribute by name.

    This assumes the attribute with the specified name has a ctypes type
    of c_char_p.

    Parameters
    ----------
    name
      Name of the string attribute to load metadata for.

    Returns
    -------
    DataProperty
      Object which can be used to read and save the values for the attribute
      with the specified name and type.
    """
    # pylint: disable=protected-access
    save_function = partial(self._save_string_attribute, name=name.to_json())
    load_function = partial(self._load_string_attribute, name=name.to_json())

    return StringDataProperty(self.owner._lock,
      StringDataPropertyConfiguration(
        name=name.name,
        default="",
        load_function=load_function,
        save_function=save_function,
        primitive_count_function=self._saved_primitive_count,
        cached_primitive_count_function=lambda: self.primitive_count
      )
    )

  def _load_type_of_attribute(self, name: str) -> type | None:
    """Loads the type of the attribute called name from the Project.

    Parameters
    ----------
    name
      The name of the attribute.

    Returns
    -------
    type
      A type from ctypes that represented the type of the attributes.

    Raises
    ------
    ValueError
      If this type of primitive isn't supported or doesn't have attributes.
    """
    if self.primitive_type == PrimitiveType.POINT:
      type_query_function = self._modelling_api().PointAttributeType
    elif self.primitive_type == PrimitiveType.EDGE:
      type_query_function = self._modelling_api().EdgeAttributeType
    elif self.primitive_type == PrimitiveType.FACET:
      type_query_function = self._modelling_api().FacetAttributeType
    elif self.primitive_type == PrimitiveType.BLOCK:
      type_query_function = self._modelling_api().BlockAttributeType
    elif self.primitive_type == PrimitiveType.CELL:
      type_query_function = self._modelling_api().CellAttributeType
    else:
      raise ValueError(f'Unexpected primitive type {self.primitive_type!r}')

    # pylint:disable=protected-access; reason="This is a mixin class"
    attribute_type = type_query_function(
      self.owner._lock.lock, name.encode('utf-8'))
    return self.__attribute_table[attribute_type]

  def _load_names(self):
    """Loads the names of all attributes from the Project.

    Returns
    -------
    list
      List of str, one for each attribute name.
    """
    if self.primitive_type == PrimitiveType.POINT:
      name_query_function = self._modelling_api().ListPointAttributeNames
    elif self.primitive_type == PrimitiveType.EDGE:
      name_query_function = self._modelling_api().ListEdgeAttributeNames
    elif self.primitive_type == PrimitiveType.FACET:
      name_query_function = self._modelling_api().ListFacetAttributeNames
    elif self.primitive_type == PrimitiveType.BLOCK:
      name_query_function = self._modelling_api().ListBlockAttributeNames
    elif self.primitive_type == PrimitiveType.CELL:
      name_query_function = self._modelling_api().ListCellAttributeNames
    else:
      raise ValueError(f'Unexpected primitive type {self.primitive_type!r}')

    # pylint:disable=protected-access; reason="This is a mixin class"
    buffer_size = name_query_function(self.owner._lock.lock, None, 0)
    string_buffer = ctypes.create_string_buffer(buffer_size)
    name_query_function(self.owner._lock.lock, string_buffer, buffer_size)
    # The last two items after the split are ignored because the last string is
    # null-terminated and the list itself is null-terminated, so there are no
    # name between them and there is no name after the final terminator.
    return bytearray(string_buffer).decode('utf-8').split('\x00')[:-2]

  def _save_colour_map(
      self, attribute_name: str, colour_map: ObjectID[ColourMap]):
    """Saves the colour map to the Project.

    Parameters
    ----------
    attribute_name
      Name of attribute to colour by colour_map
    colour_map
      The ID of the colour map object to use.

    Raises
    ------
    ValueError
      If this type of primitive doesn't support setting a colour map.
    Exception
      If the object is opened in read-only mode.
    """
    # pylint:disable=protected-access; reason="This is a mixin class"
    self.owner._raise_if_save_in_read_only()
    if self.primitive_type == PrimitiveType.POINT:
      set_function = self._modelling_api().SetDisplayedPointAttribute
    elif self.primitive_type == PrimitiveType.EDGE:
      set_function = self._modelling_api().SetDisplayedEdgeAttribute
    elif self.primitive_type == PrimitiveType.FACET:
      set_function = self._modelling_api().SetDisplayedFacetAttribute
    elif self.primitive_type == PrimitiveType.BLOCK:
      set_function = self._modelling_api().SetDisplayedBlockAttribute
    elif self.primitive_type == PrimitiveType.CELL:
      set_function = self._modelling_api().SetDisplayedCellAttribute
    else:
      raise ValueError(
        f'Unexpected primitive type {self.primitive_type!r}')
    set_function(
      self.owner._lock.lock,
      attribute_name.encode('utf-8'),
      colour_map.handle)

  def _load_colour_map(self) -> ObjectID[ColourMap] | None:
    """Loads the associated colour map from the Project.

    Returns
    -------
    ObjectID
      The colour map associated with this object.
    """
    # pylint:disable=protected-access; reason="This is a mixin class"
    result = self._modelling_api().GetDisplayedColourMap(
      self.owner._lock.lock)
    # If result is zero, no colour map was set.
    if result.value != 0:
      return ObjectID(result)
    return None

  def _delete_attribute(self, name: str):
    """Delete a primitive attribute in the Project by name.

    This version of the function performs the deletion in the Project.

    Parameters
    ----------
    name
      The name of attribute

    Raises
    ------
    CannotSaveInReadOnlyModeError
      If the object is opened in read-only mode.
    ValueError
      If the primitive type is not supported.

    """
    # pylint:disable=protected-access; reason="This is a mixin class"
    self.owner._raise_if_save_in_read_only()
    if self.primitive_type == PrimitiveType.POINT:
      delete_function = self._modelling_api().DeletePointAttribute
    elif self.primitive_type == PrimitiveType.EDGE:
      delete_function = self._modelling_api().DeleteEdgeAttribute
    elif self.primitive_type == PrimitiveType.FACET:
      delete_function = self._modelling_api().DeleteFacetAttribute
    elif self.primitive_type == PrimitiveType.BLOCK:
      delete_function = self._modelling_api().DeleteBlockAttribute
    elif self.primitive_type == PrimitiveType.CELL:
      delete_function = self._modelling_api().DeleteCellAttribute
    else:
      raise ValueError(
        f'Unexpected primitive type {self.primitive_type!r}')

    delete_function(
      self.owner._lock.lock,
      name.encode('utf-8'))

  def _load_string_attribute(
      self,
      lock: T_ReadHandle,
      name: str) -> np.ndarray:
    """Load the values of a string primitive attribute.

    Parameters
    ----------
    lock
      Lock on the object to read the string attribute of.
    name
      The name of the string attribute to read.

    Returns
    -------
    numpy.ndarray
      The values for the attribute with the given name for the given object.
    """
    # pylint: disable=protected-access
    type_name = self.primitive_type._to_string()
    save_function_name = f"{type_name}AttributeStringBeginR"
    ptr = getattr(self._modelling_api(), save_function_name)(lock,
                                                   name.encode('utf-8'))

    if not ptr:
      try:
        self._modelling_api().RaiseOnErrorCode()
      except MemoryError as error:
        log.error('Failed to read the %s attribute (%s) on %s: %s',
                  self.primitive_type.name, name, self.owner.id, str(error))
        raise MemoryError(
          'The attribute could not fit in the Project\'s cache') from None
      except:
        log.exception('Failed to read the attribute (%s) on %s',
                      name, self.owner.id)
        raise

    values = []
    # There will be a string for each primitive.
    # :TRICKY: This can't use np.empty() to preallocate the array of strings
    # because the maximum string length isn't known until all the strings
    # are read.
    for index in range(self.primitive_count):
      str_len = self._modelling_api().AttributeGetString(
        ptr, index, None, 0)
      str_buffer = ctypes.create_string_buffer(str_len)
      self._modelling_api().AttributeGetString(ptr, index, str_buffer, str_len)
      values.append(str_buffer.value.decode("utf-8"))
    return np.array(values, dtype=np.str_)

  def _save_string_attribute(
      self,
      lock: T_EditHandle,
      data: np.ndarray,
      name: str):
    """Save the values of a string primitive attribute.

    Parameters
    ----------
    lock
      Lock on the object to save the attribute.
    data
      Data to save to the string attribute. This should contain one string
      for each primitive.
    name
      Name of the string attribute to save.
    """
    # :TRICKY: name must be the last parameter because it is set
    # using functools.partial.
    # pylint: disable=protected-access
    type_name = self.primitive_type._to_string()
    save_function_name = f"{type_name}AttributeStringBeginRW"
    ptr = getattr(self._modelling_api(), save_function_name)(lock,
                                                   name.encode('utf-8'))

    if not ptr:
      try:
        self._modelling_api().RaiseOnErrorCode()
      except MemoryError as error:
        log.error('Failed to write to the %s attribute (%s) on %s: %s',
                  self.primitive_type.name, name, self.owner.id, str(error))
        raise MemoryError(
          'The attribute could not fit in the Project\'s cache') from None
      except:
        log.exception('Failed to write to the attribute (%s) on %s',
                      name, self.owner.id)
        raise

    for index, string in enumerate(data):
      utf8string = string.encode('utf-8')
      self._modelling_api().AttributeSetString(
        ptr, index, utf8string, len(utf8string))

  def _dtype_to_string(self, dtype: np.dtype) -> str:
    """Convert a numpy dtype to a string."""
    if dtype.kind == "U":
      data_type = "str"
    else:
      try:
        data_type = data_type_to_string(np.ctypeslib.as_ctypes_type(dtype))
      except NotImplementedError:
        data_type = "unknown"
    return data_type

  def _record_telemetry(self):
    """Record telemetry for the primitive attribute counts."""
    attribute_count = len(self)
    primitive_name = self.primitive_type.name.capitalize()

    # pylint: disable=protected-access
    self.owner._record_size_for(
      f"{primitive_name}Attributes",
      attribute_count
    )

  def _record_add_attribute_telemetry(
    self,
    dtype: type
  ):
    """Record telemetry for adding a primitive attribute."""
    # pylint: disable=protected-access
    data_type = data_type_to_string(dtype)
    primitive_type = self.primitive_type._to_string()
    self.owner._record_function_call_telemetry(
      f"{primitive_type}.create_{data_type}",
      self.__telemetry_type_name
    )

  def _record_edit_attribute_telemetry(
    self,
    dtype: np.dtype
  ):
    """Record telemetry for editing a primitive attribute."""
    # pylint: disable=protected-access
    data_type = self._dtype_to_string(dtype)
    primitive_type = self.primitive_type._to_string()
    self.owner._record_function_call_telemetry(
      f"{primitive_type}.edit_{data_type}",
      self.__telemetry_type_name
    )

  def _record_read_attribute_telemetry(
    self,
    dtype: np.dtype
  ):
    """Record telemetry for reading a primitive attribute."""
    # pylint: disable=protected-access
    data_type = self._dtype_to_string(dtype)
    primitive_type = self.primitive_type._to_string()
    self.owner._record_function_call_telemetry(
      f"{primitive_type}.read_{data_type}",
      self.__telemetry_type_name
    )

  def _record_delete_attribute_telemetry(
    self,
    dtype: np.dtype
  ):
    """Record telemetry for deleting a primitive attribute."""
    # pylint: disable=protected-access
    data_type = self._dtype_to_string(dtype)
    primitive_type = self.primitive_type._to_string()
    self.owner._record_function_call_telemetry(
      f"{primitive_type}.delete_{data_type}",
      self.__telemetry_type_name
    )

  def _record_set_colour_map_telemetry(
    self,
    colour_map_id: ObjectID[NumericColourMap | StringColourMap]
  ):
    """Records telemetry for setting a colour map."""
    # pylint: disable=protected-access
    primitive_type = self.primitive_type._to_string()
    if colour_map_id.is_a(NumericColourMap):
      colour_map_type = "numeric"
    elif colour_map_id.is_a(StringColourMap):
      colour_map_type = "string"
    else:
      colour_map_type = "unknown"
    self.owner._record_function_call_telemetry(
      f"{primitive_type}.set_colour_map_{colour_map_type}",
      self.__telemetry_type_name
    )

  def _record_colour_scheme_telemetry(self):
    """Record telemetry for applying a colour scheme."""
    # pylint: disable=protected-access
    primitive_type = self.primitive_type._to_string()
    self.owner._record_function_call_telemetry(
      f"{primitive_type}.apply_colour_scheme",
      self.__telemetry_type_name
    )
