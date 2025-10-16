"""Interface for factories which create message components.

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

if typing.TYPE_CHECKING:
  from ...capi.types import T_MessageHandle
  from .message_component_protocol import MessageComponent
  ComponentT = typing.TypeVar("ComponentT")

class ComponentFactory(Protocol):
  """Protocol for factories which can create message components.

  The `get()` function can be used to get a concrete implementation of
  `MessageComponent` which can be used to insert/extract values of
  the given type into/from a message. See default_manager() for a full list
  of the types supported by the SDK by default.

  The most common use case for factories is with the Message and Request
  classes. These classes hide the actual usage of the factory within the
  `send()` and `receive()` functions - see the Examples for those classes
  for more details.

  Notes
  -----
  Clients should always deal with factories through the class which implements
  this protocol returned by the `default_manager()` function. The concrete
  implementations of this protocol should be considered internal
  implementation details.
  """
  def supports_type(self, data_type: type) -> bool:
    """True if data_type is supported by this factory."""
    raise NotImplementedError

  def get(self, data_type: type[ComponentT]) -> MessageComponent[ComponentT]:
    """Get an MessageComponent which can handle `data_type`.

    Parameters
    ----------
    data_type
      The data type to return an MessageComponent concrete implementation
      which can insert or extract data of that type from a MCP message.

    Returns
    -------
    MessageComponent
      MessageComponent which can insert or extract data of type data_type
      from a MCP message.

    Raises
    ------
    DataTypeNotSupported
      If there is no MessageComponent class which can handle `data_type`.
    """
    raise NotImplementedError

  def extract(
    self,
    message_handle: T_MessageHandle,
    data_type: type[ComponentT]
  ) -> ComponentT:
    """Extract a value from a message using this factory.

    This is equivalent to a call of `get()` and `extract()` and can raise all
    of the same exceptions.

    Parameters
    ----------
    message_handle
      Handle to the message to extract from.
    data_type
      The type of the data to extract from the message handle.

    Returns
    -------
    ComponentT
      The value extracted from the message.

    Raises
    ------
    DataTypeNotSupported
      If `data_type` is not supported.
    """
    return self.get(data_type).extract(message_handle)

  def insert(
      self,
      message_handle: T_MessageHandle,
      data_type: type[ComponentT],
      value: ComponentT
    ):
    """Insert a value into a message using this class.

    This is equivalent to a call to `get()` followed by a call to `insert()`
    and can throw all of the same exceptions.

    Parameters
    ----------
    message_handle
      Handle on the message to insert the value into.
    data_type
      The type of the value to insert into the message.
    value
      The value to insert into the message.

    Raises
    ------
    DataTypeNotSupported
      If `data_type` is not supported.
    """
    return self.get(data_type).insert(message_handle, value)

  def insert_any(self, message_handle, value):
    """Insert a value into the message without specifying the type.

    This will use reflection to determine the type of value to enable
    a call to `get()` and `insert()`. Typically, this should only be used
    over the `Factory.insert()` function when the caller was going to call
    it using reflection anyway.

    Parameters
    ----------
    message_handle
      Handle on the message to insert the value into.
    value
      The value to insert into the message.

    Raises
    ------
    DataTypeNotSupported
      If `data_type` is not supported.
    """
    return self.insert(message_handle, type(value), value)
