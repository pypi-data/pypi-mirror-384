"""Function for appending a number to a name to make it unique."""
###############################################################################
#
# (C) Copyright 2024, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

from collections.abc import Callable

def unique_name(
  base_name: str,
  name_already_exists: Callable[[str], bool],
  start: int=2,
  separator: str=" "
) -> str:
  """Postfix `base_name` with a number to make it unique.

  This function is only multi-process or thread safe if name_already_exists()
  is multi process or thread-safe.

  Parameters
  ----------
  base_name
    The base name which may need a number postfixed to make it unique.
  name_already_exists
    A function which when given a name returns True if that name already
    exists and False if that name does not exist.
  start
    The first number to try prefixing to the name.
    This is 2 by default.
  separator
    The character to place between the base name and the postfix.
    This is a space by default.

  Returns
  -------
  str
    `base_name` if `name_already_exists(base_name)` is False.
    Otherwise, `base_name` postfixed with the smallest possible integer,
    starting at `start`, such that `name_already_exists()` returns False.

  """
  if not name_already_exists(base_name):
    return base_name

  name_template = f"{base_name}{separator}%i"
  i = start
  new_name = name_template % i
  while name_already_exists(new_name):
    i += 1
    new_name = name_template % i
  return new_name
