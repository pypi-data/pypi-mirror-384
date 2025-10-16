"""Colour map data types.

Colour maps (also known as legends) can be used to apply a colour schema to
other objects based on their properties (e.g. by primitive attribute, position,
etc).

The two supported types are:
  - NumericColourMap - Colour based on a numerical value.
  - StringColourMap  - Colour based on a string (letters/words) value.

See Also
--------
:documentation:`colour-map` : Help page for these classes.
"""
###############################################################################
#
# (C) Copyright 2020, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import ctypes
import logging
import typing

import numpy as np

from ..internal.data_property import DataProperty, DataPropertyConfiguration
from ..internal.lock import LockType
from ..internal.string_data_property import (
  StringDataProperty, StringDataPropertyConfiguration)
from ..internal.util import default_type_error_message
from .base import DataObject, StaticType
from .objectid import ObjectID
from .errors import InvalidColourMapError, StaleDataError
# pylint: disable=too-many-instance-attributes

if typing.TYPE_CHECKING:
  from collections.abc import Sequence, Iterable
  from ..common.typing import (
    ColourArray, ColourArrayLike, Colour, ColourLike, FloatArray,
    FloatArrayLike, StringArray, StringArrayLike)

log = logging.getLogger("mapteksdk.data")

class UnsortedRangesError(InvalidColourMapError):
  """Error raised when the ranges of a colour map are not sorted."""


class CaseInsensitiveDuplicateKeyError(InvalidColourMapError):
  """Error raised for case insensitive duplicate key.

  This is raised when attempting to add a key which only differs from an
  existing key by case to a case insensitive dictionary.
  """


class NumericColourMap(DataObject):
  """Numeric colour maps map numeric values to a colour.

  The colours can either be smoothly interpolated or within bands.

  Notes
  -----
  Numeric colour maps can either by interpolated or solid. They are
  interpolated by default.

  For an interpolated colour map, the colour transitions smoothly from
  one colour to the next based on the ranges. Thus there is one colour
  for each range value.

  e.g. Given:
    ranges = [1.5, 2.5, 3.5]
    colours = [red, green, blue]

  Then the colour map will transition from red at 1.5 to green at 2.5 and
  then to blue at 3.5.

  For a solid colour map, the colour is the same for all values between
  two ranges. Thus there must be one less colour than there are range
  values.

  e.g. Given:
    ranges = [1.5, 2.5, 3.5, 4.5]
    colours = [red, green, blue]

  All values between 1.5 and 2.5 will be red, all values between 2.5 and 3.5
  will be green and all values between 3.5 and 4.5 will be blue.

  Tip: The 'cm' module in matplotlib can generate compatible colour maps.

  Raises
  ------
  InvalidColourMapError
    If on save the ranges array contains less than two values.

  See Also
  --------
  mapteksdk.data.primitives.PrimitiveAttributes.set_colour_map() :
    Colour a topology object by a colour map.

  Examples
  --------
  Create a colour map which would colour primitives with a value
  between 0 and 50 red, between 50 and 100 green and between 100 and 150
  blue.

  >>> from mapteksdk.project import Project
  >>> from mapteksdk.data import NumericColourMap
  >>> project = Project()
  >>> with project.new("legends/colour_map", NumericColourMap) as new_map:
  >>>     new_map.interpolated = False
  >>>     new_map.ranges = [0, 50, 100, 150]
  >>>     new_map.colours = [[255, 0, 0], [0, 255, 0], [0, 0, 255]]

  Create a colour map which similar to above, but smoothly transitions
  from red to green to blue.

  >>> from mapteksdk.project import Project
  >>> from mapteksdk.data import NumericColourMap
  >>> project = Project()
  >>> with project.new("legends/interpolated_map", NumericColourMap) as new_map:
  >>>     new_map.interpolated = True
  >>>     new_map.ranges = [0, 75, 150]
  >>>     new_map.colours = [[255, 0, 0], [0, 255, 0], [0, 0, 255]]

  Colour a surface using a colour map by the "order" point_attribute.
  This uses the colour map created in the first example so make sure
  to run that example first.

  >>> from mapteksdk.project import Project
  >>> from mapteksdk.data import Surface
  >>> points = [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
  ...           [0.5, 0.5, 0.5], [0.5, 0.5, -0.5]]
  >>> facets = [[0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4],
  ...           [0, 1, 5], [1, 2, 5], [2, 3, 5], [3, 0, 5]]
  ... order = [20, 40, 60, 80, 100, 120, 140, 75]
  >>> project = Project()
  >>> colour_map_id = project.find_object("legends/colour_map")
  >>> with project.new("surfaces/ordered_surface", Surface) as surface:
  ...     surface.points = points
  ...     surface.facets = facets
  ...     surface.point_attributes["order"] = order
  ...     surface.point_attributes.set_colour_map("order", colour_map_id)

  Edit the colour map associated with the surface created in the previous
  example so make sure to run that first.

  >>> from mapteksdk.project import Project
  >>> from mapteksdk.data import NumericColourMap
  >>> project = Project()
  >>> with project.edit("surfaces/ordered_surface") as my_surface:
  >>>   with project.edit(my_surface.get_colour_map()) as cm:
  >>>     pass # Edit the colour map here.

  """
  def __init__(
      self,
      object_id: ObjectID | None=None,
      lock_type: LockType=LockType.READWRITE):
    self.__upper_cutoff: Colour | None = None
    self.__lower_cutoff: Colour | None = None
    is_new = not object_id
    if is_new:
      object_id = ObjectID(self._modelling_api().NewNumericColourMap())
    super().__init__(object_id, lock_type)
    initial_ranges: np.ndarray | None = None
    initial_colours: np.ndarray | None = None
    self.__interpolated: bool = True
    if not is_new:
      loaded_values = self._get_properties()
      initial_ranges = loaded_values[0]
      initial_colours = loaded_values[1]
      self.interpolated = loaded_values[2]
      self.upper_cutoff = loaded_values[3]
      self.lower_cutoff = loaded_values[4]
    # This is only used to handle the cached values. The loading and
    # saving is handled externally because the ranges and colours can't
    # be loaded independently.
    self.__ranges: DataProperty = DataProperty(
      self._lock,
      DataPropertyConfiguration(
        name="ranges",
        dtype=ctypes.c_float,
        default=np.nan,
        column_count=1,
        load_function=None,
        save_function=None,
        primitive_count_function=None,
        cached_primitive_count_function=None,
        set_primitive_count_function=None,
        is_colour_property=False,
        immutable=False,
        raise_on_error_code=None
      ),
      initial_values=initial_ranges
    )
    self.__colours: DataProperty = DataProperty(
      self._lock,
      DataPropertyConfiguration(
        name="colours",
        dtype=ctypes.c_uint8,
        default=[0, 255, 0, 255],
        column_count=4,
        load_function=None,
        save_function=None,
        primitive_count_function=None,
        cached_primitive_count_function=lambda: self.colour_count,
        set_primitive_count_function=None,
        is_colour_property=True,
        immutable=False,
        raise_on_error_code=None,
      ),
      initial_values=initial_colours
    )

  @classmethod
  def static_type(cls) -> StaticType:
    """Return the type of numeric colour maps as stored in a Project.

    This can be used for determining if the type of an object is a numeric
    colour map.
    """
    return cls._modelling_api().NumericColourMapType()

  def _get_properties(self
      ) -> tuple[FloatArray, ColourArray, bool, Colour, Colour]:
    """Load properties from the Project."""
    # Get the numeric colour map number of entries
    count = self._modelling_api().ReadNumericColourMap(
      self._lock.lock, 0, None, None, None, None)
    # Create an array of float to hold the ranges
    ranges = (ctypes.c_float * (count + 1))()
    # Create array to hold colours
    colours = (ctypes.c_uint8 * (count * 8))()
    # Low count array
    lower_cutoff = (ctypes.c_uint8 * 4)()
    # up count array
    upper_cutoff = (ctypes.c_uint8 * 4)()

    # Read colour map from model
    self._modelling_api().ReadNumericColourMap(
      self._lock.lock, count, colours, ranges,
      lower_cutoff, upper_cutoff)

    read_colours = np.array(colours, dtype=ctypes.c_uint8)
    read_colours.shape = (-1, 4)

    # Guess whether the colour map is solid or interpolated based on the
    # read colours.
    # For a solid colour map every odd colour will be equal to every even
    # colour.
    # e.g. [red, red, green, green, blue, blue, yellow]
    # For an interpolated colour map, not every odd colour will be equal.
    # e.g. [red, green, green, blue, blue, yellow]
    # :NOTE: If all of the colours in an interpolated colour map are the
    # same, this will determine that it is a solid colour map.
    interpolated = not np.array_equal(read_colours[::2], read_colours[1::2])

    if interpolated:
      # If the array was:
      # [red, red, green, green, blue, blue, yellow]
      # Then we want:
      # [red, green, blue, yellow]
      # This is every even colour and the final colour.
      colour_count = (read_colours.shape[0] // 2) + 1
      actual_colours = np.empty(
        (colour_count, 4), dtype=ctypes.c_uint8
      )
      actual_colours[:-1] = read_colours[::2]
      actual_colours[-1] = read_colours[-1]
    else:
      # If the array was:
      # [red, red, green, green, blue, blue, yellow]
      # Then we want:
      # [red, green, blue, yellow]
      # Which is every even (or odd) colour.
      actual_colours = read_colours[::2]

    array_ranges = np.array(ranges, dtype=ctypes.c_float)
    array_upper_cutoff = np.array(upper_cutoff, dtype=ctypes.c_uint8)
    array_lower_cutoff = np.array(lower_cutoff, dtype=ctypes.c_uint8)
    return (
      array_ranges,
      actual_colours,
      interpolated,
      array_upper_cutoff,
      array_lower_cutoff)

  @property
  def interpolated(self) -> bool:
    """If the colour map is interpolated.

    True by default. If you intend to set this to False, you should do
    so before assigning to the ranges and colours.

    For an interpolated colour map, there is one colour for each range
    value.

    For a solid colour map (interpolated=False), there is one less colour
    than ranges.
    """
    return self.__interpolated

  @interpolated.setter
  def interpolated(self, value: bool):
    self.__interpolated = value

  @property
  def intervals(self) -> int:
    """Returns the number of intervals in the colour map.

    Notes
    -----
    This is the length of the ranges array.
    """
    return self.ranges.shape[0]

  @property
  def colour_count(self) -> int:
    """The number of colours in the map.

    If the colour map is interpolated, there must be one colour for
    each range value.

    If the colour map is solid, there is one less colour than there are
    range values.
    """
    if self.interpolated:
      return self.intervals
    count = self.intervals
    if count < 1:
      return 0
    return self.intervals - 1

  @property
  def colours(self) -> ColourArray:
    """The colours in the colour map.

    If the colour map contains N colours, this is of the form:
    [[r1, g1, b1, a1], [r2, g2, b2, a2], ..., [rN, gN, bN, aN]].

    If interpolated = True, the length of this array should be equal to
    the length of the ranges array.
    If interpolated = False, the length of this array should be equal to
    the length of the ranges array minus one.

    Raises
    ------
    RuntimeError
      If set to None.
    """
    return self.__colours.values

  @colours.setter
  def colours(self, colours: ColourArrayLike):
    if colours is None:
      raise RuntimeError("Clearing cached colours is not supported.")
    self.__colours.values = colours

  @property
  def ranges(self) -> FloatArray:
    """The boundaries of the colour map.

    Array of numbers used to define where colour transitions occur
    in the colour map.
    For example, if ranges = [0, 50, 100] and the colour map is solid,
    then between 0 and 50 the first colour would be used and between
    50 and 100 the second colour would be used.

    If the colour map is interpolated, then the first colour would be
    used at 0 and between 0 and 50 the colour would slowly change to
    the second colour (reaching the second colour at 50). Then between
    50 and 100 the colour would slowly transition from the second
    colour to the third colour.

    Raises
    ------
    InvalidColourMapError
      If set to have fewer than two values.
    UnsortedRangesError
      If ranges is not sorted.
    ValueError
      If set to an array containing a non-numeric value.
    RuntimeError
      If set to None.

    Notes
    -----
    This array dictates the intervals value and also controls the
    final length of the colours array when saving.
    """
    return self.__ranges.values

  @ranges.setter
  def ranges(self, ranges: FloatArrayLike):
    if ranges is None:
      raise RuntimeError("Clearing cached ranges is not supported.")
    if len(ranges) < 2:
      raise InvalidColourMapError(
        "Ranges must contain at least two values.")
    if not np.all(ranges[:-1] <= ranges[1:]): # type: ignore
      raise UnsortedRangesError("Ranges must be sorted in ascending order.")
    self.__ranges.values = ranges

  @property
  def upper_cutoff(self) -> Colour:
    """Colour to use for values which are above the highest range.

    For example, if ranges = [0, 50, 100] then this colour is used for any
    value greater than 100.
    The default value is Red ([255, 0, 0, 255])

    Notes
    -----
    Set the alpha value to 0 to make this colour invisible.
    """
    if self.__upper_cutoff is None:
      self.__upper_cutoff = np.array(
        [255, 0, 0, 255], dtype=ctypes.c_uint8)
    return self.__upper_cutoff

  @upper_cutoff.setter
  def upper_cutoff(self, upper_cutoff: ColourLike):
    if upper_cutoff is None:
      self.__upper_cutoff = None
      return

    if self.__upper_cutoff is None:
      new_cutoff = np.empty((4,), ctypes.c_uint8)
    else:
      new_cutoff = self.__upper_cutoff

    try:
      new_cutoff[:] = upper_cutoff
    except ValueError:
      new_cutoff[:3] = upper_cutoff
    self.__upper_cutoff = new_cutoff

  @property
  def lower_cutoff(self) -> Colour:
    """Colour to use for values which are below the lowest range.

    For example, if ranges = [0, 50, 100] then this colour is used for any
    value lower than 0.
    The default value is blue ([0, 0, 255, 255]).

    Notes
    -----
    Set the alpha value to 0 to make these items invisible.
    """
    if self.__lower_cutoff is None:
      self.__lower_cutoff = np.array(
        [0, 0, 255, 255], dtype=ctypes.c_uint8)
    return self.__lower_cutoff

  @lower_cutoff.setter
  def lower_cutoff(self, lower_cutoff: ColourLike):
    if lower_cutoff is None:
      self.__lower_cutoff = None
      return

    if self.__lower_cutoff is None:
      new_cutoff = np.empty((4,), ctypes.c_uint8)
    else:
      new_cutoff = self.__lower_cutoff

    try:
      new_cutoff[:] = lower_cutoff
    except ValueError:
      new_cutoff[:3] = lower_cutoff
    self.__lower_cutoff = new_cutoff

  def colours_for(self, values: Sequence[float]) -> ColourArray:
    """Get the colour corresponding to each value in the input sequence.

    For each value in values, this returns the colour associated
    with that value based on this colour map.

    Parameters
    ----------
    values
      Values to get the colour for.

    Returns
    -------
    ColourArray
      The colour for each value in values.

    Raises
    ------
    StaleDataError
      If there may be unsaved changes to the colours, ranges or cutoff
      values.
    TypeError
      If values is not a sequence of floats.

    Examples
    --------
    This function is useful for when objects are coloured via numeric colour
    maps, because in such cases the primitive colour arrays do not contain the
    colours. The following function returns the colours of the points
    even if the points are coloured with a numeric colour map (with
    appropriate error checking):

    >>> def get_point_colours_from_colour_map(
    ...         project: Project,
    ...         oid: ObjectID) -> np.ndarray:
    >>>     '''Read the point colours generated from the associated colour map.
    ...
    ...     Parameters
    ...     ----------
    ...     project
    ...       Project to use to read the object.
    ...     oid
    ...       ObjectID of the object to read the colours of.
    ...
    ...     Returns
    ...     -------
    ...     np.ndarray
    ...       Array of the colours for each point generated from the associated
    ...       colour map.
    ...
    ...     Raises
    ...     ------
    ...     ValueError
    ...       If the object is not coloured using a colour map, if the colour
    ...       map is not a NumericColourMap, of if the colour map is not
    ...       coloured using a point attribute.
    ...     '''
    ...     with project.edit(oid) as data_object:
    ...         colour_map_id = data_object.get_colour_map()
    ...         if colour_map_id is None:
    ...             raise ValueError(
    ...                 "The object is not coloured using a colour map."
    ...             )
    ...         if not colour_map_id.is_a(NumericColourMap):
    ...             raise ValueError(
    ...                 "Cannot get colours for non-numeric colour map."
    ...             )
    ...         colour_map_attribute = None
    ...         try:
    ...             point_attributes = data_object.point_attributes
    ...             colour_map_attribute = point_attributes.colour_map_attribute
    ...         except AttributeError:
    ...             # The object does not have point attributes.
    ...             pass
    ...         if colour_map_attribute is None:
    ...             raise ValueError(
    ...                 "Object is not coloured via a point attribute.")
    ...         with project.read(data_object.get_colour_map()) as colour_map:
    ...             return colour_map.colours_for(
    ...                 data_object.point_attributes[colour_map_attribute])
    """
    if not self.is_read_only:
      raise StaleDataError(
        "Cannot read colours on colour map open for editing."
      )
    return self._modelling_api().ColourMapGetColoursForValues(
      self._lock.lock,
      values
    )

  def _extra_invalidate_properties(self):
    pass

  def _record_object_size_telemetry(self):
    self._record_size_for("Intervals", self.intervals)

  def _save(self):
    if self.intervals < 2:
      raise InvalidColourMapError(
        "Colour maps must contain at least two ranges.")
    if self.interpolated:
      self._save_interpolated_map(
        self.intervals,
        self.colours,
        self.ranges,
        self.lower_cutoff,
        self.upper_cutoff)
    else:
      # Should be safe to save now:
      self._save_solid_map(self.intervals,
                            self.colours,
                            self.ranges,
                            self.lower_cutoff,
                            self.upper_cutoff)

  def _save_solid_map(
      self,
      intervals: int,
      colours: np.ndarray,
      ranges: np.ndarray,
      lower_cutoff: np.ndarray,
      upper_cutoff: np.ndarray):
    """Save the colour map as a solid colour map to the Project.

    Parameters
    ----------
    intervals : int
      The number of intervals in the colour map.
    colours : numpy.ndarray
      Array of colours as ctypes.c_uint8. The shape should be
      (intervals - 1, 4).
    ranges : numpy.ndarray
      Array of ranges as ctypes.c_float. The shape should be (intervals, ).
    lower_cutoff : numpy.ndarray
      The lower cutoff colour represented as four ctypes.c_uint8. The shape
      should be (4, ).
    upper_cutoff : numpy.ndarray
      The upper cutoff colour represented as four ctypes.c_uint8. The shape
      should be (4, ).
    """
    c_colours = (ctypes.c_uint8 * ((intervals - 1) * 4))()
    c_ranges = (ctypes.c_float * intervals)()
    c_lower_cutoff = (ctypes.c_uint8 * 4)()
    c_upper_cutoff = (ctypes.c_uint8 * 4)()
    c_colours[:] = colours.reshape(-1)
    c_ranges[:] = ranges.reshape(-1)
    c_lower_cutoff[:] = lower_cutoff
    c_upper_cutoff[:] = upper_cutoff
    self._modelling_api().UpdateNumericColourMapSolid(self._lock.lock,
                                            intervals,
                                            c_colours,
                                            c_ranges,
                                            c_lower_cutoff,
                                            c_upper_cutoff)

  def _save_interpolated_map(
      self,
      intervals: int,
      colours: np.ndarray,
      ranges: np.ndarray,
      lower_cutoff: np.ndarray,
      upper_cutoff: np.ndarray):
    """Save the colour map as an interpolated colour map to the Project.

    Parameters
    ----------
    intervals : int
      The number of intervals in the colour map.
    colours : numpy.ndarray
      Array of colours as ctypes.c_uint8. The shape should be
      (intervals, 4).
    ranges : numpy.ndarray
      Array of ranges as ctypes.c_float. The shape should be (intervals, ).
    lower_cutoff : numpy.ndarray
      The lower cutoff colour represented as four ctypes.c_uint8. The shape
      should be (4, ).
    upper_cutoff : numpy.ndarray
      The upper cutoff colour represented as four ctypes.c_uint8. The shape
      should be (4, ).
    """
    c_colours = (ctypes.c_uint8 * (intervals * 4))()
    c_ranges = (ctypes.c_float * intervals)()
    c_lower_cutoff = (ctypes.c_uint8 * 4)()
    c_upper_cutoff = (ctypes.c_uint8 * 4)()
    c_colours[:] = colours.reshape(-1)
    c_ranges[:] = ranges.reshape(-1)
    c_lower_cutoff[:] = lower_cutoff
    c_upper_cutoff[:] = upper_cutoff

    self._modelling_api().UpdateNumericColourMapInterpolated(self._lock.lock,
                                                   intervals,
                                                   c_colours,
                                                   c_ranges,
                                                   c_lower_cutoff,
                                                   c_upper_cutoff)

class StringColourMap(DataObject):
  """Colour maps which maps colours to strings rather than numbers.

  Raises
  ------
  InvalidColourMapError
    If on save the legends array is empty.

  Warnings
  --------
  Colouring objects other than PointSets and DenseBlockModels using string
  colour maps may not be supported by applications (but may be supported in
  the future). If it is not supported the object will either be coloured red
  in the viewer or the application will crash when attempting to view the
  object.

  Notes
  -----
  Given index i, the key colour_map.legend[i] has colour colour_map.colour[i].

  The keys are case sensitive - "Unknown" and "unknown" are not considered
  to be the same key.

  Set value for a (alpha) to 0 to make out of bounds items invisible.

  Examples
  --------
  Create a string colour map which maps "Gold" to yellow, "Silver" to grey
  and "Iron" to red.

  >>> from mapteksdk.project import Project
  >>> from mapteksdk.data import StringColourMap
  >>> project = Project()
  >>> with project.new("legends/map_dict", StringColourMap) as new_map:
  ...     new_map["Gold"] = [255, 255, 0]
  ...     new_map["Silver"] = [100, 100, 100]
  ...     new_map["Iron"] = [255, 0, 0]

  Read colours from the colour map as if it was a dictionary.

  >>> from mapteksdk.project import Project
  >>> project = Project()
  >>> with project.read("legends/map_dict") as read_map:
  ...    # Sets gold_colour to the colour corresponding to the "Gold"
  ...    # key in the colour map.
  ...    # (This will raise a KeyError if "Gold" is not part of the map.)
  ...    gold_colour = read_map["Gold"]
  ...    # Sets stone_in_map to True if the key "Stone" is in the colour
  ...    # map, otherwise it sets it to False.
  ...    # This is more typically used in if statements e.g.
  ...    # if "Stone" in read_map
  ...    stone_in_map = "Stone" in read_map
  ...    # This will delete the "Iron" key and its associated colour
  ...    # from the colour map.
  ...    del read_map["Iron"]
  """
  def __init__(
      self,
      object_id: ObjectID=None,
      lock_type: LockType=LockType.READWRITE):
    is_new = not object_id
    if is_new:
      object_id = ObjectID(self._modelling_api().NewStringColourMap())
    super().__init__(object_id, lock_type)
    initial_legend = None
    initial_colours = None
    initial_cutoff = None
    if not is_new:
      initial_legend, initial_colours, initial_cutoff = self._get_properties()
    self.__legend = StringDataProperty(
      lock=self._lock,
      configuration=StringDataPropertyConfiguration(
        name="legend",
        default="",
        load_function=None,
        save_function=None,
        primitive_count_function=None,
        cached_primitive_count_function=None
      ),
      initial_values=initial_legend
    )
    self.__colours = DataProperty(
      lock=self._lock,
      configuration=DataPropertyConfiguration(
        name="colours",
        dtype=ctypes.c_uint8,
        default=[0, 255, 0, 255],
        column_count=4,
        load_function=None,
        save_function=None,
        primitive_count_function=None,
        cached_primitive_count_function=lambda: self.intervals,
        set_primitive_count_function=None,
        is_colour_property=True,
        immutable=False
      ),
      initial_values=initial_colours
    )
    self.__cutoff = initial_cutoff
    self.__case_sensitive = None

  def __getitem__(self, key: str):
    self._raise_if_invalid()
    indices = self._get_indices_for_key(key)
    if indices.size == 0:
      raise KeyError(f"'{key}' not in colour map.")
    return self.colours[indices[0]]

  def __setitem__(self, key: str, value: ColourLike):
    self._raise_if_invalid()
    indices = self._get_indices_for_key(key)
    if indices.size == 0:
      self.__legend.values = np.append(self.legend, key)
      try:
        self.__colours.values[-1] = value
      except ValueError:
        # It might be an RGB colour.
        self.__colours.values[-1][:3] = value
    else:
      index = indices[0]
      try:
        self.__colours.values[index] = value
      except ValueError:
        # It might be an RGB colour.
        self.__colours.values[index][:3] = value

  def __delitem__(self, key: str):
    self._raise_if_invalid()
    indices = self._get_indices_for_key(key)
    if indices.size == 0:
      raise KeyError(f"Cannot delete non-existent key: {key}")
    original_colours = np.copy(self.colours)
    index = indices[0]
    self.__legend.values = np.delete(self.__legend.values, index)
    self.__colours.values = np.delete(original_colours, index, axis=0)

  def __contains__(self, key: str):
    self._raise_if_invalid()
    if not isinstance(key, str):
      return False
    return self._get_indices_for_key(key).size != 0

  @classmethod
  def static_type(cls) -> StaticType:
    """Return the type of string colour maps as stored in a Project.

    This can be used for determining if the type of an object is a string
    colour map.

    """
    return cls._modelling_api().StringColourMapType()

  def _get_indices_for_key(self, key: str) -> np.ndarray:
    """Get the indices in the legends array for a key.

    This handles case-insensitive key search.

    Parameters
    ----------
    key
      The key to search for in the legends array.

    Returns
    -------
    np.ndarray
      Array of indices into the legend array where the key was found.
      If the key is not in the legend array, this will be empty.
      If the key is in the legend array, this will contain a single index.

    Raises
    ------
    TypeError
      If key is not a string.
    """
    if not isinstance(key, str):
      raise TypeError(default_type_error_message("key", key, str))

    if self.case_sensitive:
      return np.where(self.legend == key)[0]

    target_key = key.upper()
    for i, cased_key in enumerate(self.legend):
      if cased_key.upper() == target_key:
        result = np.empty((1,), int)
        result[0] = i
        return result
    return np.empty((0,), int)

  def _raise_if_case_insensitive_duplicates(self, legend: Iterable[str]):
    """Raise an error if the legend contains case-insensitive duplicates.

    Parameters
    ----------
    legend
      Iterable to check if it contains case-insensitive duplicates.

    Raises
    ------
    CaseInsensitiveDuplicateKeyError
      If legend contains two strings which compare the same when upper
      cased.
    """
    key_set = set()
    for key in legend:
      upper_key = key.upper()
      if upper_key in key_set:
        raise CaseInsensitiveDuplicateKeyError(
          "The legend contained a key which only differed by case. "
          "Cannot use it for case insensitive legend."
        )
      key_set.add(upper_key)

  def _get_properties(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load properties from the Project.

    Returns
    -------
    tuple
      A tuple containing the legend, colours and cutoff values
      read from the Project.
    """
    # Get the number of entries
    count = self._modelling_api().ReadStringColourMap(
      self._lock.lock, 0, None, 0, None, None)

    legend = None
    colours = None
    cutoff = None

    if count > 0:
      # Get the length required to store all of the strings
      buffer_len = self._modelling_api().ReadStringColourMap(
        self._lock.lock, count, None, 0, None, None)
      # Create array to hold legend strings
      c_legend = ctypes.create_string_buffer(buffer_len)
      # Create array to hold colours
      c_colours = (ctypes.c_uint8 * (4 * count))()
      # Out of bounds colour
      c_cutoff = (ctypes.c_uint8 * 4)()

      self._modelling_api().ReadStringColourMap(
        self._lock.lock, count, c_legend, buffer_len,
        c_colours, c_cutoff)

      colours = np.array(c_colours, dtype=ctypes.c_uint8)
      colours.shape = (-1, 4)
      # Convert string buffer to byte array by splitting on null terminator \x00
      legend = np.array(bytearray(c_legend).decode(
        'utf-8').split('\x00'))[:-1] # Drop the final null delimiter
      cutoff = np.array(c_cutoff, dtype=np.uint8)
    return legend, colours, cutoff

  def get(self, key: str) -> Colour:
    """Get the colour associated with the specified key.

    If the key is not part of the colour map, cutoff colour
    will be returned.

    Parameters
    ----------
    key : str
      The key to get the associated colour for.

    Returns
    -------
    numpy.ndarray
      Numpy array of shape (4,) representing the colour for the specified
      key.

    Raises
    ------
    TypeError
      If the key is not a string.
    InvalidColourMapError
      If the legend and colours arrays have a different number of elements.
    """
    try:
      return self[key]
    except KeyError:
      return self.cutoff

  def colours_for(self, values: Sequence[str]) -> ColourArray:
    """Get the colours for the strings in the given sequence.

    Parameters
    ----------
    values
      Sequence of strings to get the colours for.

    Returns
    -------
    ColourArray
      Array of colours corresponding to the strings in values based on this
      colour map.
    """
    result = np.empty((len(values), 4), dtype=np.uint8)
    for i, value in enumerate(values):
      result[i] = self.get(value)
    return result

  @property
  def intervals(self) -> int:
    """Returns the number of intervals in the colour map.

    This is the length of the legend array.
    """
    return self.legend.shape[0]

  @property
  def legend(self) -> StringArray:
    """The string keys of the colour map.

    The string colour_map.legend[i] is mapped to colour_map.colours[i].

    Raises
    ------
    InvalidColourMapError
      If set to an array with zero elements.
    RuntimeError
      If set to None.

    Notes
    -----
    This must not contain duplicates.
    """
    return self.__legend.values

  @legend.setter
  def legend(self, legend: StringArrayLike):
    if legend is None:
      raise RuntimeError("Clearing cached legend is not supported.")
    if len(legend) == 0:
      raise InvalidColourMapError("Legend must contain at least one value.")
    if not self.case_sensitive:
      self._raise_if_case_insensitive_duplicates(legend)
    self.__legend.values = legend

  @property
  def colours(self) -> ColourArray:
    """The colours in the colour map.

    Raises
    ------
    RuntimeError
      If set to None.

    Notes
    -----
    This must have the same number of elements as the legend array.
    """
    return self.__colours.values

  @colours.setter
  def colours(self, colours: ColourArrayLike):
    if colours is None:
      raise RuntimeError("Clearing cached ranges is not supported.")
    self.__colours.values = colours

  @property
  def cutoff(self) -> Colour:
    """The colour to use for values which don't match any value in legends.

    Notes
    -----
    Set the alpha value to 0 to make these items invisible.

    The default is red: [255, 0, 0, 255]

    Examples
    --------
    If the legend = ["Gold", "Silver"] then this property defines the colour
    to use for values which are not in the legend (i.e. anything which is
    not "Gold" or "Silver"). For example, it would define what colour to
    represent 'Iron' or 'Emerald'.
    """
    if self.__cutoff is None:
      self.__cutoff = np.array(
        [255, 0, 0, 255], dtype=ctypes.c_uint8)
    return self.__cutoff

  @cutoff.setter
  def cutoff(self, cutoff: ColourLike):
    if cutoff is None:
      self.__cutoff = None
      return

    if self.__cutoff is None:
      new_cutoff = np.empty((4,), ctypes.c_uint8)
    else:
      new_cutoff = self.__cutoff

    try:
      new_cutoff[:] = cutoff
    except ValueError:
      new_cutoff[:3] = cutoff
    self.__cutoff = new_cutoff

  @property
  def case_sensitive(self) -> bool:
    """If the colour map is case sensitive.

    This is True (i.e. case sensitive) by default. When constructing
    a case-insensitive colour map it is preferable to set this to False
    before adding any keys. That will allow errors to be detected earlier
    and more accurately.

    Warnings
    --------
    If case_sensitive=False, this class will consider two keys to be the same
    if they are the same when converted to uppercase using str.upper().
    This is stricter than the condition used in Vulcan GeologyCore 2022.1
    (and older applications) which consider two keys to be the same if
    they are the same after uppercasing every english letter, ignoring
    non-english letters.

    Notes
    -----
    When connected to Vulcan GeologyCore 2022.1 (and older versions)
    colour maps are assumed to always be case sensitive, regardless of
    the configuration in the application and saving the colour map
    will cause it to be set to case sensitive.

    Examples
    --------
    A case sensitive colour map treats keys with different casing as
    different keys. For example, the colour map creating in the below
    example contains three keys "iron", "Iron" and "IRON" each of which
    has a different colour.

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import StringColourMap
    >>> if __name__ == "__main__":
    ...   with Project() as project:
    ...     with project.new("legends/sensitive_map", StringColourMap
    ...         ) as string_map:
    ...       # It is best to set case sensitive before adding any keys
    ...       # to the colour map.
    ...       string_map.case_sensitive = True
    ...       string_map["iron"] = [255, 0, 0, 255]
    ...       string_map["Iron"] = [0, 255, 0, 255]
    ...       string_map["IRON"] = [0, 0, 255, 255]
    ...       for key in string_map.legend:
    ...         print(key, ":", ",".join(str(x) for x in string_map[key]))
    iron : 255,0,0,255
    Iron : 0,255,0,255
    IRON : 0,0,255,255

    The following example is the same except that the colour map is
    case insensitive. This causes "iron", "Iron" and "IRON" to be considered
    the same key, thus each assignment overwrites the previous one resulting
    in the colour map containing a single key with the last value assigned
    to it:

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import StringColourMap
    >>> if __name__ == "__main__":
    ...   with Project() as project:
    ...     with project.new("legends/insensitive_map", StringColourMap
    ...         ) as string_map:
    ...       # It is best to set case sensitive before adding any keys
    ...       # to the colour map.
    ...       string_map.case_sensitive = False
    ...       string_map["iron"] = [255, 0, 0, 255]
    ...       string_map["Iron"] = [0, 255, 0, 255]
    ...       string_map["IRON"] = [0, 0, 255, 255]
    ...       for key in string_map.legend:
    ...         print(key, ":", ",".join(str(x) for x in string_map[key]))
    iron : 0,0,255,255
    """
    if self.__case_sensitive is None:
      self.__case_sensitive = self._modelling_api(
        ).StringColourMapGetCaseSensitive(self._lock.lock)
    return self.__case_sensitive

  @case_sensitive.setter
  def case_sensitive(self, new_value: bool):
    new_value = bool(new_value)
    if not new_value:
      self._raise_if_case_insensitive_duplicates(self.legend)
    self.__case_sensitive = new_value

  def _raise_if_invalid(self):
    """Raises an error if the ranges and colours arrays have different lengths.

    Raises
    ------
    InvalidColourMapError
      If the ranges and colours have different lengths.
    """
    if self.colours.shape[0] != self.legend.shape[0]:
      raise InvalidColourMapError(
        "The operation could not be completed because the colour map is in "
        f"an inconsistent state. It contains {self.colours.shape[0]} colours "
        f"and '{self.legend.shape[0]}' keys. The operation requires equal "
        "items in each array.")

  def _extra_invalidate_properties(self):
    pass

  def _record_object_size_telemetry(self):
    self._record_size_for("Keys", len(self.legend))

  def _save(self):
    self._raise_if_save_in_read_only()
    # Check all objects are ready to save
    if self.intervals == 0:
      raise InvalidColourMapError("Legend must contain at least one value.")

    if not self.case_sensitive:
      self._raise_if_case_insensitive_duplicates(self.legend)

    # Get the maximum length string from the array to allow setup of buffers
    max_string_length = np.max(np.vectorize(len)(self.legend))
    # Create string buffers allowing for additional null character on max len
    # Create one buffer for each legend value
    string_buffers = [ctypes.create_string_buffer(int(max_string_length + 1))
                      for _ in range(self.intervals)]
    # Get the pointers for each buffer
    string_pointers = (ctypes.c_char_p * self.intervals) \
                      (*map(ctypes.addressof, string_buffers))
    # Populate the buffers with the legend values
    for i, key in enumerate(self.legend):
      string_pointers[i] = key.encode('utf-8')

    c_colours = (ctypes.c_uint8 * (self.intervals * 4))()
    c_colours[:] = self.colours.reshape(-1)

    c_cutoff = (ctypes.c_uint8 * 4)()
    c_cutoff[:] = self.cutoff

    self._modelling_api().UpdateStringColourMap(
      self._lock.lock,
      self.intervals,
      ctypes.byref(string_pointers),
      c_colours,
      c_cutoff)

    self._modelling_api().StringColourMapSetCaseSensitive(
      self._lock.lock, self.case_sensitive)

ColourMap = typing.Union[StringColourMap, NumericColourMap]
"""Union containing all objects which are colour maps."""
