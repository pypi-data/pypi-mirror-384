"""Change reasons for objects."""
###############################################################################
#
# (C) Copyright 2023, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

import enum

class ChangeReasons(enum.Flag):
  """Change reasons for an object.

  This allows for identifying which changes were made to an object.
  """
  NO_CHANGE = 0
  """Nothing has changed.

  This is returned if save() detected that no changes needed to be
  made to the object.

  This is also returned when connected to applications with an
  API version < 1.9, because the change reason cannot be determined
  in that case.
  """
  # Change reasons defined in de.H
  DESTROYED = 1 << 0
  """The object was destroyed.

  This change reason cannot be returned by save(), because it cannot
  destroy objects.
  """
  CREATED = 1 << 1
  """The object was created.

  This change reason will not be returned when calling save() in
  project.new() because the Python SDK creates the object before
  it is yielded by that function.
  """
  CONTENT_ADDED = 1 << 4
  """Data was added to the object.

  This is primarily triggered when adding children to a container.
  """
  CONTENT_REMOVED = 1 << 5
  """Data was removed from the object.

  This is primarily triggered when removing children from a container.
  """
  DESCRIPTION_CHANGED = 1 << 6
  """The description of the object changed."""
  CHILD_DESTROYED = 1 << 7
  """A child of the object was destroyed.

  This cannot be returned when calling save(), because save() cannot
  destroy children of objects.
  """
  FLAGS_CHANGED = 1 << 9
  """The flags of a container were changed.

  As of 2023-03-03, this cannot be triggered from Python.
  """
  EXTRA_HEADER_DATA_CHANGED = 1 << 10
  """Object-specific header data was changed.

  This is typically returned when an attribute with a single value for
  the entire object is changed.
  """
  SLAB_CONTENTS_CHANGED = 1 << 11
  """Data in the object was changed.

  This is typically returned when an attribute with one value per primitive
  is changed.
  """
  ATTRIBUTE_CHANGED = 1 << 12
  """One of the object's attributes has changed.

  This will be triggered if DataObject.set_attribute() is called.
  This may also be triggered if DataObject.get_attribute() is called.
  """

  # Change reasons defined in mdl.H
  GEOMETRY_CHANGED = 1 << 13
  """The geometry of the object was changed.

  This is triggered when the points or blocks of an object are changed.
  """
  TOPOLOGY_CHANGED = 1 << 14
  """The topology of the object was changed.

  This is triggered when the edges, facets or cells of an object are changed.
  Note that if both the topology and the geometry changes, only
  a GEOMETRY_CHANGED reason will be emitted.
  """
  POINT_ATTRIBUTE_CHANGED = 1 << 15
  """An attribute with one value per point was changed."""
  EDGE_ATTRIBUTE_CHANGED = 1 << 16
  """An attribute with one value per edge was changed."""
  FACET_ATTRIBUTE_CHANGED = 1 << 17
  """An attribute with one value per facet was changed."""
  TETRA_ATTRIBUTE_CHANGED = 1 << 18
  """An attribute with one value per tetra was changed.

  Notes
  -----
  As of 2023-03-03, no Maptek application supports objects with tetra
  primitives. This is included for completeness.
  """
  CELL_ATTRIBUTE_CHANGED = 1 << 19
  """An attribute with one value per cell was changed."""
  BLOCK_ATTRIBUTE_CHANGED = 1 << 20
  """An attribute with one value per block was changed."""
  POINT_SELECTION_CHANGED = 1 << 21
  """The point selection was changed."""
  EDGE_SELECTION_CHANGED = 1 << 22
  """The edge selection was changed."""
  FACET_SELECTION_CHANGED = 1 << 23
  """The facet selection was changed."""
  TETRA_SELECTION_CHANGED = 1 << 24
  """The tetra selection was changed.

  See Notes on TETRA_ATTRIBUTE_CHANGED above.
  """
  CELL_SELECTION_CHANGED = 1 << 25
  """The cell selection was changed."""
  BLOCK_SELECTION_CHANGED = 1 << 26
  """The block selection was changed."""
  POINT_HIGHLIGHT_CHANGED = 1 << 27
  """The point highlight was changed."""
  FEATURE_CHANGED = 1 << 28
  """The feature was changed.

  For example, the object was changed to be rendered as wireframe in the view.
  """
  TEXTURE_CHANGED = 1 << 29
  """The texture of the object has changed."""

  # Change reasons defined in vis.H
  TRANSFORM_CHANGED = 1 << 13
  """The transform of the object has been changed.

  As of 2023-03-03, this cannot be triggered from Python.
  """

  # Unused change reasons.
  UNUSED_A = 1 << 2
  """Included to ensure the SDK does not error if it is encountered."""
  UNUSED_B = 1 << 3
  """Included to ensure the SDK does not error if it is encountered."""
  UNUSED_C = 1 << 8
  """Included to ensure the SDK does not error if it is encountered."""
  UNUSED_D = 1 << 30
  """Included to ensure the SDK does not error if it is encountered."""
  UNUSED_E = 1 << 31
  """Included to ensure the SDK does not error if it is encountered."""
