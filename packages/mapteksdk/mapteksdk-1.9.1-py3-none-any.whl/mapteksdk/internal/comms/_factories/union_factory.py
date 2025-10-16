"""Factory which handles typing.Union.

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

from ..component_factory import ComponentFactory
from ..base_message import Union, Optional
from ..errors import MalformedMessageError, DataTypeNotSupported
from .message_component_base import MessageComponentBase

if typing.TYPE_CHECKING:
  from ..message_component_protocol import MessageComponent


class _UnionComponent(MessageComponentBase):
  def __init__(self, data_type: Union, factory: ComponentFactory) -> None:
    super().__init__(data_type)
    self.__factory = factory

  _data_type: Union

  def _insert(self, message_handle, value: typing.Any) -> None:
    for union_type in self._data_type.union_types:
      if isinstance(value, union_type):
        component = self.__factory.get(union_type)
        component.insert(message_handle, value)
        return
    raise MalformedMessageError(
      f"Unexpected data: {value}. "
      f"Expected a value of type: {self._data_type.union_types}"
    )

  def _extract(self, message_handle) -> typing.Any:
    # Extracting a union type is difficult from Python because it cannot
    # easily check what the next type in the message. This is particularly
    # true for unions of different InlineMessage.
    raise MalformedMessageError(
      "Cannot read the value of a union from a MCP message."
    )


class _OptionalComponent(MessageComponentBase):
  """Message component for an optional value.

  An optional is sent and received as a boolean indicating whether the
  optional has a value. If this boolean is True, it is followed by the value.
  If the boolean is False, then it is not followed by a value.
  """
  def __init__(self, data_type: Optional, factory: ComponentFactory) -> None:
    super().__init__(data_type)
    self.__boolean_component = factory.get(bool)
    self.__body_component = factory.get(data_type.optional_type)

  _data_type: Optional

  def _insert(self, message_handle, value: typing.Any) -> None:
    if value is None:
      self.__boolean_component.insert(message_handle, False)
    else:
      self.__boolean_component.insert(message_handle, True)
      self.__body_component.insert(message_handle, value)

  def _extract(self, message_handle) -> typing.Any:
    has_value = self.__boolean_component.extract(message_handle)
    if has_value:
      return self.__body_component.extract(message_handle)
    return None


class UnionFactory(ComponentFactory):
  """Factory which handles typing.Union and typing.Optional.

  This delays determining which type in the union the value is serialised as
  until the message is ready to be sent.
  """
  def __init__(self, content_factory: ComponentFactory) -> None:
    self.__content_factory = content_factory

  def supports_type(self, data_type: type) -> bool:
    return isinstance(data_type, (Union, Optional))

  def get(self, data_type: Union | Optional) -> MessageComponent:
    if isinstance(data_type, Union):
      return _UnionComponent(data_type, self.__content_factory)
    if isinstance(data_type, Optional):
      return _OptionalComponent(data_type, self.__content_factory)
    raise DataTypeNotSupported(
      f"Unsupported union type: {data_type}"
    )
