"""Converters for parsing inputs in a JSON file.

These convert the JSON representation of the type to the Python version.
"""
###############################################################################
#
# (C) Copyright 2023, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

from collections.abc import Iterable, Mapping
import datetime
import pathlib
import typing

import numpy as np

from ..errors import (
  InputDimensionMismatchError,
  MalformedInputError,
  UnsupportedInputTypeError,
  InputCannotBeNoneError
)

if typing.TYPE_CHECKING:
  from .schema import WorkflowInput, PrimitiveValues, SupportedTypeNames


class IConverter:
  """Interface for converters."""
  def convert(self, json_representation: PrimitiveValues) -> typing.Any:
    """Convert the value from its JSON representation to its Python one.

    For list inputs, this will be called once for each value in the list
    so this only needs to handle parsing a single value.

    Parameters
    ----------
    json_representation
      The JSON representation of a single object. Converters should handle
      the potential of this being the wrong type or an invalid value by
      throwing an exception.

    Raises
    ------
    ValueError
      If the JSON representation cannot be parsed.
    TypeError
      If the JSON representation contains a value which is the wrong type.
    """
    raise NotImplementedError("Must be implemented in child classes.")


class IntegerConverter(IConverter):
  """Converter for integer inputs."""
  def convert(self, json_representation: PrimitiveValues) -> int:
    # Static type checking correctly identifies that this will raise an error
    # for certain PrimitiveValues. This is expected behaviour.
    return int(json_representation) # type: ignore


class FloatConverter(IConverter):
  """Converter for float inputs."""
  def convert(self, json_representation: PrimitiveValues) -> float:
    # Static type checking correctly identifies that this will raise an error
    # for certain PrimitiveValues. This is expected behaviour.
    return float(json_representation) # type: ignore


class BooleanConverter(IConverter):
  """Converter for boolean inputs."""
  def convert(self, json_representation: PrimitiveValues) -> bool:
    # :NOTE: This cannot be 'return bool(json_representation)' because:
    # bool('false') == True
    # 'false' is a non-empty string, so it evaluates as True.
    if isinstance(json_representation, (int, bool)):
      return bool(json_representation)
    actual_type = type(json_representation)
    raise TypeError(
      f"Cannot convert '{json_representation}' of type "
      f"'{actual_type}' to boolean."
    )


class StringConverter(IConverter):
  """Converter for string inputs."""
  def convert(self, json_representation: PrimitiveValues) -> str:
    if isinstance(json_representation, (int, float, str, bool)):
      return str(json_representation)
    # The value was a JSON object. That can be converted into a string,
    # but that is unlikely to be correct behaviour.
    raise TypeError(f"Cannot convert: {json_representation} to string.")


class DateTimeConverter(IConverter):
  """Converter for datetime inputs."""
  def convert(self, json_representation: PrimitiveValues) -> datetime.datetime:
    # Static type checking correctly identifies that this will raise an error
    # for certain PrimitiveValues. This is expected behaviour.
    return datetime.datetime.fromisoformat(json_representation) # type: ignore


class Point3DConverter(IConverter):
  """Converter for Point 3D inputs."""
  def convert(self, json_representation: PrimitiveValues) -> np.ndarray:
    if isinstance(json_representation, dict):
      try:
        return np.array(
          [
            json_representation["x"],
            json_representation["y"],
            json_representation["z"]
          ], dtype=float)
      except KeyError as error:
        raise ValueError(
          f"Cannot convert: {json_representation} to point 3D. "
          "One or more ordinates are missing (Keys must be lower case)."
          ) from error
    raise TypeError(f"Cannot convert: {json_representation} to point 3D.")


class FileConverter(IConverter):
  """Converter for File inputs."""
  def convert(self, json_representation: PrimitiveValues) -> pathlib.Path:
    # Static type checking correctly identifies that this will raise an error
    # for certain PrimitiveValues. This is expected behaviour.
    return pathlib.Path(json_representation) # type: ignore


class DirectoryConverter(IConverter):
  """Converter for Directory inputs."""
  def convert(self, json_representation: PrimitiveValues) -> pathlib.Path:
    # Static type checking correctly identifies that this will raise an error
    # for certain PrimitiveValues. This is expected behaviour.
    return pathlib.Path(json_representation) # type: ignore


class WorkflowSelectionConverter(IConverter):
  """Converter for selection inputs.

  This does not make use of a running application to validate the object paths
  and assumes all strings represent a valid object path.
  """
  def convert(self, json_representation: PrimitiveValues) -> str:
    if isinstance(json_representation, str):
      return json_representation
    raise TypeError(
      f"Cannot convert: {json_representation} to a WorkflowSelection.")


_CONVERTERS: dict[SupportedTypeNames, IConverter] = {
  "Integer" : IntegerConverter(),
  "String" : StringConverter(),
  "Double" : FloatConverter(),
  "Boolean" : BooleanConverter(),
  "DateTime" : DateTimeConverter(),
  "Point3D" : Point3DConverter(),
  "File" : FileConverter(),
  "Folder" : DirectoryConverter(),
  "DataEngineObject" : WorkflowSelectionConverter(),
}


def parse_input(data: WorkflowInput) -> typing.Any:
  """Parse a single WorkflowInput.

  This converts the JSON object into the correct Python object.
  """
  data_type = data["dataType"]
  converter = _CONVERTERS.get(data_type["typeName"], None)
  if converter is None:
    raise UnsupportedInputTypeError(data_type["typeName"])

  value = data["value"]

  # Handle null values.
  if value is None:
    if not data_type["canBeNull"]:
      raise InputCannotBeNoneError(data["name"])
    return value

  dimensionality = data_type["dimensionality"]
  if dimensionality == "Single":
    # Raise an error if given an iterable for a single object.
    # Note that a string is an iterable and thus a single value.
    # And a mapping is a JSON object, which is also a single value.
    if (isinstance(value, Iterable)
        and not isinstance(value, (Mapping, str))):
      raise InputDimensionMismatchError(data["name"], 1, 2)
    return converter.convert(value)
  if dimensionality == "List":
    values = []
    if (not isinstance(value, Iterable)
        or isinstance(value, (Mapping, str))):
      raise InputDimensionMismatchError(data["name"], 1, 2)
    for item in value:
      values.append(converter.convert(item))
    return values
  raise MalformedInputError(
    f"Invalid value for dimensionality: {dimensionality}.")
