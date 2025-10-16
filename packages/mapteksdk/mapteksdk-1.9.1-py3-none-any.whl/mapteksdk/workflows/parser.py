"""Interface with the Extend Python Script workflow component.

This allows for Python Scripts to declare what inputs the workflow is
expected to provide, which outputs the Python Script will provide,
along with accessing arguments from the workflow and sending outputs
to the workflow.

"""
###############################################################################
#
# (C) Copyright 2021, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import argparse
import atexit
import io
import json
import logging
import sys
import typing

import numpy as np

from .connector_type import ConnectorType
from .connector_types import (BooleanConnectorType, CSVStringConnectorType,
                              AnyConnectorType, Point3DConnectorType,
                              python_type_to_connector_type)
from .errors import (
  InvalidConnectorNameError,
  DuplicateConnectorError,
  MalformedInputError,
  InputFormatNotSupportedError,
  InputTypeError,
  UnknownInputError,
  MissingInputError,
)
from .matching import MatchAttribute
from .internal.converters import parse_input
from .workflow_selection import WorkflowSelection
from ..internal.util import default_type_error_message

log = logging.getLogger("mapteksdk.workflows")

T = typing.TypeVar("T")

if typing.TYPE_CHECKING:
  from collections.abc import Callable

  from .internal.schema import (
    WorkflowInputs,
    WorkflowInput,
    SupportedTypeNames,
    Dimensionality,
  )
  try:
    class _WorkflowDescription(typing.TypedDict, total=False):
      """Typed dictionary used to type hint JSON workflow description"""
      Description: str
      InputConnectors : list[dict[str, typing.Any]]
      OutputConnectors : list[dict[str, typing.Any]]
      AllowUnknownAttributes: bool
      SupportsCommandLineArguments: bool
      MinimumJsonInputVersion: int
      MaximumJsonInputVersion: int
  except AttributeError:
    pass


class _Connector:
  """Class designed to hold metadata for input and output connectors.

  This is primarily used for serializing the input/output connector
  information to JSON to be used by the Extend Python workflow component to
  generate input and output connectors.

  Parameters
  ----------
  name
    The attribute to associate with the connector. This cannot contain
    spaces.
  arg_type
    The Python type of values accepted by the connector.
  default
    The default value for this connector. The default is None.
  connector_name
    A human-readable name for the connector. Unlike name this may contain
    spaces. If None (default) name will be used as the connector name.
  description
    The description of the connector. If None (default) the description
    will be empty.
  matching
    How the attribute will be matched on the workflows side.

  """
  def __init__(
      self,
      name: str,
      arg_type: type[ConnectorType],
      default: typing.Any=None,
      connector_name: str | None=None,
      description: str | None=None,
      matching: MatchAttribute | None=None):
    self.__name = name
    self.__arg_type = arg_type
    self.__connector_name = connector_name
    if default is None:
      self.__default = ""
    else:
      self.__default = arg_type.to_default_json(default)
    if description is None:
      self.__description = ""
    else:
      self.__description = description
    self.__matching = matching

  def to_dict(self) -> dict[str, typing.Any]:
    """Converts this object to a dictionary ready for serialization
    to JSON.

    Returns
    -------
    dict
      Dictionary representing this object ready for serialization to JSON.

    """
    # New values should not be included in the dictionary by default. This
    # ensures pre-existing tests do not need to be modified.
    result: dict[str, typing.Any] = {"Name" : self.__name}
    if self.__arg_type is not AnyConnectorType:
      result["Type"] = self.__arg_type.type_string()
    if self.__default != "":
      result["Default"] = self.__default
    if self.__description != "":
      result["Description"] = self.__description
    if self.__connector_name is not None:
      result["ConnectorName"] = self.__connector_name
    if self.__matching is not None:
      result["Matching"] = self.__matching.value
    return result

  @property
  def arg_type(self) -> type[ConnectorType]:
    """The type of argument accepted by this connector."""
    return self.__arg_type


class WorkflowArgumentParser:
  """Interface for Workflows and WorkflowMAE.

  This class allows scripts to accept inputs and produce outputs when run
  via the Extend Python Script workflow component or the Python Script
  WorkflowMAE node. In particular, scripts which use this class can
  automatically generate their input and output connectors via the
  "Generate Connectors" button in the configuration.

  Scripts which use this class are also runnable via the command line -
  values for the input connectors can be passed as command line arguments.

  Starting in 1.7, this class can also accept its inputs as a JSON file.
  This is more robust (particularly when dealing with list inputs) than
  command line inputs. When the script is run in the WorkflowMAE Python Script
  component, inputs will be passed as a JSON file. The main observable
  differences between command line vs JSON inputs is that the JSON inputs
  raises different exceptions and the type of unknown inputs does not need
  to be explicitly specified.

  Using this class is highly recommended for scripts intended to be
  embedded in workflows.

  Parameters
  ----------
  description : str
    A description of the script.
    If --help is passed to the script, this will appear in the help
    message.
  allow_unknown_attributes : bool
    New in version 1.4.
    If unknown attributes should be allowed.
    If False (default), an error will be raised if an input which does not
    correspond to a declared input connector is provided.
    If True, no error will be raised if an input which does not correspond
    to a declared input connector is provided and the value of this input
    will be available via the unknown_attribute function.

  Notes
  -----
  This table displays which Python types can be passed to
  declare_input_connector() or declare_output_connector() for a connector
  which filters input/output to a specified type. The type displayed
  in Python type and ConnectorType columns can be used interchangeably
  for types with a value in both columns.
  N/A indicates not applicable.

  +------------------+-----------------------+------------------------+
  | Workflow type    | Python type           | ConnectorType          |
  +==================+=======================+========================+
  | String           | str                   | StringConnectorType    |
  +------------------+-----------------------+------------------------+
  | Integer          | int                   | IntegerConnectorType   |
  +------------------+-----------------------+------------------------+
  | Double           | float                 | DoubleConnectorType    |
  +------------------+-----------------------+------------------------+
  | DateTime         | datetime.datetime     | DateTimeConnectorType  |
  +------------------+-----------------------+------------------------+
  | Boolean          | bool                  | BooleanConnectorType   |
  +------------------+-----------------------+------------------------+
  | CSV String       | list                  | CSVStringConnectorType |
  +------------------+-----------------------+------------------------+
  | Selection        | N/A                   | WorkflowSelection      |
  +------------------+-----------------------+------------------------+
  | Point3D          | N/A                   | Point3DConnectorType   |
  +------------------+-----------------------+------------------------+
  | File             | pathlib.Path          | FileConnectorType      |
  +------------------+-----------------------+------------------------+
  | Folder           | N/A                   | DirectoryConnectorType |
  +------------------+-----------------------+------------------------+
  | Other            | str                   | N/A                    |
  +------------------+-----------------------+------------------------+

  Examples
  --------
  **Creating 3D Text**

  Script which creates 3D text with a specified message at a specified
  path, using a list to pass the colours and a point to pass position of the
  text. If this script is used in the Extend Python Workflow component
  it would have three input connectors "text", "position" and "colour"
  which would filter values to types "String", "Point3D" and "CSV String"
  respectively. Values passed to these connectors in the workflow are used to
  set the text, position and colour of the created 3D text.

  The script can also be run through the command line. If it
  was in a file called "create_3d_text.py" and was run using:
  py create_3d_text.py
  Then it would create a 3D text object in the currently running project
  with green text reading "Hello World" at [0, 0, 0].
  However if were run with the command:
  create_3d_text.py --text="Hi" --position="1, 2, 3" --colour="255, 0, 0"
  It will create a 3D text object with text "Hi" at the point [1, 2, 3]
  and with red text.

  >>> from mapteksdk.project import Project
  >>> from mapteksdk.workflows import (WorkflowArgumentParser,
  ...                                  Point3DConnectorType)
  >>> from mapteksdk.data import Text3D
  >>> parser = WorkflowArgumentParser("Create 3D text.")
  >>> parser.declare_input_connector("text", str, default="Hello World",
  ...                                description="The text of the new 3D text")
  >>> parser.declare_input_connector("position",
  ...                                Point3DConnectorType,
  ...                                default=[0, 0, 0],
  ...                                description="[x, y, z] position of text.")
  >>> parser.declare_input_connector("colour", list, default=[0, 255, 0],
  ...                                description="[R, G, B] colour for text.")
  >>> parser.parse_arguments()
  >>> project = Project()
  >>> with project.new(f"cad/{parser['text']}", Text3D) as new_text:
  ...     new_text.text = parser["text"]
  ...     new_text.location = parser["position"]
  ...     new_text.colour = parser["colour"]

  **Reversing strings**

  Python scripts which use this module are not required to connect
  to a project. This example can be performed without a running Project, so it
  does not construct one. This script takes the string representation of the
  input and reverses it. For example, the string "Eggs" would be reversed to
  "sggE" and the number "42.42424" would be reversed to "42424.24". Note that
  reversing some types, such as datetime.datetime will not give a valid object
  of that type.

  >>> from mapteksdk.workflows import WorkflowArgumentParser
  >>> parser = WorkflowArgumentParser("Reverses the input strings")
  >>> parser.declare_input_connector("string",
  ...                                None,
  ...                                description="String to reverse.",
  ...                                default="Something to reverse")
  >>> parser.declare_output_connector("reversed",
  ...                                 None,
  ...                                 description="The reversed string.")
  >>> parser.parse_arguments()
  >>> parser.set_output("reversed", parser["string"][::-1])
  >>> parser.flush_output() # Calling this is optional.

  **Dealing with unknown arguments**
  By default, WorkflowArgumentParser will transition the workflow into
  an error state if it detects an unknown input. However by setting
  allow_unknown_attributes to True when constructing the object this error
  will be suppressed and the unknown inputs will be available to the script
  via the unknown_attribute function. This is useful for scripts where
  the exact inputs cannot be known before the workflow is run and thus
  cannot be declared as input connectors.

  The following example sums all of the input attributes which are integers.
  This declares no input connectors and will use all attributes defined
  when the workflow component is run.

  >>> from mapteksdk.workflows import WorkflowArgumentParser
  >>> parser = WorkflowArgumentParser(
  ...   description="Sums all integer input attributes.",
  ...   allow_unknown_attributes=True)
  >>> parser.declare_output_connector(
  ...   "total",
  ...   int,
  ...   connector_name="Total",
  ...   description="The sum of all integer inputs.")
  >>> parser.parse_arguments()
  >>> total = 0
  >>> for name in parser.unknown_attribute_names:
  ...   try:
  ...     total += parser.unknown_attribute(name, int)
  ...   except ValueError:
  ...     # The attribute was not an integer, skip it.
  ...     continue
  >>> parser.set_output("total", total)

  **Filtering attributes**
  As of version 1.4, WorkflowArgumentParser allows outputs to be written
  without declaring an output connector. This is useful for filtering scripts
  which do not know what the outputs will be ahead of time.

  The following example filters out all attributes which cannot be
  converted to a floating point number.

  >>> from mapteksdk.workflows import WorkflowArgumentParser
  >>> parser = WorkflowArgumentParser(
  ...   description="Filters out all non-numeric attributes.",
  ...   allow_unknown_attributes=True)
  >>> parser.parse_arguments()
  >>> for name in parser.unknown_attribute_names:
  ...   try:
  ...     parser.set_output(name, parser.unknown_attribute(name, float))
  >>>   except ValueError:
  ...     # The attribute was not numeric, skip it.
  ...     continue

  """
  _input_argument: typing.ClassVar[str] = "workflow-input-path"
  # The argument used to set the output path.
  _output_argument: typing.ClassVar[str] = "workflow-output-path"
  # The argument used to set the items property.
  _items_argument: typing.ClassVar[str] = "workflow-attribute-items"

  _minimum_json_input_version: typing.ClassVar[int] = 1
  """The minimum JSON input version supported."""
  _maximum_json_input_version: typing.ClassVar[int] = 1
  """The maximum JSON input version supported."""

  def __init__(self, description: str="", allow_unknown_attributes: bool=False):
    # Argument parser used to parse the inputs.
    self._parser: argparse.ArgumentParser = argparse.ArgumentParser(
      description=description)
    self._parser.add_argument(
      f"--{self._input_argument}",
      type=str,
      default="")
    self._parser.add_argument(f"--{self._output_argument}",
                              type=str,
                              default="")
    self._parser.add_argument(f"--{self._items_argument}",
                              type=CSVStringConnectorType.from_string,
                              default=None)
    self._parser.add_argument("--describe", action='store_true', default=False,
                              help="Outputs a description of the input and"
                              "output connectors in JSON and exits script.")
    # Contains metadata of the connectors.
    self._input_connectors: dict[str, _Connector] = {}
    self._output_connectors: dict[str, _Connector] = {}

    # Data parsed from the connectors.
    self._known_args: argparse.Namespace | None = None

    # The path to the file to send output. Generally this is provided
    # by the workflow. If None, output is printed to the command line.
    # For testing this can be set to a stringIO object to avoid needing
    # to create a temporary file.
    self._output_path: str | None = None

    # Dictionary of values to write as outputs to output connectors.
    self._output_dictionary: dict[str, typing.Any] = {}

    # Function ran to write outputs even if flush_output() is never called.
    self.__exit_function: Callable | None = None

    # Used to ensure outputs aren't written after flush_output().
    self.__output_flushed: bool = False

    # The items list passed into the script.
    self.__attribute_items: list[str] | None = None

    # Description of the argument parser.
    self.description: str = description

    # Default value for declare_input_connector matching value.
    self.__default_matching: MatchAttribute | None = None

    # If unknown attributes should be allowed.
    self.__allow_unknown_attributes: bool = allow_unknown_attributes

    # Dictionary of unknown attributes.
    self.__unknown_attributes: dict[str, str] = {}

    # Parsed unknown attributes. This is used when inputs are provided as a
    # JSON file.
    self.__unknown_json_attributes: dict[str, typing.Any] = {}

    self.__are_inputs_json = False
    """If the inputs were provided as JSON."""

  def declare_input_connector(
    self,
    name: str,
    input_type: type[ConnectorType] | type,
    default: typing.Any=None,
    connector_name: str | None=None,
    description: str="",
    *,
    matching: MatchAttribute | None=None):
    """Declares that this script expects an input connector with
    the specified name to provide a value of the specified type.

    This has no effect if parse_arguments is not called.

    Parameters
    ----------
    name
      The name of the input connector. This must be a valid Python
      identifier; however it may include "-" characters.
      Pass this to get_input() after calling parse_arguments() to get
      any values passed through this input connector.
    input_type
      The data type the input connector will accept. This can either be
      a simple python data type or a connector type. See table above for
      how to match types between Workflows and Python.
    default
      The default value to use for this connector if no value is provided
      when parse_arguments is called (eg: If the connector was deleted
      from the workflow node).
      For non-bool connectors this is None by default.
      For bool connectors this is ignored - the default is always False.
    connector_name
      The user facing name of the connector. If specified, this will
      be the "Connector Name" and name will be the "Attribute name" of the
      connector. Unlike name, this can include whitespace characters.
    description
      Description of the input connector. Use this to provide
      instructions on how to use this input connector.
      If the input connectors are automatically generated this
      will be placed in the "Description" field of the input connector.
      If --help is passed to the script, this will be displayed as
      part of the help.
      The description is optional, however it is recommended
      to provide one.
    matching
      Requires Extend Plugins 2021.2 or higher.
      How attributes are matched on the workflows side. See the documentation
      for the enumeration for more details. If None (default), the value
      of default_matching will be used instead.

    Raises
    ------
    ValueError
      If input_type is not a ConnectorType subclass or is not a Python
      type with a corresponding ConnectorType subclass in
      workflows.connector_types module.
    ValueError
      If default is not the same type as input_type.
    ValueError
      If type is AnyConnectorType and matching is AttributeMatching.ByType.
    InvalidConnectorNameError
      If name is not a valid Python identifier.
    InvalidConnectorNameError
      If declaring a connector using a name reserved for use by the SDK.
    RuntimeError
      If called after parse_args() has been called.
    DuplicateConnectorError
      If two connectors are declared with the same name or, if their name
      would be the same if "-" characters are replaced with "_" characters.
    TypeError
      If matching is not a value from AttributeMatching or None.

    Notes
    -----
    **Using from workflows**

    Python scripts can be added to workflows by dragging and dropping
    the script onto the workflow. The connectors declared by this function
    (and declare_output_connectors) will be automatically added to the
    workflow component.

    **Using via the command line**

    A script using this class is not restricted to being run in workflows -
    it can also be run via the command line or a code editor.
    Inputs can be passed into input connectors as command line arguments.
    The general form of one of these command line arguments is:

    >>> --name=value

    Or if the name is only a single character long:

    >>> -n=value

    The main exception is for bool connectors. For them omit the equals sign
    and value - the presence of the argument name indicates True and its
    absence indicates False.

    Examples
    --------
    *Command line examples*
    Given a script called "script.py" which uses this module and Python
    interpreter set to be run via the "py" command,
    the following examples show how to pass an argument to the script.

    Connector with name="name" of type str.
    The quotation marks around the string are necessary to include the spaces
    as part of the string instead of as separate arguments.

    >>> py script.py --name="Tim the enchanter"

    Connector with name="n" of type str. For connectors with single
    letter names the name is prefixed with one dash instead of two.

    >>> py script.py -n="King Arthur"

    Connector with name="pre-sorted" of type bool. Note that for bool
    connectors no value is passed.

    >>> py script.py --pre-sorted # Gives pre-sorted=True
    >>> py script.py              # Gives pre-sorted=False

    Connector with name="count" of type int

    >>> py script.py --count=42

    Connector with name="tolerance" of type float.

    >>> py script.py --tolerance=3.14159

    Connector with name="time" of type datetime.datetime. Note that
    the date must be entered in ISO-8601 compliant format.

    >>> py script.py --time="2020-07-10T12:54:07"

    Connector with name="origin" of type list.

    >>> py script.py origin="1, 1, 1"

    """
    if self._has_parsed_args:
      raise RuntimeError("Cannot declare input connector after parse_args()")
    self._raise_if_connector_name_invalid(name)
    # The dictionary key is the name with dashes replaced with underscores.
    # This replacement is done by argparse to make the name a valid
    # Python identifier. Do it here as well so that the key matches
    # what will be in the output of argparse.
    key = name.replace("-", "_")

    if key in self._input_connectors:
      message = f"Cannot declare two connectors with name: {key}"
      raise DuplicateConnectorError(message)

    if matching is None:
      matching = self.__default_matching

    if matching is not None and not isinstance(matching, MatchAttribute):
      raise TypeError(default_type_error_message(
        "matching", matching, MatchAttribute))

    prefix = "--"
    if len(name) == 1:
      prefix = "-"
    arg_name = f"{prefix}{name}"

    connector_type = _python_to_connector_type(input_type)

    if (connector_type is AnyConnectorType
        and matching is MatchAttribute.BY_TYPE):
      raise ValueError("AnyConnectorType does not support match by type")

    # :TODO: Maybe allow ConnectorType subclasses to set the action?
    if connector_type == BooleanConnectorType:
      # Special handling for bool arguments. Default value is always
      # False.
      self._parser.add_argument(arg_name, action='store_true',
                                default=False, help=description)
      default=False
    else:
      # :TRICKY: 2021-09-22. The type argument of add_argument
      # accepts any callable which takes a string and returns a value.
      # This is passing a "from_string" function instead of a constructor.
      self._parser.add_argument(arg_name, type=connector_type.from_string,
                                default=default,
                                help=description)

    self._input_connectors[key] = _Connector(
      name,
      connector_type,
      default=default,
      connector_name=connector_name,
      description=description,
      matching=matching)

  def declare_output_connector(
      self,
      name: str,
      output_type: type[ConnectorType] | type,
      connector_name: str | None=None,
      description: str | None=None):
    """Declares that this script will provide a value for an output connector.

    You should call set_output once for each connector declared with this
    function. Failing to provide a value for an output connector will cause the
    Workflow to halt.

    Parameters
    ----------
    name
      The name of the output connector. This must be a valid Python
      identifier however it may include - characters.
    output_type
      The type of the output.  This can either be a simple python type or a
      connector type. See the table in declare_input_connector to choose the
      correct Python type to match the workflows type.
    connector_name
      The user facing name of the connector. If specified, this will
      be the "Connector Name" and name will be the "Attribute name" of the
      connector. Unlike name, this can include whitespace characters.
    description
      Description of the output connector. If the connectors are automatically
      generated, this will be placed in the Description field of the connector.
      If None (default) the description will be the empty string.

    Raises
    ------
    ValueError
      If input_type is not a ConnectorType subclass or is not a Python
      type with a corresponding ConnectorType subclass in
      workflows.connector_types module.
    InvalidConnectorNameError
      If the connector name is invalid.
    RuntimeError
      If called after parse_args() has been called.

    Notes
    -----
    Changed in version 1.4.
    Prior to version 1.4, all outputs had to be declared by this function.
    In version 1.4 outputs can be set without declaring a corresponding
    output connector. Providing outputs without declaring a connector is
    useful for scripts where their outputs cannot be known before the
    workflow / script is run.

    """
    if self._has_parsed_args:
      raise RuntimeError("Cannot declare output connector after parse_args()")
    self._raise_if_connector_name_invalid(name)

    connector_type = _python_to_connector_type(output_type)

    if description is None:
      description = ""

    self._output_connectors[name] = _Connector(name=name,
                                               arg_type=connector_type,
                                               connector_name=connector_name,
                                               description=description)

  def parse_arguments(self, arguments: list[str] | None=None):
    """Indicates that the script has finished configuring the connectors
    and allows values to be read from the input connectors. This will
    also allow values to be written to the output connectors.

    If there is an error parsing the arguments, a SystemExit will be
    raised. This ensures your script will not run with invalid inputs.

    Parameters
    ----------
    arguments
      List of arguments to parse. If None (default) then the arguments
      are parsed from sys.argv[:1]. Inputs from workflows can only be
      accepted if this parameter is not specified.

    Raises
    ------
    SystemExit
      If the value passed to a connector is not compatible with the type
      specified when declare_argument was called for that connector.
      This is not raised in WorkflowMAE.
    SystemExit
      If an unknown argument appears.
      This is not raised in WorkflowMAE.
    MalformedInputError
      If the input is provided as a JSON file and the JSON is malformed.
      This only applies to WorkflowMAE.
    InputDimensionMismatchError
      If a single value is provided for a list input, or a list value is
      provided for a singular input.
      This only applies to WorkflowMAE.
    InputTypeError
      If an input has the wrong type.
      This only applies to WorkflowMAE.
    MissingInputError
      If an input is missing.
      This only applies to WorkflowMAE.
    UnknownInputError
      If this object was constructed with allow_unknown_attributes=False
      (The default) and there is an input which doesn't correspond to a
      declared input port.
      This only applies to WorkflowMAE.
    UnsupportedInputTypeError
      If an input contains a type which cannot be converted to a Python type,
      potentially due to the SDK being too old to support that input.
      This only applies to WorkflowMAE.
    InputFormatTooNewError
      If the input format is too new for this class to parse. A newer version
      of the SDK is required to parse it.
      This only applies to WorkflowMAE.
    InputCannotBeNoneError
      If an input which does not support null values has a null value.
      This only applies to WorkflowMAE.

    Warnings
    --------
    When you click the "Generate Connectors" button in the workflow component,
    the Python Script will be executed until this function is called (And
    thus to completion if this is never called). You should make sure
    that no code which has side effects is called before calling this function.

    You should always call this function before calling Project().

    Printing to standard output before calling this function will cause
    the workflow component to fail to generate connectors.

    Notes
    -----
    Usually this function will be called as:
    workflows.parse_arguments()

    """
    args = None
    if arguments is None:
      args = sys.argv[1:]
    else:
      args = arguments

    known_args = None
    unknown_args = None
    if self.__allow_unknown_attributes:
      known_args, unknown_args = self._parser.parse_known_args(args)
    else:
      known_args = self._parser.parse_args(args)

    self._output_path = known_args.workflow_output_path

    if known_args.describe:
      if self._output_path:
        with open(self._output_path, "w", encoding="utf-8") as json_file:
          self.describe_connectors(json_file)
      else:
        description = io.StringIO()
        self.describe_connectors(description)
        print(description.getvalue())

      sys.exit(0)

    input_path = known_args.workflow_input_path
    if input_path:
      self.__are_inputs_json = True
      # Arguments are provided as a JSON file.
      self._known_args = self._parse_args_from_json(input_path)
    else:
      # Arguments are provided as command line arguments.
      self._known_args = known_args
      if unknown_args is not None:
        self.__parse_unknown_args(unknown_args)

  def __getitem__(self, name: str) -> typing.Any:
    if not isinstance(name, str):
      raise TypeError(default_type_error_message("name", name, str))

    return self.get_input(name)

  def get_input(self, name: str) -> typing.Any:
    """Returns the value passed to the connector with the specified name.

    For convenience, this function can also be called via
    subscripting this object.

    Parameters
    ----------
    name
      The name of the argument to retrieve the value for.

    Returns
    -------
    type
      Value for argument name.

    Raises
    ------
    KeyError
      If there is no argument with name (Potentially because
      parse_arguments has not been called).

    """
    if not self._has_parsed_args:
      raise KeyError(
        "You must call parse_arguments() before before get_input().")
    # Replace dashes with underscores. This is done by argparse to make
    # the argument name a valid Python identifier.
    name = name.replace("-", "_")

    if name in self._input_connectors:
      value = getattr(self._known_args, name)
      return value

    raise KeyError(f"No argument with name: {name}")

  @property
  def unknown_attribute_names(self) -> tuple[str, ...]:
    """A tuple containing the names of the unknown attributes.

    This will always be empty if this object was not constructed to
    allow unknown arguments.

    Notes
    -----
    New in version 1.4.
    """
    if not self._has_parsed_args:
      raise RuntimeError(
        "Cannot access unknown attributes before parsing arguments.")
    return tuple(self.__unknown_attributes.keys())

  @typing.overload
  def unknown_attribute(self, name: str, dtype: type[T]) -> T:
    ...

  @typing.overload
  def unknown_attribute(self, name: str) -> typing.Any:
    ...

  def unknown_attribute(self,
      name: str,
      dtype: type[T] | None=None # type: ignore
      # Type checking fails on the above line due to a bug in mypy.
      # https://github.com/python/mypy/issues/3737
      ) -> T:
    """Read the value of an unknown attribute.

    Unknown attributes are input attributes of the workflow component which do
    not correspond to any of the declared input connectors.

    Allowing unknown attributes is useful for writing scripts where the inputs
    cannot be determined before the workflow or script is run (e.g. scripts
    which filter the input attributes).

    Parameters
    ----------
    name
      The name of the attribute.
    dtype
      The expected Python type of the attribute (e.g. int). This
      is str by default.
      When running in Workflows, this is str by default.
      When running in WorkflowMAE, the type will be automatically derived
      from the workflow. This argument should not need to be specified.
      In WorkflowMAE, this only supports simple types (e.g. int).

    Returns
    -------
    dtype
      The value of the unknown attribute converted to the specified type.

    Raises
    ------
    KeyError
      If there is no unknown attribute with the specified name. This will
      always be raised if this object was not constructed to allow unknown
      attributes.
    ValueError
      If the value cannot be converted to the specified type.

    Notes
    -----
    New in version 1.4.
    """
    if not self._has_parsed_args:
      raise RuntimeError(
        "Cannot access unknown attributes before parsing arguments.")
    if self.__are_inputs_json:
      # Hack to get Point3D inputs working with unknown args.
      if dtype == Point3DConnectorType:
        dtype = np.ndarray
      return self.__unknown_input_json(name, dtype)
    if dtype is None:
      dtype = str # type: ignore
    return self.__unknown_input_command_line(name, dtype) # type: ignore

  def __unknown_input_command_line(
      self,
      name: str,
      dtype: type[T]
  ) -> T:
    """Return unknown inputs which came from the command line.

    The input arrives as a string with no type information, so this is reliant
    on the caller providing the type so that the input can be parsed.
    """
    if name in self.__unknown_attributes:
      converter = _python_to_connector_type(dtype)
      return converter.from_string(self.__unknown_attributes[name])
    # The absence of a boolean value is considered "False".
    if dtype in (bool, BooleanConnectorType):
      return False # type: ignore
    raise KeyError(f"No attribute with name: '{name}'")

  def __unknown_input_json(
      self,
      name: str,
      dtype: type[T] | None
  ) -> T:
    """Return unknown inputs which came from a JSON file.

    These inputs are sent with type information, so the data type is optional.
    Specifying it will result in attempting to convert to the specified dtype.
    """
    if name in self.__unknown_json_attributes:
      value = self.__unknown_json_attributes[name]
      if dtype is None:
        return value
      if isinstance(value, dtype):
        return value
      return dtype(value)
    raise KeyError(f"No attribute with name: '{name}'")

  def set_output(self, name: str, value: typing.Any):
    """Sets the value to be written to an output.

    This should be called once for each declared output connector. Failing
    to do so will cause the workflow to halt.

    Note that the value will not appear in the workflow until the script
    successfully exits.

    Parameters
    ----------
    name
      Name of the output. This should match the name of an output connector.
    value
      Value to provide for the output. This should be a simple type, such as
      an int, float, str, list or datetime.

    Raises
    ------
    TypeError
      If name does not correspond to an output attribute and its type
      cannot be sent to the workflow.
    ValueError
      If value cannot be converted to the type passed in to
      declare_output_connector for name.
    RuntimeError
      If you attempt to call this twice for the same connector.
    RuntimeError
      If called after calling flush_output.

    Notes
    -----
    Changed in version 1.4. This function no longer raises an error if
    name does not correspond to a declared output connector.

    """
    if self.__output_flushed:
      raise RuntimeError("Cannot set output after calling flush_output()")

    if name in self._output_dictionary:
      raise RuntimeError("Cannot set value for output connector "
                         "more than once.")

    try:
      # If the output connector was declared, use its type.
      expected_type = self._output_connectors[name].arg_type
    except KeyError:
      try:
        # Otherwise attempt to derive the type.
        expected_type = _python_to_connector_type(type(value))
      except ValueError as error:
        raise TypeError(
          f"Invalid output: '{value}' (type: {type(value).__name__}) for "
          f"output: '{name}'"
        ) from error

    final_value = expected_type.to_json(value)
    self._output_dictionary[name] = final_value

    # Register the function to write these outputs to the output file
    # when the script exits. This way the user doesn't need to explicitly
    # call flush_output.
    self.__register_exit_function()

  def flush_output(self):
    """Flushes the output making it available to the output connectors.
    Call this function once you have called set_output() for each output
    connector.

    After this function has been called, you cannot write any more values to
    the output connectors.

    Raises
    ------
    RuntimeError
      If this function is called more than once.

    """
    if self.__output_flushed:
      raise RuntimeError("flush_output may only be called once.")
    self.__output_flushed = True

    # Make sure this isn't called again atexit.
    self.__unregister_exit_function()

    # Only include items if it is not None.
    if self.__attribute_items is not None:
      # Can't use items property here as accessing it would register
      # the exit function again.
      self._output_dictionary[self._items_argument] = self.__attribute_items

    if self._output_path:
      if isinstance(self._output_path, str):
        with open(self._output_path, "w", encoding="utf-8") as json_file:
          # The separators=(",", ":") removes spaces after commas and colons
          # in the resulting JSON. This makes the representation as compact
          # as possible for faster serialisation and deserialisation.
          json.dump(self._output_dictionary, json_file, separators=(",", ":"))
      elif isinstance(self._output_path, io.TextIOBase):
        json.dump(self._output_dictionary,
                  self._output_path,
                  separators=(",", ":"))
      else:
        raise ValueError(f"Invalid output path: {self._output_path}")
    else:
      # Pretty print the JSON.
      print(json.dumps(self._output_dictionary, indent=2))

  @property
  def default_matching(self) -> MatchAttribute | None:
    """The default matching type used by declare_input_connector().

    If this is set to a value from the MatchAttribute enum, if the matching
    parameter of generate_connectors is None the value of this property will be
    used instead.

    If this is None (default) the connector will use the default matching
    type as defined by the workflow component (this is currently
    MatchAttribute.BY_TYPE).

    Raises
    ------
    TypeError
      If set to a value which is not part of the MatchAttribute.BY_TYPE enum.

    Examples
    --------
    This property can be used to set all connectors to match attribute by name.
    The matching argument can be used to specify a different value for
    specific connectors.

    >>> from mapteksdk.workflows import (WorkflowArgumentParser,
    ...                                  MatchAttribute, StringConnectorType)
    >>> parser = WorkflowArgumentParser("Example showing matching by name.")
    >>> parser.default_matching = MatchAttribute.BY_NAME
    >>> # These two connectors will now match by name instead of by type.
    >>> parser.declare_input_connector("input_path", StringConnectorType)
    >>> parser.declare_input_connector("output_path", StringConnectorType)
    ... # The third connector specifies a different matching scheme
    ... # and will not match.
    >>> parser.declare_input_connector("attribute",
    ...                                StringConnectorType,
    ...                                matching=MatchAttribute.DO_NOT_MATCH,
    ...                                default="grade")
    >>> parser.parse_arguments()
    >>> # Do something useful with the arguments.
    """
    return self.__default_matching

  @default_matching.setter
  def default_matching(self, value: MatchAttribute):
    if not isinstance(value, MatchAttribute):
      raise TypeError(default_type_error_message(
        "default_matching", value, MatchAttribute))
    self.__default_matching = value

  def describe_connectors(self, destination: io.TextIOWrapper):
    """Describes the input and output connectors.

    This is used by the Extend Python Workflow Component to generate the
    connectors — it is not recommended to use this function in scripts.

    This results in an Object with three fields:
    Description : The description of the Python script.
    Input : Description of the input connectors.
    Output : Description of the output connectors.

    Parameters
    ----------
    destination
      The stream to write the description to.

    """
    description: _WorkflowDescription = {
      "Description" : self.description,
      "InputConnectors" : [],
      "OutputConnectors" : [],
      "SupportsCommandLineArguments" : True,
      "MinimumJsonInputVersion" : self._minimum_json_input_version,
      "MaximumJsonInputVersion" : self._maximum_json_input_version,
    }
    for value in self._input_connectors.values():
      description["InputConnectors"].append(value.to_dict())
    for value in self._output_connectors.values():
      description["OutputConnectors"].append(value.to_dict())
    if self.__allow_unknown_attributes:
      description["AllowUnknownAttributes"] = True

    # Separators argument is used to remove superfluous whitespace.
    json.dump(description, destination, separators=(",", ":"))

  @property
  def items(self) -> list[str]:
    """The items array set by a Data Editor workflow component.

    Set this to None to indicate no change should be made to the items
    array.

    Raises
    ------
    RuntimeError
      If accessed before parse_arguments() or if set after flush_output().

    Warnings
    --------
    This requires Python Plugin version 2021.1 to be effective.

    Notes
    -----
    When using Python Plugin versions less than 2021.1, the workflow
    component will ignore the items list. This property will always start
    as an empty list and changes will not be propagated back to the workflow.

    Lists and dicts should not be added to this list. They will cause
    errors on the workflow side.

    """
    if not self._has_parsed_args:
      raise RuntimeError(
        "You must call parse_arguments() before getting items.")
    # Only load items value from the arguments if it is used. This means
    # that if the Python Script doesn't access items, they won't
    # be written out, so the workflow component will know not to change
    # the attribute items.
    if self.__attribute_items is None:
      self.__attribute_items = self._known_args.workflow_attribute_items
    # If it is still None it was not set. Return an empty list.
    if self.__attribute_items is None:
      self.__attribute_items = []
    self.__register_exit_function()
    return self.__attribute_items

  @items.setter
  def items(self, value: list[str]):
    if self._known_args is None:
      raise RuntimeError("You must call parse_arguments() before "
                         "setting items.")
    if self.__output_flushed:
      raise RuntimeError("Cannot set items after flushing output.")

    self.__register_exit_function()

    if value is None:
      self.__attribute_items = None
    else:
      self.__attribute_items = list(value)

  @property
  def _has_parsed_args(self):
    """If the parse_arguments() function has been called."""
    return self._known_args is not None

  def _parse_args_from_json(self, json_path: str
                            ) -> argparse.Namespace:
    """Parse arguments from a JSON input file.

    Parameters
    ----------
    json_path
      JSON read from the file.

    Returns
    -------
    Namespace
      Namespace similar to what would be returned by argparse if the arguments
      had been provided via the command line.
    """
    with open(json_path, "r", encoding="utf-8") as input_file:
      workflow_inputs: WorkflowInputs = json.load(input_file)
    known_arguments: dict[str, typing.Any] = {}
    try:
      self._check_input_version_supported(workflow_inputs)

      expected_inputs: dict[str, tuple[SupportedTypeNames, Dimensionality]] = {
        name : (
          connector.arg_type.json_type_string(),
          connector.arg_type.json_dimensionality()
        ) for name, connector in self._input_connectors.items()
      } # type: ignore
      for workflow_input in workflow_inputs["inputs"]:
        is_known_input = True
        name = workflow_input["name"]
        data_type = workflow_input["dataType"]
        actual_type_name = data_type["typeName"]

        # Ensure that the input is the correct type.
        if not self._is_known_input(workflow_input, expected_inputs):
          if not self.__allow_unknown_attributes:
            raise UnknownInputError(name)
          is_known_input = False

        parsed_input = parse_input(workflow_input)
        # :HACK: 2023-10-26 WorkflowSelection is implicitly a list due to the
        # original workflows system always considering selections to be a
        # list.
        # The parse_input() function doesn't support a list of values
        # becoming a single output, so need to manually construct the
        # WorkflowSelection to ensure the behaviour is consistent with
        # command line arguments.
        if actual_type_name == "DataEngineObject":
          parsed_input = WorkflowSelection.from_string_list(parsed_input)

        if is_known_input:
          known_arguments[name] = parsed_input
        else:
          self.__unknown_json_attributes[name] = parsed_input

      missing_arguments = set(
        expected_inputs.keys()).difference(
          known_arguments.keys())
      if len(missing_arguments) != 0:
        raise MissingInputError(missing_arguments)
      return argparse.Namespace(**known_arguments)
    except KeyError as error:
      raise MalformedInputError(
        "The inputs to the script could not be read. A field was missing."
        ) from error

  def _check_input_version_supported(self, workflow_inputs: WorkflowInputs):
    """Raise an error if the input version is not supported.

    Raises
    ------
    InputFormatNotSupportedError
      If the input's version is below the minimum supported version or above
      the maximum supported version.
    """
    version = workflow_inputs["version"]

    if (version < self._minimum_json_input_version
        or version > self._maximum_json_input_version):
      raise InputFormatNotSupportedError(
        version,
        self._maximum_json_input_version,
        self._minimum_json_input_version
      )

  def _is_known_input(
      self,
      workflow_input: WorkflowInput,
      expected_inputs: dict[str, tuple[SupportedTypeNames, Dimensionality]]
    ) -> bool:
    """True if the input corresponds to an input port, False otherwise.

    This also checks if the input's type matches the type of the input port.

    Parameters
    ----------
    workflow_input
      The input to check if it corresponds to an input port.
    expected_inputs
      Dictionary mapping the names of expected ports to a tuple containing
      the type name and dimensionality of those ports.

    Raises
    ------
    InputTypeError
      If the input corresponds to an input port and the type of the input
      does not match the type of the input port.
    """
    name = workflow_input["name"]
    actual_type = workflow_input["dataType"]
    actual_type_name = actual_type["typeName"]
    actual_dimensionality = actual_type["dimensionality"]
    expected_type, expected_dimensionality = expected_inputs.get(
      name, (None, None))
    if None not in (expected_type, expected_dimensionality):
      # A blank type name indicates the Any type.
      if (expected_type != ""
          and (actual_type_name, actual_dimensionality)
          != (expected_type, expected_dimensionality)):
        raise InputTypeError(
          name,
          expected_type_name=f"{expected_type} ({expected_dimensionality})",
          actual_type_name=f"{actual_type_name} ({actual_dimensionality})"
        )
      return True
    return False

  def __register_exit_function(self):
    """Registers flush output to run when the process exits.

    This ensures the user does not need to explicitly call
    flush_output. This function will only register the exit function once
    even if it is called multiple times.

    Raises
    ------
    RuntimeError
      If output has been flushed.

    """
    if self.__output_flushed:
      raise RuntimeError("Operation is unsupported after output is flushed.")
    if not self.__exit_function:
      self.__exit_function = atexit.register(
        self.flush_output)

  def __unregister_exit_function(self):
    """Deregisters the exit function. This is called in flush_output
    to ensure that if the user explicitly calls flush output then
    the function is not called twice.

    This has no effect if the exit function is not registered.

    """
    atexit.unregister(self.__exit_function)
    self.__exit_function = None

  def __parse_unknown_args(self, unknown_args: list[str]):
    """Parses the unknown arguments.

    This makes the unknown arguments available through this class.

    Parameters
    ----------
    unknown_args
      A list of strings of the following forms:
      --name=value
      -n=value
      --name
      -n

    """
    for unknown_arg in unknown_args:
      if "=" in unknown_arg:
        # The unknown arg is of the form:
        # --name=value
        # or
        # -n=value
        key, value = unknown_arg.split("=", maxsplit=1)
      else:
        # The unknown arg is of the form:
        # -k
        # or
        # --key
        key = unknown_arg
        value = str(True)
      key = key.strip("-")
      self.__unknown_attributes[key] = value

  @classmethod
  def _raise_if_connector_name_invalid(cls, name: str):
    """Raises an InvalidConnectorName error if the name is invalid."""
    reserved_names = (cls._output_argument, cls._items_argument)
    if name in reserved_names:
      raise InvalidConnectorNameError(
        f"Cannot declare connector with name : {name}. The name is reserved.")
    if not name.replace("-", "_").isidentifier():
      raise InvalidConnectorNameError(f"Invalid name : {name}. "
                                      "Name is not a valid identifier")

def _python_to_connector_type(python_type: type | type[ConnectorType]
    ) -> type[ConnectorType]:
  """Get the corresponding connector type for a Python type.

  Parameters
  ----------
  python_type
    Python type to get the corresponding connector type for.

  Returns
  -------
  ConnectorType
    If python_type is a ConnectorType it will be returned.
    Otherwise this will be a ConnectorType subclass defined in
    workflows.connector_types which corresponds
    to python_type.

  Raises
  ------
  ValueError
    If there is no basic ConnectorType subclass corresponding to python_type.
  """
  try:
    if issubclass(python_type, ConnectorType):
      return python_type
  except TypeError:
    pass

  try:
    return python_type_to_connector_type(python_type)
  except KeyError as error:
    raise ValueError("Connector type must be a ConnectorType subclass"
      ) from error
