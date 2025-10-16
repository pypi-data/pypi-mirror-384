"""Operations available in PointStudio.

Operations exposes functionality from within an application that can be
invoked from Python functions. These typically correspond to menu items that
are available in the application, but their inputs can be populated from Python
without requiring the user to fill them out.

Available operations from PointStudio include contouring, triangulating a
surface, simplifying a surface, filtering points.

Notes
-----
Some of the operations available in this module are defined in the general
operations module and can be imported from there instead. Such operations
are not limited to being used with PointStudio.
"""

###############################################################################
#
# (C) Copyright 2020, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import enum
import typing

import numpy

from mapteksdk.common import convert_to_rgba
from mapteksdk.capi import Mcp
from mapteksdk.data import Topology, NumericColourMap, ObjectID
from mapteksdk.internal.normalise_selection import (
  normalise_selection,
  validate_selection,
)
from mapteksdk.internal.transaction import (
  request_transaction,
  RequestTransactionWithInputs,
)
from mapteksdk.internal.serialisation import Icon
from mapteksdk.internal.util import default_type_error_message
# pylint: disable=unused-import
# Import operations which were moved to mapteksdk.operations for
# backwards compatibility.
from mapteksdk.operations import (
  _decode_selection,
  TooOldForOperation,
  PickFailedError,
  SelectablePrimitiveType,
  Primitive,
  open_new_view,
  opened_views,
  active_view,
  active_view_or_new_view,
  coordinate_pick,
  object_pick,
  primitive_pick,
  write_report,
)
from mapteksdk.internal.shared_operations import (
  _loop_surface_iterative,
  _loop_surface_straight,
  _fix_surface,
)
from mapteksdk.workflows import WorkflowSelection

if typing.TYPE_CHECKING:
  from collections.abc import Sequence, MutableSequence

  from mapteksdk.data import (
    PointSet,
    Polygon,
    Polyline,
    Scan,
    Surface,
  )
  PointSetLike: typing.TypeAlias = str | ObjectID[PointSet] | PointSet
  PolylineLike: typing.TypeAlias = str | ObjectID[Polyline] | Polyline
  PolygonLike: typing.TypeAlias = str | ObjectID[Polygon] | Polygon
  ScanLike: typing.TypeAlias = str | ObjectID[Scan] | Scan
  SurfaceLike: typing.TypeAlias = str | ObjectID[Surface] | Surface
  TopologyLike: typing.TypeAlias = str | ObjectID[Topology] | Topology

  class DistanceFromObjectOutputs(typing.TypedDict):
    """The output from the `distance_from_objects` operation."""
    selection: WorkflowSelection
    """The output selection.

    This should be identical to the `objects_to_colour` input.
    """
    mean_distance: float | None
    """The mean distance from the objects.

    This will be None if the application does not report the mean distance.
    """

__all__ = (
  # Defined in mapteksdk.operations:
  "TooOldForOperation",
  "PickFailedError",
  "SelectablePrimitiveType",
  "Primitive",
  "open_new_view",
  "opened_views",
  "active_view",
  "active_view_or_new_view",
  "coordinate_pick",
  "object_pick",
  "primitive_pick",
  "write_report",

  # Defined in this module:
  "DistanceMeasurementTarget",
  "DistanceType",
  "TriangulationOutput",
  "MaskOperation",
  "colour_by_distance_from_object",
  "contour_surface",
  "fill_holes",
  "filter_by_polygon",
  "filter_isolated_points",
  "filter_minimum_separation",
  "filter_topography",
  "simplify_by_distance_error",
  "simplify_by_triangle_count",
  "despike",
  "fix_surface",
  "topographic_triangulation",
  "loop_surface_straight",
  "loop_surface_iterative",
)

COMMAND_PREFIX = 'Maptek.PointStudio.Python.Commands'

class DistanceMeasurementTarget(enum.Enum):
  """If there are multiple objects to measure the distance to this specifies
  how it should be done."""
  CLOSEST_OBJECT = 1
  AVERAGE = 2


class DistanceType(enum.Enum):
  """Specifies whether distances should be considered as a signed or absolute.
  """
  SIGNED = 1
  ABSOLUTE = 2


class TriangulationOutput(enum.Enum):
  """Specifies what the output of a triangulation should be."""
  SINGLE_SURFACE = 1
  SURFACE_PER_OBJECT = 2
  SPLIT_ALONG_EDGE_CONSTRAINTS = 3  # The edges will be specified separately.
  RELIMIT_TO_POLYGON = 4  # The polygon will be specified separately.


class MaskOperation(enum.Enum):
  """Specifies how an operation should act with existing data.

  This is typically used for filtering operations.
  """
  AND = 1
  OR = 2
  REPLACE = 3

  def format_to_operation_string(self):
    """Format the value as expected by an operation input."""
    if self is self.AND:
      return 'And'
    if self is self.OR:
      return 'Or'
    if self is self.REPLACE:
      return 'Replace'

    raise ValueError(f'Unknown value {self.value}')


def colour_by_distance_from_object(
    objects_to_colour: Sequence[TopologyLike],
    base_objects: Sequence[TopologyLike],
    measurement_target: DistanceMeasurementTarget,
    distance_type: DistanceType,
    legend: ObjectID[NumericColourMap],
  ) -> DistanceFromObjectOutputs:
  """Colour points based on their distance from the base objects.

  This is useful for comparing triangulations of as-built surfaces against
  design models to highlight non-conformance. It can also be used to visualise
  areas of change between scans of the same area, for example a slow moving
  failure in an open pit mine.

  Parameters
  ----------
  objects_to_colour
    The objects to colour.
  base_objects
    The base or reference objects to measure the distance from.
  measurement_target
    If CLOSEST_OBJECT then colouring is based on the closest base object to
    that point.
    If AVERAGE then colour is based on the average distance to every base
    object.
  distance_type
    If SIGNED then colouring will depend on which side of the base objects it is
    on.
    If ABSOLUTE then colouring will depend on the absolute distance.
  legend
    A numeric 1D colour map to use as the legend for colouring the object.

  Returns
  -------
  dict
    A dictionary with two keys - "selection" and "mean_distance".
    The value of the "selection" key will be the objects which were coloured.
    The value of the "mean_distance" key will be the mean distance from the
    object to colour to the base objects.
  """
  if not isinstance(legend, ObjectID) or not legend.is_a(NumericColourMap):
    raise TypeError(default_type_error_message(
      argument_name="legend",
      actual_value=legend,
      required_type=ObjectID[NumericColourMap]
    ))
  if not isinstance(measurement_target, DistanceMeasurementTarget):
    raise TypeError(default_type_error_message(
      argument_name="measurement_target",
      actual_value=measurement_target,
      required_type=DistanceMeasurementTarget
    ))
  if not isinstance(distance_type, DistanceType):
    raise TypeError(default_type_error_message(
      argument_name="distance_type",
      actual_value=distance_type,
      required_type=DistanceType
    ))

  format_selection = RequestTransactionWithInputs.format_normalised_selection

  selection = normalise_selection(objects_to_colour)
  if len(selection) == 0:
    raise ValueError(
      "Colour by distance from object requires at least one object to colour."
    )
  validate_selection(selection, Topology)

  base_selection = normalise_selection(base_objects)
  if len(base_selection) == 0:
    raise ValueError(
      "Colour by distance from object requires at least one base object."
    )
  validate_selection(base_selection, Topology)

  inputs = [
    ('selection', format_selection(selection)),
    # The typo of objects below is required and is expected by the transaction.
    ('baseObects', format_selection(base_selection)),
    ('legend', repr(legend)),
    ('Closest object',
     measurement_target is DistanceMeasurementTarget.CLOSEST_OBJECT),
    ('Average', measurement_target is DistanceMeasurementTarget.AVERAGE),
    ('Signed', distance_type is DistanceType.SIGNED),
    ('Absolute', distance_type is DistanceType.ABSOLUTE),
  ]

  outputs = request_transaction(
    server='sdpServer',
    transaction='mtp::sdpS_ColourDistanceFromSurfaceTransaction',
    command_name=f'{COMMAND_PREFIX}.ColourByDistance',
    inputs=inputs,
    )

  for output in outputs.value:
    if output['idPath'] == 'distance':
      mean_distance = float(output.get('value', 'NaN'))
      break
  else:
    mean_distance = None

  return {
    'selection': _decode_selection(outputs),
    'mean_distance': mean_distance,
  }


def contour_surface(
  surfaces: Sequence[SurfaceLike],
  lower_limit: float,
  upper_limit: float,
  major_contour_intervals: float=15.0,
  major_contour_colour: Sequence[int]=(0, 255, 255, 255),
  minor_contour_intervals: float | None=None,
  minor_contour_colour: Sequence[int]=(255, 0, 127, 255),
  destination_path: str | None=None
) -> WorkflowSelection:
  """Create contours from surfaces (triangulations).

  The contours are saved into an edge network object.

  Parameters
  ----------
  surfaces
    The surfaces to contour.
  lower_limit
    The minimum value of the contours (the lowest elevation).
  upper_limit
    The maximum value of the contours (the highest elevation).
  major_contour_intervals
    The difference in elevation between major contour lines.
  major_contour_colour
    The colour of the major contour lines. This may be a RGB colour
    [red, green, blue] or a RGBA colour [red, green, blue, alpha].
  minor_contour_intervals
    If None then no minor contours lines will be included.
    The difference in elevation between minor contour lines between
    the major contour lines.
  minor_contour_colour
    The colour of the minor contour lines. This may be a RGB colour
    [red, green, blue] or a RGBA colour [red, green, blue, alpha].
    This is only relevant if minor_contour_intervals is not None.
  destination_path
    The path to where the contours should be written.
    If None then the default path will be used.

  Returns
  ----------
  WorkflowSelection
    The edge networks which contain the resulting contour lines if there are
    no minor contours. Otherwise, containers which contain the contour lines.

  Raises
  ------
  ValueError
    If a colour cannot be converted to a valid RGBA colour.
  ValueError
    If lower_limit is greater than upper_limit. You may have simply passed the
    arguments in the wrong way around.
  """

  if lower_limit > upper_limit:
    raise ValueError(f'The lower limit is greater ({lower_limit:.3f}) than '
                     f'the upper limit ({upper_limit:.3f})')

  def _format_colour(colour):
    """Format a single colour for use as the value for a workflow input."""
    rgba_colour = convert_to_rgba(colour)
    # pylint: disable=consider-using-f-string
    return '({},{},{},{})'.format(*rgba_colour)

  inputs: MutableSequence[tuple[str, typing.Any]] = [
    ('selection', RequestTransactionWithInputs.format_selection(surfaces)),
    ('lowerLimit', f'(0.0, 0.0, {lower_limit})'),
    ('upperLimit', f'(0.0, 0.0, {upper_limit})'),
    ('majorColour', _format_colour(major_contour_colour)),
    ('majorInterval', str(major_contour_intervals)),
  ]

  if minor_contour_intervals is not None:
    inputs.extend([
      ('useMinorContours', True),
      ('useMinorContours/minorInterval', str(minor_contour_intervals)),
      ('useMinorContours/minorColour',
       _format_colour(minor_contour_colour)),
    ])

  if destination_path:
    inputs.append(('destination', destination_path))

  outputs = request_transaction(
    server='sdpServer',
    transaction='mtp::sdpS_ContourFacetNetworkTransaction',
    command_name=f'{COMMAND_PREFIX}.ContourSurface',
    inputs=inputs,
    )

  return _decode_selection(outputs)

def fill_holes(surfaces: Sequence[SurfaceLike]):
  """Fills holes that may appear when editing a surface (triangulation).

  Parameters
  ----------
  surfaces
    The surfaces to have holes filled in.
  """

  inputs = [
    ('selection', RequestTransactionWithInputs.format_selection(surfaces)),
  ]

  request_transaction(
    server='sdpServer',
    transaction='mtp::sdpS_FillHolesTransaction',
    command_name=f'{COMMAND_PREFIX}.FillHoles',
    inputs=inputs,
    )


def filter_by_polygon(
  scans: Sequence[ScanLike | PointSetLike],
  polygon: ObjectID[Polygon],
  extrusion_direction: tuple[float, float, float]=(0, 0, 1),
  keep_points_inside: bool=True,
  filter_combination: MaskOperation=MaskOperation.AND
):
  """Filter scan data specified by a polygon.

  This can either retain points inside or outside of the polygon.

  Parameters
  ----------
  scans
    The scans to which the filter should be applied.
  polygon
    The polygons by which to filter
  extrusion_direction
    The direction of the polygon extrusions.
  keep_points_inside
    If true then points inside the polygon region are kept, otherwise
    points outside the polygon region are kept.
  filter_combination
    Specify how to combine this filter with any filter previously applied to
    the selected data.

  Raises
  ------
  ValueError
    If extrusion_direction is not a three dimensional vector.
  """
  format_selection = RequestTransactionWithInputs.format_selection

  if numpy.shape(extrusion_direction) != (3,):
    raise ValueError('The extrusion direction must be a vector with a X, Y '
                     'and Z component.')

  inputs = [
    ('selection', format_selection(scans)),
    ('polygon', repr(polygon)),
    # pylint: disable=consider-using-f-string
    ('direction', '({}, {}, {})'.format(*extrusion_direction)),
    ('Inside', keep_points_inside),
    ('Outside', not keep_points_inside),
    ('maskOperation', filter_combination.format_to_operation_string()),
  ]

  request_transaction(
    server='sdpServer',
    transaction='mtp::sdpS_MaskByPolygonTransaction',
    command_name=f'{COMMAND_PREFIX}.FilterPolygon',
    inputs=inputs,
    )


def filter_isolated_points(
  scans: Sequence[ScanLike | PointSetLike],
  point_separation: float,
  filter_combination: MaskOperation=MaskOperation.AND
):
  """Filter point that are a large distance from any other points.

  This can be useful for filtering dust particles or insects that may have
  been scanned.

  Parameters
  ----------
  scans
    The scans to which the filter should be applied.
  point_separation
    Points without a neighbouring point within this distance will be filtered.
    Any points separated by less than this distance will be retained.
    This distance should be in metres.
  filter_combination : MaskOperation
    Specify how to combine this filter with any filter previously applied to
    the selected data.
  """

  format_selection = RequestTransactionWithInputs.format_selection

  inputs = [
    ('selection', format_selection(scans)),
    ('pointSeparation', str(point_separation)),
    ('maskOperation', filter_combination.format_to_operation_string()),
  ]

  request_transaction(
    server='sdpServer',
    transaction='::sdpS_MaskOutlierTransaction',
    command_name=f'{COMMAND_PREFIX}.FilterIsolatedPoints',
    inputs=inputs,
    )


def filter_minimum_separation(
  scans: Sequence[ScanLike | PointSetLike],
  minimum_distance: float,
  filter_combination: MaskOperation=MaskOperation.AND,
  treat_scans_separately: bool=False
):
  """Filter point sets to give a more even distribution.

  Point density decreases as the distance from the scanner increases, so this
  option is able to reduce the number of points close to the scanner whilst
  retaining points further away.

  Data reduction can have a major impact on the number of points in an object
  and on the modelling processes.

  Parameters
  ----------
  scans
    The scans to which the filter should be applied.
  minimum_distance
    The average minimum separation between points in the object. This distance
    should be in metres.
  filter_combination
    Specify how to combine this filter with any filter previously applied to
    the selected data.
  treat_scans_separately
    Treat scans separately such that each scan is considered in isolation.
    Otherwise it works on all objects as a complete set which results in an
    even distribution of data for the entire set of objects.
  """

  format_selection = RequestTransactionWithInputs.format_selection

  inputs = [
    ('selection', format_selection(scans)),
    ('minimumDistance', str(minimum_distance)),
    ('maskOperation', filter_combination.format_to_operation_string()),
    ('Apply filter to selection as a whole',
     not treat_scans_separately),
  ]

  request_transaction(
    server='sdpServer',
    transaction='mtp::sdpS_MaskMinimumSeparationTransaction',
    command_name=f'{COMMAND_PREFIX}.FilterMinimumSeparation',
    inputs=inputs,
    )


def filter_topography(
  scans: Sequence[ScanLike | PointSetLike],
  search_cell_size: float,
  keep_lower_points: bool=True,
  filter_combination: MaskOperation=MaskOperation.AND,
  treat_scans_separately: bool=False
):
  """Filter point sets to remove unwanted features.

  This enables equipment such as trucks and loaders to be filtered and retains
  only the relevant topographic surface of the mine.

  The topography filter divides the scan data into a horizontal grid with a
  defined cell size. Only the single lowest or highest point in the cell is
  retained.

  Data reduction can have a major impact on the number of points in an object
  and on the modelling processes.

  Parameters
  ----------
  scans
    The scans to which the filter should be applied.
  search_cell_size
    The size of the cells. A typical cell size is between 0.5 and 2 metres.
    If the cell size is too large it will have the effect of rounding edges.
  keep_lower_points
    If true then lower points are kept, otherwise the upper points are kept.
    Upper points would only be used in an underground situation to retain the
    roof.
  filter_combination
    Specify how to combine this filter with any filter previously applied to
    the selected data.
  treat_scans_separately
    Treat scans separately such that each scan is considered in isolation.
    Otherwise it works on all objects as a complete set which results in an
    even distribution of data for the entire set of objects.
  """

  format_selection = RequestTransactionWithInputs.format_selection

  inputs = [
    ('selection', format_selection(scans)),
    ('searchCellSize', str(search_cell_size)),
    ('Lower points', keep_lower_points),
    ('Upper points', not keep_lower_points),
    ('maskOperation', filter_combination.format_to_operation_string()),
    ('Apply filter to selection as a whole',
     not treat_scans_separately),
  ]

  request_transaction(
    server='sdpServer',
    transaction='mtp::sdpS_MaskHighLowTransaction',
    command_name=f'{COMMAND_PREFIX}.FilterTopography',
    inputs=inputs,
    )


def simplify_by_distance_error(
  surfaces: Sequence[ScanLike | PointSetLike],
  distance_error: float,
  preserve_boundary_edges: bool=False,
  avoid_intersections: bool=True
) -> WorkflowSelection:
  """Simplify a surface.

  This reduces the number of facets while maintaining the surface shape.

  Triangulation simplification can introduce inconsistencies in the surface,
  such as triangles that overlap or cross.

  Parameters
  ----------
  surfaces
    The surfaces to simplify.
  distance_error
    The maximum allowable average error by which each simplified surface can
    deviate from its original surface.
  preserve_boundary_edges
    Specify if the surface boundary should remain unchanged.
  avoid_intersections
    Prevent self intersections in the resulting surface. This will offer
    some performance benefit at the cost that the resulting surface may not
    work with other tools until the self intersections are fixed.

  Returns
  ----------
  WorkflowSelection
    The surfaces which were simplified.
  """

  inputs = [
    ('selection', RequestTransactionWithInputs.format_selection(surfaces)),
    ('distanceError', str(distance_error)),
    ('preserveBoundaryEdges', preserve_boundary_edges),
    ('avoidIntersections', avoid_intersections),
  ]

  outputs = request_transaction(
    server='sdpServer',
    transaction='mtp::sdpS_SimplifyFacetNetworkPanelTransaction',
    command_name=f'{COMMAND_PREFIX}.SimplifyByDistanceError',
    requester_icon=Icon('SimplifyTriangulationError'),
    inputs=inputs,
    )

  return _decode_selection(outputs)


def simplify_by_triangle_count(
  surfaces: Sequence[SurfaceLike],
  triangle_count: int,
  preserve_boundary_edges: bool=False,
  avoid_intersections: bool=True
) -> WorkflowSelection:
  """Simplifies a surface by facet count.

  This reduces the number of facets while maintaining the surface shape.

  This should be used if there there is a specific number of triangles to which
  the triangulation must be restricted.

  Triangulation simplification can introduce inconsistencies in the surface,
  such as triangles that overlap or cross.

  Parameters
  ----------
  surfaces
    The surfaces to simplify.
  triangle_count
    The target number of triangles is the approximate number of triangles each
    simplified triangulation (surface) will contain.
  preserve_boundary_edges
    Specify if the surface boundary should remain unchanged.
  avoid_intersections
    Prevent self intersections in the resulting surface. This will offer
    some performance benefit at the cost that the resulting surface may not
    work with other tools until the self intersections are fixed.

  Returns
  ----------
  WorkflowSelections
    The surfaces which were simplified.
  """

  inputs = [
    ('selection', RequestTransactionWithInputs.format_selection(surfaces)),
    ('facetCount', str(triangle_count)),
    ('preserveBoundaryEdges', preserve_boundary_edges),
    ('avoidIntersections', avoid_intersections),
  ]

  outputs = request_transaction(
    server='sdpServer',
    transaction='mtp::sdpS_SimplifyFacetNetworkPanelTransaction',
    command_name=f'{COMMAND_PREFIX}.SimplifyByFacetCount',
    requester_icon=Icon('SimplifyTriangulationCount'),
    inputs=inputs,
    )

  return _decode_selection(outputs)


def despike(
  surfaces: Sequence[SurfaceLike]
) -> WorkflowSelection:
  """Remove spikes from a triangulation.

  The Despike option removes spikes caused by dust or vegetation that may
  appear when creating a data model. This modifies the objects in-place, i.e
  it does not create a copy of the data.

  If unwanted points remain after running the despike tool, these must be
  manually deleted or a supplementary tool may resolve the issues.

  Parameters
  ----------
  surfaces
    The surfaces to despike.

  Returns
  ----------
  WorkflowSelection
    The surfaces which were despiked.
  """

  # There were no surfaces to despike.
  if not surfaces:
    return WorkflowSelection(selection_string="")

  inputs = [
    ('selection', RequestTransactionWithInputs.format_selection(surfaces)),
  ]

  outputs = request_transaction(
    server='sdpServer',
    transaction='mtp::sdpS_FacetNetworkDespikerTransaction',
    command_name=f'{COMMAND_PREFIX}.Despike',
    inputs=inputs,
  )

  return _decode_selection(outputs)


def fix_surface(
  surfaces: Sequence[SurfaceLike]
) -> WorkflowSelection:
  """Automates the fixing of common issues with surfaces (triangulation).

  The fixes it performs are:
  - Self intersections - Fixes cases where the surface intersects itself

  - Trifurcations - Fixes cases where the surface meets itself, creating a
    T-junction.

  - Facet normals - Orient facet normals to point in the same direction.
    This will be up for surfaces/topography and out for solids.

  - Vertical facets - Remove vertical facets and close the hole this produces
    by moving the points along the top down, adding points as necessary to
    neighbouring non-vertical facets to maintain a consistent surface.

  Parameters
  ----------
  surfaces
    The surfaces to fix.

  Returns
  ----------
  list
    The fixed surfaces.
  """
  return _fix_surface(surfaces, COMMAND_PREFIX)


def topographic_triangulation(
    scans: Sequence[ScanLike | PointSetLike],
    trim_edges_to_maximum_length: float | None=None,
    output_option: TriangulationOutput=TriangulationOutput.SINGLE_SURFACE,
    relimit_to_polygon: ObjectID[Polygon] | None=None,
    edge_constraints: Sequence[PolygonLike | PolygonLike] | None=None,
    destination: str=''
  ):
  """Create triangulations (surfaces) of a group of scans.

  This works in the XY plane, that is, it triangulates straight down.
  This means that if there are areas of undercut walls, these will not
  be modelled accurately.

  This option is typically used once scans have been registered and filtered.

  Parameters
  ----------
  scans
    The scan objects to triangulate.
  trim_edges_to_maximum_length
    If not None, then long, incorrectly generated boundary triangles will be
    eliminated. A maximum length is specified, which prevents triangles
    greater than this being created.
    This option is only applicable to boundary triangles; large voids in the
    centre of the data will still be modelled.
  output_option
    If SINGLE_SURFACE, then this creates a single surface from the selected
    objects/scans.
    If SURFACE_PER_OBJECT, then this creates a single surface for each
    selected object/scan.
    If SPLIT_ALONG_EDGE_CONSTRAINTS, then splits the triangulation into
    separate objects based on any lines or polygons provided by
    edge_constraints.
  relimit_to_polygon
    Constrains the model to a polygon, for example a pit boundary.
    The output_option must be RELIMIT_TO_POLYGON to use this.
  edge_constraints
    The lines and polygons to use when splitting the triangulation into
    separate objects. The output_option must be SPLIT_ALONG_EDGE_CONSTRAINTS
    to use this.
  destination
    An optional path to the container to store the resulting triangulations.
    The empty string will use a default path.
  """

  if relimit_to_polygon and \
      output_option is not TriangulationOutput.RELIMIT_TO_POLYGON:
    raise ValueError('If providing a polygon to relimit to, the output_option '
                     'should be RELIMIT_TO_POLYGON')

  if edge_constraints and \
      output_option is not TriangulationOutput.SPLIT_ALONG_EDGE_CONSTRAINTS:
    raise ValueError('If providing the edges for edge constraints, the '
                     'output_option should be SPLIT_ALONG_EDGE_CONSTRAINTS')

  selection: Sequence[
    TopologyLike] = list(scans) + list(edge_constraints or [])
  inputs: list[tuple[str, typing.Any]] = [
    ('selection',
     RequestTransactionWithInputs.format_selection(selection)),
  ]

  if destination:
    inputs.append(('destination', destination))

  if Mcp().version >= (1, 10):  # PointStudio 2024 or later.
    if trim_edges_to_maximum_length is None:
      inputs.append(('trimLargeTriangles', False))
    else:
      inputs.extend([
        ('trimLargeTriangles', True),
        ('trimLargeTriangles/boundaryEdgesOnly', True),
        ('trimLargeTriangles/maximumEdgeLength',
        str(trim_edges_to_maximum_length)),
      ])
  else:
    # The properties were renamed in PointStudio 2023, which did not have an
    # API version change. To handle both this version and older version, the
    # new and old names are both sent. This works because older versions will
    # ignore the new names and PointStudio 2023 will ignore the old names.
    if trim_edges_to_maximum_length is None:
      inputs.append(('trimBoundaryTriangles', False))
      inputs.append(('trimLargeTriangles', False))
    else:
      inputs.extend([
        # Old names for before PointStudio 2023.
        ('trimBoundaryTriangles', True),
        ('trimBoundaryTriangles/maximumEdgeLength',
        trim_edges_to_maximum_length),

        # New names for PointStudio 2023.
        ('trimLargeTriangles', True),
        ('trimLargeTriangles/boundaryEdgesOnly', True),
        ('trimLargeTriangles/maximumEdgeLength',
        trim_edges_to_maximum_length),
      ])
  if output_option is TriangulationOutput.SINGLE_SURFACE:
    inputs.extend([
      ('singleSurface', True),
      ('singleSurfacePerObject', False),
      ('relimitToPolygon', False),
      ('splitAlongEdgeConstraints', False),
    ])
  elif output_option is TriangulationOutput.SURFACE_PER_OBJECT:
    inputs.extend([
      ('singleSurface', False),
      ('singleSurfacePerObject', True),
      ('relimitToPolygon', False),
      ('splitAlongEdgeConstraints', False),
    ])
  elif output_option is TriangulationOutput.SPLIT_ALONG_EDGE_CONSTRAINTS:
    inputs.extend([
      ('singleSurface', False),
      ('singleSurfacePerObject', False),
      ('relimitToPolygon', False),
      ('splitAlongEdgeConstraints', True),
    ])
  elif output_option is TriangulationOutput.RELIMIT_TO_POLYGON:
    inputs.extend([
      ('singleSurface', False),
      ('singleSurfacePerObject', False),
      ('relimitToPolygon', True),
      ('splitAlongEdgeConstraints', False),
      ('relimitToPolygon/relimitPolygon', repr(relimit_to_polygon)),
    ])

  request_transaction(
    server='sdpServer',
    transaction='mtp::sdpS_Triangulation2DTransaction',
    command_name=f'{COMMAND_PREFIX}.TopographicTriangulation',
    inputs=inputs,
    )


def loop_surface_straight(
  selection: Sequence[SurfaceLike | PolygonLike],
  destination: str | None=None
) -> WorkflowSelection:
  """Create a Surface from a series of loops using "straight loop ordering".

  This creates a single Surface with the loops connected based on
  their orientation.

  Parameters
  ----------
  selection
    The Surfaces or Polygons to use to generate the loop surface.
    Each must contain loops.
  destination
    Path to place the destination object. If not specified,
    this will use the default destination of the menu item.

  Returns
  -------
  WorkflowSelection
    Selection containing the created Surface.
  """
  return _loop_surface_straight(selection, COMMAND_PREFIX, destination)


def loop_surface_iterative(
  selection: Sequence[SurfaceLike | PolygonLike],
  destination: str | None=None
) -> WorkflowSelection:
  """Creates Surfaces from a series of loops using "iterative loop ordering".

  This joins nearby loops with similar orientations. This can create
  multiple surfaces and may wrap around corners if needed.

  Unlike loop_surface_straight, this may ignore loops if they are not
  sufficiently close to another loop.

  Parameters
  ----------
  selection
    List of Surfaces or Polygons to use to generate the loop surfaces.
    Each must contain loops.
  destination
    Path to place the destination object. If not specified,
    this will use the default destination of the menu item.

  Returns
  -------
  WorkflowSelection
    Selection containing the created Surface(s).
  """
  return _loop_surface_iterative(selection, COMMAND_PREFIX, destination)
