"""Internal functions for working with the 3D viewer.

For querying an existing view see: mapteksdk.operations
Otherwise see: mapteksdk.view.

Warnings
--------
Vendors and clients should not develop scripts or applications against
this package. The contents may change at any time without warning.
"""
###############################################################################
#
# (C) Copyright 2024, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

import ctypes
import ctypes.wintypes
import logging
import os
import pathlib
import threading
import typing

from mapteksdk.capi import DataEngine, Viewer
from mapteksdk.data.objectid import ObjectID
from mapteksdk.internal.mcp import McpCallback
from mapteksdk.internal.transaction_elemental import PathBody
from mapteksdk.internal.comms import (
  Request,
  Response,
  Message,
  default_manager,
)
from mapteksdk.internal.comms import types as comm_types
from mapteksdk.internal.overwrite import unique_filename
from mapteksdk.overwrite_modes import OverwriteMode


class NewViewMessageV1(Message):
  """Defines the NewView message sent to new viewer."""

  @classmethod
  def message_name(cls) -> str:
    return "NewView"

  # If the message format changes, this can be re-organised so this can be
  # parsed first before determining the rest of the fields.
  message_version_number: comm_types.Int16u = 1
  """The version number of this message."""

  window_id: comm_types.Int64u
  """The window ID to render the 3D view into."""

  view_container_object_id: comm_types.Int64u
  """This is the object ID of the view object."""

  preference_category: str = "viewer"
  """The preference area for where to read preferences for this viewer."""

  locked_features: comm_types.Int32u = 0
  """The initial lockable features to apply to this viewer."""

  is_rendering_off_screen: bool = True
  is_ignoring_active_selection: bool = True
  is_anti_aliasing_enabled: bool = False
  is_action_plane_active: bool = False
  is_in_hands_free_mode: bool = False


class ScreenshotResponse(Response):
  """The response back after requesting a screenshot."""

  always_true: bool


class DumpScreenshotV1(Request):
  """A message for a viewer to ask it to create a screenshot.

  This is the older version of the request which required the format to be
  sent.

  This is applicable for PointStudio 2024 and earlier.
  """

  @classmethod
  def message_name(cls) -> str:
    return "DumpScreenShot"

  @classmethod
  def response_type(cls) -> type[ScreenshotResponse]:
    return ScreenshotResponse

  width: comm_types.Int32u
  height: comm_types.Int32u
  path: PathBody
  image_format: comm_types.Int32u = 3  # 3 is PNG


class DumpScreenshotV2(Request):
  """A message for a viewer to ask it to create a screenshot.

  This is the newer version and applicable to GeologyCore 2024 and PointStudio
  2024.1.
  """

  @classmethod
  def message_name(cls) -> str:
    return "DumpScreenShot"

  @classmethod
  def response_type(cls) -> type[ScreenshotResponse]:
    return ScreenshotResponse

  width: comm_types.Int32u
  height: comm_types.Int32u
  path: PathBody


class ViewWindowBase:
  """A view window that this process created and owns."""
  def __init__(self, *, width: int, height: int, logger: logging.Logger):
    self._window_handle = _create_window(width=width, height=height)
    self.logger = logger
    self.width = width
    self.height = height
    try:
      self._view_id, self._view_name = _create_view(self._window_handle)
    except:
      self._destroy_window()
      raise

  @property
  def view_id(self) -> ObjectID:
    """The ID of the view object."""
    return self._view_id

  def _save_to_image(self, path: "os.PathLike | str"):
    """Save this view to an image file.

    Objects should be added to the view before saving it to an image.

    The view window should ideally only be used for saving images and not be
    shown directly to the user or allow user interaction.

    Parameters
    ----------
    path
      The path to where the image should be saved.
      This ideally should have a PNG extension.
    """
    # The following is problematic as PointStudio 2024 lacks the change but GeologyCore 2024
    # has the change and both are C API 1.10.
    #
    # The other option is to limit this to API 1.11 or greater.
    comms_manager = default_manager()
    if Viewer().version < (1, 10):
      # Rather than competently disallow older applications, let this work.
      screenshot_request = DumpScreenshotV1(comms_manager)
    elif Viewer().version == (1, 10):
      #pylint: disable=wrong-import-position Avoid circular dependency issue.
      from mapteksdk.project.errors import ApplicationTooOldError

      # PointStudio 2024 and GeologyCore 2024 are both API 1.10 but
      # require different versions of this message.
      #
      # Rather than simply require >= (1, 11)
      raise ApplicationTooOldError(
        "A newer version of the application is needed to save a view "
        "to an image.")
    else:
      # Later version of the products use version 2.
      screenshot_request = DumpScreenshotV2(comms_manager)

    screenshot_request.width = self.width
    screenshot_request.height = self.height
    screenshot_request.path = PathBody.from_pathlib(pathlib.Path(path))
    screenshot_request.send(destination=self._view_name)
    self.logger.info("An image of the view was saved to %s", path)

  def __enter__(self) -> "typing.Self":
    return self

  def __exit__(
      self,
      __exc_type: "type[BaseException] | None",
      __exc_value: "BaseException | None",
      __traceback: "TracebackType | None") -> "bool | None":
    # SDK-1223: This hits an assertion because the view_id is deleted before
    # the view is finished cleaning up.
    # success = DataEngine().DeleteObject(self.view_id.handle)
    # if not success:
    #   self.logger.warning(
    #     "Failed to delete view object when closing view window.")
    self._destroy_window()

  def _destroy_window(self):
    """Destroy the window."""
    if ctypes.windll.user32.DestroyWindow(self._window_handle) == 0:
      error = ctypes.GetLastError()
      error_message = ctypes.FormatError(error)
      self.logger.warning(
        "Failed to close window for off-screen viewer (error: %d) - %s",
        error,
        error_message,
      )
      # There is nothing more to do about this error.


def _create_view(window_handle) -> tuple[ObjectID, str]:
  """Create the view object and wait until it is ready before returning."""
  viewer_dll = Viewer()
  view_handle = viewer_dll.CreateNewViewObject()
  if not view_handle:
    raise RuntimeError("Unable to create view.")

  # Query the server name does not do the normal buffer size negotiation that
  # capi.util.get_string() handles. Nor does it have error reporting.
  # server_name = util.get_string(view_handle, viewer_dll.GetServerName)
  buffer = ctypes.create_string_buffer(1024)
  viewer_dll.GetServerName(view_handle, buffer, 1024)
  server_name = buffer.value.decode("utf-8")

  if not server_name:
    DataEngine().DeleteObject(view_handle)
    raise RuntimeError("Failed to create view")

  view_complete = threading.Event()

  def _on_view_complete(response):
    view_complete.set()

  comms_manager = default_manager()
  with McpCallback("NewViewComplete", _on_view_complete):
    message = NewViewMessageV1(comms_manager)
    message.window_id = window_handle
    message.view_container_object_id = view_handle
    message.send(destination=server_name)

    # Wait until _on_view_complete is called.
    while not view_complete.is_set():
      comms_manager.service_events()

  return ObjectID(view_handle), server_name


def _create_window(*, width: int, height: int) -> ctypes.c_void_p:
  """Create the window of the given width and height.

  Raises
  ------
  RuntimeError
    If the window can not be created.
  """
  # ruff: noqa: N806 Keep these local with their original names.
  WS_POPUP = 0x80000000
  WS_DISABLED = 0x08000000

  create_window_ex = ctypes.windll.user32.CreateWindowExA
  create_window_ex.argtypes = [
    ctypes.c_int,
    ctypes.c_char_p,
    ctypes.c_char_p,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_void_p,
  ]
  create_window_ex.restype = ctypes.c_void_p

  # Create Window
  hwnd = create_window_ex(
    0,
    b"static",
    b"View Rendering Target",
    WS_POPUP | WS_DISABLED,
    0,  # x
    0,  # y
    ctypes.c_int(width),
    ctypes.c_int(height),
    0,
    0,
    0,
    0,
  )
  if not hwnd:
    error = ctypes.GetLastError()
    error_message = ctypes.FormatError(error)
    logging.getLogger("mapteksdk.view").error(
      "Failed to create window for off-screen rendering (error: %d) - %s",
      error,
      error_message,
    )
    raise RuntimeError(
      "Unable to create window for off-screen rendering.",
      error,
      error_message,
    )
  return hwnd
