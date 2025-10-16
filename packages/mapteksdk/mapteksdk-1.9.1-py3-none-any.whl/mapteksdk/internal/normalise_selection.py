"""Utility function for normalising a selection.

Warnings
--------
Vendors and clients should not develop scripts or applications against
this package. The contents may change at any time without warning.

"""
###############################################################################
#
# (C) Copyright 2022, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import typing

from ..data import DataObject, ObjectID
from .util import default_type_error_message

if typing.TYPE_CHECKING:
  from collections.abc import Sequence, Iterable

def normalise_selection(
  selection: Iterable[str | DataObject | ObjectID[DataObject]]
) -> Sequence[ObjectID[DataObject]]:
  """Normalises an iterable of objects to an iterable of ObjectID.

  The selection iterable can contain a mix of the following:
  * Object path strings.
  * DataObject subclasses.
  * ObjectIDs.

  This function handles converting each to an ObjectID.

  Parameters
  ----------
  selection
    An iterable containing strings, DataObject subclasses or ObjectIDs.

  Returns
  -------
  Iterable[ObjectID]
    Iterable of ObjectID corresponding to each object in the input
    selection.

  Raises
  ------
  TypeError
    If any item in selection is not a string, DataObject or ObjectID.
  ValueError
    If any item in selection is a string, but there was no object at the
    specified path.
  """
  def to_object_id(item: str | DataObject | ObjectID[DataObject]
      ) -> ObjectID[DataObject]:
    if isinstance(item, ObjectID):
      return item
    if isinstance(item, DataObject):
      return item.id
    if isinstance(item, str):
      return ObjectID.from_path(item)
    raise TypeError(default_type_error_message("selection",
                                              item,
                                              (ObjectID, DataObject, str)))
  return [to_object_id(item) for item in selection]


def validate_selection(
  selection: Sequence[ObjectID[DataObject]],
  expected_type: type[DataObject]
):
  """Validate that `selection` only contains object of type `expected_type`.

  Raises
  ------
  TypeError
    If any object in `selection` is not the object ID of a `expected_type`.
  """
  def try_is_a(oid: ObjectID, expected_type: type[DataObject]) -> bool:
    try:
      return oid.is_a(expected_type)
    except TypeError:
      return False
  if not all(try_is_a(oid, expected_type) for oid in selection):
    def try_type_name(oid: ObjectID):
      try:
        return oid.type_name
      except TypeError:
        return "NULL"
    bad_types = {
      try_type_name(oid) for oid in selection
      if not try_is_a(oid, expected_type)
    }
    raise TypeError(
      f"All objects in the selection must be {expected_type.__name__} objects. "
      f"Unexpected types: {','.join(bad_types)}"
    )
