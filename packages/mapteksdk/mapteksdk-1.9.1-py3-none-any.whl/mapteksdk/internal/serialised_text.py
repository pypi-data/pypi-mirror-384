"""Types for sending / receiving serialised text via the MCP.

Warnings
--------
Vendors and clients should not develop scripts or applications against
this package. The contents may change at any time without warning.
"""
###############################################################################
#
# (C) Copyright 2024, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

from collections.abc import Sequence
import contextlib
import typing

from mapteksdk.capi import Translation
from mapteksdk.capi import Mcp

T = typing.TypeVar('T')

class ReceivedSerialisedText:
  """Represents text received through the communication system.

  It differs from SerialisedText as the text template and arguments for it is
  opaque. It is not possible to query them.
  """
  def __init__(self, serialised_string):
    self.serialised_string = serialised_string

  def __repr__(self):
    return f'ReceivedSerialisedText("{self.serialised_string}")'

  @contextlib.contextmanager
  def to_text_handle(self):
    """Converts the text to a text_handle."""
    text_handle = Translation().FromSerialisedString(
      self.serialised_string.encode('utf-8'))

    try:
      yield text_handle
    finally:
      Translation().FreeText(text_handle)

  @classmethod
  def from_handle(cls: type[T], handle) -> T:
    """Read the message from a handle.

    This is useful when receiving a message from a sender.

    Returns
    -------
    cls
      A ReceivedSerialisedText rather than SerialisedText as the text template
      and parameters can't be queried.
    """
    text_handle = Mcp().ExtractText(handle)
    try:
      return cls(Translation().ToSerialisedString(text_handle))
    finally:
      Translation().FreeText(text_handle)


class SerialisedText:
  """Represents text sent through the communication system.

  The two parts of it are the text template and the arguments, where arguments
  can be strings and numbers. The text template specify where they appear in
  the text and how they are formatted.

  Parameters may be a string, float, SerialisedText or a sequence of strings.
  If you want integers at this time, use %.0f and convert the parameter to a
  float.
  Sequences of strings allow for use of the %v format specification.
  Only strings are supported at this time.
  """

  def __init__(self, text_template, *parameters):
    if isinstance(text_template, SerialisedText):
      self.text_template = text_template.text_template
      self.parameters = text_template.parameters
    else:
      self.text_template = text_template
      self.parameters = parameters

      # Check parameters are the basic supported types.
      supported_parameter_types = (
        str,
        float,
        SerialisedText,
        Sequence,
        )

      for index, parameter in enumerate(self.parameters):
        if not isinstance(parameter, supported_parameter_types):
          raise TypeError(f'Parameter {index + 1} is an unsupported type: '
                          + type(parameter).__name__)

  def __repr__(self):
    parameter_string = ','.join(str(parameter) for parameter in self.parameters)
    return f'SerialisedText("{self.text_template}", {parameter_string})'

  @contextlib.contextmanager
  def to_text_handle(self):
    """Converts the text to a text_handle."""
    text_handle = Translation().NewText(self.text_template.encode('utf-8'))
    # Add each of the arguments
    for index, parameter in enumerate(self.parameters):
      if isinstance(parameter, str):
        Translation().AddArgumentString(text_handle, parameter.encode('utf-8'))
      elif isinstance(parameter, float):
        Translation().AddArgumentDouble(text_handle, parameter)
      elif isinstance(parameter, SerialisedText):
        with parameter.to_text_handle() as inner_handle:
          Translation().AddArgumentText(text_handle, inner_handle)
      elif isinstance(parameter, Sequence):
        Translation().AddArgumentStringVector(text_handle, parameter)
      else:
        Translation().FreeText(text_handle)
        raise TypeError(f'Parameter {index+1} is an unsupported type: '
                        + type(parameter).__name__)
    try:
      yield text_handle
    finally:
      Translation().FreeText(text_handle)

  def __eq__(self, value: object) -> bool:
    if not isinstance(value, type(self)):
      return False
    return (
      self.text_template == value.text_template
      and self.parameters == value.parameters
    )

  def __hash__(self) -> int:
    return hash(self.text_template) + hash(self.parameters)
