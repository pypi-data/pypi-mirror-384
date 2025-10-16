"""Container data types.

Containers are objects which hold other objects. They are used to organise
data into a hierarchical structure. A container may have children objects,
each of which has a name. Containers may contain other containers, allowing
for an arbitrarily nested structure.

"""
###############################################################################
#
# (C) Copyright 2020, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

from __future__ import annotations

import logging

from ..internal.lock import LockType, WriteLock, ObjectClosedError
from .base import DataObject, StaticType
from .objectid import ObjectID
# pylint: disable=too-many-instance-attributes


log = logging.getLogger("mapteksdk.data")

class Container(DataObject):
  """Plain container object that nests other objects.

  It is used to organise data in a hierarchical structure.
  It is similar to a directory or folder concept in file systems.
  This type of container can not be viewed. If you are looking to create a
  container then you likely want to create a VisualContainer.

  The same object can be in the same container multiple times with different
  names.

  The same name cannot be used multiple times in the same container.
  """

  _original_children = None
  """Caches the original list of children.

  This is maintained by _cache_children().
  """

  _current_children = None
  """Holds the current state of the children after changes have been made.

  This maintains a list of all children after changes have been made,
  including hidden objects.

  This will always be None if the container is not open for editing.

  If not None then this takes precedence over the original children list.
  """

  allow_hidden_objects : bool = False
  """Allow the SDK to list and create objects considered hidden.

  The names of hidden objects start with a full stop (e.g. ".hidden").

  Warnings
  --------
  This should be configured prior to reading the children of the container.

  Setting allow_hidden_objects to True and deleting hidden containers that
  you didn't create may cause tools in the application to fail and can cause
  the application to crash.
  """

  allow_standard_containers : bool = False
  """Allow the SDK to handle standard containers like any other containers.

  This disables the handling of standard containers as they appear to users.

  If False (default), standard containers cannot be added or removed.
  If True, standard containers are treated as normal containers.

  Warnings
  --------
  This should be configured prior to modifying the children of the container.

  Setting allow_standard_containers to True and deleting standard containers
  can cause the application to crash.
  """

  def __init__(self, object_id=None, lock_type=LockType.READ):
    if not object_id:
      object_id = self._create_object()

    # This object modifies the RW instance of the object as it goes along
    # rather than waiting for save. As a result, it needs to be configured to
    # rollback on error.
    super().__init__(object_id, lock_type, rollback_on_error=True)

    self._invalidate_properties()

  def _create_object(self):
    """Creates a new instance of this object in the project."""
    raise NotImplementedError(
      "Creating a new Container isn't supported.\n"
      "Consider if a VisualContainer() would suit your needs.")

  @classmethod
  def static_type(cls) -> StaticType:
    """Return the type of container as stored in a Project.

    This can be used for determining if the type of an object is a container.

    """
    return cls._data_engine_api().ContainerType()

  def _extra_invalidate_properties(self):
    # Clear any changes / old state.
    self._original_children = None
    self._current_children = None

  def _record_object_size_telemetry(self):
    length = self._data_engine_api().ContainerElementCount(self._lock.lock)
    self._record_size_for("Length", length)

  def cancel(self):
    """Cancel any pending changes to the object.

    Raises
    ------
    ReadOnlyError
      If the object was open for read only (i.e not for editing).
      It is not necessary to call this for a read only object as there will be
      no pending changes.


    """
    self._raise_if_read_only("cancel changes")

    self._lock.cancel()
    self._invalidate_properties()

  def _save(self):
    self._raise_if_save_in_read_only()

    # There is little to do here as the changes have already been applied to
    # the persistent representation.
    #
    # Applying the changes as they are made avoids the need to:
    # - Maintain a list of changes to 'replay' here.
    # - Derive the changes to apply here.
    # - Use the naive approach which would be to the clear the container and
    #   repopulate. This will not perform well when simply adding objects to a
    #   large container.
    if self._data_engine_api().version < (1, 9):
      # The checkpoint function (called in DataObject.save(), which calls
      # this function) was added in API version 1.9. When connected
      # to applications with a lower API version, this simulates calling
      # checkpoint by closing and re-opening the lock.
      log.debug("Closing then reopening object for writing: %s of type %s",
        self.id, type(self).__qualname__)
      self._lock.close()
      self._lock = WriteLock(
        self.id.handle,
        self._data_engine_api(),
        rollback_on_error=self._lock.rollback_on_error)

  def names(self) -> list[str]:
    """Returns the names of the children.

    Returns
    -------
    list
      List of names of children.

    """
    return self._cache_children().names()

  def ids(self) -> list[ObjectID[DataObject]]:
    """Returns the object IDs of the children.

    Returns
    -------
    list
      List of ObjectIDs of the children.

    """
    return self._cache_children().ids()

  def items(self) -> list[tuple[str, ObjectID[DataObject]]]:
    """Return the (name, object ID) pair for each child.

    Returns
    -------
    list
      List of tuples in the form (name, object ID).

    """
    return self._cache_children().items()

  def append(self, child: tuple[str, ObjectID]):
    """Append a child to the end of the container.

    Any leading or trailing whitespace will be stripped, such whitespace is
    avoided as it is hard for users to tell two objects apart if the only
    difference in their name is whitespace.

    If the object referred to by the given ObjectID is deleted, the child
    will not be added to the container on save.

    Parameters
    ----------
    child
      The name to give the object and the ID of the object.

    Raises
    ------
    ValueError
      If the name is None, the empty string or name contains a new line or
      slashes (forward and back).
    ValueError
      If there is another object in the container with the given name (after
      leading and trailing whitespace has been removed).
    ReadOnlyError
      If the object was open for read only (i.e not for editing).
    """
    self._raise_if_read_only("append to container")

    name, oid = child

    self._validate_name(name)

    name = name.strip()

    if not oid:
      raise ValueError('A null object ID cannot be added to a container.')

    # Convert a DataObject to an ID.
    if isinstance(oid, DataObject):
      oid = oid.id

    if not self.allow_standard_containers and oid.is_a(StandardContainer):
      raise ValueError(
        'A standard container cannot be added to another container.')

    if self._current_children is None:
      self._current_children = self._children(include_hidden=True)

    if any(name == child_name for child_name, _ in self._current_children):
      raise ValueError(
        f'An object in the container already has the name: "{name}".')

    self._current_children.append((name, oid))

    # Make the change - this won't be visible until the object is closed.
    force_primary_parenting = False
    self._data_engine_api().ContainerAppend(
      self._lock.lock,
      name,
      oid.handle,
      force_primary_parenting
    )

  def insert(self, index: int, child: tuple[str, ObjectID]):
    """Insert child before index in the container.

    Any leading or trailing whitespace will be stripped, such whitespace is
    avoided as it is hard for users to tell two objects apart if the only
    difference in their name is whitespace.

    Parameters
    ----------
    index
      The position of where the child should be inserted.
    child
      The name to give the object and the ID of the object.

    Raises
    ------
    ValueError
      If the name is None, the empty string or name contains a new line or
      slashes (forward and back).
    ValueError
      If there is another object in the container with the given name (after
      leading and trailing whitespace has been removed).
    ReadOnlyError
      If the object was open for read only (i.e not for editing).
    """
    self._raise_if_read_only("insert into container")

    name, oid = child

    self._validate_name(name)

    name = name.strip()

    if not oid:
      raise ValueError('A null object ID cannot be added to a container.')

    # Convert a DataObject to an ID.
    if isinstance(oid, DataObject):
      oid = oid.id

    if not self.allow_standard_containers and oid.is_a(StandardContainer):
      raise ValueError(
        'A standard container cannot be added to another container.')

    if self._current_children is None:
      self._current_children = self._children(include_hidden=True)

    if any(name == child_name for child_name, _ in self._current_children):
      raise ValueError(
        f'An object in the container already has the name: "{name}".')

    # Treat the index as being for if it's hidden.
    if self.allow_hidden_objects:
      insertion_index = index
    elif index == 0:
      # This will insert before the first visible child.
      children = self._cache_children()
      if children:
        insertion_index = self._current_children.index(children[index])
      else:
        insertion_index = 0
    else:
      # Find the name of the item at the index that it would be inserted at
      # if there were no hidden objects.
      children = self._cache_children()
      name_of_item_at_index = children[index][0]

      # Find the index of the item with the given name in the changes,
      # which include hidden objects.
      def index_from_name(children, name):
        return next((index for index, child in enumerate(children)
                    if child[0] == name), -1)

      insertion_index = index_from_name(self._current_children,
                                        name_of_item_at_index)

    self._current_children.insert(insertion_index, (name, oid))

    # Make the change - this won't be visible until the object is closed.
    force_primary_parenting = False
    insertion_iterator = self._iterator_from_index(insertion_index)
    self._data_engine_api().ContainerInsert(self._lock.lock, insertion_iterator,
                                 name.encode('utf-8'),
                                 oid.handle, force_primary_parenting)

  def remove(self, name: str) -> ObjectID[DataObject]:
    """Remove the child with the given name or object ID from the container.

    The name itself won't be validated to reject names that aren't possible
    for a child.

    Returns
    -------
    ObjectID
      The ID of the removed object.

    Raises
    ------
    ReadOnlyError
      If the object was open for read only (i.e not for editing).
    KeyError
      If there is no child with the given name in the container.
    ValueError
      If the given name is for a hidden object and allow_hidden_objects is
      False (default).
    ValueError
      If the given name is a standard container allow_standard_containers is
      False (default).
    """
    self._raise_if_read_only("remove from container")

    if not self.allow_hidden_objects and name.startswith('.'):
      raise ValueError("Removing a hidden object is not allowed.")

    if self._current_children is None:
      self._current_children = self._children(include_hidden=True)

    def index_from_name(children, name):
      return next((index for index, child in enumerate(children)
                   if child[0] == name), -1)

    index = index_from_name(self._current_children, name)
    if index == -1:
      raise KeyError(f'No child called "{name}" in container ({self.id})')

    oid = self._current_children[index][1]
    if not self.allow_standard_containers and oid.is_a(StandardContainer):
      raise ValueError('Removing a standard container is not allowed.')

    del self._current_children[index]

    # Make the change - this won't be visible until the object is closed.
    self._data_engine_api().ContainerRemove(
      self._lock.lock, name)

    return oid

  def remove_object(self, object_to_remove: ObjectID | DataObject):
    """Remove the first child with object ID from the container.

    Only the first occurrence of the object will be removed.

    Raises
    ------
    ReadOnlyError
      If the object was open for read only (i.e not for editing).
    ValueError
      If there is no child with the given object ID in the container.
    ValueError
      If the given object is considered hidden and allow_hidden_objects is
      False (default).
    ValueError
      If the given object is a standard container allow_standard_containers is
      False (default).
    """
    if isinstance(object_to_remove, DataObject):
      object_to_remove = object_to_remove.id

    # Find the name of the item.
    children = self._cache_children()
    name = next((child_name for child_name, oid in children
                if oid == object_to_remove), '')
    if not name:
      raise ValueError(
        f'There is no object ({object_to_remove}) in the container '
        'to remove.')

    del self[name]

  def replace(self,
              name: str,
              new_object: ObjectID | DataObject) -> ObjectID[DataObject]:
    """Replace the object with the given name with a different object.

    This is similar to removing the object with the given name and then
    inserting the new object at its old position/index.

    This can be used for overwriting an existing object in a container with
    another.

    If the object referred to by the given ObjectID is deleted, the child
    will not be added to the container on save.

    Parameters
    ----------
    name
      The name of the object in the container to replace.
      This is not the path to the object, only its name. For example, to
      replace the pointset at the path "cad/pointset", the name of the object
      to replace is "pointset", where as "cad" is the name of the container.
    new_object
      The object to replace with.

    Returns
    -------
    ObjectID
      The ID of the object that was replaced.

    Raises
    ------
    KeyError
      If there is no child called name (the key) in the container.
    ValueError
      If new_object is not a valid object (it is null).
    ValueError
      If the given name is for a hidden object and allow_hidden_objects is
      False (default).
    ValueError
      If the given object is a standard container and
      allow_standard_containers is False (default).
    ReadOnlyError
      If the object was open for read only (i.e not for editing).
    """
    self._raise_if_read_only("replace object in container")

    if isinstance(new_object, DataObject):
      new_object = new_object.id

    if not new_object:
      raise ValueError('The new_object should not be null.')

    if self._current_children is None:
      self._current_children = self._children(include_hidden=True)

    def index_from_name(children, name):
      return next((index for index, child in enumerate(children)
                  if child[0] == name), -1)

    if not self.allow_hidden_objects and name.startswith('.'):
      # Treat it the same as if the object doesn't exist.
      index = -1
    else:
      index = index_from_name(self._current_children, name)

    if index < 0:
      raise KeyError()

    # Replacing one standard container with another could be allowed.
    old_object = self._current_children[index][1]
    if (not self.allow_standard_containers and
        old_object.is_a(StandardContainer)):
      raise ValueError(
        'A standard container cannot be replaced with another object.')

    self._current_children[index] = (name, new_object)

    # Make the change - this won't be visible until the object is closed.
    iterator = self._iterator_from_index(index)
    self._data_engine_api().ContainerReplaceElement(
      self._lock.lock, iterator, new_object.handle)

    return old_object

  def rename(self, old_name: str, new_name: str):
    """Rename an object within this container.

    Renaming an object to its own name has no effect.

    Renaming a standard container will create a container with the new name
    and move the children into the new container unless
    allow_standard_containers is True. This matches the behaviour of if a user
    renames the container from the explorer.

    Care should be taken when renaming standard containers when
    allow_standard_containers is True. Avoid renaming standard containers that
    you did not create (i.e avoid renaming standard containers that are created
    by the applications themselves).

    Warnings
    --------
    If a standard container is renamed when allow_standard_containers is False
    then you must ensure the changes are saved (no error is raised before it
    is saved). Failing to do so will result in the objects in the standard
    container being lost.

    Parameters
    ----------
    old_name
      The current name of the object to rename.
      This is not the path to the object, only its name. For example, to
      rename the pointset at the path "cad/pointset", the old name of the
      object would be "pointset".
    new_name
      The new name for the object.

    Raises
    ------
    KeyError
      If there is no child by old_name (the key) in the container.
    ValueError
      If the new_name is not a valid name to change to.
    ValueError
      If the given name is for a hidden object and allow_hidden_objects is
      False (default).
    ReadOnlyError
      If the object was open for read only (i.e not for editing).

    """
    self._raise_if_read_only("rename object in container")

    def index_from_name(children, name):
      return next((index for index, child in enumerate(children)
                   if child[0] == name), -1)

    self._validate_name(new_name)

    no_existing_changes = self._current_children is None
    if no_existing_changes:
      self._current_children = self._children(include_hidden=True)

    index = index_from_name(self._current_children, old_name)
    if index == -1:
      # Trying to rename a hidden object will fail with this message as it
      # will appear that the container doesn't have the hidden object, unless
      # allow_hidden_objects is True.
      if no_existing_changes:
        self._current_children = None
      raise KeyError(f'No child called "{old_name}" in container ({self.id})')

    object_id = self._current_children[index][1]

    if (not self.allow_standard_containers and
        object_id.is_a(StandardContainer)):
      # When the user renames a standard container from the explorer the
      # standard container remains but a new container is created with the
      # contents of the standard container. This is what we want to do here.

      standard_container = StandardContainer(object_id,
                                             lock_type=LockType.READWRITE)

      # Reconsider if hidden objects should be moved to the new container or
      # should remain where they are
      standard_container.allow_hidden_objects = True

      try:
        # Create a new container.
        new_container = VisualContainer(lock_type=LockType.READWRITE)
      except ValueError:
        # This situation is highly improbable and so is not documented.
        raise ValueError("Couldn't rename standard container.\n"
                         "Failed to create a new container.\n")

      new_container.allow_hidden_objects = True
      for child in standard_container.items():
        new_container.append(child)

      # The contents of the standard container have been moved to
      # new_container.
      standard_container.clear()

      new_container.save()
      standard_container.save()

      new_container.close()
      standard_container.close()

      # Append the new container as a child of the current container.
      self._current_children.append((new_name, new_container.id))

      # Make the change - this won't be visible until the object is closed.
      force_primary_parenting = False
      self._data_engine_api().ContainerAppend(
        self._lock.lock, new_name, new_container.id.handle,
        force_primary_parenting)
    else:
      self._current_children[index] = (new_name, object_id)

      # Make the change - this won't be visible until the object is closed.
      element = self._data_engine_api().ContainerFindElement(
        self._lock.lock, old_name.encode('utf-8'))

      delete_if_orphaned = False
      insertion_point = self._data_engine_api().ContainerRemoveElement(
        self._lock.lock, element, delete_if_orphaned)

      force_primary_parenting = False
      self._data_engine_api().ContainerInsert(
        self._lock.lock, insertion_point, new_name.encode('utf-8'),
        object_id.handle,
        force_primary_parenting)

  def clear(self):
    """Remove all children from the container.

    Any child objects that are not in another container will be deleted.

    It is fine to call this function if there are no children in the container.
    This does not clear any object attributes.

    The post condition of this function will be len(self) == 0.

    Raises
    ------
    ReadOnlyError
      If the object was open for read only (i.e not for editing).
    """
    self._raise_if_read_only("clear container")

    if self.allow_hidden_objects and self.allow_standard_containers:
      self._current_children = []

      # Make the change - this won't be visible until the object is closed.
      lock = self._lock.lock
      self._data_engine_api().ContainerPurge(lock)
    else:
      children = self._children(include_hidden=True)

      if self.allow_standard_containers:
        # Preserve hidden objects but not standard containers.
        def keep(name, oid):
          """Return True if the child should be kept."""
          return name.startswith('.')
      elif self.allow_hidden_objects:
        # Preserve standard containers but not hidden containers.
        def keep(name, oid):
          """Return True if the child should be kept."""
          return oid.is_a(StandardContainer)
      else:
        # Preserve hidden objects and standard but remove the rest.
        def keep(name, oid):
          """Return True if the child should be kept."""
          return oid.is_a(StandardContainer) or name.startswith('.')

      self._current_children = [
        (name, oid) for name, oid in children if keep(name, oid)
      ]

      # Make the change - this won't be visible to until the object is closed.
      lock = self._lock.lock
      self._data_engine_api().ContainerPurge(lock)
      for name, oid in self._current_children:
        self._data_engine_api().ContainerAppend(
          lock, name, oid.handle, True)

  def name_of_object(self, object_id: ObjectID | DataObject) -> str:
    """Return the name of the given object in the container.

    Only the name of the first occurrence of the object will be provided.

    Parameters
    ----------
    object_id
      The ID of the object to find the name of.

    Returns
    -------
    str
      The name of the object in this container if found.

    Raises
    ------
    ValueError
      If there is no child with the given object ID in the container.
      This will be raised if the object is hidden and allow_hidden_objects is
      False (default) as it will be as if the object ID didn't appear.
    """
    if isinstance(object_id, DataObject):
      object_id = object_id.id

    # Find the name of the item.
    children = self._cache_children()

    name = next((child_name for child_name, oid in children.items()
                if oid == object_id), '')

    if not name or (not self.allow_hidden_objects and name.startswith('.')):
      raise ValueError(f'There is no object ({object_id}) in the container.')

    return name

  def get(self,
          name: str,
          default: ObjectID = ObjectID()) -> ObjectID[DataObject]:
    """Return the object ID for the given name in the container.

    If there is no such child, the null object ID will be returned or
    default

    Parameters
    ----------
    name
      The name of the child to return.
    default
      The ID to return if there is no object called name in the container.

    Returns
    -------
    ObjectID
      The object ID of the object if found otherwise default.
    """
    name = name.strip()
    children = self._cache_children().items()
    return next((oid for child_name, oid in children if name == child_name),
                default)

  def __len__(self) -> int:
    """The length of the container is the number of children it has."""
    children = self._cache_children()
    return len(children)

  def __contains__(self, item: object) -> bool:
    """Return True if the item is in the container.

    Parameters
    ----------
    item
      The name of the item or the object ID.
    """
    children = self._cache_children()

    # Convert a DataObject to an ID.
    if isinstance(item, DataObject):
      item = item.id

    # Account for trailing whitespace to ensure that the caller can check if
    # the item exists before calling append(). Without handling this it means
    # checking if " foo " is in the container would say False but then
    # append() would fail if "foo" is in the container.
    if isinstance(item, str):
      item = item.strip()

    return any(item in (name, oid) for name, oid in children.children)

  def __getitem__(self, key: str | int):
    """Return the OID with the given name or the child with the given index.

    This enables the container to act as both a list of children and a mapping
    from name to object ID.

    Parameters
    ----------
    key
      The name or the index of the child to return.

    Raises
    ------
    KeyError
      If the key is a string and there is no child by that name in the
      container.
    IndexError
      If the key is an integer and there is no such index, the container has
      fewer elements than the index.
    """
    children = self._cache_children()

    if isinstance(key, str):
      object_id = self.get(key)
      if object_id:
        return object_id
      raise KeyError(f'No child called "{key}" in container ({self.id})')

    return children[key]

  def __delitem__(self, name: str):
    """Remove the child in the container with the given name.

    Raises
    ------
    ReadOnlyError
      If the object was open for read only (i.e not for editing).
    KeyError
      If there is no child called name in the container.
    ValueError
      If the given name contains hidden objects and allow_hidden_objects is
      False (default).
    ValueError
      If the child to remove is a standard container and
      allow_standard_containers is False (default).
    """
    # This does not support deleting by index, in part because it would need to
    # consider what is visible or not (i.e hidden objects). Potentially,
    # looking up the name from the index and then deleting the item.

    self.remove(name)

  def _children(self, include_hidden: bool):
    """Return the children of the container as (name, object ID) pairs.

    Not all children will be included.

    Parameters
    ----------
    include_hidden
      If True then objects that are considered hidden (those that are not
      shown in the explorer of an application) will be included.
    """
    def _should_include_child(name: str) -> bool:
      """Return true if the child with the given name should be included."""
      if not include_hidden and name.startswith('.'):
        return False

      return True

    children = []

    lock = self._lock.lock

    child_names_and_handles = self._data_engine_api().GetContainerContents(
      lock,
      _should_include_child
    )
    children = [
      (name, ObjectID(handle)) for name, handle in child_names_and_handles
    ]

    return children

  def _cache_children(self):
    """Cache the children of the container.

    If the children have been modified, that list takes precedences.

    Raises
    ------
    ValueError
      If the container is closed.
    """
    if self.closed:
      raise ObjectClosedError()

    def _should_include_child(name: str) -> bool:
      """Return true if the child with the given name should be included."""
      if not self.allow_hidden_objects and name.startswith('.'):
        return False

      return True

    if self._current_children is not None:
      self._original_children = ChildView([
        (name, oid) for name, oid in self._current_children
        if _should_include_child(name)
      ])
    elif self._original_children is None:
      self._original_children = ChildView(
        self._children(self.allow_hidden_objects))
    return self._original_children

  def _validate_name(self, name: str):
    """Raises ValueError exception if the name is not valid."""
    if name is None:
      raise ValueError('The name of an object cannot be be None.')

    if not name:
      raise ValueError('The name of an object cannot be the empty string.')

    invalid_symbols = '\\/\n'
    if any(symbol in name for symbol in invalid_symbols):
      raise ValueError(f'The name ("{name}") cannot contain \\ or / or a new '
                       'line')

    # The following two are not allowed to be in a name.
    # . represents the current container in a path
    # .. represents the parent container in a path.
    if name in ('.', '..'):
      raise ValueError('The name cannot be "." or ".."')

    # Users should not be allowed to start things with fullstop.
    #
    # The user interface prevents this, however application developers may
    # do this.
    if not self.allow_hidden_objects and name.startswith('.'):
      raise ValueError('The name cannot start with a full stop.')

  def _iterator_from_index(self, index):
    """Returns iterator into the container from the given index.

    If the index is out of range it returns end iterator.
    """
    lock = self._lock.lock
    begin = self._data_engine_api().ContainerBegin(lock)
    end = self._data_engine_api().ContainerEnd(lock)

    if index < 0:
      return end

    iterator = begin
    for _ in range(index):
      if iterator.value == end.value:
        break

      iterator = self._data_engine_api().ContainerNextElement(lock, iterator)

    return iterator


class VisualContainer(Container):
  """A container whose content is intended to be spatial in nature and can be
  viewed.

  This is the typical container object that users create and see in the
  explorer.

  The container can be added to a view. Any applicable children in the
  container will also appear in the view.

  Examples
  --------
  Create a container with a child.

  >>> from mapteksdk.project import Project
  >>> from mapteksdk.data import VisualContainer
  >>> project = Project()
  >>> with project.new("example", VisualContainer) as container:
  ...     with project.new(None, VisualContainer) as child:
  ...        pass
  ...     container.append(('child', child.id))

  List the children of the root container.

  >>> from mapteksdk.project import Project
  >>> project = Project()
  >>> with project.read(project.root_id) as container:
  ...     for name, object_id in container.items():
  ...          print(name, object_id)

  Query the object ID of the cad container in the root container.

  >>> from mapteksdk.project import Project
  >>> project = Project()
  >>> with project.read(project.root_id) as container:
  ...     print(container["cad"])

  """
  # pylint: disable=too-few-public-methods
  def _create_object(self):
    return ObjectID(self._modelling_api().NewVisualContainer())

  @classmethod
  def static_type(cls) -> StaticType:
    """Return the type of visual container as stored in a Project.

    This can be used for determining if the type of an object is a visual
    container.

    """
    return cls._modelling_api().VisualContainerType()

  def _save(self):
    self._raise_if_save_in_read_only()
    super()._save()

class StandardContainer(VisualContainer):
  """Class for standard containers (such as cad and surfaces)."""
  def _create_object(self):
    return ObjectID(self._modelling_api().NewStandardContainer())

  @classmethod
  def static_type(cls) -> StaticType:
    """Return the type of standard container as stored in a Project."""
    return cls._modelling_api().StandardContainerType()

class ChildView:
  """Provides a view onto the children of a container.

  Iterating over the view will provide both the name and the ID of the
  objects like the items() function.
  The container object does not need to remain open to access data in this
  view. It has cached the data itself.
  Use Project.get_children() to get a view of the children of a container.

  Parameters
  ----------
  children : list
    List of children to be viewed in the form name, ID.

  """

  def __init__(self, children):
    self.children = children

  def names(self):
    """Returns the names of the children.

    Returns
    -------
    list
      List of names of children.

    """
    return [name for name, _ in self.children]

  def ids(self):
    """Returns the object IDs of the children.

    Returns
    -------
    list
      List of ObjectIDs of the children.

    """
    return [object_id for _, object_id in self.children]

  def items(self):
    """Return the (name, object ID) pair for each child.

    Returns
    -------
    list
      List of tuples in the form (name, object ID).

    """
    return self.children

  def __getitem__(self, index):
    return self.children[index]

  def __len__(self):
    return len(self.children)

  def __iter__(self):
    return iter(self.children)
