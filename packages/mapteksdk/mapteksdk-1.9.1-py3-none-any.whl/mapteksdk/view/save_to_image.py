"""Function for saving a view to an image file."""
###############################################################################
#
# (C) Copyright 2024, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import os
import pathlib
import typing

from mapteksdk.overwrite_modes import OverwriteMode
from mapteksdk.view.view import ViewController, ViewWindow

if typing.TYPE_CHECKING:
  from collections.abc import Iterable
  from mapteksdk.data import ObjectID, DataObject

def _choose_better_camera_for_image(view: ViewController):
  """Choose a better camera based on the data given.

  The default camera is top-down which works well for data that should be
  viewed in plan view. However, other data doesn't look great from that view.

  The idea is to choose a better camera orientation based on the data. If the
  object was the Standford Bunny then rather than top-down it will be front
  on.

  Parameters
  ----------
  view
    The view controller to apply the better camera to for taking an image.
  """
  extent = view.scene_extents()
  span_x, span_y, span_z = extent.span

  if span_z < 0.00001 and span_z > -0.00001:
    return

  ratio_xz = span_x / span_z
  ratio_yz = span_y / span_z

  if ratio_xz < 10 or ratio_yz < 10:
    # Use a different orientation.
    look_vector = (1.0, 1.0, -0.5)
    up_vector = (0.25, 0.25, 1)

    view.view_objects_by_extents(extent, look_vector, up_vector)

    # Since this is for an image rather than an interactive view, it can be
    # zoomed in as it doesn't need to allow the data to fit in the view
    # after it has been rotated, which is what view_objects_by_extents()
    # does.
    # pylint: disable=protected-access
    view._scale_linear_field_of_view(0.8)


def save_to_image(
  objects: Iterable[ObjectID | DataObject | str],
  path: os.PathLike | str,
  overwrite: OverwriteMode = OverwriteMode.ERROR,
) -> pathlib.Path:
  """Save the given objects to an image file as they would be seen in a view.

  The camera will either look top-down at the objects or from the front.

  Objects may obstruct other objects. This means one or more of the objects
  provided may not be seen in the resulting image.

  Parameters
  ----------
  objects
    The objects included in the image.
  path
    The path to where the image should be saved.
    This ideally should have a PNG extension.
  overwrite
    How to handle writing an image to path if a file already exists
    there.

  Returns
  ------
  pathlib.Path
    The path of the resulting image.

  Raises
  ------
  ApplicationTooOldError
    If you should use a newer version of the application as the feature is
    not available with the version connected to.
  RuntimeError
    If the view can not be opened.
  NotADirectoryError
    If the directory the image should be saved in does not exist or is not a
    directory.
  FileExistsError
    If overwrite is OverwriteMode.ERROR and path already exists.
  OSError
    If overwrite is OverwriteMode.OVERWRITE and path can't be deleted.
  """
  with ViewWindow(width=1920, height=1080) as view_window:
    view = ViewController(view_window.view_id)
    try:
      view.add_objects(objects)

      if objects:
        _choose_better_camera_for_image(view)

      try:
        image_path = view_window.save_to_image(
          path, overwrite=overwrite)
      except FileExistsError as error:
        view_window.logger.error("Image was unable to be saved: %s", error)
        raise
    finally:
      view.close()

  return image_path
