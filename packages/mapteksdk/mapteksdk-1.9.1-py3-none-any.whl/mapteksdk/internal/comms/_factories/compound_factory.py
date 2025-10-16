"""A Factory which works by composing multiple factories.

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
from ..message_component_protocol import MessageComponent

if typing.TYPE_CHECKING:
  from ..component_factory import ComponentT


class CompoundFactory(ComponentFactory):
  """A Factory which composes multiple Factory objects."""
  def __init__(self, factories: typing.Sequence[ComponentFactory]) -> None:
    self.__factories = list(factories)

  def add_factory(self, factory: ComponentFactory):
    """Add a new factory to this compound factory."""
    self.__factories.append(factory)

  def supports_type(self, data_type: type) -> bool:
    for factory in self.__factories:
      if factory.supports_type(data_type):
        return True
    return False

  def get(self, data_type: type[ComponentT]) -> MessageComponent[ComponentT]:
    for factory in self.__factories:
      if factory.supports_type(data_type):
        return factory.get(data_type)

    if isinstance(data_type, str):
      raise DataTypeNotSupported(
        f"Unsupported data type: {data_type}. "
        "You may have defined the Message subclass in a file with "
        "'from __future__ import annotations', which is not supported."
      )
    raise DataTypeNotSupported(
      f"Unsupported data type: {data_type}"
    )
