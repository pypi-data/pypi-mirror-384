"""Enum representing the state of a transaction.

Despite the similar names, this has no relation to anything in transaction.py.

Warnings
--------
Vendors and clients should not develop scripts or applications against
this package. The contents may change at any time without warning.
"""

import enum

class TransactionState(enum.Enum):
  """The state of a transaction.

  This does not correspond to the state on the C++ side. This is simply a
  useful way for Python to keep track of the state of its transaction
  objects.
  """
  PENDING = 0
  """The transaction has not been sent to the server yet."""

  ACTIVE = 1
  """The transaction has been sent to the server.

  It is currently awaiting user input.
  """

  FINAL = 2
  """The transaction has been confirmed.

  The user has provided input and it has been populated to this object.
  """

  CANCELLED = 3
  """The transaction has been cancelled."""

  FAILED = 255
  """The transaction has failed.

  Typically this indicates an internal error.
  """
