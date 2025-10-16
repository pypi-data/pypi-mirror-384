"""Interface for the eureka drillholemodel library.

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

# pylint: disable=line-too-long
import ctypes
import math
import warnings

from .errors import (
  CApiUnknownError,
  CApiUnknownWarning,
)
from .types import T_TypeIndex, T_ReadHandle, T_ObjectHandle
from .util import raise_if_version_too_old
from .wrapper_base import WrapperBase

COLUMN_LENGTH_MISMATCH_LOG_MESSAGE = (
  "Column length hint was incorrect for table: '%s', field: %i. "
  "Expected length: %i, Actual length: %i")

FAILED_TO_READ_VALUES_MESSAGE = (
  "Failed to read values for table: '%s', field: '%i'"
)

FAILED_TO_WRITE_VALUES_MESSAGE = (
  "Failed to write values for table: '%s', field: '%i'"
)

ERROR_CODE_DATABASE_DOES_NOT_SUPPORT_EDIT = 254

_CACHED_DATABASE_INFORMATION = {}
"""Used to cache database information read from the application.

The key is the ObjectID of the drillhole database and the value is a tuple
of the form: (database_description, checksum) where:
database_description is the JSON description of the database.
checksum is the checksum calculated over this description.
"""

class S_DrillholeInformation(ctypes.c_void_p):
  """Struct representing a drillhole in the database.

  This is an opaque pointer which can be passed to C API functions to
  specify which drillhole in the database the functions should use.
  These structs can either be read-only or read-write depending on the function
  in the C API which returned it.
  To avoid memory leaks, these objects must be deallocated through the C API.
  See the documentation on the function which returned the object for
  instructions on how it should be deallocated.
  """

class DrillholeModelApi(WrapperBase):
  """Access to the application drillhole model API.

  This API is only available in GeologyCore. Attempting to load it when
  connected to another application will encounter an error.
  This should be accessed through get_application_dlls() for new code.
  """
  @staticmethod
  def method_prefix():
    return "DrillholeModel"

  @staticmethod
  def dll_name() -> str:
    return "drillholemodel"

  def capi_functions(self):
    return [
      # Functions changed in version 0.
      {},
      # Functions changed in version 1.
      {
        "DrillholeModelCApiVersion" : (ctypes.c_uint32, None),
        "DrillholeModelCApiMinorVersion" : (ctypes.c_uint32, None),
        "DrillholeModelDatabaseType" : (T_TypeIndex, None),
        "DrillholeModelDrillholeType" : (T_TypeIndex, None),
        "DrillholeModelDrillholeDatabaseDataengineType" : (T_TypeIndex, None),
        "DrillholeModelNewInternalDatabase" : (T_ObjectHandle, None),
        "DrillholeModelNewDrillhole" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ctypes.POINTER(T_ObjectHandle), ]),
        "DrillholeModelDrillholeId" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint32), ]),
        "DrillholeModelGetName" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint32), ]),
        "DrillholeModelGetCollar" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_double), ]),
        "DrillholeModelGetDisplayedTableName" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint32), ]),
        "DrillholeModelGetDisplayedFieldName" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint32), ]),
        "DrillholeModelGetDisplayedColourMap" : (T_ObjectHandle, [ctypes.POINTER(T_ReadHandle), ]),
        "DrillholeModelDrillholeSetVisualisation" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ctypes.c_char_p, T_ObjectHandle, ]),
        "DrillholeModelGetDatabaseInformationChecksum" : (ctypes.c_uint8, [T_ObjectHandle, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32, ]),
        "DrillholeModelGetDatabaseInformation" : (ctypes.c_uint8, [T_ObjectHandle, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint32), ]),
        "DrillholeModelOpenDrillholeInformationReadOnly" : (S_DrillholeInformation, [T_ObjectHandle, ctypes.c_char_p, ]),
        "DrillholeModelOpenDrillholeInformationReadWrite" : (S_DrillholeInformation, [T_ObjectHandle, ctypes.c_char_p, ]),
        "DrillholeModelCloseDrillholeInformation" : (None, [S_DrillholeInformation, ]),
        "DrillholeModelWriteToBackend" : (ctypes.c_uint8, [S_DrillholeInformation, ]),
        "DrillholeModelBuildGeometry" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), S_DrillholeInformation, ]),
        "DrillholeModelGetTableRowCount" : (ctypes.c_uint64, [S_DrillholeInformation, ctypes.c_char_p, ]),
        "DrillholeModelAddRows" : (ctypes.c_uint8, [S_DrillholeInformation, ctypes.c_char_p, ctypes.c_uint64, ctypes.c_uint64, ]),
        "DrillholeModelRemoveRows" : (ctypes.c_uint8, [S_DrillholeInformation, ctypes.c_char_p, ctypes.c_uint64, ctypes.c_uint64, ]),
        "DrillholeModelDatabaseFromJson" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
        "DrillholeModelDatabaseRefreshDrillholes" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ]),
        "DrillholeModelGetDatabaseDesurveyMethod" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ]),
        "DrillholeModelSetDatabaseDesurveyMethod" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint8, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ]),
        "DrillholeModelDrillholeGetPointAtDepth" : (ctypes.c_uint8, [S_DrillholeInformation, ctypes.POINTER(T_ReadHandle), ctypes.c_double, ctypes.POINTER(ctypes.c_double), ]),
        "DrillholeModelGetTableColumnValuesDouble" : (ctypes.c_uint8, [S_DrillholeInformation, ctypes.c_char_p, ctypes.c_uint64, ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_uint64), ]),
        "DrillholeModelGetTableColumnValuesFloat" : (ctypes.c_uint8, [S_DrillholeInformation, ctypes.c_char_p, ctypes.c_uint64, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_uint64), ]),
        "DrillholeModelGetTableColumnValuesBoolean" : (ctypes.c_uint8, [S_DrillholeInformation, ctypes.c_char_p, ctypes.c_uint64, ctypes.POINTER(ctypes.c_bool), ctypes.POINTER(ctypes.c_uint64), ]),
        "DrillholeModelGetTableColumnValuesString" : (ctypes.c_uint8, [S_DrillholeInformation, ctypes.c_char_p, ctypes.c_uint64, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint64), ]),
        "DrillholeModelGetTableColumnValuesTint32s" : (ctypes.c_uint8, [S_DrillholeInformation, ctypes.c_char_p, ctypes.c_uint64, ctypes.POINTER(ctypes.c_int32), ctypes.POINTER(ctypes.c_bool), ctypes.POINTER(ctypes.c_uint64), ]),
        "DrillholeModelSetTableColumnValuesDouble" : (ctypes.c_uint8, [S_DrillholeInformation, ctypes.c_char_p, ctypes.c_uint64, ctypes.POINTER(ctypes.c_double), ctypes.c_uint64, ]),
        "DrillholeModelSetTableColumnValuesFloat" : (ctypes.c_uint8, [S_DrillholeInformation, ctypes.c_char_p, ctypes.c_uint64, ctypes.POINTER(ctypes.c_float), ctypes.c_uint64, ]),
        "DrillholeModelSetTableColumnValuesBoolean" : (ctypes.c_uint8, [S_DrillholeInformation, ctypes.c_char_p, ctypes.c_uint64, ctypes.POINTER(ctypes.c_bool), ctypes.c_uint64, ]),
        "DrillholeModelSetTableColumnValuesString" : (ctypes.c_uint8, [S_DrillholeInformation, ctypes.c_char_p, ctypes.c_uint64, ctypes.c_char_p, ctypes.c_uint64, ctypes.c_uint64, ]),
        "DrillholeModelSetTableColumnValuesTint32s" : (ctypes.c_uint8, [S_DrillholeInformation, ctypes.c_char_p, ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_bool), ctypes.c_uint64, ]),
      },
    ]

  def _handle_string_buffer(self, *args, c_api_function):
    """Runs a function in the C API which uses a string buffer.

    This requires the string buffer to be the second last argument and for
    the last argument to be a pointer to the length of the string buffer.

    Parameters
    ----------
    *args
      Positional arguments to pass to c_api_function. These should be
      in order and are passed before the string buffer and length arguments.
    c_api_function : function
      The function to call. This should accept a string buffer as the second
      last argument and the length of that buffer as the last argument.

    Returns
    -------
    str
      The string read from the c_api_function.

    Raises
    ------
    CApiUnknownError
      If an unknown error occurs.
    """
    # Start with a null buffer. This will cause the buffer length
    # to be set to an appropriate size.
    buffer_length = ctypes.c_uint32(0)
    buffer = None

    result = c_api_function(
      *args, buffer, ctypes.byref(buffer_length))

    # The empty buffer was large enough so the property must be empty.
    if result == 0:
      return ""

    # A result of 5 indicates that the buffer was too small, and
    # buffer length was set to the required buffer size.
    if result != 5:
      message = "Failed to read drillhole information."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

    # Try again with an appropriately sized buffer.
    buffer = ctypes.create_string_buffer(buffer_length.value)
    result = c_api_function(
      *args, buffer, ctypes.byref(buffer_length))

    if result == 0:
      return bytearray(buffer).decode('utf-8')

    message = "Failed to read drillhole information."
    self.log.error(message)
    self.log.info("Error code: %s", result)
    raise CApiUnknownError(message)

  def DatabaseType(self):
    """Wrapper for returning the type index for dhmC_Database."""
    raise_if_version_too_old("Drillhole databases",
                             current_version=self.version,
                             required_version=(1, 7))
    return self.dll.DrillholeModelDatabaseType()

  def DrillholeType(self):
    """Wrapper for returning the type index for dhmC_Drillhole."""
    raise_if_version_too_old("Drillholes",
                             current_version=self.version,
                             required_version=(1, 7))
    return self.dll.DrillholeModelDrillholeType()

  def DrillholeDatabaseDataengineType(self):
    """Wrapper for returning the type index for ddbdC_Database"""
    raise_if_version_too_old("Drillhole databases",
                             current_version=self.version,
                             required_version=(1, 7))
    return self.dll.DrillholeModelDrillholeDatabaseDataengineType()

  def NewInternalDatabase(self):
    """Wrapper for creating a new internal drillhole database."""
    raise_if_version_too_old("Creating an internal drillhole database",
                             current_version=self.version,
                             required_version=(1, 7))
    return self.dll.DrillholeModelNewInternalDatabase()

  def NewDrillhole(self, lock, hole_id):
    """Wrapper for adding a new drillhole.

    Parameters
    ----------
    lock : Lock
      Edit lock on the dhmC_Database to add the drillhole to.
    hole_id : str
      Unique string identifier for the new drillhole.

    Returns
    -------
    T_ObjectHandle
      Object handle for the newly created drillhole.

    Raises
    ------
    ValueError
      If there is already a drillhole with the given ID in the database.
    """
    raise_if_version_too_old("Creating a new drillhole",
                             current_version=self.version,
                             required_version=(1, 7))
    drillhole = T_ObjectHandle(0)
    result = self.dll.DrillholeModelNewDrillhole(
      lock, hole_id.encode("utf-8"), ctypes.byref(drillhole))

    if result == 0:
      return drillhole

    if result == 3:
      raise ValueError(
        f"Failed to create a new drillhole with ID: '{hole_id}'."
        "The database already contained a drillhole with that ID.")

    message = "Failed to add drillhole to the database."
    self.log.error(message)
    self.log.info("Error code: %s", result)
    raise CApiUnknownError(message)

  def DrillholeId(self, lock):
    """Wrapper for reading the drillhole ID of a drillhole.

    Parameters
    ----------
    lock : Lock
      Lock on the Drillhole from which to query the ID.

    Returns
    -------
    str
      The drillhole's ID in the database.
    """
    raise_if_version_too_old("Accessing back-end of drillhole database",
                             current_version=self.version,
                             required_version=(1, 7))

    return self._handle_string_buffer(lock, c_api_function=self.dll.DrillholeModelDrillholeId)

  def GetName(self, lock):
    """Wrapper for reading the name of a drillhole.

    Parameters
    ----------
    lock : Lock
      Lock on the Drillhole from which to query the ID.

    Returns
    -------
    str
      The drillhole's name.
    """
    raise_if_version_too_old("Accessing name of a drillhole",
                             current_version=self.version,
                             required_version=(1, 7))

    return self._handle_string_buffer(lock, c_api_function=self.dll.DrillholeModelGetName)

  def GetCollar(self, lock):
    """Wrapper for reading the collar of a drillhole.

    This reads the collar property of the drillhole which may differ from
    the value in the collar table if a coordinate system transformation was
    made on the drillhole.

    Parameters
    ----------
    lock : Lock
      Lock on the drillhole for which the collar point should be returned.

    Returns
    -------
    ctypes.c_double * 3
      Ctypes array of doubles containing the X, Y and Z points of the drillhole.
    """
    raise_if_version_too_old("Accessing name of a drillhole",
                             current_version=self.version,
                             required_version=(1, 7))
    collar_point = (ctypes.c_double * 3)()

    result = self.dll.DrillholeModelGetCollar(lock, collar_point)

    if result == 0:
      return collar_point

    message = "Failed to get drillhole name."
    self.log.error(message)
    self.log.info("Error code: %s", result)
    raise CApiUnknownError(message)

  def GetDisplayedTableName(self, lock):
    """Wrapper for reading the displayed table name for a drillhole.

    Parameters
    ----------
    lock : Lock
      Lock on the Drillhole for which to query the displayed table name.

    Returns
    -------
    str
      The name of the displayed table.
    """
    raise_if_version_too_old("Accessing displayed table name of a drillhole",
                             current_version=self.version,
                             required_version=(1, 7))

    return self._handle_string_buffer(
      lock, c_api_function=self.dll.DrillholeModelGetDisplayedTableName)

  def GetDisplayedFieldName(self, lock):
    """Wrapper for reading the displayed field name for a drillhole.

    Parameters
    ----------
    lock : Lock
      Lock on the Drillhole for which to query the displayed field name.

    Returns
    -------
    str
      The name of the displayed field.
    """
    raise_if_version_too_old("Accessing displayed field name of a drillhole",
                             current_version=self.version,
                             required_version=(1, 7))

    return self._handle_string_buffer(
      lock, c_api_function=self.dll.DrillholeModelGetDisplayedFieldName)

  def GetDisplayedColourMap(self, lock):
    """Wrapper for reading the displayed colour map.

    Parameters
    ----------
    lock : Lock
      Lock on the Drillhole for which to query the displayed colour map.

    Returns
    -------
    T_ObjectHandle
      Object handle of the colour map used to colour the drillhole.
    """
    raise_if_version_too_old("Accessing displayed colour map of a drillhole",
                             current_version=self.version,
                             required_version=(1, 7))

    return self.dll.DrillholeModelGetDisplayedColourMap(lock)

  def DrillholeSetVisualisation(
      self, lock, table_name, field_name, colour_map_handle):
    """Wrapper for setting the visualisation of a drillhole.

    Parameters
    ----------
    lock : Lock
      Read/write lock on drillhole to set visualisation for.
    table_name : str
      Name of the table containing the field to use to colour the
      drillhole.
    field_name : str
      Name of the field to use to colour the drillhole.
    colour_map_handle : T_ObjectHandle
      Handle of the colour map to use to colour the drillhole.
      This must be a string colour map for string fields and a numeric
      colour map for numeric fields.
    """
    raise_if_version_too_old("Setting display information for a drillhole",
                             current_version=self.version,
                             required_version=(1, 7))
    result = self.dll.DrillholeModelDrillholeSetVisualisation(
      lock,
      table_name.encode("utf-8"),
      field_name.encode("utf-8"),
      colour_map_handle)

    if result != 0:
      message = "Failed to set drillhole visualisation."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def GetDatabaseInformationChecksum(self, database_handle):
    """Get a checksum of the database information.

    This is used to detect changes to the database information. If the checksum
    changes, then the database information has changed and it must be
    read from the Project.

    Parameters
    ----------
    database_handle : T_ObjectHandle
      Object ID of the drillhole database to get the checksum for its database
      description.

    Returns
    -------
    Union[bytearray, float]
      The checksum represented as a bytearray.
      If an error occurs, this will be NaN (and thus will not compare
      as equal to any other checksum).
    """
    raise_if_version_too_old("Getting drillhole database checksum",
                             current_version=self.version,
                             required_version=(1, 7))

    hash_length = 64
    checksum = (ctypes.c_ubyte * hash_length)()
    result = self.dll.DrillholeModelGetDatabaseInformationChecksum(
      database_handle, checksum, hash_length)

    if result != 0:
      message = "Failed to query database checksum."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      warnings.warn(CApiUnknownWarning(message))
      # math.nan != math.nan, so this checksum will always compare as not equal.
      return math.nan
    return bytearray(checksum)

  def GetDatabaseInformation(self, handle):
    """Gets a JSON representation of the database information.

    Parameters
    ----------
    handle : T_ObjectHandle
      Object ID of the DrillholeDatabase for which the information should
      be returned.

    Returns
    -------
    str
      JSON string of database information.
    """
    raise_if_version_too_old("Getting drillhole table information",
                             current_version=self.version,
                             required_version=(1, 7))

    checksum = self.GetDatabaseInformationChecksum(handle)

    # Check if the cached database information could be used.
    if handle in _CACHED_DATABASE_INFORMATION:
      cached_information, old_checksum = _CACHED_DATABASE_INFORMATION[handle]
      if checksum == old_checksum:
        return cached_information

    database_information = self._handle_string_buffer(
      handle,
      c_api_function=self.dll.DrillholeModelGetDatabaseInformation)

    _CACHED_DATABASE_INFORMATION[handle] = (database_information, checksum)

    return database_information

  def OpenDrillholeInformationReadOnly(self, handle, hole_name):
    """Returns a pointer to a struct representing a drillhole.

    This can be passed to the drillhole_information parameter of other
    functions in this C API. This function returns a read-only version
    of S_DrillholeInformation. The pointer returned by this function must
    be freed by the CloseDrillholeInformationReadOnly function.

    Parameters
    ----------
    handle : T_ObjectHandle
      Object handle of the DrillholeDatabase for which contains the drillhole.
    hole_name : str
      The name of the hole.

    Returns
    -------
    S_DrillholeInformation
      Pointer to a struct representing the drillhole. This is a read-only
      version - passing it to functions which edit the drillhole will fail.
    """
    raise_if_version_too_old("Accessing drillhole in the database",
                             current_version=self.version,
                             required_version=(1, 7))
    return self.dll.DrillholeModelOpenDrillholeInformationReadOnly(
      handle,
      hole_name.encode("utf-8"))

  def OpenDrillholeInformationReadWrite(self, handle, hole_name):
    """Returns a pointer to a struct representing a drillhole.

    This is an opaque type which can be passed to various other functions
    to read or write to the drillhole. The pointer returned by this function
    must be freed by the CloseDrillholeInformationReadWrite function.

    Parameters
    ----------
    handle : T_ObjectHandle
      Object handle of the DrillholeDatabase for which contains the drillhole.
    hole_name : str
      The name of the hole.

    Returns
    -------
    S_DrillholeInformation
      Pointer to a struct representing the drillhole. This is a read/write
      version of the struct. It can be passed to any function requiring a
      S_DrillholeInformation.
    """
    raise_if_version_too_old("Editing drillhole in the database",
                             current_version=self.version,
                             required_version=(1, 7))
    return self.dll.DrillholeModelOpenDrillholeInformationReadWrite(
      handle,
      hole_name.encode("utf-8"))

  def CloseDrillholeInformation(self, pointer):
    """Deletes a S_DrillholeInformation object.

    Does nothing if passed a null pointer.

    Parameters
    ----------
    pointer : S_DrillholeInformation
      Object to free.
    """
    raise_if_version_too_old("Closing drillhole database",
                             current_version=self.version,
                             required_version=(1, 7))
    return self.dll.DrillholeModelCloseDrillholeInformation(pointer)

  def WriteToBackend(self, drillhole_information_rw):
    """Write the changes to the drillhole to the backend.

    Parameters
    ----------
    drillhole_information_rw : S_DrillholeInformation
      A read/write S_DrillholeInformation with the changes applied.
    """
    raise_if_version_too_old("Saving changes to drillhole database",
                             current_version=self.version,
                             required_version=(1, 7))
    result = self.dll.DrillholeModelWriteToBackend(drillhole_information_rw)

    if result != 0:
      message = "Failed to save drillhole."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def BuildGeometry(self, lock, drillhole_information_rw):
    """Build the drillhole's visualisation

    Parameters
    ----------
    lock : Lock
      Lock on the drillhole for which the geometry should be locked.
    drillhole_information_rw : S_DrillholeInformation
      A S_DrillholeInformation for the drillhole in the database which should
      be used to build the geometry.
    """
    raise_if_version_too_old("Building drillhole geometry",
                             current_version=self.version,
                             required_version=(1, 7))
    result = self.dll.DrillholeModelBuildGeometry(lock, drillhole_information_rw)

    if result != 0:
      message = "Failed to update drillhole geometry."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def GetTableRowCount(self, drillhole_information, table_name):
    """Returns the number of columns in the specified table.

    Parameters
    ----------
    drillhole_information : S_DrillholeInformation
      A S_DrillholeInformation for the drillhole whose row count should be
      returned.
    table_name : str
      The table's name in the database.

    Returns
    -------
    int
      The number rows the specified drillhole has for the specified table.
    """
    raise_if_version_too_old("Getting row count",
                             current_version=self.version,
                             required_version=(1, 7))

    return self.dll.DrillholeModelGetTableRowCount(
      drillhole_information, table_name.encode('utf-8'))

  def AddRows(self, drillhole_information, table_name, index, count):
    """Add multiple new row to the specified table of the specified drillhole.

    Parameters
    ----------
    drillhole_information : S_DrillholeInformation
      A S_DrillholeInformation for the drillhole to which the new rows should
      be added. This must be a read/write S_DrillholeInformation.
    table_name : str
      The name of the table to which the new rows should be added.
    index : int
      The index of the first new row to be added.
    count : int
      The number of new rows to add.
    """
    raise_if_version_too_old("Adding new rows",
                             current_version=self.version,
                             required_version=(1, 7))

    result = self.dll.DrillholeModelAddRows(
      drillhole_information, table_name.encode("utf-8"), index, count)

    if result != 0:
      message = "Failed to add row to drillhole."
      self.log.error("Failed to add rows to table: %s", table_name)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def RemoveRows(self, drillhole_information, table_name, index, count):
    """Remove one or more rows from the specified table.

    Parameters
    ----------
    drillhole_information : S_DrillholeInformation
      A S_DrillholeInformation for the drillhole which contains the table
      from which the rows should be removed. This must be a read/write
      S_DrillholeInformation.
    table_name : str
      The name of the table the rows should be deleted from.
    index : int
      The index of the first row to delete.
    count : int
      The number of rows to delete.
    """
    raise_if_version_too_old("Deleting rows",
                             current_version=self.version,
                             required_version=(1, 7))

    result = self.dll.DrillholeModelRemoveRows(
      drillhole_information, table_name.encode("utf-8"), index, count)

    if result != 0:
      message = "Failed to remove rows from drillhole."
      self.log.error("Failed to remove rows from table: %s", table_name)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def DatabaseFromJson(self, lock, database_information):
    """Wrapper for updating the database using JSON."""
    raise_if_version_too_old("Updating drillhole database schema",
                             current_version=self.version,
                             required_version=(1, 7))

    result = self.dll.DrillholeModelDatabaseFromJson(
      lock, database_information.encode("utf-8"))
    if result == ERROR_CODE_DATABASE_DOES_NOT_SUPPORT_EDIT:
      raise ValueError("The database does not supported editing its structure.")
    if result != 0:
      message = "Failed to update drillhole database information."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def DatabaseRefreshDrillholes(self, lock):
    """Wrapper for refreshing the visualisation of holes in a database.

    Parameters
    ----------
    lock : Lock
      Lock on the database for which the visualisation of its drillholes
      should be updated.
    """
    raise_if_version_too_old("Refreshing drillhole visualiation",
                             current_version=self.version,
                             required_version=(1, 7))
    result = self.dll.DrillholeModelDatabaseRefreshDrillholes(lock)

    if result != 0:
      message = (
        "Failed to refresh drillhole visualisation. "
        "The visualisation may need to be refreshed manually.")
      self.log.error(message)
      self.log.info("Error code: %s", result)
      # Failing to refresh the drillholes is not a fatal error, so emit
      # a warning instead of raising an error.
      warnings.warn(message, CApiUnknownWarning)

  def GetDatabaseDesurveyMethod(self, lock):
    """Wrapper for getting desurvey method of a drillhole database.

    Parameters
    ----------
    lock: Lock
      Lock on the database for which the desurvey method should be
      updated.

    Returns
    -------
    tuple
      Tuple containing the desurvey method, the tangent length and the
      tangent tolerance. The desurvey method is encoded as an integer
      using the following values:
      * 0 = None.
      * 1 = Segment following.
      * 2 = Segment preceding.
      * 3 = Tangent.
      * 4 = Tangent with length.
      * 5 = Balanced Tangent.
      * 6 = Minimum curvature.
      * 254 = Undefined.
      * 255 = Failed to determine the desurvey method.
      The tangent length and tolerance will be null unless the desurvey
      method is "Tangent with length" or "Minimum curvature".
    """
    raise_if_version_too_old("Getting desurvey method",
                             current_version=self.version,
                             required_version=(1, 8))

    tangent_length = ctypes.c_float(math.nan)
    tangent_tolerance = ctypes.c_float(math.nan)

    desurvey_method = self.dll.DrillholeModelGetDatabaseDesurveyMethod(
      lock,
      ctypes.byref(tangent_length),
      ctypes.byref(tangent_tolerance))

    return desurvey_method, tangent_length.value, tangent_tolerance.value

  def SetDatabaseDesurveyMethod(self, lock, desurvey_method, length, tolerance):
    """Wrapper for setting desurvey method of a drillhole database.

    Parameters
    ----------
    lock: Lock
      Lock on the database for which the desurvey method should be set.
    desurvey_method: int
      Integer encoded desurvey method to set to the drillhole database.
      The encoding is the same as the return value for
      GetDatabaseDesurveyMethod().
    length: float
      The length to use for the "Tangent with length" or "Minimum curvature"
      desurvey method.
    tolerance: float
      The tolerance to use for the "Tangent with length" or "Minimum curvature"
      desurvey method.
    """
    raise_if_version_too_old("Setting desurvey method",
                             current_version=self.version,
                             required_version=(1, 8))

    c_length = ctypes.c_float(length)
    c_tolerance = ctypes.c_float(tolerance)

    result = self.dll.DrillholeModelSetDatabaseDesurveyMethod(
      lock,
      desurvey_method,
      ctypes.byref(c_length),
      ctypes.byref(c_tolerance)
    )

    if result != 0:
      message = "Failed to set desurvey method."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def DrillholeGetPointAtDepth(
      self,
      drillhole_information,
      lock,
      depth):
    """Get the point of a drillhole at the specified depth.

    Parameters
    ----------
    drillhole_information
      Drillhole information for the drillhole for which the point at
      the specified depth should be returned.
    lock
      Lock on the drillhole for which the point at the specified depth
      should be returned.
    depth
      The depth of the point which should be returned.

    Returns
    -------
    list
      The point at the specified depth represented as the list
      [X, Y, Z].
    """
    raise_if_version_too_old("Getting point at depth",
                             current_version=self.version,
                             required_version=(1, 8))

    point_at_depth = (ctypes.c_double * 3)()

    result = self.dll.DrillholeModelDrillholeGetPointAtDepth(
      drillhole_information,
      lock,
      depth,
      point_at_depth
    )

    if result != 0:
      message = "Failed to get point at depth."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

    return list(point_at_depth)

  def GetTableColumnValuesDouble(
      self, drillhole_information, table_name, field_index, value_length_hint):
    """Get the values for the specified hole, table and field.

    This version of the function is for double columns. Undefined behaviour
    will occur if this is called for a non-double field.

    Parameters
    ----------
    drillhole_information : S_DrillholeInformation
      A S_DrillholeInformation for the drillhole whose values should be
      returned.
    table_name : str
      The table's name in the database.
    field_index : int
      The index of the field in the table.
    value_length_hint : int
      The expected number of values in the column.

    Returns
    -------
    list
      The values of the specified field in the specified hole.

    Raises
    ------
    CApiUnknownError
      If an unknown error occurs.
    """
    raise_if_version_too_old("Getting double values",
                             current_version=self.version,
                             required_version=(1, 7))

    # Use the length hint to allocate an appropriately sized array.
    values_length = ctypes.c_uint64(value_length_hint)
    values = (ctypes.c_double * values_length.value)()
    result = self.dll.DrillholeModelGetTableColumnValuesDouble(
      drillhole_information,
      table_name.encode('utf-8'),
      field_index,
      values,
      ctypes.byref(values_length))

    if result == 5:
      # The length hint was wrong which likely indicates a bug.
      self.log.warning(
        COLUMN_LENGTH_MISMATCH_LOG_MESSAGE,
        table_name, field_index, value_length_hint, values_length.value)
      # The buffer was too small, but values_length was set to the correct
      # size buffer. Try again with a correctly sized buffer.
      values = (ctypes.c_double * values_length.value)()
      result = self.dll.DrillholeModelGetTableColumnValuesDouble(
        drillhole_information,
        table_name.encode('utf-8'),
        field_index,
        values,
        ctypes.byref(values_length))

    if result == 0:
      # The slice removes any unused items in the buffer.
      return values[:values_length.value]

    message = "Failed to read values from drillhole."
    self.log.error(
      FAILED_TO_READ_VALUES_MESSAGE,table_name, field_index)
    self.log.info("Error code: %s", result)
    raise CApiUnknownError(message)

  def GetTableColumnValuesFloat(
      self, drillhole_information, table_name, field_index, value_length_hint):
    """Get the values for the specified hole, table and field.

    This version of the function is for float columns. Undefined behaviour
    will occur if this is called for a non-float field.

    Parameters
    ----------
    drillhole_information : S_DrillholeInformation
      A S_DrillholeInformation for the drillhole whose values should be
      returned.
    table_name : str
      The table's name in the database.
    field_index : int
      The index of the field in the table.
    value_length_hint : int
      The expected number of values in the column.

    Returns
    -------
    list
      The values of the specified field in the specified hole.

    Raises
    ------
    CApiUnknownError
      If an unknown error occurs.
    """
    raise_if_version_too_old("Getting float values",
                             current_version=self.version,
                             required_version=(1, 7))

    # Use the length hint to allocate an appropriately sized array.
    values_length = ctypes.c_uint64(value_length_hint)
    values = (ctypes.c_float * values_length.value)()
    result = self.dll.DrillholeModelGetTableColumnValuesFloat(
      drillhole_information,
      table_name.encode('utf-8'),
      field_index,
      values,
      ctypes.byref(values_length))

    if result == 5:
      # The length hint was wrong which likely indicates a bug.
      self.log.warning(
        COLUMN_LENGTH_MISMATCH_LOG_MESSAGE,
        table_name, field_index, value_length_hint, values_length.value)
      # The buffer was too small, but values_length was set to the correct
      # size buffer. Try again with a correctly sized buffer.
      values = (ctypes.c_float * values_length.value)()
      result = self.dll.DrillholeModelGetTableColumnValuesFloat(
        drillhole_information,
        table_name.encode('utf-8'),
        field_index,
        values,
        ctypes.byref(values_length))

    if result == 0:
      # The slice removes any unused items in the buffer.
      return values[:values_length.value]

    message = "Failed to read values from drillhole."
    self.log.error(
      FAILED_TO_READ_VALUES_MESSAGE, table_name, field_index)
    self.log.info("Error code: %s", result)
    raise CApiUnknownError(message)

  def GetTableColumnValuesString(
      self, drillhole_information, table_name, field_index, value_length_hint):
    """Get the values for the specified hole, table and field.

    This version of the function is for string columns. Undefined behaviour
    will occur if this is called for a non-string field.

    Parameters
    ----------
    drillhole_information : S_DrillholeInformation
      A S_DrillholeInformation for the drillhole whose values should be
      returned.
    table_name : str
      The table's name in the database.
    field_index : int
      The index of the field in the table.
    value_length_hint : int
      The expected number of values in the column.

    Returns
    -------
    list
      The values of the specified field in the specified hole.

    Raises
    ------
    CApiUnknownError
      If an unknown error occurs.
    """
    raise_if_version_too_old("Getting double values",
                             current_version=self.version,
                             required_version=(1, 7))

    # We can't predict the buffer size for strings, so start with an
    # empty buffer.
    buffer_length = ctypes.c_uint64(0)
    buffer = None
    result = self.dll.DrillholeModelGetTableColumnValuesString(
      drillhole_information,
      table_name.encode('utf-8'),
      field_index,
      buffer,
      ctypes.byref(buffer_length))

    # A result of zero here indicates there are no rows in the table.
    if result == 0:
      return []

    # The result should be 5 indicating that the buffer size was set.
    if result != 5:
      message = (
        "Failed to determine required buffer size for drillhole attribute.")
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

    # values_length was set to an appropriate buffer size. Try again
    # with an appropriately sized buffer.
    buffer = ctypes.create_string_buffer(buffer_length.value)
    result = self.dll.DrillholeModelGetTableColumnValuesString(
      drillhole_information,
      table_name.encode('utf-8'),
      field_index,
      buffer,
      ctypes.byref(buffer_length))

    if result == 0:
      # Values was set to all of the string values concatenated together
      # (each ending with a null terminating character).
      # Remove the last null terminating character and split the string
      # to get a list of strings.
      values = bytearray(buffer)[:-1].decode("utf-8").split("\0")
      if len(values) != value_length_hint:
        # The length hint was wrong which likely indicates a bug.
        self.log.warning(
          COLUMN_LENGTH_MISMATCH_LOG_MESSAGE,
          table_name, field_index, value_length_hint, len(values))

      # The slice removes any excess strings.
      return values[:value_length_hint]

    message = "Failed to read values from drillhole."
    self.log.error(
      FAILED_TO_READ_VALUES_MESSAGE, table_name, field_index)
    self.log.info("Error code: %s", result)
    raise CApiUnknownError(message)

  def GetTableColumnValuesTint32s(
      self, drillhole_information, table_name, field_index, value_length_hint):
    """Get the values for the specified hole, table and field.

    This version of the function is for 32 bit signed integer columns. Undefined
    behaviour will occur if this is called for fields of a different type.

    Parameters
    ----------
    drillhole_information : S_DrillholeInformation
      A S_DrillholeInformation for the drillhole whose values should be
      returned.
    table_name : str
      The table's name in the database.
    field_index : int
      The index of the field in the table.
    value_length_hint : int
      The expected number of values in the column.

    Returns
    -------
    tuple
      A tuple containing a list of the values of the specified field in the
      specified hole and a list of booleans indicating which values of the
      specified field are valid.

    Raises
    ------
    CApiUnknownError
      If an unknown error occurs.
    """
    raise_if_version_too_old("Getting 32 bit unsigned integer values",
                             current_version=self.version,
                             required_version=(1, 7))

    # Use the length hint to allocate an appropriately sized array.
    values_length = ctypes.c_uint64(value_length_hint)
    values = (ctypes.c_int32 * values_length.value)()
    validity = (ctypes.c_bool * values_length.value)()
    result = self.dll.DrillholeModelGetTableColumnValuesTint32s(
      drillhole_information,
      table_name.encode('utf-8'),
      field_index,
      values,
      validity,
      ctypes.byref(values_length))

    if result == 5:
      # The length hint was wrong which likely indicates a bug.
      self.log.warning(
        COLUMN_LENGTH_MISMATCH_LOG_MESSAGE,
        table_name, field_index, value_length_hint, values_length.value)
      # The buffer was too small, but values_length was set to the correct
      # size buffer. Try again with a correctly sized buffer.
      values = (ctypes.c_double * values_length.value)()
      values = (ctypes.c_int32 * values_length.value)()
      validity = (ctypes.c_bool * values_length.value)()
      result = self.dll.DrillholeModelGetTableColumnValuesTint32s(
        drillhole_information,
        table_name.encode('utf-8'),
        field_index,
        values,
        validity,
        ctypes.byref(values_length))

    if result == 0:
      # The slice removes any unused items in the buffer.
      return (values[:values_length.value], validity[:values_length.value])

    message = "Failed to read values from drillhole."
    self.log.error(
      FAILED_TO_READ_VALUES_MESSAGE, table_name, field_index)
    self.log.info("Error code: %s", result)
    raise CApiUnknownError(message)

  def GetTableColumnValuesBoolean(
      self, drillhole_information, table_name, field_index, value_length_hint):
    """Get the values for the specified hole, table and field.

    This version of the function is for boolean columns. Undefined behaviour
    will occur if this is called for a non-boolean field.

    Parameters
    ----------
    drillhole_information : S_DrillholeInformation
      A S_DrillholeInformation for the drillhole whose values should be
      returned.
    table_name : str
      The table's name in the database.
    field_index : int
      The index of the field in the table.
    value_length_hint : int
      The expected number of values in the column.

    Returns
    -------
    list
      The values of the specified field in the specified hole.

    Raises
    ------
    CApiUnknownError
      If an unknown error occurs.
    """
    raise_if_version_too_old("Getting boolean values",
                             current_version=self.version,
                             required_version=(1, 7))

    # Use the length hint to allocate an appropriately sized array.
    values_length = ctypes.c_uint64(value_length_hint)
    values = (ctypes.c_bool * values_length.value)()
    result = self.dll.DrillholeModelGetTableColumnValuesBoolean(
      drillhole_information,
      table_name.encode('utf-8'),
      field_index,
      values,
      ctypes.byref(values_length))

    if result == 5:
      # The length hint was wrong which likely indicates a bug.
      self.log.warning(
        COLUMN_LENGTH_MISMATCH_LOG_MESSAGE,
        table_name, field_index, value_length_hint, values_length.value)
      # The buffer was too small, but values_length was set to the correct
      # size buffer. Try again with a correctly sized buffer.
      values = (ctypes.c_double * values_length.value)()
      values = (ctypes.c_bool * values_length.value)()
      result = self.dll.DrillholeModelGetTableColumnValuesBoolean(
        drillhole_information,
        table_name.encode('utf-8'),
        field_index,
        values,
        ctypes.byref(values_length))

    if result == 0:
      # The slice removes any unused items in the buffer.
      return values[:values_length.value]

    message = "Failed to read values from drillhole."
    self.log.error(
      FAILED_TO_READ_VALUES_MESSAGE, table_name, field_index)
    self.log.info("Error code: %s", result)
    raise CApiUnknownError(message)

  def SetTableColumnValuesDouble(
      self, editable_drillhole, table_name, field_index, values_array):
    """Set the values of a double column.

    Parameters
    ----------
    editable_drillhole: S_DrillholeInformation
      A read/write S_DrillholeInformation for the drillhole whose values
      should be set.
    table_name : str
      The name of the table to set the values for.
    field_index : int
      Index of the field to set the values for.
    values_array : np.ma.MaskedArray
      Masked array containing the values to assign to the column.
      This should have the same length as the number of rows in the table.
      This function assumes that this array does not have strides set.
    """
    values_length = values_array.shape[0]

    # The mask is not sent to the C++ code so we need to set the masked
    # values to the fill value (nan) so that the mask will round trip.
    values_array.data[values_array.mask] = values_array.fill_value

    result = self.dll.DrillholeModelSetTableColumnValuesDouble(
      editable_drillhole,
      table_name.encode("utf-8"),
      field_index,
      values_array.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
      values_length)

    if result != 0:
      message = "Failed to write values for drillhole."
      self.log.error(
        FAILED_TO_WRITE_VALUES_MESSAGE, table_name, field_index)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def SetTableColumnValuesFloat(
      self, editable_drillhole, table_name, field_index, values_array):
    """Set the values of a float column.

    Parameters
    ----------
    editable_drillhole: S_DrillholeInformation
      A read/write S_DrillholeInformation for the drillhole whose values
      should be set.
    table_name : str
      The name of the table to set the values for.
    field_index : int
      Index of the field to set the values for.
    values_array : np.ma.MaskedArray
      Masked array containing the values to assign to the column.
      This should have the same length as the number of rows in the table.
      This function assumes that this array does not have strides set.
    """
    values_length = values_array.shape[0]

    # The mask is not sent to the C++ code so we need to set the masked
    # values to the fill value (nan) so that the mask will round trip.
    values_array.data[values_array.mask] = values_array.fill_value

    result = self.dll.DrillholeModelSetTableColumnValuesFloat(
      editable_drillhole,
      table_name.encode("utf-8"),
      field_index,
      values_array.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
      values_length)

    if result != 0:
      message = "Failed to write values for drillhole."
      self.log.error(
        FAILED_TO_WRITE_VALUES_MESSAGE, table_name, field_index)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def SetTableColumnValuesBoolean(
      self, editable_drillhole, table_name, field_index, values_array):
    """Set the values of a boolean column.

    Parameters
    ----------
    editable_drillhole: S_DrillholeInformation
      A read/write S_DrillholeInformation for the drillhole whose values
      should be set.
    table_name : str
      The name of the table to set the values for.
    field_index : int
      Index of the field to set the values for.
    values_array : np.ma.MaskedArray
      Masked array containing the values to assign to the column.
      This should have the same length as the number of rows in the table.
      This function assumes that this array does not have strides set.
    """
    values_length = values_array.shape[0]

    # The mask is not sent to the C++ code so we need to set the masked
    # values to the fill value (nan) so that the mask will round trip.
    values_array.data[values_array.mask] = values_array.fill_value

    result = self.dll.DrillholeModelSetTableColumnValuesBoolean(
      editable_drillhole,
      table_name.encode("utf-8"),
      field_index,
      values_array.ctypes.data_as(ctypes.POINTER(ctypes.c_bool)),
      values_length)

    if result != 0:
      message = "Failed to write values for drillhole."
      self.log.error(
        FAILED_TO_WRITE_VALUES_MESSAGE, table_name, field_index)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def SetTableColumnValuesString(
      self, editable_drillhole, table_name, field_index, values_array):
    """Set the values of a string column.

    Parameters
    ----------
    editable_drillhole: S_DrillholeInformation
      A read/write S_DrillholeInformation for the drillhole whose values
      should be set.
    table_name : str
      The name of the table to set the values for.
    field_index : int
      Index of the field to set the values for.
    values_array : np.ma.MaskedArray
      Masked array containing the values to assign to the column.
      This should have the same length as the number of rows in the table.
    """
    values_length = values_array.shape[0]

    # The mask is not sent to the C++ code so we need to set the masked
    # values to the fill value so that the mask will round trip.
    values_array.data[values_array.mask] = values_array.fill_value

    values = ""
    for value in values_array.data:
      values += value
      values += "\0"

    value_char_length = len(values)

    # This can't use values_array.ctypes.data_as(ctypes.POINTER(ctypes.c_char_p))
    # because numpy arrays are encoded as UCS4 (UTF-32) and not UTF-8.
    result = self.dll.DrillholeModelSetTableColumnValuesString(
      editable_drillhole,
      table_name.encode("utf-8"),
      field_index,
      values.encode("utf-8"),
      values_length,
      value_char_length)

    if result != 0:
      message = "Failed to write values for drillhole."
      self.log.error(
        FAILED_TO_WRITE_VALUES_MESSAGE, table_name, field_index)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def SetTableColumnValuesTint32s(
      self, editable_drillhole, table_name, field_index, values_array):
    """Set the values of a unsigned 32 bit integer column.

    Parameters
    ----------
    editable_drillhole: S_DrillholeInformation
      A read/write S_DrillholeInformation for the drillhole whose values
      should be set.
    table_name : str
      The name of the table to set the values for.
    field_index : int
      Index of the field to set the values for.
    values_array : np.ma.MaskedArray
      Masked array containing the values to assign to the column.
      This should have the same length as the number of rows in the table.
      This function assumes that this array does not have strides set.
    """
    values_length = values_array.shape[0]

    result = self.dll.DrillholeModelSetTableColumnValuesTint32s(
      editable_drillhole,
      table_name.encode("utf-8"),
      field_index,
      values_array.ctypes.data_as(ctypes.POINTER(ctypes.c_uint32)),
      # The mask is inverted for the C++ side.
      (~values_array.mask).ctypes.data_as(ctypes.POINTER(ctypes.c_bool)),
      values_length)

    if result != 0:
      message = "Failed to write values for drillhole."
      self.log.error(
        FAILED_TO_WRITE_VALUES_MESSAGE, table_name, field_index)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)
