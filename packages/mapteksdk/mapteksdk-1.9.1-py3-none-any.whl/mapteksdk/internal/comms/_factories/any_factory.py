"""Factory which handles typing.Any.

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
from ..base_message import List, Set, Tuple
from .message_component_base import MessageComponentBase

if typing.TYPE_CHECKING:
  from ..message_component_protocol import MessageComponent


class _AnyComponent(MessageComponentBase):
  """Component which handles the tying.Any type.

  This uses reflection to get the type of the value at runtime and uses
  factory to get an appropriate message component to add the value to the
  message.

  This does not support extracting values from the message.
  """
  def __init__(self, factory: ComponentFactory) -> None:
    super().__init__(typing.Any)
    self.__factory = factory

  def _insert(self, message_handle, value: typing.Any) -> None:
    data_type = type(value)

    if data_type is list:
      if len(value) == 0:
        # The element type doesn't matter if the list is empty.
        element_type = bool
      else:
        element_type = type(value[0])
      component = self.__factory.get(List(element_type))
    elif data_type is set:
      if len(value) == 0:
        # The element type doesn't matter if the list is empty.
        element_type = bool
      else:
        # Get any value from the set and assume all values
        # have that type.
        element_type = type(next(iter(value)))
      component = self.__factory.get(Set(element_type))
    elif data_type is tuple:
      element_types = [type(element) for element in value]
      component = self.__factory.get(Tuple(*element_types))
    else:
      component = self.__factory.get(type(value))
    component.insert(message_handle, value)

  def _extract(self, message_handle) -> typing.Any:
    return NotImplemented



class AnyFactory(ComponentFactory):
  """Factory for handling typing.any.

  This uses reflection to get the type of the data passed to it and uses
  content_factory to find an appropriate message component for that data.
  """
  def __init__(self, content_factory: ComponentFactory) -> None:
    self.__content_factory = content_factory

  def supports_type(self, data_type: type) -> bool:
    return data_type is typing.Any

  def get(self, _: typing.Any) -> MessageComponent[typing.Any]:
    return _AnyComponent(self.__content_factory)
