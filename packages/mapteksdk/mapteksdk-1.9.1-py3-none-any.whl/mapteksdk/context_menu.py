"""Module for scripts run from context menus.

Workbench customisation can be used to add Python Scripts to context menus.
This module contains functions designed for scripts run from context menus.
"""
###############################################################################
#
# (C) Copyright 2022, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

import os

import numpy as np

from .data.base import DataObject
from .data.objectid import ObjectID

_MAPTEK_SDK_CONTEXT_MENU_OBJECT = "MAPTEK_SDK_CONTEXT_MENU_OBJECT"
"""Environment variable used to communicate context menu object."""

_MAPTEK_SDK_CONTEXT_MENU_LOCATION = "MAPTEK_SDK_CONTEXT_MENU_LOCATION"
"""Environment variable used to communicate the context menu location."""

_NO_CONTEXT_INFORMATION_ERROR_MESSAGE = ("Failed to read context information. "
  "The script was not run from a context menu or there was no compatible "
  "object under the mouse when the context menu was opened.")

class NoContextInformationError(RuntimeError):
  """Exception raised when the context menu information does not exist."""


class InvalidContextInformationError(ValueError):
  """Error raised when the context menu information is invalid."""


def context_location() -> np.ndarray:
  """The location of the mouse pointer when the context menu was opened.

  Typically this will be a point on the context object. This can be any point
  on the object and often will not correspond with any of the points in the
  points property of the context object.

  Returns
  -------
  numpy.ndarray
    Numpy array of the form [X, Y, Z] representing the location of the mouse.

  Raises
  ------
  NoContextInformationError
    If the script was not run from a context menu or there were no compatible
    objects under the mouse when the context menu was opened.
  InvalidContextInformationError
    If the context location could not be parsed. This typically indicates
    a version mismatch.
  """
  location_string = None
  try:
    location_string = os.environ[_MAPTEK_SDK_CONTEXT_MENU_LOCATION]
  except KeyError:
    # This is purposefully discarding the inner exception to avoid leaking the
    # environment variable into the error message.
    raise NoContextInformationError(_NO_CONTEXT_INFORMATION_ERROR_MESSAGE
      ) from None

  location_string = location_string.strip("()")

  try:
    return np.fromiter((
      float(x) for x in location_string.split(",", maxsplit=2)),
      count=3,
      dtype=float)
  except ValueError as error:
    raise InvalidContextInformationError(
      f"Failed to parse context location: '{location_string}'") from error

def context_object_path() -> str:
  """The path to the context object in the Project.

  This can be passed to Project.edit() or Project.read() to open the context
  object.

  Returns
  -------
  str
    The path to the object the mouse was over when the context menu was opened.

  Raises
  ------
  NoContextInformationError
    If the script was not run from a context menu or there were no compatible
    objects under the mouse when the context menu was opened.
  """
  try:
    return os.environ[_MAPTEK_SDK_CONTEXT_MENU_OBJECT]
  except KeyError:
    # This is purposefully discarding the inner exception to avoid leaking the
    # environment variable into the error message.
    raise NoContextInformationError(_NO_CONTEXT_INFORMATION_ERROR_MESSAGE
      ) from None

def context_object_id() -> ObjectID[DataObject]:
  """The object ID of the context object in the Project.

  Unlike context_object_path(), this will fail if the script is not
  connected to an application. This can be passed to Project.edit() or
  Project.read() to read the context object.

  Returns
  -------
  ObjectID
    The object ID of the object the mouse was over when the context menu
    was opened.

  Raises
  ------
  NoContextInformationError
    If the script was not run from a context menu or there were no compatible
    objects under the mouse when the context menu was opened.
  InvalidContextInformationError
    If the context object could not be found.
  NoConnectedApplicationError
    If this function is called when the script is not connected to an
    application.
  """
  try:
    return ObjectID.from_path(context_object_path())
  except InvalidContextInformationError:
    # InvalidContextInformationError inherits from ValueError. This block
    # ensures it is not caught by the following block.
    raise
  except ValueError as error:
    raise InvalidContextInformationError(
      "Failed to find the context object. The script may have connected "
      "to the wrong application."
    ) from error
