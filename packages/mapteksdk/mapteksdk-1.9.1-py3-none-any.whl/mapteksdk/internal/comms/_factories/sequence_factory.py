"""Factory which handles sequence types.

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

from ..errors import DataTypeNotSupported
from ..component_factory import ComponentFactory
from ..base_message import List, Set, Tuple
from .message_component_base import MessageComponentBase

if typing.TYPE_CHECKING:
  from ....capi import McpApi
  from ..message_component_protocol import MessageComponent
  SupportedTypes = typing.TypeVar("SupportedTypes", List, Set, Tuple)


class _ListComponent(MessageComponentBase):
  """Component for single typed lists."""
  def __init__(self, element_component: MessageComponent, mcp: McpApi) -> None:
    super().__init__(List)
    self.__element_component = element_component
    self.__mcp = mcp

  def _insert(self, message_handle, value: list) -> None:
    self.__mcp.AppendUInt(message_handle, len(value), 8)
    for sub_value in value:
      self.__element_component.insert(message_handle, sub_value)

  def _extract(self, message_handle) -> list:
    result = []
    length = self.__mcp.ExtractUInt(message_handle)
    for _ in range(length):
      result.append(self.__element_component.extract(message_handle))
    return result


class _SetComponent(MessageComponentBase):
  """Component for single typed sets."""
  def __init__(self, element_component: MessageComponent, mcp: McpApi) -> None:
    super().__init__(Set)
    self.__element_component = element_component
    self.__mcp = mcp

  def _insert(self, message_handle, value: set) -> None:
    self.__mcp.AppendUInt(message_handle, len(value), 8)
    for sub_value in value:
      self.__element_component.insert(message_handle, sub_value)

  def _extract(self, message_handle) -> set:
    result = set()
    length = self.__mcp.ExtractUInt(message_handle)
    for _ in range(length):
      result.add(self.__element_component.extract(message_handle))
    return result


class _TupleComponent(MessageComponentBase):
  """Component for tuples."""
  def __init__(self, element_components: list[MessageComponent]) -> None:
    super().__init__(Tuple)
    self.__element_components = element_components

  def _insert(self, message_handle, value: tuple) -> None:
    if len(value) != len(self.__element_components):
      raise ValueError(
        "Not enough elements for tuple in message. "
        f"Expected: {len(self.__element_components)} elements. "
        f"Got: {len(value)} elements. "
      )
    for sub_value, component in zip(value, self.__element_components):
      component.insert(message_handle, sub_value)

  def _extract(self, message_handle) -> tuple:
    return tuple(
      component.extract(message_handle)
      for component in self.__element_components
    )


class SequenceFactory(ComponentFactory):
  """Factory which handles sequence types.

  This includes lists, sets and tuples.

  Parameters
  ----------
  content_factory
    Factory to use to serialise the contents of the sequence.
  mcp
    MCP dll to use to insert / read the length of the list.
  """
  def __init__(self, content_factory: ComponentFactory, mcp: McpApi) -> None:
    self.__content_factory = content_factory
    self.__mcp = mcp

  def supports_type(self, data_type: type) -> bool:
    return isinstance(data_type, (List, Tuple, Set))

  def get(
    self,
    data_type: SupportedTypes
  ) -> MessageComponent[SupportedTypes]:
    if isinstance(data_type, List):
      try:
        return _ListComponent(
          self.__content_factory.get(data_type.element_type),
          self.__mcp
        )
      except DataTypeNotSupported as error:
        raise DataTypeNotSupported(
          f"Unsupported element type for list: {data_type}"
        ) from error
    if isinstance(data_type, Set):
      try:
        return _SetComponent(
          self.__content_factory.get(data_type.element_type),
          self.__mcp
        )
      except DataTypeNotSupported as error:
        raise DataTypeNotSupported(
          f"Unsupported element type for set: {data_type}"
        ) from error
    if isinstance(data_type, Tuple):
      try:
        tuple_components = [
          self.__content_factory.get(child_type)
          for child_type in data_type.element_types
        ]

        return _TupleComponent(tuple_components)
      except DataTypeNotSupported as error:
        raise DataTypeNotSupported(
          f"Unsupported element type for tuple: {data_type}"
        ) from error
    raise DataTypeNotSupported(
      f"Unsupported sequence type in message: {data_type}"
    )
