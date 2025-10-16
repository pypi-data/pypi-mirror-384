"""Classes used for type hints which can be used at run time.

Unlike mapteksdk.common.typing, it is safe to import from this package at
runtime.
"""
###############################################################################
#
# (C) Copyright 2024, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import sys
import typing

from .base import DataObject

if typing.TYPE_CHECKING:
  from .objectid import ObjectID

DataObjectT_co = typing.TypeVar(
  "DataObjectT_co",
  bound=DataObject,
  covariant=True
)
"""Indicates a child class of DataObject."""


if sys.version_info < (3, 11):
  # Python 3.10 and earlier does not support generic named tuples at runtime,
  # so use a derived tuple class with the same behaviour instead.
  class ImportedObject(tuple, typing.Generic[DataObjectT_co]):
    """An object imported from a file.

    This named tuple includes the name and the ObjectID of an imported object.
    """
    def __new__(cls, name: str, oid: ObjectID):
      return super(ImportedObject, cls).__new__(cls, (name, oid))

    @property
    def name(self) -> str:
      """The name provided by the import framework for the imported object.

      Multiple objects imported from the same file may have the same name.
      """
      return self[0]

    @property
    def oid(self) -> ObjectID[DataObjectT_co]:
      """The object ID of the imported object."""
      return self[1]
else:
  class ImportedObject(typing.NamedTuple, typing.Generic[DataObjectT_co]):
    """An object imported from a file.

    This named tuple includes the name and the ObjectID of an imported object.
    """
    name: str
    """The name provided by the import framework for the imported object.

    Multiple objects imported from the same file may have the same name.
    """
    oid: ObjectID[DataObjectT_co]
    """The object ID of the imported object."""
