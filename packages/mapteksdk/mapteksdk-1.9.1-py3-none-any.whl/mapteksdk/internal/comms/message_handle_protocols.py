"""Protocols implemented by message handles.

Client classes should deal with the implementations of these protocols through
the protocol. This will enable for different implementations of message
handles to be substituted in (Typically for testing).

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
T = typing.TypeVar("T")


class IncomingMessageHandle(Protocol):
  """Protocol for a message which has been received by this thread.

  Values can be extracted from a received message, but not inserted.
  Received messages cannot be sent.
  """
  def extract(self, data_type: type[T]) -> T:
    """Extract the next value from the message.

    Parameters
    ----------
    data_type
      The expected data type of the next value in the message.

    Raises
    ------
    DataTypeNotSupported
      If `data_type` is not supported.
    MalformedMessageError
      If the next item in the message does not have the expected type.
    """
    raise NotImplementedError


class IncomingRequestHandle(IncomingMessageHandle):
  """Protocol for a request which has been received by this thread.

  Unlike messages, requests expect a response so this includes extra
  functionality to get the response handle to enable sending the
  response.
  """
  def response_handle(self) -> OutgoingMessageHandle:
    """Get the response handle for this request."""
    raise NotImplementedError


class OutgoingMessageHandle(Protocol):
  """Protocol for a message which is intended to be sent from this thread.

  Values can be inserted into a sendable message and then it can be sent.
  """
  def insert(self, value, data_type=None):
    """Insert `value` into the message as `data_type`.

    Parameters
    ----------
    value
      The data to insert into the message.
    data_type
      The type to insert data as into the message. If None, then `type(value)`
      will be used to determine the data type.

    Raises
    ------
    DataTypeNotSupported
      If `data_type` is not supported.
    """

  def send(self) -> None:
    """Send the message."""

class OutgoingRequestHandle(OutgoingMessageHandle, Protocol):
  """Protocol for a request which is intended to be sent from this thread.

  Unlike messages, requests expect a response.
  """
  def send(self) -> IncomingMessageHandle:
    """Send the request.

    Returns
    -------
    IncomingMessageHandle
      The message handle for the response.
    """
    raise NotImplementedError
