"""Internal implementation details for the geologycore module.

Warnings
--------
Vendors and clients should not develop scripts or applications against
this module. The contents may change at any time without warning.
"""
###############################################################################
#
# (C) Copyright 2022, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

from collections.abc import (
  MutableSequence,
  Sequence,
  MutableMapping,
  Callable,
)
import json
import logging
import typing
import warnings

from .constants import DATABASE_CONSTANTS
from ..errors import (TableNotFoundError, TooManyTablesError,
                     TooManyTablesWarning, DatabaseLoadError,
                     DatabaseVersionNotSupportedError)
from ..tables import DrillholeTableType, BaseTable

if typing.TYPE_CHECKING:
  from ...data import ObjectID

TableTypeT = typing.TypeVar("TableTypeT", bound=BaseTable)
"""Generic field type used by tables.

This is used to enable static type checking to determine whether a particular
table comes from a DrillholeDatabase or a Drillhole.
"""

_TablesByTypeDictionary: typing.TypeAlias = MutableMapping[
  DrillholeTableType, MutableSequence[TableTypeT]]
"""A dictionary which enables looking up tables via type."""

_TablesByNameDictionary: typing.TypeAlias = MutableMapping[
  str, TableTypeT]
"""A dictionary which enables looking up tables via name."""

_TableConstructor: typing.TypeAlias = Callable[[dict], TableTypeT]
"""Constructor for a table of the specified type."""

LOG = logging.getLogger("mapteksdk.geologycore")

class TablesMixin(typing.Generic[TableTypeT]):
  """Mixin class which adds functionality for keeping track of tables.

  This is intended to be used by Drillhole and DrillholeDatabase to
  allow for shared functionality for accessing tables.
  """
  # Properties the inheriting class should provide:
  # This is in a type checking block so that these implementations cannot be
  # used at runtime.
  if typing.TYPE_CHECKING:
    @property
    def id(self) -> ObjectID[typing.Any]:
      raise NotImplementedError

    @property
    def is_read_only(self) -> bool:
      raise NotImplementedError

    def _raise_if_read_only(self, operation: str):
      raise NotImplementedError

  # Properties provided by the mixin:
  def _initialise_table_variables(self):
    """Initialise the variables required for keeping track of tables.

    This should be called in the inheriting class's __init__() method.
    """
    self.__tables: MutableSequence[TableTypeT] | None = None
    self.__tables_by_type: _TablesByTypeDictionary[TableTypeT] = {
      table_type : [] for table_type in DrillholeTableType
    }
    self.__tables_by_name: _TablesByNameDictionary[TableTypeT] = {}

  @property
  def _tables(self) -> MutableSequence[TableTypeT]:
    """Internal access the tables of this object."""
    if self.__tables is None:
      self._load_tables()
      tables = self.__tables
      if tables is None:
        LOG.warning("Failed to load tables for drillhole database.")
      return tables or []
    return self.__tables

  @property
  def _tables_by_type(self) -> _TablesByTypeDictionary[TableTypeT]:
    """Internal access to the tables by type."""
    if not self._tables_cached:
      # Load the tables to populate the dictionary before returning it.
      self._load_tables()
    return self.__tables_by_type

  @property
  def _tables_by_name(self) -> _TablesByNameDictionary[TableTypeT]:
    """Internal access to the tables by name"""
    if not self._tables_cached:
      # Load the tables to populate the dictionary before returning it.
      self._load_tables()
    return self.__tables_by_name

  @property
  def _tables_cached(self):
    """True if the tables are cached, False otherwise."""
    return self.__tables is not None

  @property
  def assay_table(self) -> TableTypeT:
    """Returns the assay table if it exists.

    This property should only be used if the caller is certain that the database
    only contains one assay table.

    Raises
    ------
    TableNotFoundError
      If there is no assay table.

    Warns
    -----
    TooManyTablesWarning
      If the database contains multiple assay tables. The first table
      was returned.
    """
    return self._table_by_type(
      DrillholeTableType.ASSAY, error_multiple_tables=False)

  @property
  def collar_table(self) -> TableTypeT:
    """Returns the collar table if it exists.

    The collar table represents the location on the surface which the
    drillhole was taken from.

    A database can only have one collar table.

    Raises
    ------
    TableNotFoundError
      If there is no collar table.
    TooManyTablesError
      If there are multiple collar tables in the database. This should not
      be possible.
    """
    return self._table_by_type(
      DrillholeTableType.COLLAR, error_multiple_tables=True)

  @property
  def survey_table(self) -> TableTypeT:
    """Returns the survey table if it exists.

    A database can only contain one survey table.

    Raises
    ------
    TableNotFoundError
      If there is no survey table.
    TooManyTablesError
      If there are multiple survey tables in the database. This should not
      be possible.
    """
    return self._table_by_type(
      DrillholeTableType.SURVEY, error_multiple_tables=True)

  @property
  def geology_table(self) -> TableTypeT:
    """Returns the geology table if it exists.

    A database may contain multiple geology tables. This property should
    only be used if the caller is certain that the database only contains
    one geology table.

    Raises
    ------
    TableNotFoundError
      If there is no geology table.

    Warns
    -----
    TooManyTablesWarning
      If the database contains multiple geology tables. The first table
      was returned.
    """
    return self._table_by_type(
      DrillholeTableType.GEOLOGY, error_multiple_tables=False)

  @property
  def downhole_table(self) -> TableTypeT:
    """Returns the downhole table if it exists.

    A database may contain multiple downhole tables. This property should
    only be used if the caller is certain that the database only contains
    one downhole table.

    Raises
    ------
    TableNotFoundError
      If there is no geology table.

    Warns
    -----
    TooManyTablesWarning
      If the database contains multiple geology tables. The first table
      was returned.
    """
    return self._table_by_type(
      DrillholeTableType.DOWNHOLE, error_multiple_tables=False)

  @property
  def quality_table(self) -> TableTypeT:
    """Returns the quality table if it exists.

    A database may contain multiple quality tables. This property should
    only be used if the caller is certain that the database only contains
    one quality table.

    Raises
    ------
    TableNotFoundError
      If there is no geology table.

    Warns
    -----
    TooManyTablesWarning
      If the database contains multiple geology tables. The first table
      was returned.
    """
    return self._table_by_type(
      DrillholeTableType.QUALITY, error_multiple_tables=False)

  @property
  def tables(self) -> Sequence[TableTypeT]:
    """The tables representing the drillhole.

    Returns
    -------
    list
      List of BaseDrillholeTable for the drillhole.
    """
    return tuple(self._tables)

  @property
  def table_count(self) -> int:
    """The number of tables in the database."""
    return len(self._tables)

  def tables_by_type(
    self,
    table_type: DrillholeTableType
  ) -> Sequence[TableTypeT]:
    """Returns a list of tables with the specified type.

    Parameters
    ----------
    table_type
      The type of table to include in the list.

    Returns
    -------
    Sequence[BaseTable]
      List of BaseDrillholeTable objects with the specified table type.

    Raises
    ------
    KeyError
      If table_type is not a DrillholeTableType.
    """
    return tuple(self._tables_by_type[table_type])

  def table_by_name(self, name: str) -> TableTypeT:
    """Returns the table with the specified name.

    Parameters
    ----------
    name
      The name of the table to return.

    Returns
    -------
    BaseDrillholeTable
      The table with the specified name.

    Raises
    ------
    TableNotFoundError
      If there is no table with the specified name.
    """
    try:
      return self._tables_by_name[name]
    except KeyError as error:
      raise TableNotFoundError(name) from error

  def _table_by_type(
      self, table_type: DrillholeTableType, error_multiple_tables: bool=False
      ) -> TableTypeT:
    """Get a table by type.

    Unlike tables_by_type(), this will raise an error if the table is
    not found.

    Parameters
    ----------
    table_type
      The type of table to return.
    error_multiple_tables
      If True, raise an error if there are multiple tables with the specified
      type. If False (Default), a warning is raised instead.

    Raises
    ------
    TableNotFoundError
      If there is no such table.
    TooManyTablesError
      If there are multiple tables of the specified type and
      error_multiple_tables=True.

    Warnings
    --------
    TooManyTablesWarning
      If there are multiple tables of the specified type and
      error_multiple_tables=False.
    """
    tables = self.tables_by_type(table_type)
    table_count = len(tables)
    if table_count == 0:
      raise TableNotFoundError(table_type.value)
    if table_count > 1:
      if error_multiple_tables:
        raise TooManyTablesError(
          table_type, expected_count=1, actual_count=table_count
        )
      warnings.warn(TooManyTablesWarning(
        table_type, expected_count=1, actual_count=table_count
      ))
    return tables[0]

  def _add_table(self, table: TableTypeT):
    """Add a BaseDrillholeTable object to this object's list of tables.

    This is used to populate the existing tables when this object is
    constructed. This cannot be used to add new tables.

    Parameters
    ----------
    table
      The table to add to this object.

    Raises
    ------
    ValueError
      If the table has been added to another table.
    TypeError
      If the table is not a BaseDrillholeTable object.
    """
    #pylint: disable=protected-access
    table._parent = self
    self._tables.append(table)
    self._tables_by_type[table.table_type].append(table)
    self._tables_by_name[table.name] = table

  def _load_database_information(self) -> str:
    """Returns a JSON string containing the table information.

    This should be a raw JSON string. It should not have been parsed
    with the JSON library.

    This must be implemented by child classes.

    Returns
    -------
    str
      JSON string containing the table information.
    """
    raise NotImplementedError

  def _unlink(self):
    """Unlink the object from its tables and fields.

    This breaks all of the cyclic dependencies between the drillhole
    and its tables and fields which should allow for these objects to
    be garbage collected.
    """
    # Don't attempt to unlink from the tables if they are not cached because
    # that would load them only to immediately garbage collect them.
    if self._tables_cached:
      for table in self.tables:
        # pylint: disable=protected-access
        table._unlink()
      self._initialise_table_variables()

  @classmethod
  def _table_type_to_class(cls) -> dict[
      DrillholeTableType, _TableConstructor[TableTypeT]]:
    """Dictionary of table types to table types.

    This must be implemented in child classes. This determines the table
    class which will be instantiated to represent tables of each table
    type.
    """
    raise NotImplementedError

  @classmethod
  def _default_table_type(cls) -> _TableConstructor[TableTypeT]:
    """Default table class for if the type is not in _table_type_to_class().

    This must be defined on child classes.
    """
    raise NotImplementedError

  def _load_table(self, table_json: dict) -> TableTypeT:
    """Load a table as the appropriate type from JSON.

    This will instantiate the table object as the appropriate BaseTable
    subclass as defined by _table_type_to_class().

    Parameters
    ----------
    table_json : dict
      Parsed JSON dictionary representing the table, including all of its
      fields.

    Returns
    -------
    BaseTable
      An appropriate subclass of BaseTable which represents the table.
    """
    try:
      table_type = DrillholeTableType(table_json[DATABASE_CONSTANTS.TABLE_TYPE])
    except KeyError:
      LOG.warning("Failed to identify the type of a table.")
      table_type = DrillholeTableType.UNKNOWN
    except ValueError:
      LOG.warning("Detected unknown table type: %s",
                  table_json[DATABASE_CONSTANTS.TABLE_TYPE])
      table_type = DrillholeTableType.UNKNOWN

    table_class = self._table_type_to_class().get(
      table_type, self._default_table_type())

    return table_class(table_json,)

  def _load_tables(self):
    """Loads the tables.

    This populates tables, tables_by_type and table_by_name. Subclasses can
    call this to trigger loading the tables.
    """
    # The tables have already been loaded.
    if self.__tables is not None:
      return

    json_string = self._load_database_information()
    self.__tables = []

    try:
      table_information = json.loads(json_string)
    except json.JSONDecodeError as error:
      raise DatabaseLoadError(
        f"Failed to read the database for '{self.id.name}'. "
        "The description could not be parsed. The database may be corrupt."
        ) from error

    version = table_information[DATABASE_CONSTANTS.VERSION]
    if version != 1:
      raise DatabaseVersionNotSupportedError(
        expected_version=1,
        current_version=version)

    for table_json in table_information.get(DATABASE_CONSTANTS.TABLES, []):
      drillhole_table = self._load_table(table_json)
      self._add_table(drillhole_table)
