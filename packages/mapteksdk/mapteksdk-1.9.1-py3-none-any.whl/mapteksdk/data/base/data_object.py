"""The base classes of all objects in a Project."""
###############################################################################
#
# (C) Copyright 2024, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import ctypes
import datetime
import logging
import typing

from .internal import ObjectAttributeDictionary as _ObjectAttributeDictionary
from ..change_reasons import ChangeReasons
from ..errors import (
  CannotSaveInReadOnlyModeError,
  ReadOnlyError,
  AlreadyOpenedError
)
from ..objectid import ObjectID
from ...capi import get_application_dlls
from ...internal.lock import LockType, ReadLock, WriteLock
from ...internal.singular_data_property_read_only import (
  SingularDataPropertyReadOnly,
)
from ...internal.telemetry import get_telemetry, data_type_to_string

if typing.TYPE_CHECKING:
  from ...capi.mdf_dlls import MdfDlls, DataEngineApi, ModellingApi
  from ...internal.telemetry import TelemetryProtocol

  ObjectAttributeTypes = (
    None | ctypes.c_bool | ctypes.c_int8 | ctypes.c_uint8
    | ctypes.c_int16 | ctypes.c_uint16 | ctypes.c_int32 | ctypes.c_uint32
    | ctypes.c_int64 | ctypes.c_uint64 | ctypes.c_float | ctypes.c_double
    | ctypes.c_char_p | datetime.datetime | datetime.date
  )
  ObjectAttributeDataTypes = type[ObjectAttributeTypes]
  """Alias for the union of valid data types for object attributes."""

  ObjectAttributeTypesWithAlias = (
    ObjectAttributeTypes | bool | str | int | float
  )
  """Object attribute types plus Python types which alias common types.

  For convenience some functions treat certain Python types as aliases
  for C types. The aliases are displayed in the following tables.

  +-------------+-----------------+
  | Python type | C type          |
  +=============+=================+
  | bool        | ctypes.c_bool   |
  +-------------+-----------------+
  | str         | ctypes.c_char_p |
  +-------------+-----------------+
  | int         | ctypes.c_int16  |
  +-------------+-----------------+
  | float       | ctypes.c_double |
  +-------------+-----------------+

  Notes
  -----
  The above table only applies for object-level attributes.
  """


log = logging.getLogger("mapteksdk.data")

StaticType = typing.NewType("StaticType", ctypes.c_uint64)

class DataObject:
  """The basic unit of data in a Project.

  Each object can be referenced (opened/loaded) from its ID, see `ObjectID`,
  `Project.read()` and `Project.edit()`.
  """
  # This corresponds to C++ type called mdf::deC_Object.

  def __init__(self, object_id: ObjectID, lock_type: LockType, *,
               rollback_on_error: bool = False):
    """Opens the object for read or read-write.

    It is recommended to go through `Project.read()` and `Project.edit()`
    instead of constructing this object directly.

    Parameters
    ----------
    object_id
      The ID of the object to open for read or read-write.
    lock_type
      Specify read/write operation intended for the
      lifespan of this object instance.
    rollback_on_error
      When true, changes should be rolled back if there is an error.
    """
    assert object_id
    self.__id: ObjectID = object_id
    self.__lock_type: LockType = lock_type
    self.__object_attributes = SingularDataPropertyReadOnly(
      "object_attributes",
      lambda: [lambda: self._lock.lock, self._data_engine_api()],
      _ObjectAttributeDictionary
    )
    self.__lock_opened = False
    self._lock: ReadLock | WriteLock = self.__begin_lock(rollback_on_error)
    self.__telemetry: TelemetryProtocol = get_telemetry()
    self.__record_object_type_telemetry(lock_type)

  @classmethod
  def _type_name(cls) -> str:
    return cls.__name__

  @classmethod
  def static_type(cls) -> StaticType:
    """Return this type as stored in a Project."""
    raise NotImplementedError(
      "Static type must be implemented on child classes.")

  @property
  def id(self) -> ObjectID[typing.Self]:
    """Object ID that uniquely references this object in the project.

    Returns
    -------
    ObjectID
      The unique id of this object.
    """
    return self.__id

  @property
  def closed(self) -> bool:
    """If this object has been closed.

    Attempting to read or edit a closed object will raise an ObjectClosedError.
    Such an error typically indicates an error in the script and should not
    be caught.

    Examples
    --------
    If the object was opened with the Project.new(), Project.edit() or
    Project.read() in a "with" block, this will be True until the with
    block is closed and False afterwards.

    >>> with project.new("cad/point_set", PointSet) as point_set:
    >>>     point_set.points = [[1, 2, 3], [4, 5, 6]]
    >>>     print("closed?", point_set.closed)
    >>> print("closed?", point_set.closed)
    closed? False
    closed? True
    """
    return self._lock.is_closed

  @property
  def is_read_only(self) -> bool:
    """If this object is read-only.

    This will return True if the object was open with Project.read()
    and False if it was open with Project.edit() or Project.new().
    Attempting to edit a read-only object will raise an error.
    """
    return self.lock_type is not LockType.READWRITE

  @property
  def lock_type(self) -> LockType:
    """Indicates whether operating in read-only or read-write mode.

    Use the is_read_only property instead for checking if an object
    is open for reading or editing.

    Returns
    -------
    LockType
      The type of lock on this object. This will be LockType.ReadWrite
      if the object is open for editing and LockType.Read if the object
      is open for reading.
    """
    return self.__lock_type

  @classmethod
  def _application_api(cls) -> MdfDlls:
    return get_application_dlls()

  @classmethod
  def _modelling_api(cls) -> ModellingApi:
    """Access the modelling C API."""
    return cls._application_api().modelling

  @classmethod
  def _data_engine_api(cls) -> DataEngineApi:
    """Access the DataEngine C API."""
    return cls._application_api().dataengine

  def _invalidate_properties(self):
    """Invalidates the properties of the object.

    The next time a property is requested, its values will be loaded from the
    project.
    """
    self._extra_invalidate_properties()

  def _extra_invalidate_properties(self):
    """Invalidate properties defined by the child class.

    This is called during _invalidate_properties() and should never
    be called directly.
    Child classes must implement this to invalidate the properties
    they define. They must not overwrite _invalidate_properties().
    """
    raise NotImplementedError(
      "_extra_invalidate_properties must be implemented on child classes"
    )

  # Child classes should place their child-specific function in _save()
  # instead of overwriting or overriding save().
  @typing.final
  def save(self) -> ChangeReasons:
    """Save the changes made to the object.

    Generally a user does not need to call this function, because it is called
    automatically at the end of a with block using Project.new() or
    Project.edit().

    Returns
    -------
    ChangeReasons
      The change reasons for the operation. This depends on what changes
      to the object were saved.
      If the api_version is less than 1.9, this always returns
      ChangeReasons.NO_CHANGE.
    """
    self._raise_if_save_in_read_only()
    self._save()
    self.__record_object_size_telemetry()
    self._invalidate_properties()
    return self._checkpoint()

  def _save(self):
    """Save the properties defined by the child class.

    This is called during save() and should never be called directly.
    Child classes must implement this to save the properties they define.
    They must not overwrite save().
    """
    raise NotImplementedError("_save() must be implemented on child classes")

  def close(self):
    """Closes the object.

    This should be called as soon as you are finished working with an object.
    To avoid needing to remember to call this function, open the object using
    a with block and project.read(), project.new() or project.edit().
    Those functions automatically call this function at the end of the with
    block.

    A closed object cannot be used for further reading or writing. The ID of
    a closed object may be queried and this can then be used to re-open the
    object.
    """
    if self.is_read_only and not self.closed:
      # If this object is open for read-only, record the size telemetry before
      # closing the object.
      # If the object is open for read-write, save() should have already
      # recorded the telemetry.
      self.__record_object_size_telemetry()
    self.__end_lock()

  def _checkpoint(self) -> ChangeReasons:
    """Checkpoint the saved changes to the object.

    This makes the changes to the object saved by save() visible to
    readers of the lock.
    """
    self._raise_if_read_only("Save changes")
    return ChangeReasons(self._data_engine_api().Checkpoint(self._lock.lock))

  def _raise_if_read_only(self, operation: str):
    """Raise a ReadOnlyError if this object is open for read-only.

    The message is: "Cannot {operation} in read-only mode".

    Parameters
    ----------
    operation
      The operation which cannot be done in read-only mode.
      This should not start with a capital letter and should describe
      what operation cannot be performed in read-only mode.

    Raises
    ------
    ReadOnlyError
      If this object is open for read-only.
    """
    if self.is_read_only:
      raise ReadOnlyError(f"Cannot {operation} in read-only mode.")

  def _raise_if_save_in_read_only(self):
    """Raise a CannotSaveInReadOnlyModeError if open for read-only.

    This should be called in the save() function of child classes.

    Raises
    ------
    CannotSaveInReadOnlyModeError
      If this object is open for read-only.
    """
    if self.is_read_only:
      error = CannotSaveInReadOnlyModeError()
      log.error(error)
      raise error

  def _record_function_call_telemetry(
    self,
    function_name: str,
    type_name: str | None=None
  ):
    """Records function call telemetry.

    Parameters
    ----------
    function_name
      The name of the function to record telemetry for.
    type_name
      The name of the type to record the function was called on.
      This is the name of the current class by default.
    """
    actual_name: str = type_name or self._type_name()
    self.__telemetry.record_function_call(f"{actual_name}.{function_name}")

  def _record_size_for(self, name: str, size: int):
    """Record object size telemetry for `name` with `size`.

    This will prefix the event with the name of the current class so that the
    caller does not need to do so.

    Parameters
    ----------
    name
      The type of size telemetry which is being recorded. For example, this
      could be "Points" if recording the point count of the object.
    size
      The size to record. No telemetry event will be recorded if it is zero
      or negative.
    """
    if size <= 0:
      return
    self.__telemetry.record_object_size(
      f"{self._type_name()}{name}",
      size
    )

  def _record_object_size_telemetry(self):
    """Record object-specific object size telemetry.

    Implementations should use `_record_size_for()` to record the relevant
    sizes for this object.
    """
    raise NotImplementedError

  def __record_object_size_telemetry(self):
    """Records the object size telemetry."""
    # pylint: disable=broad-exception-caught
    # An error when recording telemetry should not crash the program.
    try:
      self._record_object_size_telemetry()
    except Exception:
      log.exception(
        "Error while recording object size telemetry."
      )

  def __begin_lock(self, rollback_on_error: bool) -> ReadLock | WriteLock:
    if self.__lock_opened:
      raise AlreadyOpenedError(
        "This object has already been opened. After closing the object, you "
        "should start a new context manager using the with statement.")
    self.__lock_opened = True
    lock: ReadLock | WriteLock
    if self.__lock_type is LockType.READWRITE:
      lock = WriteLock(
        self.__id.handle,
        self._data_engine_api(),
        rollback_on_error=rollback_on_error
      )
      log.debug("Opened object for writing: %s of type %s",
                self.__id, self.__derived_type_name)
    else:
      lock = ReadLock(self.__id.handle, self._data_engine_api())
      log.debug("Opened object for reading: %s of type %s",
                self.__id, self.__derived_type_name)
    return lock

  def __end_lock(self):
    if not self.closed:
      self._lock.close()
      if self.__lock_type is LockType.READWRITE:
        log.debug("Closed object for writing: %s of type %s",
                  self.__id, self.__derived_type_name)
      else:
        log.debug("Closed object for reading: %s of type %s",
                  self.__id, self.__derived_type_name)

  def __enter__(self) -> typing.Self:
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    """Close the object. See close()"""
    self.close()

  @property
  def __derived_type_name(self) -> str:
    """Return qualified name of the derived object type."""
    return type(self).__qualname__

  def __repr__(self) -> str:
    return f'{self.__derived_type_name}({self.__id})'

  # =========================================================================
  # Properties of the underlying object in the project.
  # =========================================================================

  @property
  def created_date(self) -> datetime.datetime:
    """The date and time (in UTC) of when this object was created.

    Returns
    -------
    datetime.datetime:
      The date and time the object was created.
      0:0:0 1/1/1970 if the operation failed.
    """
    value = ctypes.c_int64() # value provided in microseconds
    success = self._data_engine_api().GetObjectCreationDateTime(
      self._lock.lock, ctypes.byref(value))
    if success:
      try:
        return datetime.datetime.fromtimestamp(float(value.value) / 1000000,
                                               datetime.timezone.utc).replace(
                                                 tzinfo=None)
      except (OSError, OverflowError) as error:
        message = str(error)
    else:
      message = self._data_engine_api().ErrorMessage()

    log.warning(
      'Failed to determine the creation date of object %s because %s',
      self.id, message)
    return datetime.datetime.fromtimestamp(0, datetime.timezone.utc).replace(
      tzinfo=None)

  @property
  def modified_date(self) -> datetime.datetime:
    """The date and time (in UTC) of when this object was last modified.

    Returns
    -------
    datetime.datetime
      The date and time this object was last modified.
      0:0:0 1/1/1970 if the operation failed.
    """
    value = ctypes.c_int64() # value provided in microseconds
    success = self._data_engine_api().GetObjectModificationDateTime(
      self._lock.lock, ctypes.byref(value))
    if success:
      return datetime.datetime.fromtimestamp(float(value.value) / 1000000,
                                             datetime.timezone.utc).replace(
                                               tzinfo=None)

    message = self._data_engine_api().ErrorMessage()
    log.warning(
      'Failed to determine the last modified date of object %s because %s',
      self.id, message)
    return datetime.datetime.fromtimestamp(0, datetime.timezone.utc).replace(
      tzinfo=None)

  @property
  def _revision_number(self) -> int:
    """The revision number of the object.

    This is incremented when save() is called or when the object is closed
    by project.edit() (assuming a change was made).

    If the application is too old to support this, the revision number
    will always be zero.

    Warnings
    --------
    The revision number is not stored persistently. If a maptekdb is
    closed and reopened, the revision number for each object will reset
    to one.
    """
    return self._data_engine_api().GetObjectRevisionNumber(self._lock.lock) or 0

  @property
  def _object_attributes(self) -> _ObjectAttributeDictionary:
    """Property for accessing the object attributes.

    When first called, the names of all object attributes are cached.
    """
    return self.__object_attributes.value

  @typing.overload
  def set_attribute(
      self,
      name: str,
      dtype: type[datetime.date],
      data: datetime.date | tuple[float, float, float]):
    ...

  @typing.overload
  def set_attribute(
      self,
      name: str,
      dtype: type[datetime.datetime],
      data: datetime.datetime | str):
    ...

  @typing.overload
  def set_attribute(
      self,
      name: str,
      dtype: type[bool],
      data: bool):
    ...

  @typing.overload
  def set_attribute(
      self,
      name: str,
      dtype: type[int],
      data: int):
    ...

  @typing.overload
  def set_attribute(
      self,
      name: str,
      dtype: type[float],
      data: float):
    ...

  @typing.overload
  def set_attribute(
      self,
      name: str,
      dtype: type[str],
      data: str):
    ...

  @typing.overload
  def set_attribute(
      self,
      name: str,
      dtype: ObjectAttributeDataTypes,
      data: ObjectAttributeTypesWithAlias):
    ...

  def set_attribute(
      self,
      name: str,
      dtype: ObjectAttributeDataTypes | type[
        datetime.datetime | datetime.date | bool |
        int | float | str],
      data: typing.Any):
    """Sets the value for the object attribute with the specified name.

    This will overwrite any existing attribute with the specified name.

    Parameters
    ----------
    name
      The name of the object attribute for which the value should be set.
    dtype
      The type of data to assign to the attribute. This should be
      a type from the ctypes module or datetime.datetime or datetime.date.
      Passing bool is equivalent to passing ctypes.c_bool.
      Passing str is equivalent to passing ctypes.c_char_p.
      Passing int is equivalent to passing ctypes.c_int16.
      Passing float is equivalent to passing ctypes.c_double.
    data
      The value to assign to object attribute `name`.
      For `dtype` = datetime.datetime this can either be a datetime
      object or timestamp which will be passed directly to
      datetime.fromtimestamp().
      For `dtype` = datetime.date this can either be a date object or a
      tuple of the form: (year, month, day).

    Raises
    ------
    ValueError
      If `dtype` is an unsupported type.
    TypeError
      If `value` is an inappropriate type for object attribute `name`.
    ValueError
      If `name` starts or ends with whitespace or is empty.
    RuntimeError
      If a different error occurs.

    Notes
    -----
    If an error occurs after adding a new object attribute or editing
    an existing object attribute resulting in save() not being called,
    the changes to the object attributes can only be undone if
    the application's API version is 1.6 or greater.

    Prior to mapteksdk 1.6:
    Adding new object attributes, or editing the values of object
    attributes, will not be undone if an error occurs.

    Examples
    --------
    Create an object attribute on an object at "target" and then read its
    value.

    >>> import ctypes
    >>> from mapteksdk.project import Project
    >>> project = Project()
    >>> with project.edit("target") as edit_object:
    ...     edit_object.set_attribute("count", ctypes.c_int16, 0)
    ... with project.read("target") as read_object:
    ...     print(read_object.get_attribute("count"))
    0
    """
    self._raise_if_read_only("set object attributes")

    actual_dtype: ObjectAttributeDataTypes
    if dtype is bool:
      actual_dtype = ctypes.c_bool
    elif dtype is str:
      actual_dtype = ctypes.c_char_p
    elif dtype is int:
      actual_dtype = ctypes.c_int16
    elif dtype is float:
      actual_dtype = ctypes.c_double
    else:
      # Pylance is only type narrowing on the if and ignoring the intermediate
      # elif blocks resulting in a false positive for static type checking here.
      actual_dtype = dtype # type: ignore

    if (actual_dtype is datetime.datetime
        and not isinstance(data, datetime.datetime)):
      data = datetime.datetime.fromtimestamp(data, datetime.timezone.utc)
      data = data.replace(tzinfo=None)  # Remove timezone awareness.

    if actual_dtype is datetime.date and not isinstance(data, datetime.date):
      data = datetime.date(data[0], data[1], data[2])

    self._object_attributes.create(name, actual_dtype, data)
    telemetry_event = data_type_to_string(actual_dtype)
    self._record_function_call_telemetry(
      f"set_attribute_{telemetry_event}",
      "DataObject"
    )

  def attribute_names(self) -> list[str]:
    """Returns a list containing the names of all object-level attributes.

    Use this to iterate over the object attributes.

    Returns
    -------
    list
      List containing the attribute names.

    Examples
    --------
    Iterate over all object attributes of the object stared at "target"
    and print their values.

    >>> from mapteksdk.project import Project
    >>> project = Project()
    >>> with project.read("target") as read_object:
    ...     for name in read_object.attribute_names():
    ...         print(name, ":", read_object.get_attribute(name))
    """
    return list(self._object_attributes.names())

  def get_attribute(self, name: str) -> ObjectAttributeTypes:
    """Returns the value for the attribute with the specified name.

    Parameters
    ----------
    name
      The name of the object attribute to get the value for.

    Returns
    -------
    ObjectAttributeTypes
      The value of the object attribute `name`.
      For `dtype` = datetime.datetime this is an integer representing
      the number of milliseconds since 1st Jan 1970.
      For `dtype` = datetime.date this is a tuple of the form:
      (year, month, day).

    Raises
    ------
    KeyError
      If there is no object attribute called `name`.

    Warnings
    --------
    In the future this function may be changed to return datetime.datetime
    and datetime.date objects instead of the current representation for
    object attributes of type datetime.datetime or datetime.date.
    """
    attribute = self._object_attributes[name]
    telemetry_event = data_type_to_string(attribute.dtype)
    self._record_function_call_telemetry(
      f"get_attribute_{telemetry_event}",
      "DataObject"
    )
    return self._object_attributes[name].value

  def get_attribute_type(self, name: str) -> ObjectAttributeDataTypes:
    """Returns the type of the attribute with the specified name.

    Parameters
    ----------
    name
      Name of the attribute whose type should be returned.

    Returns
    -------
    ObjectAttributeDataTypes
      The type of the object attribute `name`.

    Raises
    ------
    KeyError
      If there is no object attribute called `name`.
    """
    return self._object_attributes[name].dtype

  def delete_all_attributes(self):
    """Delete all object attributes attached to an object.

    This only deletes object attributes and has no effect
    on PrimitiveAttributes.

    Raises
    ------
    RuntimeError
      If all attributes cannot be deleted.
    """
    self._raise_if_read_only("delete all object attributes")
    self._record_function_call_telemetry(
      "delete_all_attributes",
      "DataObject"
    )
    self._object_attributes.delete_all()

  def delete_attribute(self, attribute: str) -> bool:
    """Deletes a single object-level attribute.

    Deleting a non-existent object attribute will not raise an error.

    Parameters
    ----------
    attribute : str
      Name of attribute to delete.

    Returns
    -------
    bool
      True if the object attribute existed and was deleted;
      False if the object attribute did not exist.

    Raises
    ------
    RuntimeError
      If the attribute cannot be deleted.
    """
    self._raise_if_read_only("delete object attributes")
    self._record_function_call_telemetry(
      "delete_attribute",
      "DataObject"
    )
    return self._object_attributes.delete(attribute)

  def __record_object_type_telemetry(self, lock_type: LockType):
    """Records telemetry for this object type being opened."""
    mode = "unknown"
    if lock_type is LockType.READ:
      mode = "read"
    elif lock_type is LockType.READWRITE:
      mode = "edit"

    self._record_function_call_telemetry(mode)
