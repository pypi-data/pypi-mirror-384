"""The Request class for the comms module.

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

from collections.abc import Callable
from contextlib import AbstractContextManager
import typing

from .repeating_fields import MessageWithRepeatingField
from .sendable_message import SendableMessage


if typing.TYPE_CHECKING:
  from .base_message import BaseMessage
  from .communication_manager import CommunicationsManager
  from .message_handle_protocols import (
    IncomingRequestHandle,
    OutgoingRequestHandle
  )


class Response(MessageWithRepeatingField):
  """Base class for responses to requests."""


class Request(SendableMessage):
  """A MCP message which forms a request that expects a response back.

  This provides special case handling for this scenario. It is often
  possible to mimic this behaviour by listening for a message that forms
  the reply and then sending an message which will elicit the message
  being sent back.

  Warnings
  --------
  If a thread calls `send()` on a `Request` subclass then that thread will
  block until the `Response` to the request arrives. If the `Response` never
  arrives, the thread will block forever. There is currently no mechanism for
  placing a timeout on receiving the response.

  Examples
  --------
  `Request` subclasses are structured the same as message subclasses, except
  that they have an extra `classproperty` which indicates the response type.
  The following example demonstrates a `Request` which sends the
  server a number and receives a `Response` which contains a different number.

  >>> class DoubleMessage(Request):
  ...     class DoubleResponse(Response):
  ...         result: Int64s
  ...
  ...     @classmethod
  ...     def message_name(cls) -> str:
  ...         return "double"
  ...
  ...     @classmethod
  ...     def response_type(cls) -> "type[DoubleResponse]":
  ...         return cls.DoubleResponse
  ...     value: Int64s

  The request can be sent by calling the `send()` function on an instance of
  the `Request` subclass. This will return an instance of the response type:

  >>> message = DoubleMessage(default_manager())
  >>> message.value = 42
  >>> response = message.send("doubleServer")
  >>> print(response.result)
  84

  To receive a `Request` subclass on a thread, it is best to use the
  `callback_on_receive()` classmethod. This handles sending the response
  returned by the callback and disposing of any message handles. The following
  example demonstrates a thread which will receive and send a response to a
  single `DoubleMessage` request.

  >>> finished = threading.Event()
  >>> def callback(message: DoubleMessage) -> DoubleMessage.DoubleResponse:
  ...     response = DoubleMessage.Response()
  ...     response.result = message.value * 2
  ...     finished.set()
  ...     return response
  >>> with DoubleMessage.callback_on_receive(
  ...     callback,
  ...     default_manager()
  >>> ):
  ...     while not finished.is_set():
  ...         Mcpd().ServicePendingEvents()
  """
  @classmethod
  def message_name(cls) -> str:
    raise NotImplementedError

  @classmethod
  def response_type(cls) -> type[Response]:
    """The type of the response expected for this Request.

    This must be implemented by child classes.
    """
    raise NotImplementedError

  @classmethod
  def callback_on_receive(
    cls,
    callback: Callable[["typing.Self"], Response],
    manager: "CommunicationsManager"
  ) -> AbstractContextManager:
    """Call a callback when a message of this type is received.

    This returns a MCPCallback and is best used in a with block.
    The callback should return the response to the message. This will handle
    sending that response.

    Parameters
    ----------
    mcp
      MCP DLL to use to receive the message.
    callback
      Callback to call when a message of this type is received. The callback
      is passed the received message as its only parameter. The callback
      should return an appropriate response to this message. This function
      will handle sending this response.
    manager
      Communications manager to use to receive the message.
    """
    def receive_message_and_call_callback(
        request_handle: "IncomingRequestHandle"):
      request = request_handle.extract(cls)
      response = callback(request)
      response_handle = request_handle.response_handle()
      response_handle.insert(response)
      response_handle.send()
    return manager.callback_on_request(
      cls.message_name(),
      receive_message_and_call_callback
    )

  def _create_message(self, destination: str) -> "OutgoingRequestHandle":
    # pylint: disable=protected-access
    return self._manager._create_request(
      self.message_name(),
      destination,
    )

  def _parse_response(
    self,
    response_handle: "IncomingRequestHandle | None"
  ) -> "BaseMessage | None":
    if response_handle is None:
      # This should be unreachable.
      raise RuntimeError("No response received for request.")

    return response_handle.extract(self.response_type())

  def send(self, destination: str,) -> Response:
    # The implementation of _send_message() ensures this will return a
    # Response object.
    return super().send(destination) # type: ignore
