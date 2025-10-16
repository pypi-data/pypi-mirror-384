"""Base class for message components.

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

from ..errors import MalformedMessageError
from ..message_component_protocol import MessageComponent, T

try:
  final = typing.final
except AttributeError:
  # :TODO: SDK-506 typing.final was added to the typing module in
  # Python 3.8. When dropping support for Python 3.7, this try
  # catch can be removed.
  # pylint: disable=invalid-name
  def final(f):
    """Empty decorator to replace final in Python 3.7."""
    return f


class MessageComponentBase(MessageComponent[T]):
  """Base class for message components.

  By inheriting from this class rather than MessageComponent directly
  this allows for de-duplicating error handling code for message components.

  Child classes should implement _insert() and _extract() instead of insert()
  and extract().

  Parameters
  ----------
  data_type
    Data type to report in error messages.
  """
  def __init__(self, data_type: type[T]) -> None:
    self.__data_type = data_type

  @property
  def _data_type(self) -> type[T]:
    return self.__data_type

  def _insert(self, message_handle, value: T) -> None:
    """Implementation of insert.

    This does not need to handle any errors.
    """
    raise NotImplementedError

  def _extract(self, message_handle) -> T:
    """Implementation of insert.

    This does not need to handle any errors.
    """
    raise NotImplementedError

  @final
  def insert(self, message_handle, value: T) -> None:
    try:
      self._insert(message_handle, value)
    except AttributeError as error:
      # The name field was added in Python 3.10.
      name = getattr(error, "name", None) or "[Unavailable]"
      raise MalformedMessageError(
        f"Failed to construct the message. The {name} property was "
        "not assigned a value."
      ) from error
    except Exception as error:
      raise MalformedMessageError(
        "Failed to send a message to the connected application. The message "
        f"expected a value of type: '{self._data_type}', but a value of type "
        f"'{type(value)}' was provided instead. "
        "This may indicate the SDK does not support the connected application. "
        "If that is not the case, please report the problem to Maptek via "
        "Request Support in the Workbench."
      ) from error

  @final
  def extract(self, message_handle) -> T:
    try:
      return self._extract(message_handle)
    except Exception as error:
      raise MalformedMessageError(
        "Failed to receive a response from the connected application. "
        f"The SDK expected a value of type: '{self._data_type}'."
        "This may indicate the SDK does not support the connected application. "
        "If that is not the case, please report the problem to Maptek via "
        "Request Support in the Workbench."
      ) from error
