"""A mixin which adds support for repeating fields.

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

import typing

from .base_message import BaseMessage

if typing.TYPE_CHECKING:
  from collections.abc import Sequence


class RepeatingField:
  """Represents a repeating field in the structure of a message.

  A repeating field repeats values of the specified type until the end of the
  message.

  Parameters
  ----------
  element_type
    The type of elements in the repeating field.
  """
  def __init__(self, element_type: typing.Any) -> None:
    self.__element_type = element_type

  @property
  def element_type(self) -> type:
    """The type of the elements stored in this repeating field."""
    return self.__element_type


class MessageWithRepeatingField(BaseMessage):
  """A message which can include a repeating field.

  A repeating field is a field placed at the end of the message which includes
  values of a type defined by repeating_field_type until the end of the message.
  This is similar to a list, except that the length of the sequence is not
  in the message because the sequence ends when the message ends.
  """
  def __init__(self) -> None:
    self.__values: Sequence = []
    """Backing field for the repeating field values."""

  @classmethod
  def repeating_field_type(cls):
    """The type of values stored in the repeating field.

    If None, this message does not have a repeating field.
    """
    return None

  @classmethod
  def message_structure(cls) -> dict[str, typing.Any]:
    message_structure = super().message_structure()
    repeating_field_type = cls.repeating_field_type()

    if cls.repeating_field_type() is not None:
      message_structure[
        "repeating_field_values"
      ] = RepeatingField(repeating_field_type)
    return message_structure

  @property
  def repeating_field_values(self) -> Sequence:
    """The values of the repeating field.

    Every value in the sequence must have the type defined by
    repeating_field_type otherwise a MalformedMessageError will be raised
    when the message is sent.

    Raises
    ------
    TypeError
      If this subclass has a repeating_field_type of None.
      This is the default repeating field type.

    Examples
    --------
    The property name "repeating_field_values" is rarely a good name for the
    repeating fields, so it is often best to define a new name for the
    property similar to below:

    >>> class Group(SubMessage):
    ...   '''Message representing a group of people.'''
    ...   division: str
    ...
    ...   @classmethod
    ...   def repeating_field_type(cls):
    ...     return str
    ...
    ...   @property
    ...   def participants(self) -> Sequence[str]:
    ...     '''The participants of the group.'''
    ...     return self.repeating_field_values
    ...
    ...   @participants.setter
    ...   def participants(self, value: Sequence[str]):
    ...     self.repeating_field_values = value
    """
    if self.repeating_field_type() is None:
      raise TypeError(
        f"This {type(self).__name__} does not have a repeating field.")
    return self.__values

  @repeating_field_values.setter
  def repeating_field_values(self, new_values: Sequence):
    if self.repeating_field_type() is None:
      raise TypeError(
        f"This {type(self).__name__} does not have a repeating field.")
    self.__values = new_values
