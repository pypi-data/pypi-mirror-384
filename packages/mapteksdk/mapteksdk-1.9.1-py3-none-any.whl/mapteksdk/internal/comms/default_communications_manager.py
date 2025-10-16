"""Default manager for MCP messages.

This combines all of the concrete factories defined by the SDK.

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

from ...capi import Mcp, McpApi
from ..mcp import McpCallback
from .communication_manager import CommunicationsManager
from .message_handle import (
  MessageHandle,
  RequestHandle,
  ReceivedMessageHandle,
  ReceivedRequestHandle,
)
from ._factories.any_factory import AnyFactory
from ._factories.compound_factory import CompoundFactory
from ._factories.message_factory import MessageFactory
from ._factories.primitive_factory import PrimitiveFactory
from ._factories.repeating_field_factory import RepeatingFieldFactory
from ._factories.serialisable_factory import SerialisableFactory
from ._factories.sequence_factory import SequenceFactory
from ._factories.union_factory import UnionFactory

if typing.TYPE_CHECKING:
  from collections.abc import Callable
  from contextlib import AbstractContextManager

  from ...capi.types import T_MessageHandle
  from .sendable_message import SendableMessage

  MessageT = typing.TypeVar("MessageT", bound=SendableMessage)


class DefaultCommunicationsManager(CompoundFactory, CommunicationsManager):
  """Default communications manager.

  This concrete implementation uses the MCP to communicate with the running
  application.
  """
  def __init__(self, mcp: McpApi | None) -> None:
    self.__mcp = mcp or Mcp()
    factories = [
      PrimitiveFactory(self.__mcp),
      SerialisableFactory(self),
      SequenceFactory(self, self.__mcp),
      RepeatingFieldFactory(self, self.__mcp),
      MessageFactory(self, self.__mcp),
      UnionFactory(self),
      AnyFactory(self),
    ]
    super().__init__(factories)

  @property
  def mcp(self) -> McpApi:
    """The MCP DLL used by this manager."""
    return self.__mcp

  def service_events(self):
    return self.mcp.ServicePendingEvents()

  def _create_message(self, name: str, destination: str) -> MessageHandle:
    return MessageHandle(name, destination, self)

  def _create_request(self, name: str, destination: str) -> RequestHandle:
    return RequestHandle(name, destination, self)

  def callback_on_message(
    self,
    event_name: str,
    callback: Callable[[ReceivedMessageHandle], None],
  ) -> AbstractContextManager:
    def raw_callback(raw_handle: T_MessageHandle):
      with ReceivedMessageHandle(raw_handle, self) as handle:
        callback(handle)
    return McpCallback(
      event_name,
      raw_callback,
      self.mcp
    )

  def callback_on_request(
    self,
    event_name: str,
    callback: Callable[[ReceivedRequestHandle], None]
  ):
    def raw_callback(raw_handle: T_MessageHandle):
      with ReceivedRequestHandle(raw_handle, self) as handle:
        callback(handle)
    return McpCallback(
      event_name,
      raw_callback,
      self.mcp
    )
