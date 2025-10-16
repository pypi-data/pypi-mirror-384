"""Basic connector type subclasses.

These can be passed to WorkflowArgumentParser.declare_input_connector
and WorkflowArgumentParser.declare_output_connector to determine which
type of data the connector should accept. The names of these classes
match the names of the connectors types as displayed in workflows.

"""
###############################################################################
#
# (C) Copyright 2021, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

from collections.abc import Iterable
import csv
import datetime
import os
import pathlib

import numpy as np

from .connector_type import ConnectorType
from ..internal.util import default_type_error_message

def python_type_to_connector_type(python_type: type) -> type[ConnectorType]:
  """Returns the corresponding ConnectorType subclass for a Python type.

  This only contains mappings for the ConnectorType subclasses
  defined in this file.

  Parameters
  ----------
  python_type : Type
    The Python type to match to a basic connector type.

  Returns
  -------
  ConnectorType
    The corresponding ConnectorType subclass from this file.

  Raises
  ------
  KeyError
    If there was no corresponding ConnectorType subclass.

  """
  type_mapping = {
    str: StringConnectorType,
    int: IntegerConnectorType,
    float: DoubleConnectorType,
    bool: BooleanConnectorType,
    list: CSVStringConnectorType,
    datetime.datetime: DateTimeConnectorType,
    pathlib.Path: FileConnectorType,
    None: AnyConnectorType
  }
  return type_mapping[python_type]

class AnyConnectorType(ConnectorType):
  """Connector type representing no connector type set.

  This corresponds to the connector type being blank on the workflows
  side. Input connectors of this type will accept any value from other
  connectors and the string representation of that value will be returned.
  Output connectors of this type will accept any value which can be converted
  into a string.

  """
  @classmethod
  def type_string(cls) -> str:
    return ""

  @classmethod
  def from_string(cls, string_value: str) -> str:
    return string_value

  @classmethod
  def to_json(cls, value: str) -> str:
    return str(value)

class StringConnectorType(ConnectorType):
  """Connector type corresponding to String on the workflows side
  and str on the Python side.

  This can be passed to declare_input_connector or declare_output_connector
  to declare the connector type as String. Passing the python type str
  is equivalent to passing this class.

  Examples
  --------
  This example sets the output connector "reversed" to contain a reversed
  version of the string from the input connector "string"

  >>> from mapteksdk.workflows import (WorkflowArgumentParser,
  ...                                  StringConnectorType)
  >>> parser = WorkflowArgumentParser()
  >>> parser.declare_input_connector("string", StringConnectorType)
  >>> parser.declare_output_connector("reversed", StringConnectorType)
  >>> parser.parse_arguments()
  >>> parser.set_output("reversed", parser["string"][::-1])

  """
  @classmethod
  def type_string(cls) -> str:
    return "String"

  @classmethod
  def from_string(cls, string_value: str) -> str:
    return string_value

  @classmethod
  def to_json(cls, value: str) -> str:
    return str(value)

class IntegerConnectorType(ConnectorType):
  """Connector type corresponding to Integer on the workflows side and
  int on the Python side. Passing the connector type as int is equivalent to
  passing this to declare_input/output_connector.

  Examples
  --------
  This example creates a workflow component with an Integer
  input and output connector. The output connector "new_count" is set to the
  value of the input connector "count" plus one.

  >>> from mapteksdk.workflows import (WorkflowArgumentParser,
  ...                                  IntegerConnectorType)
  >>> parser = WorkflowArgumentParser()
  >>> parser.declare_input_connector("count", IntegerConnectorType)
  >>> parser.declare_output_connector("new_count", IntegerConnectorType)
  >>> parser.parse_arguments()
  >>> parser.set_output("new_count", parser["count"] += 1)

  """
  @classmethod
  def type_string(cls) -> str:
    return "Integer"

  @classmethod
  def from_string(cls, string_value: str) -> int:
    return int(string_value)

  @classmethod
  def to_json(cls, value: int) -> int:
    return int(value)

class DoubleConnectorType(ConnectorType):
  """Connector type corresponding to Double on the workflows side and
  float on the Python side. Passing the connector type as float is equivalent
  to passing this to declare_input/output_connector.

  Examples
  --------
  This example sets the value of the output connector "x_over_2" to the value
  of the input connector "x" divided by two.

  >>> from mapteksdk.workflows import (WorkflowArgumentParser,
  ...                                  DoubleConnectorType)
  >>> parser = WorkflowArgumentParser()
  >>> parser.declare_input_connector("x", DoubleConnectorType)
  >>> parser.declare_output_connector("x_over_2", DoubleConnectorType)
  >>> parser.parse_arguments()
  >>> parser.set_output("x_over_2", parser["x"] / 2)

  """
  @classmethod
  def type_string(cls) -> str:
    return "Double"

  @classmethod
  def from_string(cls, string_value: str) -> float:
    return float(string_value)

  @classmethod
  def to_json(cls, value: float) -> float:
    return float(value)

class BooleanConnectorType(ConnectorType):
  """Connector type corresponding to Boolean on the workflows side and
  bool on the Python side. Passing the connector type as bool is equivalent
  to passing this to declare_input/output_connector.

  Examples
  --------
  This example sets the output connector "not x" to be the inverse of the
  value passed to the "x" input connector.

  >>> from mapteksdk.workflows import (WorkflowArgumentParser,
  ...                                  IntegerConnectorType)
  >>> parser = WorkflowArgumentParser()
  >>> parser.declare_input_connector("x", BooleanConnectorType)
  >>> parser.declare_output_connector("not x", BooleanConnectorType)
  >>> parser.parse_arguments()
  >>> parser.set_output("not x", not parser["x"])

  """
  @classmethod
  def type_string(cls) -> str:
    return "Boolean"

  @classmethod
  def from_string(cls, string_value: str) -> float:
    return bool(string_value)

  @classmethod
  def to_json(cls, value: bool) -> bool:
    return bool(value)

class CSVStringConnectorType(ConnectorType):
  """Connector type coresponding to CSV String on the workflows side
  and list on the Python side. Passing the connector type as list is
  equivalent to passing this to declare_input/output_connector.

  Examples
  --------
  This example filters out every second element in the list from the
  input connector "values" and sets the filtered list to the output connector
  "second_values".

  >>> from mapteksdk.workflows import (WorkflowArgumentParser,
  ...                                  CSVStringConnectorType)
  >>> parser = WorkflowArgumentParser()
  >>> parser.declare_input_connector("values", CSVStringConnectorType)
  >>> parser.declare_output_connector("second_values", CSVStringConnectorType)
  >>> parser.parse_arguments()
  >>> parser.set_output("second_values", parser["values"][::2])

  """
  @classmethod
  def type_string(cls) -> str:
    return "List"

  @classmethod
  def json_type_string(cls) -> str:
    return "String"

  @classmethod
  def json_dimensionality(cls) -> str:
    return "List"

  @classmethod
  def from_string(cls, string_value: str) -> list:
    if not isinstance(string_value, str):
      raise TypeError(default_type_error_message("string_value",
                                                 string_value,
                                                 str))
    # Strip off the first and last character if they are brackets.
    if string_value.startswith("[") and string_value.endswith("]"):
      string_value = string_value[1:-1]
    elif string_value.startswith("(") and string_value.endswith(")"):
      string_value = string_value[1:-1]

    # Use csv reader to parse the comma separated string and take the first
    # line. This should work as long as there are no new lines in the list.
    return list(csv.reader([string_value], skipinitialspace=True))[0]

  @classmethod
  def to_json(cls, value: list) -> list:
    return list(value)

  @classmethod
  def to_default_json(cls, value):
    if not isinstance(value, Iterable):
      raise TypeError(default_type_error_message("list default",
                                                 value,
                                                 Iterable))
    return ",".join([str(x) for x in value])

class DateTimeConnectorType(ConnectorType):
  """Connector type corresponding to Date Time on the Workflows side
  and datetime.datetime on the Python side. Passing the connector type as
  datetime.datetime is equivalent to passing this to
  declare_input/output_connector.

  This does not currently support defaults.

  Examples
  --------
  This example adds 24 hours to the time from the input connector "today" and
  sets that time to the output connector "tomorrow".
  Note that this may not give the same time on the next day due to
  daylight savings start/ending.

  >>> import datetime
  >>> from mapteksdk.workflows import (WorkflowArgumentParser,
  ...                                  DateTimeConnectorType)
  >>> parser = WorkflowArgumentParser()
  >>> parser.declare_input_connector("today", DateTimeConnectorType)
  >>> parser.declare_output_connector("tomorrow", DateTimeConnectorType)
  >>> parser.parse_arguments()
  >>> tomorrow = parser["today"] + datetime.timedelta(days=1)
  >>> parser.set_output("tomorrow", tomorrow)

  """
  @classmethod
  def type_string(cls) -> str:
    return "DateTime"

  @classmethod
  def from_string(cls, string_value: str) -> datetime.datetime:
    if not isinstance(string_value, str):
      raise TypeError(default_type_error_message("string_value",
                                                 string_value,
                                                 str))
    string_value = string_value.strip('"\'')
    return datetime.datetime.fromisoformat(string_value)

  @classmethod
  def to_json(cls, value: datetime.datetime) -> str:
    if isinstance(value, str):
      try:
        datetime.datetime.fromisoformat(value)
      except ValueError as error:
        message = f"Invalid datetime string: {value}. Must be ISO-8601 format."
        raise ValueError(message) from error
      return value
    try:
      return value.isoformat()
    except AttributeError as error:
      raise TypeError(default_type_error_message("value",
                                                 value,
                                                 datetime.datetime)) from error

  @classmethod
  def to_default_json(cls, value: datetime.datetime) -> str:
    raise TypeError("Default value for datetime is not supported.")

class Point3DConnectorType(ConnectorType):
  """Connector type representing a 3D point in workflows.

  An input connector of this type will return a numpy array of floats with
  shape (3, ) representing the point in the form [X, Y, Z].

  Default values can be specified using any iterable as long as its length
  is three and all values can be converted to floats, though list or numpy
  arrays are generally preferable.

  Given a script called "script.py" with an input connector of type
  Point3DConnectorType called "point", to pass the point [1.2, 3.4, -1.3]
  via the command line you would type:

  >>> py script.py --point=(1.2,3.4,-1.3)

  Examples
  --------
  This example sets the output connector "inverted_point" to the inverse of the
  point from the input connector "point".

  >>> from mapteksdk.workflows import (WorkflowArgumentParser,
  ...                                  Point3DConnectorType)
  >>> parser = WorkflowArgumentParser()
  >>> parser.declare_input_connector("point", Point3DConnectorType)
  >>> parser.declare_output_connector("inverted_point", Point3DConnectorType)
  >>> parser.parse_arguments()
  >>> parser.set_output("inverted_point", -parser["point"])

  """
  @classmethod
  def type_string(cls) -> str:
    return "Point3D"

  @classmethod
  def from_string(cls, string_value: str) -> np.ndarray:
    if not isinstance(string_value, str):
      raise TypeError(default_type_error_message("string_value",
                                                 string_value,
                                                 str))
    ordinates = string_value.strip("()").split(",")
    point = np.zeros((3,), float)
    point[:] = ordinates
    return point

  @classmethod
  def to_json(cls, value: np.ndarray) -> str:
    middle = ", ".join([str(float(x)) for x in value])
    return f"({middle})"


class FileConnectorType(ConnectorType):
  """Connector type representing a File.

  If used as an input, the file path will be returned as a pathlib.Path
  object.

  If used as an output, the file path can be provided as any path-like
  object.

  Warnings
  --------
  This class does not validate the file paths received from a Workflow, nor does
  it validate file paths provided to output connectors. This means:

  * The file path given by an input connector may not point to an existing file.
  * The file path given by an input connector may be the path to a directory
    instead of a file.
  * An output connector will not raise an error if given the path to a file
    which does not exist.
  * An output connector will not raise an error if given the path to a
    directory.

  Notes
  -----
  When declaring connectors, pathlib.Path can be used instead of this class.

  Examples
  --------
  The following example demonstrates a script which accepts a file path from
  a workflow and then reads the CSV file at that file path using pandas.

  >>> import pandas
  >>> import pathlib
  >>> from mapteksdk.workflows import WorkflowArgumentParser, FileConnectorType
  >>> if __name__ == "__main__":
  ...   parser = WorkflowArgumentParser(
  ...     description="Example of reading a CSV file.")
  ...   parser.declare_input_connector(
  ...     "csv_file",
  ...     FileConnectorType,
  ...     description="Path to the CSV file to read."
  ...   )
  ...   parser.parse_arguments()
  ...   csv_file_path: pathlib.Path = parser["csv_file"]
  ...   if not csv_file_path.exists():
  ...     raise FileNotFoundError(
  ...       f"The CSV file does not exist: '{csv_file_path}'"
  ...     )
  ...   if csv_file_path.is_dir():
  ...     raise ValueError(
  ...       f"The CSV file cannot be a directory."
  ...     )
  ...   csv_data = pandas.read_csv(csv_file_path)
  ...   # Now do something with the CSV.
  """
  @classmethod
  def type_string(cls) -> str:
    return "File"

  @classmethod
  def from_string(cls, string_value: str) -> pathlib.Path:
    # :NOTE: Ideally, this would use pathlib.Path.resolve(), however there
    # is a bug in Python 3.7~3.9 where if a file path:
    # * Is relative.
    # * Leads to a non-existent file or directory.
    # * Doesn't contain ".."
    # Then pathlib.Path.resolve() will return the path unchanged, thus returning
    # a relative path instead of an absolute path.
    # To avoid this, this uses os.path.abspath().
    # :NOTE: This calls resolve on the path even though it is already
    # absolute to convert 8.3 file names to long file names.
    return pathlib.Path(os.path.abspath(string_value)).resolve()

  @classmethod
  def to_json(cls, value: os.PathLike) -> str:
    # See note in "from_string()" for why this is using os.path instead
    # of pathlib.Path.
    return os.path.abspath(value)


class DirectoryConnectorType(ConnectorType):
  """Connector type representing a directory.

  If used as an input, the path to the directory is returned as a pathlib.Path
  object.

  If used as an output, the directory path can be provided as any path-like
  object.

  Warnings
  --------
  This class does not validate the directory paths received from a Workflow,
  nor does it validate directory paths provided to output connectors. This
  means:

  * The directory path given by an input connector may not point to an existing
    directory.
  * The directory path given by an input connector may be the path to a file
    instead of a directory.
  * An output connector will not raise an error if given the path to a directory
    which does not exist.
  * An output connector will not raise an error if given the path to a
    file.

  Examples
  --------
  The following example demonstrates a workflow which accepts a directory input
  and produces an output list which contains every file within that directory.

  >>> import pathlib
  >>> from mapteksdk.workflows import (
  ...   WorkflowArgumentParser, DirectoryConnectorType)
  >>> if __name__ == "__main__":
  ...   parser = WorkflowArgumentParser(
  ...     description="This script accepts a directory input from workflows. "
  ...       "It outputs a list containing all of the files within that "
  ...       "directory. This script will fail if the file input does not exist "
  ...       "or the user does not have permissions to access that directory."
  ...   )
  ...   parser.declare_input_connector(
  ...     "directory",
  ...     DirectoryConnectorType,
  ...     description="Path to the directory to list the files it contains."
  ...   )
  ...   parser.declare_output_connector(
  ...     "files_in_directory",
  ...     list,
  ...     description="Path to the files contained in the input directory."
  ...   )
  ...   parser.parse_arguments()
  ...   directory: pathlib.Path = parser["directory"]
  ...   # :NOTE: is_dir() will return false if the directory does not exist.
  ...   # Thus check if the path exists before checking if it is a directory.
  ...   if not directory.exists():
  ...     raise FileNotFoundError(
  ...       f"The input directory did not exist: '{directory}'"
  ...     )
  ...   if not directory.is_dir():
  ...     raise ValueError(
  ...       f"The input directory path pointed to a file: {directory}"
  ...     )
  ...   files_in_directory = [str(path) for path in directory.iterdir()]
  ...   parser.set_output("files_in_directory", files_in_directory)
  """
  @classmethod
  def type_string(cls) -> str:
    return "Folder"

  @classmethod
  def from_string(cls, string_value: str) -> pathlib.Path:
    # :NOTE: Ideally, this would use pathlib.Path.resolve(), however there
    # is a bug in Python 3.7~3.9 where if a file path:
    # * Is relative.
    # * Leads to a non-existent file or directory.
    # * Doesn't contain ".."
    # Then pathlib.Path.resolve() will return the path unchanged, thus returning
    # a relative path instead of an absolute path.
    # To avoid this, this uses os.path.abspath().
    # :NOTE: This calls resolve on the path even though it is already
    # absolute to convert 8.3 file names to long file names.
    return pathlib.Path(os.path.abspath(string_value)).resolve()

  @classmethod
  def to_json(cls, value: os.PathLike) -> str:
    # See note in "from_string()" for why this is using os.path instead
    # of pathlib.Path.
    return os.path.abspath(value)
