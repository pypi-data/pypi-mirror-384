"""Helper functions for overwriting objects."""
###############################################################################
#
# (C) Copyright 2023, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations
import os
import pathlib
import typing

from ..data import ObjectID
from .lock import WriteLock
from .path_helpers import check_path_component_validity
from .unique_name import unique_name
from ..overwrite_modes import OverwriteMode

def _unique_name(object_name: str, container_lock: WriteLock) -> str:
  """Get a unique unused name for the object.

  Parameters
  ----------
  object_name
    The name to use as a base.
  container_lock
    Lock on the container to generate the unique name for.

  Returns
  -------
  str
    object_name with the smallest possible integer appended such
    that there is no object in the container with that name.
  """
  def name_exists(name: str) -> bool:
    # pylint: disable=protected-access
    return container_lock._data_engine.ContainerFind(
      container_lock.lock, name).value != 0
  return unique_name(object_name, name_exists, start=1)


def _add_to_container_with_override(
    container_lock: WriteLock,
    object_name: str,
    object_id: ObjectID,
    allow_hidden_objects: bool,
    overwrite: OverwriteMode):
  """Add a single object to an open container.

  Parameters
  ----------
  container_lock
    Write lock on the container to add the object to.
  object_name
    The name to add the object with.
  object_id
    ObjectID of the object to add.
  allow_hidden_objects
    If True, object_name can be the name for a hidden object.
    If False, an error will be raised if object_name is for
    a hidden object.
  overwrite
    Enum indicating what behaviour to use if there is already an object with
    the given name in the container.
  """
  check_path_component_validity(object_name, allow_hidden_objects)
  # pylint: disable=protected-access
  existing_object = container_lock._data_engine.ContainerFind(
      container_lock.lock, object_name)
  if existing_object:
    if existing_object.value == object_id.handle.value:
      # The object has already been added to the container
      # with the specified name.
      return

    if overwrite is OverwriteMode.ERROR:
      raise ValueError(
        f"There is already an object in the container "
        f"called: '{object_name}'")
    if overwrite is OverwriteMode.OVERWRITE:
      container_lock._data_engine.ContainerRemoveObject(
        container_lock.lock, existing_object, False)
    elif overwrite is OverwriteMode.UNIQUE_NAME:
      new_name = _unique_name(object_name, container_lock)
      object_name = new_name

  container_lock._data_engine.ContainerAppend(
    container_lock.lock,
    object_name,
    object_id.handle,
    True)


def add_objects_with_overwrite(
    container_lock: WriteLock,
    objects_to_add: typing.Iterable[tuple[str, ObjectID]],
    allow_hidden_objects: bool,
    overwrite: OverwriteMode):
  """Add objects to the container with overwrite support.

  Parameters
  ----------
  container_lock
    Write lock on the container to add objects to.
  objects_to_add
    An iterable of tuples containing the name to add each object at
    and the object ID of each object to add.
  allow_hidden_objects
    If true, allows adding hidden objects to the container.
    If false, an error will be raised if an object_to_add would be
    a hidden object.
  overwrite
    Enum indicating what behaviour to use if there is already an object with
    the given names in the container.

  Raises
  ------
  ValueError
    If overwrite is OverwriteMode.ERROR and there is already an object
    with the specified name in the container.
  ValueError
    If this would add a hidden object and adding hidden objects
    is disallowed.
  """
  for object_name, object_id in objects_to_add:
    _add_to_container_with_override(
      container_lock, object_name, object_id, allow_hidden_objects, overwrite)

def unique_filename(path: os.PathLike | str) -> pathlib.Path:
  """Return a unique filename, at the current point in time.

  This is achieved by adding a number before the file extension (suffix).
  If there is already a number before the file extension in the path given
  then it will not be incremented and instead another number is appended.

  Parameters
  ----------
  path
    The path to the file that may already exist.

  Warnings
  --------
  If another process or thread is creating folders with a similar name then
  there is a risk it won't be unique.
  """
  path = pathlib.Path(os.fspath(path))
  if not path.exists():
    return path

  suffix = path.suffix
  existing_names = set(
    sibling.name for sibling in path.parent.glob(f"*{suffix}")
  )

  def name_already_exists(name: str) -> bool:
    name = f"{name}{suffix}"
    if name not in existing_names:
      # Check again to be sure it doesn't exist.
      unique_path = path.parent / name
      if not unique_path.exists():
        return False
    return True

  new_name = unique_name(path.stem, name_already_exists, separator="_")
  return path.parent / f"{new_name}{suffix}"
