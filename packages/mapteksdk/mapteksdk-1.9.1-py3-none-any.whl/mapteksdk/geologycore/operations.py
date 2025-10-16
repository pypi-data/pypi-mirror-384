"""Operations available in GeologyCore.

Operations exposes functionality from within an application that can be
invoked from Python functions. These typically correspond to menu items that
are available in the application, but their inputs can be populated from Python
without requiring the user to fill them out.

Notes
-----
Some of the operations available in this module are defined in the general
operations module and can be imported from there instead. Such operations
are not limited to being used with GeologyCore.
"""

###############################################################################
#
# (C) Copyright 2021, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import typing

from mapteksdk.common import convert_to_rgba
from mapteksdk.capi import Mcp
from mapteksdk.internal.transaction import (request_transaction,
                                            RequestTransactionWithInputs)
# pylint: disable=unused-import
# Import general operations so that they can be imported from this module.
from mapteksdk.operations import (TooOldForOperation,
                                  PickFailedError, SelectablePrimitiveType,
                                  Primitive, open_new_view, opened_views,
                                  active_view, active_view_or_new_view,
                                  coordinate_pick, object_pick,
                                  primitive_pick, write_report,
                                  _decode_selection)
from mapteksdk.pointstudio.operations import TriangulationOutput
from ..internal.shared_operations import (_loop_surface_iterative,
                                          _loop_surface_straight,
                                          _fix_surface)

if typing.TYPE_CHECKING:
  from collections.abc import Sequence

  from mapteksdk.data import (
    ObjectID,
    PointSet,
    Polygon,
    Polyline,
    Scan,
    Surface,
    Topology,
  )
  from mapteksdk.workflows import WorkflowSelection
  PointSetLike: typing.TypeAlias = str | ObjectID[PointSet] | PointSet
  PolylineLike: typing.TypeAlias = str | ObjectID[Polyline] | Polyline
  PolygonLike: typing.TypeAlias = str | ObjectID[Polygon] | Polygon
  ScanLike: typing.TypeAlias = str | ObjectID[Scan] | Scan
  SurfaceLike: typing.TypeAlias = str | ObjectID[Surface] | Surface
  TopologyLike: typing.TypeAlias = str | ObjectID[Topology] | Topology

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
  "topographic_triangulation",
  "boundary_edges",
  "contour_surface",
  "loop_surface_straight",
  "loop_surface_iterative",
  "fix_surface",
)

COMMAND_PREFIX = 'Maptek.GeologyCore.Python.Commands'

def topographic_triangulation(
  scans: Sequence[ScanLike | PointSetLike],
  trim_edges_to_maximum_length: float | None=None,
  output_option: TriangulationOutput=TriangulationOutput.SINGLE_SURFACE,
  relimit_to_polygon: ObjectID[Polygon] | None=None,
  edge_constraints: Sequence[PolylineLike | PolygonLike] | None=None,
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

  # The properties were renamed between GeologyCore 2023.1 (API 1.9) and
  # 2023.2 (API 1.10).
  if Mcp().version >= (1, 10):
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
    if trim_edges_to_maximum_length is None:
      inputs.append(('trimBoundaryTriangles', False))
    else:
      inputs.extend([
        ('trimBoundaryTriangles', True),
        ('trimBoundaryTriangles/maximumEdgeLength',
        str(trim_edges_to_maximum_length)),
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

def boundary_edges(
  selection: TopologyLike | Sequence[TopologyLike],
  merge_boundaries: bool=False
) -> WorkflowSelection:
  """Finds boundary edges for objects in the selection.

  This creates either a single edge network or multiple polylines which
  represent the edges of the objects in the selection.

  Parameters
  ----------
  selection
    List of paths or object ids of the objects to find the boundary edges
    for.
  merge_boundaries
    If True, all boundary edges are combined into a single edge network.
    If False, each boundary edge is a polygon. They are coloured green for
    edges around the perimeter of the object and red if they are edges
    around holes in the object.

  Returns
  -------
  WorkflowSelection
    Selection containing the created objects.
    If merge_boundaries is True, this will contain between zero and
    len(selection) objects.
    if merge_boundaries is False, this can contain any number of objects.

  Raises
  ------
  TransactionFailed
    If no object in selection is a Surface or Discontinuity.

  Warnings
  --------
  This operation will enter an infinite loop if all objects in the selection
  are surfaces which do not contain boundary edges.
  """
  inputs = [
    ('selection', RequestTransactionWithInputs.format_selection(selection)),
    ('Combine output', merge_boundaries)
  ]

  outputs = request_transaction(
    server='cadServer',
    transaction='mtp::cadS_FindBoundaryEdgesTransaction',
    command_name=f'{COMMAND_PREFIX}.Boundaries',
    inputs=inputs)

  return _decode_selection(outputs)

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
    The list of surfaces to contour.
  lower_limit
    The minimum value of the contours (the lowest elevation).
  upper_limit
    The maximum value of the contours (the highest elevation).
  major_contour_intervals
    The difference in elevation between major contour lines.
  major_contour_colour : sequence
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
  -------
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
    # Using format and unpacking is more readable than an f string.
    return '({},{},{},{})'.format(*rgba_colour)

  inputs = [
    ('selection', RequestTransactionWithInputs.format_selection(surfaces)),
    ('lowerLimit', f'(0.0, 0.0, {lower_limit})'),
    ('upperLimit', f'(0.0, 0.0, {upper_limit})'),
    ('manualContours', True),
    ('manualContours/majorColour', _format_colour(major_contour_colour)),
    ('manualContours/majorInterval', str(major_contour_intervals)),
  ]

  if minor_contour_intervals is not None:
    inputs.extend([
      ('manualContours/minorContours', True),
      ('manualContours/minorContours/minorInterval',
       str(minor_contour_intervals)),
      ('manualContours/minorContours/minorColour',
       _format_colour(minor_contour_colour)),
    ])

  if destination_path:
    inputs.append(('destination', destination_path))

  outputs = request_transaction(
    server='sdpServer',
    transaction='::sdpS_ContourFacetNetworkTransaction',
    command_name=f'{COMMAND_PREFIX}.ContourSurface',
    inputs=inputs,
    )

  return _decode_selection(outputs)

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
    Surfaces or Polygons to use to generate the loop surface.
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
    Surfaces or Polygons to use to generate the loop surfaces.
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
  WorkflowSelection
    The surfaces which were fixed.
  """
  return _fix_surface(surfaces, COMMAND_PREFIX)
