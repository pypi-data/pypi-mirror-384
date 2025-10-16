"""The primitive type enum."""
###############################################################################
#
# (C) Copyright 2022, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

import enum

class PrimitiveType(enum.Enum):
  """Enumeration of fundamental primitive types."""
  POINT = 1
  EDGE = 2
  FACET = 3
  TETRA = 4
  CELL = 5
  BLOCK = 6

  def _to_string(self) -> str:
    """Convert to a string.

    The string returned by this function is intended to be used to generate
    the names of functions to call in the C API for this primitive type.
    """
    to_string_dictionary = {
      PrimitiveType.POINT : "Point",
      PrimitiveType.EDGE : "Edge",
      PrimitiveType.FACET : "Facet",
      PrimitiveType.TETRA : "Tetra",
      PrimitiveType.CELL : "Cell",
      PrimitiveType.BLOCK : "Block"
    }

    try:
      return to_string_dictionary[self]
    except KeyError as error:
      raise ValueError(
        f'The primitive type {self} is an unsupported type.') from error
