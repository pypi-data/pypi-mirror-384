"""Class representing the action plane of a view.

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
from mapteksdk.geometry import Plane
from mapteksdk.internal.comms import InlineMessage, Double

class ActionPlane(InlineMessage):
  """An action plane is a plane set in a view.

  It is used for digitising points and describing the plane to use for
  quickly setting up clip plane sectioning data.
  """
  plane_coefficient_a: Double
  plane_coefficient_b: Double
  plane_coefficient_c: Double
  plane_coefficient_d: Double

  visualisation_centroid_x: Double = float('NaN')
  visualisation_centroid_y: Double = float('NaN')
  visualisation_centroid_z: Double = float('NaN')

  grid_orientation_x: Double = float('NaN')
  grid_orientation_y: Double = float('NaN')
  grid_orientation_z: Double = float('NaN')

  @property
  def plane(self) -> Plane:
    """The plane portion of the action plane."""
    return Plane(self.plane_coefficient_a,
                 self.plane_coefficient_b,
                 self.plane_coefficient_c,
                 self.plane_coefficient_d)

  @plane.setter
  def plane(self, plane: Plane):
    """The plane portion of the action plane."""
    self.plane_coefficient_a = plane.coefficient_a
    self.plane_coefficient_b = plane.coefficient_b
    self.plane_coefficient_c = plane.coefficient_c
    self.plane_coefficient_d = plane.coefficient_d