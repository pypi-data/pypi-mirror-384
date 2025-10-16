"""Features used to display objects.
"""
###############################################################################
#
# (C) Copyright 2024, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import enum
import typing

class Appearance(enum.Enum):
  """Appearances which allow for an object to be rendered in different ways.

  Note that most appearances are not available for most objects.
  """
  SIMPLIFIED = "simple"
  """Display the object in a simplified form."""
  ANNOTATED = "annotated"
  """Display the object with additional annotations."""
  FLAT_SHADED = "image"
  """Display a Surface with flat shading.

  This means there will be no interpolation of point properties resulting
  in sharp angular effects.
  """
  SMOOTH_SHADED = "surface"
  """Display a Surface with smooth shading.

  Point properties will be interpolated causing a smooth effect.
  """
  TEXTURED = "drape"
  """Display the object with a texture.

  This is typically used for textured Surfaces.
  """
  WIREFRAME = "line"
  """Display only the edges of the object.

  Other geometry, such as facets or blocks, will be hidden.
  """
  POINTS = "point"
  """Display only the points of the object.

  Other geometry, such as edges and facets, will be hidden.
  """
  UNKNOWN = ""
  """The feature is not supported by the Python SDK.

  This typically indicates the application is newer than the Python SDK
  and contains features which the SDK cannot understand.
  """

  @classmethod
  def from_name(cls, name: str) -> typing.Self:
    """Create this object from the enum value.

    Unlike the constructor, this will return Appearance.UNKNOWN for any name
    which does not match an enum member.
    """
    try:
      return cls(name)
    except ValueError:
      return cls(cls.UNKNOWN)
