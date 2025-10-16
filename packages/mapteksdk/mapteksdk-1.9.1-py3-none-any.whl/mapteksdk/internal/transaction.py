"""Low level module for working with transactions (menu commands).

The specific transactions which within the Python SDK are known as
operations are provided in per-application modules.

A connection to an existing application is required.

Warnings
--------
Vendors and clients should not develop scripts or applications against
this package. The contents may change at any time without warning.
"""
###############################################################################
#
# (C) Copyright 2020, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from collections.abc import Sequence
import itertools
import threading
import typing

from mapteksdk.internal.normalise_selection import normalise_selection
from mapteksdk.capi import Mcp
from mapteksdk.capi.util import (
  raise_if_version_too_old,
  CApiDllLoadFailureError
)

from .comms import (
  Message,
  Request,
  Response,
  Int32s,
  Int16u,
  Int64u,
  default_manager,
)
from .qualifiers import QualifierSet
from .serialised_text import SerialisedText, ReceivedSerialisedText
from .serialisation import JsonValue, Icon
from .telemetry import get_telemetry

if typing.TYPE_CHECKING:
  from ..data import ObjectID, DataObject
  SelectionLike: typing.TypeAlias = str | ObjectID[DataObject] | DataObject
  TransactionInputs = Sequence[
    tuple[
      str | typing.LiteralString,
      typing.Any
    ]
  ]

NEXT_OPERATION_ID = itertools.count(start=1)


class RequestTransactionWithInputs(Message):
  """Define the message known as RequestTransactionWithInputs.

  This message can be used to request a transaction in an application.
  """

  @classmethod
  def message_name(cls) -> str:
    return 'RequestTransactionWithInputs'

  transaction_name: str
  operation_id: Int32s = 0
  operation_command: str
  requester_icon: Icon = Icon('')
  can_confirm_immediately: bool = True
  confirm_immediately: bool = True
  run_silently: bool = True  # Only present in 1.2+.
  selection_contains_objects: bool = False
  selection_contains_point_primitives: bool = False
  selection_contains_edge_primitives: bool = False
  selection_contains_facet_primitives: bool = False
  transaction_inputs: JsonValue = JsonValue([])

  @classmethod
  def format_selection(
    cls,
    selection: "SelectionLike | Sequence[SelectionLike]"
  ) -> str:
    """Format a list of objects suitable for use as the value of a selection
    in the transaction_inputs.

    This supports ObjectIDs, DataObjects and paths.

    Raises
    ------
    ValueError
      If the selection contains a path to a non-existent object.
    TypeError
      If the selection contains an object which is not an ObjectID,
      DataObject or path.

    Raises
    ------
    ValueError
      If the selection contains a path to a non-existent object.
    TypeError
      If an object in the selection is not of the expected type.
    TypeError
      If the selection contains an object which is not an ObjectID,
      DataObject or path.
    """
    if isinstance(selection, str):
      # String is an iterable, but don't treat it as such here.
      # We don't want to try creating an object id for each character
      # in the string.
      selection = [selection]
    if not isinstance(selection, Sequence):
      selection = [selection]
    actual_selection = normalise_selection(selection)
    return cls.format_normalised_selection(actual_selection)

  @classmethod
  def format_normalised_selection(
    cls,
    selection: "Sequence[ObjectID[DataObject]]"
  ) -> str:
    """Format a normalised selection to a string.

    A normalised selection is any sequence of Object IDs.
    """
    # This uses repr because str on ObjectID will return "Undefined" for
    # null object ids which the C++ code will not be able to parse.
    return ','.join(f'"{obj!r}"' for obj in selection)


class RequestTransactionWithInputsV13(Message):
  """Define the message known as RequestTransactionWithInputs.

  This message can be used to request a transaction in an application.

  This version is needed by PointStudio 2021.1 and later. It approximately
  corresponds to version 1.3 of the API.
  """
  @classmethod
  def message_name(cls) -> str:
    return 'RequestTransactionWithInputs'
  transaction_name: str
  operation_id: Int32s = 0
  operation_command: str
  requester_icon: Icon = Icon('')
  can_confirm_immediately: bool = True
  confirm_immediately: bool = True
  run_silently: bool = True  # Only present in 1.2+.
  pass_all_errors_back_to_requestor: bool = True # Only present in 1.3+
  selection_contains_objects: bool = False
  selection_contains_point_primitives: bool = False
  selection_contains_edge_primitives: bool = False
  selection_contains_facet_primitives: bool = False
  transaction_inputs: JsonValue = JsonValue([])

class OperationCompleted(Message):
  """Define the message known as OperationCompleted.

  This message is sent when a specified transaction has completed.

  It uses the operation_id sent when the transaction was requested to
  determine what request it corresponds with.
  """

  @classmethod
  def message_name(cls) -> str:
    return  'OperationCompleted'

  operation_id: Int32s
  operation_command: str
  outputs: JsonValue
  completed_okay: bool

  def send(self, destination):
    raise TypeError("This type of message is a response only. It shouldn't be "
                    "sent.")


class OperationCompletedV13(Message):
  """Define the message known as OperationCompleted.

  This message is sent when a specified transaction has completed.

  It uses the operation_id sent when the transaction was requested to
  determine what request it corresponds with.

  This version is needed by PointStudio 2021.1 and later. It approximately
  corresponds to version 1.3 of the API.
  """

  @classmethod
  def message_name(cls) -> str:
    return 'OperationCompleted'

  operation_id: Int32s
  operation_command: str
  outputs: JsonValue
  completed_okay: bool

  # This is only present in 1.3+
  error_message: ReceivedSerialisedText

  def send(self, destination):
    raise TypeError("This type of message is a response only. It shouldn't be "
                    "sent.")


class TransactionInformation(Message):
  """Define the message known as TransactionInformation.

  This message can be used to query information about a transaction
  like what its inputs and outputs are.

  The response to the message is ReturnedTransactionInformation.
  """
  @classmethod
  def message_name(cls) -> str:
    return 'TransactionInformation'

  transaction_name: str
  requester_icon: typing.Union[Icon, str] = ''
  operation_command: str


class ReturnedTransactionInformation(Message):
  """Message representing a response to another message. As this message
  is a response, it cannot be sent.

  """
  @classmethod
  def message_name(cls) -> str:
    return  "ReturnedTransactionInformation"

  command_name: str
  transaction_information: JsonValue

  def send(self, destination):
    raise TypeError("This type of message is a response only. It shouldn't be "
                    "sent.")


class TransactionFailed(ValueError):
  """General exception raised when a transaction fails to complete."""
  def __init__(self, server, transaction, message):
    super().__init__(f'Transaction {server}::{transaction} failed to complete '
                     f'successfully. {message}')

class NoProjectError(RuntimeError):
  """Error raised when this module is used without connecting to an application.

  """


class TransactionRequest(Request):
  """Requests a transaction, which is the encapsulation of the concept of a
  transaction between two processes for the provision of specific data or
  specific events.

  For transactions that correspond with menu commands in an application then
  request_transaction() is a far superior option, as it uses the workflow
  system and it is easier to provide inputs and receive outputs.
  """

  class RemoteTransaction(Response):
    """The response back after requesting a transaction."""
    thread_id: Int16u
    transaction_manager_address: Int64u
    transaction_address: Int64u
    transaction_token: Int64u
    top_level_transaction_address: Int64u
    top_level_transaction_token: Int64u

  @classmethod
  def message_name(cls) -> str:
    return 'TransactionRequest'

  @classmethod
  def response_type(cls) -> type[RemoteTransaction]:
    return cls.RemoteTransaction

  transaction: str
  qualifiers: QualifierSet

  # This optionally has a context that can be provided.
  # At this time we don't have a use for this.
  # context: Context = None

@typing.overload
def request_transaction(
  server: str,
  transaction: str,
  command_name: str,
  inputs: "TransactionInputs",
  wait: typing.Literal[True]=True,
  requester_icon: Icon=Icon(''),
  confirm_immediately: bool=True
) -> JsonValue:
  ...

@typing.overload
def request_transaction(
  server: str,
  transaction: str,
  command_name: str,
  inputs: "TransactionInputs",
  wait: typing.Literal[False],
  requester_icon: Icon=Icon(''),
  confirm_immediately: bool=True
) -> None:
  ...

@typing.overload
def request_transaction(
  server: str,
  transaction: str,
  command_name: str,
  inputs: "TransactionInputs",
  wait: bool=True,
  requester_icon: Icon=Icon(''),
  confirm_immediately: bool=True
) -> "JsonValue | None":
  ...

def request_transaction(
  server: str,
  transaction: str,
  command_name: str,
  inputs: "TransactionInputs",
  wait: bool=True,
  requester_icon: Icon=Icon(''),
  confirm_immediately: bool=True
) -> "JsonValue | None":
  """Request a transaction on the given server.

  Parameters
  ----------
  server
    The name of the server that serves the transaction. Or at least the server
    that can launch it.
  transaction
    The name of the transaction.
  command_name
    A name of the command that the transaction represents. The name is a list
    of names separated by a full stop and loosely forms a hierarchy.
    Examples:
      Maptek.PointStudio.Python.Commands.Despike
      Maptek.PointStudio.Python.Commands.SimplifyByDistanceError
      Maptek.Common.Python.Commands.NewView
  inputs
    A list of (name, value) pairs that provide the values for the transaction.
  wait
    If True then the function waits until the transaction is complete before
    returning, otherwise it won't wait and it will return immediately.
  requester_icon
    The behaviour of transactions can change depending on the icon provided.
    This is typically done as a way to reduce code duplication where having
    two transactions with a small difference would be unnecessary.
  confirm_immediately
    If the transaction should be confirmed immediately. Default is True.

  Returns
  ----------
  list
    The outputs of the transaction.

  Raises
  ------
  TransactionFailed
    If the transaction was unable to complete successfully.
  """
  manager = default_manager()
  # We could loosen the following if we checked the version and removed the
  # run_silently field in that case.
  try:
    raise_if_version_too_old(
      "Running operations",
      current_version=Mcp().version,
      required_version=(1, 2))
  except CApiDllLoadFailureError as error:
    raise NoProjectError(
      "Failed to load the required DLLs. You must connect to an application "
      "via Project() before using this module.") from error

  get_telemetry().record_function_call(transaction)
  is_new_version = Mcp().version >= (1, 3)
  if is_new_version:
    request_type = RequestTransactionWithInputsV13
    response_type = OperationCompletedV13
  else:
    request_type = RequestTransactionWithInputs
    response_type = OperationCompleted

  request = request_type(manager)
  request.transaction_name = transaction
  request.requester_icon = requester_icon
  if wait:
    request.operation_id = next(NEXT_OPERATION_ID)
  else:
    request.operation_id = 0
  request.operation_command = command_name
  request.confirm_immediately = confirm_immediately
  def value_for_workflow(value: typing.Any) -> str:
    if value is True:
      return "true"
    if value is False:
      return "false"
    return value
  request.transaction_inputs = JsonValue([
    {'name': name, 'value': value_for_workflow(value)}
    for name, value in inputs
  ])

  if not wait:
    request.send(server)
    return None

  # The process is as follows:
  # - Register a callback for receiving the completed message.
  # - Request the transaction.
  # - Wait for the transaction to complete.

  completed = threading.Event()
  information = None

  def on_message_received(received_message):
    """Called when the message of the expected name is received."""
    nonlocal information
    information = received_message

    if information.operation_id == request.operation_id:
      completed.set()

  with response_type.callback_on_receive(
    on_message_received,
    manager
  ):
    # Request the transaction.
    request.send(server)

    # Wait for the transaction to be completed.
    while not completed.is_set():
      Mcp().dll.McpServicePendingEvents()

  # Read the result.
  response = information

  assert isinstance(response, response_type)
  assert response.operation_id == request.operation_id
  assert response.operation_command == request.operation_command

  if not response.completed_okay:
    if is_new_version:
      error_message = response.error_message
    else:
      error_message = SerialisedText("%s", 'Check application for error')
    raise TransactionFailed(server, transaction, error_message)

  return response.outputs
