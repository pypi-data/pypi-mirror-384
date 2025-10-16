"""Module containing the class and enums representing fields.

Fields are the 'columns' of a table in a drillhole database. Each field stores
data of a particular type for a particular purpose.
"""
###############################################################################
#
# (C) Copyright 2022, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

from collections.abc import Sequence
import enum
import logging
import typing

import numpy as np

from ..data.units import (
  DistanceUnit,
  AngleUnit,
  UnsupportedUnit,
  NO_UNIT,
  NoUnitType,
)
from ..internal.util import default_type_error_message
from ..internal.lock import ObjectClosedError
from .errors import (DataTypeNotSupportedError, FieldTypeNotSupportedError,
                     DeletedFieldError, FieldDoesNotSupportUnitsError,
                     UnitNotSupportedError)
from .internal.constants import FIELD_TYPE_CONSTANTS, DATABASE_CONSTANTS

if typing.TYPE_CHECKING:
  from .tables import BaseTable, BaseTableInformation, BaseDrillholeTable

LOG = logging.getLogger("mapteksdk.geologycore")

UNKNOWN_FIELD_TYPE = "UNKNOWN_FIELD_TYPE"
"""String constant used to represent an unknown field type.

This will cause an error to be raised if it is passed as the dtype
to a numpy function.
"""

class DrillholeFieldType(enum.Enum):
  """Enumeration of supported common field types.

  The field type indicates what the data in the field is intended to represent.
  """
  # :NOTE: This is based off of the string constants defined in:
  # mdf_products/mdf/src/drillholedatabase/api/FieldTypes.C
  # which are used to generate the JSON description of the Database.
  # If a new item is added to that enum and not added here, it will appear
  # as the "UNKNOWN" field type.
  NONE = ""
  """This field stores custom data not covered by another field type."""
  EASTING = "Easting"
  NORTHING = "Northing"
  ELEVATION = "RL"
  TOTAL_DEPTH = "Total depth"
  FROM_DEPTH = "From depth"
  TO_DEPTH = "To depth"
  THICKNESS = "Thickness"
  ROCK_TYPE = "Rock type"
  HORIZON = "Horizon"
  DEPTH = "Depth"
  AZIMUTH = "Azimuth"
  DIP = "Dip"
  UNKNOWN = "?"

  def can_be_repeated(self) -> bool:
    """True if a table can contain multiple fields of this type."""
    if self in (
        DrillholeFieldType.ROCK_TYPE,
        DrillholeFieldType.HORIZON,
        DrillholeFieldType.NONE):
      return True
    return False

  def supports_data_type(self, data_type: np.dtype | type) -> bool:
    """Determine if this field type supports the specified data type.

    Parameters
    ----------
    data_type
      Data type to check if it is supported.

    Returns
    -------
    bool
      True if the data type is supported.
    """
    supports_float_types = {
      DrillholeFieldType.NONE,
      DrillholeFieldType.EASTING,
      DrillholeFieldType.NORTHING,
      DrillholeFieldType.ELEVATION,
      DrillholeFieldType.TOTAL_DEPTH,
      DrillholeFieldType.FROM_DEPTH,
      DrillholeFieldType.TO_DEPTH,
      DrillholeFieldType.THICKNESS,
      DrillholeFieldType.DEPTH,
      DrillholeFieldType.AZIMUTH,
      DrillholeFieldType.DIP
    }

    supports_int_types = {
      DrillholeFieldType.NONE,
      DrillholeFieldType.EASTING,
      DrillholeFieldType.NORTHING,
      DrillholeFieldType.ELEVATION,
      DrillholeFieldType.TOTAL_DEPTH,
    }

    supports_bool_types = {
      DrillholeFieldType.NONE,
    }

    supports_str_types = {
      DrillholeFieldType.NONE,
      DrillholeFieldType.ROCK_TYPE,
      DrillholeFieldType.HORIZON,
    }

    if data_type in (np.float32, np.float64) and self in supports_float_types:
      return True
    if data_type == np.int32 and self in supports_int_types:
      return True
    if data_type == np.bool_ and self in supports_bool_types:
      return True
    if data_type == np.str_ and self in supports_str_types:
      return True

    return False

  @property
  def is_built_in(self) -> bool:
    """If the field is a built in field.

    This will return False for DrillholeFieldType.NONE and True for every
    other field type.
    """
    return self is not DrillholeFieldType.NONE

  @property
  def is_custom(self) -> bool:
    """If the field is a user-defined field.

    This is the inverse of is_built_in.
    """
    return not self.is_built_in

  @property
  def supports_distance_units(self) -> bool:
    """True if this field type supports distance units."""
    field_types_which_support_distance_units: set[DrillholeFieldType] = {
      DrillholeFieldType.EASTING,
      DrillholeFieldType.NORTHING,
      DrillholeFieldType.ELEVATION,
      DrillholeFieldType.TOTAL_DEPTH,
      DrillholeFieldType.TO_DEPTH,
      DrillholeFieldType.FROM_DEPTH,
      DrillholeFieldType.THICKNESS,
      DrillholeFieldType.DEPTH,
      DrillholeFieldType.NONE,
    }

    return self in field_types_which_support_distance_units

  @property
  def supports_angle_units(self) -> bool:
    """True if the field type supports angle units."""
    return self in (
      DrillholeFieldType.AZIMUTH,
      DrillholeFieldType.DIP,
      DrillholeFieldType.NONE,
    )

  @property
  def default_unit(self) -> DistanceUnit | AngleUnit | NoUnitType:
    """The default unit for fields of this type.

    This is NO_UNIT for the OTHER field type, metres for distance fields
    and radians for angle fields.
    """
    if self.is_custom:
      return NO_UNIT
    if self.supports_angle_units:
      return AngleUnit.RADIANS
    if self.supports_distance_units:
      return DistanceUnit.METRE
    return NO_UNIT

def _string_to_dtype(dtype_string: str) -> np.dtype:
  """Converts a string to the appropriate numpy data type.

  This is used to parse a table description from the JSON description read from
  the application.

  Parameters
  ----------
  dtype_string
    String representation of the dtype.

  Returns
  -------
  np.dtype
    Numpy datatype.

  """
  dictionary = {
    FIELD_TYPE_CONSTANTS.BOOLEAN : np.dtype(np.bool_),
    FIELD_TYPE_CONSTANTS.INTEGER_32_S : np.dtype(np.int32),
    FIELD_TYPE_CONSTANTS.FLOAT : np.dtype(np.float32),
    FIELD_TYPE_CONSTANTS.DOUBLE : np.dtype(np.float64),
    FIELD_TYPE_CONSTANTS.STRING : np.dtype(np.str_),
    FIELD_TYPE_CONSTANTS.DATETIME : np.dtype(np.datetime64)
  }

  try:
    return dictionary[dtype_string]
  except KeyError:
    LOG.warning("Encountered unknown data type: %s", dtype_string)
    return np.dtype(object)


def _dtype_to_string(dtype: np.dtype) -> str:
  """Converts a numpy dtype to a string.

  This is used to convert the field description back into a JSON
  serialisable format.

  Parameters
  ----------
  dtype : np.dtype
    The dtype to convert to a string.

  Returns
  -------
  str
    String representation of the dtype to use in JSON.

  """
  if dtype == np.dtype(np.bool_):
    return FIELD_TYPE_CONSTANTS.BOOLEAN
  if dtype == np.dtype(np.int32):
    return FIELD_TYPE_CONSTANTS.INTEGER_32_S
  if dtype == np.dtype(np.float32):
    return FIELD_TYPE_CONSTANTS.FLOAT
  if dtype == np.dtype(np.float64):
    return FIELD_TYPE_CONSTANTS.DOUBLE
  if dtype == np.dtype(np.str_):
    return FIELD_TYPE_CONSTANTS.STRING
  if dtype == np.dtype(np.datetime64):
    return FIELD_TYPE_CONSTANTS.DATETIME
  return ""


class BaseField:
  """Base class containing shared functionality for field objects.

  Parameters
  ----------
  field_information : dict
    The field information used to construct this object. Scripts should
    not construct these objects directly and thus should never need
    to provide this.
  """
  def __init__(self, field_information: dict):
    name = field_information[DATABASE_CONSTANTS.NAME]
    if not isinstance(name, str):
      raise TypeError(default_type_error_message(
        argument_name="name",
        actual_value=name,
        required_type=str
      ))
    self.__name = name

    description = field_information.get(DATABASE_CONSTANTS.DESCRIPTION, "")
    if not isinstance(description, str):
      raise TypeError(default_type_error_message(
        argument_name="description",
        actual_value=name,
        required_type=str))
    self._description = description

    field_type = field_information.get(
      DATABASE_CONSTANTS.FIELD_TYPE, DrillholeFieldType.NONE)
    if not isinstance(field_type, DrillholeFieldType):
      try:
        field_type = DrillholeFieldType(field_type)
      except ValueError:
        field_type = DrillholeFieldType.UNKNOWN
    self._field_type = field_type

    data_type = field_information.get(DATABASE_CONSTANTS.FIELD_DATA_TYPE, "")
    if not isinstance(data_type, np.dtype):
      data_type = _string_to_dtype(data_type)
    self.__data_type = data_type

    unit = field_information.get(DATABASE_CONSTANTS.UNIT, NO_UNIT)
    self._unit = self._determine_unit(unit)

    self.__table = None
    self.__index = None

    # Remember the field information used to construct this object.
    self.__field_information = field_information

  @property
  def name(self) -> str:
    """The name of the field.

    This is a user-provided string. It may differ for equivalent fields
    in different databases.
    """
    return self.__name

  @property
  def field_type(self) -> DrillholeFieldType:
    """The kind of data stored in this field.

    The field type indicates the kind of data stored in this field.
    Fields with the same field type store the same kind of data even if they
    are part of different drillhole databases (though the way that data is
    represented may still vary based on the database conventions, unit
    and data_type of the field).
    """
    return self._field_type

  @property
  def data_type(self) -> np.dtype:
    """The type of the data stored in this field."""
    return self.__data_type

  @property
  def unit(self) -> DistanceUnit | AngleUnit | UnsupportedUnit | NoUnitType:
    """The unit of the data stored in this field.

    This will be a DistanceUnit for the following field types:
    * Easting
    * Northing
    * Elevation
    * Total depth
    * To depth
    * From depth
    * Thickness
    * Depth

    This will be an AngleUnit for the following field types:
    * Azimuth
    * Dip

    If a field has a unit which is neither a DistanceUnit or an AngleUnit,
    it will be represented as an UnsupportedUnit.

    If a field has no unit information at all, this will be NO_UNIT.
    """
    return self._unit

  @property
  def is_numeric(self) -> bool:
    """If the data type is numeric.

    This is True if this field can be used to colour the drillhole using
    a NumericColourMap.
    """
    return self.data_type in (np.float32, np.float64, np.int32)

  @property
  def is_string(self) -> bool:
    """If the data type is a string.

    This is True if this field can be used to colour the drillhole using
    a StringColourMap.
    """
    return self.data_type == np.str_

  @property
  def description(self) -> str:
    """User provided description of the field.

    This can be used to provide additional details on the data stored in
    this field.
    """
    return self._description

  @property
  def _default_unit(self):
    """The default unit for the field."""
    return self.field_type.default_unit

  @property
  def _table(self) -> BaseTable:
    """The table this field is part of.

    Raises
    ------
    ValueError
      If set more than once.
    """
    if self.__table is None:
      raise ObjectClosedError()
    return self.__table

  @_table.setter
  def _table(self, value: BaseTable):
    if self.__table is not None:
      raise ValueError(
        "Table property of a DrillholeDatabaseField can only be set once.")
    self.__table = value

  def _raise_if_read_only(self, operation):
    """Raise a ReadOnlyError if this object is open for read-only.

    Raises
    ------
    ReadOnlyError
      If this object is open for read-only.
    """
    # pylint: disable=protected-access
    self._table._raise_if_read_only(operation)

  @property
  def is_read_only(self) -> bool:
    """True if the field is read-only."""
    return self._table.is_read_only

  def _unlink(self):
    """Removes the field's link to its table.

    This should only be called from the parent table's _unlink()
    function.
    """
    self.__table = None

  @property
  def _index(self) -> int:
    """The index of the field in the table.

    This is used to access this field.
    """
    if self.__index is None:
      raise RuntimeError("This field is not part of a table.")
    return self.__index

  @_index.setter
  def _index(self, value: int):
    if self.__index is not None:
      raise ValueError(
        "_index property of a DrillholeDatabaseField can only be set once.")

    self.__index = value

  def _determine_unit_built_in_field(
      self,
      unit: str | DistanceUnit | AngleUnit | NoUnitType | UnsupportedUnit
      ) -> DistanceUnit | AngleUnit | NoUnitType:
    """Convert the unit to an appropriate type and check it is valid.

    This form of the function handles built-in field types (i.e. All
    field types except for the NONE field type).

    Parameters
    ----------
    unit
      The unit to convert and check.

    Returns
    -------
    DistanceUnit | AngleUnit | NoUnitType
      This will return a distance unit if the field supports distance units,
      an angle unit if the field supports angle units or
      NO_UNIT if the field does not support units

    Raises
    ------
    UnitNotSupportedError
      If unit is not supported by this field.
      * A distance unit was passed to an angle field.
      * An angle unit was passed to a distance field.
      * No unit was passed to a distance or angle field.
    FieldDoesNotSupportUnitsError
      If the field does not support units and unit is not NO_UNIT.
    """
    # A built-in field type either supports distance units, angle units
    # or it doesn't support units.
    if self._field_type.supports_distance_units:
      unit_type = DistanceUnit
    elif self._field_type.supports_angle_units:
      unit_type = AngleUnit
    elif not isinstance(unit, NoUnitType):
      raise FieldDoesNotSupportUnitsError(self.field_type)
    else:
      return unit

    if unit == NO_UNIT:
      # The absence of a unit is how the JSON represents the unknown unit.
      return unit_type.UNKNOWN
    if isinstance(unit, str):
      unit = unit_type._from_serialisation_string(unit)
    if not isinstance(unit, unit_type):
      raise UnitNotSupportedError(self.field_type, unit)
    return unit

  def _determine_unit_custom_field(
      self,
      unit: str | DistanceUnit | AngleUnit | NoUnitType | UnsupportedUnit
      ) -> DistanceUnit | AngleUnit | NoUnitType | UnsupportedUnit:
    """Convert the unit to an appropriate type and check it is valid.

    This form of the function handles custom field types (i.e.
    The NONE field type).

    Parameters
    ----------
    unit
      The unit to convert and check.

    Returns
    -------
    DistanceUnit | AngleUnit | NoUnitType | UnsupportedUnit
      This will return a distance unit if the field supports distance units,
      an angle unit if the field supports angle units,
      NO_UNIT if the field does not support units
      or UnsupportedUnit if the field has a unit not supported by the SDK.

    Raises
    ------
    UnitNotSupportedError
      If unit could not be recognised as a unit type.
    FieldDoesNotSupportUnitsError
      If the field does not support units and unit is not NO_UNIT.
    """
    # Non-numeric custom fields do not support units.
    if not self.is_numeric:
      if unit != NO_UNIT:
        raise FieldDoesNotSupportUnitsError(self.field_type)

    # Custom fields support all distance and angle units.
    if isinstance(unit, (DistanceUnit, AngleUnit)):
      return unit

    # Custom fields are allowed to not have a unit.
    if isinstance(unit, NoUnitType):
      return unit

    if isinstance(unit, str):
      # pylint: disable=protected-access
      distance_unit = DistanceUnit._from_serialisation_string(unit)
      if distance_unit != DistanceUnit.UNKNOWN:
        return distance_unit
      angle_unit = AngleUnit._from_serialisation_string(unit)
      if angle_unit != AngleUnit.UNKNOWN:
        return angle_unit
      return UnsupportedUnit(unit)

    raise UnitNotSupportedError(self.field_type, unit)

  def _determine_unit(
      self,
      unit: str | DistanceUnit | AngleUnit | NoUnitType | UnsupportedUnit | None
      ) -> DistanceUnit | AngleUnit | NoUnitType | UnsupportedUnit:
    """Convert the unit to the correct form and check it is valid.

    Parameters
    ----------
    unit
      The unit to convert and check.
      If None, the default unit for this field will be used.

    Returns
    -------
    DistanceUnit | AngleUnit | NO_UNIT | UnsupportedUnit
      This will return a distance unit if the field supports distance units,
      an angle unit if the field supports angle units,
      NO_UNIT if the field does not support units
      or UnsupportedUnit if the field has a unit not supported by the SDK.

    Raises
    ------
    UnitNotSupportedError
      If unit is not supported by this field.
      * A distance unit was passed to an angle field.
      * An angle unit was passed to a distance field.
      * No unit was passed to a distance or angle field.
    FieldDoesNotSupportUnitsError
      If the field does not support units and unit is not NO_UNIT.
    """
    if unit is None:
      return self._default_unit

    if self.field_type.is_built_in:
      return self._determine_unit_built_in_field(unit)
    return self._determine_unit_custom_field(unit)

  def _to_json_dictionary(self) -> dict:
    """Return a dictionary representing this object.

    The dictionary returned from this function is ready to be serialised
    to JSON.
    """
    # Start with a copy of the field information used to create this object.
    # This ensures that any unsupported items in the field information
    # are propagated unchanged.
    field_information = self.__field_information.copy()

    # Apply any changes to the field information and fill out empty fields.
    field_information[DATABASE_CONSTANTS.NAME] = self.name
    if self.field_type == DrillholeFieldType.UNKNOWN:
      raise RuntimeError("Cannot save a drillhole database containing field "
        f"'{self.name}' of unknown type.")
    field_information[DATABASE_CONSTANTS.FIELD_TYPE] = self.field_type.value
    field_information[DATABASE_CONSTANTS.FIELD_DATA_TYPE] = _dtype_to_string(
      self.data_type)
    field_information[DATABASE_CONSTANTS.DESCRIPTION] = self.description
    # The unit tag isn't written if the field has no unit.
    if not isinstance(self.unit, NoUnitType):
      # pylint: disable=protected-access
      field_information[DATABASE_CONSTANTS.UNIT
        ] = self.unit._to_serialisation_string()
    else:
      # This handles the case where the field had a unit, but the user
      # has removed it by assigning the unit to NO_UNIT.
      field_information.pop(DATABASE_CONSTANTS.UNIT, None)
    field_information[DATABASE_CONSTANTS.VERSION] = 1
    return field_information


class FieldInformation(BaseField):
  """Access metadata of a field.

  This class represents the configuration of the field and cannot be
  used to access any of the values in the database.

  Changes made to this object are made to all of the fields for all of the
  drillholes in the drillhole database.
  """
  _table: BaseTableInformation

  def __init__(self, field_information: dict):
    super().__init__(field_information)
    self.__deleted = False

  @BaseField.description.setter
  def description(self, value: str):
    if self.__deleted:
      raise DeletedFieldError(self)
    self._raise_if_read_only("edit description")
    if not isinstance(value, str):
      raise TypeError(default_type_error_message(
        "description", value, str))
    self._description = value

  @BaseField.field_type.setter
  def field_type(self, value: DrillholeFieldType):
    if self.__deleted:
      raise DeletedFieldError(self)
    self._raise_if_read_only("edit field type")
    if not isinstance(value, DrillholeFieldType):
      raise TypeError(default_type_error_message(
        "field_type", value, DrillholeFieldType))
    if not value.supports_data_type(self.data_type):
      raise DataTypeNotSupportedError(value, self.data_type)
    # Built-in fields require specific units.
    if value is not DrillholeFieldType.NONE:
      if value.supports_angle_units and not isinstance(self.unit, AngleUnit):
        raise UnitNotSupportedError(value, self.unit)
      if value.supports_distance_units and not isinstance(
          self.unit, DistanceUnit):
        raise UnitNotSupportedError(value, self.unit)
    # pylint: disable=protected-access
    if value not in self._table._allowed_field_types():
      raise FieldTypeNotSupportedError(value, self._table.table_type)
    old_field_type = self._field_type
    self._field_type = value

    # Ensure the table is notified of this change.
    # pylint: disable=protected-access
    self._table._notify_field_type_changed(self, old_field_type)

  @BaseField.unit.setter
  def unit(self, value: DistanceUnit | AngleUnit | NoUnitType):
    # Pylint can't follow this code because of the addition of the field_type
    # setter in this class, so disable its warning.
    # pylint: disable=no-member
    if self.__deleted:
      raise DeletedFieldError(self)
    self._raise_if_read_only("edit unit")
    field_type = self.field_type
    # Only numeric fields support units.
    if not self.is_numeric:
      raise FieldDoesNotSupportUnitsError(field_type)
    if isinstance(value, DistanceUnit):
      if not field_type.supports_distance_units:
        raise UnitNotSupportedError(field_type, value)
      # Custom fields don't support the unknown unit.
      if (value == DistanceUnit.UNKNOWN and field_type.is_custom):
        raise UnitNotSupportedError(field_type, value)
    elif isinstance(value, AngleUnit):
      if not field_type.supports_angle_units:
        raise UnitNotSupportedError(field_type, value)
      # Custom fields don't support the unknown unit.
      if value == AngleUnit.UNKNOWN and field_type.is_custom:
        raise UnitNotSupportedError(field_type, value)
    elif value == NO_UNIT:
      if field_type.is_built_in:
        raise UnitNotSupportedError(field_type, value)
    else:
      raise UnitNotSupportedError(field_type, value)

    self._unit = value

  def delete(self):
    """Deletes this field from the database.

    This will not raise an error if the field has already been deleted.

    Warnings
    --------
    Deleting a field will permanently delete all values in that field for all
    drillholes in the database. There is no way to undo this change once
    it is done.
    """
    # pylint: disable=protected-access
    if self.__deleted:
      return
    self._raise_if_read_only("delete field")
    self._table._notify_field_deleted(self)
    self.__deleted = True

# :NOTE: This inherits from typing.Sequence and implements __setitem__ to
# avoid unintended side effects when mutating the sequence.
# e.g. If this did inherit from typing.MutableSequence, then it would
# implement the pop() function. Calling pop on one field would result
# in the removal of the entire last row (not just the value in that field).
# This is a problematic side effect, so this cannot inherit from
# typing.MutableSequence.
class DrillholeDatabaseField(BaseField, Sequence):
  """A field retrieved from a drillhole.

  This allows access to the values of the field for a specific drillhole.
  The number of values stored in a particular field will vary between
  drillholes, but will be the same for all fields in the same drillhole and
  table.
  """
  _table: BaseDrillholeTable

  def __init__(
      self, field_information: dict):
    super().__init__(field_information)
    self.__values = None

  def __getitem__(self, index: int | slice):
    return self.values[index]

  def __setitem__(self, index: int | slice, value: typing.Any):
    self.values[index] = value

  def __len__(self):
    return len(self.values)

  @property
  def _values_cached(self) -> bool:
    return self.__values is not None

  @property
  def values(self) -> np.ma.MaskedArray:
    """Masked numpy array containing the values for this field.

    The array may contain invalid values as indicated by the array mask.
    The type of the data stored in this array is determined by the data_type
    property of this object.

    Raises
    ------
    ValueError
      If attempting to set this property in read-only mode or to an array
      of an incorrect shape.
    NotImplementedError
      If reading data for the data_type of this field is not implemented.

    Notes
    -----
    * This cannot be resized by assigning an array with a different length.
      Call add_rows and remove_rows on the table to add/remove values from
      this array.
    * For string fields, the strings in the array have a fixed length. Assigning
      an array of longer strings to this property will cause a new array
      containing longer strings to be allocated. This invalidates any
      existing references to the values in this array.
    """
    if self.__values is None:
      #pylint: disable=protected-access
      self.__values = self._table._parent._table_values(self._table, self)
    return self.__values

  @values.setter
  def values(
    self,
    new_values : np.ma.MaskedArray | np.ndarray | Sequence | float
  ):
    # This doesn't work for strings because the datatype is dependant on the
    # length of the longest string, so we don't know it until all the strings
    # are loaded.
    if self.__values is None and self.data_type != np.str_:
      # The values array is about to be set to a new array so there is
      # no point in loading it from the database. Instead allocate an
      # appropriately sized and typed array of values. All of the values
      # in this array are masked.
      self.__values = np.ma.masked_all(
        (self._table.row_count,), dtype=self.data_type)
      if self.data_type in (np.float64, np.float32):
        self.__values.fill_value = np.nan
      if self.data_type == np.bool_:
        self.__values.fill_value = False
    # If the data type is a string, this needs to check if the array
    # is large enough to hold the new strings.
    if self.data_type == np.str_:
      # Ensure the new values are a numpy array or a subclass, such
      # as masked array.
      if not isinstance(new_values, np.ndarray):
        new_values = np.ma.MaskedArray(new_values, fill_value="", dtype=np.str_)
      if new_values.dtype.kind == "O":
        # The "O" dtype indicates an array of pointers to Python objects.
        # Convert them to strings.
        new_values = new_values.astype(np.str_)
      if new_values.dtype.kind != "U":
        raise TypeError(f"Cannot convert {new_values.dtype} to np.str_")
      # If the new values item size is larger than the current values item
      # size, then assigning the new strings into the existing array would
      # cause them to be truncated. To avoid this, allocate a new array which
      # contains large enough strings to store the new strings.
      values_item_size = self.values.dtype.itemsize
      new_values_item_size = new_values.dtype.itemsize
      if values_item_size < new_values_item_size:
        self.__values = np.ma.masked_all(
          self._table.row_count, dtype=new_values.dtype)
        self.__values.fill_value = ""
    self.values[:] = new_values

  def _invalidate_properties(self):
    """Invalidates the properties of this field.

    The next time any of the properties are accessed, they will be loaded
    from the database.
    """
    self.__values = None
