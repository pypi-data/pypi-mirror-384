"""The ObjectID class.

An ObjectID uniquely references an object within a Project. Note that an
ObjectID is only unique within one Project - an ObjectID of an object in one
project may be the ID of a different object in a different project.
Attempting to use an ObjectID once the project has been closed (or before
it has been opened) will raise an error.

"""
###############################################################################
#
# (C) Copyright 2020, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

from collections.abc import Iterable
import ctypes
import typing

from ..capi.util import get_string, CApiDllLoadFailureError
from ..capi.types import T_ObjectHandle
from ..capi import DataEngine, DataEngineApi
from ..internal.comms import Int64u
from ..internal.util import default_type_error_message

if typing.TYPE_CHECKING:
  from ..capi.types import T_NodePathHandle
  from ..data.base import DataObject, StaticType

T_co = typing.TypeVar("T_co", covariant=True)

class ObjectID(typing.Generic[T_co]):
  """ObjectID used to identify and represent an object.

  There is a special value an Object ID can represent called the null object ID.
  The null object ID is considered False and other values are considered True.

  This object is generic for the purposes of typing hinting but not during
  run-time. It is possible for the type of the object an ObjectID represents to
  change or for the type hint to be incorrect.
  e.g. Type hinting an object id as ObjectID[Surface] only tells your code
  editor to provide autocomplete suggestions as if it were the ObjectID
  of a Surface. When the code is run, it does not check that it is the
  ObjectID of a Surface. To check the actual type of an ObjectID, use
  ObjectID.is_a() instead.

  Examples
  --------
  Test if an object ID is the null object ID or not.

  >>> def test_object_id(object_id: ObjectID):
  ...     if object_id:
  ...         print("Object ID is not the null object ID.")
  ...     else:
  ...         print("The given object ID is null")
  """
  # Specifies the underlying storage type of this class for the communication
  # system.
  storage_type = Int64u

  def __init__(self, handle=None):
    if handle is None:
      self.__handle = T_ObjectHandle(0)
    elif isinstance(handle, T_ObjectHandle):
      self.__handle = handle
    else:
      raise TypeError(
        default_type_error_message(
          argument_name="handle",
          actual_value=handle,
          required_type=T_ObjectHandle
        ))

  @classmethod
  def convert_from(cls, value: int):
    """Convert from the underlying value (of storage type) to this type.

    This is used by the communication system.
    """
    return cls(T_ObjectHandle(value))

  def convert_to(self) -> int:
    """Convert to the underlying value.

    This is used by the communication system.
    """
    return self.handle.value

  @classmethod
  def _from_string(cls, oid_string: str):
    """Constructs an ObjectID instance from a valid Object ID string.

    This is a string of the form of 'OID(I##, C##, T##)'
    (e.g. 'OID(I123, C33, T22)').
    Newer applications no longer have the type index in the object ID
    and the ObjectID string will be of the form 'OID(I##, C##)'.

    This method relies on a valid object existing in the Project.
    for the string passed into this method.

    Parameters
    ----------
    oid_string : str
      Object ID string in the form of 'OID(I##, C##, T##)' or 'OID(I##, C##)'.

    Returns
    -------
    ObjectID
      An ObjectID instance.

    Raises
    ------
    TypeError
      If the oid_string parameter is not a string.
    ValueError
      If oid_string is not in form 'OID(I##, C##, T##)' or 'OID(I##, C##)'.
    ValueError
      If oid_string fails to convert to an ObjectID.
    """
    if isinstance(oid_string, str):
      obj = T_ObjectHandle()
      try:
        success = cls._data_engine_api().ObjectHandleFromString(
          oid_string.encode("utf-8"),
          obj)
      except CApiDllLoadFailureError as error:
        raise CApiDllLoadFailureError(
          "Failed to parse ObjectID because no project is connected."
          ) from error
      if not success or obj is None or obj.value == 0:
        raise ValueError(f"'{oid_string}' failed to convert to an ObjectID.")
      return cls(obj)
    raise TypeError(
      default_type_error_message(
        argument_name="oid_string",
        actual_value=oid_string,
        required_type=str
      ))

  @classmethod
  def from_path(cls, object_path: str) -> typing.Self:
    """Constructs an ObjectID instance from a valid object path string.

    This method relies on a valid object existing in the Project
    at the path passed into this method.

    Parameters
    ----------
    object_path : str
      Path to the object to get the ID of.

    Returns
    -------
    ObjectID
      An ObjectID instance if the string was valid.

    Raises
    ------
    TypeError
      If the object_path parameter is not a string.
    ValueError
      If object_path failed to convert to an ObjectID.
    """
    if isinstance(object_path, str):
      obj = T_ObjectHandle()
      try:
        node_path_handle = cls._data_engine_api().NodePathFromString(
          object_path.encode("utf-8"))
      except CApiDllLoadFailureError as error:
        raise CApiDllLoadFailureError(
            "Failed to parse ObjectID because no project is connected."
            ) from error
      if node_path_handle.value > 0:
        success = cls._data_engine_api().ObjectHandleFromNodePath(
          node_path_handle,
          obj)
        if success and obj.value > 0:
          return cls(obj)
        raise ValueError(
          "Failed to create an ObjectID from path "
          f"'{object_path}'. The path doesn't exist.")
      raise ValueError(
        f"Failed to create an ObjectID from path '{object_path}'.")
    raise TypeError(
      default_type_error_message(
        argument_name="object_path",
        actual_value=object_path,
        required_type=str
      )
    )

  def __str__(self):
    return (repr(self)) if self.handle else "Undefined"

  def __repr__(self):
    """Converts to a string presentation in the form of 'OID(I##, C##, T##)'

    This is where:
    OID = Object ID.
    "I" = Object Index, "C" = Object Index Counter, "T" = Type Index.

    For newer applications there is no type index so this will be of the form:
    'OID(I##, C##)'
    """
    raw_handle = self.native_handle
    object_index = raw_handle & 0xFFFFFFFF
    if self._data_engine_api().version < (1, 4):
      object_index_counter = (raw_handle >> 32) & 0xFFFF
      type_index = (raw_handle >> 48) & 0xFFFF
      return f'OID(I{object_index}, C{object_index_counter}, T{type_index})'
    object_index_counter = (raw_handle >> 32) & 0xFFFFFFFF
    return f'OID(I{object_index}, C{object_index_counter})'

  def __eq__(self, obj):
    return isinstance(obj, ObjectID) and obj.native_handle == self.native_handle

  def __int__(self):
    return self.native_handle

  def __bool__(self):
    return self.native_handle > 0

  def __hash__(self) -> int:
    return self.native_handle.__hash__()

  @staticmethod
  def _data_engine_api() -> DataEngineApi:
    """Access the DataEngine C API."""
    return DataEngine()

  @property
  def handle(self) -> T_ObjectHandle:
    """T_ObjectHandle representation of the Object ID.

    Returns
    -------
    T_ObjectHandle
      This handle represents the Object ID.
    """
    return self.__handle

  @property
  def native_handle(self) -> int:
    """Native Integer (uint64) representation of the Object ID.

    Returns
    -------
    int
      uint64 representation of the Object ID.
    """
    return self.__handle.value

  @property
  def icon_name(self) -> str:
    """The name of the icon that represents the object.

    Returns
    -------
    str
      Icon name for the object type.

    Raises
    ------
    TypeError
      If the ObjectID refers to the null object ID.
    """
    self.__check_handle()
    return get_string(self.__handle,
                      self._data_engine_api().ObjectHandleIcon) or ""

  @property
  def type_name(self) -> str:
    """The type name of this object.

    This name is for diagnostics purposes only. Do not use it to alter the
    behaviour of your code. If you wish to check if an object is of a given
    type, use is_a() instead.

    Returns
    -------
    str
      The name of the type of the given object.

    Raises
    ------
    TypeError
      If the ObjectID refers to the null object ID.

    See Also
    --------
    is_a : Check if the type of an object is the expected type.
    """

    self.__check_handle()
    dynamic_type = self._data_engine_api().ObjectDynamicType(self.__handle)
    raw_type_name: str = self._data_engine_api().TypeName(
      dynamic_type).decode('utf-8')

    # Tidy up certain names for users of the Python SDK.
    raw_to_friendly_name = {
      '3DContainer': 'VisualContainer',
      '3DEdgeChain': 'Polyline',
      '3DEdgeNetwork': 'EdgeNetwork',
      '3DFacetNetwork': 'Surface',
      '3DNonBrowseableContainer': 'NonBrowseableContainer',
      '3DPointSet': 'PointSet',
      'BlockNetworkDenseRegular': 'DenseBlockModel',
      'BlockNetworkDenseSubblocked': 'SubblockedBlockModel',
      'ColourMapNumeric1D': 'NumericColourMap',
      'ColourMapString1D': 'StringColourMap',
      'EdgeLoop': 'Polygon',
      'RangeImage': 'Scan',
      'StandardContainer': 'StandardContainer',
      'TangentPlane': 'Discontinuity',
    }

    # Exclude the old (and obsolete) revision number.
    raw_type_name = raw_type_name.partition('_r')[0]

    return raw_to_friendly_name.get(raw_type_name, raw_type_name)

  @property
  def exists(self) -> bool:
    """If the object associated with this object id exists.

    This can be used to check if a previously existing object
    has been deleted or if the parameters used to create the ObjectID
    instance are valid and refer to an existing object.

    Returns
    -------
    bool
      True if it exists; False if it no longer exists.
      False is also returned if ObjectID never existed.
    """
    return self._data_engine_api().ObjectHandleExists(self.__handle) \
      if self.native_handle else False

  @property
  def name(self) -> str:
    """The name of the object (if one exists).

    If the object is not inside a container then it won't have a name. The
    name comes from its parent.
    If the object is inside more than one container (has multiple paths)
    then this is the name in the primary container.
    Each container that this object is in can assign it a different name.

    Returns
    -------
    str
      The name of the object.

    Raises
    ------
    TypeError
      If the ObjectID is the null object ID.
    """
    self.__check_handle()
    path_handle = self.__node_path_handle
    return get_string(path_handle, self._data_engine_api().NodePathLeaf) or ""

  @property
  def path(self) -> str:
    """The path to the object (if one exists) in the project.

    If an object has multiple paths, the primary path will be returned.

    Returns
    -------
    str
      Path to the object if one exists (e.g. '/cad/my_object').

    Raises
    ------
    TypeError
      If the ObjectID is the null object ID.
    """
    self.__check_handle()
    path_handle = self.__node_path_handle
    return get_string(path_handle,
                      self._data_engine_api().NodePathToString) or ""

  @property
  def hidden(self) -> bool:
    """If the object is a hidden object.

    Returns
    -------
    bool
      True if hidden, False if not hidden.

    Raises
    ------
    TypeError
      If the ObjectID is the null object ID. An object that doesn't exist is
      not hidden but it is also not hidden.
    """
    # Exception will be raised when checking path if handle is None
    path = self.path
    parts = path.strip("/").split("/")
    # Remove empty strings (e.g. /surfaces/ = '', surfaces, '')
    parts = list(filter(None, parts))
    return any(part.startswith('.') for part in parts)

  @property
  def parent(self) -> typing.Self:
    """The ObjectID of the primary parent of this object.

    Returns
    -------
    ObjectID
      ObjectID instance representing the parent of this object.

    Raises
    ------
    TypeError
      If the ObjectID handle is None.

    Notes
    -----
    If this object is already the root, the same object will
    be returned.
    If this object has multiple parents, the primary parent
    will be returned.
    """
    self.__check_handle()
    return type(self)(self._data_engine_api().ObjectParentId(self.__handle))

  @property
  def is_orphan(self) -> bool:
    """Check if object is an orphan.

    An orphan is an object which is not in a container or is in a container
    which is an orphan.

    Returns
    -------
    bool
      True if the object is an orphan or False if it is not.

    Raises
    ------
    TypeError
      If the ObjectID handle is None.
    """
    self.__check_handle()
    return self._data_engine_api().ObjectHandleIsOrphan(self.__handle)

  @property
  def _revision_number(self) -> int | None:
    """Returns the revision number of the object.

    This allows the revision number to be queried without opening the object.

    See Also
    --------
    DataObject._revision_number : A detailed explanation of revision numbers.
    """
    return self._data_engine_api().GetObjectIdRevisionNumber(self.handle)

  def is_a(
    self,
    object_type: (
      type[DataObject]
      | tuple[type[DataObject], ...]
      | StaticType |
      tuple[StaticType]
    )
  ) -> bool:
    """Check if this object ID represents an object of the given type.

    This allows for checking the type of an object without opening it.

    This takes into account inheritance. For example, for a Polygon object
    this function will return True if object type is Polygon or Topology because
    Polygon is a child class of Topology.

    Parameters
    ----------
    object_type
      The Python class to check if this object ID represents an object of this
      type (or any subclass of this type) or a tuple of classes to check.

    Returns
    -------
    bool
      True if the object referenced by this object ID is of the type (or any
      subclass of) object_type otherwise False.
      If object_type is a tuple of types, then True if the object referenced
      by this object ID is any of the types in the tuple otherwise False.

    Raises
    ------
    TypeError
      If the argument is not a type of object or a tuple of object types.

    Examples
    --------
    The following example demonstrates is_a() for the object id of a Polygon
    object.

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import Polygon, Topology, Surface
    >>> with Project() as project:
    ...     with project.new("cad/test_polygon", Polygon) as polygon:
    ...         polygon.points = [[0, 0, 0], [0, 1, 0], [0, 1, -1], [0, 0, -1]]
    ...     polygon_id = polygon.id
    ...     print("Polygon is a Polygon?", polygon_id.is_a(Polygon))
    ...     print("Polygon is a Topology?", polygon_id.is_a(Topology))
    ...     print("Polygon is a Surface?", polygon_id.is_a(Surface))
    ...     # Specifying a tuple of types allows for checking if the object
    ...     # is any of those types.
    ...     print(
    ...         "Polygon is a Polygon or Surface?",
    ...          polygon_id.is_a((Polygon, Surface)))
    Polygon is a Polygon? True
    Polygon is a Topology? True
    Polygon is a Surface? False
    Polygon is a Polygon or Surface? True
    """
    self.__check_handle()

    dynamic_type = self._data_engine_api().ObjectDynamicType(self.__handle)

    # Support both the object type directly or a class/object which has a
    # static_type function. The latter should be favoured.
    def _static_type(object_type):
      return getattr(object_type, 'static_type', lambda: object_type)()

    if not isinstance(object_type, Iterable):
      object_types = [object_type]
    else:
      object_types = object_type

    for individual_type in object_types:
      try:
        result = self._data_engine_api().TypeIsA(
          dynamic_type, _static_type(individual_type))
      except CApiDllLoadFailureError:
        # Failed to load the DLL the type is in. It must not be this type,
        # so move onto the next type.
        continue
      except ctypes.ArgumentError as error:
        raise TypeError(
          "is_a must be provided an object type, a class with static_type "
          f"property, or tuple, not '{object_type}'") from error
      if result:
        return True
    return False

  def _is_exactly_a(self, object_type: type[DataObject] | StaticType) -> bool:
    """Return True if type of the object is exactly the specified type.

    Unlike is_a(), this does not take into account inheritance.

    Parameters
    ----------
    object_type
      The Python class to check if this object ID represents an object of this
      type.

    Returns
    -------
    bool
      True if the object referenced by this object ID is of the type
      object_type otherwise False.

    Raises
    ------
    TypeError
      If the argument is not a type of object.

    Examples
    --------
    ObjectID.is_a() will return True if the object is a subclass of the
    specified class. This means that:

    >>> object_id.is_a(Topology)

    will return True for almost all object IDs because almost all objects
    inherit from topology (the main exceptions are colour maps and containers).
    On the other hand:

    >>> object_id._is_exactly_a(Topology)

    will always return False, because no object is exactly a Topology. Most
    are subclasses of Topology, but no object in a project will be exactly a
    Topology. The following example demonstrates the differences between is_a()
    and _is_exactly_a() for Polygon, a type which like many others inherits from
    Topology.

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import Polygon, Topology
    >>> with Project() as project:
    ...     with project.new("cad/test_polygon", Polygon) as polygon:
    ...         polygon.points = [[0, 0, 0], [0, 1, 0], [0, 1, -1], [0, 0, -1]]
    ...     polygon_id = polygon.id
    ...     print("Polygon is a Polygon?", polygon_id.is_a(Polygon))
    ...     print("Polygon is a Topology?", polygon_id.is_a(Topology))
    ...     print(
    ...         "Polygon is exactly a Polygon?",
    ...         polygon_id._is_exactly_a(Polygon))
    ...     print(
    ...         "Polygon is exactly a Topology?",
    ...         polygon_id._is_exactly_a(Topology))
    Polygon is a Polygon? True
    Polygon is a Topology? True
    Polygon is exactly a Polygon? True
    Polygon is exactly a Topology? False
    """
    self.__check_handle()

    dynamic_type = self._data_engine_api().ObjectDynamicType(self.__handle)

    # Support both the object type directly or a class/object which has a
    # static_type function. The latter should be favoured.
    def _static_type(object_type):
      return getattr(object_type, 'static_type', lambda: object_type)()

    static_type = _static_type(object_type)
    try:
      return dynamic_type.value == static_type.value
    except AttributeError:
      raise TypeError(
        "_is_exactly_a must be provided an object type or a class with "
        f"static_type property, not '{object_type}'") from None

  @property
  def __node_path_handle(self) -> T_NodePathHandle:
    """Get the node path (as a T_NodePathHandle) for the object.

    Notes
    -----
    If the object has been appended to the project more than
    once this may not return the first occurrence.
    """
    return self._data_engine_api().ObjectHandleNodePath(self.__handle)

  def __check_handle(self):
    """Check if the handle of this ObjectID is valid.

    Raises a TypeError if the handle is invalid.
    """
    is_a_handle = isinstance(self.__handle, T_ObjectHandle)
    if not is_a_handle:
      # This is not the user's of the SDK problem unless they have been been
      # messing with the internals.
      raise TypeError("ObjectID's handle is not a T_ObjectHandle.")

    if self.__handle.value == 0:
      # Ideally this would raise a ValueError, prior it to 1.5, it was treated
      # as if the handle was as a different type (None). Changing it would
      # break compatibility with old scripts expecting a TypeError.
      raise TypeError("ObjectID is null.")
