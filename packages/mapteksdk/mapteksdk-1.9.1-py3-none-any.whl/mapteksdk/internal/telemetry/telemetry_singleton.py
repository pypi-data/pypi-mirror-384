"""Singleton access to a single telemetry instance.

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

import contextlib
import logging
import os

from .null_telemetry import NullTelemetry
from .telemetry import Telemetry
from .telemetry_protocol import TelemetryProtocol

# pylint: disable=global-statement

LOG = logging.getLogger("mapteksdk.telemetry_singleton")
_TELEMETRY: TelemetryProtocol | None = None
"""The telemetry singleton."""

class _SendTelemetryManager(contextlib.AbstractContextManager):
  """Context manager which sends telemetry on exit."""
  def __exit__(
    self,
    exc_type: type[BaseException] | None,
    exc_value: BaseException | None,
    traceback
  ) -> bool | None:
    global _TELEMETRY
    telemetry = _TELEMETRY
    # Clear the telemetry to avoid a double send.
    _TELEMETRY = None
    if telemetry:
      telemetry.send()

def enable_telemetry() -> contextlib.AbstractContextManager:
  """Enable for telemetry to be sent.

  Returns a context manager which when closed will cause the telemetry to be
  sent. If this is called multiple times, telemetry will only be sent when the
  first context manager returned is sent.
  """
  global _TELEMETRY
  if _TELEMETRY is not None:
    LOG.info("Telemetry already set up.")
    return contextlib.nullcontext()

  if os.environ.get("MAPTEK_TELEMETRY_DISABLED", ""):
    LOG.info("Telemetry is disabled.")
    _TELEMETRY = NullTelemetry()
    return contextlib.nullcontext()

  if os.environ.get("MTK_TESTER", ""):
    LOG.info("Telemetry is disabled on test machines.")
    _TELEMETRY = NullTelemetry()
    return contextlib.nullcontext()

  _TELEMETRY = Telemetry()
  return _SendTelemetryManager()

def get_telemetry() -> TelemetryProtocol:
  """Get the singleton object which can be used to record telemetry."""
  if _TELEMETRY is None:
    return NullTelemetry()
  return _TELEMETRY
