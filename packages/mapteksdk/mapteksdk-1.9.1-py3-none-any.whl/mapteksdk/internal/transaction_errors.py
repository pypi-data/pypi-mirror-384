"""Errors raised by the TransactionManager.

These errors are not intended to be user facing and should be caught by
callers and converted into user-friendly errors.

Despite the similar names, this has no relation to anything in transaction.py.

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

class TransactionFailedError(Exception):
  """Error raised when a transaction fails.

  This may indicate this operation is not supported by the application.
  """


class TransactionSetUpError(TransactionFailedError):
  """Exception thrown when failing to start a transaction.

  This indicates the server returned an error response to TransactionRequest.

  Parameters
  ----------
  transaction_name
    Name of the menu command which could not be created.
  """
  def __init__(self, transaction_name: str):
    self.transaction_name = transaction_name
    super().__init__(
      f"Failed to start menu command: {transaction_name}."
    )


class TransactionCancelledError(Exception):
  """Error raised when a menu command is cancelled.

  This indicates the user pressed "Cancel" or closed the window
  without confirming it.
  """
  def __init__(self, transaction_name: str):
    self.transaction_name = transaction_name
    super().__init__(
      f"The following command was cancelled: {transaction_name}."
    )


class TransactionTimeoutError(Exception):
  """Error raised when a transaction times out."""
  def __init__(self, transaction_name: str, timeout: float) -> None:
    super().__init__(
      f"{transaction_name} failed to return a response in {timeout}s."
    )
