"""Subpackage containing classes relevant to telemetry.

Warnings
--------
Vendors and clients should not develop scripts or applications against
this package. The contents may change at any time without warning.
"""
import ctypes
import datetime

from .telemetry_singleton import enable_telemetry, get_telemetry
from .telemetry_protocol import TelemetryProtocol

_DTYPE_TELEMETRY: dict[type, str] = {
  type(None) : "null", ctypes.c_bool : "bool", ctypes.c_int8: "int8",
  ctypes.c_uint8 : "int8u", ctypes.c_int16 : "int16",
  ctypes.c_uint16 : "int16u", ctypes.c_int32 : "int32",
  ctypes.c_uint32 : "int32u", ctypes.c_int64 : "int64",
  ctypes.c_uint64 : "int64u", ctypes.c_float : "float32",
  ctypes.c_double : "float64", ctypes.c_char_p : "str",
  datetime.datetime : "datetime", datetime.date : "date",
}

def data_type_to_string(data_type: type) -> str:
  """Convert a data type to a string suitable for telemetry."""
  return _DTYPE_TELEMETRY.get(data_type, "unknown")

__all__ = [
  "enable_telemetry",
  "get_telemetry",
  "data_type_to_string",
  "TelemetryProtocol"
]
