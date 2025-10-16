"""Module containing operations shared by multiple applications.

The operations included here are shared by multiple applications and use
almost identical implementations for each application, but they
are not general enough to be included in the general operations module.
"""
###############################################################################
#
# (C) Copyright 2021, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import typing

from mapteksdk.internal.transaction import (request_transaction,
                                            RequestTransactionWithInputs)
from mapteksdk.operations import _decode_selection
from mapteksdk.workflows import WorkflowSelection

if typing.TYPE_CHECKING:
  from collections.abc import Sequence

  from mapteksdk.data import ObjectID, Polygon, Surface
  PolygonLike: typing.TypeAlias = str | ObjectID[Polygon] | Polygon
  SurfaceLike: typing.TypeAlias = str | ObjectID[Surface] | Surface

def _loop_surface_straight(
  selection: typing.Sequence[SurfaceLike | PolygonLike],
  command_prefix: str,
  destination: str | None=None
) -> WorkflowSelection:
  """Create a Surface from a series of loops using "straight loop ordering".

  This creates a single Surface with the loops connected based on
  their orientation.

  Parameters
  ----------
  selection
    List of Surfaces or Polygons to use to generate the loop surface.
    Each must contain loops.
  command_prefix
    Command prefix for the application to run the operation.
  destination
    Path to place the destination object. If not specified,
    this will use the default destination of the menu item.

  Returns
  -------
  WorkflowSelection
    Selection containing the created Surface.
  """
  inputs = [
    ('selection', RequestTransactionWithInputs.format_selection(selection)),
    ('straightLoopOrdering', True),
    ('iterativeLoopOrdering', False),
  ]

  if destination:
    inputs.append(('destination', destination))

  outputs = request_transaction(
    server='sdpServer',
    transaction='mtp::sdpS_TriangulateLoopSetTransaction',
    command_name=f'{command_prefix}.TriangulateLoopSet',
    inputs=inputs,
    )

  return _decode_selection(outputs)


def _loop_surface_iterative(
  selection: Sequence[SurfaceLike | PolygonLike],
  command_prefix: str,
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
  command_prefix
    Command prefix for the application to run the operation.
  destination
    Path to place the destination object. If not specified,
    this will use the default destination of the menu item.

  Returns
  -------
  WorkflowSelection
    Selection containing the created Surface(s).

  """
  inputs = [
    ('selection', RequestTransactionWithInputs.format_selection(selection)),
    ('straightLoopOrdering', False),
    ('iterativeLoopOrdering', True),
  ]

  if destination:
    inputs.append(('destination', destination))

  outputs = request_transaction(
    server='sdpServer',
    transaction='mtp::sdpS_TriangulateLoopSetTransaction',
    command_name=f'{command_prefix}.TriangulateLoopSet',
    inputs=inputs,
    )

  return _decode_selection(outputs)

def _fix_surface(
  surfaces: Sequence[SurfaceLike],
  command_prefix: str
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
  command_prefix
    Command prefix for the application to run the operation.

  Returns
  ----------
  WorkflowSelection
    The fixed surfaces.
  """
  if not surfaces:
    return WorkflowSelection("")

  inputs = [
    ('selection', RequestTransactionWithInputs.format_selection(surfaces)),
    ('isFixingSelfIntersections', True),
    ('isFixingTrifurcations', True),
    ('isFixingFacetNormals', True),
    ('collapseVerticalFacet', 'Down'),  # Up is the other option.
  ]

  outputs = request_transaction(
    server='sdpServer',
    transaction='mtp::sdpS_FixFacetNetworkTransaction',
    command_name=f'{command_prefix}.FixSurface',
    inputs=inputs,
    )

  return _decode_selection(outputs)
