"""Module containing classes and enums for representing tables.

A table is a group of fields in a database which store related information.
Common tables have their own subclass which provides additional information
on the fields which are stored in tables of that type.

Note that each hole in a drillhole database has its own copy of each table
defined in the database. Which tables and the fields contained within those
tables are the same for all drillholes within the same database.
"""
###############################################################################
#
# (C) Copyright 2022, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

from collections.abc import (
  Generator,
  MutableMapping,
  MutableSequence,
  Sequence,
  Callable,
)
from contextlib import contextmanager
import enum
from itertools import chain
import logging
import warnings
import typing

import numpy as np
import pandas as pd

from ..data.units import DistanceUnit, AngleUnit, NO_UNIT, NoUnitType
from ..internal.lock import ObjectClosedError
from ..internal.util import default_type_error_message
from .errors import (TooManyFieldsError, TooManyFieldsWarning,
                     FieldNotFoundError, TableMismatchError,
                     FieldTypeNotSupportedError, DuplicateFieldTypeError,
                     DataTypeNotSupportedError, DuplicateFieldNameError,
                     EmptyTableError, MissingRequiredFieldsError,
                     CollarTableRowError, UnitNotSupportedError)
from .fields import (DrillholeFieldType, DrillholeDatabaseField,
                     FieldInformation, BaseField)
from .internal.constants import DATABASE_CONSTANTS

if typing.TYPE_CHECKING:
  from .drillholes import Drillhole
  from .database import DrillholeDatabase
  from .internal.tables_mixin import TablesMixin
  from ..common.typing import Point, PointLike

FieldTypeT = typing.TypeVar("FieldTypeT", bound=BaseField)
"""Generic field type used by tables.

This is used to enable static type checking to determine whether a particular
table comes from a DrillholeDatabase or a Drillhole.

See Also
--------
mapteksdk.geologycore.fields.DrillholeDatabaseField
  The type of fields read from a drillhole database.
mapteksdk.geologycore.fields.FieldInformation
  The type of fields read from a drillhole.
"""

_FieldByTypeDictionary: typing.TypeAlias = MutableMapping[
  DrillholeFieldType, MutableSequence[FieldTypeT]]
"""Dictionary which maps a field type to a list of fields."""

_FieldByNameDictionary: typing.TypeAlias = MutableMapping[str, FieldTypeT]
"""Dictionary which maps names to the corresponding field."""

LOG = logging.getLogger("mapteksdk.geologycore")

class DrillholeTableType(enum.Enum):
  """Enumeration of supported table types."""
  # :NOTE: 2022-04-13 This is based off of the string constants defined in:
  # mdf_products/mdf/src/drillholedatabase/api/TableType.C
  # which are used to generate the JSON description of the Database.
  # If a new item is added to that enum and not added here, it will appear
  # as the "UNKNOWN" table type.
  COLLAR = "Collar"
  GEOLOGY = "Geology"
  ASSAY = "Assay"
  QUALITY = "Quality"
  DOWNHOLE = "Downhole"
  SURVEY = "Survey"
  OTHER = "Other"
  UNKNOWN  = ""

  def must_be_unique(self) -> bool:
    """True if a database can contain multiple tables of this type."""
    if self in (
        DrillholeTableType.ASSAY,
        DrillholeTableType.GEOLOGY,
        DrillholeTableType.QUALITY,
        DrillholeTableType.DOWNHOLE,
        DrillholeTableType.OTHER):
      return False
    return True


class BaseTable(typing.Generic[FieldTypeT]):
  """Base class for tables containing shared functionality.

  This is an abstract base class which should not be instantiated directly.

  Parameters
  ----------
  name
    The name of the table this object represents.
  """
  def __init__(self, table_information: dict):
    name = table_information[DATABASE_CONSTANTS.NAME]
    if not isinstance(name, str):
      raise TypeError(default_type_error_message(
        argument_name="name",
        actual_value=name,
        required_type=str))
    self.__name = name

    # These are set to None when the object is closed.
    self.__parent: TablesMixin[typing.Self] | None = None
    self.__fields: MutableSequence[FieldTypeT] | None = []
    self.__fields_by_type: _FieldByTypeDictionary | None = {
      field_type : [] for field_type in DrillholeFieldType
    }
    self.__fields_by_name: _FieldByNameDictionary | None = {}

    self.__table_information = table_information

  @property
  def name(self) -> str:
    """The table's name.

    This is a user-provided string. It may differ for equivalent tables
    in different databases.
    """
    return self.__name

  @property
  def table_type(self) -> DrillholeTableType:
    """The table's type in the TableType enum."""
    raise NotImplementedError

  @property
  def fields(self) -> Sequence[FieldTypeT]:
    """The fields in this table."""
    return tuple(self._fields)

  @property
  def field_count(self) -> int:
    """The count of fields in the table."""
    return len(self._fields)

  @property
  def custom_fields(self) -> Sequence[FieldTypeT]:
    """Returns a list of custom fields in this table.

    Custom fields are all fields which do not correspond to a field type
    defined in the FieldType enum.
    """
    return self.fields_by_type(DrillholeFieldType.NONE)

  @property
  def _fields(self) -> MutableSequence[FieldTypeT]:
    if self.__fields is None:
      raise ObjectClosedError()
    return self.__fields

  @property
  def _fields_by_type(self) -> _FieldByTypeDictionary[FieldTypeT]:
    if self.__fields_by_type is None:
      raise ObjectClosedError()
    return self.__fields_by_type

  @property
  def _fields_by_name(self) -> _FieldByNameDictionary[FieldTypeT]:
    if self.__fields_by_name is None:
      raise ObjectClosedError()
    return self.__fields_by_name

  @property
  def _parent(self) -> TablesMixin[typing.Self]:
    """The drillhole or drillhole database this table is part of.

    This will be None if the table is not part of a drillhole or drillhole
    database.

    Raises
    ------
    ValueError
      If set more than once.
    TypeError
      If set to an object which is not a Drillhole.
    """
    if self.__parent is None:
      raise ObjectClosedError()
    return self.__parent

  @_parent.setter
  def _parent(self, value: TablesMixin[typing.Self]):
    if self.__parent is not None:
      raise ValueError(
        "A table may only be part of one drillhole or database.")
    self.__parent = value

  def _raise_if_read_only(self, operation):
    """Raise a ReadOnlyError if this object is open for read-only.

    Raises
    ------
    ReadOnlyError
      If this object is open for read-only.
    """
    # pylint: disable=protected-access
    self._parent._raise_if_read_only(operation)

  @property
  def is_read_only(self) -> bool:
    """True if the table is read only."""
    return self._parent.is_read_only

  def fields_by_type(self, field_type: DrillholeFieldType
      ) -> Sequence[FieldTypeT]:
    """Returns a list of fields with the specified field type.

    As of mapteksdk 1.8, this returns a copy of the list.

    Parameters
    ----------
    field_type
      The type of field to return fields for.

    Returns
    -------
    list
      List of fields with the specified field type.

    Raises
    ------
    KeyError
      If field_type is not part of the DrillholeFieldType enum.
    """
    return tuple(self._fields_by_type[field_type])

  def field_by_name(self, name: str) -> FieldTypeT:
    """Returns the field with the specified name.

    Parameters
    ----------
    name
      The name of the field to get

    Returns
    -------
    BaseField
      The field with the specified name.

    Raises
    ------
    FieldNotFoundError
      If there is no field with the specified name.
    """
    try:
      return self._fields_by_name[name]
    except KeyError as error:
      raise FieldNotFoundError(name) from error

  def _field_by_type(
      self, field_type: DrillholeFieldType) -> FieldTypeT:
    """Get a field by type.

    Unlike fields_by_type(), this will raise an error if the field is
    not found.

    Parameters
    ----------
    field_type
      The type of field to return.

    Returns
    -------
    BaseField
      A field with the specified name.

    Raises
    ------
    FieldNotFoundError
      If there is no such field.
    TooManyFieldsError
      If there are multiple fields of the specified type and the field
      does not support duplicates.

    Warnings
    --------
    TooManyFieldsWarning
      If there are multiple fields of the specified type and
      error_multiple_fields=False.
    """
    fields = self.fields_by_type(field_type)
    field_count = len(fields)
    if field_count == 0:
      raise FieldNotFoundError(field_type)
    if field_count > 1:
      if not field_type.can_be_repeated():
        raise TooManyFieldsError(
          field_type, expected_count=1, actual_count=field_count
        )
      warnings.warn(TooManyFieldsWarning(
        field_type, expected_count=1, actual_count=field_count
      ))
    return fields[0]

  def _populate_field(self, field: BaseField, next_index: int):
    """Adds an object representing an existing field to the table.

    This is used to add field objects representing the existing fields
    to this object while it is being created. This updates the
    fields, fields_by_type() and fields_by_name().

    This function only adds the field to the table object. It does not
    add it to the underlying database.

    Parameters
    ----------
    field
      The field to add to this object.
    next_index
      The index to insert the new field at.

    Raises
    ------
    ValueError
      If the field was already added to another table.
    TypeError
      If field is not a supported type.
    """
    raise NotImplementedError(
      "_populate_field must be implemented in child classes.")

  def _unlink(self):
    """Remove the links on this object.

    This unlinks the object from its parent and the fields it contains,
    resolving the circular links which will stop these objects from being
    garbage collected.
    This should only be called from the _unlink() function
    of Drillhole.
    """
    for field in self.fields:
      # pylint: disable=protected-access
      field._unlink()
    self.__parent = None
    self.__fields = None
    self.__fields_by_type = None
    self.__fields_by_name = None

  def _to_json_dictionary(self):
    """Return a dictionary representing this object.

    The dictionary returned from this function is ready to be serialised
    to JSON.
    """
    table_information = self.__table_information.copy()
    table_information[DATABASE_CONSTANTS.TABLE_TYPE] = self.table_type.value
    table_information[DATABASE_CONSTANTS.VERSION] = 1
    field_json = []
    for field in self.fields:
      # pylint: disable=protected-access
      field_json.append(field._to_json_dictionary())
    table_information[DATABASE_CONSTANTS.FIELDS] = field_json
    return table_information


class BaseTableInformation(BaseTable[FieldInformation]):
  """Base class for table information.

  This represents the configuration of a table in a drillhole database.
  This cannot be used to access the values stored in the table, however
  it can be used to add new fields.

  Any changes made to this object will be made to all drillholes in the
  drillhole database.

  Parameters
  ----------
  name
    The name of the table this object represents.
  """
  _parent: DrillholeDatabase
  def __init__(self, table_information: dict):
    super().__init__(table_information)

    for field in table_information.get(DATABASE_CONSTANTS.FIELDS, []):
      field_object = FieldInformation(field)
      # Add the field at the end of the table.
      self._populate_field(field_object, self.field_count)

  def add_field(
      self,
      name: str,
      data_type: type | np.dtype,
      description: str,
      *,
      field_type: DrillholeFieldType=DrillholeFieldType.NONE,
      unit: DistanceUnit | AngleUnit | NoUnitType | None=None,
      index: int | None=None) -> FieldInformation:
    """Add a new field to the table.

    After the database is closed, this new field will be available in all
    drillholes in the drillhole database.

    Parameters
    ----------
    name
      The name for the new field.
    data_type
      The type of data stored in the field. This can be int, float, bool, str
      or a numpy dtype.
    description
      Description for the field.
    field_type
      A keyword only argument to specify the field type to give to the new
      field. This defaults to DrillholeFieldType.None.
    unit
      The unit of the data stored in the field.
      If None (default) the default unit for the field type will be used.
      This is meters for distance fields and radians for angle fields.
    index
      A keyword only argument for specifying the index in the table to insert
      the new field at. By default the new field will be inserted at the
      end of the table.

    Returns
    -------
    FieldInformation
      The newly added field.

    Raises
    ------
    TypeError
      If field_name or description are not strings.
    TypeError
      If data_type is not a valid data type.
    TypeError
      If field_type is not part of the DrillholeFieldType enum.
    ValueError
      If index is not a number or if it is below zero or greater than the number
      of fields.
    DuplicateFieldNameError
      If there is already a field with the specified name.
    FieldTypeNotSupportedError
      If field_type is not supported by table.
    DuplicateFieldTypeError
      If there is already a field with the specified type in the table and
      that field type does not support duplicates.
    DataTypeNotSupportedError
      If data_type is not supported by field_type.
    UnitNotSupportedUnitError
      If unit is not supported by field_type.
    FieldDoesNotSupportUnitsError
      If unit is not None or NO_UNIT for a field which does not support units.
    """
    self._raise_if_read_only("add fields")

    if index is None:
      index = self.field_count
    else:
      index = int(index)

    if not isinstance(name, str):
      raise TypeError(default_type_error_message("field_name", name, str))

    # :TRICKY: This check is only performed at the UI level when adding a
    # field in the application. The database has no issues storing fields with
    # duplicate names, however GeologyCore and the SDK don't support them
    # well.
    if name in self._fields_by_name:
      raise DuplicateFieldNameError(name)

    if not isinstance(description, str):
      raise TypeError(
        default_type_error_message("description", description, str))

    if not isinstance(field_type, DrillholeFieldType):
      raise TypeError(
        default_type_error_message(
          "field_type", field_type, DrillholeFieldType))

    if index < 0 or index > self.field_count:
      raise ValueError(
        "Index for new field is out of bounds. Index must be between "
        f"0 and {self.field_count} (inclusive).")

    # This should also catch the case of FieldType.UNKNOWN because no
    # tables should support it.
    # pylint: disable=protected-access
    if field_type not in self._allowed_field_types():
      raise FieldTypeNotSupportedError(field_type, self.table_type)

    if (len(self.fields_by_type(field_type)) != 0
        and not field_type.can_be_repeated()):
      raise DuplicateFieldTypeError(field_type, self.name)

    # Convert the data type to a numpy data type.
    if data_type is int:
      # Treat int as 32-bit integer. In Numpy 2.0 and later int maps to
      # np.int64 instead and we want it to be 32-bit integer as that is the
      # type that "Integer" maps to in the GeologyCore application.
      dtype = np.dtype(np.int32)
    else:
      # This, for example, allows callers to pass "bool" instead of "np.bool_"
      dtype = np.dtype(data_type)

    # :TRICKY: This check is only performed on the UI level when adding a
    # field in the application. The database has no issue storing fields with
    # unsupported types, however doing so may cause the application to crash.
    if not field_type.supports_data_type(dtype):
      raise DataTypeNotSupportedError(field_type, data_type)

    # Ensure that the unit is one of the types specified in the type hint.
    if (unit != NO_UNIT
        and not isinstance(unit, (DistanceUnit, AngleUnit, type(None)))):
      raise UnitNotSupportedError(field_type, unit)

    field_information = {
      DATABASE_CONSTANTS.NAME : name,
      DATABASE_CONSTANTS.FIELD_DATA_TYPE : dtype,
      DATABASE_CONSTANTS.FIELD_TYPE : field_type,
      DATABASE_CONSTANTS.DESCRIPTION : description,
    }

    # No unit indicates the absence of a unit, so don't include the unit
    # key in that case.
    if unit != NO_UNIT:
      field_information[DATABASE_CONSTANTS.UNIT] = unit
    elif field_type.is_built_in:
      if field_type.supports_angle_units or field_type.supports_distance_units:
        # Built in fields which support angle or distance units require
        # a unit.
        # This is done here, rather than in the FieldInformation constructor
        # because the constructor accepts NO_UNIT as an alias for the unknown
        # unit.
        raise UnitNotSupportedError(field_type, unit)

    new_field = FieldInformation(field_information)

    self._populate_field(new_field, index)
    return new_field

  def delete(self):
    """Delete this table from the drillhole database.

    This will discard all data in this table for all drillholes in the
    database.

    Raises
    ------
    ValueError
      If attempting to delete the collar table.
    """
    # pylint: disable=protected-access
    self._parent._delete_table(self)

  def _populate_field(self, field: FieldInformation, next_index: int):
    if not isinstance(field, FieldInformation):
      raise TypeError(default_type_error_message(
        "field", field, FieldInformation))

    if field.field_type not in self._allowed_field_types():
      LOG.warning("Unexpected field %s of type %s. This field type "
                  "is not expected to be found in table of type %s",
                  field.name,
                  field.field_type.value,
                  self.table_type.value)

    #pylint: disable=protected-access
    field._index = next_index
    field._table = self
    self._fields.insert(next_index, field)
    self._fields_by_type[field.field_type].append(field)
    self._fields_by_name[field.name] = field

  def _notify_field_type_changed(
      self, field: FieldInformation, old_type: DrillholeFieldType):
    """Used by fields to notify the table when their field type changes.

    This enables the table to update its properties corresponding to the
    change.
    """
    # pylint: disable=protected-access
    if field._table is not self:
      raise ValueError("The field was not part of this table.")

    self._fields_by_type[old_type].remove(field)
    self._fields_by_type[field.field_type].append(field)

  def _notify_field_deleted(self, field: FieldInformation):
    """Used by fields to notify the table when they are deleted.

    This enables the table to update its properties corresponding to the
    deletion.
    """
    self._fields_by_type[field.field_type].remove(field)
    self._fields_by_name.pop(field.name, None)
    self._fields.remove(field)

  def _add_required_fields(self):
    """Add the required fields to this table.

    This is called when a new table of this type is added to a drillhole
    database. It should not be called from user code because the table
    should already contain all of its required fields.
    """
    for required_field in self._required_fields():
      self.add_field(
        required_field.name, np.float64, "", field_type=required_field)

  def _raise_if_invalid(self):
    """Raises an error if the table is invalid.

    Raises
    ------
    EmptyTableError
      If the table contains no fields.
    DuplicateFieldTypeError
      If there are multiple fields with the same type for fields which
      do not support duplicates.
    MissingRequiredFieldsError
      If the table does not contain its required fields.
    """
    if self.field_count == 0:
      raise EmptyTableError(self.name)

    # Check for duplicate fields for supported field types which do
    # not support duplicates.
    unrepeatable_field_types = (
      f for f in self._allowed_field_types() if not f.can_be_repeated())
    for field_type in unrepeatable_field_types:
      count = len(self._fields_by_type[field_type])
      if count > 1:
        raise DuplicateFieldTypeError(field_type, self.name)
    self._raise_if_required_fields_missing()

  def _raise_if_required_fields_missing(self):
    """Raises an error if the table does not contain enough required fields.

    If _all_required_fields_required is True, this will raise an error
    if any required field are not in the table.
    If _all_required_fields_required is False, this will only raise
    an error if the table contains none of the required fields.
    """
    missing_fields = []
    for field_type in self._required_fields():
      if len(self.fields_by_type(field_type)) == 0:
        # A required field which is not in the table was found.
        # Add it to the list of missing fields.
        missing_fields.append(field_type)
      elif not self._all_required_fields_required():
        # A required field was found and this table only requires one
        # required field to be valid. Stop the check here.
        return
    if missing_fields:
      raise MissingRequiredFieldsError(
        self, missing_fields, self._all_required_fields_required())

  @classmethod
  def _required_fields(cls) -> tuple[DrillholeFieldType]:
    """Returns a tuple containing the required field types for this table type.

    This must be implemented in base classes.

    Returns
    -------
    tuple
      Tuple containing the types of the required fields for this table.
    """
    raise NotImplementedError

  @classmethod
  def _all_required_fields_required(cls) -> bool:
    """If all of the required fields are required.

    If True, then this class requires all fields listed as required fields.
    If False, then this class only requires one of the required fields.
    """
    raise NotImplementedError

  @classmethod
  def _additional_allowed_field_types(cls) -> tuple[DrillholeFieldType]:
    """Returns a tuple containing additional field types allowed in a subclass.

    This must be implemented by child classes.

    Returns
    -------
    tuple
      Tuple containing additional types allowed in a subclass.
    """
    raise NotImplementedError

  @classmethod
  def _allowed_field_types(cls) -> frozenset[DrillholeFieldType]:
    """Returns a read-only set containing the allowed field types.

    The order of elements in the set is not deterministic.

    This should not be extended in base classes. Instead
    overwrite _additional_allowed_field_types.

    Returns
    -------
    frozenset
      Frozen set containing the types of field allowed in this table.
    """
    return frozenset(chain(
      (DrillholeFieldType.NONE, ),
      cls._additional_allowed_field_types(),
      cls._required_fields(),
    ))


class BaseDrillholeTable(BaseTable[DrillholeDatabaseField]):
  """Base class representing a table in a Drillhole Database.

  Each hole has its own copy of each table in the Database. Each table
  stores a group of related fields. Subclasses define convenience properties
  for accessing fields which are commonly part of this type of table.

  Parameters
  ----------
  name : str
    The name of the table.

  Raises
  ------
  TypeError
    If name is not a string.

  Warnings
  --------
  Users of the SDK should not create subclasses of this class. This class
  is only part of the public API to allow for type hinting.

  """
  _parent: Drillhole
  HOLE_ID = "HOLE_ID"
  """The name of the hole ID column in pandas dataframes."""

  def __init__(self, table_information: dict):
    super().__init__(table_information)
    self.__row_count = None

    for field in table_information.get(DATABASE_CONSTANTS.FIELDS, []):
      field_object = DrillholeDatabaseField(field)
      # Add the field at the end of the table.
      self._populate_field(field_object, self.field_count)

  @property
  def table_type(self) -> DrillholeTableType:
    return super().table_type

  @property
  def row_count(self) -> int:
    """The number of rows in this table."""
    if self.__row_count is None:
      #pylint: disable=protected-access
      self.__row_count = self._parent._drillhole_model_api().GetTableRowCount(
        self._parent._drillhole_information, self.name)
    return self.__row_count

  def add_row(self, *, index: int | None=None):
    """Add a new row to the table.

    Parameters
    ----------
    index
      The index to add the new row at.
      If None (default), add the new row at the end.

    Raises
    ------
    ValueError
      If index is below zero or greater than the row count, or if index
      cannot be converted to an integer.
    CollarTableRowError
      If attempting to add a row to the collar table.

    Warnings
    --------
    This invalidates the properties of the table, requiring them to be
    loaded from the database again.
    """
    self.add_rows(1, index=index)

  def add_rows(self, count: int=1, *, index: int | None=None):
    """Add multiple rows to the table.

    This is more efficient than adding a single row to the table multiple
    times because the properties of the table are only invalidated once.

    Parameters
    ----------
    count
      The number of new rows to add.
    index
      The index of the first new row to add.
      If None (default), add the new rows at the end.

    Raises
    ------
    ValueError
      If index is below zero or greater than the row count, or if index
      cannot be converted to an integer.
    ValueError
      If count is less than one or cannot be converted to an integer.
    CollarTableRowError
      If attempting to add rows to the collar table.

    Warnings
    --------
    This invalidates the properties of the table, requiring them to be
    loaded from the database again.
    """
    self._raise_if_read_only("add rows")
    if index is None:
      index = self.row_count
    else:
      index = int(index)
    count = int(count)

    # This check must be performed on the Python side because it is handled
    # with assertions on the C++ side.
    if index < 0 or index > self.row_count:
      raise ValueError(
        f"Invalid index for new row: {index}. New index must be between "
        f"0 and {self.row_count}")

    if count < 1:
      raise ValueError(
        f"Invalid count: {count}. Count must be greater than one.")

    # pylint: disable=protected-access
    self._parent._drillhole_model_api().AddRows(
      self._parent._drillhole_information,
      self.name,
      index,
      count)

    self._invalidate_properties()

  def remove_row(self, index: int):
    """Remove the specified row from the table.

    Parameters
    ----------
    index
      Index of the row to remove.

    Raises
    ------
    ValueError
      If index cannot be converted to an integer.
    IndexError
      If there is no row with the specified index.
    CollarTableRowError
      If attempting to remove a row from the collar table.

    Warnings
    --------
    This invalidates the properties of the table, requiring them to be
    loaded from the database again.
    """
    self.remove_rows(index, 1)

  def remove_rows(self, index: int, count: int):
    """Remove count rows starting at index.

    Parameters
    ----------
    index
      Index of the row to remove.
    count
      The number of rows to remove.

    Raises
    ------
    ValueError
      If index cannot be converted to an integer.
    ValueError
      If count cannot be converted to an integer.
    IndexError
      If one or more rows to delete do not exist.
    CollarTableRowError
      If attempting to remove rows from the collar table.

    Warnings
    --------
    This invalidates the properties of the table, requiring them to be
    loaded from the database again.
    """
    self._raise_if_read_only("remove rows")
    index = int(index)
    count = int(count)

    if count < 0:
      raise ValueError(
        f"Invalid count: {count}. Count must be greater than zero.")

    # Subtract 1 from count because start index is included in the count
    # of rows to remove.
    end_index = index + (count - 1)
    if index < 0 or index >= self.row_count:
      raise IndexError(
        f"Cannot delete row {index} because it does not exist "
        f"(The table contains {self.row_count} rows).")
    if end_index < 0 or end_index >= self.row_count:
      raise IndexError(
        f"Cannot delete {count} rows starting at index {index} because "
        "one of more indices refer to rows which do not exist "
        f"(The table contains {self.row_count} rows).")

    # pylint: disable=protected-access
    self._parent._drillhole_model_api().RemoveRows(
      self._parent._drillhole_information,
      self.name,
      index,
      count)

    self._invalidate_properties()

  @contextmanager
  def dataframe(self, *,
      fields: Sequence[DrillholeDatabaseField] | None=None,
      include_hole_id: bool=True,
      save_changes: bool=False
      ) -> Generator[pd.DataFrame, None, None]:
    """Context manager for a pandas dataframe representing this table.

    Each field of the table becomes a column of the dataframe. The column
    name is the field name and the column contains the values of that
    field.

    Parameters
    ----------
    fields
      A list of fields to include in the dataframe. Only fields in the list
      will be included in the dataframe.
      If None (Default), the dataframe will include all fields in the table.
      Filtering out fields which will not be used will reduce the memory
      and time required to construct and perform operations on the dataframe.
    include_hole_id
      If True (Default) the hole id column will be included in the dataframe.
      This column will have the name BaseDrillholeTable.HOLE_ID and it will have
      a unique value for each drillhole in the underlying database.
      This allows for dataframes of the same table from different holes in the
      same database to be safely concatenated.
      If False, the hole id column will not be included.
    save_changes
      If False (default) any changes to the dataframe will not be
      propagated to the table.
      If True, and the object is open for reading, changes to the
      dataframe will be propagated to the table.

    Yields
    ------
    pd.DataFrame
      Dataframe representing the table.

    Raises
    ------
    TypeError
      If any item in fields is not a DrillholeDatabaseField.
    ReadOnlyError
      If save_changes is True when the object is open for reading.
    TableMismatchError
      If fields includes a field which is not part of this table.

    Examples
    --------
    Calculating the length of each interval in a table based on the
    to and from depth fields.

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.geologycore import Drillhole
    >>> project = Project()
    >>> with project.read("path/to/drillhole") as drillhole:
    ...   drillhole: Drillhole
    ...   geology_table = drillhole.geology_table
    ...   to_depth_name = geology_table.to_depth.name
    ...   from_depth_name = geology_table.from_depth.name
    ...   with geology_table.dataframe() as frame:
    ...     # The dataframe is indexed via field name. Use the field name
    ...     # queried earlier.
    ...     length = frame[to_depth_name] - frame[from_depth_name]
    ...     print(length)

    The above script only uses the to depth and from depth fields, however
    the dataframe includes all of the fields in the table. If the table has a
    large number of rows or fields, this can be very inefficient. The
    performance of the operation can be improved by filtering out the fields
    which are not needed as shown in the below version of the same
    script.

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.geologycore import Drillhole
    >>> project = Project()
    >>> with project.read("path/to/drillhole") as drillhole:
    ...   drillhole: Drillhole
    ...   geology_table = drillhole.geology_table
    ...   to_depth = geology_table.to_depth
    ...   from_depth = geology_table.from_depth
    ...   with geology_table.dataframe(fields=(to_depth, from_depth)) as frame:
    ...     length = frame[to_depth.name] - frame[from_depth.name]
    ...     print(length)

    Setting the save_changes flag to True causes the changes to the
    dataframe to be written back to the Drillhole when the with block
    ends. To make full usage of this, make sure that all operations
    on the dataframe are performed in-place. The following script
    uses this to sort the geology table of the picked drillhole by
    from depth and then removes duplicate rows.

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.geologycore import Drillhole
    >>> from mapteksdk.operations import object_pick
    >>> if __name__ == "__main__":
    ...   with Project() as project:
    ...     oid = object_pick(
    ...       label="Pick a drillhole to sort and drop duplicates.")
    ...     with project.edit(oid, Drillhole) as drillhole:
    ...       geology_table = drillhole.geology_table
    ...       with geology_table.dataframe(
    ...           save_changes=True, include_hole_id=False
    ...           ) as frame:
    ...         frame.sort_values(by="FROM_DEPTH", inplace=True)
    ...         frame.drop_duplicates(inplace=True)
    """
    if save_changes:
      self._raise_if_read_only("edit dataframe")
    if fields is None:
      fields = self.fields
    frame = self._get_pandas(fields, include_hole_id)
    try:
      yield frame
    finally:
      if save_changes and not self.is_read_only:
        LOG.info(
          "Write pandas dataframe changes to table %s of drillhole %s",
          self.name,
          self._parent.name)
        self._put_pandas(frame)
      else:
        LOG.info(
          "Read-only finished with dataframe for table %s of drillhole %s",
          self.name,
          self._parent.name)

  def _invalidate_properties(self):
    """Invalidates the properties of the table and its field.

    The next time these values are accessed they will be reloaded from
    the database.
    """
    self.__row_count = None
    for field in self.fields:
      # pylint: disable=protected-access
      field._invalidate_properties()

  def _populate_field(self, field: DrillholeDatabaseField, next_index: int):
    if not isinstance(field, DrillholeDatabaseField):
      raise TypeError(default_type_error_message(
        "field", field, DrillholeDatabaseField))

    #pylint: disable=protected-access
    field._index = next_index
    field._table = self
    self._fields.append(field)
    self._fields_by_type[field.field_type].append(field)
    self._fields_by_name[field.name] = field

  def _get_pandas(self,
      fields: Sequence[DrillholeDatabaseField],
      include_hole_id: bool
      ) -> pd.DataFrame:
    """Get a pandas dataframe representing this table.

    By default this includes all the fields in the table. The column
    names are the field names.

    Parameters
    ----------
    fields
      A list of fields to include in the dataframe. Only fields in the list
      will be included in the dataframe.
      Filtering out fields which will not be used will reduce the memory
      and time required to construct and operate on the dataframe.
    include_hole_id
      If the hole id column should be included in the dataframe.

    Returns
    -------
    pandas.DataFrame
      Dataframe representing this table.

    Raises
    ------
    TypeError
      If any item in fields is not a DrillholeDatabaseField.
    TableMismatchError
      If fields includes a field which is not part of this table.
    """
    frame_dictionary = {}

    # pylint: disable=try-except-raise
    for field in fields:
      try:
        # pylint: disable=protected-access
        if field._table is not self:
          raise TableMismatchError(field, self)
        frame_dictionary[field.name] = field.values
      except NotImplementedError:
        # Skip fields which are not implemented.
        LOG.warning(
          ("Skipping field: %s of type %s because reading fields of that type "
           "is not implemented."),
          field.name, field.data_type.name)
      except AttributeError:
        # The field was the wrong type.
        raise TypeError(default_type_error_message(
          "field", field, DrillholeDatabaseField)) from None
      except TableMismatchError:
        # Ensure the TableMismatchError is not caught here.
        raise

    frame = pd.DataFrame(frame_dictionary)

    if include_hole_id:
      #pylint: disable=protected-access
      frame.insert(0, BaseDrillholeTable.HOLE_ID, self._parent._hole_id)

    return frame

  def _put_pandas(self, frame: pd.DataFrame):
    """Set the values in this table using a pandas dataframe.

    This is intended to be used with _get_pandas.

    Parameters
    ----------
    frame
      Dataframe to use to set the fields. The column names of the frame
      should match column names for the table.
    """
    current_row_count = self.row_count
    new_row_count = frame.shape[0]
    if current_row_count > new_row_count:
      rows_to_delete = current_row_count - new_row_count
      self.remove_rows(self.row_count - rows_to_delete, rows_to_delete)
    elif current_row_count < new_row_count:
      rows_to_add = new_row_count - current_row_count
      self.add_rows(rows_to_add)
    for field in self.fields:
      try:
        new_values = frame[field.name].values

        # Mask any value which is NaN or the empty string.
        # :NOTE: Pandas stores string arrays as arrays of pointers to
        # Python objects. This allows them to use NaN to indicate missing
        # values, just like for numeric arrays.
        mask = pd.isnull(new_values)
        if field.data_type == np.str_:
          empty_strings = new_values == ""
          mask[empty_strings] = True
        masked_new_values = np.ma.masked_array(
          new_values, mask=mask, dtype=field.data_type)
        field.values = masked_new_values
      except KeyError:
        continue

class _TableWithDepthFieldsMixin(typing.Generic[FieldTypeT]):
  """Mixin which provides to_depth, from_depth and thickness fields."""
  # Properties expected to be provided by the inherited class:
  _field_by_type: Callable[[DrillholeFieldType], FieldTypeT]

  # Properties provided by the Mixin:
  @property
  def from_depth(self) -> FieldTypeT:
    """The from depth field of a hole.

    A value in this field represents the distance down the hole the interval
    the row represents starts down the hole.

    Typically from_depth is coupled with the to_depth field to provide
    a depth range for an interval.

    Raises
    ------
    FieldNotFoundError
      If there is no from depth field.
    TooManyFieldsError
      If there are multiple from fields in the table. This should
      not be possible. If this error is thrown, the database was invalid.

    Warnings
    --------
    It is possible for intervals in this property to be out of order or
    overlap.

    Notes
    -----
    from_depth can be used on its own to define intervals. For example, given
    a from_depth field with values [A, B, C, D] then the first row represents
    the depth range [A, B), the second row represents the depth range [B, C),
    the third row represents the depth range [C, D) and the fourth row
    represents the depth range [D, total_depth).
    """
    return self._field_by_type(DrillholeFieldType.FROM_DEPTH)

  @property
  def to_depth(self) -> FieldTypeT:
    """The to depth field of the hole.

    A value in this field represents the distance down the hole the interval
    the row represents ends at.

    Typically to_depth is coupled with the from_depth field to provide
    a depth range for a interval.

    Raises
    ------
    FieldNotFoundError
      If there is no to depth field.
    TooManyFieldsError
      If there are multiple to depth fields in the table. This should
      not be possible. If this error is thrown, the database was invalid.

    Warnings
    --------
    It is possible for intervals in this property to be out of order or
    overlap.

    Notes
    -----
    to_depth can be used on its own to define intervals. For example, given
    a to_depth field with values [A, B, C, D] then the first row represents
    a depth range of [0, A), the second row represents a depth range of
    [A, B), the third row represents a depth range of [B, C) and the
    fourth row represents the depth range [C, D).
    """
    return self._field_by_type(DrillholeFieldType.TO_DEPTH)

  @property
  def thickness(self) -> FieldTypeT:
    """Field representing the thickness of the hole in each interval.

    Raises
    ------
    FieldNotFoundError
      If there is no thickness field.
    TooManyFieldsError
      If there are multiple thickness fields in the table. This should
      not be possible. If this error is thrown, the database was invalid.
    """
    return self._field_by_type(DrillholeFieldType.THICKNESS)

class _TableWithAzimuthDipMixin(typing.Generic[FieldTypeT]):
  """Mixin which provides azimuth and depth fields"""
  # Properties expected to be provided by the inherited class:
  _field_by_type: Callable[[DrillholeFieldType], FieldTypeT]

  # Properties provided by the Mixin:

  @property
  def azimuth(self) -> FieldTypeT:
    """Field representing the azimuth of the drillhole.

    Raises
    ------
    FieldNotFoundError
      If there is no azimuth field.
    TooManyFieldsError
      If there are multiple azimuth fields in the table. This should
      not be possible. If this error is thrown, the database was invalid.
    """
    return self._field_by_type(DrillholeFieldType.AZIMUTH)

  @property
  def dip(self) -> FieldTypeT:
    """Field representing the dip angle of the drillhole.

    Raises
    ------
    FieldNotFoundError
      If there is no dip field.
    TooManyFieldsError
      If there are multiple dip fields in the table. This should
      not be possible. If this error is thrown, the database was invalid.
    """
    return self._field_by_type(DrillholeFieldType.DIP)

class _CollarTableMixin(_TableWithAzimuthDipMixin[FieldTypeT]):
  """Mixin which adds properties for accessing common fields in collar tables.
  """

  @property
  def easting(self) -> FieldTypeT:
    """Field representing the easting of a drillhole.

    In a default project, this corresponds to the x coordinate of the drillhole.
    Changes to the easting field will be propagated to the collar point
    of the drillhole when save() is called.

    Raises
    ------
    FieldNotFoundError
      If there is no easting field.
    TooManyFieldsError
      If there are multiple easting fields in the table. This should
      not be possible. If this error is thrown, the database was invalid.
    """
    return self._field_by_type(DrillholeFieldType.EASTING)

  @property
  def northing(self) -> FieldTypeT:
    """Field representing the northing of a drillhole.

    In a default project, this corresponds to the y coordinate of the drillhole.
    Changes to the northing field will be propagated to the collar point
    of the drillhole when save() is called.

    Raises
    ------
    FieldNotFoundError
      If there is no easting field.
    TooManyFieldsError
      If there are multiple easting fields in the table. This should
      not be possible. If this error is thrown, the database was invalid.
    """
    return self._field_by_type(DrillholeFieldType.NORTHING)

  @property
  def elevation(self) -> FieldTypeT:
    """Field representing the elevation of a drillhole.

    In a default project, this corresponds to the z coordinate of the drillhole.
    Changes to the elevation field will be propagated to the collar point
    of the drillhole when save() is called.

    Raises
    ------
    FieldNotFoundError
      If there is no elevation field.
    TooManyFieldsError
      If there are multiple elevation fields in the table. This should
      not be possible. If this error is thrown, the database was invalid.
    """
    return self._field_by_type(DrillholeFieldType.ELEVATION)

  @property
  def total_depth(self) -> FieldTypeT:
    """The total depth of the drillhole.

    If any table has to_depth or from_depth fields, they should not contain
    values which exceed the total_depth of the drillhole.

    Raises
    ------
    FieldNotFoundError
      If there is no total depth field.
    TooManyFieldsError
      If there are multiple total depth fields in the table. This should
      not be possible. If this error is thrown, the database was invalid.
    """
    return self._field_by_type(DrillholeFieldType.TOTAL_DEPTH)


class _SurveyTableMixin(_TableWithAzimuthDipMixin[FieldTypeT]):
  """Mixin which adds properties for accessing common fields in survey tables.
  """

  @property
  def depth(self) -> FieldTypeT:
    """The depth values for the table.

    This indicates the depth each azimuth and dip measurement were taken at.

    Raises
    ------
    FieldNotFoundError
      If there is no depth field.
    TooManyFieldsError
      If there are multiple depth fields in the table. This should
      not be possible. If this error is thrown, the database was invalid.
    """
    return self._field_by_type(DrillholeFieldType.DEPTH)


class _GeologyTableMixin(_TableWithDepthFieldsMixin[FieldTypeT]):
  """Mixin which adds properties for accessing common fields in geology tables.
  """

  @property
  def rock_type(self) -> FieldTypeT:
    """The rock type field.

    This indicates the type of rock in each interval defined by the
    to_depth and/or from_depth.

    A table may contain multiple rock type fields. This property should only
    be used if you are certain that the table only contains one rock type
    field.

    Raises
    ------
    FieldNotFoundError
      If there is no rock type field.

    Warns
    -----
    TooManyFieldsWarning
      If the table contains multiple rock type fields. The first field
      was returned.
    """
    return self._field_by_type(DrillholeFieldType.ROCK_TYPE)

  @property
  def horizon(self) -> FieldTypeT:
    """The horizon field.

    A table may contain multiple horizon fields. This property should only
    be used if you are certain that the table only contains one horizon
    field.

    Raises
    ------
    FieldNotFoundError
      If there is no horizon field.

    Warns
    -----
    TooManyFieldsWarning
      If the table contains multiple horizon fields. The first field
      was returned.
    """
    return self._field_by_type(DrillholeFieldType.HORIZON)


class CollarTable(
  BaseDrillholeTable,
  _CollarTableMixin[DrillholeDatabaseField],
):
  """Table containing information on the collar of the drillhole.

  The collar is the point on the surface where the drillhole was taken.

  Notes
  -----
  The collar table should only have a single row in it and thus a single value
  for each field.
  """
  @property
  def table_type(self):
    return DrillholeTableType.COLLAR

  @property
  def collar_point(self) -> Point:
    """The collar point of the drillhole as specified by this table.

    This property handles missing elevation values. This reads the x, y and
    z coordinate straight from the table and does not consider coordinate
    systems.

    If the collar table does not contain an elevation field, the z component
    of the collar point will be zero.

    Raises
    ------
    TableNotFoundError
      If there is no collar table.
    TooManyTablesError
      If there are multiple collar tables in the database.

    Warns
    -----
    RuntimeWarning
      If the table contains no elevation field and the collar is set to
      a point containing a non-zero z ordinate.
    """
    # This explicitly sets the ordinate to NaN if it is masked to avoid
    # numpy raising a warning about converting 'masked' to NaN.
    easting_values = self.easting.values
    try:
      x = np.nan if easting_values.mask[0] else easting_values[0]
    except IndexError:
      x = np.nan

    northing_values = self.northing.values
    try:
      y = np.nan if northing_values.mask[0] else northing_values[0]
    except IndexError:
      y = np.nan

    try:
      elevation_values = self.elevation.values
      z = np.nan if elevation_values.mask[0] else elevation_values[0]
    except IndexError:
      z = np.nan
    except FieldNotFoundError:
      # If there is no elevation field, the z component of the collar point
      # is always considered to be zero.
      z = 0

    return np.array((x, y, z), dtype=float)

  @collar_point.setter
  def collar_point(self, value: PointLike):
    self.easting.values[0] = value[0]
    self.northing.values[0] = value[1]
    try:
      self.elevation.values[0] = value[2]
    except IndexError:
      # The input value only contained two elements. Ignore this error
      # so that the caller only needs to provide two floats if there is
      # no elevation field.
      pass
    except FieldNotFoundError:
      if value[2]:
        warnings.warn(
          "Ignoring z component of collar point because the database "
          "does not contain an elevation field.",
          RuntimeWarning)

  def add_rows(self, count: int = 1, *, index: int | None = None):
    raise CollarTableRowError()

  def remove_rows(self, index: int, count: int):
    raise CollarTableRowError()


class SurveyTable(
  BaseDrillholeTable,
  _SurveyTableMixin[DrillholeDatabaseField],
):
  """Table containing survey information for a drillhole.

  Changes to the depth and azimuth fields will be propagated to the points
  used to visualise the drillhole when save() is called.
  """
  @property
  def table_type(self):
    return DrillholeTableType.SURVEY


class GeologyTable(
  BaseDrillholeTable,
  _GeologyTableMixin[DrillholeDatabaseField],
):
  """Table containing geology information for a drillhole."""
  @property
  def table_type(self):
    return DrillholeTableType.GEOLOGY


class AssayTable(
  BaseDrillholeTable,
  _TableWithDepthFieldsMixin[DrillholeDatabaseField],
):
  """Table containing assay information for a drillhole."""
  @property
  def table_type(self):
    return DrillholeTableType.ASSAY


class DownholeTable(
  BaseDrillholeTable,
  _TableWithDepthFieldsMixin[DrillholeDatabaseField],
):
  """Table containing downhole information for a drillhole."""
  @property
  def table_type(self):
    return DrillholeTableType.DOWNHOLE


class QualityTable(
  BaseDrillholeTable,
  _TableWithDepthFieldsMixin[DrillholeDatabaseField],
):
  """Table containing quality information for a drillhole."""
  @property
  def table_type(self):
    return DrillholeTableType.QUALITY


class CustomTable(BaseDrillholeTable):
  """Table containing non-standard information for a drillhole.

  Custom tables have no restrictions on the type and kind of data
  which is stored in them. All fields in custom tables are of type
  DrillholeFieldType.NONE and thus the values must be retrieved by name.
  """
  @property
  def table_type(self):
    return DrillholeTableType.OTHER


class CollarTableInformation(
  BaseTableInformation,
  _CollarTableMixin[FieldInformation],
):
  """The configuration of the collar table.

  A collar table is required to have the following fields:

  * DrillholeFieldType.EASTING
  * DrillholeFieldType.NORTHING

  A collar table may also include fields of the following types:

  * DrillholeFieldType.ELEVATION
  * DrillholeFieldType.TOTAL_DEPTH
  * DrillholeFieldType.AZIMUTH
  * DrillholeFieldType.DIP
  * DrillholeFieldType.NONE
  """
  @property
  def table_type(self):
    return DrillholeTableType.COLLAR

  @classmethod
  def _required_fields(cls):
    return (
      DrillholeFieldType.EASTING,
      DrillholeFieldType.NORTHING,
    )

  @classmethod
  def _all_required_fields_required(cls) -> bool:
    # This table requires all of the required fields to be present.
    return True

  @classmethod
  def _additional_allowed_field_types(cls):
    return (
      DrillholeFieldType.ELEVATION,
      DrillholeFieldType.TOTAL_DEPTH,
      DrillholeFieldType.AZIMUTH,
      DrillholeFieldType.DIP,
    )

class SurveyTableInformation(
  BaseTableInformation,
  _SurveyTableMixin[FieldInformation],
):
  """The configuration of the survey table.

  A survey table is required to include the following fields:

  * DrillholeFieldType.DEPTH
  * DrillholeFieldType.AZIMUTH
  * DrillholeFieldType.DIP

  A survey table may also include fields of the following types:

  * DrillholeFieldType.NONE
  """
  @property
  def table_type(self):
    return DrillholeTableType.SURVEY

  @classmethod
  def _required_fields(cls):
    return (
      DrillholeFieldType.AZIMUTH,
      DrillholeFieldType.DEPTH,
      DrillholeFieldType.DIP,
    )

  @classmethod
  def _all_required_fields_required(cls) -> bool:
    # This table requires all of the required fields to be present.
    return True

  @classmethod
  def _additional_allowed_field_types(cls):
    return tuple()


class GeologyTableInformation(
  BaseTableInformation,
  _GeologyTableMixin[FieldInformation],
):
  """The configuration of a geology table.

  A geology table must contain one field of the following type:
  * DrillholeFieldType.FROM_DEPTH
  * DrillholeFieldType.TO_DEPTH

  Typically a geology table will contain both, however it is possible
  for it to only contain one. A geology table may also include fields
  of the following types:

  * DrillholeFieldType.THICKNESS
  * DrillholeFieldType.ROCK_TYPE
  * DrillholeFieldType.HORIZON
  * DrillholeFieldType.NONE
  """
  @property
  def table_type(self):
    return DrillholeTableType.GEOLOGY

  @classmethod
  def _required_fields(cls):
    return (
      DrillholeFieldType.FROM_DEPTH,
      DrillholeFieldType.TO_DEPTH,
    )

  @classmethod
  def _all_required_fields_required(cls) -> bool:
    # This table only requires one of the required fields.
    return False

  @classmethod
  def _additional_allowed_field_types(cls):
    return (
      DrillholeFieldType.THICKNESS,
      DrillholeFieldType.ROCK_TYPE,
      DrillholeFieldType.HORIZON,
    )


class AssayTableInformation(
  BaseTableInformation,
  _TableWithDepthFieldsMixin[FieldInformation],
):
  """The configuration of a assay table.

  An assay table must contain one field of the following type:
  * DrillholeFieldType.FROM_DEPTH
  * DrillholeFieldType.TO_DEPTH

  Typically an assay table will contain both, however it is possible
  for it to only contain one. An assay table may also include fields
  of the following types:

  * DrillholeFieldType.THICKNESS
  * DrillholeFieldType.NONE
  """
  @property
  def table_type(self):
    return DrillholeTableType.ASSAY

  @classmethod
  def _required_fields(cls):
    return (
      DrillholeFieldType.FROM_DEPTH,
      DrillholeFieldType.TO_DEPTH,
    )

  @classmethod
  def _all_required_fields_required(cls) -> bool:
    # This table only requires one of the required fields.
    return False

  @classmethod
  def _additional_allowed_field_types(cls):
    return (
      DrillholeFieldType.THICKNESS,
    )


class DownholeTableInformation(
    BaseTableInformation, _TableWithDepthFieldsMixin[FieldInformation]):
  """The configuration of a downhole table.

  A downhole table must contain one field of the following type:
  * DrillholeFieldType.FROM_DEPTH
  * DrillholeFieldType.TO_DEPTH

  Typically a downhole table will contain both, however it is possible
  for it to only contain one. A downhole table may also include fields
  of the following types:

  * DrillholeFieldType.THICKNESS
  * DrillholeFieldType.NONE
  """
  @property
  def table_type(self):
    return DrillholeTableType.DOWNHOLE

  @classmethod
  def _required_fields(cls):
    return (
      DrillholeFieldType.FROM_DEPTH,
      DrillholeFieldType.TO_DEPTH,
    )

  @classmethod
  def _all_required_fields_required(cls) -> bool:
    # This table only requires one of the required fields.
    return False

  @classmethod
  def _additional_allowed_field_types(cls):
    return (
      DrillholeFieldType.THICKNESS,
    )


class QualityTableInformation(
  BaseTableInformation,
  _TableWithDepthFieldsMixin[FieldInformation],
):
  """The configuration of a quality table.

  An quality table must contain one field of the following type:
  * DrillholeFieldType.FROM_DEPTH
  * DrillholeFieldType.TO_DEPTH

  Typically a quality table will contain both, however it is possible
  for it to only contain one. A quality table may also include fields
  of the following types:

  * DrillholeFieldType.THICKNESS
  * DrillholeFieldType.NONE
  """
  @property
  def table_type(self):
    return DrillholeTableType.QUALITY

  @classmethod
  def _required_fields(cls):
    return (
      DrillholeFieldType.FROM_DEPTH,
      DrillholeFieldType.TO_DEPTH,
    )

  @classmethod
  def _all_required_fields_required(cls) -> bool:
    # This table only requires one of the required fields.
    return False

  @classmethod
  def _additional_allowed_field_types(cls):
    return (
      DrillholeFieldType.THICKNESS,
    )


class CustomTableInformation(BaseTableInformation):
  """The configuration of a custom (user-defined) table.

  Custom tables have no restrictions on the type and kind of data
  which is stored in them. They have no required fields and only support
  fields of type DrillholeFieldType.NONE.

  Note that because these tables are custom, applications do not have
  any built-in support for interpreting or operating on the data stored in
  these tables.
  """
  @property
  def table_type(self):
    return DrillholeTableType.OTHER

  @classmethod
  def _required_fields(cls):
    return tuple()

  @classmethod
  def _all_required_fields_required(cls) -> bool:
    return False

  @classmethod
  def _additional_allowed_field_types(cls):
    return tuple()
