"""Special errors raised in this module."""
###############################################################################
#
# (C) Copyright 2022, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

from __future__ import annotations
import typing

if typing.TYPE_CHECKING:
  import numpy as np

  from .fields import DrillholeFieldType, BaseField, FieldInformation
  from .tables import DrillholeTableType, BaseTable, BaseTableInformation

class DatabaseVersionNotSupportedError(Exception):
  """Error raised when opening a drillhole database which is too new.

  Drillhole database objects have an internal version. This error is raised
  if this version indicates that the Python SDK does not know how to read
  the database.

  Parameters
  ----------
  expected_version
    The expected database version.
  current_version
    The actual database version.
  """
  def __init__(self, expected_version: int, current_version: int):
    self.expected_version = expected_version
    self.current_version = current_version
    Exception.__init__(
      self,
      f"Database version is too new to be read by the SDK. Database version: "
      f"{current_version} (Supported version: {expected_version})")


class DatabaseLoadError(Exception):
  """Error raised if the SDK fails to read a drillhole database"""


class OrphanDrillholeError(Exception):
  """Exception raised when attempting to read an orphaned drillhole.

  Alternatively, a drillhole is considered orphaned between when it is
  created and when the database which contains it is closed.

  Parameters
  ----------
  drillhole_id
    The id of the orphaned drillhole.
  """
  def __init__(self, drillhole_id: str):
    self.drillhole_id = drillhole_id
    Exception.__init__(
      self,
      f"The drillhole '{drillhole_id}' is not part of a drillhole database. "
      "It may have been removed from its database container. "
      "(If it is a new drillhole, you must close the drillhole database before "
      "opening the drillhole).")


class TableNotFoundError(Exception):
  """Error raised when a table could not be found.

  Parameters
  ----------
  table
    The name or type of the table which was not found.
  """
  def __init__(self, table: str | DrillholeTableType):
    self.table = table
    Exception.__init__(
      self,
      f"Failed to find the '{table}' table.")


class TooManyTablesError(Exception):
  """Error raised when multiple tables were found.

  Parameters
  ----------
  table_type
    The type of the table.
  expected_count
    The expected number of tables with the specified type.
  actual_count
    The actual number of tables with the specified type.
  """
  def __init__(
      self,
      table_type: DrillholeTableType,
      expected_count: int,
      actual_count: int):
    self.table_type = table_type
    self.expected_count = expected_count
    self.actual_count = actual_count
    Exception.__init__(
      self,
      f"Too many {table_type} tables were found. "
      f"Expected: {expected_count}, Found: {actual_count}."
      "The correct table may not have been used.")


class TooManyTablesWarning(Warning):
  """Warning given when too many tables were found.

  Parameters
  ----------
  table_type
    String representation of the table type which triggered the warning.
  expected_count
    The expected number of tables.
  actual_count
    The actual number of tables.
  """
  def __init__(
      self,
      table_type: DrillholeTableType,
      expected_count: int,
      actual_count: int):
    self.table_type = table_type
    self.expected_count = expected_count
    self.actual_count = actual_count
    Warning.__init__(
      self,
      f"Too many {table_type} tables were found. "
      f"Expected: {expected_count}, Found: {actual_count}. "
      "The correct table may not have been used.")


class FieldNotFoundError(Exception):
  """Error raised when a field could not be found.

  Parameters
  ----------
  field
    The name or type of the field which was not found.
  """
  def __init__(self, field: str | DrillholeFieldType):
    self.field = field
    Exception.__init__(
      self,
      f"Failed to find the '{field}' field.")


class TooManyFieldsError(Exception):
  """Error raised when multiple fields were found.

  Parameters
  ----------
  field_type
    String representation of the field type which triggered the error.
  expected_count
    The expected number of fields.
  actual_count
    The actual number of fields.
  """
  def __init__(
      self, field_type: str | DrillholeFieldType,
      expected_count: int,
      actual_count: int):
    self.field_type = field_type
    self.expected_count = expected_count
    self.actual_count = actual_count
    Exception.__init__(
      self,
      f"Too many {field_type} fields were found. "
      f"Expected: {expected_count}, Found: {actual_count}."
      "The correct field may not have been used.")


class TooManyFieldsWarning(Warning):
  """Warning given when too many fields were found.

  Parameters
  ----------
  field_type
    String representation of the field type which triggered the warning.
  expected_count
    The expected number of fields.
  actual_count
    The actual number of fields.
  """
  def __init__(
      self,
      field_type: str | DrillholeFieldType,
      expected_count: int,
      actual_count: int):
    self.field_type = field_type
    self.expected_count = expected_count
    Warning.__init__(
      self,
      f"Too many {field_type} fields were found. "
      f"Expected: {expected_count}, Found: {actual_count}."
      "The correct field may not have been used.")


class TableMismatchError(Exception):
  """Error raised when attempting to use a field from a different table.

  Parameters
  ----------
  field
    The field which is mismatched.
  table
    The table the field should have been part of.
  """
  def __init__(self, field: BaseField, expected_table: BaseTable):
    # No type hint because it would introduce a circular dependency.
    self.field = field
    self.expected_table = expected_table
    field_name = field.name
    field_table_name = field._table.name
    expected_table_name = expected_table.name
    Exception.__init__(
      self,
      f"Field: '{field_name}' of table: '{field_table_name}' is not part of "
      f"table: '{expected_table_name}'"
    )


class FieldTypeNotSupportedError(Exception):
  """Error raised when attempting to add an unsupported field to a table.

  Parameters
  ----------
  field_type
    The unsupported field type.
  table_type
    The type of table which does not support the field type.
  """
  def __init__(
      self, field_type: DrillholeFieldType, table_type: DrillholeTableType):
    self.field_type = field_type
    self.table_type = table_type
    super().__init__(
      f"Adding a field of type '{field_type}' to a table of type "
      f"'{table_type}' is not supported.")


class DataTypeNotSupportedError(Exception):
  """Error raised when attempting to add a field with an unsupported data type.

  Parameters
  ----------
  field_type
    The unsupported field type.
  data_type
    The type of data which is not supported.
  """
  def __init__(
    self,
    field_type: DrillholeFieldType,
    data_type: type | np.dtype
  ):
    self.field_type = field_type
    self.data_type = data_type
    super().__init__(
      f"Fields of type '{field_type}' do not support values of type: "
      f"'{data_type}'")


class UnitNotSupportedError(Exception):
  """Error raised when a unit is not supported."""
  def __init__(self, field_type: DrillholeFieldType, unit: typing.Any):
    self.field_type = field_type
    self.unit = unit
    super().__init__(
      f"Fields of type '{field_type}' do not support unit: '{unit}'")


class FieldDoesNotSupportUnitsError(Exception):
  """Error raised when a field does not support units.

  This indicates that the data stored in the field has no unit, but the caller
  attempted to give the field a unit.
  """
  def __init__(self, field_type: DrillholeFieldType):
    self.field_type = field_type
    super().__init__(
      f"Fields of type '{field_type}' do not support units.")


class DuplicateFieldTypeError(Exception):
  """Error raised when adding a field which already exists to a table.

  Parameters
  ----------
  field_type
    The type of field which has been duplicated.
  table_name
    The name of the table the field was intended to be added to.
  """
  def __init__(self, field_type: DrillholeFieldType, table_name: str):
    self.field_type = field_type
    self.table_name = table_name
    super().__init__(
      f"The table '{table_name}' already contains a field of "
      f"type '{field_type}'"
    )


class DuplicateFieldNameError(Exception):
  """Error raised when adding a field with the same name as an existing field.

  Parameters
  ----------
  field_name
    The name of the duplicate field.
  """
  def __init__(self, field_name: str):
    self.field_name = field_name
    super().__init__(
      f"The table already contains a field with name: {field_name}"
    )


class EmptyTableError(Exception):
  """Error raised when a table with no fields is saved.

  Parameters
  ----------
  table_name
    The name of the table with no fields.
  """
  def __init__(self, table_name: str):
    self.table_name = table_name
    super().__init__(f"Table '{table_name}' did not contain any fields.")


class MissingRequiredFieldsError(Exception):
  """Error raised when a table does not contain sufficient required fields.

  Parameters
  ----------
  table
    The name which is missing fields.
  missing_fields
    List of required field types which are missing.
  all_fields_required
    If True, then all required fields are required to make the table valid.
    If False, then only one of the required fields is needed to make the table
    valid.
  """
  def __init__(
      self,
      table: BaseTableInformation,
      missing_fields: list[DrillholeFieldType],
      all_fields_required: bool):
    self.table = table
    self.field_types = missing_fields
    field_type_values = [f.name for f in missing_fields]
    message = (f"Table '{table.name}' (Type: '{table.table_type.name}') does"
      " not contain all required fields."
    )
    if all_fields_required:
      message += (
        f" It must contain fields of the following types: {field_type_values}")
    else:
      message += (
        " It must contain at least one field from the "
        f"following types: {field_type_values}")
    super().__init__(message)


class DuplicateTableTypeError(Exception):
  """Error raised when adding a duplicate table.

  This is raised when attempting to add a second collar or survey table
  to a drillhole database. Those table types do not support duplicates.

  Parameters
  ----------
  table_type
    The type of the duplicate table.
  """
  def __init__(self, table_type: DrillholeTableType):
    self.table_type = table_type
    super().__init__(
      f"Cannot add table of type: '{table_type}'. A table with that type "
      "already exists in the database.")


class DuplicateTableNameError(Exception):
  """Error raised when adding a table with the same name as an existing table.

  Parameters
  ----------
  table_name
    The name of the duplicate table.
  """
  def __init__(self, table_name: str) -> None:
    super().__init__(
      f"There is already a table called: '{table_name}'")
    self.table_name = table_name


class DeletedFieldError(Exception):
  """Error raised when attempting to use a field after it has been deleted."""
  def __init__(self, field: FieldInformation):
    self.field = field
    super().__init__(
      f"The '{field.name}' field has been deleted.")


class CollarTableRowError(Exception):
  """Error raised when attempting to add/remove rows from the collar table."""
  def __init__(self):
    super().__init__(
      "Cannot add or remove rows from the collar table."
    )


class SurveyTableLoadedError(Exception):
  """Exception raised when the survey table is loaded.

  This is raised when there may be unsaved changes to the survey table
  which would cause a function to return incorrect values.
  """


class DesurveyMethodNotSupportedError(Exception):
  """Exception raised when the desurvey method is not supported.

  This indicates the application does not support this desurvey method.
  """
