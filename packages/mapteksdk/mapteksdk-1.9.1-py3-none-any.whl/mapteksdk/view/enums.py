"""Enums used to interact with a view."""
###############################################################################
#
# (C) Copyright 2021, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
import enum
import typing

from mapteksdk.data import ObjectID
from mapteksdk.internal.comms import (
  InlineMessage,
)
from mapteksdk.internal.serialisation import (
  FixedInteger32Mixin,
  FixedInteger32uMixin
)


class PredefinedView(enum.Enum):
  """Predefined camera angles for viewing data."""
  FRONT = 0
  BACK = 1
  TOP = 2
  BOTTOM = 3
  LEFT = 4
  RIGHT = 5

  @property
  def look_direction(self) -> tuple[float, float, float]:
    """The view direction of this predefined view."""
    if self is PredefinedView.FRONT:
      return (0.0, 1.0, 0.0)
    if self is PredefinedView.BACK:
      return (0.0, -1.0, 0.0)
    if self is PredefinedView.LEFT:
      return (1.0, 0.0, 0.0)
    if self is PredefinedView.RIGHT:
      return (-1.0, 0.0, 0.0)
    if self is PredefinedView.BOTTOM:
      return (0.0, 0.0, 1.0)
    if self is PredefinedView.TOP:
      return (0.0, 0.0, -1.0)

    raise NotImplementedError(
      f"Unsupported predefined view: {self}. "
    )

  @property
  def up_direction(self) -> tuple[float, float, float]:
    """The up direction of this predefined view."""
    if self.look_direction[2] == 0.0:
      return (0, 0, 1)
    return (0, 1, 0)


class ManipulationMode(enum.Enum):
  """View manipulation modes.

  These control how panning and rotating the view is handled.
  """
  Z_UP = "ModeZUp"
  LOOK_FROM = "ModeLookFrom"
  PLAN_VIEW_MODE = "ModePlanView"
  SCREEN_MODE = "ModeScreen"
  UNKNOWN = ""
  """The manipulation mode is not supported by this enum.

  This will be commonly encountered if the view is a stereonet view as this
  has its own view mode which is not included in this enum because it is
  not applicable to normal views.
  """


class ObjectFilter(FixedInteger32uMixin, enum.IntEnum):
  """Describes different ways to filter what objects are returned by
  a ViewController."""

  DEFAULT = 0
  """Default - return all object except transient and background objects but
  ignoring visibility, and selection

  Transient objects are objects that are in the view for previewing an
  operation or providing additional clarity while a tool in the application
  is running.
  """

  VISIBLE_ONLY = 1 << 0
  """Only return objects that are visible in the view."""

  HIDDEN_ONLY = 1 << 1
  """Only return objects that are hidden in the view."""

  SELECTED_ONLY = 1 << 2
  """Only return objects that are selected and are in the view."""

  @classmethod
  def from_bytes(
      cls,
      # pylint: disable=redefined-builtin
      bytes,
      byteorder = "big",
      *,
      signed = False):
    """Return the integer represented by the given array of bytes.

    bytes
        Holds the array of bytes to convert. The argument must either
        support the buffer protocol or be an iterable object
        producing bytes. Bytes and bytearray are examples of built-in
        objects that support the buffer protocol.
    byteorder
        The byte order used to represent the integer. If byteorder is
        'big', the most significant byte is at the beginning of the
        byte array. If byteorder is 'little', the most significant
        byte is at the end of the byte array. To request the native
        byte order of the host system, use 'sys.byteorder' as the
        byte order value. Default is to use 'big'.
    signed
        Indicates whether two's complement is used to represent the integer.
    """
    # :HACK: There is a mismatched quotation mark in the docstring in the
    # standard library for this function, which results in the
    # sphinx documentation failing to build.
    # Overwrite the function to fix the docstring.
    return super().from_bytes(bytes, byteorder, signed=signed) # type: ignore

  def to_bytes(
      self,
      length = 1,
      byteorder = "big",
      *,
      signed = False):
    """Return an array of bytes representing an integer.

    Parameters
    ----------
    length
      Length of bytes object to use. An OverflowError is raised if the
      integer is not representable with the given number of bytes.
      Default is length 1.
    byteorder
      The byte order used to represent the integer.
      If byteorder is 'big', the most significant byte is at the beginning
      of the byte array. If byteorder is 'little', the most significant byte
      is at the end of the byte array. To request the native byte order of
      the host system, use 'sys.byteorder' as the byte order value.
      Default is to use 'big'.
    signed
      Determines whether two's complement is used to represent the integer.
      If signed is False and a negative integer is given, an OverflowError
      is raised.
    """
    # :HACK: There is a mismatched quotation mark in the docstring in the
    # standard library for this function, which results in the
    # sphinx documentation failing to build.
    # Overwrite the function to fix the docstring.
    return super().to_bytes(length, byteorder, signed=signed)

class SectionMode(enum.IntEnum):
  """Enumeration of the available section modes.
  """

  NO_MODE = 0
  """No section mode is active."""

  POSITIVE_HALF_SPACE = 1
  """Only show data on the normal side of the plane.

  The clip plane is defined to be the action plane in the direction
  of the plane normal.

  A section width may be defined to only show the data on the normal
  side of the plane that is at a maximum the section width away.
  """

  NEGATIVE_HALF_SPACE = 2
  """Only show data on the negative side of the plane.

  The clip plane is defined to be the action plane in the opposite
  direction of the plane normal.

  A section width may be defined to only show the data on the normal
  side of the plane that is at a maximum the section width away.
  """

  STRIP = 3
  """Show data between two parallel planes.

  The clip planes are defined to be half the section width either side of the
  plane.
  """

  @classmethod
  def from_bytes(
      cls,
      # pylint: disable=redefined-builtin
      bytes,
      byteorder = "big",
      *,
      signed = False):
    """Return the integer represented by the given array of bytes.

    bytes
        Holds the array of bytes to convert. The argument must either
        support the buffer protocol or be an iterable object
        producing bytes. Bytes and bytearray are examples of built-in
        objects that support the buffer protocol.
    byteorder
        The byte order used to represent the integer. If byteorder is
        'big', the most significant byte is at the beginning of the
        byte array. If byteorder is 'little', the most significant
        byte is at the end of the byte array. To request the native
        byte order of the host system, use 'sys.byteorder' as the
        byte order value. Default is to use 'big'.
    signed
        Indicates whether two's complement is used to represent the integer.
    """
    # :HACK: There is a mismatched quotation mark in the docstring in the
    # standard library for this function, which results in the
    # sphinx documentation failing to build.
    # Overwrite the function to fix the docstring.
    return super().from_bytes(bytes, byteorder, signed=signed) # type: ignore

  def to_bytes(
      self,
      length = 1,
      byteorder = "big",
      *,
      signed = False):
    """Return an array of bytes representing an integer.

    Parameters
    ----------
    length
      Length of bytes object to use. An OverflowError is raised if the
      integer is not representable with the given number of bytes.
      Default is length 1.
    byteorder
      The byte order used to represent the integer.
      If byteorder is 'big', the most significant byte is at the beginning
      of the byte array. If byteorder is 'little', the most significant byte
      is at the end of the byte array. To request the native byte order of
      the host system, use 'sys.byteorder' as the byte order value.
      Default is to use 'big'.
    signed
      Determines whether two's complement is used to represent the integer.
      If signed is False and a negative integer is given, an OverflowError
      is raised.
    """
    # :HACK: There is a mismatched quotation mark in the docstring in the
    # standard library for this function, which results in the
    # sphinx documentation failing to build.
    # Overwrite the function to fix the docstring.
    return super().to_bytes(length, byteorder, signed=signed)


class SectionStepDirection(enum.IntEnum):
  """Enumeration of the section stepping directions.

  This refers to the screen-space directions in which to move the section.

  The two compound directions (LEFT_AND_UP and RIGHT_AND_DOWN) will move the
  section in the direction of the strongest component of the section plane
  normal as seen in screen-space (horizontal or vertical).
  """

  LEFT = 0
  RIGHT = 1
  UP = 2
  DOWN = 3
  LEFT_AND_UP = 4
  RIGHT_AND_DOWN = 5

  @classmethod
  def from_bytes(
      cls,
      # pylint: disable=redefined-builtin
      bytes,
      byteorder = "big",
      *,
      signed = False):
    """Return the integer represented by the given array of bytes.

    bytes
        Holds the array of bytes to convert. The argument must either
        support the buffer protocol or be an iterable object
        producing bytes. Bytes and bytearray are examples of built-in
        objects that support the buffer protocol.
    byteorder
        The byte order used to represent the integer. If byteorder is
        'big', the most significant byte is at the beginning of the
        byte array. If byteorder is 'little', the most significant
        byte is at the end of the byte array. To request the native
        byte order of the host system, use 'sys.byteorder' as the
        byte order value. Default is to use 'big'.
    signed
        Indicates whether two's complement is used to represent the integer.
    """
    # :HACK: There is a mismatched quotation mark in the docstring in the
    # standard library for this function, which results in the
    # sphinx documentation failing to build.
    # Overwrite the function to fix the docstring.
    return super().from_bytes(bytes, byteorder, signed=signed) # type: ignore

  def to_bytes(
      self,
      length: "typing.SupportsIndex" = 1,
      byteorder: "typing.Literal['little', 'big']" = "big",
      *,
      signed: bool = False) -> bytes:
    """Return an array of bytes representing an integer.

    Parameters
    ----------
    length
      Length of bytes object to use. An OverflowError is raised if the
      integer is not representable with the given number of bytes.
      Default is length 1.
    byteorder
      The byte order used to represent the integer.
      If byteorder is 'big', the most significant byte is at the beginning
      of the byte array. If byteorder is 'little', the most significant byte
      is at the end of the byte array. To request the native byte order of
      the host system, use 'sys.byteorder' as the byte order value.
      Default is to use 'big'.
    signed
      Determines whether two's complement is used to represent the integer.
      If signed is False and a negative integer is given, an OverflowError
      is raised.
    """
    # :HACK: There is a mismatched quotation mark in the docstring in the
    # standard library for this function, which results in the
    # sphinx documentation failing to build.
    # Overwrite the function to fix the docstring.
    return super().to_bytes(length, byteorder, signed=signed)


class TransientGeometryRestrictMode(FixedInteger32Mixin, enum.IntEnum):
  """Enumeration describing the possible restrictions on transient geometry.

  The options are:

  - No restrictions (show in all picked views).
  - Only shown in the specific view (after pick in that view).
  - Only shown in views that are not the specified view (after pick in that
    view).
  """
  NO_RESTRICTIONS = 0
  ONLY_IN_VIEW = 1
  NEVER_IN_VIEW = 2

  @classmethod
  def from_bytes(
      cls,
      # pylint: disable=redefined-builtin
      bytes,
      byteorder = "big",
      *,
      signed = False):
    """Return the integer represented by the given array of bytes.

    bytes
        Holds the array of bytes to convert. The argument must either
        support the buffer protocol or be an iterable object
        producing bytes. Bytes and bytearray are examples of built-in
        objects that support the buffer protocol.
    byteorder
        The byte order used to represent the integer. If byteorder is
        'big', the most significant byte is at the beginning of the
        byte array. If byteorder is 'little', the most significant
        byte is at the end of the byte array. To request the native
        byte order of the host system, use 'sys.byteorder' as the
        byte order value. Default is to use 'big'.
    signed
        Indicates whether two's complement is used to represent the integer.
    """
    # :HACK: There is a mismatched quotation mark in the docstring in the
    # standard library for this function, which results in the
    # sphinx documentation failing to build.
    # Overwrite the function to fix the docstring.
    return super().from_bytes(bytes, byteorder, signed=signed) # type: ignore

  def to_bytes(
      self,
      length: "typing.SupportsIndex" = 1,
      byteorder: "typing.Literal['little', 'big']" = "big",
      *,
      signed: bool = False) -> bytes:
    """Return an array of bytes representing an integer.

    Parameters
    ----------
    length
      Length of bytes object to use. An OverflowError is raised if the
      integer is not representable with the given number of bytes.
      Default is length 1.
    byteorder
      The byte order used to represent the integer.
      If byteorder is 'big', the most significant byte is at the beginning
      of the byte array. If byteorder is 'little', the most significant byte
      is at the end of the byte array. To request the native byte order of
      the host system, use 'sys.byteorder' as the byte order value.
      Default is to use 'big'.
    signed
      Determines whether two's complement is used to represent the integer.
      If signed is False and a negative integer is given, an OverflowError
      is raised.
    """
    # :HACK: There is a mismatched quotation mark in the docstring in the
    # standard library for this function, which results in the
    # sphinx documentation failing to build.
    # Overwrite the function to fix the docstring.
    return super().to_bytes(length, byteorder, signed=signed)


class TransientGeometrySettings(InlineMessage):
  """Settings for transient geometry.

  These affect how an object is treated when they are transient
  geometry.
  """
  is_clippable: bool = True
  is_pickable: bool = False
  is_selectable: bool = False
  is_initially_visible: bool =  True

  restrict_mode: TransientGeometryRestrictMode = \
    TransientGeometryRestrictMode.NO_RESTRICTIONS
  restricted_views: list[ObjectID] = []

  def __repr__(self):
    # This intentionally does not include every property, it is just enough to
    # summarise the basic settings. is_initially_visible for example is only
    # relevant when it is first added to the view so not hugely important.
    return f'{self.__class__.__qualname__}(' + \
      f'is_clippable={self.is_clippable}, is_pickable={self.is_pickable}, ' + \
      f'is_selectable={self.is_selectable})'

  def __eq__(self, value: object) -> bool:
    if not isinstance(value, TransientGeometrySettings):
      return False
    return (
      self.is_clippable == value.is_clippable
      and self.is_pickable == value.is_pickable
      and self.is_selectable == value.is_selectable
      and self.is_initially_visible == value.is_initially_visible
      and self.restrict_mode == value.restrict_mode
      and self.restricted_views == value.restricted_views
    )
