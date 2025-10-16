"""Compound transactions for the transaction manager.

These are transactions which contain other transactions.
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
from __future__ import annotations

import typing

from .comms import CommunicationsManager
from .transaction_base import CompoundTransactionBase, TransactionBase
from .transaction_elemental import (
  CoordinateTransaction,
  PrimitiveTransaction,
  CommandTransaction,
)
from .transaction_mixins import (
  MessageMixin,
  IconMixin,
  TitleMixin,
)
from .qualifiers import Qualifiers, InstanceTypes, Qualifier

if typing.TYPE_CHECKING:
  from collections.abc import Sequence, Iterable, Callable

  from ..common.typing import Point, PointLike
  from ..data import ObjectID
  from ..operations import SelectablePrimitiveType
  from .transaction_manager_protocol import (
    TransactionManagerProtocol,
  )

  class CoordinatePickTransactionChildren(typing.TypedDict):
    """Static type checking for coordinate pick transaction's children."""
    coordinate: "CoordinateTransaction"


  class PrimitivePickTransactionChildren(typing.TypedDict):
    """Static type checking for primitive pick transaction's children."""
    primitive: "PrimitiveTransaction"


class CoordinatePickTransaction(CompoundTransactionBase):
  """Transaction which allows the user to perform a single coordinate pick."""
  _child_transactions: "CoordinatePickTransactionChildren" # type: ignore
  @staticmethod
  def name() -> str:
    return 'py::pyC_CoordinatePickTransaction'

  @staticmethod
  def data_type_name() -> str:
    return 'mdf::serC_DataGroup'

  @classmethod
  def _default_qualifiers(cls) -> Sequence[Qualifier]:
    return [
      Qualifiers.instance_type(InstanceTypes.SEQUENCE),
      Qualifiers.title("Python")
    ]

  @staticmethod
  def child_transaction_types():
    return (
      ("coordinate", CoordinateTransaction),
    )

  def initialise_child_transactions(self):
    child = self._child_transactions["coordinate"]
    # Always add the world pick hint qualifier.
    child.add_world_pick_hint()

    # When the child is confirmed, confirm this transaction.
    def confirm_parent(_):
      self._confirm()
    child.register_confirm_callback(confirm_parent)

  @property
  def coordinate(self) -> "Point":
    """The picked coordinate as a NumPy array."""
    return self._child_transactions["coordinate"].coordinate

  @coordinate.setter
  def coordinate(self, new_point: "PointLike"):
    self._child_transactions["coordinate"].coordinate = new_point

  def set_label(self, label: str):
    """Set the label of the child request."""
    self._child_transactions["coordinate"].label = label

  def set_support_label(self, support_label: str):
    """Set the support label for the child request."""
    self._child_transactions["coordinate"].support_label = support_label

  def set_help(self, help_text: str):
    """Set the help for the child request."""
    self._child_transactions["coordinate"].help = help_text


class PrimitivePickTransaction(CompoundTransactionBase):
  """Transaction for a primitive pick.

  This causes the pick to be realised in the status bar at the
  bottom of the screen.
  """
  _child_transactions: "PrimitivePickTransactionChildren" # type: ignore
  @staticmethod
  def name() -> str:
    return "py::pyC_PrimitivePickTransaction"

  @classmethod
  def _default_qualifiers(cls) -> Sequence[Qualifier]:
    return [
      Qualifiers.instance_type(InstanceTypes.SEQUENCE),
      Qualifiers.title("Python")
    ]

  @staticmethod
  def child_transaction_types():
    return (
      ("primitive", PrimitiveTransaction),
    )

  def initialise_child_transactions(self):
    child = self._child_transactions["primitive"]
    # When the child is confirmed, confirm this transaction.
    def confirm_parent(_):
      self._confirm()
    child.register_confirm_callback(confirm_parent)

  def set_primitive_type(self, primitive_type: "SelectablePrimitiveType"):
    """Set the primitive type of the pick."""
    self._child_transactions["primitive"].primitive_type = primitive_type

  def set_label(self, label: str):
    """Set the label of the child request."""
    self._child_transactions["primitive"].label = label

  def set_support_label(self, support_label: str):
    """Set the support label for the child request."""
    self._child_transactions["primitive"].support_label = support_label

  def set_help(self, help_text: str):
    """Set the help for the child request."""
    self._child_transactions["primitive"].help = help_text

  def add_locate_on_objects(self, oids: "Iterable[ObjectID]"):
    """Restrict the pick to be on the given object.

    This can be called more than once. If so, then the pick is restricted
    to be located on any of the given objects.
    """
    child = self._child_transactions["primitive"]
    for oid in oids:
      child.add_locate_on_object(oid)

  @property
  def owner_id(self) -> "ObjectID":
    """Object ID of the object which owns the selected primitive.

    This will be the null object ID before the transaction is confirmed.
    """
    return self._child_transactions["primitive"].owner_id

  @property
  def index(self) -> int:
    """Index of the selected primitive in the owning object.

    This will be zero before the transaction is confirmed.
    """
    return self._child_transactions["primitive"].index


class QuestionTransaction(
    CompoundTransactionBase,
    IconMixin,
    MessageMixin,
    TitleMixin):
  """Transaction for asking a question with multiple possible responses.

  Use the add_response() function to add the possible responses to the question.
  The title property will set the title of the window containing the question.
  The icon property will set the icon of the window containing the question.
  The message property will set the question displayed at the top of the window.
  """
  def __init__(
      self,
      manager: "TransactionManagerProtocol",
      comms_manager: "CommunicationsManager",
      parent: TransactionBase | None) -> None:
    super().__init__(manager, comms_manager, parent)
    self.__selected_index: int | None = None
    self.__has_received_cancel: bool = False
    """If this transaction has been cancelled.

    When a child of the question Transaction is confirmed, the question
    transaction also receives a TransactionCancel message. And when it is
    cancelled, it receives two TransactionCancel messages. To ensure this
    is only cancelled when it is cancelled, the first TransactionCancel
    message is always ignored.
    """

  @staticmethod
  def name() -> str:
    return "mdf::uiC_QuestionTransaction"

  @staticmethod
  def data_type_name() -> str:
    return "mdf::uiS_Question"

  @classmethod
  def _default_qualifiers(cls) -> Sequence[Qualifier]:
    return [
      Qualifiers.instance_type(InstanceTypes.CHOICE)
    ]

  @staticmethod
  def child_transaction_types():
    return tuple()

  def cancel(self):
    if self.__selected_index is not None:
      # A child has been confirmed, so ignore all TransactionCancel messages.
      # Even the user selects a response, this transaction will still receive
      # two cancel messages.
      return

    # This transaction may receive a cancel message before a confirm for one
    # of its children, so always ignore the first cancel message. A second
    # cancel is required to cancel this.
    if not self.__has_received_cancel:
      self.__has_received_cancel = True
    else:
      super().cancel()

  def add_response(
      self,
      setup_child: Callable[[CommandTransaction], None]):
    """Add a possible response to the question.

    Parameters
    ----------
    setup_child
      Function which sets up the command transaction which represents the
      new response.
    """
    child_index = len(self._child_transactions)
    def confirm_callback(_: CommandTransaction):
      self.__selected_index = child_index
      self._confirm()

    child = self._manager.create_transaction(
      CommandTransaction,
      self
    )
    setup_child(child)

    child.register_confirm_callback(confirm_callback)

    # :HACK: This only works because CommandTransaction does not have a body,
    # so it doesn't affect what needs to be send / received from the server.
    self._child_transactions[str(child_index)] = child

  @property
  def selected_index(self) -> int:
    """The index of the child which was selected.

    Raises
    ------
    RuntimeError
      If this is called before the user has selected an option.
    """
    if self.__selected_index is None:
      raise RuntimeError(
        "The user has not selected a result."
      )
    return self.__selected_index
