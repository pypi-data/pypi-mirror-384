"""Provides an abstraction for working with a selection of objects.
"""
###############################################################################
#
# (C) Copyright 2022, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

from __future__ import annotations

from collections.abc import Sequence, Iterable
import typing

from ..capi import DataEngine, DataEngineApi
from ..capi.types import T_ObjectHandle
from ..data.base import DataObject
from ..data.containers import VisualContainer
from ..data.objectid import ObjectID
from ..internal.transaction_elemental import SelectionTransaction
from ..operations import _request_transaction_and_wait

DataObjectT = typing.TypeVar("DataObjectT", bound=DataObject)
"""Generic type referring to any subclass of DataObject."""

if typing.TYPE_CHECKING:
  OtherDataObjectT = typing.TypeVar("OtherDataObjectT", bound=DataObject)


class Selection(Sequence[ObjectID[DataObjectT]]):
  """Represents a selection or put simply a sequence of objects.

  The selection will only contain a given object once.

  An application maintains a special selection, known as the active selection,
  which is the selection highlighted in views and the browser, and under
  direct control of the user.

  This means it will either be a copy of the active selection, a subset of it
  or an independent collection of objects.
  """

  def __init__(self, initial: list[ObjectID[DataObjectT]] | None = None):
    self.objects: list[ObjectID[DataObjectT]] = []

    if initial:
      # The goal is to preserve the original order, as such we don't simply
      # convert to a set and back to a list.
      seen = set()
      for item in initial:
        if item not in seen:
          self.objects.append(item)
          seen.add(item)

  @classmethod
  def active_selection(cls) -> "typing.Self":
    """Construct a Selection object from the active selection.

    The returned selection object contains the active selection when it was
    constructed. It will not change what objects are in it when the active
    selection is changed.
    """
    count = cls._data_engine_api().GetSelectedObjectCount()
    object_handle_array = (T_ObjectHandle * count)()
    cls._data_engine_api().GetSelectedObjects(object_handle_array)
    selected_objects = [ObjectID(handle) for handle in object_handle_array]
    return cls(selected_objects)

  @classmethod
  def _data_engine_api(cls) -> DataEngineApi:
    """Access the DataEngine C API."""
    return DataEngine()

  def __len__(self) -> int:
    return len(self.objects)

  def __getitem__(self, index) -> ObjectID[DataObjectT]:
    return self.objects[index]

  def append(self, item: ObjectID[DataObjectT] | DataObjectT):
    """Append an object to the end of this selection.

    If the object is already in the selection it will not be added and no
    error is raised.

    Arguments
    ---------
    item
      The object to append.

    Examples
    --------
    Add the object from the context to a selection.

    >> from mapteksdk.project import Project
    >> from mapteksdk.context_menu import context_object_id
    >> from mapteksdk.context_menu import NoContextInformationError
    >> project = Project()
    >> selection = project.get_selected()
    >> try:
    ...    selection.append(context_object_id())
    >> except NoContextInformationError:
    ...    pass  # There is no object to add (no context).
    """
    # Convert a DataObject to an ID.
    if isinstance(item, DataObject):
      oid: ObjectID = item.id
    else:
      oid: ObjectID = item

    if item not in self.objects:
      self.objects.append(oid)

  def clear(self):
    """Remove all items from this selection."""
    self.objects.clear()

  def extend(self, iterable: Iterable[DataObjectT]):
    """Extend this selection by appending elements from the iterable.

    If an object is already in the selection then it will not be appended and
    will be skipped over and subsequent objects will be added if they are not
    already in the selection.
    """

    def _to_id(item: ObjectID | DataObject) -> ObjectID:
      """Return the object ID from an object ID or DataObject."""
      return item.id if isinstance(item, DataObject) else item

    existing_objects = set(self.objects)

    # Marks the item as being seen
    def _add_and_return(item):
      """Return the original item after adding it to existing_objects."""
      existing_objects.add(item)
      return item

    self.objects.extend(
      _add_and_return(new_id) for new_id in map(_to_id, iterable)
      if new_id not in existing_objects
    )

  def where(
    self,
    *object_types: type[OtherDataObjectT]
  ) -> Selection[OtherDataObjectT]:
    """Return a selection where the type of the object matches given types.

    If multiple types are specified, this will filter the selection down to
    objects which are any of the specified types.

    It does not require that the object is all of the types because it will
    either be impossible to match them all or it will only match the most
    derived type.

    This does not change the current selection.

    There is no need to call "where(Topology, EdgeChain)" as that is the
    same as calling "where(EdgeChain)".

    Arguments
    ---------
    *object_types
        Variable number of object types to filter by.

    Returns
    -------
    Selection
        A new selection which only contains objects that match at least one
        of the given types.

    Examples
    --------
    Find all the selected polygons.

    >> from mapteksdk.project import Project
    >> from mapteksdk.data import Polygon
    >> project = Project()
    >> selection = project.get_selected()
    >> polygons = selection.where(Polygon)
    >> print(f'There were {len(polygons)} out of {len(selection)}.')

    Find all the selected polygons and polylines.

    >> from mapteksdk.project import Project
    >> from mapteksdk.data import Polygon, Polyline
    >> project = Project()
    >> selection = project.get_selected()
    >> polygons_and_lines = selection.where(Polygon, Polyline)
    >> print(f'There were {len(polygons_and_lines)} out of {len(selection)}.')

    """
    return Selection([
      selected_object for selected_object in self.objects
      if any(selected_object.is_a(object_type)
             for object_type in object_types)
    ]) # type: ignore

  def where_not(
    self,
    *object_types: type[OtherDataObjectT]
  ) -> Selection[DataObject]:
    """Return a selection containing all objects not of the specified types.

    When more than one type is given, it will exclude any object if it matches
    any of the given types.

    This does not change the current selection.

    Arguments
    ---------
    *object_types
        Variable number of object types to filter by.

    Returns
    -------
    Selection
        A new selection which only contains objects that are not of the given
        types.

    Warnings
    --------
    The static type checking of this function is overly general. Consider the
    following code:

    >>> selection: Selection[Text2D, Text3D]
    >>> text_2ds = Selection.where_not(Text3D)

    In the above code, static type checking will determine the type as
    `Selection[DataObject]` instead of `Selection[Text2D]`. If correct
    static type checking is desired, you will need to add the type hint
    manually:

    >>> selection: Selection[Text2D, Text3D]
    >>> text_2ds: Selection[Text2D] = Selection.where_not(Text3D)

    Examples
    --------
    Exclude any containers from the selection.

    >> from mapteksdk.project import Project
    >> from mapteksdk.data import VisualContainer
    >> project = Project()
    >> selection = project.get_selected()
    >> non_containers = selection.where_not(VisualContainer)
    >> print(f'There were {len(non_containers)} out of {len(selection)}.')

    """
    return Selection([
      selected_object for selected_object in self.objects
      if not any(selected_object.is_a(object_type)
                 for object_type in object_types)
    ]) # type: ignore

  def partition(
    self,
    *object_types: type[DataObject],
    with_remainder=False
  ) -> tuple[Selection[DataObject], ...]:
    """Partition the selection by the given types into separate selections.

    The same object can appear in multiple selections if one of the object
    types are related to another

    If a single type is given and with_remainder is False then you would be
    better off using where() instead. The specific case in which using
    partition() would be useful is if the list of types is variable, for
    example they are conditional or user defined.

    Parameters
    ----------
    *object_types
      Variable number of object types to partition by.
    with_remainder
      If True, an additional selection will be included in the results with
      the remaining objects in the selection that didn't match any of the
      object types given.

    Returns
    -------
    tuple
        A selection for each of the given object types, with objects of the
        given type. If with_remainder is True then an additional selection is
        included at the end containing the objects which didn't match any
        given object types.

    Warnings
    --------
    The type hints for this function are overly general. Consider the following
    code:

    >>> selection: Selection[Text2D, Text3D]
    >>> text_2ds, text_3ds = selection.partition(Text2D, Text3D)

    In this example, `text_2ds` and `text_3ds` will both be considered by
    static type checking to have the type `Selection[DataObject]` which is
    true, as both `Text2D` and `Text3D` are subclasses of `DataObject`, but
    not accurate, as `Surface` and many other types are also subclasses
    of `DataObject`. If static type checking is required for code which uses
    this function, you will need to manually assign the type hints:

    >>> selection: Selection[Text2D, Text3D]
    >>> text_2ds, text_3ds = selection.partition(Text2D, Text3D) # type: ignore
    >>> text_2ds: Selection[Text2D]
    >>> text_3ds: Selection[Text3D]

    This may be fixed in a future version of the Python SDK.

    Examples
    --------
    Find all the selected polygons and polylines.

    >> from mapteksdk.project import Project
    >> from mapteksdk.data import Polygon, Polyline
    >> project = Project()
    >> selection = project.get_selected()
    >> polygons, lines = selection.partition(Polygon, Polyline)
    >> print(f'There were {len(polygons)} polygons out of {len(selection)}.')
    >> print(f'There were {len(lines)} polylines out of {len(selection)}.')

    """
    results = [
      Selection() for _ in object_types
    ]

    if with_remainder:
      results.append(Selection())

    # Ideally, this would query the dynamic type of each object once and
    # then compare the type against each object type.

    for selected_object in self.objects:
      no_match = True
      for object_type, result in zip(object_types, results):
        if selected_object.is_a(object_type):
          result.objects.append(selected_object)
          no_match = False

      if with_remainder and no_match:
        results[-1].objects.append(selected_object)

    return tuple(results)

  @property
  def roots(self) -> Selection[DataObjectT]:
    """Return the root objects of this selection.

    The root objects in this selection are the objects whose parents are not
    part of this selection.

    This is useful when the individual objects in a container aren't needed
    because the function handles containers themselves.

    For example if the selection contains three objects:
    - /cad
    - /cad/loop
    - /cad/line
    - /scrapbook/surface
    The root objects would be /cad and /scrapbook/surface.

    Examples
    --------
    Recycle objects in the active selection.

    >> from mapteksdk.project import Project
    >> project = Project()
    >> selection = project.get_selected()
    >> for object_to_recycle in selection.roots:
    ...    project.recycle(object_to_recycle)

    If you have selected the four objects mentioned above, then this will
    ensure the recycle bin contains a cad container (with the loop and line
    inside it) and surface from /scrapbook. If you were to use selection rather
    than selection.roots then it would recycle each individual object so the
    recycle bin would have cad, loop, line and surface with no
    nesting/hierarchy.
    """
    containers = self.where(VisualContainer)

    # The roots are objects whose parents are containers that are
    # also not in the selection.
    roots = [
        object for object in self
        if object.parent not in containers
    ]

    return Selection(roots)

  def _make_active_selection(
      self,
      update_explorer: bool=True,
      allow_undo: bool=True):
    """Make this selection the active selection.

    Parameters
    ----------
    update_explorer
      If the explorer should be informed to the change. False by default.
    allow_undo
      If the change in selection should be undoable. False by default.
      Ignored if update_explorer is False.
    """
    object_count = len(self)
    object_array = (T_ObjectHandle * object_count)(
      *[oid.handle for oid in self])
    self._data_engine_api().SetSelectedObjects(object_array, object_count)

    if update_explorer:
      self._send_update_message(allow_undo)

  def _send_update_message(self, allow_undo: bool):
    """Update the project explorer after a selection change.

    Parameters
    ----------
    allow_undo
      If True, the change to the selection will be undoable.
      If False, the change to the selection will not be
      undoable.
    """
    def setup(transaction: SelectionTransaction):
      transaction.selection = self
      if not allow_undo:
        transaction.disable_undo_redo()

    def read_result(_: SelectionTransaction):
      return None

    _request_transaction_and_wait(
      SelectionTransaction,
      setup,
      read_result
    )
