"""Interaction with a view in an applicable Maptek application.

The first step is opening a new view which returns a view controller for the
new view. From there you can control the view by adding/removing objects,
hiding/showing objects and querying what objects are in the view.

>>> from mapteksdk.project import Project
>>> import mapteksdk.operations as operations
>>> project = Project()
>>> view = operations.open_new_view()
>>> view.add_objects([project.find_object('/cad')])
>>> view.close()
>>> project.unload_project()
"""
###############################################################################
#
# (C) Copyright 2021, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

from collections.abc import Iterable, Sequence
import copy
import ctypes
import logging
import math
import pathlib
import os

from mapteksdk.view.enums import (
  ManipulationMode,
  ObjectFilter,
  PredefinedView,
  SectionMode,
  SectionStepDirection,
  TransientGeometrySettings
)
from mapteksdk.view.errors import ViewNoLongerExists
from mapteksdk.view.internal import (
  ActionPlane,
  WindowTitle,
  DestroyView,
  SceneExtent,
  ObjectsInView,
  AddObjects,
  RemoveObjects,
  HideObjectsOld,
  HideObjects,
  ShowObjects,
  AddTransientGeometry,
  PromoteTransientGeometry,
  TransientObjectsInView,
  AxesVisibility,
  SetAxesVisibility,
  SetActionPlaneSectionWidths,
  SetActionPlaneSectionMode,
  ActionPlaneSectionWidths,
  ActionPlaneSectionMode,
  ActionPlaneMessage,
  SetActionPlane,
  SectionStepDistance,
  SetSectionStepDistance,
  ViewObjectByExtents,
  RequestBackgroundColour,
  SetBackgroundColour,
  StartTransition,
  StepActionPlaneSection,
  ScaleLinearFieldOfView,
  TransformWorld,
  GetManipulationMode,
  SetManipulationMode,
  SetCameraTransform,
)
from mapteksdk.capi import Viewer, ViewerApi
from mapteksdk.capi.viewer import ViewerErrorCodes
from mapteksdk.data import ObjectID, DataObject, Axis
from mapteksdk.errors import ApplicationTooOldError
from mapteksdk.geometry import Extent, Plane
from mapteksdk.overwrite_modes import OverwriteMode
from mapteksdk.internal.rotation import Rotation
import mapteksdk.internal.view as view_private
from mapteksdk.internal.overwrite import unique_filename
from mapteksdk.internal.comms import (
  default_manager,
  CommunicationsManager,
  MalformedMessageError,
  Request,
  Response,
)
from mapteksdk.internal.normalise_selection import normalise_selection
from mapteksdk.internal.util import default_type_error_message

class ViewController:
  """Provides access onto a specified view.

  This allows for objects to be added/removed/shown and hidden.
  """
  def __init__(
    self,
    view_id: ObjectID[DataObject],
    *,
    viewer: ViewerApi | None=None,
    manager: CommunicationsManager | None=None
  ):
    # In PointStudio 2020.1, there are no safe-guards in place to confirm that
    # the given view_id is infact an ID for a view and it exists. This will
    # simply crash.
    self._viewer = viewer or Viewer()
    maximum_length = 256
    server_name = ctypes.create_string_buffer(maximum_length)
    self._viewer.GetServerName(
      view_id.native_handle, server_name, maximum_length)
    if not server_name.value:
      error_message = self._viewer.ErrorMessage()
      if self._viewer.ErrorCode() == ViewerErrorCodes.VIEW_NO_LONGER_EXISTS:
        raise ViewNoLongerExists(error_message)
      raise ValueError(error_message)

    self.server_name = server_name.value.decode('utf-8')

    # Like the DataObject class provide the ability to query the ID of the
    # view controller.
    self.id = view_id
    self.__manager = manager or default_manager()
    self.__closed = False
    """If the view has been closed."""

  def __repr__(self):
    return type(self).__name__ + f'({self.id}, "{self.server_name}")'

  @property
  def _manager(self) -> CommunicationsManager:
    if self.__closed:
      raise ViewNoLongerExists("The view has been closed.")
    return self.__manager

  @property
  def window_title(self) -> str:
    """Return the window title.

    This is the name of the view window as seen in the application.
    """
    request = WindowTitle(self._manager)
    request.view_name = self.server_name

    try:
      # The viewer server doesn't know its title as its the uiServer that
      # is responsible for that.
      # Because this sends to the uiServer, this cannot use
      # self._safe_send_to_server().
      response: WindowTitle.WindowResponse = request.send(
        'uiServer') # type: ignore
    except MalformedMessageError as error:
      raise ViewNoLongerExists(
        "The view has likely been closed in the application."
      ) from error
    return response.title

  def close(self):
    """Close the view.

    Avoid closing views that you didn't open, as such avoid closing the view
    if it came from a non-empty active view. This is because you may close a
    view that was being used by another tool in the application.

    A case where closing the view is a good idea is if the script creates one
    and is interactive and long-running. Think about when the script is done if
    the person running the script would miss seeing what is in the view, would
    find it a hassle to have to close it themself or if the content is no
    longer relevant after the script has exited.

    Examples
    --------
    Opens a new view then closes it.

    >>> from mapteksdk.project import Project
    >>> import mapteksdk.operations as operations
    >>> project = Project()
    >>> view = operations.open_new_view()
    >>> input('Press enter to finish')
    >>> view.close()
    >>> project.unload_project()
    """
    if self.__closed:
      return
    DestroyView(self._manager).send(self.server_name)
    self.__closed = True

  def scene_extents(self) -> Extent:
    """Return the scene extents of this view."""
    request = SceneExtent(self._manager)
    response: SceneExtent.SceneResponse = self._safe_send_to_server(
      request) # type: ignore
    return Extent(response.minimum, response.maximum)

  def objects_in_view(
      self,
      object_filter: ObjectFilter=ObjectFilter.DEFAULT
      ) -> list[ObjectID]:
    """Return a list of objects that are in the the view.

    Parameters
    ----------
    object_filter : ObjectFilter
      A filter that limits what objects are returned.

    Returns
    -------
    list
      A list of object IDs of objects that are in the view that meet the filter
      criteria.
    """

    # TODO: Support filtering by object types.
    # Essentially support user providing list of type index or classes with
    # static_type function that returns a type index or a mix of both.
    #
    # This should ideally handle values of the form: [Surface, Polygon,
    # Polyline]
    # However receiving a message containing it would be problematic as its
    # not easy to map it back.
    request = ObjectsInView(self._manager)
    request.object_filter = object_filter
    request.type_filter = []

    response: ObjectsInView.InViewResponse = self._safe_send_to_server(
      request) # type: ignore
    return response.objects

  def add_objects(
    self,
    objects: Iterable[ObjectID | DataObject | str]
  ):
    """Adds the provided objects to the view.

    Parameters
    ----------
    objects
      A list of IDs of objects to add to the view.
    """
    request = AddObjects(self._manager)
    request.objects = list(normalise_selection(objects))
    request.send(self.server_name)

  def add_object(self, object_to_add: ObjectID | DataObject | str):
    """Add a single object to the view.

    Parameters
    ----------
    object_to_add
      The object to add, the ObjectID of the object to add, or a path string
      for the object to add.
    """
    self.add_objects([object_to_add])

  def remove_objects(
    self,
    objects: Iterable[ObjectID | DataObject | str]
  ):
    """Removes the provided objects from the view if present.

    Removing objects not in the view will do nothing.

    Parameters
    ----------
    objects
      A list of IDs of objects to remove from the view.
    """
    request = RemoveObjects(self._manager)
    request.objects = list(normalise_selection(objects))
    request.send(self.server_name)

  def remove_object(
    self, object_to_remove: ObjectID | DataObject | str
  ):
    """Remove a single object from the view.

    Parameters
    ----------
    object_to_remove
      The object to remove, the ObjectID of the object to remove, or a path
      string for the object to remove.
    """
    self.remove_objects([object_to_remove])

  def hide_objects(
    self,
    objects: Iterable[ObjectID | DataObject | str]
  ):
    """Hide the provided objects in the view.

    Hiding objects not in the view will do nothing.

    Parameters
    ----------
    objects
      A list of IDs of objects to hide.
    """
    if self._viewer.version >= (1, 1):
      hide_objects = HideObjects
    else:
      hide_objects = HideObjectsOld

    request = hide_objects(self._manager)
    request.objects = list(normalise_selection(objects))
    request.send(self.server_name)

  def hide_object(
    self,
    object_to_hide: ObjectID | DataObject | str
  ):
    """Hide a single object in the view.

    Parameters
    ----------
    object_to_hide
      The object to hide, the ObjectID of the object to hide, or a path string
      for the object to hide.
    """
    self.hide_objects([object_to_hide])

  def show_objects(
    self,
    objects: Iterable[ObjectID | DataObject | str]
  ):
    """Show the provided objects in the view (if hidden).

    If the objects are not in the view then they won't be shown.

    Parameters
    ----------
    objects
      A list of IDs of objects to hide.
    """
    request = ShowObjects(self._manager)
    request.objects = list(normalise_selection(objects))
    request.send(self.server_name)

  def show_object(
    self,
    object_to_show: ObjectID | DataObject | str
  ):
    """Show a single hidden object in the view.

    Parameters
    ----------
    object_to_show
      The object to show, the ObjectID of the object to show, or a path string
      for the object to show.
    """
    self.show_objects([object_to_show])

  def add_transient_object(
    self,
    object_to_add: ObjectID | DataObject | str,
    settings: TransientGeometrySettings = TransientGeometrySettings()
  ):
    """Add a single object to the view as a transient object.

    Transient objects by default are not pickable or selectable. They
    are typically used to show a preview of some operation.

    You are responsible for removing the object from the view when you are
    done with it (or if you opened the view then close the view). The object
    should not be left in the view after you are done with it as this will
    leave the user with only the option of closing the view to get rid of it
    themselves. If you promote the transient object then it doesn't need to
    be removed.

    Parameters
    ----------
    object_to_add
      The object to add, the ObjectID of the object to add, or a path string
      for the object to add.
    settings
      The transient geometry settings that apply to the object_to_add.

    See Also
    --------
    remove_object : To remove the object from the view.
    promote_transient_object : To promote the transient object.
    """
    self.add_transient_objects([object_to_add], settings)

  def add_transient_objects(
    self,
    objects: Iterable[ObjectID | DataObject | str],
    settings: TransientGeometrySettings = TransientGeometrySettings()
  ):
    """Adds the provided objects to the view as transient objects.

    Transient objects by default are not pickable or selectable. They
    are typically used to show a preview of some operation.

    You are responsible for removing the object from the view when you are
    done with it (or if you opened the view then close the view). The object
    should not be left in the view after you are done with it as this will
    leave the user with only the option of closing the view to get rid of it
    themselves. If you promote the transient object then it doesn't need to
    be removed.

    Parameters
    ----------
    objects
      A list of IDs of objects to add to the view.
    settings
      The transient geometry settings that apply to objects.

    See Also
    --------
    remove_objects : To remove the object from the view.
    promote_transient_objects : To promote transient objects.
    """
    request = AddTransientGeometry(self._manager)
    request.objects = list(normalise_selection(objects))
    request.settings = settings
    request.send(self.server_name)

  def promote_transient_object(
    self,
    data_object: ObjectID | DataObject | str
  ):
    """Promote a transient object to being a permanent object.

    This is relevant to the view only, to ensure the geometry persists it
    should be added to the project.
    """
    self.promote_transient_objects([data_object])

  def promote_transient_objects(
    self,
    objects: Iterable[ObjectID | DataObject | str]
  ):
    """Promote transient objects to being permanent objects.

    This is relevant to the view only, to ensure the objects persists they
    should be added to the project.
    """
    request = PromoteTransientGeometry(self._manager)
    request.objects = list(normalise_selection(objects))
    request.send(self.server_name)

  def transient_objects_in_view(self) -> \
      list[tuple[ObjectID[DataObject], TransientGeometrySettings]]:
    """
    Return the transient objects that are in the the view and their settings.

    Returns
    -------
    list
      A list of each transient object and their corresponding settings.
    """
    request = TransientObjectsInView(self._manager)
    response: TransientObjectsInView.TransientResponse = (
      self._safe_send_to_server(request) # type: ignore
    )

    # Flatten out the list also known as de-grouping them as the objects were
    # grouped together.
    result = []
    for objects, settings in zip(response.object_groups, response.settings):
      for transient_object in objects:
        result.append((transient_object, copy.deepcopy(settings)))
    return result

  @property
  def axes_visibility(self):
    """The visibility of the axes in the view.

    Examples
    --------
    Querying the visibility of the axes in the view.
    >>> from mapteksdk.project import Project
    >>> from mapteksdk.operations import active_view
    >>> project = Project()
    >>> view = active_view()
    >>> view.axes_visibility
    True
    >>> project.unload_project()

    Turn on axes in the current view.

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.operations import active_view
    >>> project = Project()
    >>> view = active_view()
    >>> view.axes_visibility = True
    >>> project.unload_project()

    Turn off axes in the current view.

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.operations import active_view
    >>> project = Project()
    >>> view = active_view()
    >>> view.axes_visibility = False
    >>> project.unload_project()
    """
    request = AxesVisibility(self._manager)
    response: AxesVisibility.AxesVisibilityResponse = (
      self._safe_send_to_server(request) # type: ignore
    )

    return response.visibility

  @axes_visibility.setter
  def axes_visibility(self, visibility: bool):
    """Change the visibility of the axes in the view.

    Parameters
    ----------
    visibility
        If true the axes will be visible, otherwise they will be
        hidden (or invisible).
    """
    message = SetAxesVisibility(self._manager)
    message.axes_are_visible = visibility
    message.send(self.server_name)

  def action_plane_section_widths(self) -> tuple[float, float]:
    """Return the widths of the section in this view."""
    request = ActionPlaneSectionWidths(self._manager)
    response: ActionPlaneSectionWidths.SectionWidthResponse = (
      self._safe_send_to_server(request) # type: ignore
    )
    return (response.back, response.front)

  def set_action_plane_section_widths(
      self, back_width: float, front_width: float):
    """Change the section width of the view.

    This will only take affect if view's section mode is not
    SectionMode.NO_MODE.

    It is typical for the same width to be given for both the front and back.

    Parameters
    ----------
    back_width
        The width of the section from the action plane to the back.
    front_width
        The width of the section from the action plane to the front.

    See Also
    --------
    action_plane_section_mode : Query the current section mode
    set_action_plane_section_mode : Set the current section modes (enable
        sectioning)
    """
    message = SetActionPlaneSectionWidths(self._manager)
    message.back = back_width
    message.front = front_width
    message.send(self.server_name)

  def action_plane_section_mode(self) -> SectionMode:
    """Return the current section mode of this view."""
    request = ActionPlaneSectionMode(self._manager)
    response: ActionPlaneSectionMode.SectionModeResponse = (
      self._safe_send_to_server(request) # type: ignore
    )
    return SectionMode(response.section_mode)

  def set_action_plane_section_mode(self, section_mode: SectionMode):
    """Change the view's section mode to the mode given.

    Parameters
    ----------
    section_mode
        The section mode to change to.

    Examples
    --------
    Turn on sectioning in the current view.

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.operations import active_view
    >>> from mapteksdk.view import SectionMode
    >>> project = Project()
    >>> view = active_view()
    >>> view.set_action_plane_section_mode(SectionMode.STRIP)
    >>> project.unload_project()

    Turn off sectioning in the current view.

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.operations import active_view
    >>> from mapteksdk.view import SectionMode
    >>> project = Project()
    >>> view = active_view()
    >>> view.set_action_plane_section_mode(SectionMode.NO_MODE)
    >>> project.unload_project()
    """
    message = SetActionPlaneSectionMode(self._manager)
    message.section_mode = section_mode
    message.send(self.server_name)

  def action_plane(self) -> Plane:
    """Return the action plane in this view."""
    request = ActionPlaneMessage(self._manager)
    response: ActionPlaneMessage.ActionPlaneResponse = (
      self._safe_send_to_server(request) # type: ignore
    )

    return response.action_plane.plane

  def set_action_plane(self, plane: Plane):
    """Set the action plane in this view.

    Parameters
    ----------
    plane
      The plane to use for the action plane.
    """
    message = SetActionPlane(self._manager)
    message.action_plane = ActionPlane()
    message.action_plane.plane = plane
    message.send(self.server_name)

  def action_plane_section_step_distance(self) -> float:
    """The distance that the action plane will move if it is stepped by."""
    request = SectionStepDistance(self._manager)
    response: SectionStepDistance.SectionStepDistanceResponse = (
      self._safe_send_to_server(request) # type: ignore
    )
    return response.step_distance

  def set_action_plane_section_step_distance(self, step_distance: float):
    """Change the section step distance of the view.

    Parameters
    ----------
    step_distance
        The distance to step forward/back with the section.

    See Also
    --------
    step_action_plane_section_forwards : Step forwards by the last distance.
    step_action_plane_section_backwards : Step backwards by the last distance.
    """
    message = SetSectionStepDistance(self._manager)
    message.step_distance = step_distance
    message.send(self.server_name)

  def step_action_plane_section_forwards(self):
    """Step (moves) the action plane forwards.

    The distance the plane will move is based on the last set step distance for
    the view.

    See Also
    --------
    set_action_plane_section_step_distance : Set the step distance.
    step_action_plane_section_backwards : Step in the other direction.
    """
    self._step_action_plane_section(SectionStepDirection.LEFT_AND_UP)

  def step_action_plane_section_backwards(self):
    """Step (moves) the action plane backwards.

    The distance the plane will move is based on the last set step distance for
    the view.

    See Also
    --------
    set_action_plane_section_step_distance : Set the step distance.
    step_action_plane_section_forwards : Step in the other direction.
    """
    self._step_action_plane_section(SectionStepDirection.RIGHT_AND_DOWN)

  def view_objects_by_extents(self,
                              extent: Extent | None,
                              look_direction: Sequence[float],
                              up_direction: Sequence[float]):
    """Change the camera such that it views all data in extent.

    Use this to move the camera to view a specific object (or objects), based on
    its (or their) extents.

    The camera will be looking at the centre of the extent from a point
    sufficiently far from the centre such that the entire extent will be visible
    in perspective projection, and a sufficiently large linear field of view to
    see the entire extent when in orthographic projection.

    The specified look_direction and up_direction will be taken into account.

    Parameters
    ----------
    extent
      The extent of the objects that the view should focus on.
      If None, the view extent will be used.
    look_direction
      The look direction is in the direction the camera should be looking and
      is from the camera towards to point of interest and should be towards
      the extent.
    up_direction
      The up direction is a vector that points up relative to the camera,
      typically towards the sky and affects the camera's tilt and roll.
    """
    rotation = Rotation.create_from_look_and_up_direction(look_direction,
                                                          up_direction)

    message = ViewObjectByExtents(self._manager)
    if extent is None:
      # An empty extent is results in using the view extent.
      message.extent_minimum = (math.nan, math.nan, math.nan)
      message.extent_maximum = (math.nan, math.nan, math.nan)
    else:
      message.extent_minimum = extent.minimum
      message.extent_maximum = extent.maximum
    message.rotation = rotation.quaternion
    message.send(self.server_name)

  def use_predefined_view(
    self,
    view_direction: PredefinedView,
    extent: Extent | None = None
  ):
    """View the objects in the view from `view_direction`.

    Parameters
    ----------
    view_direction
      The predefined view direction to use for the view.
    extent
      The extent to view from the view direction.
      If None (default), then all objects currently in the view will be
      used to determine the extent.
    """
    if not isinstance(view_direction, PredefinedView):
      raise TypeError(
        default_type_error_message(
          "view_direction", view_direction, PredefinedView
        )
      )
    self.view_objects_by_extents(
      extent,
      view_direction.look_direction,
      view_direction.up_direction
    )

  def look_at_point(
    self,
    point_to_look_at: tuple[float, float, float],
    camera_point: tuple[float, float, float]
  ):
    """Move the camera to `camera_point` and face it towards `point_to_look_at`.

    This will implicitly change the view manipulation mode to
    `ManipulationMode.LOOK_FROM` if possible.

    Parameters
    ----------
    point_to_look_at
      The point of interest for the camera to look at.
    camera_point
      The point to place the camera at.

    Raises
    ------
    ValueError
      If any ordinate in `point_to_look_at` or `camera_point` is not finite.
      If `point_to_look_at` and `camera_point` are the same point.
    """
    look_point = self._validate_point(point_to_look_at, "Point to look at")
    actual_camera_point = self._validate_point(camera_point, "Camera point")

    vector = tuple(y - x for x, y in zip(actual_camera_point, look_point))
    if all(math.isclose(ordinate, 0.0, abs_tol=1e-8) for ordinate in vector):
      raise ValueError(
        "Look point and camera point must be different points. "
        f"Look point: {point_to_look_at}, "
        f"Camera point: {camera_point}"
      )
    rotation = Rotation.create_from_look_and_up_direction(
      vector,
      (0.0, 0.0, 1.0)
    )

    # The camera transform is sometimes applied incorrectly if the manipulation
    # mode is set after the transform, so set the manipulation mode first.
    self.set_manipulation_mode(ManipulationMode.LOOK_FROM)

    set_transform = SetCameraTransform(self._manager)
    set_transform.position = actual_camera_point
    set_transform.quaternion = rotation.quaternion
    set_transform.send(self.server_name)

  @property
  def background_colour(self) -> tuple[int, int, int, int]:
    """The background colour of the view window.

    This is represented as a tuple containing red, green, blue, alpha values
    of the colour.
    Each value is an integer in the range [0, 255].

    When changing the background colour, the alpha is optional and
    the colour may be given as either a tuple, list or ndarray.
    """
    request = RequestBackgroundColour(self._manager)
    response: RequestBackgroundColour.BackgroundColourResponse = (
      self._safe_send_to_server(request) # type: ignore
    )

    alpha = (response.colour >> 24) & 0xFF
    blue = (response.colour >> 16) & 0xFF
    green = (response.colour >> 8) & 0xFF
    red = response.colour & 0xFF

    return (red, green, blue, alpha)

  @background_colour.setter
  def background_colour(self, new_colour: Sequence[int]):
    # This could be useful when detecting if really dark coloured objects are
    # in the view and switching the background so it is lighter colour to
    # give contrast between foreground and background.
    #
    # It could also be possible to implement a night-light like application
    # which reduces specific colours used in the background as the time of day
    # changes.
    red, green, blue = new_colour[:3]
    if len(new_colour) == 4:
      alpha = new_colour[3]
    else:
      alpha = 255

    # Colour encoded as a 32-bit integer. This more than likely needs
    # to be packaged up as part of the comms module.
    colour = (alpha << 24) | (blue << 16) | (green << 8) | (red << 0)

    message = SetBackgroundColour(self._manager)
    message.colour = colour
    message.send(self.server_name)

  def rotate_camera(
    self,
    angle: float,
    axis: tuple[float, float, float] | Axis,
    centre: tuple[float, float, float] | None = None
  ):
    """Rotate the camera `angle` degrees around `centre` by `axis`.

    Parameters
    ----------
    angle
      The angle in radians to rotate the camera by.
    axis
      The axis to rotate around.
      This is of the form (x, y, z) and does not need to be normalised.
      Axis.X is equivalent to (1, 0, 0).
      Axis.Y is equivalent to (0, 1, 0).
      Axis.Z is equivalent to (0, 0, 1).
    centre
      The centre of rotation in the form (x, y, z).
      If None, the current centre of rotation of the view will be used.
    """
    actual_angle = self._validate_angle(angle)
    actual_axis = self._validate_axis(axis)

    if centre is None:
      actual_centre = (math.nan, math.nan, math.nan)
    else:
      actual_centre = self._validate_point(centre, "Centre of rotation")
    rotation = Rotation.axis_rotation(actual_angle, actual_axis)

    message = TransformWorld(self._manager)
    message.centre = actual_centre
    message.rotation = rotation.quaternion
    message.translation = (0.0, 0.0, 0.0)
    message.send(self.server_name)

  def translate_camera(self, vector: tuple[float, float, float]):
    """Translate the camera by `vector`."""
    actual_vector = self._validate_vector(vector)

    message = TransformWorld(self._manager)
    message.centre = (0.0, 0.0, 0.0)
    message.rotation = (1.0, 0.0, 0.0, 0.0)
    message.translation = actual_vector
    message.send(self.server_name)

  def get_manipulation_mode(self) -> ManipulationMode:
    """Get the manipulation mode of the view.

    This will return `ManipulationMode.UNKNOWN` if the view is non-standard
    (e.g. A stereonet view).
    """
    message = GetManipulationMode(self._manager)
    response: GetManipulationMode.ModeResponse = self._safe_send_to_server(
      message
    ) # type: ignore
    try:
      return ManipulationMode(response.mode)
    except ValueError:
      return ManipulationMode.UNKNOWN

  def set_manipulation_mode(self, mode: ManipulationMode):
    """Set the manipulation mode of the view.

    This will be ignored if the current view does not support setting the
    manipulation mode.
    """
    if not isinstance(mode, ManipulationMode):
      raise TypeError(
        default_type_error_message("mode", mode, ManipulationMode)
      )

    if mode is ManipulationMode.UNKNOWN:
      raise ValueError("Cannot set the manipulation mode to UNKNOWN.")

    if self._viewer.version < (1, 12):
      raise ApplicationTooOldError.with_default_message(
        "Set manipulation mode"
      )

    message = SetManipulationMode(self._manager)
    message.mode = mode.value
    message.send(self.server_name)

  def _safe_send_to_server(self, request: Request) -> Response:
    """Send `request` to the viewer server and return the response.

    Raises
    ------
    ViewNoLongerExists
      If the view has been closed.
    """
    try:
      return request.send(self.server_name)
    except MalformedMessageError as error:
      raise ViewNoLongerExists(
        "The view has likely been closed in the application."
      ) from error

  def _start_camera_transition(self, transition_time: float):
    """Enables the camera to smoothly transition to a new state

    Parameters
    ----------
    transition_time
      The time the transition should last in seconds.
    """
    message = StartTransition(self._manager)
    message.transition_time = transition_time
    message.send(self.server_name)

  def _step_action_plane_section(self, direction: SectionStepDirection):
    """Step the action plane section in the given direction.

    The distance the plane will move is based on the last set step distance for
    the view.

    Parameters
    ----------
    direction
      The direction to step the section.
    """
    message = StepActionPlaneSection(self._manager)
    message.step_direction = direction
    message.send(self.server_name)

  def _scale_linear_field_of_view(self, scale: float):
    """Apply a relative linear field of view to this view.

    Parameters
    ----------
    scale
      The scaling factor to apply to the linear field of view.
    """
    message = ScaleLinearFieldOfView(self._manager)
    message.scale = scale
    message.send(self.server_name)

  def _validate_angle(self, angle: float) -> float:
    """Validates that `angle` is a valid angle of rotation.

    Parameters
    ----------
    angle
      The angle of rotation to validate.

    Returns
    -------
    float
      The validated angle of rotation. This will always be a float, even
      if an integer is passed as an input.

    Raises
    ------
    ValueError
      If `angle` is close to zero or not finite.
    """
    angle = float(angle)
    if math.isclose(angle, 0.0):
      raise ValueError(
        f"The angle to rotate by must not be close to zero. It was: {angle}.")
    if not math.isfinite(angle):
      raise ValueError(
        f"The angle to rotate by must be finite. It was: {angle}.")
    return angle

  def _validate_axis(
    self,
    axis: tuple[float, float, float] | Axis
  ) -> tuple[float, float, float]:
    """Validates that `axis` is a valid axis to rotate around.

    Parameters
    ----------
    axis
      The axis to validate. This can be an axis enum member or a vector of
      the form (x, y, z) indicating the axis to rotate about.

    Returns
    -------
    tuple[float, float, float]
      This will be axis if it was a tuple of three floats.
      Otherwise, this will be the appropriate axis for the axis enum member
      passed to this function.

    Raises
    ------
    ValueError
      If all ordinates of axis are close to zero, or if any ordinate is not
      finite.
    """
    if isinstance(axis, Axis):
      if axis is Axis.X:
        return (1, 0, 0)
      if axis is Axis.Y:
        return (0, 1, 0)
      if axis is Axis.Z:
        return (0, 0, 1)
      # This will be reached if a new axis enum member is added.
      raise ValueError(f"Unsupported axis enum member: {axis}")

    if not isinstance(axis, Iterable):
      raise TypeError(
        f"Axis must be a tuple containing three floats. It was: {axis}.")

    if len(axis) != 3:
      raise ValueError(f"Axis must contain three ordinates, not {len(axis)}.")

    if all(math.isclose(ordinate, 0) for ordinate in axis):
      raise ValueError(
        "At least one axis ordinate must not be close to zero. "
        f"The axis was: {axis}"
      )
    if any(not math.isfinite(ordinate) for ordinate in axis):
      raise ValueError(
        f"All axis ordinates must be finite. The axis was: {axis}"
      )
    return axis

  def _validate_vector(
    self,
    vector: tuple[float, float, float]
  ) -> tuple[float, float, float]:
    """Validate that `vector` is a valid translation vector.

    This validates that no ordinates are non-finite and that at least one
    ordinate is non-zero.

    Raises
    ------
    ValueError
      If `vector` is not an iterable and does not contain exactly three floats.
      If `vector` contains a value which is not finite.
      If `vector` is a zero-vector.
    TypeError
      If `vector` is not an sequence.
      If `vector` contains a value which cannot be converted to a float.
    """
    vector = self._validate_point(vector, name="vector")

    if all(math.isclose(ordinate, 0) for ordinate in vector):
      raise ValueError(
        "At least one vector ordinate must not be close to zero. "
        f"The vector was: {vector}"
      )
    return vector

  def _validate_point(
    self,
    point: tuple[float, float, float],
    name: str
  ) -> tuple[float, float, float]:
    """Validates that `point` does not include any non-finite values.

    Parameters
    ----------
    point
      The point to validate.
    name
      The name to include in error messages. This should start with a capital
      letter.

    Returns
    -------
    tuple[float, float, float]
      The validated point.

    Raises
    ------
    ValueError
      If `point` is not an iterable and does not contain exactly three floats.
      If `point` contains a value which is not finite.
    TypeError
      If `point` is not an sequence.
      If `point` contains a value which cannot be converted to a float.
    """
    if not isinstance(point, Sequence):
      raise TypeError(
        f"{name} must be a tuple containing three floats. "
        f"It was: {point}.")

    if len(point) != 3:
      raise ValueError(
        f"{name} must contain three ordinates, "
        f"not {len(point)}."
      )

    if any(not math.isfinite(ordinate) for ordinate in point):
      raise ValueError(
        f"All {name} ordinates must be finite. "
        f"{name} was: {point}"
      )
    return point


class ViewWindow(view_private.ViewWindowBase):
  """A view window that this process created and owns.

  This can be used as a context manager and used in a with statement.
  It is recommended to use it in a with statement to ensure the view window
  is closed when it's not longer required.

  Parameters
  ----------
  width
    The width (horizontal length) of the viewer in pixels.
  height
    The height (vertical length) of the viewer in pixels.

  Example
  -------
  Create a view with a triangle and save it to an image.

  >>> from mapteksdk.project import Project
  >>> from mapteksdk.data import Surface
  >>> from mapteksdk.view import ViewWindow
  >>> project = Project()
  >>> with project.new("/surface/triangle", Surface) as surface:
  ...     surface.points = [(0.0, 0.0, 0.0), (5.0, 0.0, 0.0), (5.0, 5.0, 0.0)]
  ...     surface.facets = [(0, 1, 2)]
  >>> with ViewWindow(width=1024, height=1024) as view:
  ...     view.controller.add_object(surface.id)
  ...     view.save_to_image("triangle.png")
  >>> project.unload_project()
  """
  def __init__(self, *, width: int, height: int):
    logger = logging.getLogger("mapteksdk.view")
    logger.info(
      "Creating an off-screen view for rendering the view to an image.")
    super().__init__(width=width, height=height, logger=logger)
    self._controller = ViewController(self._view_id)

  @property
  def controller(self) -> ViewController:
    """Provides access to control this view."""
    return self._controller

  def save_to_image(
    self,
    path: os.PathLike | str,
    overwrite: OverwriteMode = OverwriteMode.ERROR,
  ) -> pathlib.Path:
    """Save this view to an image file.

    Objects should be added to the view before saving it to an image.

    The view window should ideally only be used for saving images and not be
    shown directly to the user or allow user interaction.

    Parameters
    ----------
    path
      The path to where the image should be saved.
      This ideally should have a PNG extension.
    overwrite
      How to handle writing an image to a path that already exists.

    Returns
    ------
    pathlib.Path
      The path of the resulting image.

    Raises
    ------
    NotADirectoryError
      If the directory the image should be saved in does not exist or is not a
      directory.
    FileExistsError
      If overwrite is OverwriteMode.ERROR and path already exists.
    OSError
      If overwrite is OverwriteMode.OVERWRITE and path can't be deleted.
    """
    path = pathlib.Path(path)
    if path.exists():
      if overwrite == OverwriteMode.ERROR:
        raise FileExistsError(f"There is already a file at {path}")
      elif overwrite == OverwriteMode.OVERWRITE:
        # Delete the file first to ensure that the file is indeed replaced.
        path.unlink(missing_ok=True)
      elif overwrite == OverwriteMode.UNIQUE_NAME:
        path = unique_filename(path)

    if not path.parent.exists():
      error = f"The directory '{path.parent}' where the image would " + \
        "be saved does not exist."
      raise NotADirectoryError(error)
    if not path.parent.is_dir():
      error = f"'{path.parent}' is not a directory so the image '{path}' " + \
        "can't be saved."
      raise NotADirectoryError(error)

    self._save_to_image(path)
    return path
