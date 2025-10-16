"""Helpers for handling object paths."""
###############################################################################
#
# (C) Copyright 2023, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations


class HiddenObjectPermissionError(ValueError):
  """Raised if the object being used is hidden and that is not allowed."""

  def __init__(self) -> None:
    super().__init__("Names cannot start with '.' if hidden objects are disabled.")


def check_path_component_validity(path: str, allow_hidden_objects: bool):
  """Raises an appropriate error if the path component is invalid.

  Parameters
  ----------
  path
    The path to check for validity.
  allow_hidden_objects
    If True, the path component may be a hidden object.
    If False, an error will be raised if the path component is a hidden
    object.

  Raises
  ------
  ValueError
    path is empty or only whitespace.
  ValueError
    Backslash character is in the path.
  ValueError
    path starts with "." and hidden objects are disabled.
  ValueError
    If path starts or ends with whitespace.
  ValueError
    If path contains newline characters.
  ValueError
    If path contains a "/" character.

  """
  if path == "" or path.isspace():
    raise ValueError("Object name cannot be blank.")

  if path[0].isspace() or path[-1].isspace():
    raise ValueError("Names cannot start or end with whitespace.")

  if "\\" in path:
    raise ValueError("Paths cannot contain \\ characters.")

  if "\n" in path:
    raise ValueError("Paths cannot contain newline characters.")

  if "/" in path:
    raise ValueError("Names cannot contain / characters.")

  if not allow_hidden_objects and path.startswith("."):
    raise HiddenObjectPermissionError()

def valid_path(full_path: str, allow_hidden_objects: bool) -> tuple[str, str]:
  """Returns a tuple consisting of the container name and the object
  name for the passed full_path with any leading/trailing "/" or
  whitespace removed.

  Parameters
  ----------
  full_path
    Full path to the object. This includes all parent containers, along
    with an optional leading and trailing "/" character.
  allow_hidden_objects
    If True, the path may contain hidden objects.
    If False, an error will be raised if the path contains hidden objects.

  Returns
  -------
  tuple
    Tuple containing two elements. The first is the container name and
    the second is the object name. This has leading and trailing "/"
    characters and whitespace removed.

  Raises
  ------
  HiddenObjectPermissionError
    If any path component starts with "." and working with hidden objects is
    not allowed.
  ValueError
    If any path component is invalid, as specified by
    _check_path_component_validity.

  Notes
  -----
  The returned container name can be nested. For example, if full_path =
  "cad/lines/line1" then the return value would be:
  ("cad/lines", "line1")

  """
  full_path = full_path.strip()
  if full_path.startswith("/"):
    full_path = full_path[1:]

  if full_path.endswith("/"):
    full_path = full_path[:-1]
  path_components = full_path.split("/")

  for path in path_components:
    check_path_component_validity(path, allow_hidden_objects)

  if len(path_components) == 1:
    return ("", path_components[0])

  return ("/".join(path_components[:-1]), path_components[-1])
