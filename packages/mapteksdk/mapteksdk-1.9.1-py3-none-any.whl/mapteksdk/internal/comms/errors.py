"""Errors raised by the comms module.

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

class FailedToCreateMessageError(Exception):
  """A Message to send to an application could not be created.

  This is raised if the C API returns a null message handle.
  """


class DataTypeNotSupported(Exception):
  """A MCP message included a data type which is not supported."""


class MalformedMessageError(Exception):
  """Exception raised when a message is malformed."""


class MessageDeletedError(Exception):
  """Exception raised when an operation is performed on a deleted message."""
  def __init__(self, *args) -> None:
    super().__init__(
      "Attempted to access a deleted message. "
      "This likely indicates a bug in the mapteksdk package. Please report "
      "steps to replicate this error to Maptek via the 'Request Support' "
      "function in the Workbench.",
      *args
    )


class ResponseNotSentError(Exception):
  """Exception raised when a response to a request was not sent.

  This exception indicates that Python received a request but never attempted
  to send a response. This may cause the requester to loop infinitely
  waiting for a response. The code which reaches this exception should be
  unreachable
  """
