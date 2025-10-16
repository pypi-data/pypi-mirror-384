"""Elemental transactions for the transaction manager.

Mixins for defining shared functionality for Transactions.

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
from .qualifiers import Qualifiers, Qualifier
from .serialisation import Icon
from .util import default_type_error_message
from ..data import ObjectID

if typing.TYPE_CHECKING:
  from collections.abc import Iterable
  from ..operations import SelectablePrimitiveType


T = typing.TypeVar("T")

class QualifierOwner(Protocol):
  """Protocol indicating a class which has qualifiers."""
  def _add_qualifier(self, qualifier: Qualifier):
    ...

class LabelMixin(QualifierOwner, Protocol):
  """Mixin which allows for the label qualifier to be added to a request."""
  __label: str | None = None
  """The value set to the label."""

  @property
  def label(self) -> str | None:
    """The label for this request.

    This will be None if no label has been set.

    Raises
    ------
    RuntimeError
      If this is set more than once.
    """
    return self.__label

  @label.setter
  def label(self, new_label: str):
    if self.__label is not None:
      raise RuntimeError("The label has already been set.")
    self.__label = new_label
    self._add_qualifier(Qualifiers.label(new_label))


class SupportLabelMixin(QualifierOwner, Protocol):
  """Mixin which adds support for the support label qualifier."""
  __support_label: str | None = None
  """The value set to the support label."""

  @property
  def support_label(self) -> str | None:
    """The support label for this request.

    This will be None if no label has been set.

    Raises
    ------
    RuntimeError
      If this is set more than once.
    """
    return self.__support_label

  @support_label.setter
  def support_label(self, new_label: str):
    if self.__support_label is not None:
      raise RuntimeError("The label has already been set.")
    self.__support_label = new_label
    self._add_qualifier(Qualifiers.support_label(new_label))


class HelpMixin(QualifierOwner, Protocol):
  """Mixin which allows for the Help qualifier to be added to a request."""
  __help: str | None = None
  """The value set to the help."""

  @property
  def help(self) -> str | None:
    """The help for this request.

    This will be None if no help has been set.

    Raises
    ------
    RuntimeError
      If this is set more than once.
    """
    return self.__help

  @help.setter
  def help(self, new_help: str):
    if self.__help is not None:
      raise RuntimeError("The help has already been set.")
    self.__help = new_help
    self._add_qualifier(Qualifiers.help(new_help))


class TitleMixin(QualifierOwner, Protocol):
  """Mixin which allows for the title qualifier to be added to a request."""
  __title: str | None = None
  """The value set to the title."""

  @property
  def title(self) -> str | None:
    """The title for this request.

    This will be None if no title has been set.

    Raises
    ------
    RuntimeError
      If this is set more than once.
    """
    return self.__title

  @title.setter
  def title(self, new_title: str):
    if self.__title is not None:
      raise RuntimeError("The title has already been set.")
    self.__title = new_title
    self._add_qualifier(Qualifiers.title(new_title))


class MessageMixin(QualifierOwner, Protocol):
  """Mixin which adds support for the Message() qualifier."""
  __message: str | None = None
  """The value set to the message."""

  @property
  def message(self) -> str | None:
    """The message for this request.

    This will be None if no message has been set.

    Raises
    ------
    RuntimeError
      If this is called more than once.
    """
    return self.__message

  @message.setter
  def message(self, new_message: str):
    if self.__message is not None:
      raise RuntimeError("The message has already been set!")
    self.__message = new_message
    self._add_qualifier(Qualifiers.message(new_message))


class ChoiceValuesMixin(
    QualifierOwner,
    Protocol,
    typing.Generic[T],
  ):
  """Mixin for adding choice values."""
  __choices: tuple[T, ...] | None = None

  def _read_value(self) -> T | None:
    """Read the value of this transaction."""
    raise NotImplementedError

  def _set_value(self, new_value: T):
    """Set the value of this transaction.

    Calling this bypasses the check for if it is a valid option, so calling
    this directly should be avoided. Use the value property instead.
    """
    raise NotImplementedError

  @property
  def choices(self) -> typing.Sequence[T] | None:
    """The choices the value must choose from.

    If None, the value can be any valid value for the type.
    """
    return self.__choices

  @choices.setter
  def choices(self, new_choices: Iterable[T]):
    if self.__choices is not None:
      raise ValueError("Cannot set choices more than once.")
    choices = tuple(new_choices)
    current_value = self._read_value()
    self.validate_choice(current_value, choices)
    self._add_qualifier(
      Qualifiers.choice_values(choices)
    )
    self.__choices = choices
    if current_value is None:
      self._set_value(choices[0])

  @property
  def value(self) -> T | None:
    """The user's chosen value.

    This will be a member of choices if it is set, otherwise
    it can be any valid value of the specified type.
    """
    return self._read_value()

  @value.setter
  def value(self, new_value: T):
    self.validate_choice(new_value, self.__choices)
    self._set_value(new_value)

  @staticmethod
  def validate_choice(
      value: T | None,
      choices: tuple[T, ...] | None):
    """Validate the value is in the expected values.

    Parameters
    ----------
    value
      The value to check if it is in choices. If it is None, no error is
      raised.
    choices
      The choices to check if the value is in. If it is None, no error is
      raised.

    Raises
    ------
    ValueError
      Error value and choices is not None and value is not in choices.
    """
    if value and choices and value not in choices:
      raise ValueError(
        f"Cannot set value to {value}. It is not in: " +
        ",".join(str(choice) for choice in choices))

class WorldPickHintMixin(QualifierOwner, Protocol):
  """Mixin which adds support for the WorldPickHint qualifier.
  """

  def add_world_pick_hint(self):
    """Adds the world pick hint to the request.

    This ensures that the UI is set to "world mode" so that the pick is not
    restricted to the action plane.
    """
    self._add_qualifier(Qualifiers.world_pick_hint())


class PrimitiveTypeMixin(QualifierOwner, Protocol):
  """Mixin which enables the PrimitiveType qualifier."""
  __primitive_type: SelectablePrimitiveType | None = None
  """The value set to the title."""

  @property
  def primitive_type(self) -> SelectablePrimitiveType | None:
    """The primitive type for this transaction.

    This will be None if no primitive type has been set.

    Raises
    ------
    RuntimeError
      If this is set more than once.
    """
    return self.__primitive_type

  @primitive_type.setter
  def primitive_type(self, new_type: SelectablePrimitiveType):
    if self.__primitive_type is not None:
      raise RuntimeError("The primitive type has already been set.")
    self.__primitive_type = new_type
    self._add_qualifier(Qualifiers.primitive_type(new_type))


class LocateOnMixin(QualifierOwner, Protocol):
  """Mixin which enables the LocateOn qualifier."""

  def add_locate_on_object(self, object_id: ObjectID):
    """Restrict the pick to be on the given object.

    This can be called multiple times. If so, then the pick must be on one
    of the objects passed to this function.
    """
    if not isinstance(object_id, ObjectID):
      raise TypeError(
        default_type_error_message(
          "locate_on",
          object_id,
          ObjectID
        )
      )
    self._add_qualifier(Qualifiers.locate_on(object_id))


class MarkupMixin(QualifierOwner, Protocol):
  """Mixin which enables the MarkUp qualifier."""
  __markup_string: str | None = None

  def set_markup(self, markup_string: str):
    """Set the markup for this transaction.

    This is used to determine how a various types should be represented in
    the user interface.
    """
    if self.__markup_string is not None:
      raise RuntimeError("Markup string has already been set.")

    self._add_qualifier(Qualifiers.markup(markup_string))
    self.__markup_string = markup_string


class IconMixin(QualifierOwner, Protocol):
  """Mixin which enables the Icon qualifier."""
  __icon_name: str | None = None

  @property
  def icon(self) -> Icon | None:
    """The icon assigned to this transaction."""
    if self.__icon_name:
      return Icon(self.__icon_name)
    return None

  @icon.setter
  def icon(self, new_icon: Icon | str):
    if self.__icon_name is not None:
      raise RuntimeError(
        "Cannot set icon more than once."
      )
    if isinstance(new_icon, str):
      actual_icon = Icon(new_icon)
    elif isinstance(new_icon, Icon):
      actual_icon = new_icon
    else:
      raise TypeError(
        default_type_error_message(
          "Icon",
          new_icon,
          (Icon, str)
        )
      )

    self._add_qualifier(Qualifiers.icon(actual_icon))
    self.__icon_name = actual_icon.name


class PersistentMixin(QualifierOwner, Protocol):
  """Add support for the Persistent qualifier to a transaction.

  This qualifier is used by progress indicators to indicate the operation
  may take a long time or is being performed in the background. This causes
  the progress indicator to be placed inside the status bar. This realisation
  is considered to be less obtrusive than the standard panel.
  """
  __is_persistent: bool = False

  @property
  def is_persistent(self) -> bool:
    """True if the persistent qualifier has been applied."""
    return self.__is_persistent

  def set_persistent(self):
    """Apply the persistent qualifier to the transaction."""
    if not self.__is_persistent:
      self._add_qualifier(Qualifiers.persistent())
      self.__is_persistent = True
