"""Point data types.

This module contains data types where the most complicated primitive they
use is points. Though many other objects use points, the types defined
here only use points.

Currently there is only one such data type (PointSet).

"""
###############################################################################
#
# (C) Copyright 2020, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

from __future__ import annotations

from contextlib import contextmanager
import logging
import typing

import numpy as np
import pandas as pd

from ..internal.lock import LockType
from .base import Topology, StaticType
from .primitives import PointProperties, PointDeletionProperties
from .objectid import ObjectID

# pylint: disable=too-many-lines
# pylint: disable=too-many-instance-attributes
log = logging.getLogger("mapteksdk.data")

class PointSet(Topology, PointProperties, PointDeletionProperties):
  """A pointset is a set of three dimensional points.

  See Also
  --------
  :documentation:`point-set` : Help page for this class.
  """
  # :Warning: Changing these constants will break backwards compatibility.
  X: typing.ClassVar[str] = "X"
  """The column name for the X values."""

  Y: typing.ClassVar[str] = "Y"
  """The column name for the Y values."""

  Z: typing.ClassVar[str] = "Z"
  """The column name for the Z values."""

  RED: typing.ClassVar[str] = "R"
  """The column name for the red component of the point colour."""

  GREEN: typing.ClassVar[str] = "G"
  """The column name for the green component of the point colour."""

  BLUE: typing.ClassVar[str] = "B"
  """The column name for the blue component of the point colour."""

  ALPHA: typing.ClassVar[str] = "A"
  """The column name for the alpha component of the point colour."""

  Visible: typing.ClassVar[str] = "Visible"
  """The column name for the point visibility."""

  Selected: typing.ClassVar[str] = "Selected"
  """The column name for the point selection."""

  # pylint: disable=too-many-instance-attributes
  def __init__(self, object_id=None, lock_type=LockType.READWRITE):
    if not object_id:
      object_id = ObjectID(self._modelling_api().NewPointSet())
    super().__init__(object_id, lock_type)
    self._initialise_point_properties(False)

  @classmethod
  def static_type(cls) -> StaticType:
    """Return the type of point set as stored in a Project.

    This can be used for determining if the type of an object is a point set.

    """
    return cls._modelling_api().PointSetType()

  def _extra_invalidate_properties(self):
    super()._extra_invalidate_properties()
    self._invalidate_point_properties()

  def _record_object_size_telemetry(self):
    self._record_point_telemetry()

  @contextmanager
  def dataframe(
      self,
      save_changes=True,
      attributes=None,
      include_colours=True,
      include_visibility=True,
      include_selection=True):
    """Context managed representation of the PointSet as a Pandas Dataframe.

    Parameters
    ----------
    save_changes : bool
      If save_changes = False then any changes to the data frame will not
      be propagated to the point set.
      If save_changes = True (default) and the point set is opened for editing,
      all changes made to the dataframe will be propagated to the point set when
      the with block finishes.
      This is ignored if the point set is opened in read mode - in that case
      changes to the dataframe will never be made to the point set.
    attributes : iterable
      List of names of point attributes to include as extra columns in the
      DataFrame. If None (default) all existing point properties are included
      in the dataframe. For better performance, only include the point
      attributes you want in the DataFrame.
    include_colours : bool
      If True (default), the point colours will be included in the dataframe
      as the "R", "G", "B" and "A" columns.
      If False, the point colours will not be included in the dataframe
      (And thus the dataframe will not have the "R", "G", "B", "A" columns).
      Setting this to False is more efficient than dropping these columns
      from the dataframe.
    include_visibility : bool
      If True (default), the point visibility will be included in the dataframe
      as the "Visible" column.
      If False, the point visibility will not be included and the dataframe
      will not have a "Visible" column.
      Setting this to False is more efficient than dropping this column
      from the dataframe.
    include_selection : bool
      If True (default), the point selection will be included in the dataframe
      as the "Selected" column.
      If False, the point selection will not be included and the dataframe
      will not have a "Selected" column.
      Setting this to False is more efficient than dropping this column
      from the dataframe.

    Yields
    ------
    pandas.DataFrame
      DataFrame representing the PointSet. Columns include:
      ['X', 'Y', 'Z', 'R', 'G', 'B', 'A', 'Visible', 'Selected']
      Any point attributes included in the DataFrame are
      inserted after Selected.

    Raises
    ------
    KeyError
      If attributes contains an attribute name which doesn't exist.
    KeyError
      If the X, Y or Z columns of the data frame are dropped.

    Notes
    -----
    If save_changes is True, dropping the R, G or B column will cause
    the red, green or blue component of the colour to be set to 0.
    Dropping the A column will cause the alpha of all points to be
    set to 255.
    Dropping the Visible column will cause all points to be set to
    be visible.
    Dropping the Selected column will cause all points to be set to
    be not selected.
    Dropping a primitive attribute column will cause that primitive
    attribute to be deleted.

    Examples
    --------
    Use pandas to hide all points with Z less than 15.

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import PointSet
    >>> project = Project()
    >>> with project.new("cad/my_points", PointSet) as new_set:
    ...     new_set.points = [[1, 2, 3], [5, 5, 16], [-1, -6, -16]]
    ...     with new_set.dataframe() as frame:
    ...         frame.loc[frame.Z < 15, "Visible"] = False
    >>>     print(new_set.point_visibility)
    [False True False]

    Calculate and print the mean 'redness' of points using pandas.

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import PointSet
    >>> project = Project()
    >>> with project.new("cad/my_other_points", PointSet) as new_set:
    ...     new_set.points = [[1, 2, 3], [5, 5, 16], [-1, -6, -16]]
    ...     new_set.point_colours = [[100, 0, 0], [150, 0, 0], [200, 50, 50]]
    >>> with project.read("cad/my_other_points") as read_set:
    ...     with read_set.dataframe() as frame:
    ...         print(frame.loc[:, 'R'].mean())
    150.0

    Populate a point property with if the x value of the point is
    negative or positive.

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import PointSet
    >>> project = Project()
    >>> with project.new("cad/positive_points", PointSet) as new_set:
    ...     new_set.points = [[-1, 3, 9], [1, 4, -5], [-5, 2, 3]]
    ...     new_set.point_attributes['negative_x'] = [False] * 3
    ...     with new_set.dataframe() as frame:
    ...         frame.loc[frame.X < 0, 'negative_x'] = True
    ...         frame.loc[frame.X >= 0, 'negative_x'] = False
    ...     print(new_set.point_attributes['negative_x'])
    [True False True]

    When extracting the values of points as a pandas dataframe, you
    can set it to not save changes. This way you can make changes
    to the Dataframe without changing the original point set.
    In the below example, all points with red greater than or equal
    to 200 have their red set to zero in the dataframe and prints them.
    However when the with statement ends, the points are left unchanged
    - when the points colours are printed, they are the same as before
    the dataframe.
    Use this to work with a temporary copy of your data.

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import PointSet
    >>> project = Project()
    >>> with project.new("cad/my_nice_points", PointSet) as new_set:
    ...     new_set.points = [[1, 2, 3], [5, 5, 16], [-1, -6, -16]]
    ...     new_set.point_colours = [[100, 0, 0], [150, 0, 0], [200, 50, 50]]
    ...     with new_set.dataframe(save_changes=False) as frame:
    ...         frame.loc[frame.R >= 200, 'R'] = 0
    ...         print(frame.loc[:, 'R'])
    ...     print(new_set.point_colours)
    0    100
    1    150
    2      0
    Name: R, dtype: uint8
    [[100   0   0 255]
     [150   0   0 255]
     [200  50  50 255]]

    """
    log.info("Access pandas dataframe of %r, %s", self, self.id)
    if attributes is None:
      attributes = list(self.point_attributes.names)
    df_pointset = self._get_pandas(
      attributes, include_colours, include_visibility, include_selection)
    try:
      yield df_pointset
    finally:
      if save_changes and not self.is_read_only:
        log.info("Write pandas dataframe changes to %r, %s", self, self.id)
        self._put_pandas(
          df_pointset, attributes, include_colours, include_visibility,
          include_selection)
      else:
        log.info("Read-only finished with pandas dataframe of %s, %s", self,
                 self.id)
      del df_pointset

  def _get_pandas(
      self,
      included_names,
      include_colours,
      include_visibility,
      include_selection):
    """Provides representation of entire PointSet as a Pandas Dataframe.

    Parameters
    ----------
    included_names : iterable
      Iterable of attribute names to include in the DataFrame.
    include_colours : bool
      True if the point colours should be included in the dataframe.
    include_visibility : bool
      True if the point visibility should be included in the dataframe.
    include_selection : bool
      True if the point selection should be included in the dataframe.

    """
    # Putting the columns into a dictionary allows pandas to maintain
    # the data types when creating the dataframe.
    frame_dictionary: dict[str, np.ndarray] = {
      PointSet.X : self.points[:, 0],
      PointSet.Y : self.points[:, 1],
      PointSet.Z : self.points[:, 2],
    }

    # Maintain a list of column names. This determines the order of the
    # columns in the final dataframe.
    column_names = list(frame_dictionary.keys())

    if include_colours:
      frame_dictionary[PointSet.RED] = self.point_colours[:, 0]
      frame_dictionary[PointSet.GREEN] = self.point_colours[:, 1]
      frame_dictionary[PointSet.BLUE] = self.point_colours[:, 2]
      frame_dictionary[PointSet.ALPHA] = self.point_colours[:, 3]

      # Insert the colour names into the dictionary after Z but
      # before visible.
      column_names.extend(
        (PointSet.RED, PointSet.GREEN, PointSet.BLUE, PointSet.ALPHA))

    if include_visibility:
      frame_dictionary[PointSet.Visible] = self.point_visibility
      column_names.append(PointSet.Visible)

    if include_selection:
      frame_dictionary[PointSet.Selected] = self.point_selection
      column_names.append(PointSet.Selected)

    # Add the primitive attributes to the dictionary.
    for name in included_names:
      frame_dictionary[name] = self.point_attributes[name]
      column_names.append(name)
    return pd.DataFrame(frame_dictionary, columns=column_names)

  def _put_pandas(self, point_collection, included_names, include_colours,
      include_visibility, include_selection):
    """Stores pandas dataframe back into numpy arrays for the object.

    If the R, G or B columns are not present, the corresponding component
    of the colour will be set to 0.
    If the A column is not present, the alpha of all points will be set to 255.
    If the Visible column is not present, all points will be made visible.
    If the Selected column is not present, all points will be set to
    not selected.
    If a primitive attribute is in included_names but is not in
    the DataFrame the primitive attribute will be deleted.

    Parameters
    ----------
    point_collection : pandas.DataFrame
      Pandas dataframe created by _get_pandas.
    include_names : iterable
      Iterable of primitive attributes to include.
    include_colours : bool
      If the point colours were included in the dataframe.
    include_visibility : bool
      If the point visibility was included in the dataframe.
    include_selection : bool
      If the point selection was included in the dataframe.

    Raises
    ------
    KeyError
      If X, Y or Z columns have been dropped.

    """
    try:
      self.points = point_collection[
        [PointSet.X, PointSet.Y, PointSet.Z]].values
    except KeyError as error:
      # Provide a specific error message if the caller dropped
      # the X, Y or Z columns.
      message = (
        f"Dropping or renaming the '{PointSet.X}', '{PointSet.Y}' or "
        f"'{PointSet.Z}' columns is not supported. "
        f"Columns: {point_collection.columns.tolist()}"
      )
      raise KeyError(message) from error

    # If the colours were included in the dataframe, write them
    # back to the point set.
    if include_colours:
      if PointSet.RED in point_collection.columns:
        self.point_colours[:, 0] = point_collection[PointSet.RED].values
      else:
        self.point_colours[:, 0] = 0
      if PointSet.GREEN in point_collection.columns:
        self.point_colours[:, 1] = point_collection[PointSet.GREEN].values
      else:
        self.point_colours[:, 1] = 0
      if PointSet.BLUE in point_collection.columns:
        self.point_colours[:, 2] = point_collection[PointSet.BLUE].values
      else:
        self.point_colours[:, 2] = 0
      if PointSet.ALPHA in point_collection.columns:
        self.point_colours[:, 3] = point_collection[PointSet.ALPHA].values
      else:
        self.point_colours[:, 3] = 255

    if include_visibility:
      if PointSet.Visible in point_collection.columns:
        self.point_visibility = point_collection[PointSet.Visible].values
      else:
        self.point_visibility[:] = True

    if include_selection:
      if PointSet.Selected in point_collection.columns:
        self.point_selection = point_collection[PointSet.Selected].values
      else:
        self.point_selection[:] = False

    names_to_delete = []
    for name in included_names:
      if name in point_collection.columns:
        typed_values = point_collection[name].values
        self.point_attributes[name] = typed_values
      else:
        names_to_delete.append(name)

    # By default this is a KeyView of the attributes dictionary
    # so deleting the attribute inside the loop will raise an exception
    # due to the size of the collection changing during iteration.
    for name in names_to_delete:
      self.point_attributes.delete_attribute(name)

  def _save_topology(self):
    self._save_point_properties()
