"""Factory for handling repeating fields in messages.

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

from ..repeating_fields import RepeatingField
from ..errors import DataTypeNotSupported
from ..component_factory import ComponentFactory
from ..message_component_protocol import MessageComponent

if typing.TYPE_CHECKING:
  from ....capi import McpApi

class _RepeatingFieldComponent(MessageComponent):
  """Message component for repeating fields.

  This must be the last component in the message.

  Parameters
  ----------
  element_component
    Message component to use to insert or extract the elements of the
    repeating field from the message.
  """
  def __init__(self, element_component: MessageComponent, mcp: McpApi) -> None:
    self.__element_component = element_component
    self.__mcp = mcp

  def insert(self, message_handle, value: typing.Sequence) -> None:
    for item in value:
      self.__element_component.insert(message_handle, item)

  def extract(self, message_handle) -> typing.Sequence:
    result = []
    while not self.__mcp.IsEom(message_handle):
      value = self.__element_component.extract(message_handle)

      # Break from the loop if the value is NotImplemented. This is the case
      # for a repeating field of class typing.Any.
      # :TODO: SDK-919 Remove this hack when adding a better way to extract
      # qualifier parameters.
      if value == NotImplemented:
        break
      result.append(
        value
      )
    return result


class RepeatingFieldFactory(ComponentFactory):
  """Factory which handles repeating fields.

  Repeating fields are lists of values which continue until the end of the
  message.
  """
  def __init__(self, element_factory: ComponentFactory, mcp: McpApi) -> None:
    self.__element_factory = element_factory
    self.__mcp = mcp

  def supports_type(self, data_type: type) -> bool:
    try:
      return isinstance(data_type, RepeatingField)
    except TypeError:
      pass
    return False

  def get(self, data_type: RepeatingField) -> MessageComponent:
    if isinstance(data_type, RepeatingField):
      return _RepeatingFieldComponent(
        self.__element_factory.get(data_type.element_type),
        self.__mcp
      )
    raise DataTypeNotSupported(
      "Unsupported repeating field type."
    )
