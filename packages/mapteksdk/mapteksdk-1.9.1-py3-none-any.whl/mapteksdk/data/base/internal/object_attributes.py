"""Classes for keeping track of object attributes."""
###############################################################################
#
# (C) Copyright 2025, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

from collections.abc import Callable, Iterable
import ctypes
import datetime
import typing
import warnings

from ....internal.util import default_type_error_message

if typing.TYPE_CHECKING:
  from ....capi import DataEngineApi

  ObjectAttributeTypes = (
    None | ctypes.c_bool | ctypes.c_int8 | ctypes.c_uint8
    | ctypes.c_int16 | ctypes.c_uint16 | ctypes.c_int32 | ctypes.c_uint32
    | ctypes.c_int64 | ctypes.c_uint64 | ctypes.c_float | ctypes.c_double
    | ctypes.c_char_p | datetime.datetime | datetime.date
  )
  ObjectAttributeDataTypes = type[ObjectAttributeTypes]
  """Alias for the union of valid data types for object attributes."""

_object_attribute_table: dict[int, ObjectAttributeDataTypes] = {
  1: type(None), 2: ctypes.c_bool, 3: ctypes.c_int8,
  4: ctypes.c_uint8, 5: ctypes.c_int16, 6: ctypes.c_uint16,
  7: ctypes.c_int32, 8: ctypes.c_uint32, 9: ctypes.c_int64,
  10: ctypes.c_uint64, 11: ctypes.c_float, 12: ctypes.c_double,
  13: ctypes.c_char_p, 14: datetime.datetime, 15: datetime.date,
}
"""Dictionary which maps object attribute type IDs to Python types."""

_INTEGER_OBJECT_ATTRIBUTE_TYPES = (
  ctypes.c_int8,
  ctypes.c_uint8,
  ctypes.c_int16,
  ctypes.c_uint16,
  ctypes.c_int32,
  ctypes.c_uint32,
  ctypes.c_int64,
  ctypes.c_uint64
)

_FLOAT_OBJECT_ATTRIBUTE_TYPES = (
  ctypes.c_float,
  ctypes.c_double
)

class UnsupportedObjectAttributeTypeError(Exception):
  """Error raised if an object attribute has an unsupported type.

  A newer version of the SDK will be required to read the object attribute.
  """


class ObjectAttributeDoesNotExistError(Exception):
  """Error raised if an object attribute does not exist."""


class ObjectAttribute:
  """Holds data for an object attribute."""
  name : str
  """The name of the object attribute."""
  id : int
  """The ID of the object attribute."""
  dtype : ObjectAttributeDataTypes
  """The data type of the object attribute."""

  def __init__(
    self,
    name: str,
    attribute_id: int,
    dtype: ObjectAttributeDataTypes,
    get_value: Callable[[], typing.Any]
  ):
    self.name = name
    self.id = attribute_id
    self.dtype = dtype
    self._value = None
    self.__get_value = get_value

  @property
  def value(self) -> ObjectAttributeTypes:
    """The data stored in this attribute."""
    if self.dtype is type(None):
      return None
    if self._value is None:
      self._value = self.__get_value()
    return self._value


class ObjectAttributeDictionary:
  """A dictionary-like object which holds object attributes.

  Parameters
  ----------
  get_lock
    A function which gets the lock on the object to manage the object
    attributes for.
    This should raise an error if the object is closed.
  data_engine_api
    DataEngine API to use to for accessing object attributes.
  """
  def __init__(
    self,
    get_lock: Callable[[], typing.Any],
    data_engine_api: DataEngineApi
  ):
    self.__get_lock = get_lock
    self.__data_engine = data_engine_api
    self.__attributes: dict[str, ObjectAttribute] = {}
    attribute_ids = data_engine_api.GetAttributeList(get_lock())
    for attribute_id in attribute_ids:
      try:
        attribute = self.__load(attribute_id)
      except ObjectAttributeDoesNotExistError:
        warnings.warn(
          "Skipping non-existent object attribute. "
          "This may indicate the object is corrupt.",
          RuntimeWarning
        )
        continue
      except UnsupportedObjectAttributeTypeError:
        warnings.warn(
          "Skipping unsupported object attribute. "
          "A newer version of the SDK is required to read object attributes of "
          "this type.",
          RuntimeWarning
        )
        continue

      self.__attributes[attribute.name] = attribute

  def __len__(self) -> int:
    return len(self.__attributes)

  def __getitem__(self, name: str) -> ObjectAttribute:
    """Get object attribute by name."""
    return self.__attributes[name]

  def __contains__(self, name: typing.Any) -> bool:
    """Check if this object contains an attribute with the given name."""
    return name in self.__attributes

  def names(self) -> Iterable[str]:
    """Get a list containing all of the names of object attributes."""
    return self.__attributes.keys()

  @typing.overload
  def create(
    self,
    name: str,
    data_type: type[None],
    value: None,
  ):
    ...

  @typing.overload
  def create(
    self,
    name: str,
    data_type: type[ctypes.c_bool],
    value: bool,
  ):
    ...

  @typing.overload
  def create(
    self,
    name: str,
    data_type: type[
      ctypes.c_int8
      | ctypes.c_uint8
      | ctypes.c_int16
      | ctypes.c_uint16
      | ctypes.c_int32
      | ctypes.c_uint32
      | ctypes.c_int64
      | ctypes.c_uint64
    ],
    value: int,
  ):
    ...

  @typing.overload
  def create(
    self,
    name: str,
    data_type: type[ctypes.c_float | ctypes.c_double],
    value: float,
  ):
    ...

  @typing.overload
  def create(
    self,
    name: str,
    data_type: type[datetime.datetime],
    value: datetime.datetime,
  ):
    ...


  @typing.overload
  def create(
    self,
    name: str,
    data_type: type[datetime.date],
    value: datetime.date,
  ):
    ...

  @typing.overload
  def create(
    self,
    name: str,
    data_type: ObjectAttributeDataTypes,
    value: str | int | float | bool | datetime.datetime | datetime.date | None,
  ):
    ...

  def create(
    self,
    name: str,
    data_type: ObjectAttributeDataTypes,
    value: str | int | float | bool | datetime.datetime | datetime.date | None,
  ):
    """Create a new object attribute."""
    self.__attributes[name] = self.__create(
      name,
      data_type,
      value,
    )

  def delete(self, name: str) -> bool:
    """Delete the object attribute with `name`.

    Raises
    ------
    RuntimeError
      If the attribute could not be deleted.

    Returns
    -------
    bool
      True if an attribute was deleted.
      False if there was no attribute with the given name to delete.
    """
    attribute = self.__attributes.get(name, None)
    if attribute is None:
      return False
    self.__data_engine.DeleteAttribute(self.__get_lock(), attribute.id)
    del self.__attributes[name]
    return True

  def delete_all(self):
    """Delete all object attributes in this dictionary.

    Raises
    ------
    RuntimeError
      If the attributes could not be deleted.
    """
    self.__data_engine.DeleteAllAttributes(self.__get_lock())
    self.__attributes.clear()

  def __raise_if_name_invalid(self, name: str):
    """Raise an error if `name` is not valid for an object attribute."""
    if name.strip() != name:
      raise ValueError(
        "Attribute names must not contain leading or trailing whitespace. "
        f"Invalid attribute name: '{name}'."
      )
    if name == "":
      raise ValueError(
        "Attribute name must not be empty."
      )

  def __load(
    self,
    attribute_id: int,
  ) -> ObjectAttribute:
    """Load the meta data for the object attribute with the given id.

    Returns
    -------
    ObjectAttribute
      The object attribute loaded from the parameters.

    Raises
    ------
    UnsupportedObjectAttributeTypeError
      If the attribute cannot be read due to its data type not being supported
      by the SDK.
    """
    name = self.__data_engine.GetAttributeName(attribute_id)
    data_type_id = self.__data_engine.GetAttributeValueType(
      self.__get_lock(),
      attribute_id
    )
    if data_type_id == 0:
      raise ObjectAttributeDoesNotExistError(
        f"No object attribute with name: {name}."
      )
    try:
      data_type = _object_attribute_table[data_type_id]
    except KeyError as error:
      raise UnsupportedObjectAttributeTypeError(
        f"Unrecognised object attribute type id: {data_type_id}. "
        "A newer version of the SDK will be required to read this attribute."
      ) from error

    type_to_function: dict[ObjectAttributeDataTypes, Callable] = {
      ctypes.c_bool: self.__data_engine.GetAttributeValueBool,
      ctypes.c_int8: self.__data_engine.GetAttributeValueInt8s,
      ctypes.c_uint8: self.__data_engine.GetAttributeValueInt8u,
      ctypes.c_int16: self.__data_engine.GetAttributeValueInt16s,
      ctypes.c_uint16: self.__data_engine.GetAttributeValueInt16u,
      ctypes.c_int32: self.__data_engine.GetAttributeValueInt32s,
      ctypes.c_uint32: self.__data_engine.GetAttributeValueInt32u,
      ctypes.c_int64: self.__data_engine.GetAttributeValueInt64s,
      ctypes.c_uint64: self.__data_engine.GetAttributeValueInt64u,
      ctypes.c_float: self.__data_engine.GetAttributeValueFloat32,
      ctypes.c_double: self.__data_engine.GetAttributeValueFloat64,
      ctypes.c_char_p: self.__data_engine.GetAttributeValueString,
      datetime.datetime: self.__data_engine.GetAttributeValueDateTime,
      datetime.date: self.__data_engine.GetAttributeValueDate,
    }

    function = type_to_function.get(data_type, None)
    if function is None:
      def load_unsupported_type(_, _0):
        raise ValueError(
          f'The type of the attribute ({data_type}) is an unsupported type.')
      function = load_unsupported_type

    return ObjectAttribute(
      name,
      attribute_id,
      data_type,
      lambda: function(self.__get_lock(), attribute_id)
    )

  @typing.overload
  def __create(
    self,
    name: str,
    data_type: type[None],
    value: None,
  ) -> ObjectAttribute:
    ...

  @typing.overload
  def __create(
    self,
    name: str,
    data_type: type[ctypes.c_bool],
    value: bool,
  ) -> ObjectAttribute:
    ...

  @typing.overload
  def __create(
    self,
    name: str,
    data_type: type[
      ctypes.c_int8
      | ctypes.c_uint8
      | ctypes.c_int16
      | ctypes.c_uint16
      | ctypes.c_int32
      | ctypes.c_uint32
      | ctypes.c_int64
      | ctypes.c_uint64
    ],
    value: int,
  ) -> ObjectAttribute:
    ...

  @typing.overload
  def __create(
    self,
    name: str,
    data_type: type[ctypes.c_float | ctypes.c_double],
    value: float,
  ) -> ObjectAttribute:
    ...

  @typing.overload
  def __create(
    self,
    name: str,
    data_type: type[datetime.datetime],
    value: datetime.datetime,
  ) -> ObjectAttribute:
    ...


  @typing.overload
  def __create(
    self,
    name: str,
    data_type: type[datetime.date],
    value: datetime.date,
  ) -> ObjectAttribute:
    ...

  @typing.overload
  def __create(
    self,
    name: str,
    data_type: ObjectAttributeDataTypes,
    value: str | int | float | bool | datetime.datetime | datetime.date | None,
  ) -> ObjectAttribute:
    ...

  def __create(
    self,
    name: str,
    data_type: ObjectAttributeDataTypes,
    value: str | int | float | bool | datetime.datetime | datetime.date | None,
  ) -> ObjectAttribute:
    """Create a new object attribute."""
    self.__raise_if_name_invalid(name)

    attribute_id = self.__data_engine.GetAttributeId(name)

    if data_type is ctypes.c_bool:
      value = bool(value)
    elif data_type in _INTEGER_OBJECT_ATTRIBUTE_TYPES:
      try:
        value = int(value) # type: ignore
      except ValueError:
        raise TypeError(
          default_type_error_message(
            "value",
            value,
            int
          )
        ) from None
    elif data_type in _FLOAT_OBJECT_ATTRIBUTE_TYPES:
      try:
        value = float(value) # type: ignore
      except ValueError:
        raise TypeError(
          default_type_error_message(
            "value",
            value,
            float
          )
        ) from None
    elif data_type in (str, ctypes.c_char_p):
      if not isinstance(value, str):
        raise TypeError(
          default_type_error_message(
            "value",
            value,
            str
          )
        )
    elif data_type is datetime.datetime:
      if not isinstance(value, datetime.datetime):
        raise TypeError(default_type_error_message(
            "value",
            value,
            datetime.datetime
          ))
    elif data_type is datetime.date:
      if not isinstance(value, datetime.date):
        raise TypeError(
          default_type_error_message(
            "value",
            value,
            datetime.date
          )
        )
    elif data_type is type(None):
      if value is not None:
        raise TypeError(
          default_type_error_message(
            "value",
            value,
            type(None)
          )
        )
    else:
      raise TypeError(f"Unsupported dtype: \"{data_type}\".")

    try:
      # Try to handle the 'easy' data types. The data types in the
      # dictionary don't require any extra handling on the Python side.
      # :TRICKY: This dictionary can't be a property of the class because
      # self._data_engine_api() will raise an error if there is no connected
      # application.
      dtype_to_c_api_function: dict[
          type, Callable] = {
        type(None) : self.__data_engine.SetAttributeNull,
        ctypes.c_char_p : self.__data_engine.SetAttributeString,
        str : self.__data_engine.SetAttributeString,
        ctypes.c_bool : self.__data_engine.SetAttributeBool,
        bool : self.__data_engine.SetAttributeBool,
        ctypes.c_int8 : self.__data_engine.SetAttributeInt8s,
        ctypes.c_uint8 : self.__data_engine.SetAttributeInt8u,
        ctypes.c_int16 : self.__data_engine.SetAttributeInt16s,
        ctypes.c_uint16 : self.__data_engine.SetAttributeInt16u,
        ctypes.c_int32 : self.__data_engine.SetAttributeInt32s,
        ctypes.c_uint32 : self.__data_engine.SetAttributeInt32u,
        ctypes.c_int64 : self.__data_engine.SetAttributeInt64s,
        ctypes.c_uint64 : self.__data_engine.SetAttributeInt64u,
        ctypes.c_float : self.__data_engine.SetAttributeFloat32,
        ctypes.c_double : self.__data_engine.SetAttributeFloat64,
        datetime.datetime : self.__data_engine.SetAttributeDateTime,
        datetime.date : self.__data_engine.SetAttributeDate,
      }

      try:
        result = dtype_to_c_api_function[data_type](
          self.__get_lock(), attribute_id, value)
      except ctypes.ArgumentError as exception:
        raise TypeError(f"Cannot convert {value} of type {type(value)} to "
                        f"type: {data_type}.") from exception

      if not result:
        message = self.__data_engine.ErrorMessage()
        raise RuntimeError(f"Failed to save attribute: '{name}' on object "
                          f"'{attribute_id}'. {message}")
    except KeyError:
      raise TypeError(f"Unsupported dtype: \"{data_type}\".") from None

    return ObjectAttribute(
      name,
      attribute_id,
      data_type,
      lambda: value
    )
