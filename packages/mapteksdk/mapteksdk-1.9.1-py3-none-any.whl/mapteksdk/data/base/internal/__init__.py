"""Implementation details for this package."""
###############################################################################
#
# (C) Copyright 2025, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

import typing

from .object_attributes import (
  ObjectAttribute,
  ObjectAttributeDictionary,
)

if typing.TYPE_CHECKING:
  from .object_attributes import (
    ObjectAttributeTypes,
    ObjectAttributeDataTypes,
  )
