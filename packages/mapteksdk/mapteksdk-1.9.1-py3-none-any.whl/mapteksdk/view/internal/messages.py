"""Implementation details for the view subpackage."""
###############################################################################
#
# (C) Copyright 2024, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
import typing

from mapteksdk.data import ObjectID, DataObject
from mapteksdk.internal.comms import (
  Message,
  Request,
  Response,
  Double,
  Int32s,
  Int16u,
  Int32u,
)
from mapteksdk.view.enums import ObjectFilter, TransientGeometrySettings
from mapteksdk.view.internal.action_plane import ActionPlane

Point: "typing.TypeAlias" = tuple[Double, Double, Double]
"""Tuple representing a point."""


class WindowTitle(Request):
  """Defines a message for querying the window title of a view."""

  class WindowResponse(Response):
    """The response containing the window title."""
    title: str

  @classmethod
  def message_name(cls) -> str:
    return 'WindowTitle'

  @classmethod
  def response_type(cls) -> type[Response]:
    return cls.WindowResponse

  view_name: str


class DestroyView(Message):
  """This message destroys (closes) the view."""
  @classmethod
  def message_name(cls) -> str:
    return 'DestroyView'


class SceneExtent(Request):
  """Request for the extents of a scene."""

  class SceneResponse(Response):
    """The response with the extents for the scene."""
    minimum: Point
    maximum: Point

  @classmethod
  def message_name(cls) -> str:
    return "SceneExtent"

  @classmethod
  def response_type(cls) -> type[SceneResponse]:
    return cls.SceneResponse


class ObjectsInView(Request):
  """Defines message for querying what objects are in a view."""

  class InViewResponse(Response):
    """The response back with what objects are in a view."""
    objects: list[ObjectID[DataObject]]

  @classmethod
  def message_name(cls) -> str:
    return 'ObjectsInView'

  @classmethod
  def response_type(cls) -> type[Response]:
    return cls.InViewResponse

  object_filter: ObjectFilter
  type_filter: list[Int16u]


class AddObjects(Message):
  """Message for the viewer for adding objects to it."""
  @classmethod
  def message_name(cls) -> str:
    return 'AddObjects'

  objects: list[ObjectID[DataObject]]
  drop_point: tuple[Double, Double] = (
    float('NaN'), float('NaN'))


class RemoveObjects(Message):
  """Message for the viewer for removing objects from it."""
  @classmethod
  def message_name(cls) -> str:
    return 'RemoveObjects'

  objects: list[ObjectID[DataObject]]


class HideObjectsOld(Message):
  """Message for the viewer for hiding objects."""
  @classmethod
  def message_name(cls) -> str:
    return 'HideObjects'

  objects: list[ObjectID[DataObject]]


class HideObjects(Message):
  """Message for the viewer for hiding objects."""
  @classmethod
  def message_name(cls) -> str:
    return 'HideObjects'

  objects: list[ObjectID[DataObject]]
  mouse: tuple[Double, Double] = (
    float('NaN'), float('NaN'))


class ShowObjects(Message):
  """Message for the viewer for showing objects."""
  @classmethod
  def message_name(cls) -> str:
    return 'ShowObjects'

  objects: list[ObjectID[DataObject]]


class AddTransientGeometry(Message):
  """Message for the viewer for adding  transient objects to it."""
  @classmethod
  def message_name(cls) -> str:
    return 'AddTransientGeometry'
  objects: list[ObjectID[DataObject]]
  settings: TransientGeometrySettings


class PromoteTransientGeometry(Message):
  """Message for the viewer for adding  transient objects to it."""
  @classmethod
  def message_name(cls) -> str:
    return 'PromoteTransientGeometry'
  objects: list[ObjectID[DataObject]]


class TransientObjectsInView(Request):
  """Message for the viewer for querying transient objects in it."""

  class TransientResponse(Response):
    """The response back with what transient objects are in a view."""
    object_groups: list[list[ObjectID[DataObject]]]
    settings: list[TransientGeometrySettings]

  @classmethod
  def message_name(cls) -> str:
    return 'TransientObjectsInView'

  @classmethod
  def response_type(cls) -> type[Response]:
    return cls.TransientResponse


class AxesVisibility(Request):
  """Request the axes visibility."""

  class AxesVisibilityResponse(Response):
    """Response to an axes visibility request"""
    visibility: bool

  @classmethod
  def message_name(cls) -> str:
    return "AxesVisibility"

  @classmethod
  def response_type(cls) -> type[AxesVisibilityResponse]:
    return cls.AxesVisibilityResponse


class SetAxesVisibility(Message):
  """Message for changing the visibility of the axes in a view."""
  @classmethod
  def message_name(cls) -> str:
    return 'SetAxesVisibility'
  axes_are_visible: bool


class ActionPlaneSectionWidths(Request):
  """Query the action plane section widths."""

  class SectionWidthResponse(Response):
    """The response containing the section widths."""
    back: Double
    front: Double

  @classmethod
  def message_name(cls) -> str:
    return "ActionPlaneSectionWidths"

  @classmethod
  def response_type(cls) -> type[SectionWidthResponse]:
    return cls.SectionWidthResponse


class SetActionPlaneSectionWidths(Message):
  """Message for changing the section width."""
  @classmethod
  def message_name(cls) -> str:
    return 'SetActionPlaneSectionWidths'
  back: Double
  front: Double


class ActionPlaneSectionMode(Request):
  """Request the current section mode."""

  class SectionModeResponse(Response):
    """The response containing the section mode."""
    section_mode: Int32s  # vwrE_SectionMode.

  @classmethod
  def message_name(cls) -> str:
    return "ActionPlaneSectionMode"

  @classmethod
  def response_type(cls) -> type[SectionModeResponse]:
    return cls.SectionModeResponse


class SetActionPlaneSectionMode(Message):
  """Message for changing the section mode."""
  @classmethod
  def message_name(cls) -> str:
    return 'SetActionPlaneSectionMode'
  section_mode: Int32s


class ActionPlaneMessage(Request):
  """Get the action plane."""

  class ActionPlaneResponse(Response):
    """The response containing the action plane.

    This also contains the visualisation centroid and grid orientation.
    """
    action_plane: ActionPlane

  @classmethod
  def message_name(cls) -> str:
    return "ActionPlane"

  @classmethod
  def response_type(cls) -> type[ActionPlaneResponse]:
    return cls.ActionPlaneResponse


class SetActionPlane(Message):
  """The message to set the action plane of the view this is sent to."""
  @classmethod
  def message_name(cls) -> str:
    return 'SetActionPlane'

  action_plane: ActionPlane


class SectionStepDistance(Request):
  """Get the action plane step distance."""

  class SectionStepDistanceResponse(Response):
    """The response containing the step distance."""
    step_distance: Double

  @classmethod
  def message_name(cls) -> str:
    return "ActionPlaneSectionStepDistance"

  @classmethod
  def response_type(cls) -> type[SectionStepDistanceResponse]:
    return cls.SectionStepDistanceResponse


class SetSectionStepDistance(Message):
  """Message for changing the section step distance."""
  @classmethod
  def message_name(cls) -> str:
    return 'SetActionPlaneSectionStepDistance'
  step_distance: Double


class ViewObjectByExtents(Message):
  """A message for the viewer server to change the camera."""
  extent_minimum: Point
  extent_maximum: Point
  rotation: tuple[Double, Double, Double, Double]
  any_orientation: bool = False

  @classmethod
  def message_name(cls) -> str:
    return "ViewObjectByExtents"


class RequestBackgroundColour(Request):
  """Query background colour of a view window."""

  class BackgroundColourResponse(Response):
    """Response to a request background colour request"""
    colour: Int32u

  @classmethod
  def message_name(cls) -> str:
    return 'BackgroundColour'

  @classmethod
  def response_type(cls) -> type[BackgroundColourResponse]:
    return cls.BackgroundColourResponse


class SetBackgroundColour(Message):
  """Sets the background colour of a view window."""
  @classmethod
  def message_name(cls) -> str:
    return 'SetBackgroundColour'

  colour: Int32u


class StartTransition(Message):
  """Tells the viewer that it will be transitioning the camera to a new
  location.
  """
  @classmethod
  def message_name(cls) -> str:
    return 'StartTransition'

  axes_transition_mode: Int32s = 2
  transition_time: Double


class StepActionPlaneSection(Message):
  """Message that causes the view to step the action plane in a direction.
  """
  @classmethod
  def message_name(cls) -> str:
    return 'StepActionPlaneSection'
  step_direction: Int32s


class ScaleLinearFieldOfView(Message):
  """Scale the linear field of view."""
  scale: Double

  @classmethod
  def message_name(cls) -> str:
    return "ScaleLinearFieldOfView"


class TransformWorld(Message):
  """Message for rotating and translating the camera."""
  rotation: tuple[Double, Double, Double, Double]
  translation: tuple[Double, Double, Double]
  centre: Point

  @classmethod
  def message_name(cls) -> str:
    return "TransformWorld"


class GetManipulationMode(Request):
  """Get the manipulation mode."""
  class ModeResponse(Response):
    """Response containing the manipulation mode."""
    mode: str

  @classmethod
  def message_name(cls) -> str:
    return "ManipulationMode"

  @classmethod
  def response_type(cls) -> type[ModeResponse]:
    return cls.ModeResponse


class SetManipulationMode(Message):
  """Set the manipulation mode.

  This messages requires C API version 1.12 or higher.
  """
  mode: str
  is_tied_change: bool = False

  @classmethod
  def message_name(cls) -> str:
    return "SetManipulationMode"


class SetCameraTransform(Message):
  """Set the camera transform."""
  quaternion: tuple[Double, Double, Double, Double]
  position: Point

  @classmethod
  def message_name(cls) -> str:
    return "SetTransform"
