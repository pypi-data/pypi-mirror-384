"""Modules which provide support for topological primitives.

Warnings
--------
The contents of this module should be considered implementation details.
The documentation is provided for completeness only. Scripts should not use
this module directly.

"""
###############################################################################
#
# (C) Copyright 2020, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
import typing

from .attribute_key import AttributeKey
from .block_properties import BlockProperties
from .cell_properties import CellProperties
from .colour_scheme import ColourScheme
from .edge_properties import EdgeProperties
from .facet_properties import FacetProperties
from .point_properties import PointProperties, PointDeletionProperties

if typing.TYPE_CHECKING:
  __all__ = [
    "AttributeKey",
    "BlockProperties",
    "CellProperties",
    "ColourScheme",
    "EdgeProperties",
    "FacetProperties",
    "PointDeletionProperties",
    "PointProperties",
  ]
