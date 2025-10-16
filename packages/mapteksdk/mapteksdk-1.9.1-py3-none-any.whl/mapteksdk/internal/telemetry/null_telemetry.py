"""Null telemetry.

This is an implementation of the null object pattern for telemetry.

Warnings
--------
Vendors and clients should not develop scripts or applications against
this package. The contents may change at any time without warning.
"""
from __future__ import annotations

from .telemetry_protocol import TelemetryProtocol

class NullTelemetry(TelemetryProtocol):
  """Null telemetry.

  This does not record any telemetry.
  """
  def record_function_call(self, name: str):
    pass

  def record_object_size(self, name: str, size: int):
    pass

  def send(self):
    pass
