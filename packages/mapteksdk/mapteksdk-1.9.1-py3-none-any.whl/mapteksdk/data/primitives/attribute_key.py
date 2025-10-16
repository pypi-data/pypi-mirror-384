"""Keys for accessing primitive attributes consistently."""
###############################################################################
#
# (C) Copyright 2023, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import ctypes
import dataclasses
import json
import typing

from ..units import (
  DistanceUnit, AngleUnit, UnsupportedUnit, _any_unit_from_string)

if typing.TYPE_CHECKING:
  import sys

  if sys.version_info >= (3, 11):
    Self = typing.Self
  else:
    Self = typing.Any

_STRING_TO_DTYPE = {
  "Tbool": ctypes.c_bool,
  "Tint8u" : ctypes.c_uint8,
  "Tint8s" : ctypes.c_int8,
  "Tint16u" : ctypes.c_uint16,
  "Tint16s" : ctypes.c_int16,
  "Tint32u" : ctypes.c_uint32,
  "Tint32s" : ctypes.c_int32,
  "Tint64u" : ctypes.c_uint64,
  "Tint64s" : ctypes.c_int64,
  "Tfloat32" : ctypes.c_float,
  "Tfloat64" : ctypes.c_double,
  "Tstring" : ctypes.c_char_p
}
"""Map strings to corresponding data types."""

_DTYPE_TO_STRING = {
  ctypes.c_bool : "Tbool",
  ctypes.c_uint8 : "Tint8u",
  ctypes.c_int8 : "Tint8s",
  ctypes.c_uint16 : "Tint16u",
  ctypes.c_int16 : "Tint16s",
  ctypes.c_uint32 : "Tint32u",
  ctypes.c_int32 : "Tint32s",
  ctypes.c_uint64 : "Tint64u",
  ctypes.c_int64 : "Tint64s",
  ctypes.c_float : "Tfloat32",
  ctypes.c_double : "Tfloat64",
  ctypes.c_char_p : "Tstring"
}
"""Maps data types to corresponding strings."""

_VERSION_KEY: typing.LiteralString = "v"
"""Key used to serialise the version."""
_SEMANTIC_KEY: typing.LiteralString = "s"
"""Key used to serialise the semantic."""
_TYPE_KEY: typing.LiteralString = "t"
"""Key used to serialise the type."""
_UNIT_KEY: typing.LiteralString = "u"
"""Key used to serialise the unit."""
_NAME_KEY: typing.LiteralString = "c"
"""Key used to serialise the name."""
_NULL_VALUES_KEY: typing.LiteralString = "n"
"""Key used to serialise the null values."""

class AttributeKey:
  """A key for accessing attributes.

  Primitive attributes can be read, edited and created using their
  name (a string) or using an AttributeKey object. The primary advantage
  of using an AttributeKey is it allows for any metadata (e.g. The unit) of the
  primitive attribute to be read via the properties on the AttributeKey
  object.

  Examples
  --------
  If an AttributeKey is constructed through the constructor, then it
  will contain no metadata and attempting to access the metadata will
  return None. For example:

  >>> from mapteksdk.data import AttributeKey
  >>> no_meta_data_key = AttributeKey("distance from object")
  >>> print("Name: ", no_metadata_key.name)
  >>> print("Data type: ", no_metadata_key.data_type)
  >>> print("Unit: ", no_metadata_key.unit)
  >>> print("Null values: ", no_metadata_key.null_values)
  Name:  distance from object
  Data type:  None
  Unit:  None
  Null values:  None

  Alternatively, the metadata of an AttributeKey can be specified
  when it is created. This allows for creating primitive attributes
  with additional metadata.

  >>> import ctypes
  >>> import math
  >>> from mapteksdk.data import AttributeKey, DistanceUnit
  >>> metadata_key = AttributeKey.create_with_metadata(
  ...     "distance from origin",
  ...     # The values of the attribute must be 64 bit floating point numbers.
  ...     data_type=ctypes.c_double,
  ...     # The values are in metres.
  ...     unit=DistanceUnit.METRE,
  ...     # NaN (Not a Number) is used to represent invalid values.
  ...     null_values=(math.nan,)
  >>> )
  >>> print("Name: ", metadata_key.name)
  >>> print("Data type: ", metadata_key.data_type)
  >>> print("Unit: ", metadata_key.unit)
  >>> print("Null values: ", metadata_key.null_values)
  Name:  distance from origin
  Data type:  <class 'ctypes.c_double'>
  Unit:  DistanceUnit.METRE
  Null values:  ('nan',)

  Once an AttributeKey is created, it can be used to create a primitive
  attribute the same as a string. For example:

  >>> point_set: PointSet
  >>> point_set.point_attributes[no_metadata_key] = np.zeros(
  ...     (point_set.point_count,))
  >>> point_set.point_attributes[metadata_key] = np.zeros(
  ...     (point_set.point_count,))

  To read the primitive attribute, you can either use the attribute key
  or the name given to the attribute.

  >>> point_set: PointSet
  >>> # These will both read the same point attribute.
  >>> _ = point_set.point_attributes[no_metadata_key]
  >>> _ = point_set.point_attributes["distance from object"]
  """
  @dataclasses.dataclass(frozen=True)
  class _AttributeKeyMetadata:
    data_type: type
    """The type of data stored for each primitive."""
    semantic: str
    """Semantic of the data."""
    unit: UnsupportedUnit | DistanceUnit | AngleUnit
    """The unit the data is stored in."""
    null_values: tuple[str, ...] = tuple()
    """A tuple of null values for the attribute.

    The null values are always represented as strings and are never
    checked for being the correct type.
    """
    version: int = 3
    """The version of the attribute metadata."""

  _PYTHON_TYPE_TO_C_TYPE: typing.ClassVar[dict[type, type]] = {
    int : ctypes.c_int32,
    float : ctypes.c_double,
    bool : ctypes.c_bool,
    str : ctypes.c_char_p
  }
  """Dictionary which maps Python types to ctypes.

  This is used to allow AttributeKey.create_with_metadata() to accept
  Python types.
  """

  SUPPORTED_DATA_TYPES: typing.ClassVar[set[type]] = {
    ctypes.c_uint8, ctypes.c_int8, ctypes.c_uint16, ctypes.c_int16,
    ctypes.c_uint32, ctypes.c_int32, ctypes.c_uint64, ctypes.c_int64,
    ctypes.c_double, ctypes.c_float, ctypes.c_char_p, ctypes.c_bool
  }
  """The set of supported data types for AttributeKeys."""

  def __init__(self, name: str) -> None:
    self.__name: str = name
    self._metadata: AttributeKey._AttributeKeyMetadata | None = None

  def __eq__(self, __value: object) -> bool:
    if not isinstance(__value, AttributeKey):
      return False
    return self.name == __value.name and self._metadata == __value._metadata

  def __hash__(self) -> int:
    return hash(self.__name) + hash(self._metadata)

  @property
  def name(self) -> str:
    """The name of the attribute.

    This should uniquely identify the primitive attribute.
    """
    return self.__name

  @property
  def display_name(self) -> str:
    """The display name of the attribute.

    This is the name if the name is not empty. Otherwise, this will be the
    semantic. If both the name and semantic are empty, this will be the empty
    string.

    Certain built-in primitive attributes use the semantic as the name and
    leave the name blank.
    """
    return self.name or self.semantic or ""

  @property
  def data_type(self) -> type | None:
    """The type of data stored by this attribute.

    Attempting to assign values which cannot be converted to this
    type to a primitive attribute with this key will raise a
    ValueError.

    If this is None, then values of any type can be associated with this
    primitive attribute.
    """
    if self._metadata is None:
      return None
    return self._metadata.data_type

  @property
  def semantic(self) -> str | None:
    """The semantic of the data stored by this attribute.

    If this is None, the semantic is undefined.
    """
    if self._metadata is None:
      return None
    return self._metadata.semantic

  @property
  def unit(self) -> UnsupportedUnit | DistanceUnit | AngleUnit | None:
    """The unit this data is stored in.

    If this attribute stores distances, this will be a DistanceUnit.
    If this attribute stores angles, this will be an AngleUnit.
    If this attribute stores any other data, this will be an
    UnsupportedUnit.
    If this is None, the unit is unspecified.
    """
    if self._metadata is None:
      return None
    return self._metadata.unit

  @property
  def null_values(self) -> tuple[str, ...] | None:
    """Values which should be considered to mean null.

    These are always stored as strings rather than the value type.
    They may not correspond to valid values for the primitive
    attribute.

    If this is None, then the null values are unspecified.
    """
    if self._metadata is None:
      return None
    return self._metadata.null_values

  @property
  def _version(self) -> int | None:
    if self._metadata is None:
      return None
    return self._metadata.version

  def to_json(self) -> str:
    """Convert the AttributeKey to JSON.

    Returns
    -------
    str
      The json string used to access this attribute.
    """
    metadata = self._metadata
    if metadata is not None:
      result = {}
      if self._version == 1:
        result["s"] = metadata.semantic
        result["t"] = metadata.data_type
        result["u"] = metadata.unit
        result["n"] = self.name
      elif self._version in (2, 3):
        result[_VERSION_KEY] = self._version
        result[_SEMANTIC_KEY] = metadata.semantic
        result[_TYPE_KEY] = _DTYPE_TO_STRING[metadata.data_type]
        # pylint: disable=protected-access
        result[_UNIT_KEY] = metadata.unit._to_serialisation_string()
        result[_NAME_KEY] = self.name

        if self._version == 3:
          result[_NULL_VALUES_KEY] = [
            str(value) for value in metadata.null_values
          ]

      return json.dumps(result, separators=(",", ":"), sort_keys=True)
    return self.name

  @classmethod
  def create_with_metadata(
      cls,
      name: str,
      data_type: type,
      *,
      unit: UnsupportedUnit | DistanceUnit | AngleUnit | None = None,
      null_values: tuple[str, ...] | None = None,
      semantic: str | None = None
      ) -> typing.Self:
    """Create an AttributeKey with metadata.

    Parameters
    ----------
    name
      Name of the primitive attribute.
    data_type
      Ctypes type of data stored by the attribute or int, float, bool or str.
      See Notes for how Python types are mapped to ctypes types.
      This will restrict the values in the array for this attribute to have
      the specified type.
    unit
      The unit of the data. If not specified, the unit will be unknown.
      Typically, if this is specified, it should be a member of the
      DistanceUnit or AngleUnit enums. Though other units can be represented
      by passing UnsupportedUnit, this is not recommended.
    null_values
      Tuple of values the data should treat as null.
    semantic
      By default, this will be set appropriately based on the data_type.
      Typically, this should be left to the default.
      If this is set to a semantic not recognised by the application, the
      application may fail to read the values.

    Notes
    -----
    The below table defines how Python types passed as the data_type are
    mapped to ctypes types:

    +-------------+-------------+
    | Python type | Ctypes type |
    +=============+=============+
    | int         | c_int32     |
    +-------------+-------------+
    | float       | c_double    |
    +-------------+-------------+
    | bool        | c_bool      |
    +-------------+-------------+
    | str         | c_char_p    |
    +-------------+-------------+
    """
    result = cls(name)

    if data_type in cls._PYTHON_TYPE_TO_C_TYPE:
      data_type = cls._PYTHON_TYPE_TO_C_TYPE[data_type]

    if data_type not in cls.SUPPORTED_DATA_TYPES:
      raise ValueError(f"Unsupported type for AttributeKey: {data_type}")

    if semantic is None:
      if data_type in (
          ctypes.c_uint8, ctypes.c_int8,
          ctypes.c_uint16, ctypes.c_int16,
          ctypes.c_uint32, ctypes.c_int32,
          ctypes.c_uint64, ctypes.c_int64,
          ctypes.c_double, ctypes.c_float):
        semantic = "Point attribute (numeric)"
      elif data_type == ctypes.c_char_p:
        semantic = "Point attribute (text)"
      elif data_type == ctypes.c_bool:
        semantic = "Point attribute (boolean)"
      else:
        raise ValueError(
          f"Unsupported type for AttributeKey: {data_type}"
        )

    if unit is None:
      actual_unit = UnsupportedUnit("unknown")
    elif isinstance(unit, str):
      actual_unit = _any_unit_from_string(unit)
    else:
      actual_unit = unit

    if null_values is None:
      actual_null_values = tuple()
    else:
      actual_null_values = tuple(str(value) for value in null_values)

    metadata = cls._AttributeKeyMetadata(
      data_type=data_type,
      semantic=semantic,
      unit=actual_unit,
      null_values=actual_null_values
    )
    result._metadata = metadata
    return result

  @classmethod
  def from_json(cls, json_string: str) -> Self:
    """Create an AttributeKey from a JSON string containing the name.

    Parameters
    ----------
    json_string
      The JSON string containing the name.

    Returns
    -------
    Self
      An instance of this class loaded from the string.
    """
    # If it starts with a curly bracket, it must be an
    # mdlC_Attribute based attribute.
    if json_string.startswith("{"):
      result = json.loads(json_string)

      version = result[_VERSION_KEY]
      if version > 3:
        raise ValueError(
          f"Cannot read attribute of version: {version}. "
          "Only version 3 and lower is supported."
        )
      semantic = result[_SEMANTIC_KEY]
      data_type = _STRING_TO_DTYPE.get(result["t"], type(None))
      unit = _any_unit_from_string(result[_UNIT_KEY])
      if version == 1:
        name = result["n"]
      else:
        name = result[_NAME_KEY]
      null_values = tuple()
      if version >= 2:
        null_values = tuple(result[_NULL_VALUES_KEY])

      result = cls(name)
      result._metadata = cls._AttributeKeyMetadata(
        data_type=data_type,
        semantic=semantic,
        unit=unit,
        null_values=null_values,
        version=version
      )
      return result
    else:
      return cls(
        json_string
      )
