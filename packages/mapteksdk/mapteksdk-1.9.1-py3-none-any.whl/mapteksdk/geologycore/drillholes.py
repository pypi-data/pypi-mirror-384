"""Drillhole data types."""
###############################################################################
#
# (C) Copyright 2022, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import ctypes
import logging
import typing

import numpy as np

from .errors import (
  DatabaseLoadError, OrphanDrillholeError, SurveyTableLoadedError)
from .fields import DrillholeDatabaseField
from .internal.tables_mixin import TablesMixin
from .tables import (DrillholeTableType, AssayTable, CollarTable, SurveyTable,
                     GeologyTable, DownholeTable, QualityTable, CustomTable,
                     BaseDrillholeTable)
from ..capi import DrillholeModelApi
from ..data.base import Topology, StaticType
from ..data.colourmaps import NumericColourMap, StringColourMap, ColourMap
from ..data.objectid import ObjectID
from ..internal.data_property import DataProperty, DataPropertyConfiguration
from ..internal.lock import LockType, ObjectClosedError
from ..internal.util import default_type_error_message

if typing.TYPE_CHECKING:
  from collections.abc import Sequence

  from ..capi.drillholemodel import S_DrillholeInformation
  from ..common.typing import Point, PointLike


LOG = logging.getLogger("mapteksdk.geologycore")

# :NOTE: Drillhole inherits from EdgeNetwork on the C++ side, however it does
# not support all the operations available on EdgeNetwork so it inherits from
# Topology here.
class Drillhole(Topology, TablesMixin[BaseDrillholeTable]):
  """Class representing a single drillhole.

  Drillholes cannot be created with Project.new() like other objects.
  Instead they are created through DrillholeDatabase.new_drillhole().
  An error will be raised if you open the new drillhole before closing
  the drillhole database.

  Notes
  -----
  Though the values representing a Drillhole are accessed through this object,
  they are actually stored in the DrillholeDatabase which the Drillhole is
  inside.

  Drillholes in the same database will have the same tables and fields.

  Raises
  ------
  TypeError
    If passed to Project.new().
  OrphanDrillholeError
    If the drillhole is not inside of a drillhole database container.
    This error will also be raised if a new drillhole is opened before
    the drillhole database is closed.

  See Also
  --------
  mapteksdk.geologycore.database.DrillholeDatabase.new_drillhole :
    Create new drillholes.
  :documentation:`drillholes` : Help page for this class.
  """
  def __init__(
      self, object_id: ObjectID | None=None, lock_type: LockType=LockType.READ):
    if not object_id:
      raise TypeError(
        "Drillholes cannot be created with Project.new(). "
        "Use DrillholeDatabase.new_drillhole() instead.")

    super().__init__(object_id, lock_type)
    self.__hole_id = None
    self.__name = None
    self.__collar = None
    self.__displayed_table = None
    self.__displayed_field = None
    self.__colour_map = None

    # :NOTE: Though drillholes have points and edges, they do not inherit
    # from point and edge properties, because they do not support most of
    # the operations defined by those classes.
    self.__points = DataProperty(
      lock=self._lock,
      configuration=DataPropertyConfiguration(
        name="points",
        dtype=ctypes.c_double,
        default=np.nan,
        column_count=3,
        primitive_count_function=self._modelling_api().ReadPointCount,
        cached_primitive_count_function=None,
        load_function=self._modelling_api().PointCoordinatesBeginR,
        save_function=None,
        set_primitive_count_function=None,
        immutable=True,
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode
      )
    )
    self.__point_selection = DataProperty(
      lock=self._lock,
      configuration=DataPropertyConfiguration(
        name="point_selection",
        dtype=ctypes.c_bool,
        default=False,
        column_count=1,
        primitive_count_function=self._modelling_api().ReadPointCount,
        cached_primitive_count_function=None,
        load_function=self._modelling_api().PointSelectionBeginR,
        save_function=None,
        immutable=True,
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode
      )
    )
    self.__edges = DataProperty(
      lock=self._lock,
      configuration=DataPropertyConfiguration(
        name="edges",
        dtype=ctypes.c_int32,
        default=0,
        column_count=2,
        primitive_count_function=self._modelling_api().ReadEdgeCount,
        load_function=self._modelling_api().EdgeToPointIndexBeginR,
        save_function=None,
        cached_primitive_count_function=None,
        immutable=True,
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode
      )
    )
    self.__edge_selection = DataProperty(
      lock=self._lock,
      configuration=DataPropertyConfiguration(
        name="edge_selection",
        dtype=ctypes.c_bool,
        default=False,
        column_count=1,
        primitive_count_function=self._modelling_api().ReadEdgeCount,
        cached_primitive_count_function=None,
        load_function=self._modelling_api().EdgeSelectionBeginR,
        save_function=None,
        immutable=True,
        raise_on_error_code=self._modelling_api().RaiseOnErrorCode
      )
    )
    self.__drillhole_information = None
    self.__visualisation_dirty = False
    self._initialise_table_variables()
    # Acquire the drillhole information immediately. This will ensure
    # a write lock is immediately taken on the database if the drillhole was
    # opened with Project.edit().
    _ = self._drillhole_information

  @classmethod
  def _drillhole_model_api(cls) -> DrillholeModelApi:
    """Access the DrillholeModel C API."""
    return cls._application_api().drillhole_model

  @classmethod
  def static_type(cls) -> StaticType:
    return cls._drillhole_model_api().DrillholeType()

  def _extra_invalidate_properties(self):
    super()._extra_invalidate_properties()
    self.__hole_id = None
    self.__name = None
    self.__collar = None
    self.__colour_map = None
    self.__points.invalidate()
    self.__point_selection.invalidate()
    self.__edges.invalidate()
    self.__edge_selection.invalidate()
    self.__displayed_table = None
    self.__displayed_field = None
    self.__visualisation_dirty = False
    if self._tables_cached:
      for table in self.tables:
        # pylint: disable=protected-access
        table._invalidate_properties()

  def _record_object_size_telemetry(self):
    if self._tables_cached:
      for table in self.tables:
        row_count = table.row_count
        self._record_size_for(
          f"{table.table_type.name.title()}",
          row_count
        )

  def _unlink(self):
    """Unlink the drillhole from its tables and fields.

    This breaks all of the cyclic dependencies between the drillhole
    and its tables and fields which should allow for these objects to
    be garbage collected.
    """
    super()._unlink()
    self.__displayed_table = None
    self.__displayed_field = None

  def close(self):
    # Note that the superclass implementation of close() will call
    # invalidate properties.
    super().close()
    self._unlink()
    # The drillhole information struct is kept until the object is closed.
    # This way if the properties are invalidated, it can be reused to
    # read the values.
    self.__delete_drillhole_information()

  def _save_topology(self):
    self.__save_tables(self._drillhole_information)
    if self.__visualisation_dirty:
      self._drillhole_model_api().DrillholeSetVisualisation(
        self._lock.lock,
        self.displayed_table.name,
        self.displayed_field.name,
        self.get_colour_map().handle)
      self.__visualisation_dirty = False
    self._drillhole_model_api().WriteToBackend(self._drillhole_information)
    self._drillhole_model_api().BuildGeometry(
      self._lock.lock, self._drillhole_information)

  @property
  def _database_id(self) -> ObjectID:
    """The object id of the database which the drillhole is a part of."""
    parent_id = self.id.parent
    if not parent_id:
      raise OrphanDrillholeError(self._hole_id)
    return parent_id

  @property
  def _hole_id(self) -> str:
    """The hole id for the drillhole in the database.

    This may not be the same as the drillhole's name in the Project
    if the drillhole has been renamed.
    """
    if self.__hole_id is None:
      self.__hole_id = self._drillhole_model_api().DrillholeId(self._lock.lock)
    return self.__hole_id

  @property
  def _drillhole_information(self) -> S_DrillholeInformation:
    """A pointer to a struct which contains the drillhole object.

    This is passed to the C API to access the drillhole. From the Python
    side it is a ctypes.c_void_p object.

    Warnings
    --------
    If this is accessed, it must eventually be deallocated with
    _delete_drillhole_information() otherwise there will be a memory leak.
    """
    if self.__drillhole_information is None:
      if self.is_read_only:
        self.__drillhole_information = \
          self._drillhole_model_api().OpenDrillholeInformationReadOnly(
            self._database_id.handle, self._hole_id)
      else:
        self.__drillhole_information = \
          self._drillhole_model_api().OpenDrillholeInformationReadWrite(
            self._database_id.handle, self._hole_id)
    return self.__drillhole_information

  @property
  def name(self) -> str:
    """The name of the drillhole."""
    if self.__name is None:
      self.__name = self._drillhole_model_api().GetName(self._lock.lock)
    return self.__name

  @property
  def converted_collar(self) -> Point:
    """The collar point of the drillhole adjusted for the coordinate system.

    This is the collar point adjusted for the drillhole's coordinate system
    and thus where the collar point appears when the drillhole is viewed in
    the application.

    This will not match the ordinates read from the collar table (and thus
    the raw_collar property) if the drillhole has a coordinate system.

    Raises
    ------
    TableNotFoundError
      If there is no collar table.
    TooManyTablesError
      If there are multiple collar tables in the database.

    Warnings
    --------
    If the collar table or the raw_collar property is edited, changes will
    only be reflected in this property after save() is called.

    Notes
    -----
    If there is no elevation field in the collar table, the Z ordinate
    will always be zero.
    """
    if self.__collar is None:
      self.__collar = np.array(
        self._drillhole_model_api().GetCollar(
          self._lock.lock), dtype=np.float64)
    return self.__collar

  @property
  def raw_collar(self) -> Point:
    """The collar point as it appears in the collar table.

    This does not take into account the drillhole's coordinate system.

    This will not match the converted_collar property if the drillhole has
    a coordinate system.

    Warns
    -----
    RuntimeWarning
      If the table contains no elevation field and the collar is set to
      a point containing a non-zero Z ordinate.

    Notes
    -----
    If there is no elevation field in the collar table, the Z ordinate
    will always be zero.

    Examples
    --------
    If the table has an elevation field, when assigning to this property
    the caller should provide a northing, easting and elevation value:

    >>> drillhole.raw_collar = [1.1, 2.2, 3.3]

    If the table does not have an elevation field, when assigning to this
    property the elevation may be omitted:

    >>> drillhole.raw_collar = [1.1, 2.2]
    """
    return self.collar_table.collar_point

  @raw_collar.setter
  def raw_collar(self, value: PointLike):
    self.collar_table.collar_point = value

  @property
  def displayed_table(self) -> BaseDrillholeTable:
    """Returns the displayed table for the drillhole.

    This is the table which contains the displayed field used to colour
    the intervals of the drillhole in views.

    Returns
    -------
    BaseDrillholeTable
      The displayed table.

    Raises
    ------
    TableNotFoundError
      If the displayed table cannot be found.
    """
    if self.__displayed_table is None:
      displayed_table_name = self._drillhole_model_api().GetDisplayedTableName(
        self._lock.lock)
      self.__displayed_table = self.table_by_name(displayed_table_name)
    return self.__displayed_table

  @property
  def displayed_field(self) -> DrillholeDatabaseField:
    """Returns the displayed field for the drillhole.

    When the drillhole is displayed in the application, this is the field which
    is used to determine the intervals used to colour the drillhole. This is
    also the field used to determine the points and edges returned by the
    drillhole's point and edge properties.

    Returns
    -------
    DrillholeDatabaseField
      The displayed field.

    Raises
    ------
    TableNotFoundError
      If the displayed table cannot be found.
    FieldNotFoundError
      If the displayed field cannot be found.
    """
    if self.__displayed_field is None:
      displayed_field_name = self._drillhole_model_api().GetDisplayedFieldName(
        self._lock.lock)
      displayed_table = self.displayed_table
      self.__displayed_field = displayed_table.field_by_name(
        displayed_field_name)
    return self.__displayed_field

  def get_colour_map(self):
    if self.__colour_map is None:
      colour_map_id = ObjectID(
        self._drillhole_model_api().GetDisplayedColourMap(self._lock.lock))
      self.__colour_map = colour_map_id
    return self.__colour_map

  def set_visualisation(
      self,
      field: DrillholeDatabaseField,
      colour_map: ObjectID[ColourMap] | ColourMap):
    """Set the field and colour map used to display the Drillhole.

    Parameters
    ----------
    field
      Field to use to display the Drillhole.
    colour_map
      ObjectID of the colour map to use to display the Drillhole, or the
      colour map object itself.

    Raises
    ------
    ReadOnlyError
      If the drillhole is open for read-only.
    TypeError
      If colour_map is not an ObjectID.
    TypeError
      If field is not a DrillholeDatabaseField.
    TypeError
      If field contains numeric values and colour_map is a StringColourMap.
    TypeError
      If field contains string values and colour_map is a NumericColourMap.
    ValueError
      If field stores boolean values.
    ValueError
      If field is not a field read from this drillhole.
    """
    # pylint: disable=protected-access
    self._raise_if_read_only("set visualisation")
    if not isinstance(field, DrillholeDatabaseField):
      raise TypeError(
        default_type_error_message("field", field, DrillholeDatabaseField)
      )
    if field._table._parent is not self:
      field_drillhole_id = field._table._parent.id
      raise ValueError(
        "The field must be part of the drillhole to be coloured. "
        f"A field read from drillhole: '{field_drillhole_id.path}'."
        f"Cannot be used to colour: '{self.id.path}'")
    if not isinstance(colour_map, ObjectID):
      # If the caller passed a string or numeric colour map, extract
      # the id and continue.
      if isinstance(colour_map, (NumericColourMap, StringColourMap)):
        colour_map = colour_map.id
      else:
        raise TypeError(
          default_type_error_message(
            "colour_map",
            colour_map,
            (ObjectID, StringColourMap, NumericColourMap)))
    if field.is_numeric and colour_map.is_a(StringColourMap):
      raise TypeError(
        "Cannot colour drillhole by a numeric field of type "
        f"'{field.data_type}' using a non-numeric colour map of type: "
        f"'{colour_map.type_name}'")
    if field.is_string and colour_map.is_a(NumericColourMap):
      raise TypeError(
        "Cannot colour drillhole by a string field using a "
        f"non-string colour map of type: '{colour_map.type_name}'")
    # This would be a lot smoother if there was a base class for colour maps.
    if not colour_map.is_a(StringColourMap
        ) and not colour_map.is_a(NumericColourMap):
      numeric_map = NumericColourMap.__name__
      string_map = StringColourMap.__name__
      raise TypeError(
        f"Invalid colour map: {colour_map} ({colour_map.type_name}). "
        f"colour_map must be the object id of a {numeric_map} "
        f"or a {string_map}")
    if field.data_type == np.bool_:
      raise ValueError(
        "Cannot colour drillhole using a boolean field.")

    self.__displayed_field = field
    self.__displayed_table = field._table
    self.__colour_map = colour_map
    self.__visualisation_dirty = True

  @property
  def points(self) -> np.ndarray:
    """The points used to visualise the drillhole.

    These points mark the boundaries of intervals for the displayed field
    in the displayed table. Thus these are a property of the visualisation of
    the drillhole and not the drillhole itself. This array cannot be edited
    directly, however edits to the displayed field will propagate to this
    property when the drillhole is saved.

    Notes
    -----
    The points of a drillhole are derived from the displayed table and cannot
    be edited directly from Python.
    """
    return self.__points.values

  @property
  def point_selection(self) -> np.ndarray:
    """Point selection array for the drillhole.

    If point_selection[i] is True then the point located at points[i] is
    selected.

    Notes
    -----
    The point selection of a drillhole cannot be edited from Python.
    """
    return self.__point_selection.values

  @property
  def edges(self) -> np.ndarray:
    """The edges used to visualise the drillhole.

    The edges which represent the intervals of the displayed field in the
    displayed table. Thus these are a property of the visualisation of the
    drillhole and not the drillhole itself. This array cannot be edited
    directly, however edits to the displayed field will propagate to this
    property when the drillhole is saved.

    Notes
    -----
    The edges of a drillhole are derived from the displayed table and cannot
    be edited directly from Python.
    """
    return self.__edges.values

  @property
  def edge_selection(self) -> np.ndarray:
    """Edge selection array for the drillhole.

    If edge_selection[i] is True then the edge located at edges[i] is selected.

    Notes
    -----
    The edge selection of a drillhole cannot be edited from Python.
    """
    return self.__edge_selection.values

  @property
  def assay_table(self) -> AssayTable:
    return super().assay_table # type: ignore

  @property
  def collar_table(self) -> CollarTable:
    return super().collar_table # type: ignore

  @property
  def survey_table(self) -> SurveyTable:
    return super().survey_table # type: ignore

  @property
  def geology_table(self) -> GeologyTable:
    return super().geology_table # type: ignore

  @property
  def downhole_table(self) -> DownholeTable:
    return super().downhole_table # type: ignore

  @property
  def quality_table(self) -> QualityTable:
    return super().quality_table # type: ignore

  @property
  def tables(self) -> Sequence[BaseDrillholeTable]:
    return super().tables

  def point_at_depth(self, depth: float) -> np.ndarray:
    """Get the point in the drillhole at the specified depth.

    The returned point is relative to the collar point. To get the point
    at the specified depth in world coordinates, you must add the collar
    point to this point.

    This takes into account the desurvey method assigned to the drillhole
    database and any values in the survey table.

    Parameters
    ----------
    depth
      The depth down the hole for which the point should be returned.

    Returns
    -------
    np.ndarray
      Numpy array of shape (3,) containing the X, Y and Z coordinate of
      the point at the specified depth down the hole. This may not
      correspond to any point in the points array.

    Raises
    ------
    SurveyTableLoadedError
      If the drillhole is open for editing and may have unsaved changes.
    """
    if not self.is_read_only:
      survey_table = self.survey_table
      # pylint: disable=protected-access
      if any((
            survey_table.depth._values_cached,
            survey_table.azimuth._values_cached,
            survey_table.dip._values_cached,
          )):
        raise SurveyTableLoadedError(
          "There may be unsaved changes to the survey table."
          "You must close and reopen the drillhole before calling this "
          "function.")
    # Convert the depth to a float. This provides a better error message
    # than relying on ctypes to perform the conversion.
    float_depth = float(depth)
    return np.array(
      self._drillhole_model_api().DrillholeGetPointAtDepth(
        self._drillhole_information,
        self._lock.lock,
        float_depth
      )
    )

  @typing.overload
  def tables_by_type(
    self,
    table_type: typing.Literal[DrillholeTableType.ASSAY]
  ) -> Sequence[AssayTable]:
    ...

  @typing.overload
  def tables_by_type(
    self,
    table_type: typing.Literal[DrillholeTableType.COLLAR]
  ) -> Sequence[CollarTable]:
    ...

  @typing.overload
  def tables_by_type(
    self,
    table_type: typing.Literal[DrillholeTableType.DOWNHOLE]
  ) -> Sequence[DownholeTable]:
    ...

  @typing.overload
  def tables_by_type(
    self,
    table_type: typing.Literal[DrillholeTableType.GEOLOGY]
  ) -> Sequence[GeologyTable]:
    ...

  @typing.overload
  def tables_by_type(
    self,
    table_type: typing.Literal[DrillholeTableType.QUALITY]
  ) -> Sequence[QualityTable]:
    ...

  @typing.overload
  def tables_by_type(
    self,
    table_type: typing.Literal[DrillholeTableType.SURVEY]
  ) -> Sequence[SurveyTable]:
    ...

  @typing.overload
  def tables_by_type(
    self,
    table_type: typing.Literal[DrillholeTableType.OTHER]
  ) -> Sequence[BaseDrillholeTable]:
    ...

  @typing.overload
  def tables_by_type(
    self,
    table_type: typing.Literal[DrillholeTableType.UNKNOWN]
  ) -> Sequence[BaseDrillholeTable]:
    ...

  @typing.overload
  def tables_by_type(
    self,
    table_type: DrillholeTableType
  ) -> Sequence[BaseDrillholeTable]:
    ...

  def tables_by_type(self, table_type: DrillholeTableType
      ) -> Sequence[BaseDrillholeTable]:
    return super().tables_by_type(table_type)

  def _table_values(
      self, table: BaseDrillholeTable, field: DrillholeDatabaseField
      ) -> np.ma.MaskedArray:
    """Returns the values for the specified table, field and hole.

    Parameters
    ----------
    table
      The table to query the values for.
    field
      The field to query the values for.
    hole
      The drillhole to return values for.

    Returns
    -------
    numpy.ma.MaskedArray
      Masked numpy array containing the values for the specified table, field
      and hole.

    Raises
    ------
    NotImplementedError
      If reading values of the field's data_type is not implemented.
    """
    #pylint: disable=protected-access
    row_count = table.row_count
    if field.data_type == np.float64:
      values = self._drillhole_model_api().GetTableColumnValuesDouble(
        self._drillhole_information, table.name, field._index, row_count)
      values = np.ma.masked_array(
        values, mask=np.isnan(values), dtype=field.data_type, fill_value=np.nan)
    elif field.data_type == np.float32:
      values = self._drillhole_model_api().GetTableColumnValuesFloat(
        self._drillhole_information, table.name, field._index, row_count)
      # :TRICKY: This can't use np.ma.masked_where or similar functions because
      # they would incorrectly deduce the dtype as np.float64.
      values = np.ma.masked_array(
        values, mask=np.isnan(values), dtype=field.data_type, fill_value=np.nan)
    elif field.data_type == np.bool_:
      values = self._drillhole_model_api().GetTableColumnValuesBoolean(
        self._drillhole_information, table.name, field._index, row_count)
      values = np.ma.array(
        values, mask=np.ma.nomask, dtype=field.data_type, fill_value=False)
    elif field.data_type == np.str_:
      values = self._drillhole_model_api().GetTableColumnValuesString(
        self._drillhole_information, table.name, field._index, row_count)
      # Also can't use np.ma.masked_where here because it incorrectly
      # deduces the type for empty arrays to be float.
      values = np.ma.array(
        values, mask=np.ma.nomask, dtype=field.data_type, fill_value="")
      # Empty strings are used to represent invalid values.
      values.mask = values == ""
    elif field.data_type == np.int32:
      values, mask = self._drillhole_model_api().GetTableColumnValuesTint32s(
        self._drillhole_information, table.name, field._index, row_count)
      mask = np.array(mask, dtype=np.bool_)
      # Masked arrays use True to indicate an invalid index so the mask
      # must be inverted.
      np.invert(mask, out=mask)
      values = np.ma.array(values, mask=mask, dtype=np.int32)
    else:
      # :TODO: SDK-663: Support DateTime fields. They were removed from
      # the UI due to issues in their implementation.

      raise NotImplementedError(
        f"Reading values of field '{field.name}' of type: '{field.data_type}' "
        "is not implemented")

    values.flags.writeable = not self.is_read_only
    return values

  def __save_tables(self, editable_drillhole: S_DrillholeInformation):
    """Save the tables to the database.

    Parameters
    ----------
    editable_drillhole
      Read/write S_DrillholeInformation for the drillhole to save the tables
      for.
    """
    # Skip saving the tables if they were not loaded.
    if not self._tables_cached:
      return

    for table in self.tables:
      for field in table.fields:
        self.__save_values(table, field, editable_drillhole)

  def __save_values(
      self,
      table: BaseDrillholeTable,
      field: DrillholeDatabaseField,
      editable_drillhole: S_DrillholeInformation):
    """Save the values of a table.

    Parameters
    ----------
    table
      The table to save the values for.
    field
      The field to save the values for.
    editable_drillhole
      Read/write S_DrillholeInformation for the drillhole to save the
      values for.
    """
    # pylint: disable=protected-access

    # If the values were not accessed, do not save them.
    if not field._values_cached:
      return

    if field.data_type == np.float64:
      self._drillhole_model_api().SetTableColumnValuesDouble(
        editable_drillhole, table.name, field._index, field.values)
    elif field.data_type == np.float32:
      self._drillhole_model_api().SetTableColumnValuesFloat(
        editable_drillhole, table.name, field._index, field.values)
    elif field.data_type == np.bool_:
      self._drillhole_model_api().SetTableColumnValuesBoolean(
        editable_drillhole, table.name, field._index, field.values)
    elif field.data_type == np.str_:
      self._drillhole_model_api().SetTableColumnValuesString(
        editable_drillhole, table.name, field._index, field.values)
    elif field.data_type == np.int32:
      self._drillhole_model_api().SetTableColumnValuesTint32s(
        editable_drillhole, table.name, field._index, field.values)
    else:
      LOG.warning("Skipping saving field: '%s' of table '%s' of drillhole "
                  "'%s'. Saving fields of type: '%s' is not implemented.",
                  field.name, table.name, self.name, field.data_type.name)

  def _load_database_information(self) -> str:
    if self.closed:
      raise ObjectClosedError()
    try:
      return self._drillhole_model_api().GetDatabaseInformation(
        self._database_id.handle)
    except Exception as error:
      raise DatabaseLoadError(
        f"Failed to read the database for '{self.id.name}'. "
        "It may not be inside a DrillholeDatabase or the drillhole "
        "may have been deleted from the database."
      ) from error

  @classmethod
  def _table_type_to_class(cls):
    return {
      DrillholeTableType.ASSAY : AssayTable,
      DrillholeTableType.COLLAR : CollarTable,
      DrillholeTableType.DOWNHOLE : DownholeTable,
      DrillholeTableType.GEOLOGY : GeologyTable,
      DrillholeTableType.QUALITY : QualityTable,
      DrillholeTableType.SURVEY : SurveyTable,
      DrillholeTableType.OTHER : CustomTable,
    }

  @classmethod
  def _default_table_type(cls):
    return CustomTable

  def __delete_drillhole_information(self):
    """Delete the drillhole information object.

    Does nothing if the drillhole information was not accessed.
    """
    if self.__drillhole_information is not None:
      self._drillhole_model_api().CloseDrillholeInformation(
        self.__drillhole_information)
      self.__drillhole_information = None
