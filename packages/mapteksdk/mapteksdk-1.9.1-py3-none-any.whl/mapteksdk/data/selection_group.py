"""The selection group data type."""
###############################################################################
#
# (C) Copyright 2025, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

from collections.abc import Iterable
import enum
import typing

from .objectid import ObjectID
from .base import DataObject
from .containers import Container, VisualContainer
from ..capi.util import CApiDllLoadFailureError
from ..internal.lock import LockType
from ..internal.unique_name import unique_name
from ..internal.util import default_type_error_message

if typing.TYPE_CHECKING:
  from collections.abc import Sequence

  from .base.data_object import StaticType
  from ..capi import SelectionApi


class _Unsupported:
  """Sentinel value used to detect when drillholes are not supported."""


class SelectionGroupTypeNotSupportedError(ValueError):
  """Error raised if the selection group type is not supported."""


class GroupCannotContainObjectError(ValueError):
  """Error raised if the selection group cannot contain an object."""
  def __init__(self, group_type: _SelectionGroupType, oid: ObjectID) -> None:
    super().__init__(
      f"Cannot add objects of type: {oid.type_name} to selection group "
      f"of type {group_type}"
    )
    self.group_type = group_type
    """The group type which triggered this error."""
    self.oid = oid
    """The Object ID of the object which could not be part of the group."""


class _SelectionGroupType(enum.Enum):
  """Enum indicating the type of objects stored in a selection group."""
  UNDEFINED = 0
  """The selection group type is undefined."""
  DRILLHOLE = 1
  """The selection group can only contain drillholes.

  Warnings
  --------
  This group type only works when the script is connected to GeologyCore.
  Other applications can't operate on drillholes and any attempt to
  add objects to such a group will fail (including attempts to add a drillhole
  to the group).
  Note that the blast holes in BlastLogic are not considered drillholes for
  the purposes of this group type.
  """
  MIXED = 2
  """The selection group can contain any object."""
  FUTURE = 255
  """The selection group type is not supported by the SDK.

  The selection group can be read, but not edited.
  """

  @classmethod
  def from_index(cls, index: int) -> _SelectionGroupType:
    """Construct a selection group type from the index.

    If the index is not supported, this will return SelectionGroupType.FUTURE.
    """
    try:
      return cls(index)
    except ValueError:
      return cls.FUTURE

  def is_supported(self) -> bool:
    """True if this group type is supported by mapteksdk."""
    return self in (_SelectionGroupType.DRILLHOLE, _SelectionGroupType.MIXED)


class _SelectionGroup(DataObject):
  """A selection which has been saved into the Project.

  These can be selected in the explorer to automatically select the objects in
  the selection group.
  """
  def __init__(
    self,
    object_id: ObjectID | None = None,
    lock_type: LockType = LockType.READWRITE,
    *,
    rollback_on_error: bool = False
  ):
    is_new = False
    if not object_id:
      object_id = ObjectID(
        self._data_engine_api().NewObject(self.static_type()) # type: ignore
      )
      is_new = True

    super().__init__(object_id, lock_type, rollback_on_error=rollback_on_error)
    self.__contents: dict[str, ObjectID] | None = None
    """Cached copy of the contents of the selection.

    When editing this class, one must be careful to ensure this remains
    synced with the contents in the application.
    """
    self.__drillhole_static_type: StaticType | _Unsupported | None  = None
    """The static type of drillholes.

    Access this through self._drillhole_static_type() instead.
    This will be None if this has not been queried.
    """

    if is_new:
      self._group_type = _SelectionGroupType.MIXED
      self.__contents = {}
      self._save_group_type(self._group_type)
    else:
      self._group_type = _SelectionGroupType.from_index(
        self._selection_api().GetSelectionGroupContextType(self._lock.lock)
      )

  @classmethod
  def _selection_api(cls) -> SelectionApi:
    return cls._application_api().selection

  @classmethod
  def _type_name(cls) -> str:
    # Record the telemetry as "SelectionGroup" instead of "_SelectionGroup".
    return "SelectionGroup"

  @classmethod
  def static_type(cls) -> StaticType:
    return cls._selection_api().GroupType() # type: ignore

  def _save(self):
    # SelectionGroup does not cache any of its properties, so there is nothing
    # to do during save.
    # As this class does not use potentially large NumPy arrays, there is no
    # need for caching.
    pass

  def _extra_invalidate_properties(self):
    self.__contents = None

  def _record_object_size_telemetry(self):
    length = self._data_engine_api().ContainerElementCount(self._lock.lock)
    self._record_size_for("Length", length)

  def _save_group_type(self, group_type: _SelectionGroupType):
    """Save the selection group type."""
    self._selection_api().SetSelectionGroupContextType(
        self._lock.lock,
        group_type.value
      )

  def _drillhole_static_type(self) -> StaticType | _Unsupported:
    """The static type for drillholes.

    This does not use `ObjectID.is_a(Drillhole)` because the `geologycore`
    package depends on `data`, so the `data` package cannot use classes
    defined in `geologycore` without introducing a circular dependency.
    """
    drillhole_static_type = self.__drillhole_static_type
    if drillhole_static_type is None:
      try:
        drillhole_static_type = (
          self._application_api().drillhole_model.DrillholeType()
        )
      except CApiDllLoadFailureError:
        # This must not throw exceptions to avoid the script crashing when not
        # connected to GeologyCore.
        drillhole_static_type = _Unsupported()
      self.__drillhole_static_type = drillhole_static_type
    return drillhole_static_type

  def _is_a_drillhole(self, oid: ObjectID) -> bool:
    """True if the object ID is a drillhole.

    When not connected to GeologyCore, this will always return False.
    """
    drillhole_static_type = self._drillhole_static_type()
    if isinstance(drillhole_static_type, _Unsupported):
      return False

    return oid.is_a(drillhole_static_type)

  def _can_change_group_type_to(self, new_type: _SelectionGroupType) -> bool:
    if not new_type.is_supported():
      return False
    if new_type is _SelectionGroupType.DRILLHOLE and isinstance(
      self._drillhole_static_type(), _Unsupported
    ):
      return False
    return True

  def __raise_if_oid_is_invalid(self, object_id: ObjectID):
    """Raises an error if `object_id` cannot be added to the selection."""
    if not isinstance(object_id, ObjectID):
      raise TypeError(
        default_type_error_message(
          "oid",
          object_id,
          ObjectID
        )
      )

    if not object_id:
      raise ValueError("Cannot add null object ID to the selection.")

    # SelectionGroups only have non-primary parents, so the object ID must
    # have a primary parent.
    if not object_id.parent:
      raise ValueError("Cannot add orphan object to the selection group.")

  def __add(self, name: str, oid: ObjectID):
    """Add an item to the selection group."""
    contents = self._contents

    if oid in contents.values():
      # The Object ID is already in the group.
      # Note that this can't be done via name, as the name of the object
      # in the selection group may not match the primary name.
      # This occurs if the object was added to the selection group and then
      # its primary name was changed, as in this case the secondary name will
      # not be updated to match.
      return

    name = unique_name(
      name,
      lambda potential_name: potential_name in contents
    )

    self._data_engine_api().ContainerAppend(
      self._lock.lock,
      name,
      oid.handle,
      force_primary_parenting=False
    )
    self._contents[name] = oid

  def __is_a_container(
    self,
    oid: ObjectID[DataObject]
  ) -> typing.TypeGuard[ObjectID[Container]]:
    """Type guard which indicates that an OID is a container.

    `oid.is_a(Container)` will return True for almost all objects, as almost
    all objects are non-browsable containers. This returns true if an object
    is a browsable container.
    """
    # pylint: disable=protected-access
    if oid._is_exactly_a(Container):
      return True
    # Note that a SelectionGroup is a VisualContainer on the C++ side,
    # so this returns true for them as well.
    if oid.is_a(VisualContainer):
      return True
    return False

  def __can_include_oid(self, oid: ObjectID) -> bool:
    """True if `oid` can be added to this group."""
    if self.group_type is _SelectionGroupType.MIXED:
      return not oid.is_a(VisualContainer)
    if self.group_type is _SelectionGroupType.DRILLHOLE:
      return self._is_a_drillhole(oid)
    # Cannot add to a group type Python doesn't know how to handle.
    return False

  def _remove_unsupported_objects(self):
    """Remove all unsupported objects for the current group type."""
    contents = self.contents
    for oid in contents:
      if not self.__can_include_oid(oid):
        self.remove(oid)

  @property
  def _contents(self) -> dict[str, ObjectID]:
    """The names and object IDs of the objects in the selection.

    The name of any item in the selection may not match the object id's
    primary name if the object was renamed since being added to the selection.
    """
    if self.__contents is None:
      contents = self._data_engine_api().GetContainerContents(self._lock.lock)
      self.__contents = {
        name : ObjectID(handle) for name, handle in contents
      }
    return self.__contents

  @property
  def contents(self) -> Sequence[ObjectID]:
    """The Object IDs of the objects in this selection group.

    If this has the DRILLHOLE group_type, this may be a stale selection of
    drillholes if the drillhole database or selection files have been edited
    since this selection group has been updated.
    """
    return tuple(self._contents.values())

  @property
  def group_type(self) -> _SelectionGroupType:
    """The type of this selection group."""
    return self._group_type

  def change_group_type(self, new_type: _SelectionGroupType):
    """Change the group type to `new_type`.

    This will remove any unsupported objects from the selection group.
    For example, changing the group type to `SelectionGroupType.Drillhole`
    will remove all non-drillhole objects from the group.

    Raises
    ------
    SelectionGroupTypeNotSupportedError
      If changing the group type to `new_type` is not supported. This will
      always be raised for `SelectionGroupType.UNDEFINED` or
      `SelectionGroupType.FUTURE`. If the script is not connected to
      GeologyCore, this will be raised for `SelectionGroupType.DRILLHOLE` as
      well.
    """
    if not isinstance(new_type, _SelectionGroupType):
      raise TypeError(
        default_type_error_message("new_type", new_type, _SelectionGroupType)
      )
    if not self._can_change_group_type_to(new_type):
      raise SelectionGroupTypeNotSupportedError(
        f"Unsupported group type: {new_type.name}"
      )
    self._save_group_type(new_type)
    self._group_type = new_type
    self._remove_unsupported_objects()
    self._record_function_call_telemetry(
      f"change_group_type.{new_type.name.lower()}"
    )

  def add(self, oid: ObjectID[DataObject]):
    """Add `oid` to this selection group.

    Raises
    ------
    ValueError
      If `oid` is an orphan object or the null object.
    GroupCannotContainObjectError
      If `oid` cannot be added to groups of this type.
      The most common case of this is if the group type is
      `SelectionGroupType.DRILLHOLE` and `oid` is not a drillhole or if the
      script is not connected to GeologyCore.
    """
    self.extend([oid])

  def extend(self, oids: Iterable[ObjectID[DataObject]]):
    """Add all items in `oids` to the selection group.

    Raises
    ------
    ValueError
      If any item in `oids` is an orphan object or the null object.
    GroupCannotContainObjectError
      If any object in `oids` cannot be added to groups of this type.
      The most common case of this is if the group type is
      `SelectionGroupType.DRILLHOLE` and any item in `oids` is not a drillhole
      or if the script is not connected to GeologyCore.
    """
    if not self.group_type.is_supported():
      raise NotImplementedError(
        f"Adding to groups of type: {self.group_type} is not implemented."
      )
    actual_oids = list(oids)
    # Collect the names and handles first so that if an object ID
    # in the middle is invalid, then none of them are added.
    objects_to_add: list[tuple[str, ObjectID]] = []
    for oid in actual_oids:
      self.__raise_if_oid_is_invalid(oid)
      if self.__is_a_container(oid):
        # Add the contents of a container instead of the container.
        with Container(oid, LockType.READ) as container:
          actual_oids.extend(container.ids())
          continue
      if not self.__can_include_oid(oid):
        raise GroupCannotContainObjectError(self.group_type, oid)
      objects_to_add.append((oid.name, oid))

    for name, handle in objects_to_add:
      self.__add(name, handle)

  def remove(self, oid: ObjectID[DataObject]):
    """Remove `oid` from the selection group.

    This has no effect if `oid` is not in the group.
    """
    if not self.group_type.is_supported():
      raise NotImplementedError(
        f"Removing from groups of type: {self.group_type} is not implemented."
      )
    try:
      self._data_engine_api().ContainerRemoveObject(
        self._lock.lock,
        oid.handle,
        True
      )
    except (AttributeError, TypeError):
      raise TypeError(
        default_type_error_message(
          "oid",
          oid,
          ObjectID[DataObject]
        )
      ) from None
    key_to_remove: str | None = None
    for key, item in self._contents.items():
      if item == oid:
        key_to_remove = key
        break
    if key_to_remove is not None:
      del self._contents[key_to_remove]

  def clear(self):
    """Remove all items from this selection group."""
    if not self.group_type.is_supported():
      raise NotImplementedError(
        f"Clearing groups of type: {self.group_type} is not implemented."
      )
    self._data_engine_api().ContainerPurge(self._lock.lock)
    self._contents.clear()
