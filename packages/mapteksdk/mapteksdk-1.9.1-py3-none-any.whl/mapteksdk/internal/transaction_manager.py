"""Request transactions without using the Workflows system.

This is an alternative to the classes defined in transactions.py.
Unlike RequestTransactionWithInputs, this requests the transaction the
same way as C++ code in the application would do it. This provides more
versatility than RequestTransactionWithInputs, however it is more difficult
to automate and read outputs.

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
from __future__ import annotations

import warnings
import logging
import typing

from .transaction_base import (
  TransactionBase,
  TransactionKey,
)
from .transaction_manager_protocol import TransactionManagerProtocol
from .transaction_messages import (
  ReceivedTransactionCancelHeader,
  ReceivedTransactionConfirmHeader
)

if typing.TYPE_CHECKING:
  from contextlib import AbstractContextManager

  from .comms import CommunicationsManager
  from .comms.message_handle import IncomingMessageHandle

LOG = logging.getLogger("mapteksdk.internal.transaction_manager")

T = typing.TypeVar("T", bound=TransactionBase)


class TransactionManager(TransactionManagerProtocol):
  """Manages MCP messages related to transactions.

  This class maintains a list of all of the transactions it has started.
  When an MCP event arrives which is relevant to one of these transactions,
  it parses enough of the message to identify which transaction the message
  is for. It then passes the remainder of that message to the transaction
  for handling.

  Parameters
  ----------
  comms_manager
    The communications manager to use to send and receive messages.
  """
  default_timeout: typing.ClassVar[float | None]=None
  """The default time out for operations.

  This is None by default, indicating operations should only time out if the
  caller specifies a timeout.
  """

  def __init__(self, comms_manager: CommunicationsManager):
    self._comms_manager = comms_manager
    """Manager to use to send and receive messages."""
    self.__callbacks: list[AbstractContextManager] = []
    """List of MCP callbacks.

    This is used to ensure that all callbacks are disposed when this object
    is exited.
    """

    self.__transactions: dict[
      TransactionKey, TransactionBase] = {}
    """Dictionary of transactions this object is keeping track of.

    The keys are a tuple of the transaction address and transaction token,
    and the values are the actual Transaction objects.
    """

  def __enter__(self):
    def _on_transaction_confirm(message_handle: IncomingMessageHandle):
      """Callback run when a TransactionConfirm message arrives."""
      # This reads the generic parts of the TransactionConfirm.
      # It doesn't read to the end of the message, only the
      # generic part at the beginning.
      # Because of this piecemeal method of reading, this cannot use
      # callback_on_receive().
      event = message_handle.extract(ReceivedTransactionConfirmHeader)
      try:
        # pylint: disable=no-member
        # Pylint incorrectly deduces the type of event as Message
        # instead of TransactionConfirm.
        # See: https://github.com/PyCQA/pylint/issues/981
        transaction = self.__transactions[
            (int(event.transaction_address), int(event.transaction_token))
          ]
        transaction.confirm(message_handle)
      except KeyError:
        # pylint: disable=no-member
        # Same issue as in the try block.
        LOG.info(
          "Received TransactionConfirm for: "
          "transaction_address: %s "
          "transaction token: %s "
          "But it was not found in the transaction list",
          event.transaction_address, event.transaction_token)

    def _on_transaction_cancel(event: ReceivedTransactionCancelHeader):
      """Callback run when a TransactionCancel message arrives."""
      try:
        # pylint: disable=no-member
        transaction = self.__transactions[
          (int(event.transaction_address), int(event.transaction_token))
        ]
        transaction.cancel()

      except KeyError:
        # pylint: disable=no-member
        LOG.info(
          "Received TransactionCancel for: "
          "transaction_address: %s "
          "transaction token: %s "
          "But it was not found in the transaction list",
          event.transaction_address, event.transaction_token)

    self.__callbacks.append(
      self._comms_manager.callback_on_message(
        "TransactionConfirm",
        _on_transaction_confirm)
    )
    self.__callbacks.append(
      ReceivedTransactionCancelHeader.callback_on_receive(
        _on_transaction_cancel,
        self._comms_manager
      )
    )
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    if len(self.__transactions) != 0:
      count = len(self.__transactions)
      warnings.warn(
        RuntimeWarning(
          f"{count} transactions were not removed."
        )
      )
    for transaction in list(self.__transactions.values()):
      self._remove_transaction(transaction)
    for callback in self.__callbacks:
      callback.__exit__(None, None, None)

  def create_transaction(
      self,
      transaction_type: type[T],
      parent_transaction: TransactionBase | None=None
      ) -> T:
    transaction = transaction_type(
      self, self._comms_manager, parent_transaction)
    key = transaction.key()
    self.__transactions[key] = transaction
    return transaction

  def _remove_transaction(self, transaction: TransactionBase):
    try:
      del self.__transactions[transaction.key()]
    except KeyError:
      pass
