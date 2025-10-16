"""Schema for JSON inputs.

This defines how JSON inputs for a workflow read from a file are defined.
"""
###############################################################################
#
# (C) Copyright 2023, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

from collections.abc import Sequence
import sys
import typing

if sys.version_info >= (3, 8):
  SupportedTypeNames = typing.Literal[
    "String",
    "Integer",
    "Double",
    "Boolean",
    "DateTime",
    "Point3D",
    "File",
    "Folder",
    "DataEngineObject"
  ]
  """The names of types supported by the schema."""


  Dimensionality = typing.Literal[
    "Single",
    "List"
  ]
  """The supported dimensionality types."""


  class Point3dValue(typing.TypedDict):
    """Value representation for Point 3D."""
    x: float
    y: float
    z: float

  if sys.version_info >= (3, 10):
    PrimitiveValues: typing.TypeAlias = (
      int | float | bool | str | Point3dValue
    )
    """Single values supported by the schema."""

    SupportedValues: typing.TypeAlias = (
      PrimitiveValues | Sequence[PrimitiveValues] | None
    )
    """Values supported by the values field.

    Depending on the data type, only a subset of these will be allowed.
    """
  else:
    PrimitiveValues: typing.TypeAlias = typing.Union[
      int, float, bool, str, Point3dValue
    ]
    SupportedValues: typing.TypeAlias = typing.Union[
      PrimitiveValues, typing.Sequence[PrimitiveValues], None
    ]


  class WorkflowType(typing.TypedDict):
    """The type of an input."""
    typeName: SupportedTypeNames
    """The data type associated with the input."""
    dimensionality : Dimensionality
    """The dimensionality associated with the input."""
    canBeNull: bool
    """If the value can be null."""


  class WorkflowInput(typing.TypedDict):
    """A single input for the Workflow."""
    name: str
    """The name associated with the input."""
    dataType: WorkflowType
    """The data type of this input."""
    value: SupportedValues
    """The value of the input.

    The exact type will depend on the data type.
    """


  class WorkflowInputs(typing.TypedDict):
    """JSON inputs for a Workflow."""
    version: int
    """The version of the input schema in use.

    If this is greater than the highest version the SDK understands, an error
    will be raised.

    Notes
    -----
    The version only needs to be incremented if a backwards incompatible
    change is made. Hopefully this never needs to happen.
    But if such a change needs to be made, the SDK should support both the
    new and old versions of the inputs for a version or two to make the
    switch over to the new format smoother for users.
    """
    inputs: list[WorkflowInput]
    """The inputs to the script."""
else:
  SupportedTypeNames = str
  SupportedValues = str
  Point3dValue = dict
  WorkflowInput = dict
  WorkflowInputs = dict
  WorkflowType = dict
