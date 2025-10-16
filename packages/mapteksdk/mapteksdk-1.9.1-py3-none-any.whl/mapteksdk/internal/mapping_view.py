"""A mapping which is a view of another mapping class."""
###############################################################################
#
# (C) Copyright 2023, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

from collections.abc import Callable, Mapping, MutableMapping, Iterator
import typing

KeyT = typing.TypeVar("KeyT")
ValueT = typing.TypeVar("ValueT")

class MappingView(Mapping[KeyT, ValueT]):
  """A read-only view of another mapping with a transformation applied.

  Parameters
  ----------
  owner
    The owner which contains keys and values.
  get_item
    A function which given the owner and a key returns the value for the view.
    This can perform simple transforms on the value.
  """
  def __init__(
      self,
      owner: Mapping[KeyT, ValueT],
      get_item: Callable[
        [Mapping[KeyT, ValueT], KeyT], ValueT]) -> None:
    self._owner = owner
    self.__get_item = get_item

  def __getitem__(self, __key: KeyT) -> ValueT:
    return self.__get_item(self._owner, __key)

  def __len__(self) -> int:
    return len(self._owner)

  def __iter__(self) -> Iterator[KeyT]:
    return iter(self._owner)


class MutableMappingView(
    MutableMapping[KeyT, ValueT], MappingView[KeyT, ValueT]):
  """A read-write view of another mapping with a transformation applied.

  Parameters
  ----------
  owner
    The owner which contains keys and values.
  get_item
    A function which given the owner and a key returns the value for the view.
    This can perform simple transforms on the value.
  inverse_function
    A function which given the owner, a key and a value sets the value.
    If get_item() performs a transform, this should perform the inverse
    transform where possible before assigning the new value to owner.
  """
  def __init__(
      self,
      owner: MutableMapping[KeyT, ValueT],
      get_item: Callable[[Mapping[KeyT, ValueT], KeyT], ValueT],
      set_item: Callable[
        [MutableMapping[KeyT, ValueT], KeyT, ValueT], None]
      ) -> None:
    super().__init__(owner, get_item)
    self.__set_item = set_item

  def __delitem__(self, __key: KeyT) -> None:
    del self._owner[__key]

  def __setitem__(self, __key: KeyT, __value: ValueT) -> None:
    self.__set_item(self._owner, __key, __value)
