"""Representation of the objects within a Project.

Many of the types within this package can be used to create a new object
of that type through Project.new(). Classes defined in this module are yielded
when opening an object via Project.read() and Project.edit().

See Also
--------
:documentation:`data-types` : Documentation of data types.

"""
###############################################################################
#
# (C) Copyright 2020, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

import typing

from .annotations import (
  Text2D,
  Text3D,
  Marker,
  VerticalAlignment,
  HorizontalAlignment,
  FontStyle,
)
from .base import DataObject, Topology, Appearance
from .blocks import DenseBlockModel, SubblockedBlockModel, SparseBlockModel
from .block_model_definition import BlockModelDefinition, SubblockRatio
from .block_utilities import (
  create_dense_model_from_definition,
  create_subblocked_model_from_definition,
  create_model_from_definition,
)
from .cells import GridSurface
from .change_reasons import ChangeReasons
from .colourmaps import (
  NumericColourMap,
  StringColourMap,
  UnsortedRangesError,
  CaseInsensitiveDuplicateKeyError,
)
from .containers import Container, VisualContainer, StandardContainer
from .coordinate_systems import (
  CoordinateSystem,
  LocalTransform,
  LocalTransformNotSupportedError,
)
from .edges import EdgeNetwork, Polygon, Polyline
from .ellipsoid import Ellipsoid
from .errors import (
  CannotSaveInReadOnlyModeError,
  DegenerateTopologyError,
  InvalidColourMapError,
)
from .facets import Surface
from .filled_polygon import FilledPolygon
from .geotechnical import Discontinuity, Polarity
from .images import Raster
from .image_registration import (
  RasterRegistrationTwoPoint,
  RasterRegistrationNone,
  RasterRegistrationUnsupported,
  RasterRegistrationMultiPoint,
  RasterRegistrationOverride
)
from .objectid import ObjectID
from .ribbons import RibbonChain, RibbonLoop
from .points import PointSet
from .primitives import AttributeKey, ColourScheme
from .scans import Scan
from .selection_file import SelectionFile
from .selection_group import _SelectionGroup, _SelectionGroupType
from .units import DistanceUnit, AngleUnit, UnsupportedUnit, Axis

if typing.TYPE_CHECKING:
  __all__ = [
    "AngleUnit",
    "Appearance",
    "AttributeKey",
    "Axis",
    "BlockModelDefinition",
    "CannotSaveInReadOnlyModeError",
    "CaseInsensitiveDuplicateKeyError",
    "ChangeReasons",
    "ColourScheme",
    "Container",
    "CoordinateSystem",
    "DenseBlockModel",
    "DataObject",
    "DegenerateTopologyError",
    "Discontinuity",
    "DistanceUnit",
    "EdgeNetwork",
    "Ellipsoid",
    "FilledPolygon",
    "FontStyle",
    "GridSurface",
    "HorizontalAlignment",
    "InvalidColourMapError",
    "LocalTransform",
    "LocalTransformNotSupportedError",
    "Marker",
    "NumericColourMap",
    "ObjectID",
    "PointSet",
    "Polarity",
    "Polygon",
    "Polyline",
    "Raster",
    "RasterRegistrationMultiPoint",
    "RasterRegistrationNone",
    "RasterRegistrationOverride",
    "RasterRegistrationTwoPoint",
    "RasterRegistrationUnsupported",
    "RibbonChain",
    "RibbonLoop",
    "SelectionFile",
    "_SelectionGroup",
    "_SelectionGroupType",
    "Scan",
    "SparseBlockModel",
    "StringColourMap",
    "StandardContainer",
    "SubblockedBlockModel",
    "SubblockRatio",
    "Surface",
    "Text2D",
    "Text3D",
    "Topology",
    "UnsortedRangesError",
    "UnsupportedUnit",
    "VerticalAlignment",
    "VisualContainer",

    # Free functions.
    "create_dense_model_from_definition",
    "create_subblocked_model_from_definition",
    "create_model_from_definition",
  ]
