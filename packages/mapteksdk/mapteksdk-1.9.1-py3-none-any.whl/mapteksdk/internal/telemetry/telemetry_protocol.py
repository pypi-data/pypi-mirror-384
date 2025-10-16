"""Protocol for classes which can record and send telemetry.

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

# pylint: disable=unused-argument
def _null_function(*args, **kwargs):
  """A function which accepts any arguments and does nothing.

  This is returned if a Telemetry function which does not exist is accessed
  to ensure that telemetry will not raise an error for undefined functions.
  """

class TelemetryProtocol(typing.Protocol):
  """Protocol for managing telemetry."""
  def record_function_call(self, name: str):
    """Record a function call."""
    raise NotImplementedError

  def record_object_size(self, name: str, size: int):
    """Record the size of an object."""
    raise NotImplementedError

  def send(self):
    """Send the telemetry.

    Once telemetry has been sent, no further telemetry can be recorded.
    """
    raise NotImplementedError

  def __getattr__(self, name):
    # Return a null function, so that calling an undefined telemetry function
    # will do nothing instead of raising an error.
    return _null_function
