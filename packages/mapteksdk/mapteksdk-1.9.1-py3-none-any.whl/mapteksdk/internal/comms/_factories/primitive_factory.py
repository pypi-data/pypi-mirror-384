"""Factory which handles primitive types.

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

import ctypes
import functools
import typing

from ...serialised_text import (
  SerialisedText,
  ReceivedSerialisedText,
)
from ..errors import DataTypeNotSupported
from ..component_factory import ComponentFactory
from ..message_component_protocol import MessageComponent
from ..types import (
  Int8s,
  Int16s,
  Int32s,
  Int64s,
  Int8u,
  Int16u,
  Int32u,
  Int64u,
  Float,
  Double,
  Integers,
  Floats,
  Primitives
)
from .message_component_base import MessageComponentBase

if typing.TYPE_CHECKING:
  from mapteksdk.capi import McpApi

class _IntegerMessageComponent(MessageComponentBase[Integers]):
  """Message component for integer primitives."""
  def __init__(self, mcp: McpApi, data_type: type[Integers]) -> None:
    integers = {Int8s, Int16s, Int32s, Int64s, Int8u, Int16u, Int32u, Int64u,}
    if data_type not in integers:
      raise RuntimeError(f"Unsupported integer type: {data_type}")
    super().__init__(data_type)
    self.__mcp = mcp

  def _append_int8s(self, message, value: int):
    self.__mcp.AppendSInt(message, value, 1)

  def _append_int16s(self, message, value: int):
    self.__mcp.AppendSInt(message, value, 2)

  def _append_int32s(self, message, value: int):
    self.__mcp.AppendSInt(message, value, 4)

  def _append_int64s(self, message, value: int):
    self.__mcp.AppendSInt(message, value, 8)

  def _append_int8u(self, message, value: int):
    self.__mcp.AppendUInt(message, value, 1)

  def _append_int16u(self, message, value: int):
    self.__mcp.AppendUInt(message, value, 2)

  def _append_int32u(self, message, value: int):
    self.__mcp.AppendUInt(message, value, 4)

  def _append_int64u(self, message, value: int):
    self.__mcp.AppendUInt(message, value, 8)

  def _extract_signed_int(self, message) -> int:
    return self.__mcp.ExtractSInt(message)

  def _extract_unsigned_int(self, message) -> int:
    return self.__mcp.ExtractUInt(message)

  def _insert(self, message_handle, value: int) -> None:
    append_functions: dict[
        type[Integers],
        typing.Callable[[typing.Any, int], None]
    ] = {
      Int8s : self._append_int8s,
      Int16s : self._append_int16s,
      Int32s : self._append_int32s,
      Int64s : self._append_int64s,
      Int8u : self._append_int8u,
      Int16u : self._append_int16u,
      Int32u : self._append_int32u,
      Int64u : self._append_int64u,
    }

    append_functions[self._data_type](message_handle, value)

  def _extract(self, message_handle) -> int:
    extract_functions: dict[
        type[Integers],
        typing.Callable[[typing.Any], int]
    ] = {
      Int8s : self._extract_signed_int,
      Int16s : self._extract_signed_int,
      Int32s : self._extract_signed_int,
      Int64s : self._extract_signed_int,
      Int8u : self._extract_unsigned_int,
      Int16u : self._extract_unsigned_int,
      Int32u : self._extract_unsigned_int,
      Int64u : self._extract_unsigned_int,
    }
    return extract_functions[self._data_type](message_handle)


class _FloatMessageComponent(MessageComponentBase[Floats]):
  def __init__(self, mcp: McpApi, data_type: type[Floats]) -> None:
    if data_type not in (Float, Double):
      raise RuntimeError(
        f"Unsupported float data type: {data_type}."
      )
    super().__init__(data_type)
    self.__mcp = mcp

  def _append_float(self, message, value: float):
    self.__mcp.AppendFloat(message, value)

  def _append_double(self, message, value: float):
    self.__mcp.AppendDouble(message, value)

  def _extract_float(self, message) -> float:
    return self.__mcp.ExtractFloat(message)

  def _insert(self, message_handle, value: float) -> None:
    if self._data_type == Float:
      self._append_float(message_handle, value)
    elif self._data_type == Double:
      self._append_double(message_handle, value)

  def _extract(self, message_handle) -> float:
    return self._extract_float(message_handle)


class _BooleanMessageComponent(MessageComponentBase[bool]):
  def __init__(self, mcp: McpApi) -> None:
    super().__init__(bool)
    self.__mcp = mcp

  def _insert(self, message_handle, value: bool) -> None:
    self.__mcp.AppendBool(message_handle, value)

  def _extract(self, message_handle) -> bool:
    return self.__mcp.ExtractBool(message_handle)


class _StringMessageComponent(MessageComponentBase[str]):
  def __init__(self, mcp: McpApi) -> None:
    super().__init__(str)
    self.__mcp = mcp

  def _insert(self, message_handle, value: str) -> None:
    self.__mcp.AppendString(message_handle, value.encode('utf-8'))

  def _extract(self, message_handle) -> str:
    string_length = self.__mcp.GetNextStringLength(message_handle)
    if string_length == 0:
      self.__mcp.ExtractString(
        message_handle, ctypes.c_char_p(), string_length)
      return ''

    string_buffer = ctypes.create_string_buffer(string_length)
    self.__mcp.ExtractString(message_handle, string_buffer, string_length)
    return string_buffer.value.decode('utf-8')


class _TextMessageComponent(MessageComponentBase[SerialisedText]):
  def __init__(self, mcp: McpApi) -> None:
    super().__init__(SerialisedText)
    self.__mcp = mcp

  def _insert(self, message_handle, value: SerialisedText) -> None:
    with value.to_text_handle() as text_handle:
      self.__mcp.AppendText(message_handle, text_handle)

  def _extract(self, message_handle) -> ReceivedSerialisedText:
    return ReceivedSerialisedText.from_handle(message_handle)


class PrimitiveFactory(ComponentFactory):
  """Factory which handles primitive types.

  This can create message components for integers, floats, booleans, strings
  and text.

  Parameters
  ----------
  mcp
    MCP DLL to use to append and extract components to and from messages.
  """
  def __init__(self, mcp: McpApi) -> None:
    self.__mcp = mcp
    self.__component_types: dict[
      type[Primitives],
      typing.Callable[[McpApi], MessageComponent]
    ] = {
      Int8s : functools.partial(
        _IntegerMessageComponent,
        data_type=Int8s
      ),
      Int16s : functools.partial(
        _IntegerMessageComponent,
        data_type=Int16s
      ),
      Int32s : functools.partial(
        _IntegerMessageComponent,
        data_type=Int32s
      ),
      Int64s : functools.partial(
        _IntegerMessageComponent,
        data_type=Int64s
      ),
      Int8u : functools.partial(
        _IntegerMessageComponent,
        data_type=Int8u
      ),
      Int16u : functools.partial(
        _IntegerMessageComponent,
        data_type=Int16u
      ),
      Int32u : functools.partial(
        _IntegerMessageComponent,
        data_type=Int32u
      ),
      Int64u : functools.partial(
        _IntegerMessageComponent,
        data_type=Int64u
      ),
      Float : functools.partial(
        _FloatMessageComponent,
        data_type=Float
      ),
      Double : functools.partial(
        _FloatMessageComponent,
        data_type=Double
      ),
      bool: _BooleanMessageComponent,
      str: _StringMessageComponent,
      SerialisedText: _TextMessageComponent,
      ReceivedSerialisedText: _TextMessageComponent,
    }

  def supports_type(self, data_type: type) -> bool:
    return data_type in self.__component_types

  def get(self, data_type: type[Primitives]) -> MessageComponent[Primitives]:
    try:
      return self.__component_types[data_type](self.__mcp)
    except KeyError:
      raise DataTypeNotSupported(
        f"Unsupported primitive type in message: {data_type}"
      ) from None
