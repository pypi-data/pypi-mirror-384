"""MCP messages for handling transactions using the TransactionManager.

These messages are separated into a "Header" and a "Body".
The header contains information which is the same regardless of which
transaction the message is for.
The body contains the information which varies depending on the transaction.
This is an Inline message which is provided by the Transaction class. They
are defined in transaction_elemental.py (and generated at runtime
in transaction_compound.py).

Splitting up the messages like this is required because the header of the
message must be read to determine what the transaction the message is for,
and thus what content can be found in the body of the transaction.


Warnings
--------
Vendors and clients should not develop scripts or applications against
this package. The contents may change at any time without warning.
"""

###############################################################################
#
# (C) Copyright 2023, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

import typing

from .comms import (
  Request,
  Response,
  InlineMessage,
  Message,
  Int64u,
)
from .qualifiers import QualifierSet
from .serialisation import Context
from .transaction_request_data import (
  TransactionRequestData,
  TransactionRequestDataList,
)

T = typing.TypeVar("T")

class TransactionConfirmHeader(InlineMessage):
  """The header for a TransactionConfirm message."""
  transaction_address: Int64u
  """The address of the transaction which was confirmed.

  This will be the same as in the corresponding TransactionCreate
  message.
  """

  transaction_token: Int64u
  """The token of the transaction which was confirmed.

  This will be the same as in the corresponding TransactionCreate
  message
  """
  context: Context

  def __init__(self) -> None:
    self.context = Context.default_context()


class NoChildren(InlineMessage):
  """Placeholder for no children.

  This is used for TransactionCreate for elemental transactions to avoid
  adding an empty sub message. This matches the behaviour of the applications.
  """


class TransactionCreateHeader(InlineMessage):
  """The header for a non-compound TransactionCreate.

  This is the part of the header which does not differ for compound /
  elemental transactions.
  """
  manager_address: Int64u
  request_data: TransactionRequestData
  """The data of the transaction to request."""


class TransactionCancelHeader(InlineMessage):
  """The header for a TransactionCancel message.

  This is more detailed than the TransactionCancel class available in
  the Python SDK because the Python SDK only reads the first few fields
  of the message. As this needs to be sent, it contains the entire header
  of the message.
  """
  top_level_transaction_address: Int64u
  """The address of the top-level transaction which was cancelled."""

  transaction_token: Int64u
  """The token of the transaction which was cancelled."""

  transaction_address: Int64u
  """The address of the transaction which was cancelled."""

  context: Context
  """The context of the cancelled transaction.

  As of 2023-06-06 this is not read by the Python SDK. It is included
  here so that the send message matches what would be send by an
  application.
  """
  def __init__(
      self,
      top_level_transaction_address: Int64u,
      transaction_token: Int64u,
      transaction_address: Int64u) -> None:
    self.top_level_transaction_address = top_level_transaction_address
    self.transaction_token = transaction_token
    self.transaction_address = transaction_address
    self.context = Context.default_context()

class TransactionCreate(Request):
  """A message requesting for a transaction to be created."""
  class CreateResponse(Response):
    """The response to a TransactionCreate message."""
    success: bool
    """True if the transaction was successfully started."""
    server_address: Int64u
    """The address of the transaction on the server."""

  @classmethod
  def message_name(cls) -> str:
    return "TransactionCreate"

  @classmethod
  def response_type(cls) -> type[CreateResponse]:
    return cls.CreateResponse

  def send(self, destination: str) -> CreateResponse:
    return super().send(destination) # type: ignore

  header: TransactionCreateHeader
  child_requests: typing.Union[
    TransactionRequestDataList,
    NoChildren,
  ]
  body: InlineMessage
  """Initial values to place into the panel.

  This is typically (but not required to be) a TransactionData subclass.
  """

class TransactionConfirm(Message):
  """Message for confirming a transaction."""
  @classmethod
  def message_name(cls) -> str:
    return "TransactionConfirm"

  header: TransactionConfirmHeader
  body: InlineMessage

class TransactionCancel(Message):
  """Message for cancelling a transaction."""
  @classmethod
  def message_name(cls) -> str:
    return "TransactionCancel"

  header: TransactionCancelHeader
  body: InlineMessage


class TransactionDestroy(Message):
  """Destroy a transaction on the server."""
  @classmethod
  def message_name(cls) -> str:
    return "TransactionDestroy"

  parent_transaction_address: Int64u
  """The address of the parent transaction of the transaction to destroy."""

  transaction_address: Int64u
  """The address of the transaction to destroy."""


class TransactionSynch(Message):
  """Synchronise changes to the Transaction between client and server."""
  @classmethod
  def message_name(cls) -> str:
    return "TransactionSynch"
  parent_address: Int64u
  """The address of the parent of the transaction to synchronise."""
  transaction_address: Int64u
  """The address of the transaction to synchronise."""
  qualifiers: typing.Optional[QualifierSet]
  """Qualifiers to update for the Transaction.

  If None, no changes to the qualifiers will be made.
  """
  body: typing.Optional[InlineMessage]
  """The update body of the Transaction.

  If None, no changes to the body will be made.
  """


class ReceivedTransactionConfirmHeader(Message):
  """A message indicating a transaction has been confirmed.

  This does not parse the entire TransactionConfirm message. Instead
  it only parses the generic part of the message. This is used to identify
  which transaction was confirmed. The transaction then parses the remainder
  of the message (typically via a TransactionData subclass).

  This can never be sent by Python, only received.
  """
  @classmethod
  def message_name(cls) -> str:
    return "TransactionConfirm"

  transaction_address: Int64u
  """The address of the transaction which was confirmed.

  This will be the same as in the corresponding TransactionCreate
  message.
  """

  transaction_token: Int64u
  """The token of the transaction which was confirmed.

  This will be the same as in the corresponding TransactionCreate
  message
  """

  def send(self, destination):
    raise TypeError(
      "This type of message is a response only. It shouldn't be sent."
    )


class ReceivedTransactionCancelHeader(Message):
  """A message indicating a transaction has been cancelled.

  This does not parse the entire TransactionCancel message. Instead it
  only parses the generic part of the message. This is used to identify which
  transaction was cancelled.

  This can never be sent by Python, only received.
  """
  @classmethod
  def message_name(cls) -> str:
    return "TransactionCancel"

  top_level_transaction_address: Int64u
  """The address of the top-level transaction which was cancelled."""

  transaction_token: Int64u
  """The token of the transaction which was cancelled."""

  transaction_address: Int64u
  """The address of the transaction which was cancelled."""

  def send(self, destination):
    raise TypeError(
      "This type of message is a response only. It shouldn't be sent."
    )
