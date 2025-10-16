"""Types for communicating with Maptek Applications.

Code outside of this package should only import from this file.
Every class not revealed here should be treated as an internal implementation
detail and not imported.

The types for working with the communication layer in Maptek applications that
use the Master Control Program (MCP).
"""
###############################################################################
#
# (C) Copyright 2024, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import typing

from .default_communications_manager import DefaultCommunicationsManager
from .communication_manager import CommunicationsManager
from .errors import DataTypeNotSupported, MalformedMessageError
from .message import Message
from .inline_message import InlineMessage
from .sub_message import SubMessage
from .request import Request, Response
from .types import (
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
)

if typing.TYPE_CHECKING:
  from ...capi import McpApi


def default_manager(mcp: McpApi | None=None) -> CommunicationsManager:
  """Get a default communications manager object.

  This returns a new manager each time this is called.

  The default communication manager uses the MCP to send and receive messages
  with application. Message classes intended to be sent using this
  communication manager can include:

  * `Message`
  * `Request`
  * `Response`
  * `SubMessage`
  * `InlineMessage`
  * `str`
  * `bool`
  * `SerialisedText`
  * `ReceivedSerialisedText`
  * The integer and float types defined in types.py.
  * The structure types defined in base_message.py.
  * `typing.Any` (Only when inserting into a message).
  """
  manager =  DefaultCommunicationsManager(mcp)
  return manager
