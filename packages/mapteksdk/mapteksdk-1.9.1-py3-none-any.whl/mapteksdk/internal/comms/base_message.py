"""Base class for Message, Request, SubMessage and InlineMessage.

Warnings
--------
Vendors and clients should not develop scripts or applications against
this package. The contents may change at any time without warning.
"""
###############################################################################
#
# (C) Copyright 2024, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

from collections.abc import Sequence
import typing

from .errors import DataTypeNotSupported

class List:
  """Represents a list in the structure of a message.

  A type hint in a message of a list is converted into this class when the
  structure of the message is read. This ensures the message sending
  infrastructure does not need to understand the complexities of type hinting
  lists.
  """
  def __init__(self, element_type: typing.Any) -> None:
    if isinstance(element_type, typing.TypeVar):
      raise DataTypeNotSupported(
        "The type of a list must be specified."
      )
    self.__element_type = element_type

  @property
  def element_type(self) -> type:
    """The type of the elements stored in this list.

    The messaging system requires that all elements in a list have the same
    type.
    """
    return self.__element_type

  def __eq__(self, value: object) -> bool:
    return (
      isinstance(value, type(self))
      and value.element_type == self.element_type
    )

  def __hash__(self) -> int:
    return hash(self.element_type)


class Set:
  """Represents a set in the structure of a message.

  A type hint in a message of a set is converted into this class when the
  structure of the message is read. This ensures the message sending
  infrastructure does not need to understand the complexities of type hinting
  sets.
  """
  def __init__(self, element_type: typing.Any) -> None:
    if isinstance(element_type, typing.TypeVar):
      raise DataTypeNotSupported(
        "The type of a set must be specified."
      )
    self.__element_type = element_type

  @property
  def element_type(self) -> type:
    """The type of the elements stored in this list.

    The messaging system requires that all elements in a set have the same
    type.
    """
    return self.__element_type

  def __eq__(self, value: object) -> bool:
    return (
      isinstance(value, type(self))
      and value.element_type == self.element_type
    )

  def __hash__(self) -> int:
    return hash(self.element_type)


class Optional:
  """Represents an optional value in the structure of a message.

  A type hint in a message of typing.Optional is converted into this class
  when the structure of the message is read. This ensures the message sending
  infrastructure does not need to understand the complexities of type hinting
  optionals.
  """
  def __init__(self, optional_type: typing.Any):
    self.__optional_type = optional_type

  @property
  def optional_type(self) -> type:
    """The optional type.

    A value of this type can be an instance of this type or None.
    """
    return self.__optional_type

  def __eq__(self, value: object) -> bool:
    return (
      isinstance(value, type(self))
      and value.optional_type == self.optional_type
    )

  def __hash__(self) -> int:
    return hash(self.optional_type)


class Tuple:
  """Represents a tuple in the structure of a message.

  A type hint in a message of a tuple is converted into this class when the
  structure of the message is read. This ensures the message sending
  infrastructure does not need to understand the complexities of type hinting
  tuples.
  """
  def __init__(self, *args: typing.Any) -> None:
    if len(args) > 0 and args[-1] == ...:
      raise DataTypeNotSupported(
        "Variable length tuples are not supported."
      )
    self.__element_types = args

  @property
  def element_types(self) -> Sequence[typing.Any]:
    """The type of the elements stored in this tuple.

    The returned sequence has one element for each item in the tuple.
    """
    return self.__element_types

  def __eq__(self, value: object) -> bool:
    return (
      isinstance(value, type(self))
      and len(self.element_types) == len(value.element_types)
      and all(
        my_element == other_element
        for my_element, other_element
        in zip(self.element_types, value.element_types))
    )

  def __hash__(self) -> int:
    return hash(self.element_types)


class Union:
  """Represents a union in the structure of a message.

  If a message needs to be received, then it cannot include union types.
  Attempting to read the value of a union type will result in an error.

  A type hint of a union type is converted into this class when the structure
  of the message is read. This ensures the message sending
  infrastructure does not need to understand the complexities of type hinting
  unions.
  """
  def __init__(self, *args: typing.Any) -> None:
    if len(args) < 2:
      raise DataTypeNotSupported(
        "Unions must include at least two types."
      )
    self.__union_types = args

  @property
  def union_types(self) -> Sequence[typing.Any]:
    """The possible types of the value stored in this union.

    The value can be one of any of these types.
    """
    return self.__union_types

  def __eq__(self, value: object) -> bool:
    return (
      isinstance(value, type(self))
      and len(self.union_types) == len(value.union_types)
      and all(
        my_element == other_element
        for my_element, other_element
        in zip(self.union_types, value.union_types))
    )

  def __hash__(self) -> int:
    return hash(self.union_types)


class BaseMessage:
  """Base class for message classes.

  Derived types specify the fields that make up the message using instance
  variable annotations (PEP-526), the general form of which is:
    name: type
    name: type = value

  The name must be a valid Python identifier. It is not used by the
  communications system, so should be selected based on code clarity.
  The type should be:

  * bool
  * str
  * Primitives (For integers / floats. This is defined in primitives.py).
  * SubMessage
  * InlineMessage
  * typing.Union
  * typing.Optional

  If the name starts with an underscore, the field will be ignored by the
  communication system.

  Warnings
  --------
  Subclasses of this class must not be defined in classes which have
  'from __future__ import annotations' at the top of the file. This causes
  the type hints to be stringified at runtime, which the comms package cannot
  handle.
  """
  @classmethod
  def message_structure(cls) -> dict[str, typing.Any]:
    """Read the structure of this message from the type hints.

    Returns
    -------
    dict[str, typing.Any]
      A dictionary where the key is the name of each property and
      the value is its type.
      For primitive types, the value will be str, bool or one of the types
      defined in primitives.py.
      For sequence types, this will be the List, Set or Tuple class defined
      in this class.
      Otherwise this will be the type read from the annotations.

    Raises
    ------
    DataTypeNotSupported
      If one of the data types in the type hints is not supported.
    """
    # Determine the list of fields of the message from the annotations.
    annotations = getattr(cls, '__annotations__', {})

    message_structure = {}

    for field_name, field_type in annotations.items():
      origin = getattr(field_type, '__origin__', field_type)

      if not cls._include_in_message_structure(field_name, origin):
        continue


      message_structure[field_name] = cls.__convert_to_message_structure_type(
        field_type,
        origin
      )

    return message_structure

  @classmethod
  def _include_in_message_structure(
      cls,
      field_name: str,
      origin: typing.Any
    ) -> bool:
    """Determine if `field_name` should be included in the message structure.

    Parameters
    ----------
    field_name
      The name of the field.
    origin
      The origin type of the field.

    Returns
    -------
    bool
      True if this field is part of the message structure.
      False if it is not part of the message structure.
    """
    if field_name.startswith("_"):
      return False

    if origin is typing.ClassVar:
      return False

    return True

  @classmethod
  def __convert_to_message_structure_type(
      cls,
      field_type: typing.Any,
      origin: typing.Any
    ) -> typing.Any:
    """Convert the field type to the message structure type.

    Parameters
    ----------
    field_type
      The field type to convert to a structure type.
    origin
      The origin of the field type.

    Returns
    -------
    Any
      The structure type for field_type.
    """
    if origin is list or origin is set:
      return cls.__convert_list_or_set(field_type, origin)

    if origin is tuple:
      return cls.__convert_tuple(field_type)

    if origin is typing.Union:
      return cls.__convert_union(field_type)

    return cls.__convert_plain_type(field_type)

  @classmethod
  def __convert_plain_type(
      cls,
      field_type: typing.Any
    ) -> typing.Any:
    """Convert a plain type to a message structure type.

    This is the default handling for a field.

    Parameters
    ----------
    field_type
      The type of the field, as read from the type hints.

    Returns
    -------
    Any
      The structure type for field_type.
    """
    return field_type

  @classmethod
  def __convert_tuple(
      cls,
      field_type
    ) -> Tuple:
    """Convert a tuple to a message structure type.

    Parameters
    ----------
    field_type
      The type of the field, as read from the type hints. This is assumed to
      be tuple with its __args__ populated with the contents of the tuple.

    Returns
    -------
    Tuple
      A tuple object representing the structure.
    """
    return Tuple(
      *(cls.__convert_to_message_structure_type(
        arg, getattr(arg, "__origin__", None))
      for arg in getattr(field_type, "__args__", tuple()))
    )

  @classmethod
  def __convert_union(
    cls,
    field_type
  ) -> typing.Union[Union, Optional]:
    """Convert a typing.Union to a message structure type.

    Parameters
    ----------
    field_type
      The type of the field, as read from the type hints. This is assumed to
      be tuple with its __args__ populated with the contents of the tuple.

    Returns
    -------
    Union
      A union object indicating which values can be placed in the message
      at that location.
    Optional
      If the union includes None.
    """
    args = getattr(field_type, "__args__", tuple())

    if type(None) in args:
      if len(args) != 2:
        raise DataTypeNotSupported(
          "Optional only supports one type."
        )
      return Optional(
        cls.__convert_to_message_structure_type(
          args[0],
          getattr(args[0], "__origin__", None)
        )
      )
    return Union(
      *(cls.__convert_to_message_structure_type(
        arg, getattr(arg, "__origin__", None))
      for arg in args))

  @classmethod
  def __convert_list_or_set(
    cls,
    field_type: typing.Any,
    origin: typing.Any
  ) -> typing.Union[List, Set]:
    """Convert a list or set to a message structure type.

    Parameters
    ----------
    field_type
      The type of the field, as read from the type hints. This is assumed to
      be list or set with a single subtype in __args__ defining the type of
      values stored in the list or set.
    origin
      The list type if this is a list and the set type if this is a set.

    Returns
    -------
    Any
      The structure type for field_type.

    Raises
    ------
    ValueError
      If field_type has more than 1 subtype in its __args__.
    """
    display_type = List if origin is list else Set
    args = getattr(field_type, "__args__", tuple())
    # The type of the elements comes from the arguments of the type.
    if len(args) != 1:
      raise DataTypeNotSupported(
          f'The type {field_type} should only specify one type '
          f'for the contents.')

    child_field_type = args[0]
    child_origin = getattr(child_field_type, "__origin__", None)
    return display_type(
      cls.__convert_to_message_structure_type(
        child_field_type,
        child_origin
      )
    )
