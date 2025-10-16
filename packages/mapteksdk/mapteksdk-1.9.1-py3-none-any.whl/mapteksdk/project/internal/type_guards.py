"""Type guards used in this package."""
###############################################################################
#
# (C) Copyright 2024, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import typing

from ...data import (
  ObjectID,
  VisualContainer,
  StandardContainer,
  Container,
  DataObject,
)

DataObjectT = typing.TypeVar("DataObjectT", bound=DataObject)


def is_a_standard_container(
  oid: ObjectID[typing.Any]
) -> typing.TypeGuard[ObjectID[StandardContainer]]:
  """Type guard which indicates if `oid` is a standard container."""
  return oid.is_a(StandardContainer)


def is_a_container(
    oid: ObjectID[typing.Any]
) -> typing.TypeGuard[
    ObjectID[Container | StandardContainer | VisualContainer]]:
  """Type guard which indicates if `oid` is a container of any kind.

  This does not treat Container subclasses (e.g. Surface) as a container.
  """
  return (
    oid.is_a((VisualContainer, StandardContainer))
    # pylint: disable=protected-access
    or oid._is_exactly_a(Container)
  )

def is_a(
    oid: ObjectID[DataObject],
    data_type: type[DataObjectT] | DataObjectT
) -> typing.TypeGuard[ObjectID[DataObjectT]]:
  """Type guard which indicates if `oid` is a `data_type`."""
  return oid.is_a(data_type)
