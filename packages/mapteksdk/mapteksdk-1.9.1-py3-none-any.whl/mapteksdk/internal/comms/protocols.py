"""Protocols defined for communication.

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


class Serialisable(Protocol):
  """Protocol defining classes which can be serialised for MCP messages.

  This allows for classes to define how they are serialised to the MCP
  without the class needing to depend on the comms package or vice
  versa.
  """
  storage_type: typing.ClassVar
  """The type this class is stored as when serialised for MCP messages."""

  @classmethod
  def convert_from(cls, value) -> "typing.Self":
    """Create an instance of this type from the storage type."""
    ... # pylint: disable=unnecessary-ellipsis

  def convert_to(self) -> typing.Any:
    """Convert this instance to its storage type."""
