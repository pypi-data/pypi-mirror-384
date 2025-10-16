"""The selection file data type."""
###############################################################################
#
# (C) Copyright 2024, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

from collections.abc import MutableMapping, Iterable, Iterator, Sequence
import typing
import re

from .base import DataObject, StaticType
from .objectid import ObjectID
from ..internal.lock import LockType
from ..internal.singular_data_property_read_write import (
  SingularDataPropertyReadWrite,
)
from ..internal.util import default_type_error_message

if typing.TYPE_CHECKING:
  from ..capi import VulcanApi


class _SelectionFileItem:
  """An item contained within a selection file.

  This can either be a name to match or a set of names to match defined
  by a regular expression containing a ? or *.
  """
  def __init__(self, name: str):
    self.__name = name
    self.__regex: re.Pattern | None = None
    if "*" in name or "?" in name:
      pattern = re.escape(self.__name)
      # A ? matches any character, so replace it with a dot.
      # A * matches zero or more characters, so replace it with dot star.
      # Add a $ to the end to ensure the match ends at the entire string.
      pattern = pattern.replace("\\?", ".")
      pattern = pattern.replace("\\*", ".*")
      pattern += "$"
      self.__regex = re.compile(pattern)

  @property
  def name(self) -> str:
    """The name passed to the constructor."""
    return self.__name

  def matches(self, value: str) -> bool:
    """Check if this item matches `value`."""
    if self.__regex:
      return self.__regex.match(value) is not None
    return self.__name == value

  def __eq__(self, value: object) -> bool:
    if isinstance(value, type(self)):
      return self.name == value.name
    return False

  def __hash__(self) -> int:
    return hash(self.__name)


class SelectionFile(DataObject):
  r"""A Vulcan selection file stored within a maptekdb.

  A selection file represents a set of names which are either included or
  excluded from a selection. In the application, these objects can be dragged
  and dropped onto a drillhole database to create a selection object which
  contains all of the drillholes with names in the selection file. The Python
  implementation can be used on any string-based data.

  Examples
  --------
  The most basic way to use a selection file is to add names which should be
  matched to the file:

  >>> with project.new(
  ...     "selection files/basic example",
  ...     SelectionFile
  ... ) as selection_file:
  ...     selection_file.add("dog")
  ...     print("dog in selection file:", "dog" in selection_file)
  ...     print("Dog in selection file:", "Dog" in selection_file)
  dog in selection file: True
  Dog in selection file: False

  Note that the matching is case sensitive - "dog" is considered to be in the
  selection, but "Dog" is not.
  By calling `add()` multiple times, or by using `extend()`, multiple names can
  be added to the selection:

  >>> with project.new(
  ...     "selection files/many example",
  ...     SelectionFile
  ... ) as selection_file:
  ...     selection_file.extend(("dog", "cat"))
  ...     print("dog in selection file:", "dog" in selection_file)
  ...     print("cat in selection file:", "cat" in selection_file)
  dog in selection file: True
  cat in selection file: True

  This causes all of these names to be considered as part of the selection.
  For more complicated matches, two wildcards are available. The first is the
  ? wildcard. This matches any character. For example:

  >>> with project.new(
  ...   "selection files/question mark example",
  ...   SelectionFile
  ... ) as selection_file:
  ...   selection_file.add("?og")
  ...   print("dog in selection file:", "dog" in selection_file)
  ...   print("cog in selection file:", "cog" in selection_file)
  ...   print("og in selection file:", "og" in selection_file)
  ...   print("frog in selection file:", "frog" in selection_file)
  dog in selection file: True
  cog in selection file: True
  og in selection file: False
  frog in selection file: False

  As the above example shows, adding the name "?og" will cause the selection
  file to be considered to contain "dog" and "cog", but not "frog" or "og".
  Alternatively, the \* wildcard can be used to match zero or more characters.
  For example:

  >>> with project.new(
  ...   "selection files/star example",
  ...   SelectionFile
  ... ) as selection_file:
  ...   selection_file.add("\*og")
  ...   print("dog in selection file:", "dog" in selection_file)
  ...   print("cog in selection file:", "cog" in selection_file)
  ...   print("og in selection file:", "og" in selection_file)
  ...   print("frog in selection file:", "frog" in selection_file)
  dog in selection file: True
  cog in selection file: True
  og in selection file: True
  frog in selection file: True

  Finally, all matches can be inverted by setting the `is_inclusion` file
  to `False`, as shown in the below example:

  >>> with project.new(
  ...     "selection files/invert example",
  ...     SelectionFile
  ... ) as selection_file:
  ...     selection_file.add("*og")
  ...     selection_file.is_inclusion = False
  ...     print("dog in selection file:", "dog" in selection_file)
  ...     print("cog in selection file:", "cog" in selection_file)
  ...     print("og in selection file:", "og" in selection_file)
  ...     print("frog in selection file:", "frog" in selection_file)
  ...     print("cat in selection file:", "cat" in selection_file)
  dog in selection file: False
  cog in selection file: False
  og in selection file: False
  frog in selection file: False
  cat in selection file: True

  By changing the selection file from an inclusion file to an exclusion file,
  the addition of "\*og" causes it to contain any name which does not match
  "\*og", such as "cat" in the above example.
  """
  def __init__(
    self,
    object_id: ObjectID | None = None,
    lock_type: LockType = LockType.READWRITE,
    *,
    rollback_on_error: bool = False
  ):
    if not object_id:
      object_id = ObjectID(self._vulcan_api().NewSelectionFile())
    super().__init__(object_id, lock_type, rollback_on_error=rollback_on_error)
    # This uses a dictionary as a simple ordered set to preserve the order
    # of items in the selection file.
    self.__contents: SingularDataPropertyReadWrite[
      MutableMapping[str, _SelectionFileItem]
    ] = SingularDataPropertyReadWrite(
      "contents",
      lambda: [self._lock.lock,],
      self.is_read_only,
      self.__load_contents,
      self.__save_contents
    )
    self.__is_inclusion: SingularDataPropertyReadWrite[
      bool
    ] = SingularDataPropertyReadWrite(
      "is_inclusive",
      lambda: [self._lock.lock,],
      self.is_read_only,
      self.__load_is_inclusive,
      self.__save_is_inclusive
    )

  @classmethod
  def _vulcan_api(cls) -> VulcanApi:
    """Access to the Vulcan API."""
    return cls._application_api().vulcan

  @classmethod
  def static_type(cls) -> StaticType:
    return StaticType(cls._vulcan_api().SelectionFileType())

  def __load_contents(self, lock) -> MutableMapping[str, _SelectionFileItem]:
    return {
      key: _SelectionFileItem(key)
      for key in self._vulcan_api().GetSelectionFileContents(lock)
    }

  def __save_contents(self, lock, contents: MutableMapping[
    str, _SelectionFileItem
  ]):
    self._vulcan_api().SetSelectionFileContents(lock, tuple(contents.keys()))

  def __load_is_inclusive(self, lock) -> bool:
    return self._vulcan_api().SelectionFileGetIsInclusive(lock)

  def __save_is_inclusive(self, lock, is_inclusive: bool):
    self._vulcan_api().SelectionFileSetIsInclusive(lock, is_inclusive)

  def _extra_invalidate_properties(self):
    self.__contents.invalidate()
    self.__is_inclusion.invalidate()

  def _record_object_size_telemetry(self):
    if not self.__contents.are_values_cached:
      # Don't load the contents solely to record telemetry.
      return

    self._record_size_for("Length", len(self))

  def _save(self):
    self.__contents.save()
    self.__is_inclusion.save()

  def __contains__(self, x: object) -> bool:
    matches = self._matches(x)
    if self.is_inclusion:
      return matches
    # Exclusion files invert the match.
    return not matches

  def __iter__(self) -> Iterator[str]:
    return iter(self.__contents.value)

  def __len__(self) -> int:
    return len(self.__contents.value)

  def _matches(self, value: object) -> bool:
    """Returns true if `value` matches any line in the file.

    This ignores whether this file is an inclusion or exclusion selection
    file and always treats it as an inclusion file.
    """
    if not isinstance(value, str):
      return False
    for item in self.__contents.value.values():
      if item.matches(value):
        return True
    return False

  def add(self, name: str) -> None:
    """Add `name` to this selection file.

    This does nothing if the `name` is already in the selection file.

    Parameters
    ----------
    name
      The name to add to the selection file.
      This must not be empty.
      This can include "*" and "?" wildcards.
      "*" will match any character 0 or more times.
      "?" will match any character.

    Raises
    ------
    ValueError
      If `name` is the empty string.
    """
    if not isinstance(name, str):
      raise TypeError(default_type_error_message("value", name, str))
    if name == "":
      raise ValueError("Cannot add an empty name to a selection file.")
    self.__contents.value[name] = _SelectionFileItem(name)

  def extend(self, names: Iterable[str]):
    """Add multiple names to the selection file at once.

    This is equivalent to calling add for each item in `names`.
    """
    for name in names:
      self.add(name)

  def discard(self, name: str) -> None:
    """Remove `name` from the selection file.

    This does nothing if `name` is not in the selection file.
    """
    self.__contents.value.pop(name, None)

  def remove(self, name: str):
    """Remove `name` from the selection file.

    This raises an error if `name` is not in the selection file.
    """
    del self.__contents.value[name]

  def clear(self):
    """Remove all names from this selection file."""
    self.__contents.value.clear()

  @property
  def patterns(self) -> Sequence[str]:
    """Return a sequence containing the patterns in this selection file."""
    return tuple(self.__contents.value.keys())

  @property
  def is_inclusion(self) -> bool:
    """If this is an inclusion file.

    If True, then the selection this object represents will include every name
    added via `add()`.
    If False, then the selection will exclude every name added via `add()`.
    """
    return self.__is_inclusion.value

  @is_inclusion.setter
  def is_inclusion(self, value: bool):
    self.__is_inclusion.value = value
