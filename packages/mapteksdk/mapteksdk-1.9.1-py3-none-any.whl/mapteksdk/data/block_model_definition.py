"""The block model definition class."""
###############################################################################
#
# (C) Copyright 2024, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import enum
import typing

import numpy as np

from ..internal.singular_data_property_read_write import (
  SingularDataPropertyReadWrite as DataProperty,
)
from ..internal.block_model_definition_schema import (
  InternalBlockModelDefinition as InternalDefinition,
)
from ..internal.lock import LockType
from ..internal.util import default_type_error_message
from .base import DataObject, StaticType
from .errors import DegenerateTopologyError
from .objectid import ObjectID

if typing.TYPE_CHECKING:
  from collections.abc import Sequence

  from ..capi import VulcanApi
  from ..internal.block_model_definition_schema import _Variable

  # This uses the Python type rather than the more accurate c type because
  # that makes the code simpler because there are less types to handle.
  PythonVariableTypes: typing.TypeAlias = (
    str | int | float | bool | None
  )
  """The Python data types for block model definition variables."""

class SubblockRatio(enum.Enum):
  """Enum representing the ratio between subblocks and primary blocks.

  These ratios are the ones which are well supported by DomainMCF.
  A block model can have a different ratio (potentially a different one
  in each dimension), though such block models are not supported by DomainMCF.
  """
  NO_SUBBLOCKS = 1
  """The model has no subblocks."""
  ONE_HALF = 1 / 2
  """The subblocks are half the size in every dimension."""
  ONE_QUARTER = 1 / 4
  """The subblocks are one quarter the size in every dimension."""
  ONE_EIGHTH = 1 / 8
  """The subblocks are one eighth the size in every dimension."""
  ONE_SIXTEENTH = 1 / 16
  """The subblocks are one sixteenth the size in every dimension."""


class VariableType(enum.Enum):
  """The data types for variables in block model definitions."""
  STRING = "string"
  """The variable stores text."""
  DOUBLE = "double"
  """The variable stores IEEE double precision floating point numbers."""
  FLOAT = "float"
  """The variable stores IEEE single precision floating point numbers."""
  SHORT = "integer32"
  """The variable stores a 32 bit signed integers."""
  INTEGER = "integer64"
  """The variable stores a 64 bit signed integers."""
  BOOLEAN = "boolean"
  """The variable stores boolean values."""
  BYTE = "byte"
  """The variables stores a 8 bit integer."""
  UNKNOWN = "unknown"
  """Python does not recognise the data type."""

  @classmethod
  def from_string(cls, value: str) -> typing.Self:
    """Get a variable type from a string.

    Unlike the constructor, this will return UNKNOWN instead of raising an
    error for values not in the enum.
    """
    try:
      return cls(value)
    except (ValueError, TypeError):
      return cls(cls.UNKNOWN)

  @property
  def python_type(self) -> type[PythonVariableTypes]:
    """The Python type corresponding to this enum value."""
    mapping = {
      self.STRING : str,
      self.DOUBLE : float,
      self.FLOAT : float,
      self.SHORT : int,
      self.INTEGER : int,
      self.BOOLEAN : bool,
      self.BYTE : int,
    }
    try:
      return mapping[self]
    except KeyError:
      return type(None)

  @property
  def numpy_dtype(self) -> np.dtype:
    """The numpy dtype corresponding to this enum value."""
    mapping = {
      self.STRING : str,
      self.DOUBLE : np.float64,
      self.FLOAT : np.float32,
      self.SHORT : np.int32,
      self.INTEGER : np.int64,
      self.BOOLEAN : bool,
      self.BYTE : np.int8,
    }
    try:
      return mapping[self]
    except KeyError:
      return np.dtype(None)


class Variable:
  """A variable defined in a block model definition."""
  def __init__(
    self,
    backing: _Variable
  ):
    self.__backing = backing

  @property
  def name(self) -> str:
    """The name of the variable."""
    return self.__backing["Name"]

  @name.setter
  def name(self, new_name: str):
    self.__backing["Name"] = str(new_name)

  @property
  def data_type(self) -> VariableType:
    """The type of data stored in this variable.

    Changing the data type will clear the default value.
    """
    return VariableType.from_string(self.__backing["Type"])

  @data_type.setter
  def data_type(self, data_type: VariableType):
    if not isinstance(data_type, VariableType):
      raise TypeError(
        default_type_error_message(
          "data_type",
          data_type,
          VariableType
        )
      )
    self.__backing["Type"] = data_type.value
    # Clear the default to avoid having an invalid value.
    self.__backing["Default"] = ""

  @property
  def default(self) -> PythonVariableTypes:
    """The default value represented as a string."""
    python_type = self.data_type.python_type
    if python_type is type(None):
      return None

    try:
      return python_type(self.__backing["Default"])
    except (ValueError, TypeError):
      return python_type()

  @default.setter
  def default(self, default: str | float | int | bool):
    python_type = self.data_type.python_type
    if python_type is type(None):
      raise ValueError(
        "Cannot set default value for variable with unknown type.")
    value = python_type(default)
    self.__backing["Default"] = str(value)

  @property
  def description(self) -> str:
    """A description of the variable."""
    return self.__backing["Description"]

  @description.setter
  def description(self, description: str):
    self.__backing["Description"] = str(description)


class BlockModelDefinition(DataObject):
  """The definition for a block model.

  This enables configuring the specification for the primary and subblocks
  of a block model and the variables in the model.

  Raises
  ------
  InvalidPrimaryBlockSizesError
    If on save the primary block sizes are invalid.
  """
  VariableType: typing.ClassVar = VariableType
  """Type used to represent variables defined by this object."""
  Variable: typing.ClassVar = Variable
  """Enum used to represent the data type of variables."""

  def __init__(
    self,
    object_id: ObjectID | None=None,
    lock_type: LockType=LockType.READWRITE,
    *,
    rollback_on_error: bool = False
  ):
    is_new = False
    if object_id is None:
      object_id = ObjectID(self._vulcan_api().NewBlockModelDefinition())
      is_new = True
    super().__init__(object_id, lock_type, rollback_on_error=rollback_on_error)
    self.__definition: DataProperty[InternalDefinition] = DataProperty(
      "definition",
      lambda: [],
      read_only=self.is_read_only,
      load_function=self._load_definition,
      save_function=self._save_definition
    )
    if is_new:
      # For new definitions, construct the initial JSON in Python rather than
      # read it from C++.
      self.__definition.value = InternalDefinition.blank_definition()

  @classmethod
  def _vulcan_api(cls) -> VulcanApi:
    """Access the Vulcan C API."""
    return cls._application_api().vulcan

  @classmethod
  def static_type(cls) -> StaticType:
    return cls._vulcan_api().BlockModelDefinitionType()

  def _extra_invalidate_properties(self):
    self.__definition.invalidate()

  def _record_object_size_telemetry(self):
    self._record_size_for(
      "Blocks",
      self.block_counts[0] * self.block_counts[1] * self.block_counts[2]
    )

  def _save(self):
    self.__definition.save()

  def _load_definition(self) -> InternalDefinition:
    return InternalDefinition.from_json(
          self._vulcan_api().ReadBlockModelDefinitionJson(self._lock.lock))

  def _save_definition(self, schema: InternalDefinition):
    try:
      self._vulcan_api().WriteBlockModelDefinitionJson(
        self._lock.lock, schema.to_json())
    except RuntimeError:
      raise DegenerateTopologyError(
        "One or more properties of the block model definition included a NaN "
        "or infinite value."
      ) from None

  @property
  def _definition(self) -> InternalDefinition:
    """The JSON representation of the block model definition."""
    return self.__definition.value

  @property
  def block_size(self) -> tuple[float, float, float]:
    """The size of the primary blocks.

    This is of the form (x_size, y_size, z_size).
    """
    return self._definition.block_size

  @property
  def subblock_size(self) -> tuple[float, float, float]:
    """The size of the subblocks.

    This is of the form (x_size, y_size, z_size). This will be equal to the
    block_size if the model is dense.
    """
    return self._definition.subblock_size

  @property
  def rounded_subblock_size(self) -> tuple[float, float, float]:
    """The size of the subblocks rounded to the supported ratio."""
    ratio = self.supported_subblock_ratio
    # Size is a length three tuple, so the output tuple must also have
    # a length of three.
    return tuple(
      size * ratio.value for size in self.block_size
    ) # type: ignore

  @property
  def subblock_ratio(self) -> tuple[float, float, float]:
    """The subblock ratio in each dimension.

    This is of the form: (x_ratio, y_ratio, z_ratio) where each ratio is
    between 0 and 1.

    Notes
    -----
    This is the block size divided by the sub block size.
    For block models supported by DomainMCF, all three elements of the
    returned tuple will be the same and will correspond to a value in the
    SubblockRatio enum.
    """
    return tuple(
      sub / primary for primary, sub in zip(self.block_size, self.subblock_size)
    ) # type: ignore

  @property
  def supported_subblock_ratio(self) -> SubblockRatio:
    """The rounded ratio of the primary blocks to the subblocks.

    This is the subblock ratio rounded to the closest ratio in the
    SubblockRatio enum. This is the ratio displayed in the
    "Edit Block Model Definition" panel in GeologyCore.
    """
    subblocks_per_parent = tuple(
      primary / sub for primary, sub in zip(self.block_size, self.subblock_size)
    )
    average_size = sum(subblocks_per_parent) / len(subblocks_per_parent)
    minimum_distance = average_size
    closest = SubblockRatio.NO_SUBBLOCKS

    for ratio in SubblockRatio:
      if ratio is SubblockRatio.NO_SUBBLOCKS:
        continue
      distance = np.abs((1 / ratio.value) - average_size)
      if distance < minimum_distance:
        closest = ratio
        minimum_distance = distance
    return closest

  @property
  def block_counts(self) -> tuple[int, int, int]:
    """The block counts in the form (x_count, y_count, z_count).

    Raises
    ------
    RuntimeError
      If this is set before the block sizes.
    """
    return self._definition.block_counts

  @block_counts.setter
  def block_counts(self, new_counts: tuple[int, int, int]):
    self._raise_if_read_only("Set block counts")
    self._definition.set_block_counts(new_counts)

  @property
  def origin(self) -> tuple[float, float, float]:
    """The origin of the block model this defines."""
    return self._definition.origin

  @origin.setter
  def origin(self, new_origin: tuple[float, float, float]):
    self._raise_if_read_only("Set origin")
    self._definition.origin = new_origin

  @property
  def orientation(self) -> tuple[float, float, float]:
    """The rotation of the block model in the form (dip, plunge, bearing).

    This differs from other orientation (and rotation) properties in the SDK
    because the dip, plunge and bearing of a block model definition can be
    between -360 and 360 degrees (inclusive).

    Though this is true to the values which can be stored in a block model
    definition file (.bdf), there are orientation values which are non-equal
    which result in the same rotation (i.e.
    definition_a.orientation != definition_b.orientation does not guarantee
    that their rotations are not the same).
    """
    return self._definition.orientation

  @orientation.setter
  def orientation(self, new_orientation: tuple[float, float, float]):
    self._raise_if_read_only("Set orientation")
    self._definition.orientation = new_orientation

  @property
  def model_extent(self) -> tuple[float, float, float]:
    """The maximum x, y and z values in the model.

    This matches the extent displayed in the "Edit Block Model Definition"
    transaction. This is the block size multiplied by the block count.
    See the extent property for the actual extent of the definition.
    """
    # The block size and counts are both three tuples so we can guarantee
    # this will return a three tuple.
    return tuple(
      size * count for size, count in zip(self.block_size, self.block_counts)
    ) # type: ignore

  def set_block_size(
    self,
    block_size: tuple[float, float, float],
    subblock_ratio: SubblockRatio=SubblockRatio.NO_SUBBLOCKS
  ):
    """Set the size of the blocks and subblocks.

    This only enables setting the subblock sizes to values which are expected
    to work with DomainMCF. The ratio of the block sizes is restricted based
    on the values in the SubblockRatio enum.

    Parameters
    ----------
    block_size
      The size for the primary blocks in the form (x_size, y_size, z_size).
    subblock_ratio
      The ratio of the subblock size to the primary block size.
      This is SubblockRatio.NO_SUBBLOCKS by default, resulting in a dense
      block model.
    """
    self._raise_if_read_only("Set block size")
    if not isinstance(subblock_ratio, SubblockRatio):
      raise TypeError(
        default_type_error_message(
          "subblock_ratio", subblock_ratio, SubblockRatio))
    self._definition.set_regular_block_size(block_size, subblock_ratio.value)

  def variables(self) -> Sequence[Variable]:
    """Get a sequence containing the variables of the block model.

    This returns a new sequence containing new copies of the `Variable`
    objects each time this is called. Old return values become stale
    when variables are added or deleted.
    """
    return tuple(
      self.Variable(variable) for variable in self._definition.variables
    )

  @typing.overload
  def add_variable(
    self,
    name: str,
    data_type: typing.Literal[VariableType.BOOLEAN],
    default: bool | None=None,
    description: str=""
  ):
    ...

  @typing.overload
  def add_variable(
    self,
    name: str,
    data_type: typing.Literal[VariableType.STRING],
    default: str | None=None,
    description: str=""
  ):
    ...

  @typing.overload
  def add_variable(
    self,
    name: str,
    data_type: typing.Literal[VariableType.FLOAT, VariableType.DOUBLE],
    default: float | None=None,
    description: str=""
  ):
    ...

  @typing.overload
  def add_variable(
    self,
    name: str,
    data_type: typing.Literal[
      VariableType.INTEGER, VariableType.SHORT, VariableType.BYTE],
    default: int | None=None,
    description: str=""
  ):
    ...

  @typing.overload
  def add_variable(
    self,
    name: str,
    data_type: VariableType,
    default: str | float | bool | None=None,
    description: str=""
  ):
    ...

  def add_variable(
    self,
    name: str,
    data_type: VariableType,
    default: str | float | bool | None=None,
    description: str=""
  ):
    """Add a new variable to the block model definition.

    Parameters
    ----------
    name
      The name of the variable.
    data_type
      The type of data stored in this variable.
    default
      The default value of the variable represented as a string.
      It is the caller's responsibility to ensure this is a valid default
      value for the data type.
    description
      Short textual description of the variable.

    Raises
    ------
    ValueError
      * If `data_type` is `VariableType.UNKNOWN`.
      * If there is already a variable with `name`.
      * If `default` is not a valid value for `data_type`
    TypeError
      If `default` is a type which cannot be converted to `data_type`.
    """
    if data_type is VariableType.UNKNOWN:
      raise ValueError(
        "Cannot create a variable with an unknown type."
      )
    variables = self._definition.variables
    if any(name == variable["Name"] for variable in variables):
      raise ValueError(
        f"There is already a variable called: {name}"
      )
    python_type = data_type.python_type
    actual_default: str
    if python_type is not type(None):
      actual_default = str(python_type(default)) if default is not None else ""
    else:
      actual_default = ""
    variables.append(
      {
        "Name" : name,
        "Type" : data_type.value,
        "Default" : actual_default,
        "Description" : description
      }
    )

  def remove_variable(self, variable: Variable):
    """Remove `variable` from the definition.

    This does nothing if variable is not in the definition.
    """
    variables = self._definition.variables
    for existing_variable in variables:
      if existing_variable["Name"] == variable.name:
        variables.remove(existing_variable)
        break
