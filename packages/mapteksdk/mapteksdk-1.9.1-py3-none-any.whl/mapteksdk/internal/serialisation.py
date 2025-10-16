"""Classes designed to be serialised in MCP messages.

The classes declared in this file must not depend on
the data subpackage.

Warnings
--------
Vendors and clients should not develop scripts or applications against
this package. The contents may change at any time without warning.
"""
###############################################################################
#
# (C) Copyright 2022, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

import json
import typing

from mapteksdk.internal.comms import (
  InlineMessage,
  SubMessage,
  Int16s,
  Int32s,
  Int8u,
  Int32u,
  Int64u,
  Double,
)
from mapteksdk.internal.qualifiers import QualifierSet

class Icon:
  """This type should be used in the definition of a message where an icon is
  expected.
  """
  storage_type = str

  def __init__(self, name=''):
    self.name = name

  @classmethod
  def convert_from(cls, value):
    """Convert from the underlying value to this type."""
    assert isinstance(value, cls.storage_type)
    return cls(value)

  def convert_to(self):
    """Convert the icon name to a value of the storage type (str).

    Returns
    -------
      A str which is the name of the icon.

    Raises
    ------
    TypeError
      If value is not a Icon or str, i.e the value is not an icon.
    """
    return self.name

  @classmethod
  def okay(cls) -> "typing.Self":
    """The okay icon."""
    return cls("Okay")

  @classmethod
  def plus(cls) -> "typing.Self":
    """The plus icon."""
    return cls("Add")

  @classmethod
  def minus(cls) -> "typing.Self":
    """The minus icon."""
    return cls("Remove")

  @classmethod
  def warning(cls) -> "typing.Self":
    """The warning icon."""
    return cls("Warning")

  @classmethod
  def information(cls) -> "typing.Self":
    """The information icon."""
    return cls("Information")

  def __eq__(self, value: object) -> bool:
    return isinstance(value, type(self)) and value.name == self.name

  def __hash__(self) -> Int16s:
    return hash(self.name)

class JsonValue:
  """This type should be used in the definition of a Message where JSON is
  expected.
  """

  storage_type = str

  def __init__(self, value):
    self.value: typing.Any = value

  def __str__(self):
    return str(self.value)

  @classmethod
  def convert_from(cls, value):
    """Convert from the underlying value to this type."""
    assert isinstance(value, cls.storage_type)
    return cls(json.loads(value))

  def convert_to(self):
    """Convert the value to the storage type.

    Returns
    -------
      The serialised value to a JSON formatted str.

    Raises
    ------
    TypeError
      If value is not a JsonValue or not suitable for seralisation to JSON
      with Python's default JSON encoder.
    """
    return json.dumps(self.value)

class KeyBinding(InlineMessage):
  """A key binding for a transaction."""
  is_valid: bool
  is_hold_and_click: bool
  key: Int32u # keyE
  modifiers: Int32u # keyE_Modifier

class Context(SubMessage):
  """Transaction context object."""
  active_view_id: Int64u
  active_view_name: str
  associated_view_ids: set[Int64u]
  workspace_views: set[Int64u]
  finish_hint: Int8u # uiC_Outcome (Enum)
  selection_contains_objects: bool
  selection_type: Int32s # picE_SelectionType
  # A datetime is represented as two floats - a day number and seconds
  # since midnight.
  # Converting these to/from a Python datetime is non-trivial, so just
  # pretend it is two floats.
  selection_last_change_time_day_number: Double
  selection_last_change_time_seconds_since_midnight: Double
  key_modifiers: Int32u # keyE_Modifiers
  key_binding: KeyBinding
  scones: QualifierSet
  cookies: QualifierSet

  @classmethod
  def default_context(cls) -> "Context":
    """Return a context filled with default values."""
    context = cls()

    default_key_binding = KeyBinding()
    default_key_binding.is_valid = False
    default_key_binding.is_hold_and_click = False
    default_key_binding.key = 0
    default_key_binding.modifiers = 0

    scones = QualifierSet()
    scones.values = []

    cookies = QualifierSet()
    cookies.values = []

    context.active_view_id = 0
    context.active_view_name = ""
    context.associated_view_ids = set()
    context.workspace_views = set()
    context.finish_hint = 43 # "Success"
    context.selection_contains_objects = False
    context.selection_type = 0
    context.selection_last_change_time_day_number = 0.0
    context.selection_last_change_time_seconds_since_midnight = 0.0
    context.key_modifiers = 0
    context.key_binding = default_key_binding
    context.scones = scones
    context.cookies = cookies

    return context


class FixedInteger16Mixin:
  """A base-type for use with an enumeration that is a 16-bit integer.

  This class exists because ctypes.c_int16 can't be used as the base
  type of the enumerations due to having its own metaclass.

  To define an enumeration using this type:
  >>> import enum
  >>> class Example(FixedInteger16Mixin, enum.IntEnum)
  ...   PRIMARY = 1
  ...   SECONDARY = 2
  ...   TERTIARY = 3
  """
  storage_type: typing.ClassVar = Int16s

  @classmethod
  def convert_from(cls, value):
    """Converts the underlying value to the enumeration type."""
    return cls(value)

  def convert_to(self) -> Int16s:
    """Convert the enumeration to the value that serialised."""
    return self.value


class FixedInteger32Mixin:
  """A base-type for use with an enumeration that is a 32-bit integer.

  This class exists because ctypes.c_int132 can't be used as the base
  type of the enumerations due to having its own metaclass.

  To define an enumeration using this type:
  >>> import enum
  >>> class Example(FixedInteger32Mixin, enum.IntEnum)
  ...   PRIMARY = 1
  ...   SECONDARY = 2
  ...   TERTIARY = 3
  """
  storage_type: typing.ClassVar = Int32s

  @classmethod
  def convert_from(cls, value):
    """Converts the underlying value to the enumeration type."""
    return cls(value)

  def convert_to(self) -> Int32s:
    """Convert the enumeration to the value that serialised."""
    return self.value


class FixedInteger32uMixin:
  """A base-type for use with an enumeration that is a 32-bit unsigned integer.

  This class exists because Int32u can't be used as the base
  type of the enumerations due to having its own metaclass.

  To define an enumeration using this type:
  >>> import enum
  >>> class Example(FixedInteger32Mixin, enum.IntEnum)
  ...   PRIMARY = 1
  ...   SECONDARY = 2
  ...   TERTIARY = 3
  """
  storage_type: typing.ClassVar = Int32u

  @classmethod
  def convert_from(cls, value):
    """Converts the underlying value to the enumeration type."""
    return cls(value)

  def convert_to(self) -> Int32u:
    """Convert the enumeration to the value that serialised."""
    return self.value
