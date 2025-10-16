"""Units and other enumrations for file operations."""
###############################################################################
#
# (C) Copyright 2020, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

from __future__ import annotations

from enum import Enum
import typing
import warnings

from ..internal.classproperty import ClassProperty

class NoUnitType:
  """Type of objects used to represent the absence of a unit.

  Rather than create objects of this type directly, you should use the
  `NO_UNIT` constant defined in this module instead.

  All instances of this type evaluate as equal.

  Notes
  -----
  If PEP-661 is accepted then in future versions of the SDK this may become
  an alias for `Sentinel`.
  """
  def __eq__(self, value: object) -> bool:
    return isinstance(value, type(self))


NO_UNIT = NoUnitType()
"""Placeholder used to represent the absence of a unit."""

_DEPRECATION_MESSAGE = (
  "DistanceUnit.{0} is deprecated. Use DistanceUnit.{1} instead.")
"""Message for deprecated enum members."""

class UnsupportedUnit:
  """Class representing an unsupported unit."""
  def __init__(self, unit_string: str):
    self.unit_string: str = unit_string
    """String representation of the unsupported unit."""

  def __hash__(self) -> int:
    return self.unit_string.__hash__()

  def __eq__(self, __o: object) -> bool:
    if isinstance(__o, UnsupportedUnit):
      return __o.unit_string == self.unit_string
    return False

  def __repr__(self) -> str:
    return f"{type(self).__name__}('{self.unit_string}')"

  def _to_serialisation_string(self) -> str:
    """Convert the unsupported unit to a string representation."""
    return self.unit_string


class Axis(Enum):
  """Enum used to choose an axis."""
  X = 0
  Y = 1
  Z = 2


# Changing the name would break backwards compatibility.
class DistanceUnit(Enum):
  """Enum representing distance units supported by the Project."""
  UNKNOWN = -1
  ANGSTROM = 301
  PICOMETRE = 316
  NANOMETRE = 302
  MICROMETRE = 303
  MILLIMETRE = 304
  CENTIMETRE = 305
  DECIMETRE = 306
  METRE = 307
  DECAMETRE = 308
  HECTOMETRE = 309
  KILOMETRE = 310
  MEGAMETRE = 311
  GIGAMETRE = 312
  ASTRONOMICAL_UNIT = 313
  LIGHT_YEAR = 314
  PARSEC = 315
  MICROINCH = 351
  THOU = 352
  INCH = 353
  FEET = 354
  LINK = 356
  CHAIN = 357
  YARD = 358
  FATHOM = 359
  MILE = 360
  US_SURVEY_INCH = 361
  US_SURVEY_FEET = 362
  US_SURVEY_YARD = 363
  NAUTICAL_MILE = 364

  # pylint: disable=no-self-argument
  # Pylint can't identify that ClassProperty is equivalent to combining
  # @classmethod and @property so it thinks the first argument should be
  # self instead of cls.
  @ClassProperty
  def metre(cls) -> typing.Literal[DistanceUnit.METRE]:
    """Deprecated alias for DistanceUnit.METRE."""
    warnings.warn(
      str.format(_DEPRECATION_MESSAGE, "metre", "METRE"),
      DeprecationWarning)
    return cls.METRE

  @ClassProperty
  def millimetre(cls) -> typing.Literal[DistanceUnit.MILLIMETRE]:
    """Deprecated alias for DistanceUnit.MILLIMETRE."""
    warnings.warn(
      str.format(_DEPRECATION_MESSAGE, "millimetre", "MILLIMETRE"),
      DeprecationWarning)
    return cls.MILLIMETRE

  @ClassProperty
  def feet(cls) -> typing.Literal[DistanceUnit.FEET]:
    """Deprecated alias for DistanceUnit.FEET."""
    warnings.warn(
      str.format(_DEPRECATION_MESSAGE, "feet", "FEET"),
      DeprecationWarning)
    return cls.FEET

  @ClassProperty
  def yard(cls) -> typing.Literal[DistanceUnit.YARD]:
    """Deprecated alias for DistanceUnit.YARD."""
    warnings.warn(
      str.format(_DEPRECATION_MESSAGE, "yard", "YARD"),
      DeprecationWarning)
    return cls.YARD
  # pylint: enable=no-self-argument

  def _to_serialisation_string(self) -> str:
    """Converts the enum member to a serialisation string."""
    enum_to_serialisation_string: dict[DistanceUnit, str] = {
      DistanceUnit.UNKNOWN : "unknown",
      DistanceUnit.ANGSTROM : "angstroms",
      DistanceUnit.PICOMETRE : "picometres",
      DistanceUnit.NANOMETRE : "nanometres",
      DistanceUnit.MICROMETRE : "micrometres",
      DistanceUnit.MILLIMETRE : "millimetres",
      DistanceUnit.CENTIMETRE : "centimetres",
      DistanceUnit.DECIMETRE : "decimetres",
      DistanceUnit.METRE : "metres",
      DistanceUnit.DECAMETRE : "decametres",
      DistanceUnit.HECTOMETRE : "hectometres",
      DistanceUnit.KILOMETRE : "kilometres",
      DistanceUnit.MEGAMETRE : "megametres",
      DistanceUnit.GIGAMETRE : "gigametres",
      DistanceUnit.ASTRONOMICAL_UNIT : "astronomical units",
      DistanceUnit.LIGHT_YEAR : "light years",
      DistanceUnit.PARSEC : "parsecs",
      DistanceUnit.MICROINCH : "microinches",
      DistanceUnit.THOU : "thou",
      DistanceUnit.INCH : "inches",
      DistanceUnit.FEET : "feet",
      DistanceUnit.LINK : "links",
      DistanceUnit.CHAIN : "chain",
      DistanceUnit.YARD : "yards",
      DistanceUnit.FATHOM : "fathoms",
      DistanceUnit.MILE : "miles",
      DistanceUnit.US_SURVEY_INCH : "US survey inches",
      DistanceUnit.US_SURVEY_FEET : "US survey feet",
      DistanceUnit.US_SURVEY_YARD : "US survey yards",
      DistanceUnit.NAUTICAL_MILE : "nautical miles",
    }

    return enum_to_serialisation_string.get(self, "unknown")

  @staticmethod
  def _from_serialisation_string(string: str) -> DistanceUnit:
    """Converts a serialisation string back to the enum.

    Parameters
    ----------
    string
      A string representing a distance unit.

    Returns
    -------
    DistanceUnit
      The distance unit the serialisation string represented.
    """
    serialisation_string_to_enum: dict[str, DistanceUnit] = {
      "unknown" : DistanceUnit.UNKNOWN,
      "angstroms" : DistanceUnit.ANGSTROM,
      "picometres" : DistanceUnit.PICOMETRE,
      "nanometres" : DistanceUnit.NANOMETRE,
      "micrometres" : DistanceUnit.MICROMETRE,
      "millimetres" : DistanceUnit.MILLIMETRE,
      "centimetres" : DistanceUnit.CENTIMETRE,
      "decimetres" : DistanceUnit.DECIMETRE,
      "metres" : DistanceUnit.METRE,
      "decametres" : DistanceUnit.DECAMETRE,
      "hectometres" : DistanceUnit.HECTOMETRE,
      "kilometres" : DistanceUnit.KILOMETRE,
      "megametres" : DistanceUnit.MEGAMETRE,
      "gigametres" : DistanceUnit.GIGAMETRE,
      "astronomical units" : DistanceUnit.ASTRONOMICAL_UNIT,
      "light years" : DistanceUnit.LIGHT_YEAR,
      "parsecs" : DistanceUnit.PARSEC,
      "microinches" : DistanceUnit.MICROINCH,
      "thou" : DistanceUnit.THOU,
      "inches" : DistanceUnit.INCH,
      "feet" : DistanceUnit.FEET,
      "links" : DistanceUnit.LINK,
      "chain" : DistanceUnit.CHAIN,
      "yards" : DistanceUnit.YARD,
      "fathoms" : DistanceUnit.FATHOM,
      "miles" : DistanceUnit.MILE,
      "US survey inches" : DistanceUnit.US_SURVEY_INCH,
      "US survey feet" : DistanceUnit.US_SURVEY_FEET,
      "US survey yards" : DistanceUnit.US_SURVEY_YARD,
      "nautical miles" : DistanceUnit.NAUTICAL_MILE
    }

    return serialisation_string_to_enum.get(string, DistanceUnit.UNKNOWN)


class AngleUnit(Enum):
  """Enum representing the angle units supported by the Project."""
  UNKNOWN = -1
  RADIANS = 101
  DEGREES = 102
  ARCMINUTES = 103
  ARCSECONDS = 104
  NATO_MILS = 109
  SOVIET_MILS = 110
  MILS = 111
  GRADIANS = 107
  GONS = 108

  def _to_serialisation_string(self) -> str:
    """Converts the enum member to a serialisation string."""
    enum_to_serialisation_string: dict[AngleUnit, str] = {
      AngleUnit.UNKNOWN : "unknown",
      AngleUnit.RADIANS : "radians",
      AngleUnit.DEGREES : "degrees",
      AngleUnit.ARCMINUTES : "arcminutes",
      AngleUnit.ARCSECONDS : "arcseconds",
      AngleUnit.NATO_MILS : "NATO Mils",
      AngleUnit.SOVIET_MILS : "Soviet Mils",
      AngleUnit.MILS : "Mils",
      AngleUnit.GRADIANS : "gradians",
      AngleUnit.GONS : "gons",
    }

    return enum_to_serialisation_string.get(self, "unknown")

  @staticmethod
  def _from_serialisation_string(string: str) -> AngleUnit:
    """Converts a serialisation string back to the enum.

    Parameters
    ----------
    string
      A string representing an angle unit.

    Returns
    -------
    AngleUnit
      The angle unit the serialisation string represented.
    """
    serialisation_string_to_enum: dict[str, AngleUnit] = {
      "unknown" : AngleUnit.UNKNOWN,
      "radians" : AngleUnit.RADIANS,
      "degrees" : AngleUnit.DEGREES,
      "arcminutes" : AngleUnit.ARCMINUTES,
      "arcseconds" : AngleUnit.ARCSECONDS,
      "NATO Mils" : AngleUnit.NATO_MILS,
      "Soviet Mils" : AngleUnit.SOVIET_MILS,
      "Mils" : AngleUnit.MILS,
      "gradians" : AngleUnit.GRADIANS,
      "gons" : AngleUnit.GONS,
    }

    return serialisation_string_to_enum.get(string, AngleUnit.UNKNOWN)

# This is protected because it is not intended to be used by users
# of the SDK.
def _any_unit_from_string(unit_string: str
                          ) -> UnsupportedUnit | DistanceUnit | AngleUnit:
  """Convert a unit from a unit string.

  This is useful in the case where the unit can be any unit. If the
  unit can only be a specific type of unit, use the functions
  on the appropriate enum.

  Parameters
  ----------
  unit_string
    String representing the unit to return.

  Returns
  -------
  DistanceUnit
    If unit_string corresponded to a distance unit.
  AngleUnit
    If unit_string corresponded to an angle unit.
  UnsupportedUnit
    If unit_string corresponded to neither an angle unit nor a distance unit.
  """
  # pylint: disable=protected-access
  unit = DistanceUnit._from_serialisation_string(unit_string)
  if unit is not DistanceUnit.UNKNOWN:
    return unit

  unit = AngleUnit._from_serialisation_string(unit_string)
  if unit is not AngleUnit.UNKNOWN:
    return unit

  return UnsupportedUnit(unit_string)
