"""Errors raised in the workflows package."""
###############################################################################
#
# (C) Copyright 2023, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

class InvalidConnectorNameError(ValueError):
  """Error raised when a connector name is invalid."""


class DuplicateConnectorError(Exception):
  """Error raised when a duplicate connector is declared."""


class MalformedInputError(Exception):
  """Error raised when script inputs cannot be read."""


class InputDimensionMismatchError(Exception):
  """Error raised when an input's dimensions are incorrect."""
  def __init__(
      self,
      name: str,
      expected: int,
      actual: int):
    self.name = name
    self.expected = expected
    self.actual = actual
    super().__init__(
      f"The input '{name}' expected a {expected}D "
      f"value but was given a {actual}D value."
    )


class InputTypeError(Exception):
  """Error raised when an input's type is incorrect.

  This is raised if an input receives a value which does not match the type
  of the declared input port.
  """
  def __init__(
      self,
      name: str,
      expected_type_name: str,
      actual_type_name: str) -> None:
    self.name = name
    self.expected_type_name = expected_type_name
    self.actual_type_name = actual_type_name
    super().__init__(
      f"The input '{name}' was expected to have type: '{expected_type_name}' "
      f"but it had type: '{actual_type_name}'."
    )


class MissingInputError(Exception):
  """Error raised when one or more inputs are missing."""
  def __init__(self, missing_inputs: set[str]) -> None:
    self.missing_inputs = missing_inputs
    missing_inputs_message = ", ".join(missing_inputs)
    super().__init__(
      f"The following inputs are missing: {missing_inputs_message}")


class UnknownInputError(Exception):
  """Error raised when an unknown input is encountered.

  This will not be raised if the class is configured to allow unknown arguments.
  """
  def __init__(self, name: str) -> None:
    super().__init__(
      f"Received input '{name}' which does not correspond to an input port. "
      "Inputs must be declared with declare_input_connector().")


class UnsupportedInputTypeError(Exception):
  """Error raised when an input's type is not supported."""
  def __init__(self, unsupported_type: str):
    self.unsupported_type = unsupported_type
    super().__init__(
      f"The type '{unsupported_type}' is not supported for inputs."
    )


class InputFormatNotSupportedError(Exception):
  """Error raised when the input cannot be read because it is too new or old."""
  def __init__(
      self,
      actual_version: int,
      maximum_supported: int,
      minimum_supported: int) -> None:
    self.actual_version = actual_version
    self.maximum_supported = maximum_supported
    self.minimum_supported = minimum_supported
    super().__init__(
      f"The input version is not supported. "
      f"Input version: '{actual_version}'. "
      f"The SDK supports versions: {minimum_supported} to {maximum_supported}.")


class InputCannotBeNoneError(Exception):
  """Error raised if a non-nullable input is null."""
  def __init__(self, name: str) -> None:
    super().__init__(f"The input {name} cannot be None.")
