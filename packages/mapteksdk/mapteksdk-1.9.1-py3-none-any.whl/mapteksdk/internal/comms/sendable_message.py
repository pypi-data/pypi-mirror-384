"""Base class for messages which define a full MCP message.

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

import logging
import typing

from .base_message import BaseMessage
from .repeating_fields import MessageWithRepeatingField

if typing.TYPE_CHECKING:
  from .communication_manager import CommunicationsManager
  from .message_handle_protocols import (
    OutgoingMessageHandle,
    IncomingMessageHandle,
  )

LOGGER = logging.getLogger('mapteksdk.internal.comms')


class SendableMessage(MessageWithRepeatingField):
  """Base class for messages which define the entire message structure.

  Child classes of this can stand on their own and thus can be sent over the
  MCP.

  Parameters
  ----------
  manager
    Manager to use to send the message.
  """
  def __init__(self, manager: "CommunicationsManager") -> None:
    super().__init__()
    self.__manager = manager

  @classmethod
  def message_name(cls) -> str:
    """The name of the message.

    This must be implemented by derived types.
    This must not be empty and it must not contain any :: characters.
    This is used for sending and receiving the message over the communications
    system.
    """
    raise NotImplementedError

  @classmethod
  def logger(cls) -> logging.Logger:
    """Logger which should be used by child classes."""
    return LOGGER

  def _create_message(
      self,
      destination: str
    ) -> "OutgoingMessageHandle":
    """Create the message.

    Parameters
    ----------
    mcp
      MCP DLL to use to create the message.
    destination
      The name of the server to create the message to be sent to.

    Returns
    -------
    message_handle
      The handle for the newly created message.
    """
    raise NotImplementedError

  def _parse_response(
    self,
    response_handle: "IncomingMessageHandle | None"
  ) -> typing.Optional[BaseMessage]:
    """Parse the response to this message.

    Parameters
    ----------
    response_handle
      The response handle received for this message or None if this message
      did not expect a response.

    Returns
    -------
    Optional[BaseMessage]
      The response to this message or None if this message does not expect
      a response.
    """
    if response_handle is not None:
      # This should be unreachable.
      raise RuntimeError(
        "Received response for a message which is not expecting a response.")
    return None

  @property
  def _manager(self) -> "CommunicationsManager":
    """Communications manager to use to send or receive the message."""
    return self.__manager

  def send(
      self,
      destination: str
    ) -> typing.Optional[BaseMessage]:
    """Send this message to the destination.

    Parameters
    ----------
    destination
      The name of the server to send this message to.

    Returns
    -------
    Optional[BaseMessage]
      The response to the message if this message expects a response.
      This will be None if this message does not expect a response.
    """
    message_name = self.message_name()
    assert message_name.strip(), 'The name of the message is required.'
    assert '::' not in message_name, 'The name may not contain ::'

    if not destination:
      raise ValueError('No destination specified.')

    self.logger().info('Sending %s to %s', message_name, destination)

    handle = self._create_message(destination)
    try:
      handle.insert(self)
      return self._parse_response(handle.send())
    finally:
      # Exit the context manager if the handle is one.
      getattr(handle, "__exit__", lambda a, b, c: None)(None, None, None)
