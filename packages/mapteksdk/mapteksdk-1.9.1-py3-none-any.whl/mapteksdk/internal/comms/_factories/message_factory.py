"""Factory for creating MessageComponent objects for message classes.

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

from ..errors import DataTypeNotSupported, MalformedMessageError
from ..component_factory import ComponentFactory
from ..base_message import BaseMessage
from ..inline_message import InlineMessage
from ..message_component_protocol import MessageComponent
from ..sendable_message import SendableMessage
from ..sub_message import SubMessage

if typing.TYPE_CHECKING:
  from ....capi import McpApi
  from ..communication_manager import CommunicationsManager

class _MessageComponent(MessageComponent[BaseMessage]):
  """Message component for the bodies of message classes."""
  def __init__(
    self,
    message_type: type[BaseMessage],
    manager: CommunicationsManager
  ) -> None:
    self._message_type = message_type
    self._manager = manager

  def _create_message(self) -> BaseMessage:
    """Create an instance of the message class.

    This is used when extracting to create a message which can be populated
    with data read from the MCP.
    """
    return self._message_type()

  def insert(self, message_handle, value: BaseMessage) -> None:
    for name, data_type in self._message_type.message_structure().items():
      item = self._manager.get(data_type)
      sub_value = getattr(value, name)
      item.insert(message_handle, sub_value)

  def extract(self, message_handle) -> BaseMessage:
    message = self._create_message()
    for name, data_type in self._message_type.message_structure().items():
      item = self._manager.get(data_type)
      value = item.extract(message_handle)
      setattr(message, name, value)
    return message


class _AnyInlineMessageComponent(MessageComponent[BaseMessage]):
  """Message component which allows any InlineMessage.

  Unlike _MessageComponent, this uses reflection to determine the type of the
  InlineMessage at runtime. This allows for any InlineMessage to be placed in
  the message and it will be sent.

  This raises an error on extract because it is not possible to know where the
  InlineMessage starts and finishes or what type it is.
  """
  def __init__(self, factory: ComponentFactory) -> None:
    super().__init__()
    self.__factory = factory

  def insert(self, message_handle, value: InlineMessage) -> None:
    if not isinstance(value, InlineMessage):
      raise MalformedMessageError(
        f"Expected InlineMessage, but got {type(value)}"
      )
    component = self.__factory.get(type(value))
    component.insert(message_handle, value)

  def extract(self, message_handle) -> InlineMessage:
    raise MalformedMessageError(
      "Cannot extract a message which can contain any InlineMessage."
    )


class _SendableMessageComponent(_MessageComponent):
  """Message component for a sendable message."""
  _message_type: type[SendableMessage]
  def _create_message(self) -> SendableMessage:
    return self._message_type(self._manager)


class _SubMessageComponent(_MessageComponent):
  """Message component for sub messages.

  This expands _MessageComponent to add code for adding the markers for the
  start and end of the sub message before the body of the message.
  """
  def __init__(
    self,
    message_type: type[BaseMessage],
    manager: CommunicationsManager,
    mcp: McpApi
  ) -> None:
    super().__init__(message_type, manager)
    self.__mcp = mcp

  def insert(self, message_handle, value: BaseMessage) -> None:
    sub_message = self.__mcp.NewSubMessage()
    super().insert(sub_message, value)
    try:
      self.__mcp.AppendSubMessage(message_handle, sub_message)
    finally:
      self.__mcp.FreeMessage(sub_message)

  def extract(self, message_handle) -> BaseMessage:
    if not self.__mcp.IsSubMessage(message_handle):
      raise MalformedMessageError(
        "Expected the start of a sub message."
      )
    sub_message_handle = self.__mcp.ExtractSubMessage(message_handle)

    try:
      return super().extract(sub_message_handle)
    finally:
      self.__mcp.FreeMessage(sub_message_handle)


class MessageFactory(ComponentFactory):
  """Factory for creating message components for message classes.

  Parameters
  ----------
  manager
    Manager to use to create messages.
  mcp
    MCP dll to use to create and free message handles.
  """
  def __init__(self, manager: CommunicationsManager, mcp: McpApi) -> None:
    self.__manager = manager
    self.__mcp = mcp

  def supports_type(self, data_type: type) -> bool:
    try:
      return issubclass(data_type, BaseMessage)
    except TypeError:
      return False

  def get(self, data_type: type[BaseMessage]) -> MessageComponent[BaseMessage]:
    # If the type was annotated as "InlineMessage" rather than a subtype,
    # accept any InlineMessage.
    if data_type == InlineMessage:
      return _AnyInlineMessageComponent(self.__manager)
    if issubclass(data_type, SubMessage):
      return _SubMessageComponent(data_type, self.__manager, self.__mcp)
    if issubclass(data_type, SendableMessage):
      return _SendableMessageComponent(data_type, self.__manager)
    if issubclass(data_type, BaseMessage):
      return _MessageComponent(data_type, self.__manager)
    raise DataTypeNotSupported(
      f"Unsupported Message type: {data_type}"
    )
