"""Drillhole database data types."""
###############################################################################
#
# (C) Copyright 2022, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import json
import math
import typing

from .desurvey_method import DesurveyMethod
from .drillholes import Drillhole
from .errors import (
  DatabaseLoadError, DuplicateTableTypeError, DesurveyMethodNotSupportedError,
  DuplicateTableNameError)
from .internal.constants import DATABASE_CONSTANTS
from .internal.tables_mixin import TablesMixin
from .tables import (DrillholeTableType, BaseTableInformation,
                     CollarTableInformation, AssayTableInformation,
                     SurveyTableInformation, GeologyTableInformation,
                     QualityTableInformation, DownholeTableInformation,
                     CustomTableInformation)
from ..capi.util import CApiDllLoadFailureError, CApiUnknownError
from ..data.base import StaticType
from ..data.containers import VisualContainer
from ..data.errors import ObjectNotSupportedError
from ..data.objectid import ObjectID
from ..internal.lock import LockType, WriteLock, ObjectClosedError
from ..internal.util import default_type_error_message
from ..overwrite_modes import OverwriteMode

if typing.TYPE_CHECKING:
  from collections.abc import Sequence

  from ..capi import DrillholeModelApi

class DrillholeDatabase(VisualContainer, TablesMixin[BaseTableInformation]):
  """A container which contains Drillhole objects.

  A DrillholeDatabase object is backed by a database. This database may
  be a Vulcan Isis database, a set of CSV files or an internal database.

  New databases created through this interface are always backed by an internal
  database. Upon creation, the new database contains a single
  table (A collar table containing a northing field and an easting field) and
  no drillholes.

  Raises
  ------
  EmptyTableError
    If any table in the database contains no fields.
  DuplicateFieldTypeError
    If any table contains multiple fields of a type which does not support
    duplicates.
  MissingRequiredFieldsError
    If any table does not contain all of its required fields.

  See Also
  --------
  :documentation:`drillholes` : Help page for this class.

  Examples
  --------
  Creating a new drillhole database containing a single drillhole.
  This is a simple example which only uses two tables (A collar table and a
  geology table).

  >>> from mapteksdk.project import Project
  >>> from mapteksdk.data import StringColourMap
  >>> from mapteksdk.geologycore import (
  ...   DrillholeDatabase, DrillholeTableType, DrillholeFieldType)
  >>> with Project() as project:
  ...   # The colour map to use to colour the drillhole.
  ...   with project.new("drillholes/geology_rock_type", StringColourMap
  ...       ) as colour_map:
  ...     colour_map.legend = ["DIRT", "ROCK", "UNOBTAINIUM"]
  ...     colour_map.colours = [
  ...       [165, 42, 42, 255],
  ...       [100, 100, 100, 255],
  ...       [255, 215, 0, 255]
  ...     ]
  ...   with project.new("drillholes/new_database", DrillholeDatabase
  ...       ) as database:
  ...     # The newly created database automatically contains a collar table,
  ...     # so the creator does not need to create one.
  ...     # The collar table only initially contains a northing and an easting
  ...     # field. To be able to more accurately place the drillhole, add an
  ...     # elevation field.
  ...     collar_table = database.collar_table
  ...     collar_table.add_field(
  ...       "ELEVATION",
  ...       float,
  ...       "Elevation of the drillhole",
  ...       field_type=DrillholeFieldType.ELEVATION
  ...     )
  ...     geology_table = database.add_table(
  ...       "GEOLOGY", DrillholeTableType.GEOLOGY)
  ...     # The newly created geology table automatically contains to depth
  ...     # and from depth fields so the creator does not need to create them.
  ...     geology_table.add_field(
  ...       "ROCK_TYPE",
  ...       str,
  ...       "The type of rock in the interval",
  ...       field_type=DrillholeFieldType.ROCK_TYPE)
  ...     # Add a new drillhole to the database.
  ...     drillhole_id= database.new_drillhole("D-1")
  ...   with project.edit(drillhole_id) as drillhole:
  ...     # Set the collar point.
  ...     drillhole.raw_collar = (-0.7, 1.6, -15.6)
  ...     # Populate the geology table.
  ...     geology_table = drillhole.geology_table
  ...     geology_table.add_rows(3)
  ...     geology_table.from_depth.values = [0, 12.3, 25.1]
  ...     geology_table.to_depth.values = [12.3, 25.1, 34.4]
  ...     geology_table.rock_type.values = [
  ...       "DIRT",
  ...       "ROCK",
  ...       "UNOBTAINIUM"]
  ...     drillhole.set_visualisation(geology_table.rock_type,
  ...                                 colour_map)
  """
  def __init__(
      self,
      object_id: ObjectID | None=None,
      lock_type: LockType=LockType.READWRITE):
    is_new = not object_id
    if is_new:
      object_id = self._create_object()

    self._initialise_table_variables()

    super().__init__(object_id, lock_type)

    self.__desurvey_method: DesurveyMethod | None = None
    self.__tangent_length: float | None = None
    self.__tangent_tolerance: float | None = None
    self.__refresh_drillholes: bool = False
    """If the drillholes should be refreshed when this object is saved."""

    if is_new:
      # Add a collar table to the database. This is the minimum amount of
      # tables required for the new database to be 'valid'.
      _ = self.add_table(
        DrillholeTableType.COLLAR.name, DrillholeTableType.COLLAR)

  @classmethod
  def _drillhole_model_api(cls) -> DrillholeModelApi:
    """Access the DrillholeModel C API."""
    return cls._application_api().drillhole_model

  def _create_object(self) -> ObjectID[DrillholeDatabase]:
    try:
      return ObjectID(self._drillhole_model_api().NewInternalDatabase())
    except CApiDllLoadFailureError as error:
      raise ObjectNotSupportedError(
        DrillholeDatabase) from error

  def _to_json_dictionary(self) -> dict:
    """Return a dictionary representing this object.

    This dictionary is formatted to be ready to be serialised to JSON.
    """
    # pylint: disable=protected-access
    database_information = {
      DATABASE_CONSTANTS.VERSION : 1,
      DATABASE_CONSTANTS.TABLES : [
        table._to_json_dictionary() for table in self.tables
      ]
    }

    return database_information

  def _load_desurvey_method(self):
    """Load the desurvey method from the Project.

    This also loads the tangent length and tangent tolerance.
    """
    try:
      desurvey_method_id, tangent_length, tangent_tolerance = \
        self._drillhole_model_api().GetDatabaseDesurveyMethod(self._lock.lock)
      if self.__desurvey_method is None:
        desurvey_method = DesurveyMethod(desurvey_method_id)
        self.__desurvey_method = desurvey_method
      if self.__tangent_length is None:
        self.__tangent_length = tangent_length
      if self.__tangent_tolerance is None:
        self.__tangent_tolerance = tangent_tolerance
    except ValueError:
      # GetDatabaseDesurveyMethod returned a number which doesn't
      # correspond to any known desurvey methods. It could be a new
      # desurvey method.
      self.__desurvey_method = DesurveyMethod.UNKNOWN
      self.__tangent_length = math.nan
      self.__tangent_tolerance = math.nan

  def _save(self):
    # Check all the tables are valid if they are cached.
    if self._tables is not None:
      for table in self.tables:
        # pylint: disable=protected-access
        table._raise_if_invalid()
      self._drillhole_model_api().DatabaseFromJson(
        self._lock.lock, json.dumps(self._to_json_dictionary()))

    # Only save the desurvey method if it is cached and it is not
    # unknown or undefined.
    # It can't be set to unknown and undefined, so if it has those values
    # then they were read from the project so they shouldn't need
    # to be saved.
    if (self.__desurvey_method is not None
        and self.desurvey_method not in (
          DesurveyMethod.UNDEFINED, DesurveyMethod.UNKNOWN)):
      try:
        self._drillhole_model_api().SetDatabaseDesurveyMethod(
          self._lock.lock,
          self.desurvey_method.value,
          self.tangent_length,
          self._tangent_tolerance
        )
      except CApiUnknownError:
        raise DesurveyMethodNotSupportedError(
          "The application does not support the desurvey method: "
          f"{self.desurvey_method.name}"
        ) from None


    if self._data_engine_api().version > (1, 8):
      self._data_engine_api().Checkpoint(self._lock.lock)
    else:
      # Close and reopen the write lock to simulate the behaviour
      # of CheckPoint() (Which is not revealed in the C APIs).
      # This is required so that refresh drillholes will see any changes
      # to the desurvey method.
      self._lock.close()
      self._lock = WriteLock(
        self.id.handle,
        self._data_engine_api(),
        rollback_on_error=self._lock.rollback_on_error) # type: ignore
    if self.__refresh_drillholes:
      self._drillhole_model_api().DatabaseRefreshDrillholes(self._lock.lock)
      self.__refresh_drillholes = False
    super()._save()

  def _record_object_size_telemetry(self):
    # Subtract one from the element count to avoid including the internal
    # database container in the count.
    length = self._data_engine_api().ContainerElementCount(self._lock.lock) - 1
    self._record_size_for("Length", length)

  @classmethod
  def static_type(cls) -> StaticType:
    return cls._drillhole_model_api().DatabaseType()

  def close(self):
    super().close()
    self._unlink()

  @property
  def holes(self) -> Sequence[ObjectID[Drillhole]]:
    """The object IDs of the holes in the database.

    Each time this property is accessed, it provides a copy of the sequence
    of hole IDs. Thus the returned sequence will not be updated when new
    holes are added to the database and must be re-queried.
    """
    # ObjectID.is_a() ensures the returned sequence only contains drillholes.
    # However because it cannot be a TypeGuard, the type checker cannot
    # determine this.
    return [
      drillhole_id for drillhole_id in self.ids()
      if drillhole_id.is_a(Drillhole)
    ] # type: ignore

  @property
  def desurvey_method(self) -> DesurveyMethod:
    """The desurvey method used to generate the visualisation of the drillhole.

    The default desurvey method for a new database is
    DesurveyMethod.TANGENT.

    Notes
    -----
    Setting the desurvey method to DesurveyMethod.TANGENT_WITH_LENGTH
    will set the tangent length to 1.0.

    Example
    -------
    The following example demonstrates setting the desurvey method
    of the drillholes in a picked database to the tangent desurvey method.
    In particular, note that after setting the desurvey method on
    an existing drillhole database you must call refresh_drillholes()
    to update the visualisation of the existing drillholes to use the
    new desurvey method.

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.geologycore import DrillholeDatabase, DesurveyMethod
    >>> from mapteksdk.operations import object_pick
    >>> if __name__ == "__main__":
    ...   with Project() as project:
    ...     drillhole_id = object_pick(
    ...       label="Pick a drillhole in the database to set to use the "
    ...             "tangent desurvey method")
    ...     database_id = drillhole_id.parent
    ...     with project.edit(database_id) as database:
    ...       database: DrillholeDatabase
    ...       database.desurvey_method = DesurveyMethod.TANGENT
    ...       # Refresh the visualisation of existing holes so that they know to
    ...       # use the new desurvey method.
    ...       database.refresh_holes()
    """
    if self.__desurvey_method is None:
      self._load_desurvey_method()
    return self.__desurvey_method # type: ignore

  @desurvey_method.setter
  def desurvey_method(self, new_method: DesurveyMethod):
    if not isinstance(new_method, DesurveyMethod):
      raise TypeError(
        default_type_error_message(
          "desurvey_method", new_method, DesurveyMethod))
    if new_method in (DesurveyMethod.UNKNOWN, DesurveyMethod.UNDEFINED):
      raise ValueError(
        f"Cannot set desurvey method to: '{new_method}'"
      )
    self.__desurvey_method = new_method
    # Though MINIMUM_CURVATURE allows a tangent length, it defaults to a
    # tangent length of NaN to indicate no additional smoothing.
    if self.__desurvey_method == DesurveyMethod.TANGENT_WITH_LENGTH:
      self.__tangent_length = 1.0
    else:
      self.__tangent_length = math.nan

  @property
  def tangent_length(self) -> float:
    """The tangent length used for the tangent with length desurvey method.

    If the desurvey method is not TANGENT_WITH_LENGTH, this will be NaN.
    """
    if not self.desurvey_method.supports_length:
      return math.nan
    if self.__tangent_length is None:
      self._load_desurvey_method()
    return self.__tangent_length # type: ignore

  @tangent_length.setter
  def tangent_length(self, new_length: float):
    if not self.desurvey_method.supports_length:
      raise RuntimeError(
        f"Desurvey method: '{self.desurvey_method}' does not support "
        "tangent length."
      )
    self.__tangent_length = float(new_length)
    self._tangent_tolerance = self.__tangent_length / 0.1

  @property
  def _tangent_tolerance(self) -> float:
    """The tangent tolerance used for the tangent with length desurvey method.

    If the desurvey method is not TANGENT_WITH_LENGTH, this will be NaN.

    Notes
    -----
    This is private because it is hidden in the UI. The transaction
    automatically sets this to one tenth of the tangent length.
    """
    if not self.desurvey_method.supports_length:
      return math.nan
    if self.__tangent_tolerance is None:
      self._load_desurvey_method()
    return self.__tangent_tolerance # type: ignore

  @_tangent_tolerance.setter
  def _tangent_tolerance(self, tangent_tolerance: float):
    self.__tangent_tolerance = float(tangent_tolerance)

  def new_drillhole(
      self,
      drillhole_id: str,
      overwrite: OverwriteMode=OverwriteMode.ERROR
      ) -> ObjectID[Drillhole]:
    """Create a new drillhole and add it to the database.

    The drillhole should be opened using the ObjectID returned by this
    function. The drillhole is inserted into the drillhole database
    container with drillhole_id as its name.

    Opening the new drillhole for reading or editing before closing
    the drillhole database will raise an OrphanDrillholeError.

    Parameters
    ----------
    drillhole_id
      Unique ID for the new drillhole.
    overwrite
      OverwriteMode enum member indicating what behaviour to use if there is
      already a drillhole with the specified name.
      If OverwriteMode.ERROR (default), this will raise a ValueError if there
      is already a drillhole with the specified name.
      If OverwriteMode.UNIQUE_NAME, the drillhole ID will be postfixed with an
      integer to make it unique.
      If OverwriteMode.OVERWRITE, this function will raise a
      NotImplementedError.

    Raises
    ------
    ValueError
      If there is already a drillhole with the specified ID or if
      the drillhole could not be created.
    TypeError
      If drillhole_id is not a str or overwrite is not a member of the
      OverwriteMode enum.
    ReadOnlyError
      If this object is open for read-only.

    Notes
    -----
    If there is an object at the path where the drillhole will be inserted,
    that object will be silently orphaned and the path will now refer
    to the new drillhole.
    """
    self._raise_if_read_only("add drillhole")
    if not isinstance(drillhole_id, str):
      raise TypeError(
        default_type_error_message("drillhole_id", drillhole_id, str))
    if not isinstance(overwrite, OverwriteMode):
      raise TypeError(
        default_type_error_message(
          "overwrite", overwrite, OverwriteMode
        )
      )
    if overwrite is OverwriteMode.OVERWRITE:
      # :TODO: SDK-966 Implement overwriting existing drillholes.
      raise NotImplementedError(
        "Overwriting existing drillholes is not yet implemented."
      )
    self.save()

    # This cannot use _unique_name() because:
    # A: That function is tightly coupled to the DataEngine functions.
    # B: The C API provides no function for checking the existence of a
    # drillhole with the given ID other than returning an error
    # when attempting to add a drillhole with the given ID to the database,
    # which is incompatible with the look-before-you-leap approach taken by
    # _unique_name().
    name_template = f"{drillhole_id} %i"
    i = 2
    name = drillhole_id
    while True:
      try:
        drillhole_handle = self._drillhole_model_api().NewDrillhole(
          self._lock.lock, name)
        return ObjectID(drillhole_handle)
      except ValueError as error:
        # A ValueError indicates there was already a drillhole with the givenn
        # ID.
        if overwrite is OverwriteMode.ERROR:
          raise
        if overwrite is OverwriteMode.UNIQUE_NAME:
          name = name_template % i
          i += 1
          continue
        raise RuntimeError(
          f"Unsupported overwrite mode: {overwrite}"
          ) from error

  @typing.overload
  def add_table(self, table_name: str) -> CustomTableInformation:
    ...

  @typing.overload
  def add_table(
      self,
      table_name: str,
      table_type: typing.Literal[DrillholeTableType.GEOLOGY]
      ) -> GeologyTableInformation:
    ...

  @typing.overload
  def add_table(
      self,
      table_name: str,
      table_type: typing.Literal[DrillholeTableType.ASSAY]
      ) -> AssayTableInformation:
    ...

  @typing.overload
  def add_table(
      self,
      table_name: str,
      table_type: typing.Literal[DrillholeTableType.QUALITY]
      ) -> QualityTableInformation:
    ...

  @typing.overload
  def add_table(
      self,
      table_name: str,
      table_type: typing.Literal[DrillholeTableType.DOWNHOLE]
      ) -> DownholeTableInformation:
    ...

  @typing.overload
  def add_table(
      self,
      table_name: str,
      table_type: typing.Literal[DrillholeTableType.SURVEY]
      ) -> SurveyTableInformation:
    ...

  @typing.overload
  def add_table(
      self,
      table_name: str,
      table_type: typing.Literal[DrillholeTableType.OTHER]
      ) -> CustomTableInformation:
    ...

  # :NOTE: The return type is Never because this raises an error.
  @typing.overload
  def add_table(
      self,
      table_name: str,
      table_type: typing.Literal[DrillholeTableType.COLLAR]
      ) -> typing.Never:
    ...

  @typing.overload
  def add_table(
    self,
    table_name: str,
    table_type: typing.Literal[DrillholeTableType.UNKNOWN]
  ) -> typing.Never:
    ...

  @typing.overload
  def add_table(
      self,
      table_name: str,
      table_type: DrillholeTableType
      ) -> BaseTableInformation:
    ...

  def add_table(
      self,
      table_name: str,
      table_type: DrillholeTableType=DrillholeTableType.OTHER
      ) -> BaseTableInformation:
    """Add a new table to the database.

    The newly created table will contain any fields required by the specified
    table type (For example, to and from depth fields for assay tables).

    Parameters
    ----------
    table_name
      The name for the new table.
    table_type
      The type of the new table. This is DrillholeTableType.OTHER by default.

    Returns
    -------
    BaseTableInformation
      The newly created table.

    Raises
    ------
    ValueError
      If table_type is DrillholeTableType.UNKNOWN.
    TypeError
      If table_type is not part of the DrillholeTableType enum.
    DuplicateTableTypeError
      If attempting to add a second collar or survey table to a database.

    Notes
    -----
    When creating a table which supports TO_DEPTH or FROM_DEPTH fields,
    this function will automatically add both TO_DEPTH and FROM_DEPTH fields to
    the table. Though it is valid for a table to contain only a
    TO_DEPTH field or only a FROM_DEPTH field, it is not possible to create
    such a table through this function.
    """
    self._raise_if_read_only("add a new table")

    # Ensure the existing tables are loaded.
    self._load_tables()

    if table_name in self._tables_by_name:
      raise DuplicateTableNameError(
        table_name=table_name
      )

    if table_type is DrillholeTableType.UNKNOWN:
      raise ValueError(
        f"Creating tables of '{table_type}' is not supported. "
        f"Use '{DrillholeTableType.OTHER}' for non built-in tables.")

    try:
      table_class = self._table_type_to_class()[table_type]
    except KeyError as error:
      raise TypeError(f"Unsupported table type: '{table_type}'.") from error

    # Raise an error if the table type does not support duplicates.
    if (table_type.must_be_unique()
        and len(self.tables_by_type(table_type)) != 0):
      raise DuplicateTableTypeError(table_type)

    table_information = {
      DATABASE_CONSTANTS.NAME : table_name
    }
    table = table_class(table_information)

    # Add the table in Python. This will ensure it is available via
    # fields_by_type, field_by_name.
    self._add_table(table)

    # Add the required fields to the table. This ensures tables always
    # contain their required fields.
    # pylint: disable=protected-access
    table._add_required_fields()
    return table

  def refresh_holes(self):
    """Forces the visualisation of the drillholes to be refreshed.

    The refresh occurs when the database is saved. This should be called when
    an edit to the database design will change how existing drillholes are
    visualised, typically due to field types being changed.

    Warnings
    --------
    This operation can be quite slow on databases with a large number
    of drillholes.
    """
    self.__refresh_drillholes = True

  @property
  def assay_table(self) -> AssayTableInformation:
    return super().assay_table # type: ignore

  @property
  def collar_table(self) -> CollarTableInformation:
    return super().collar_table # type: ignore

  @property
  def survey_table(self) -> SurveyTableInformation:
    return super().survey_table # type: ignore

  @property
  def geology_table(self) -> GeologyTableInformation:
    return super().geology_table # type: ignore

  @property
  def downhole_table(self) -> DownholeTableInformation:
    return super().downhole_table # type: ignore

  @property
  def quality_table(self) -> QualityTableInformation:
    return super().quality_table # type: ignore

  @property
  def tables(self) -> Sequence[BaseTableInformation]:
    return super().tables

  @typing.overload
  def tables_by_type(
    self,
    table_type: typing.Literal[DrillholeTableType.ASSAY]
  ) -> Sequence[AssayTableInformation]:
    ...

  @typing.overload
  def tables_by_type(
    self,
    table_type: typing.Literal[DrillholeTableType.COLLAR]
  ) -> Sequence[CollarTableInformation]:
    ...

  @typing.overload
  def tables_by_type(
    self,
    table_type: typing.Literal[DrillholeTableType.DOWNHOLE]
  ) -> Sequence[DownholeTableInformation]:
    ...

  @typing.overload
  def tables_by_type(
    self,
    table_type: typing.Literal[DrillholeTableType.GEOLOGY]
  ) -> Sequence[GeologyTableInformation]:
    ...

  @typing.overload
  def tables_by_type(
    self,
    table_type: typing.Literal[DrillholeTableType.QUALITY]
  ) -> Sequence[QualityTableInformation]:
    ...

  @typing.overload
  def tables_by_type(
    self,
    table_type: typing.Literal[DrillholeTableType.SURVEY]
  ) -> Sequence[SurveyTableInformation]:
    ...

  @typing.overload
  def tables_by_type(
    self,
    table_type: typing.Literal[DrillholeTableType.OTHER]
  ) -> Sequence[BaseTableInformation]:
    ...

  @typing.overload
  def tables_by_type(
    self,
    table_type: typing.Literal[DrillholeTableType.UNKNOWN]
  ) -> Sequence[BaseTableInformation]:
    ...

  @typing.overload
  def tables_by_type(
    self,
    table_type: DrillholeTableType
  ) -> Sequence[BaseTableInformation]:
    ...

  def tables_by_type(
    self,
    table_type: DrillholeTableType
  ) ->  Sequence[BaseTableInformation]:
    return super().tables_by_type(table_type)

  def _delete_table(self, table: BaseTableInformation):
    """Delete the `table` from the drillhole database.

    It is best not to call this directly. Instead call the `delete()` function
    on the table itself.
    """
    self._raise_if_read_only("delete table")
    if table not in self._tables:
      return
    if table.table_type is DrillholeTableType.COLLAR:
      raise ValueError(
        "You cannot delete the collar table."
      )
    # pylint: disable=protected-access
    for field in table.fields:
      field.delete()
    table._unlink()
    self._tables.remove(table)
    self._tables_by_name.pop(table.name)
    table_type = table.table_type
    tables_with_type = self._tables_by_type[table_type]
    tables_with_type.remove(table)

  def _load_database_information(self) -> str:
    if self.closed:
      raise ObjectClosedError()
    try:
      return self._drillhole_model_api().GetDatabaseInformation(self.id.handle)
    except Exception as error:
      raise DatabaseLoadError(
        f"Failed to read the database for '{self.id.name}'. "
        "It may not be inside a DrillholeDatabase or the drillhole "
        "may have been deleted from the database."
      ) from error

  @classmethod
  def _table_type_to_class(cls) -> dict[
      DrillholeTableType, type[BaseTableInformation]]:
    return {
      DrillholeTableType.ASSAY: AssayTableInformation,
      DrillholeTableType.COLLAR : CollarTableInformation,
      DrillholeTableType.DOWNHOLE : DownholeTableInformation,
      DrillholeTableType.GEOLOGY : GeologyTableInformation,
      DrillholeTableType.QUALITY : QualityTableInformation,
      DrillholeTableType.SURVEY : SurveyTableInformation,
      DrillholeTableType.OTHER : CustomTableInformation
    }

  @classmethod
  def _default_table_type(cls):
    return CustomTableInformation
