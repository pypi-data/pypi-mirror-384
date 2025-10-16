"""The qualifier factory.

This is used by both RequestTransactionWithInputs and TransactionManager.

Warnings
--------
Vendors and clients should not develop scripts or applications against
this package. The contents may change at any time without warning.
"""
###############################################################################
#
# (C) Copyright 2022, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

from collections.abc import Sequence, Callable, Iterable
import enum
import typing

from .comms import InlineMessage, SubMessage, Int32s, Int64u
from .serialised_text import SerialisedText
from .util import default_type_error_message

if typing.TYPE_CHECKING:
  from .transaction_base import TransactionBase
  from .serialisation import Icon
  from ..data import ObjectID
  from ..operations import SelectablePrimitiveType

class InstanceTypes(enum.Enum):
  """Instance types for the InstanceType Qualifier."""
  MONTAGE = "Montage"
  IMPERATIVE = "Imperative"
  USER_MESSAGE = "UserMessage"
  APPLICATION = "Application"
  CUSTOM_TOOL_BARS = "CustomToolBars"
  GLOBAL_MANIPULATOR = "GlobalManipulator"
  MENU_BAR = "MenuBar"
  SELECTION_TYPE = "SelectionType"
  TOOL_BAR = "ToolBar"
  VIEW = "View"
  CHOICE = "Choice"
  SEQUENCE = "Sequence"
  EMBEDDED_VIEW = "EmbeddedView"
  WIZARD = "Wizard"
  MENU = "Menu"
  REDO = "Redo"
  UNDO = "Undo"
  WIDGET_INSPECTOR = "WidgetInspector"


class Qualifiers:
  """A factory of qualifiers."""

  @staticmethod
  def label(message):
    """The Label qualifier.

    This is typically used to set the label on a transaction.

    Parameters
    ----------
    message : str | SerialisedText
      The text to put in the label or a SerialisedText object
      to place in the label.
    """
    qualifier = Qualifier()
    qualifier.key = 'Label'
    qualifier.cumulative = False

    if not isinstance(message, SerialisedText):
      text = SerialisedText("%s", message)
    else:
      text = message
    qualifier.parameters = Qualifier.Parameters(text)
    return qualifier

  @staticmethod
  def title(message):
    """The Title qualifier.

    This is typically used to set the title of a transaction.
    Note that in older applications the label qualifier was used instead.

    Parameters
    ----------
    message : str
      The title text.
    """
    qualifier = Qualifier()
    qualifier.key = 'Title'
    qualifier.cumulative = False

    text = SerialisedText("%s", message)
    qualifier.parameters = Qualifier.Parameters(text)
    return qualifier

  @staticmethod
  def message(message):
    """The Message qualifier.

    This is typically used to set the message displayed by a transaction.

    Parameters
    ----------
    message : str
      The message text.
    """
    qualifier = Qualifier()
    qualifier.key = 'Message'
    qualifier.cumulative = True

    text = SerialisedText("%s", message)
    qualifier.parameters = Qualifier.Parameters(text)
    return qualifier

  @staticmethod
  def markup(markup_string: str):
    """The Markup qualifier.

    This is used to determine how a various types should be represented in
    the user interface.

    Parameters
    ----------
    markup_string
      Markup string to apply to the value.
    """
    qualifier = Qualifier()
    qualifier.key = 'Markup'
    qualifier.cumulative = False

    qualifier.parameters = Qualifier.Parameters(markup_string)
    return qualifier

  @staticmethod
  def support_label(message):
    """The SupportLabel qualifier.

    This is used to display instructions during sequence transactions.

    Parameters
    ----------
    message : str | SerialisedText
      The text to place into the support label or a SerialisedText object
      to place in the support label.
    """
    qualifier = Qualifier()
    qualifier.key = 'SupportLabel'
    qualifier.cumulative = False

    if not isinstance(message, SerialisedText):
      text = SerialisedText("%s", message)
    else:
      text = message
    qualifier.parameters = Qualifier.Parameters(text)
    return qualifier

  @staticmethod
  def help(message):
    """The Help qualifier.

    This provides additional help information to the request.
    Typically this is realised as a tool tip.

    Parameters
    ----------
    message : str | SerialisedText
      The text to place in the tool tip.
    """
    qualifier = Qualifier()
    qualifier.key = 'Help'
    qualifier.cumulative = False

    if not isinstance(message, SerialisedText):
      text = SerialisedText("%s", message)
    else:
      text = message
    qualifier.parameters = Qualifier.Parameters(text)
    return qualifier

  @staticmethod
  def toast():
    """The Toast qualifier.

    This is used to indicate to a transaction that it should display the
    message as a toast notification.
    """
    qualifier = Qualifier()
    qualifier.key = 'Toast'
    qualifier.cumulative = False
    qualifier.parameters = Qualifier.Parameters()

    return qualifier

  @staticmethod
  def world_pick_hint():
    """The WorldPickHint qualifier.

    This can be used for requests that use location picks to ensure
    the UI is set to "world mode" for the pick. This indicates that the
    pick should not be restricted to points on the action plane.

    The alternate is "action plane mode" which indicates that the pick
    is restricted to points on the action plane.
    """
    qualifier = Qualifier()
    qualifier.key = 'WorldPickHint'
    qualifier.cumulative = False
    qualifier.parameters = Qualifier.Parameters()

    return qualifier

  @staticmethod
  def instance_type(instance_type: InstanceTypes):
    """The instance type qualifier.

    This is used to find the appropriate factory for creating the UI realisation
    of a request.

    Parameters
    ----------
    instance_type
      The instance type of this qualifier.
    """
    if not isinstance(instance_type, InstanceTypes):
      raise TypeError(default_type_error_message(
        "instance_type", instance_type, InstanceTypes
      ))
    qualifier = Qualifier()
    qualifier.key = 'InstanceType'
    qualifier.cumulative = False

    qualifier.parameters = Qualifier.Parameters(instance_type.value)
    return qualifier

  @staticmethod
  def primitive_type(primitive_type: "SelectablePrimitiveType"):
    """The primitive type qualifier.

    This is used to determine what type of primitive a primitive pick should
    return.

    Parameters
    ----------
    primitive_type
      The type of primitive to pick.
    """
    qualifier = Qualifier()
    qualifier.key = 'PrimitiveType'
    qualifier.cumulative = False

    qualifier.parameters = Qualifier.Parameters(
      Int32s(primitive_type.value))
    return qualifier

  @staticmethod
  def choice_values(choices: Iterable[typing.Any]):
    """Restrict the values to the given choices.

    Parameters
    ----------
    choices
      The choices to restrict the operation to. These must be
      of an appropriate type (e.g. If the request is for a string,
      these must also be strings).
    """
    qualifier = Qualifier()
    qualifier.key = "ChoiceValues"
    qualifier.cumulative = True
    qualifier.parameters = Qualifier.Parameters(*choices)

    return qualifier

  @staticmethod
  def icon(icon: "Icon", placement: int=0, size_hint: int=5):
    """Set the icon for the request.

    Parameters
    ----------
    icon
      The icon for the request.
    placement
      Where the icon should be placed.
      0 is undefined.
      The other values in uiE_Placement are left to be decided by the compiler
      on the C++ side.
    size_hint
      How large the icon should be.
      0 is "smallest"
      The other values in uiE_SizeHint are left to be decided by the compiler
      on the C++ side.
      As of 2023-12-18, 5 represents "undefined", but if a new value is added
      on the C++ side this may change in the future.
    """
    qualifier = Qualifier()
    qualifier.key = "Icon"
    qualifier.cumulative = False
    qualifier.parameters = Qualifier.Parameters(
      icon.name,
      Int32s(placement),
      Int32s(size_hint))

    return qualifier

  @staticmethod
  def locate_on(object_id: "ObjectID"):
    """Restrict a pick to be on the specified object.

    Parameters
    ----------
    object_id
      The ObjectID of the object to pick.
    """
    qualifier = Qualifier()
    qualifier.key = "LocateOn"
    qualifier.cumulative = True
    qualifier.parameters = Qualifier.Parameters(
      object_id
    )
    return qualifier

  @staticmethod
  def file_filter(
      filters: dict[str, typing.Union[str, Sequence[str]]]):
    """Restrict the extensions of the files which can be picked.

    Parameters
    ----------
    filters
      Dictionary where the key is the description.
      The value is a sequence of file extension strings or a single file
      extension. The extension strings should not include the leading dot
      (i.e. "txt" instead of ".txt").

    Notes
    -----
    The function names does not match the qualifier name to avoid hiding
    Python's built-in filter function.
    """
    parameters = []
    for key, value in filters.items():
      label = SerialisedText(key)
      if not isinstance(value, Sequence) or isinstance(value, str):
        value = [value]
      extensions = SerialisedText(r"%v[*.%s{; *|; |}]", value)
      parameter = SerialisedText("%t (%t)", label, extensions)
      parameters.append(parameter)

    qualifier = Qualifier()
    qualifier.key = "Filter"
    qualifier.cumulative = True
    qualifier.parameters = Qualifier.Parameters(
      *parameters
    )
    return qualifier

  @staticmethod
  def exclude_all_files_filter():
    """Exclude the all files filter for files which can be picked."""
    qualifier = Qualifier()
    qualifier.key = "ExcludeAllFilesFilter"
    qualifier.cumulative = False
    qualifier.parameters = Qualifier.Parameters()
    return qualifier

  @staticmethod
  def file_only():
    """The file dialog should only allow the selection of files."""
    qualifier = Qualifier()
    qualifier.key = "FileOnly"
    qualifier.cumulative = False
    qualifier.parameters = qualifier.Parameters()
    return qualifier

  @staticmethod
  def directory_only():
    """The file dialog should only allow the selection of directories."""
    qualifier = Qualifier()
    qualifier.key = "DirectoryOnly"
    qualifier.cumulative = False
    qualifier.parameters = qualifier.Parameters()
    return qualifier

  @staticmethod
  def as_load():
    """The file dialog should indicate a file is being read."""
    qualifier = Qualifier()
    qualifier.key = "AsLoad"
    qualifier.cumulative = False
    qualifier.parameters = qualifier.Parameters()
    return qualifier

  @staticmethod
  def as_save():
    """The file dialog should indicate a file is being saved."""
    qualifier = Qualifier()
    qualifier.key = "AsSave"
    qualifier.cumulative = False
    # The parameter is "suppressOverwritePrompt". The SDK always wants the
    # prompt, so it is hard coded to False.
    qualifier.parameters = qualifier.Parameters(False)
    return qualifier

  @staticmethod
  def no_undo_redo():
    """The operation should not allow undo / redo."""
    qualifier = Qualifier()
    qualifier.key = "NoUndoRedo"
    qualifier.cumulative = False
    qualifier.parameters = qualifier.Parameters()
    return qualifier

  @staticmethod
  def persistent():
    """Used to make progress indicators appear in the status bar."""
    qualifier = Qualifier()
    qualifier.key = "Persistent"
    qualifier.cumulative = False
    qualifier.parameters = qualifier.Parameters()
    return qualifier

  @staticmethod
  def call_on_confirm(
      callback: Callable[["TransactionBase", typing.Any], None]
      ) -> "Qualifier":
    """Call a callback when the transaction is confirmed.

    The callback is passed the transaction object created from
    the TransactionData subclass and the data from the confirm
    message.

    If the callback raises an error, then wait_for_value() will raise
    that error and no more callbacks will be called.

    Parameters
    ----------
    callback
      A callback to call when the transaction is confirmed.
    """
    qualifier = Qualifier()
    qualifier.key = "CallOnConfirm"
    qualifier.cumulative = True
    qualifier.parameters = Qualifier.Parameters(
      callback
    )
    return qualifier

  @staticmethod
  def user_data(key: str, data_type: str, value: typing.Any) -> "Qualifier":
    """Add a user-defined qualifier.

    Parameters
    ----------
    key
      The key for the user-defined qualifier. This should not include
      the leading "U.".
    data_type
      String containing the C++ type of the data.
    value
      The value of the data stored in this qualifier.

    Returns
    -------
    Qualifier
      A user-data qualifier containing the specified data.
    """
    qualifier = Qualifier()
    qualifier.key = f"U.{key}"
    qualifier.cumulative = False
    if isinstance(value, Sequence):
      # Iterables are serialised as the length followed by each value in
      # the iterable.
      qualifier.parameters = Qualifier.Parameters(
        data_type, Int64u(len(value)), *value)
    else:
      qualifier.parameters = Qualifier.Parameters(data_type, value)
    return qualifier

class Qualifier(InlineMessage):
  """A qualifier is used to attribute a quality to a transaction."""

  class Parameters(SubMessage):
    """The parameters or values of a qualifier.

    To pass integer or float parameters, the caller must cast the integer
    or float to one of the types defined in types.py (e.g. Int8u or Double).
    The type the parameter is serialised as is determined at runtime via
    reflection so the exact type of the value must unambiguously determine
    how it should be serialised.
    """
    @classmethod
    def repeating_field_type(cls):
      return typing.Any

    @property
    def values(self) -> Sequence[typing.Any]:
      """The values of this qualifier."""
      return self.repeating_field_values

    @values.setter
    def values(self, values: Sequence[typing.Any]):
      self.repeating_field_values = values

    def __init__(self, *args):
      super().__init__()
      self.values = args

  key: str
  cumulative: bool
  parameters: Parameters


class QualifierSet(SubMessage):
  """A set of qualifiers often used with a transaction to qualify it."""
  @classmethod
  def repeating_field_type(cls):
    return Qualifier

  @property
  def values(self) -> Sequence[Qualifier]:
    """The qualifiers in this set."""
    return self.repeating_field_values

  @values.setter
  def values(self, values: Sequence[Qualifier]):
    self.repeating_field_values = values
