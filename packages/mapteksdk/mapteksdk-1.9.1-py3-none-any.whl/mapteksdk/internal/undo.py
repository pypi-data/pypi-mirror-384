"""Class which handle undo."""
###############################################################################
#
# (C) Copyright 2023, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

from collections.abc import Sequence
import typing

from .comms import Int32u, default_manager
from .transaction import TransactionRequest
from .qualifiers import QualifierSet, Qualifiers
from .before_undo_state import BeforeUndoState

if typing.TYPE_CHECKING:
  from mapteksdk.data import ObjectID, ChangeReasons

class UndoNotSupportedError(Exception):
  """Error raised if undo is not supported."""


class StackClosedError(Exception):
  """Error raised if the undo stack is closed.

  Typically, this is raised when attempting to mutate an UndoStack after
  sending it to the application, or when attempting to send the UndoStack to
  the application more than once.
  """


class UndoItem(typing.NamedTuple):
  """A single item in an UndoStack.

  This contains information required to undo the changes made to a
  single object.
  """
  before_id: ObjectID
  """A clone of the object before any changes were made."""
  primary_children: set[ObjectID]
  """Primary children of the object before any changes were made."""
  after_id: ObjectID
  """The object after changes were made."""
  change_reasons: ChangeReasons
  """Change reasons recorded for the change."""


class UndoStack(Sequence):
  """A stack of operations which can be undone in the application.
  """
  def __init__(self) -> None:
    self.__items: list[UndoItem] = []
    self.__closed: bool = False
    """If the undo stack is closed."""
    self.__sent: bool = False
    """If the undo stack has been sent to the application."""
    self._closed_error_message: str | None=None

  def __getitem__(self, index: int) -> UndoItem:
    return self.__items[index]

  def __len__(self) -> int:
    return len(self.__items)

  @property
  def is_closed(self) -> bool:
    """True if the UndoStack is closed, False otherwise.

    It is an error to add new changes to a closed undo stack.
    """
    return self.__closed

  @property
  def was_sent(self) -> bool:
    """True if the UndoStack has been sent to the application."""
    return self.__sent

  def close(self, error_message=None):
    """Close the UndoStack.

    This prevents any new changes being added to the stack and stops
    the stack from being sent to the application.

    Parameters
    ----------
    error_message
      Error message to place in the StackClosedError if attempting to add to
      the stack after it is closed.
    """
    self.__closed = True
    if error_message is not None:
      self._closed_error_message = error_message

  def raise_if_closed(self):
    """Raise a StackClosedError if the stack is closed."""
    if self.__closed:
      if self._closed_error_message is not None:
        message = self._closed_error_message
      else:
        message = "Cannot add any more changes to be undone."
      raise StackClosedError(
        message
      )

  def add_operation(
      self,
      before_id: ObjectID,
      after_id: ObjectID,
      change_reason: ChangeReasons,
      primary_children: set[ObjectID]):
    """Add an operation to the list of items which can be undone.

    Parameters
    ----------
    before_id
      ObjectID of a clone of the object before the changes were made.
    after_id
      ObjectID of the object which was changed.
    change_reasons
      Change reasons reported by the save() function.

    Raises
    ------
    UnsupportedUndoOperationError
      If before_id is an unsupported type.
    StackClosedError
      If the undo stack has already been sent to the application.
    """
    if change_reason.value == 0:
      return
    self.raise_if_closed()
    self.__items.append(
      UndoItem(before_id, primary_children, after_id, change_reason)
    )

  def send_to_application(self):
    """Create the undo checkpoint in the application.

    This allows the changes to be undone by pressing the undo button
    in the application.

    Raises
    ------
    StackClosedError
      If this stack has already been sent to the application.
    """
    if self.__sent:
      raise StackClosedError("Cannot send stack to the application twice.")
    self.__sent = True
    self.close()

    if len(self) == 0:
      # No need to send a message if the stack is empty.
      return

    manager = default_manager()
    request = TransactionRequest(manager)
    request.transaction = "mtp::cadS_EditObjectTransaction"
    request.qualifiers = QualifierSet()

    before_handles = [
      BeforeUndoState(item.before_id, item.primary_children)
      for item in self.__items]
    after_handles = [item.after_id for item in self.__items]
    change_reasons = [
      Int32u(item.change_reasons.value) for item in self.__items]

    request.qualifiers.values = [
      Qualifiers.user_data(
        "beforeObjects",
        "class std::vector<class mtp::cadC_BeforeUndoState,"
        "class std::allocator<class mtp::cadC_BeforeUndoState> >",
        before_handles
      ),
      Qualifiers.user_data(
        "afterObjects",
        "class std::vector<class mdf::deC_ObjectId,"
        "class std::allocator<class mdf::deC_ObjectId> >",
        after_handles
      ),
      Qualifiers.user_data(
        "changeReasons",
        "class std::vector<unsigned int,class std::allocator<unsigned int> >",
        change_reasons
      )
    ] # type: ignore

    request.send("cadServer")
