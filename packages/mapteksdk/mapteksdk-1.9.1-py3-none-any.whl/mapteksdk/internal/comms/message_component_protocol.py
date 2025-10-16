"""Interface for objects which can be part of a MCP message.

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

import typing

from ..protocol import Protocol


if typing.TYPE_CHECKING:
  from ...capi.types import T_MessageHandle


T = typing.TypeVar("T")
"""Generic argument for MessageComponent."""

class MessageComponent(typing.Generic[T], Protocol):
  """Protocol for objects which can be part of a MCP message.

  A concrete implementation of `MessageComponent` defines how data of a
  particular type can be inserted/extracted into/from a MCP message*.
  Typically, clients of the comms package will not deal with `MessageComponent`
  directly because the usage of this class is hidden inside of the
  implementation of the `Message` and `Request` classes.

  * The MessageComponent class is sufficiently general that the MCP could be
  replaced with a different messaging system without any of the clients
  of this class needing to change.

  Notes
  -----
  Clients of this package should always interact with the concrete
  implementations of this protocol only via the interface provided by the
  protocol. The details of the concrete implementations should be considered
  internal implementation details.

  Examples
  --------
  To get a `MessageComponent` which can insert or extract a string from
  a message:

  >>> manager = default_manager()
  >>> component = manager.get(str)
  >>> # To insert into a message:
  >>> # component.insert(message, "very hungry caterpillar")
  >>> # To extract from a message:
  >>> # extracted: str = component.extract(message)
  """
  def insert(self, message_handle: "T_MessageHandle", value: T) -> None:
    """insert a value of the appropriate type to the message.

    Raises
    ------
    MalformedMessageError
      If T is not of a supported type.
    """
    raise NotImplementedError

  def extract(self, message_handle: "T_MessageHandle") -> T:
    """Extract a value of the appropriate type from the message.

    Raises
    ------
    MalformedMessageError
      If the next value to be read from the message is not of the type
      supported by this object.
    """
    raise NotImplementedError
