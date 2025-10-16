"""Factory which handles serialisable types.

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
from ..protocols import Serialisable
from .message_component_base import MessageComponentBase

if typing.TYPE_CHECKING:
  from ..message_component_protocol import MessageComponent


class _SerialisableComponent(MessageComponentBase):
  """Component which handles Serialisable classes.

  This assumes data_type implements the Serialisable protocol defined in
  this package.

  Parameters
  ----------
  data_type
    Data type this should handle. It should implement the serialisable protocol.
  component
    The component which can be used to insert and extract the storage
    type.
  """
  def __init__(
    self,
    data_type: type[Serialisable],
    component: MessageComponent
  ) -> None:
    super().__init__(data_type)
    self.__component = component

  _data_type: Serialisable

  def _insert(self, message_handle, value: Serialisable) -> None:
    storage_value = value.convert_to()
    self.__component.insert(message_handle, storage_value)

  def _extract(self, message_handle) -> Serialisable:
    storage_value = self.__component.extract(message_handle)
    return self._data_type.convert_from(storage_value)


class SerialisableFactory(ComponentFactory):
  """Factory for handling serialisable classes.

  These are classes which implement the Serialisable protocol which is defined
  in the comms package.
  """
  def __init__(self, content_factory: ComponentFactory) -> None:
    self.__content_factory = content_factory

  def supports_type(self, data_type: type) -> bool:
    # This assumes that any class which has a property named storage_type,
    # convert_to and convert_from implements the Serialisable protocol
    # and thus is supported by this class.
    # This matches how runtime-checkable protocols are implemented in the
    # Python standard library.
    # :TODO: SDK-506 Make Serialisable runtime-checkable and use it here.
    required_properties = ("storage_type", "convert_to", "convert_from")
    for required_property in required_properties:
      if not hasattr(data_type, required_property):
        return False
    return True

  def get(self, data_type: type[Serialisable]) -> MessageComponent:
    if not self.supports_type(data_type):
      raise DataTypeNotSupported(
        f"Unsupported serialisable data type: {data_type}."
      )

    try:
      storage_type_component = self.__content_factory.get(
        data_type.storage_type)
    except DataTypeNotSupported as error:
      raise DataTypeNotSupported(
        f"Unsupported storage type for serialisable type: {data_type}."
      ) from error

    return _SerialisableComponent(data_type, storage_type_component)
