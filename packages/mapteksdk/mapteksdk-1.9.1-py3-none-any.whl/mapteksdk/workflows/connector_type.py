"""The ConnectorType interface.

Classes which implement this interface can be passed to WorkflowArgumentParser
as connector types.

"""
###############################################################################
#
# (C) Copyright 2021, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import typing

class ConnectorType:
  """Interface for classes representing connector types.

  Classes which implement this interface can be passed as types for
  WorkflowArgumentParser.declare_input_connector() and
  WorkflowArgumentParser.declare_output_connector().

  """
  @classmethod
  def type_string(cls) -> str:
    """The string representation of the type to report to the Workflow
    as the type for the Connector.

    Returns
    -------
    str
      String representation of the type to report to the workflow.

    """
    raise NotImplementedError

  @classmethod
  def json_type_string(cls) -> str:
    """The type string expected to be in JSON inputs.

    This is the same as the type string by default, but for certain cases
    this differs.
    """
    return cls.type_string()

  @classmethod
  def json_dimensionality(cls) -> str:
    """The dimensionality of the input in JSON.

    This must either be 'Single' or 'List'. It is 'Single' by default.
    """
    return "Single"

  @classmethod
  def from_string(cls, string_value: str) -> typing.Any:
    """Convert a string value from an input connector to the corresponding
    python type and returns it.

    Returns
    -------
    any
      The python representation of the string value.

    Raises
    ------
    TypeError
      If string_value is not a supported type.
    ValueError
      If string_value is the correct type but an invalid value.

    """
    raise NotImplementedError

  @classmethod
  def to_json(cls, value: typing.Any) -> typing.Any:
    """Converts the value to a json-serializable value.

    This is used to convert python values to json values to be passed
    to the workflow for output connectors.

    Returns
    -------
    json-serializable
      Json serializable representation of value.

    Raises
    ------
    TypeError
      If value is not a supported type.
    ValueError
      If value is the correct type but an invalid value.

    """
    raise NotImplementedError

  @classmethod
  def to_default_json(cls, value: typing.Any) -> str:
    """Converts the value to a json serializable default.

    This allows for specifying a different representation for default
    values. The output of this function should not include lists.

    Overwrite this function to raise an error to indicate that default
    values are not supported.

    By default this calls to_json.

    Returns
    -------
    str
      String representation of value.

    Raises
    ------
    TypeError
      If value is not a supported type.
    ValueError
      If value is the correct type but an invalid value.

    """
    return cls.to_json(value)
