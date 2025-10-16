"""Protocol followed by the transaction manager.

This defines the public interface of the transaction manager. Client classes
should only call the functions defined in the protocol.

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

import typing

from .protocol import Protocol


if typing.TYPE_CHECKING:
  from .transaction_base import TransactionBase
  T = typing.TypeVar("T", bound=TransactionBase)


class TransactionManagerProtocol(Protocol):
  """Public interface for the transaction manager."""
  def create_transaction(
      self,
      transaction_type: type[T],
      parent_transaction: TransactionBase | None=None
      ) -> T:
    """Create a new transaction managed by this object.

    The transaction is not immediately sent to the server, allowing for set
    up to be performed before calling the send() function on the transaction.

    Parameters
    ----------
    transaction_type
      The type of the transaction to create. This must be a TransactionBase
      subclass.
    parent_transaction
      An existing transaction which has already been created by this object.
      If None, the newly created transaction is a top-level transaction.

    Returns
    -------
    TransactionBase
      The newly created Transaction.
    """
    raise NotImplementedError

  def _remove_transaction(self, transaction: TransactionBase):
    """Remove the transaction from the transaction manager.

    This will cause MCP events intended for this transaction to be
    ignored. This will do nothing if the transaction has already been
    removed, or was never added to this object.

    Parameters
    ----------
    transaction
      The transaction to remove.
    """
    raise NotImplementedError
