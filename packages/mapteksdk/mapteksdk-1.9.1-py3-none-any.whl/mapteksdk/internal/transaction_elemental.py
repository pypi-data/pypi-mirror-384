"""Elemental transactions for the transaction manager.

These are transactions which do not contain other transactions.

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

from collections.abc import Sequence
import enum
import pathlib
import typing

import numpy as np

from .comms import (
  InlineMessage,
  Int32u,
  Int64u,
  Int8s,
  Int32s,
  Int64s,
  Double,
  CommunicationsManager,
)
from .qualifiers import Qualifiers, Qualifier, InstanceTypes
from .util import default_type_error_message
from .transaction_base import ElementalTransactionBase
from .transaction_errors import TransactionFailedError
from .transaction_mixins import (
  LabelMixin,
  TitleMixin,
  ChoiceValuesMixin,
  SupportLabelMixin,
  HelpMixin,
  WorldPickHintMixin,
  PrimitiveTypeMixin,
  LocateOnMixin,
  MarkupMixin,
  IconMixin,
  MessageMixin,
  PersistentMixin,
)
from .writable_selection import WritableSelection
from ..data import ObjectID

if typing.TYPE_CHECKING:
  from .transaction_base import TransactionBase
  from .transaction_manager_protocol import (
    TransactionManagerProtocol,
  )
  from ..common.typing import Point, PointLike


class StringBody(InlineMessage):
  """Body of the MCP message for this transaction."""
  data: str

class StringTransaction(
  ElementalTransactionBase[StringBody],
  LabelMixin,
  TitleMixin,
  ChoiceValuesMixin
):
  """Transaction for inputting a string.

  If this is the top-level transaction, this is realised as a panel with a
  single text box the user can type a string into.
  """
  _body: StringBody

  @staticmethod
  def name() -> str:
    return "mdf::uiC_ElementalTransaction<mdf::Tstring>"

  @staticmethod
  def data_type_name() -> str:
    return "mdf::Tstring"

  @classmethod
  def _default_qualifiers(cls) -> Sequence[Qualifier]:
    return [Qualifiers.instance_type(InstanceTypes.IMPERATIVE),]

  @classmethod
  def body_type(cls) -> type[StringBody]:
    return StringBody

  def _initialise_body(self, body: StringBody):
    body.data = ""

  def _read_value(self) -> typing.Optional[str]:
    return self._body.data

  def _set_value(self, new_value: str):
    self._body.data = new_value


class Integer64SBody(InlineMessage):
  """Body of the MCP message for IntegerTransaction64S.

  This is for 64 bit signed integer.
  """
  data: Int64s


class Integer64STransaction(ElementalTransactionBase[Integer64SBody], LabelMixin):
  """Transaction for a simple request of a 64 bit integer.

  By default this is realised as a panel with a single text box the user
  can type a number into.
  """
  _body: Integer64SBody

  @staticmethod
  def name() -> str:
    return "mdf::uiC_ElementalTransaction<__int64>"

  @staticmethod
  def data_type_name() -> str:
    return "::Tint64s"

  @classmethod
  def _default_qualifiers(cls) -> Sequence[Qualifier]:
    return [Qualifiers.instance_type(InstanceTypes.IMPERATIVE),]

  @classmethod
  def body_type(cls) -> type[Integer64SBody]:
    return Integer64SBody

  def _initialise_body(self, body: Integer64SBody):
    body.data = 0

  @property
  def value(self) -> int:
    """The value of the request."""
    return int(self._body.data)

  @value.setter
  def value(self, new_value: int):
    self._body.data = new_value


class DoubleBody(InlineMessage):
  """Body of the MCP message for DoubleTransaction."""
  data: Double


class DoubleTransaction(
  ElementalTransactionBase[DoubleBody],
  LabelMixin,
  MarkupMixin,
):
  """Transaction for a simple request of a double.

  By default this is realised as a panel with a single text box the user
  can type a number into.
  """
  _body: DoubleBody

  @staticmethod
  def name() -> str:
    return "mdf::uiC_ElementalTransaction<double>"

  @staticmethod
  def data_type_name() -> str:
    return "::Tfloat64"

  @classmethod
  def _default_qualifiers(cls) -> Sequence[Qualifier]:
    return [Qualifiers.instance_type(InstanceTypes.IMPERATIVE),]

  @classmethod
  def body_type(cls) -> type[DoubleBody]:
    return DoubleBody

  def _initialise_body(self, body: DoubleBody):
    body.data = 0.0

  @property
  def value(self) -> float:
    """The value of the request."""
    return float(self._body.data)

  @value.setter
  def value(self, new_value: float):
    self._body.data = new_value


class BooleanBody(InlineMessage):
  """Body of the MCP message for BooleanTransaction."""
  data: bool

class BooleanTransaction(
  ElementalTransactionBase[BooleanBody],
  LabelMixin,
  TitleMixin
):
  """A simple request for a boolean.

  If this is a top-level request, it is realised as a panel with a "Yes" and
  a "No" button.
  """
  _body: BooleanBody

  @staticmethod
  def name() -> str:
    return "mdf::uiC_ElementalTransaction<bool>"

  @staticmethod
  def data_type_name() -> str:
    return "::Tbool"

  @classmethod
  def _default_qualifiers(cls) -> Sequence[Qualifier]:
    return [Qualifiers.instance_type(InstanceTypes.IMPERATIVE),]

  @classmethod
  def body_type(cls) -> type[BooleanBody]:
    return BooleanBody

  def _initialise_body(self, body: BooleanBody):
    body.data = False

  @property
  def value(self) -> bool:
    """The value of the request."""
    return bool(self._body.data)

  @value.setter
  def value(self, new_value: bool):
    self._body.data = bool(new_value)


class CoordinateBody(InlineMessage):
  """Body of the MCP message for CoordinateTransaction."""
  x: Double
  y: Double
  z: Double


class CoordinateTransaction(
  ElementalTransactionBase[CoordinateBody],
  LabelMixin,
  SupportLabelMixin,
  HelpMixin,
  WorldPickHintMixin
):
  """Transaction for getting a coordinate.

  If this is a top-level request, it is realised by the view entering
  pick mode.

  Warnings
  --------
  If this is used as a top-level request, it will not be possible
  to cancel the pick.
  """
  _body: CoordinateBody

  @staticmethod
  def name() -> str:
    return "mdf::uiC_ElementalTransaction<geoS_Point>"

  @staticmethod
  def data_type_name() -> str:
    return "mdf::geoS_Point"

  @classmethod
  def _default_qualifiers(cls) -> Sequence[Qualifier]:
    return [Qualifiers.instance_type(InstanceTypes.IMPERATIVE),]

  @classmethod
  def body_type(cls) -> type[CoordinateBody]:
    return CoordinateBody

  def _initialise_body(self, body: CoordinateBody):
    body.x = 0.0
    body.y = 0.0
    body.z = 0.0

  @property
  def coordinate(self) -> "Point":
    """The picked coordinate."""
    body = self._body
    return np.array(
      [body.x, body.y, body.z],
      dtype=Double
    )

  @coordinate.setter
  def coordinate(self, new_point: "PointLike"):
    body = self._body
    body.x = new_point[0]
    body.y = new_point[1]
    body.z = new_point[2]


class PrimitiveBody(InlineMessage):
  """Body for PrimitiveTransaction."""
  owner: Int64u
  primitive_type: Int32s
  index: Int32u


class PrimitiveTransaction(
  ElementalTransactionBase[PrimitiveBody],
  LabelMixin,
  SupportLabelMixin,
  HelpMixin,
  PrimitiveTypeMixin,
  LocateOnMixin
):
  """A request for a primitive of any type."""
  _body: PrimitiveBody

  @staticmethod
  def name() -> str:
    return "mdf::uiC_ElementalTransaction<mdf::mdlC_Primitive>"

  @staticmethod
  def data_type_name() -> str:
    return "mdf::mdlC_Primitive"

  @classmethod
  def _default_qualifiers(cls) -> Sequence[Qualifier]:
    return [Qualifiers.instance_type(InstanceTypes.IMPERATIVE),]

  @classmethod
  def body_type(cls) -> type[PrimitiveBody]:
    return PrimitiveBody

  def _initialise_body(self, body: PrimitiveBody):
    body.owner = 0
    body.primitive_type = 0
    body.index = 0

  @property
  def owner_id(self) -> ObjectID:
    """The ObjectID of the object owning the selected primitive."""
    return ObjectID.convert_from(self._body.owner)

  @property
  def index(self) -> int:
    """The index of the selected primitive."""
    return int(self._body.index)


class PathBody(InlineMessage):
  """Body for PrimitiveTransaction."""
  path_string: str
  contains_environment_variables: bool
  is_valid: bool
  is_absolute: bool
  is_network: bool
  end_of_root: Int32u

  @classmethod
  def invalid(cls) -> "typing.Self":
    """Create this object referring to an invalid path."""
    body = cls()
    body.path_string = ""
    body.contains_environment_variables = False
    body.is_valid = False
    body.is_absolute = False
    body.is_network = False
    body.end_of_root = 0
    return body

  @classmethod
  def from_pathlib(cls, path: pathlib.Path) -> "typing.Self":
    """Construct this object from a pathlib.Path object.

    This will make the path absolute.
    """
    absolute_path = path.absolute()
    result = cls()
    result.path_string = str(absolute_path)
    result.is_valid = True

    # Pathlib paths can't have environment variables in them.
    result.contains_environment_variables = False

    # This always makes the path absolute.
    result.is_absolute = True

    drive = absolute_path.drive
    # A network drive path is of the form:
    # \\<machine name>\<share>
    # If the absolute path starts with \\ then it must be a network share.
    result.is_network = drive.startswith("\\\\")

    # The C++ code considers the drive to be "C:/", whereas pathlib
    # considers it to be "C:". Add an extra character to get the correct
    # length.
    result.end_of_root = len(drive) + 1

    return result

  @property
  def path(self) -> pathlib.Path:
    """Get the path from this object."""
    if not self.is_valid:
      raise TransactionFailedError(
        "The file path was invalid."
      )
    if self.contains_environment_variables:
      raise NotImplementedError(
        "Handling of paths containing environment variables is not implemented."
      )

    return pathlib.Path(self.path_string)


class _PathTransaction(ElementalTransactionBase[PathBody], TitleMixin):
  """Base transaction for requesting a file or folder.

  If this is the top-level request, this is realised as a file open / save
  dialog provided by the operating system parented to the connected
  application.
  """
  _body: PathBody

  @staticmethod
  def name() -> str:
    return "mdf::uiC_ElementalTransaction<mdf::sysC_Path>"

  @staticmethod
  def data_type_name() -> str:
    return "mdf::sysC_Path"

  @classmethod
  def _default_qualifiers(cls) -> Sequence[Qualifier]:
    return [Qualifiers.instance_type(InstanceTypes.IMPERATIVE),]

  @classmethod
  def body_type(cls) -> type[PathBody]:
    return PathBody

  def _initialise_body(self, body: PathBody):
    body.path_string = ""
    body.contains_environment_variables = False
    body.is_valid = False
    body.is_absolute = False
    body.is_network = False
    body.end_of_root = 0

  @property
  def path(self) -> pathlib.Path:
    """The path to the selected file.

    Raises
    ------
    TransactionFailedError
      If the path to the file is invalid.
    """
    return self._body.path


class FileTransaction(_PathTransaction):
  """Transaction for requesting a file.

  By default, this will be an open file dialog.
  """
  class DialogType(enum.Enum):
    """The type of dialog to display."""
    SAVE = 0
    LOAD = 1
    UNKNOWN = 255

  def __init__(
      self,
      manager: "TransactionManagerProtocol",
      comms_manager: "CommunicationsManager",
      parent: "TransactionBase | None" = None) -> None:
    super().__init__(manager, comms_manager, parent)
    self.__dialog_type: FileTransaction.DialogType = self.DialogType.UNKNOWN
    """The type of this dialog."""
    self.__are_filters_set: bool = False
    """Set to true when the file filters are set."""

  @classmethod
  def _default_qualifiers(cls) -> Sequence[Qualifier]:
    qualifiers = [*super()._default_qualifiers()]
    qualifiers.append(
      Qualifiers.file_only()
    )
    return qualifiers

  def set_dialog_type(self, dialog_type: "FileTransaction.DialogType"):
    """Set the dialog type for the file select operation.

    If this is set to SAVE, the user can select non-existent files and if they
    select an existent file, they are prompted for if they want to overwrite
    the file.

    If this is set to LOAD, the user can only select existing files.
    """
    if self.__dialog_type != FileTransaction.DialogType.UNKNOWN:
      raise RuntimeError(
        "Cannot set dialog type more than once."
      )
    if not isinstance(dialog_type, FileTransaction.DialogType):
      raise TypeError(
        default_type_error_message(
          "dialog_type",
          dialog_type,
          FileTransaction.DialogType
        )
      )
    if dialog_type == FileTransaction.DialogType.UNKNOWN:
      raise ValueError(
        "Cannot set dialog type to UNKNOWN."
      )
    if dialog_type == FileTransaction.DialogType.LOAD:
      self._add_qualifier(Qualifiers.as_load())
    elif dialog_type == FileTransaction.DialogType.SAVE:
      self._add_qualifier(Qualifiers.as_save())
    else:
      raise NotImplementedError(
        f"Dialog type of: {dialog_type} is not implemented."
      )
    self.__dialog_type = dialog_type

  def set_file_filter(
      self,
      filters: "dict[str, str | Sequence[str]]",
      suppress_all_files_filter: bool):
    """Set the file filter for the file dialog.

    Parameters
    ----------
    filters
      Dictionary where the keys are the description and the values are file
      extensions or a list of file extensions.
      The file extensions must not include the dot (i.e. "txt" instead of
      ".txt").
    suppress_all_files_filter
      If True, the all files filter will be suppressed. Otherwise the all
      files filter will be present, allowing for the user to select files
      without any of the specified extensions.
    """
    if self.__are_filters_set:
      raise RuntimeError("The file filters have already been set.")
    self.__are_filters_set = True
    self._add_qualifier(
      Qualifiers.file_filter(filters)
    )
    if suppress_all_files_filter:
      self._add_qualifier(
        Qualifiers.exclude_all_files_filter()
      )


class DirectoryTransaction(_PathTransaction):
  """Transaction for requesting a directory.

  By default, this will open a file dialog for selecting a folder.
  """
  @classmethod
  def _default_qualifiers(cls) -> Sequence[Qualifier]:
    qualifiers = [*super()._default_qualifiers()]
    qualifiers.append(Qualifiers.directory_only())
    qualifiers.append(Qualifiers.as_load())
    return qualifiers


class SelectionBody(InlineMessage):
  """Body for the MCP message for SelectionTransaction."""
  data: WritableSelection


class SelectionTransaction(ElementalTransactionBase[SelectionBody]):
  """Transaction for requesting a change to the active selection."""
  _body: SelectionBody
  @staticmethod
  def name() -> str:
    return "mdf::uiC_WritableSelectionTransaction"

  @staticmethod
  def data_type_name() -> str:
    return "mdf::selC_WritableSelection"

  @classmethod
  def _default_qualifiers(cls) -> Sequence[Qualifier]:
    return [Qualifiers.instance_type(InstanceTypes.IMPERATIVE),]

  @classmethod
  def body_type(cls) -> type[SelectionBody]:
    return SelectionBody

  def _initialise_body(self, body: SelectionBody):
    body.data = WritableSelection.from_selection([])

  def _read_body(self, message_handle):
    # The body is not included in responses to this transaction, so don't
    # attempt to read it.
    return None

  def disable_undo_redo(self):
    """If this is called, the change to the selection will not be undoable."""
    self._add_qualifier(
      Qualifiers.no_undo_redo()
    )

  @property
  def selection(self) -> Sequence[ObjectID]:
    """The current selection."""
    return [
      oid for oid, _ in self._body.data
    ]

  @selection.setter
  def selection(self, new_selection: Sequence[ObjectID]):
    self._body.data = WritableSelection.from_selection(new_selection)


class CommandBody(InlineMessage):
  """Body for the command transaction.

  This is empty because this transaction does not contain any data.
  """


class CommandTransaction(
    ElementalTransactionBase[CommandBody],
    TitleMixin,
    MessageMixin,
    IconMixin):
  """Transaction representing a command to be run.

  This is intended to be used with the call_on_confirm() function to run
  a function when this command should be run.
  """
  _body: CommandBody

  @staticmethod
  def name() -> str:
    return "mdf::uiC_ElementalTransaction<mdf::uiC_Command>"

  @staticmethod
  def data_type_name() -> str:
    return "mdf::uiC_Command"

  @classmethod
  def _default_qualifiers(cls) -> Sequence[Qualifier]:
    return [Qualifiers.instance_type(InstanceTypes.IMPERATIVE),]

  @classmethod
  def body_type(cls) -> type[CommandBody]:
    return CommandBody

  def _initialise_body(self, body: CommandBody):
    pass

class ProgressBody(InlineMessage):
  """Body for the progress indicator."""
  progress: Int8s
  """The progress of the indicator.

  This should be between 0 and 100 or -100.
  0 indicates an empty progress indicator.
  100 indicates a full progress indicator.
  X where 0 < X < 100 indicates a progress indicator which is X% full.
  -100 indicates the progress indicator should display fake progress to the
  user.
  """
  is_cancellable: bool
  """If the progress indicator is cancellable."""

class ProgressIndicatorTransaction(
    ElementalTransactionBase[ProgressBody],
    TitleMixin,
    MessageMixin,
    PersistentMixin,
  ):
  """Transaction which creates a progress indicator."""
  @staticmethod
  def name() -> str:
    return "mdf::uiC_ProgressIndicatorTransaction"

  @staticmethod
  def data_type_name() -> str:
    return "mdf::uiC_ProgressIndicator"

  @classmethod
  def body_type(cls) -> type[ProgressBody]:
    return ProgressBody

  @classmethod
  def _default_qualifiers(cls) -> Sequence[Qualifier]:
    return [
      Qualifiers.instance_type(InstanceTypes.IMPERATIVE),
    ]

  def _initialise_body(self, body: ProgressBody):
    body.progress = 0
    body.is_cancellable = True
