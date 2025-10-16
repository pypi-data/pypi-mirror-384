"""Protocol for the default user facing communications manager.

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

from ..protocol import Protocol
from .component_factory import ComponentFactory

if typing.TYPE_CHECKING:
  from collections.abc import Callable
  from contextlib import AbstractContextManager
  from .message_handle_protocols import (
    IncomingMessageHandle,
    IncomingRequestHandle,
    OutgoingMessageHandle,
    OutgoingRequestHandle,
  )


class CommunicationsManager(ComponentFactory, Protocol):
  """Class which manages communications.

  This can be used to create and receive `Message` and `Request` subclasses.
  """
  def _create_message(
    self,
    name: str,
    destination: str
  ) -> OutgoingMessageHandle:
    """Create the handle for an outgoing message."""
    raise NotImplementedError

  def _create_request(
    self,
    name: str,
    destination: str
  ) -> OutgoingRequestHandle:
    """Create the handle for an outgoing request."""
    raise NotImplementedError

  def service_events(self):
    """Service pending events registered with this class.

    This will call any of callbacks registered with `callback_on_message()`
    or `callback_on_request()` if an appropriate message or request has
    been received.
    """
    raise NotImplementedError

  def callback_on_message(
    self,
    event_name: str,
    callback: Callable[[IncomingMessageHandle], None],
  ) -> AbstractContextManager:
    """Register a callback on the specified event.

    Typically, code should use `Message.callback_on_receive()` instead of
    calling this directly because that handles parsing the incoming
    message. Using this directly is only required for messages without
    a fixed structure.

    Once a callback is registered, when a message called `event_name` arrives,
    then the callback will be called on that message the next time
    `service_events()` is called.

    The callback will be unregistered when the __exit__ function of the
    returned context manager is called.

    Parameters
    ----------
    event_name
      The name of the event which should cause the callback to be called.
      This takes the handle of the incoming message as its only argument.
    callback
      Callback to call when the event is serviced.
    """
    raise NotImplementedError

  def callback_on_request(
      self,
      event_name: str,
      callback: Callable[[IncomingRequestHandle], None]
  ) -> AbstractContextManager:
    """Register a callback on the specified request.

    Typically, code should use `Request.callback_on_receive()` instead of
    calling this directly because that handles parsing the incoming
    message and sending the response. Using this directly is only required for
    requests without a fixed structure.

    Once a callback is registered, when a request called `event_name` arrives,
    then the callback will be called on that request the next time
    `service_events()` is called.

    The callback will be unregistered when the __exit__ function of the
    returned context manager is called.

    Parameters
    ----------
    event_name
      The name of the event which should cause the callback to be called.
    callback
      Callback to call when the event is serviced. This must send the response
      to the request.
      This takes the handle of the incoming request as its only argument.
    """
    raise NotImplementedError
