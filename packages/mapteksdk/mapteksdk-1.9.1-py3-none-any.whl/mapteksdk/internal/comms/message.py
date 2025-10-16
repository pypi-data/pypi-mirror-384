"""The Message class for the comms module.

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

from .sendable_message import SendableMessage

if typing.TYPE_CHECKING:
  from .communication_manager import CommunicationsManager
  from .message_handle import IncomingMessageHandle, OutgoingMessageHandle


class Message(SendableMessage):
  """Base class for defining the structure of an MCP message.

  Messages do not expect a response from the server and thus calling send()
  will not block waiting for a response.

  Use PEP-526 variable annotations as defined in BaseMessage to define the
  structure of a message.

  Examples
  --------
  Variable annotations are used to define the structure of a message subclass.
  For example, to define a message called "example" which contains an 8 bit
  unsigned integer, a boolean and then a string:

  >>> class ExampleMessage(Message):
  ...     @classmethod
  ...     def message_name(cls) -> str:
  ...         return "example"
  ...
  ...     # The order in the class matches the order they are sent.
  ...     alpha: Int8u
  ...     beta: bool
  ...     gamma: str

  To send a message, you must first create an instance of the subclass and
  call the `send()` function:

  >>> # Continuing from the previous example:
  >>> message = ExampleMessage(default_manager())
  >>> # First, populate the message.
  >>> message.alpha = 16
  >>> message.beta = True
  >>> message.gamma = "Llama"
  >>> message.send("exampleServer")

  To receive a message, you should use the `callback_on_receive()` function
  in a `with` block. For the duration of the `with` block, if a message
  of the specified type is received then the callback will be called.
  The following example demonstrates how to make a thread wait for a single
  message to arrive:

  >>> event = threading.Event()
  >>> def callback(example_message: ExampleMessage):
  ...     # Do something useful with the received message here.
  ...     event.set()
  >>>
  >>> with ExampleMessage.callback_on_receive(
  ...     on_receive,
  ...     default_manager()
  >>> ):
  ...     while not event.is_set():
  ...         Mcpd().ServicePendingEvents()
  """
  @classmethod
  def message_name(cls) -> str:
    raise NotImplementedError

  @classmethod
  def callback_on_receive(
    cls,
    callback: Callable[["typing.Self"], None],
    manager: "CommunicationsManager"
  ) -> AbstractContextManager:
    """Call a callback when a message of this type is received.

    This returns a MCPCallback and is best used in a with block.

    Parameters
    ----------
    mcp
      MCP DLL to use to receive the message.
    callback
      Callback to call when a message of this type is received. The callback
      is passed the received message as its only parameter.
    manager
      Communications manager to use to receive the message.
    """
    def receive_message_and_call_callback(
        message_handle: "IncomingMessageHandle"):
      message = message_handle.extract(cls)
      callback(message)
    return manager.callback_on_message(
      cls.message_name(),
      receive_message_and_call_callback
    )

  def _create_message(self, destination: str) -> "OutgoingMessageHandle":
    # pylint: disable=protected-access
    return self._manager._create_message(
      self.message_name(),
      destination,
    )

  def send(self, destination: str) -> None:
    # The implementation of _send_message means send() will return None.
    return super().send(destination) # type: ignore
