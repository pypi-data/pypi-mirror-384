"""Interface for the MDF modelling library.

Warnings
--------
Vendors and clients should not develop scripts or applications against
this module. The contents may change at any time without warning.

"""
###############################################################################
#
# (C) Copyright 2020, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

# pylint: disable=line-too-long
# pylint: disable=invalid-name;reason=Names match C++ names.
# pylint: disable=too-many-lines
# pylint: disable=too-many-public-methods
from collections.abc import Sequence
import ctypes
import typing
import warnings

import numpy as np

from ..errors import ApplicationTooOldError
from .errors import (
  CApiUnknownError,
  CApiUnknownWarning,
)
from .types import (T_ReadHandle, T_ObjectHandle, T_TypeIndex,
                    T_MessageHandle)
from .util import raise_if_version_too_old
from .dataengine import DataEngineApi
from .wrapper_base import WrapperBase

if typing.TYPE_CHECKING:
  from .internal.application_dll_directory import (
    ApplicationDllDirectoryProtocol,
  )


class ModellingApi(WrapperBase):
  """Access to the application modelling API.

  This should be accessed through get_application_dlls() for new code.
  """
  def __init__(self, dll_directory: ApplicationDllDirectoryProtocol):
    super().__init__(dll_directory)
    if DataEngineApi(dll_directory).dll:
      try:
        self.dll.ModellingPreDataEngineInit()
      except:
        self.log.critical('Fatal: ModellingPreDataEngineInit Not available')
        raise
    self.__feature_map: list[tuple[str, int]] | None = None

  @property
  def _feature_map(self) -> list[tuple[str, int]]:
    """Access a map of feature names to their indices.

    The feature indices are not stable across C API versions, so this
    dictionary ensures the correct indices are returned for a given name.
    """
    if self.__feature_map is None:
      feature_map = []
      feature_count = self.dll.ModellingGetFeatureCount()
      for index in range(feature_count):
        name = self.GetFeatureName(index)
        feature_map.append((name, index))

      self.__feature_map = feature_map
    return self.__feature_map

  def _feature_name_to_index(self, name: str) -> int:
    """Convert a feature name to its index."""
    for feature_name, feature_index in self._feature_map:
      if feature_name == name:
        return feature_index
    raise ApplicationTooOldError.with_default_message(
      f"The {name} feature"
    )

  def _feature_index_to_name(self, index: int) -> str:
    """Convert a feature index to its name."""
    for feature_name, feature_index in self._feature_map:
      if feature_index == index:
        return feature_name
    raise CApiUnknownError(
      f"Invalid feature index: {index}"
    )

  @staticmethod
  def method_prefix():
    return "Modelling"

  @staticmethod
  def dll_name() -> str:
    return "mdf_modelling"

  def capi_functions(self):
    return [
      # Functions changed in version 0.
      # Format:
      # "name" : (return_type, arg_types)
      {"ModellingPreDataEngineInit" : (None, None),
       "ModellingSpatialType" : (T_TypeIndex, None),
       "ModellingStandardContainerType" : (T_TypeIndex, None),
       "ModellingVisualContainerType" : (T_TypeIndex, None),
       "ModellingTopologyType" : (T_TypeIndex, None),
       "ModellingPointSetType" : (T_TypeIndex, None),
       "ModellingEdgeNetworkType" : (T_TypeIndex, None),
       "ModellingEdgeChainType" : (T_TypeIndex, None),
       "ModellingEdgeLoopType" : (T_TypeIndex, None),
       "ModellingText2DType" : (T_TypeIndex, None),
       "ModellingText3DType" : (T_TypeIndex, None),
       "ModellingMarkerType" : (T_TypeIndex, None),
       "ModellingFacetNetworkType" : (T_TypeIndex, None),
       "ModellingCellNetworkType" : (T_TypeIndex, None),
       "ModellingRegularCellNetworkType" : (T_TypeIndex, None),
       "ModellingIrregularCellNetworkType" : (T_TypeIndex, None),
       "ModellingSparseIrregularCellNetworkType" : (T_TypeIndex, None),
       "ModellingSparseRegularCellNetworkType" : (T_TypeIndex, None),
       "ModellingDenseCellNetworkType" : (T_TypeIndex, None),
       "ModellingBlockNetworkType" : (T_TypeIndex, None),
       "ModellingBlockNetworkSubblockedType" : (T_TypeIndex, None),
       "ModellingBlockNetworkHarpType" : (T_TypeIndex, None),
       "ModellingBlockNetworkDenseType" : (T_TypeIndex, None),
       "ModellingBlockNetworkSparseType" : (T_TypeIndex, None),
       "ModellingNumericColourMapType" : (T_TypeIndex, None),
       "ModellingStringColourMapType" : (T_TypeIndex, None),
       "ModellingImageType" : (T_TypeIndex, None),
       "ModellingNewVisualContainer" : (T_ObjectHandle, None),
       "ModellingNewStandardContainer" : (T_ObjectHandle, None),
       "ModellingNewBlockNetworkDense" : (T_ObjectHandle, [ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ]),
       "ModellingNewBlockNetworkSparse" : (T_ObjectHandle, [ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ]),
       "ModellingNewBlockNetworkSubblocked" : (T_ObjectHandle, [ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ]),
       "ModellingNewBlockNetworkHarp" : (T_ObjectHandle, [ctypes.c_double, ctypes.c_double, ctypes.c_uint32, ctypes.c_uint32, ]),
       "ModellingNewIrregularCellNetwork" : (T_ObjectHandle, [ctypes.c_uint64, ctypes.c_uint64, ]),
       "ModellingNewSparseIrregularCellNetwork" : (T_ObjectHandle, [ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(ctypes.c_bool), ]),
       "ModellingNewEdgeNetwork" : (T_ObjectHandle, None),
       "ModellingNewEdgeChain" : (T_ObjectHandle, None),
       "ModellingNewEdgeLoop" : (T_ObjectHandle, None),
       "ModellingNewFacetNetwork" : (T_ObjectHandle, None),
       "ModellingNew2DText" : (T_ObjectHandle, None),
       "ModellingNewMarker" : (T_ObjectHandle, None),
       "ModellingNewPointSet" : (T_ObjectHandle, None),
       "ModellingNewNumericColourMap" : (T_ObjectHandle, None),
       "ModellingNewStringColourMap" : (T_ObjectHandle, None),
       "ModellingNewImage" : (T_ObjectHandle, None),
       "ModellingSetPointCount" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint32, ]),
       "ModellingSetEdgeCount" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint32, ]),
       "ModellingSetFacetCount" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint32, ]),
       "ModellingSetBlockCount" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint32, ]),
       "ModellingAppendPoints" : (ctypes.c_uint32, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint32, ]),
       "ModellingAppendEdges" : (ctypes.c_uint32, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint32, ]),
       "ModellingAppendFacets" : (ctypes.c_uint32, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint32, ]),
       "ModellingRemovePoint" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint32, ]),
       "ModellingRemovePoints" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32, ]),
       "ModellingRemoveEdge" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint32, ]),
       "ModellingRemoveEdges" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32, ]),
       "ModellingRemoveFacet" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint32, ]),
       "ModellingRemoveFacets" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32, ]),
       "ModellingRemoveCell" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint32, ]),
       "ModellingRemoveBlock" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint32, ]),
       "ModellingReconcileChanges" : (None, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingGetDisplayedAttribute" : (ctypes.c_uint32, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ctypes.c_uint32, ]),
       "ModellingGetDisplayedAttributeType" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingSetDisplayedPointAttribute" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, T_ObjectHandle, ]),
       "ModellingSetDisplayedEdgeAttribute" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, T_ObjectHandle, ]),
       "ModellingSetDisplayedFacetAttribute" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, T_ObjectHandle, ]),
       "ModellingPointCoordinatesBeginR" : (ctypes.POINTER(ctypes.c_double), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingPointCoordinatesBeginRW" : (ctypes.POINTER(ctypes.c_double), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingPointToEdgeIndexBeginR" : (ctypes.POINTER(ctypes.c_uint32), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingPointToFacetIndexBeginR" : (ctypes.POINTER(ctypes.c_uint32), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingCellToPointIndexBeginR" : (ctypes.POINTER(ctypes.c_uint32), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingEdgeToPointIndexBeginR" : (ctypes.POINTER(ctypes.c_uint32), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingEdgeToPointIndexBeginRW" : (ctypes.POINTER(ctypes.c_uint32), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingFacetToPointIndexBeginR" : (ctypes.POINTER(ctypes.c_uint32), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingFacetToPointIndexBeginRW" : (ctypes.POINTER(ctypes.c_uint32), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingFacetTo3FacetIndexBeginR" : (ctypes.POINTER(ctypes.c_uint32), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingBlockIndicesBeginR" : (ctypes.POINTER(ctypes.c_uint32), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingBlockIndicesBeginRW" : (ctypes.POINTER(ctypes.c_uint32), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingEdgeCurveOffsetBeginR" : (ctypes.POINTER(ctypes.c_double), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingEdgeCurveOffsetBeginRW" : (ctypes.POINTER(ctypes.c_double), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingPointSelectionBeginR" : (ctypes.POINTER(ctypes.c_bool), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingPointSelectionBeginRW" : (ctypes.POINTER(ctypes.c_bool), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingClearPointSelection" : (None, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingEdgeSelectionBeginR" : (ctypes.POINTER(ctypes.c_bool), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingEdgeSelectionBeginRW" : (ctypes.POINTER(ctypes.c_bool), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingClearEdgeSelection" : (None, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingFacetSelectionBeginR" : (ctypes.POINTER(ctypes.c_bool), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingFacetSelectionBeginRW" : (ctypes.POINTER(ctypes.c_bool), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingClearFacetSelection" : (None, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingBlockSelectionBeginR" : (ctypes.POINTER(ctypes.c_bool), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingBlockSelectionBeginRW" : (ctypes.POINTER(ctypes.c_bool), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingClearBlockSelection" : (None, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingEdgeVisibilityBeginR" : (ctypes.POINTER(ctypes.c_bool), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingEdgeVisibilityBeginRW" : (ctypes.POINTER(ctypes.c_bool), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingClearEdgeVisibility" : (None, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingPointVisibilityBeginR" : (ctypes.POINTER(ctypes.c_bool), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingPointVisibilityBeginRW" : (ctypes.POINTER(ctypes.c_bool), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingClearPointVisibility" : (None, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingBlockVisibilityBeginR" : (ctypes.POINTER(ctypes.c_bool), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingBlockVisibilityBeginRW" : (ctypes.POINTER(ctypes.c_bool), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingClearBlockVisibility" : (None, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingBlockSizesBeginR" : (ctypes.POINTER(ctypes.c_float), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingBlockSizesBeginRW" : (ctypes.POINTER(ctypes.c_float), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingBlockCentroidsBeginR" : (ctypes.POINTER(ctypes.c_double), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingBlockCentroidsBeginRW" : (ctypes.POINTER(ctypes.c_double), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingBlockVolumesBeginR" : (ctypes.POINTER(ctypes.c_double), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingGridToBlockIndicesBeginR" : (ctypes.POINTER(ctypes.c_uint32), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingHarpCentreZBeginR" : (ctypes.POINTER(ctypes.c_double), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingHarpCentreZBeginRW" : (ctypes.POINTER(ctypes.c_double), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingHarpCornerOffsetsTopBeginR" : (ctypes.POINTER(ctypes.c_float), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingHarpCornerOffsetsTopBeginRW" : (ctypes.POINTER(ctypes.c_float), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingHarpCornerOffsetsBottomBeginR" : (ctypes.POINTER(ctypes.c_float), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingHarpCornerOffsetsBottomBeginRW" : (ctypes.POINTER(ctypes.c_float), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingGetDisplayedColourMap" : (T_ObjectHandle, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingUpdateNumericColourMapInterpolated" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8), ]),
       "ModellingUpdateNumericColourMapSolid" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8), ]),
       "ModellingReadNumericColourMap" : (ctypes.c_uint32, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8), ]),
       "ModellingUpdateStringColourMap" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint32, ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8), ]),
       "ModellingReadStringColourMap" : (ctypes.c_uint32, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint32, ctypes.c_char_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8), ]),
       "ModellingPointColourBeginR" : (ctypes.POINTER(ctypes.c_ubyte), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingPointColourBeginRW" : (ctypes.POINTER(ctypes.c_ubyte), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingClearPointColour" : (None, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingSetUniformPointColour" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_void_p, ]),
       "ModellingEdgeColourBeginR" : (ctypes.POINTER(ctypes.c_ubyte), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingEdgeColourBeginRW" : (ctypes.POINTER(ctypes.c_ubyte), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingClearEdgeColour" : (None, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingSetUniformEdgeColour" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_void_p, ]),
       "ModellingFacetColourBeginR" : (ctypes.POINTER(ctypes.c_ubyte), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingFacetColourBeginRW" : (ctypes.POINTER(ctypes.c_ubyte), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingClearFacetColour" : (None, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingSetUniformFacetColour" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_void_p, ]),
       "ModellingSetEdgeNetworkEdgeThickness" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_float, ]),
       "ModellingSetEdgeNetworkStipplePattern" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingSetEdgeNetworkArrowHead" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_bool, ctypes.c_float, ctypes.c_float, ]),
       "ModellingBlockColourBeginR" : (ctypes.POINTER(ctypes.c_ubyte), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingBlockColourBeginRW" : (ctypes.POINTER(ctypes.c_ubyte), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingClearBlockColour" : (None, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingSetUniformBlockColour" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_void_p, ]),
       "ModellingGetEffectiveBlockColour" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint8), ]),
       "ModellingBlockHighlightBeginR" : (ctypes.POINTER(ctypes.c_uint8), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingBlockHighlightBeginRW" : (ctypes.POINTER(ctypes.c_uint8), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingClearBlockHighlight" : (None, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingSetUniformBlockHighlight" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint8, ]),
       "ModellingSetDisplayedBlockAttribute" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, T_ObjectHandle, ]),
       "ModellingListPointAttributeNames" : (ctypes.c_uint64, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ctypes.c_uint64, ]),
       "ModellingListEdgeAttributeNames" : (ctypes.c_uint64, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ctypes.c_uint64, ]),
       "ModellingListFacetAttributeNames" : (ctypes.c_uint64, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ctypes.c_uint64, ]),
       "ModellingListBlockAttributeNames" : (ctypes.c_uint64, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ctypes.c_uint64, ]),
       "ModellingPointAttributeType" : (ctypes.c_uint32, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingEdgeAttributeType" : (ctypes.c_uint32, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingFacetAttributeType" : (ctypes.c_uint32, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingBlockAttributeType" : (ctypes.c_uint32, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingDeletePointAttribute" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingDeleteEdgeAttribute" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingDeleteFacetAttribute" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingDeleteBlockAttribute" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingFacetNetworkSolidUnion" : (T_ObjectHandle, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(T_ReadHandle), ]),
       "ModellingFacetNetworkSolidSubtraction" : (T_ObjectHandle, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(T_ReadHandle), ]),
       "ModellingFacetNetworkSolidIntersection" : (T_ObjectHandle, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(T_ReadHandle), ]),
       "ModellingFacetNetworkClipSolid" : (T_ObjectHandle, [ctypes.POINTER(T_ReadHandle), ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, ]),
       "ModellingPointAttributeBoolBeginR" : (ctypes.POINTER(ctypes.c_bool), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingPointAttributeBoolBeginRW" : (ctypes.POINTER(ctypes.c_bool), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingPointAttributeInt8uBeginR" : (ctypes.POINTER(ctypes.c_uint8), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingPointAttributeInt8uBeginRW" : (ctypes.POINTER(ctypes.c_uint8), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingPointAttributeInt8sBeginR" : (ctypes.POINTER(ctypes.c_int8), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingPointAttributeInt8sBeginRW" : (ctypes.POINTER(ctypes.c_int8), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingPointAttributeInt16uBeginR" : (ctypes.POINTER(ctypes.c_uint16), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingPointAttributeInt16uBeginRW" : (ctypes.POINTER(ctypes.c_uint16), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingPointAttributeInt16sBeginR" : (ctypes.POINTER(ctypes.c_int16), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingPointAttributeInt16sBeginRW" : (ctypes.POINTER(ctypes.c_int16), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingPointAttributeInt32uBeginR" : (ctypes.POINTER(ctypes.c_uint32), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingPointAttributeInt32uBeginRW" : (ctypes.POINTER(ctypes.c_uint32), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingPointAttributeInt32sBeginR" : (ctypes.POINTER(ctypes.c_int32), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingPointAttributeInt32sBeginRW" : (ctypes.POINTER(ctypes.c_int32), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingPointAttributeInt64uBeginR" : (ctypes.POINTER(ctypes.c_uint64), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingPointAttributeInt64uBeginRW" : (ctypes.POINTER(ctypes.c_uint64), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingPointAttributeInt64sBeginR" : (ctypes.POINTER(ctypes.c_int64), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingPointAttributeInt64sBeginRW" : (ctypes.POINTER(ctypes.c_int64), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingPointAttributeFloat32BeginR" : (ctypes.POINTER(ctypes.c_float), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingPointAttributeFloat32BeginRW" : (ctypes.POINTER(ctypes.c_float), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingPointAttributeFloat64BeginR" : (ctypes.POINTER(ctypes.c_double), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingPointAttributeFloat64BeginRW" : (ctypes.POINTER(ctypes.c_double), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingPointAttributeStringBeginR" : (ctypes.c_void_p, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingPointAttributeStringBeginRW" : (ctypes.c_void_p, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingEdgeAttributeBoolBeginR" : (ctypes.POINTER(ctypes.c_bool), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingEdgeAttributeBoolBeginRW" : (ctypes.POINTER(ctypes.c_bool), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingEdgeAttributeInt8uBeginR" : (ctypes.POINTER(ctypes.c_uint8), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingEdgeAttributeInt8uBeginRW" : (ctypes.POINTER(ctypes.c_uint8), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingEdgeAttributeInt8sBeginR" : (ctypes.POINTER(ctypes.c_int8), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingEdgeAttributeInt8sBeginRW" : (ctypes.POINTER(ctypes.c_int8), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingEdgeAttributeInt16uBeginR" : (ctypes.POINTER(ctypes.c_uint16), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingEdgeAttributeInt16uBeginRW" : (ctypes.POINTER(ctypes.c_uint16), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingEdgeAttributeInt16sBeginR" : (ctypes.POINTER(ctypes.c_int16), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingEdgeAttributeInt16sBeginRW" : (ctypes.POINTER(ctypes.c_int16), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingEdgeAttributeInt32uBeginR" : (ctypes.POINTER(ctypes.c_uint32), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingEdgeAttributeInt32uBeginRW" : (ctypes.POINTER(ctypes.c_uint32), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingEdgeAttributeInt32sBeginR" : (ctypes.POINTER(ctypes.c_int32), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingEdgeAttributeInt32sBeginRW" : (ctypes.POINTER(ctypes.c_int32), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingEdgeAttributeInt64uBeginR" : (ctypes.POINTER(ctypes.c_uint64), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingEdgeAttributeInt64uBeginRW" : (ctypes.POINTER(ctypes.c_uint64), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingEdgeAttributeInt64sBeginR" : (ctypes.POINTER(ctypes.c_int64), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingEdgeAttributeInt64sBeginRW" : (ctypes.POINTER(ctypes.c_int64), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingEdgeAttributeFloat32BeginR" : (ctypes.POINTER(ctypes.c_float), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingEdgeAttributeFloat32BeginRW" : (ctypes.POINTER(ctypes.c_float), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingEdgeAttributeFloat64BeginR" : (ctypes.POINTER(ctypes.c_double), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingEdgeAttributeFloat64BeginRW" : (ctypes.POINTER(ctypes.c_double), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingEdgeAttributeStringBeginR" : (ctypes.c_void_p, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingEdgeAttributeStringBeginRW" : (ctypes.c_void_p, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingFacetAttributeBoolBeginR" : (ctypes.POINTER(ctypes.c_bool), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingFacetAttributeBoolBeginRW" : (ctypes.POINTER(ctypes.c_bool), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingFacetAttributeInt8uBeginR" : (ctypes.POINTER(ctypes.c_uint8), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingFacetAttributeInt8uBeginRW" : (ctypes.POINTER(ctypes.c_uint8), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingFacetAttributeInt8sBeginR" : (ctypes.POINTER(ctypes.c_int8), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingFacetAttributeInt8sBeginRW" : (ctypes.POINTER(ctypes.c_int8), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingFacetAttributeInt16uBeginR" : (ctypes.POINTER(ctypes.c_uint16), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingFacetAttributeInt16uBeginRW" : (ctypes.POINTER(ctypes.c_uint16), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingFacetAttributeInt16sBeginR" : (ctypes.POINTER(ctypes.c_int16), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingFacetAttributeInt16sBeginRW" : (ctypes.POINTER(ctypes.c_int16), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingFacetAttributeInt32uBeginR" : (ctypes.POINTER(ctypes.c_uint32), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingFacetAttributeInt32uBeginRW" : (ctypes.POINTER(ctypes.c_uint32), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingFacetAttributeInt32sBeginR" : (ctypes.POINTER(ctypes.c_int32), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingFacetAttributeInt32sBeginRW" : (ctypes.POINTER(ctypes.c_int32), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingFacetAttributeInt64uBeginR" : (ctypes.POINTER(ctypes.c_uint64), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingFacetAttributeInt64uBeginRW" : (ctypes.POINTER(ctypes.c_uint64), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingFacetAttributeInt64sBeginR" : (ctypes.POINTER(ctypes.c_int64), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingFacetAttributeInt64sBeginRW" : (ctypes.POINTER(ctypes.c_int64), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingFacetAttributeFloat32BeginR" : (ctypes.POINTER(ctypes.c_float), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingFacetAttributeFloat32BeginRW" : (ctypes.POINTER(ctypes.c_float), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingFacetAttributeFloat64BeginR" : (ctypes.POINTER(ctypes.c_double), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingFacetAttributeFloat64BeginRW" : (ctypes.POINTER(ctypes.c_double), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingFacetAttributeStringBeginR" : (ctypes.c_void_p, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingFacetAttributeStringBeginRW" : (ctypes.c_void_p, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingBlockAttributeBoolBeginR" : (ctypes.POINTER(ctypes.c_bool), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingBlockAttributeBoolBeginRW" : (ctypes.POINTER(ctypes.c_bool), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingBlockAttributeInt8uBeginR" : (ctypes.POINTER(ctypes.c_uint8), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingBlockAttributeInt8uBeginRW" : (ctypes.POINTER(ctypes.c_uint8), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingBlockAttributeInt8sBeginR" : (ctypes.POINTER(ctypes.c_int8), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingBlockAttributeInt8sBeginRW" : (ctypes.POINTER(ctypes.c_int8), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingBlockAttributeInt16uBeginR" : (ctypes.POINTER(ctypes.c_uint16), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingBlockAttributeInt16uBeginRW" : (ctypes.POINTER(ctypes.c_uint16), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingBlockAttributeInt16sBeginR" : (ctypes.POINTER(ctypes.c_int16), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingBlockAttributeInt16sBeginRW" : (ctypes.POINTER(ctypes.c_int16), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingBlockAttributeInt32uBeginR" : (ctypes.POINTER(ctypes.c_uint32), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingBlockAttributeInt32uBeginRW" : (ctypes.POINTER(ctypes.c_uint32), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingBlockAttributeInt32sBeginR" : (ctypes.POINTER(ctypes.c_int32), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingBlockAttributeInt32sBeginRW" : (ctypes.POINTER(ctypes.c_int32), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingBlockAttributeInt64uBeginR" : (ctypes.POINTER(ctypes.c_uint64), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingBlockAttributeInt64uBeginRW" : (ctypes.POINTER(ctypes.c_uint64), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingBlockAttributeInt64sBeginR" : (ctypes.POINTER(ctypes.c_int64), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingBlockAttributeInt64sBeginRW" : (ctypes.POINTER(ctypes.c_int64), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingBlockAttributeFloat32BeginR" : (ctypes.POINTER(ctypes.c_float), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingBlockAttributeFloat32BeginRW" : (ctypes.POINTER(ctypes.c_float), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingBlockAttributeFloat64BeginR" : (ctypes.POINTER(ctypes.c_double), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingBlockAttributeFloat64BeginRW" : (ctypes.POINTER(ctypes.c_double), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingBlockAttributeStringBeginR" : (ctypes.c_void_p, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingBlockAttributeStringBeginRW" : (ctypes.c_void_p, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingAttributeGetString" : (ctypes.c_uint32, [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_char_p, ctypes.c_uint32, ]),
       "ModellingAttributeSetString" : (None, [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_char_p, ctypes.c_uint32, ]),
       "ModellingSetBlockTransform" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, ]),
       "ModellingReadBlockTransform" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ]),
       "ModellingGetAnnotationPosition" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_double), ]),
       "ModellingSetAnnotationPosition" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_double, ctypes.c_double, ctypes.c_double, ]),
       "ModellingGetAnnotationText" : (ctypes.c_uint64, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ctypes.c_uint64, ]),
       "ModellingSetAnnotationText" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingGetAnnotationSize" : (ctypes.c_double, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingSetAnnotationSize" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_double, ]),
       "ModellingGetAnnotationTextColour" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_void_p, ]),
       "ModellingSetAnnotationTextColour" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_void_p, ]),
       "ModellingGetMarkerRotation" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_double), ]),
       "ModellingSetMarkerRotation" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, ]),
       "ModellingGetMarkerColour" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_void_p, ]),
       "ModellingSetMarkerColour" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_void_p, ]),
       "ModellingGetMarkerStyle" : (ctypes.c_int32, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingSetMarkerStyle" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_int32, ]),
       "ModellingSetMarkerGeometry" : (None, [ctypes.POINTER(T_ReadHandle), T_ObjectHandle, ]),
       "ModellingGetMarkerGeometry" : (T_ObjectHandle, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingSetMarkerSprite" : (None, [ctypes.POINTER(T_ReadHandle), T_ObjectHandle, ]),
       "ModellingGetMarkerSprite" : (T_ObjectHandle, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingSetImageData" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p, ]),
       "ModellingReadPointCount" : (ctypes.c_uint32, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingReadEdgeCount" : (ctypes.c_uint32, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingReadFacetCount" : (ctypes.c_uint32, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingReadBlockCount" : (ctypes.c_uint32, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingReadCellCount" : (ctypes.c_uint32, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingReadBlockDimensions" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_uint32), ]),
       "ModellingReadExtent" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_double), ]),
       "ModellingReadBlockSize" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_double), ]),
       "ModellingProcessObjectSelectionChanges" : (None, [T_MessageHandle, ]),
       "ModellingProcessPrimitiveSelectionChanges" : (None, [T_MessageHandle, ]),
       "ModellingGetFeatureCount" : (ctypes.c_uint32, None),
       "ModellingGetFeatureName" : (ctypes.c_uint32, [ctypes.c_uint32, ctypes.c_char_p, ctypes.c_uint32, ]),
       "ModellingGetDisplayedFeature" : (ctypes.c_uint32, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingCanApplyFeature" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint32, ]),
       "ModellingSetDisplayedFeature" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint32, ]),},
      # Functions changed in version 1.
      {"ModellingCApiVersion" : (ctypes.c_uint32, None),
       "ModellingCApiMinorVersion" : (ctypes.c_uint32, None),
       "ModellingNew3DText" : (T_ObjectHandle, None),
       "ModellingReadCellDimensions" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32), ]),
       "ModellingCellToPointIndexBeginR" : (ctypes.POINTER(ctypes.c_uint32), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingCellSelectionBeginR" : (ctypes.POINTER(ctypes.c_bool), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingCellSelectionBeginRW" : (ctypes.POINTER(ctypes.c_bool), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingCellVisibilityBeginR" : (ctypes.POINTER(ctypes.c_bool), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingCellVisibilityBeginRW" : (ctypes.POINTER(ctypes.c_bool), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingCellColourBeginR" : (ctypes.POINTER(ctypes.c_ubyte), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingCellColourBeginRW" : (ctypes.POINTER(ctypes.c_ubyte), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingSetDisplayedCellAttribute" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, T_ObjectHandle, ]),
       "ModellingListCellAttributeNames" : (ctypes.c_uint64, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ctypes.c_uint64, ]),
       "ModellingCellAttributeType" : (ctypes.c_uint32, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingDeleteCellAttribute" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingCellAttributeBoolBeginR" : (ctypes.POINTER(ctypes.c_bool), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingCellAttributeBoolBeginRW" : (ctypes.POINTER(ctypes.c_bool), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingCellAttributeInt8uBeginR" : (ctypes.POINTER(ctypes.c_uint8), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingCellAttributeInt8uBeginRW" : (ctypes.POINTER(ctypes.c_uint8), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingCellAttributeInt8sBeginR" : (ctypes.POINTER(ctypes.c_int8), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingCellAttributeInt8sBeginRW" : (ctypes.POINTER(ctypes.c_int8), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingCellAttributeInt16uBeginR" : (ctypes.POINTER(ctypes.c_uint16), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingCellAttributeInt16uBeginRW" : (ctypes.POINTER(ctypes.c_uint16), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingCellAttributeInt16sBeginR" : (ctypes.POINTER(ctypes.c_int16), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingCellAttributeInt16sBeginRW" : (ctypes.POINTER(ctypes.c_int16), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingCellAttributeInt32uBeginR" : (ctypes.POINTER(ctypes.c_uint32), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingCellAttributeInt32uBeginRW" : (ctypes.POINTER(ctypes.c_uint32), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingCellAttributeInt32sBeginR" : (ctypes.POINTER(ctypes.c_int32), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingCellAttributeInt32sBeginRW" : (ctypes.POINTER(ctypes.c_int32), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingCellAttributeInt64uBeginR" : (ctypes.POINTER(ctypes.c_uint64), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingCellAttributeInt64uBeginRW" : (ctypes.POINTER(ctypes.c_uint64), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingCellAttributeInt64sBeginR" : (ctypes.POINTER(ctypes.c_int64), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingCellAttributeInt64sBeginRW" : (ctypes.POINTER(ctypes.c_int64), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingCellAttributeFloat32BeginR" : (ctypes.POINTER(ctypes.c_float), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingCellAttributeFloat32BeginRW" : (ctypes.POINTER(ctypes.c_float), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingCellAttributeFloat64BeginR" : (ctypes.POINTER(ctypes.c_double), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingCellAttributeFloat64BeginRW" : (ctypes.POINTER(ctypes.c_double), [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingCellAttributeStringBeginR" : (ctypes.c_void_p, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingCellAttributeStringBeginRW" : (ctypes.c_void_p, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "ModellingGetTextVerticalAlignment" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingSetTextVerticalAlignment" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint8, ]),
       "ModellingGetTextHorizontalAlignment" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingSetTextHorizontalAlignment" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint8, ]),
       "ModellingGetText3DDirection" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ]),
       "ModellingSetText3DDirection" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.c_double, ctypes.c_double, ctypes.c_double, ]),
       "ModellingGetText3DUpDirection" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ]),
       "ModellingSetText3DUpDirection" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.c_double, ctypes.c_double, ctypes.c_double, ]),
       "ModellingGetText3DIsAlwaysVisible" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingSetText3DIsAlwaysVisible" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.c_bool, ]),
       "ModellingGetText3DIsAlwaysViewerFacing" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingSetText3DIsAlwaysViewerFacing" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.c_bool, ]),
       "ModellingGetText3DIsCameraFacing" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingSetText3DIsCameraFacing" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.c_bool, ]),
       "ModellingGetTextFontStyle" : (ctypes.c_uint16, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingSetTextFontStyle" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint16, ]),
       "ModellingGetAssociatedRasterCount" : (ctypes.c_uint32, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingGetAssociatedRasters" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(T_ObjectHandle), ]),
       "ModellingAssociateRaster" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), T_ObjectHandle, ctypes.c_uint8, ctypes.POINTER(ctypes.c_uint8), ]),
       "ModellingDissociateRaster" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), T_ObjectHandle, ]),
       "ModellingRasterSetControlTwoPoint" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ctypes.POINTER(ctypes.c_double), ]),
       "ModellingGetRasterRegistrationType" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_uint8), ]),
       "ModellingRasterGetRegistration" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_double), ]),
       "ModellingTangentPlaneType" : (T_TypeIndex, None),
       "ModellingNewTangentPlane" : (T_ObjectHandle, None),
       "ModellingSetTangentPlaneFromPoints" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ]),
       "ModellingTangentPlaneGetOrientation" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ]),
       "ModellingTangentPlaneSetOrientation" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.c_double, ctypes.c_double, ]),
       "ModellingTangentPlaneGetLength" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_double), ]),
       "ModellingTangentPlaneSetLength" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.c_double, ]),
       "ModellingTangentPlaneGetArea" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_double), ]),
       "ModellingTangentPlaneGetLocation" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_double), ]),
       "ModellingTangentPlaneSetLocation" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_double), ]),
       "ModellingGetCoordinateSystem" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ]),
       "ModellingSetCoordinateSystem" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ]),

       # Functions added in 1.3 (But some of them are mixed in above)
       "ModellingRibbonChainType" : (T_TypeIndex, None),
       "ModellingRibbonLoopType" : (T_TypeIndex, None),
       "ModellingEdgeLoopAreaType" : (T_TypeIndex, None),

       # Functions added in version 1.3.
       "ModellingEllipsoidType" : (T_TypeIndex, None),

       # Functions added in version 1.4.
       "ModellingGetMarkerHeight" : (ctypes.c_double, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingSetMarkerHeight" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_double, ]),

        # Functions added in version 1.5.
       "ModellingErrorCode" : (ctypes.c_uint32, None),
       "ModellingErrorMessage" : (ctypes.c_char_p, None),

       # Functions added in version 1.8.
       "ModellingTangentPlaneGetPolarity" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_int32), ]),
       "ModellingTangentPlaneSetPolarity" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.c_int32, ]),
       "ModellingGetNaturalColour" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_uint8), ]),
       "ModellingSetNaturalColour" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_uint8), ]),
       "ModellingTopologyHasFrontColour" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingTopologyHasBackColour" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingTopologySetHasFrontColour" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.c_bool, ]),
       "ModellingTopologySetHasBackColour" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.c_bool, ]),
       "ModellingNewRibbonChain" : (T_ObjectHandle, None),
       "ModellingNewRibbonLoop" : (T_ObjectHandle, None),
       "ModellingPointWidthsBeginR" : (ctypes.POINTER(ctypes.c_double), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingPointWidthsBeginRW" : (ctypes.POINTER(ctypes.c_double), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingPointAnglesBeginR" : (ctypes.POINTER(ctypes.c_double), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingPointAnglesBeginRW" : (ctypes.POINTER(ctypes.c_double), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingPointNormalsBeginR" : (ctypes.POINTER(ctypes.c_double), [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingStringColourMapGetCaseSensitive" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingStringColourMapSetCaseSensitive" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.c_bool, ]),
       "ModellingNewEllipsoid" : (T_ObjectHandle, None),
       "ModellingGetEllipsoidA" : (ctypes.c_double, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingGetEllipsoidB" : (ctypes.c_double, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingGetEllipsoidC" : (ctypes.c_double, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingSetEllipsoidABC" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.c_double, ctypes.c_double, ctypes.c_double, ]),
       "ModellingGetEllipsoidCentre" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_double), ]),
       "ModellingSetEllipsoidCentre" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.c_double, ctypes.c_double, ctypes.c_double, ]),
       "ModellingGetEllipsoidRotation" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_double), ]),
       "ModellingSetEllipsoidRotation" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, ]),

       # Functions added in version 1.10:
       "ModellingNewEdgeLoopArea" : (T_ObjectHandle, None),
       "ModellingSurfacePointToRasterCoordinateOverrideR" : (ctypes.POINTER(ctypes.c_float), [ctypes.POINTER(T_ReadHandle), ctypes.c_uint8 ]),
       "ModellingSurfacePointToRasterCoordinateOverrideRW" : (ctypes.POINTER(ctypes.c_float), [ctypes.POINTER(T_ReadHandle), ctypes.c_uint8 ]),
       "ModellingClearCoordinateSystem" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingColourMapGetColoursForValues" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint32, ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_uint8), ]),

       # Functions added in version 1.11:
       "ModellingGetEdgeNetworkEdgeThickness" : (ctypes.c_float, [ctypes.POINTER(T_ReadHandle), ]),
       "ModellingRemoveColourMap" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ]),
       },
    ]

  # Manually generated wrapper functions.
  def New3DText(self):
    """Wrapper for making a new 3d Text object."""
    raise_if_version_too_old(
      "Creating 3D Text",
      current_version=self.version,
      required_version=(1, 0))
    return self.dll.ModellingNew3DText()

  def ReadCellDimensions(self, lock):
    """Wrapper for reading the dimensions of a cell network"""
    raise_if_version_too_old(
      "Reading dimensions of a cell network",
      current_version=self.version,
      required_version=(1, 1))

    major_dimension_count = ctypes.c_uint32()
    minor_dimension_count = ctypes.c_uint32()
    self.dll.ModellingReadCellDimensions(lock,
                                         ctypes.byref(major_dimension_count),
                                         ctypes.byref(minor_dimension_count))
    return (major_dimension_count.value, minor_dimension_count.value)

  def ReadCellPointCount(self, lock: T_ReadHandle) -> int:
    """Read the cell point count for the object.

    Parameters
    ----------
    lock
      Lock on the object on which the cell point count will be read.

    Returns
    -------
    int
      The number of points in the underlying grid.

    Notes
    -----
    This function does not correspond to a function in the C API.
    Rather it is a wrapper over ModellingReadCellDimensions so that it returns
    a single integer.
    """
    raise_if_version_too_old(
      "Reading dimensions of a cell network",
      current_version=self.version,
      required_version=(1, 1))

    major_dimension_count = ctypes.c_uint32()
    minor_dimension_count = ctypes.c_uint32()
    self.dll.ModellingReadCellDimensions(lock,
                                         ctypes.byref(major_dimension_count),
                                         ctypes.byref(minor_dimension_count))
    return major_dimension_count.value * minor_dimension_count.value

  def GetTextVerticalAlignment(self, lock):
    """Wrapper for getting vertical alignment of text."""
    raise_if_version_too_old(
      "Reading dimensions of a cell network",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingGetTextVerticalAlignment(lock)

  def SetTextVerticalAlignment(self, lock, vertical_alignment):
    """Wrapper for setting text vertical alignment.

    Raises
    ------
    CApiUnknownError
      If an error occurs.

    """
    raise_if_version_too_old(
      "Setting vertical alignment of text.",
      current_version=self.version,
      required_version=(1, 2))

    result = self.dll.ModellingSetTextVerticalAlignment(lock,
                                                        vertical_alignment)
    if result != 0:
      message = "Failed to set vertical alignment."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def GetTextHorizontalAlignment(self, lock):
    """Wrapper for getting horizontal alignment."""
    raise_if_version_too_old(
      "Reading horizontal alignment of text",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingGetTextHorizontalAlignment(lock)

  def SetTextHorizontalAlignment(self, lock, horizontal_alignment):
    """Wrapper for setting horizontal alignment.

    Raises
    ------
    CApiUnknownError
      If an error occurs.

    """
    raise_if_version_too_old(
      "Setting horizontal alignment of text",
      current_version=self.version,
      required_version=(1, 2))

    result = self.dll.ModellingSetTextHorizontalAlignment(lock,
                                                          horizontal_alignment)
    if result != 0:
      message = "Failed to set horizontal alignment."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def CellToPointIndexBeginR(self, lock):
    """Wrapper for getting read-only cell to point index."""
    raise_if_version_too_old(
      "Getting cells",
      current_version=self.version,
      required_version=(1, 3))
    return self.dll.ModellingCellToPointIndexBeginR(lock)

  def CellSelectionBeginR(self, lock):
    """Wrapper for getting read-only cell selection."""
    raise_if_version_too_old(
      "Reading Cell Selection",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingCellSelectionBeginR(lock)

  def CellSelectionBeginRW(self, lock):
    """Wrapper for getting read-only cell selection."""
    raise_if_version_too_old(
      "Editing Cell Selection",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingCellSelectionBeginRW(lock)

  def CellVisibilityBeginR(self, lock):
    """Wrapper for getting read-only cell Visibility."""
    raise_if_version_too_old(
      "Reading Cell Visibility",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingCellVisibilityBeginR(lock)

  def CellVisibilityBeginRW(self, lock):
    """Wrapper for getting read-only cell visibility."""
    raise_if_version_too_old(
      "Editing Cell Visibility",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingCellVisibilityBeginRW(lock)

  def CellColourBeginR(self, lock):
    """Wrapper for getting read-only cell colour."""
    raise_if_version_too_old(
      "Reading Cell Colour",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingCellColourBeginR(lock)

  def CellColourBeginRW(self, lock):
    """Wrapper for getting read-only cell colour."""
    raise_if_version_too_old(
      "Editing Cell Colour",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingCellColourBeginRW(lock)

  def SetDisplayedCellAttribute(self, lock, attribute_name, colour_map_id):
    """Wrapper for setting displayed cell attribute."""
    raise_if_version_too_old(
      "Assigning a colour map to a cell attribute",
      current_version=self.version,
      required_version=(1, 2))
    self.dll.ModellingSetDisplayedCellAttribute(lock,
                                                attribute_name,
                                                colour_map_id)

  def ListCellAttributeNames(self, lock, name_buffer, name_buffer_size):
    """Wrapper for listing the cell attribute names"""
    raise_if_version_too_old(
      "Listing cell attributes",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingListCellAttributeNames(lock,
                                                    name_buffer,
                                                    name_buffer_size)

  def CellAttributeType(self, lock, attribute_type):
    """Wrapper for getting the type of a cell attribute."""
    raise_if_version_too_old(
      "Getting cell attribute type",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingCellAttributeType(lock, attribute_type)

  def DeleteCellAttribute(self, lock, attribute_name):
    """Wrapper for deleting a cell attribute by name."""
    raise_if_version_too_old(
      "Deleting cell attributes",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingDeleteCellAttribute(lock, attribute_name)

  def CellAttributeBoolBeginR(self, lock, attribute_name):
    """Get the begin pointer for a boolean cell attribute (read-only)."""
    raise_if_version_too_old(
      "Reading boolean cell attributes",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingCellAttributeBoolBeginR(lock, attribute_name)

  def CellAttributeBoolBeginRW(self, lock, attribute_name):
    """Get the begin pointer for a boolean cell attribute (read/write)."""
    raise_if_version_too_old(
      "Writing boolean cell attributes",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingCellAttributeBoolBeginRW(lock, attribute_name)

  def CellAttributeInt8uBeginR(self, lock, attribute_name):
    """Get the begin pointer for a Tint8u cell attribute (read-only)."""
    raise_if_version_too_old(
      "Reading unsigned 8 bit integer cell attributes",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingCellAttributeInt8uBeginR(lock, attribute_name)

  def CellAttributeInt8uBeginRW(self, lock, attribute_name):
    """Get the begin pointer for a Tint8u cell attribute (read/write)."""
    raise_if_version_too_old(
      "Writing unsigned 8 bit integer cell attributes",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingCellAttributeInt8uBeginRW(lock, attribute_name)

  def CellAttributeInt8sBeginR(self, lock, attribute_name):
    """Get the begin pointer for a Tint8s cell attribute (read-only)."""
    raise_if_version_too_old(
      "Reading signed 8 bit integer cell attributes",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingCellAttributeInt8sBeginR(lock, attribute_name)

  def CellAttributeInt8sBeginRW(self, lock, attribute_name):
    """Get the begin pointer for a Tint8s cell attribute (read/write)."""
    raise_if_version_too_old(
      "Writing signed 8 bit integer cell attributes",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingCellAttributeInt8sBeginRW(lock, attribute_name)

  def CellAttributeInt16uBeginR(self, lock, attribute_name):
    """Get the begin pointer for a Tint16u cell attribute (read-only)."""
    raise_if_version_too_old(
      "Reading unsigned 16 bit integer cell attributes",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingCellAttributeInt16uBeginR(lock, attribute_name)

  def CellAttributeInt16uBeginRW(self, lock, attribute_name):
    """Get the begin pointer for a Tint16u cell attribute (read/write)."""
    raise_if_version_too_old(
      "Writing unsigned 16 bit integer cell attributes",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingCellAttributeInt16uBeginRW(lock, attribute_name)

  def CellAttributeInt16sBeginR(self, lock, attribute_name):
    """Get the begin pointer for a Tint16s cell attribute (read-only)."""
    raise_if_version_too_old(
      "Reading signed 16 bit integer cell attributes",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingCellAttributeInt16sBeginR(lock, attribute_name)

  def CellAttributeInt16sBeginRW(self, lock, attribute_name):
    """Get the begin pointer for a Tint16s cell attribute (read/write)."""
    raise_if_version_too_old(
      "Writing signed 16 bit integer cell attributes",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingCellAttributeInt16sBeginRW(lock, attribute_name)

  def CellAttributeInt32uBeginR(self, lock, attribute_name):
    """Get the begin pointer for a Tint32u cell attribute (read-only)."""
    raise_if_version_too_old(
      "Reading unsigned 32 bit integer cell attributes",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingCellAttributeInt32uBeginR(lock, attribute_name)

  def CellAttributeInt32uBeginRW(self, lock, attribute_name):
    """Get the begin pointer for a Tint32u cell attribute (read/write)."""
    raise_if_version_too_old(
      "Writing unsigned 32 bit integer cell attributes",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingCellAttributeInt32uBeginRW(lock, attribute_name)

  def CellAttributeInt32sBeginR(self, lock, attribute_name):
    """Get the begin pointer for a Tint32s cell attribute (read-only)."""
    raise_if_version_too_old(
      "Reading signed 32 bit integer cell attributes",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingCellAttributeInt32sBeginR(lock, attribute_name)

  def CellAttributeInt32sBeginRW(self, lock, attribute_name):
    """Get the begin pointer for a Tint32s cell attribute (read/write)."""
    raise_if_version_too_old(
      "Writing signed 32 bit integer cell attributes",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingCellAttributeInt32sBeginRW(lock, attribute_name)

  def CellAttributeInt64uBeginR(self, lock, attribute_name):
    """Get the begin pointer for a Tint64u cell attribute (read-only)."""
    raise_if_version_too_old(
      "Reading unsigned 64 bit integer cell attributes",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingCellAttributeInt64uBeginR(lock, attribute_name)

  def CellAttributeInt64uBeginRW(self, lock, attribute_name):
    """Get the begin pointer for a Tint64u cell attribute (read/write)."""
    raise_if_version_too_old(
      "Writing unsigned 64 bit integer cell attributes",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingCellAttributeInt64uBeginRW(lock, attribute_name)

  def CellAttributeInt64sBeginR(self, lock, attribute_name):
    """Get the begin pointer for a Tint64s cell attribute (read-only)."""
    raise_if_version_too_old(
      "Reading signed 64 bit integer cell attributes",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingCellAttributeInt64sBeginR(lock, attribute_name)

  def CellAttributeInt64sBeginRW(self, lock, attribute_name):
    """Get the begin pointer for a Tint64s cell attribute (read/write)."""
    raise_if_version_too_old(
      "Writing signed 64 bit integer cell attributes",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingCellAttributeInt64sBeginRW(lock, attribute_name)

  def CellAttributeFloat32BeginR(self, lock, attribute_name):
    """Get the begin pointer for a 32 bit float cell attribute (read-only)."""
    raise_if_version_too_old(
      "Reading 32 bit float cell attributes",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingCellAttributeFloat32BeginR(lock, attribute_name)

  def CellAttributeFloat32BeginRW(self, lock, attribute_name):
    """Get the begin pointer for a 32 bit float cell attribute (read/write)."""
    raise_if_version_too_old(
      "Writing 32 bit float cell attributes",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingCellAttributeFloat32BeginRW(lock, attribute_name)

  def CellAttributeFloat64BeginR(self, lock, attribute_name):
    """Get the begin pointer for a 64 bit float cell attribute (read-only)."""
    raise_if_version_too_old(
      "Reading 64 bit float cell attributes",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingCellAttributeFloat64BeginR(lock, attribute_name)

  def CellAttributeFloat64BeginRW(self, lock, attribute_name):
    """Get the begin pointer for a 64 bit float cell attribute (read/write)."""
    raise_if_version_too_old(
      "Writing 64 bit float cell attributes",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingCellAttributeFloat64BeginRW(lock, attribute_name)

  def CellAttributeStringBeginR(self, lock, attribute_name):
    """Get the begin pointer for a string cell attribute (read-only)."""
    raise_if_version_too_old(
      "Reading string cell attributes",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingCellAttributeStringBeginR(lock, attribute_name)

  def CellAttributeStringBeginRW(self, lock, attribute_name):
    """Get the begin pointer for a string cell attribute (read/write)."""
    raise_if_version_too_old(
      "Writing string cell attributes",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingCellAttributeStringBeginRW(lock, attribute_name)

  def GetText3DDirection(self, lock):
    """Returns the direction of the 3D text.

    Parameters
    ----------
    lock : lock
      Lock on the Text3D to get the direction of.

    Returns
    -------
    list
      List representing the direction of the Text3D.

    Raises
    ------
    CApiInvalidLockError
      If lock is not Text3D.
    CApiUnknownError
      If an error occurs.

    """
    raise_if_version_too_old(
      "Getting Text3D direction",
      current_version=self.version,
      required_version=(1, 2))
    x = ctypes.c_double()
    y = ctypes.c_double()
    z = ctypes.c_double()
    result = self.dll.ModellingGetText3DDirection(lock,
                                                  ctypes.byref(x),
                                                  ctypes.byref(y),
                                                  ctypes.byref(z))
    if result != 0:
      message = "Failed to get 3D text direction."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

    return [x.value, y.value, z.value]

  def SetText3DDirection(self, lock, x, y, z):
    """Sets the direction of the 3D text.

    Parameters
    ----------
    lock : lock
      Lock on the Text3D on which the direction should be set.
    x : float
      X component of the direction.
    y : float
      Y component of the direction.
    z : float
      Z component of the direction.

    Raises
    ------
    CApiUnknownError
      If an error occurs.

    """
    raise_if_version_too_old(
      "Setting Text3D direction",
      current_version=self.version,
      required_version=(1, 2))
    result = self.dll.ModellingSetText3DDirection(lock, x, y, z)

    if result != 0:
      message = "Failed to set direction of 3D text."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def GetText3DUpDirection(self, lock):
    """Returns the up direction of the 3D text.

    Parameters
    ----------
    lock : lock
      Lock on the Text3D to get the up direction of.

    Returns
    -------
    list
      List representing the up direction of the Text3D.

    Raises
    ------
    CApiUnknownError
      If an error occurs.

    """
    raise_if_version_too_old(
      "Getting Text3D up direction",
      current_version=self.version,
      required_version=(1, 2))
    x = ctypes.c_double()
    y = ctypes.c_double()
    z = ctypes.c_double()
    result = self.dll.ModellingGetText3DUpDirection(lock,
                                                    ctypes.byref(x),
                                                    ctypes.byref(y),
                                                    ctypes.byref(z))
    if result != 0:
      message = "Failed to get up direction of 3D text."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

    return [x.value, y.value, z.value]

  def SetText3DUpDirection(self, lock, x, y, z):
    """Sets the up direction of the 3D text.

    Parameters
    ----------
    lock : lock
      Lock on the Text3D on which the up direction should be set.
    x : float
      X component of the up direction.
    y : float
      Y component of the up direction.
    z : float
      Z component of the up direction.

    Raises
    ------
    CApiUnknownError
      If an error occurs.

    """
    raise_if_version_too_old(
      "Setting Text3D up direction",
      current_version=self.version,
      required_version=(1, 2))
    result = self.dll.ModellingSetText3DUpDirection(lock, x, y, z)

    if result != 0:
      message = "Failed to set up direction of 3D text."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def GetText3DIsAlwaysVisible(self, lock):
    """Returns if the 3D text is always visible.

    Parameters
    ----------
    lock : lock
      Lock on the Text3D whose visibility should be returned.

    Returns
    -------
    bool
      If the text is always visible.

    """
    raise_if_version_too_old(
      "Getting if Text3D is always visible",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingGetText3DIsAlwaysVisible(lock)

  def SetText3DIsAlwaysVisible(self, lock, always_visible):
    """Sets if 3D text is always visible.

    Parameters
    ----------
    lock : lock
      Lock on the Text3D whose visibility should be set.
    always_visible : bool
      Value to set to always visible.

    Raises
    ------
    CAPIUnknownError
      If an error occurs.

    """
    raise_if_version_too_old(
      "Setting if Text3D is always visible",
      current_version=self.version,
      required_version=(1, 2))
    result = self.dll.ModellingSetText3DIsAlwaysVisible(lock, always_visible)

    if result != 0:
      message = "Failed to set always visible of 3D text."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def GetText3DIsAlwaysViewerFacing(self, lock):
    """Returns if the 3D text is viewer facing.

    Parameters
    ----------
    lock : lock
      Lock on the 3D text to query if it is viewer facing.

    Returns
    -------
    bool
      If the 3D text is viewer facing.

    """
    raise_if_version_too_old(
      "Getting if Text3D is always viewer facing",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingGetText3DIsAlwaysViewerFacing(lock)

  def SetText3DIsAlwaysViewerFacing(self, lock, always_viewer_facing):
    """Sets if the 3D text is always viewer facing.

    Parameters
    ----------
    lock : lock
      Lock on the 3D text to set if it is viewer facing.
    always_viewer_facing : bool
      Value to set to always viewer facing.

    Raises
    ------
    CAPIUnknownError
      If an error occurs.

    """
    raise_if_version_too_old(
      "Setting if Text3D is always viewer facing",
      current_version=self.version,
      required_version=(1, 2))
    result = self.dll.ModellingSetText3DIsAlwaysViewerFacing(
      lock,
      always_viewer_facing)

    if result != 0:
      message = "Failed to set always viewer facing of 3D text."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def GetText3DIsCameraFacing(self, lock):
    """Returns if the 3D text is camera facing.

    Parameters
    ----------
    lock : lock
      Lock on the 3D text to query if it is camera facing.

    Returns
    -------
    bool
      If the 3D text is camera facing.

    """
    raise_if_version_too_old(
      "Getting if Text3D is camera facing",
      current_version=self.version,
      required_version=(1, 2))
    return self.dll.ModellingGetText3DIsCameraFacing(lock)

  def SetText3DIsCameraFacing(self, lock, camera_facing):
    """Sets if 3D text is always camera facing.

    Parameters
    ----------
    lock : lock
      Lock on the 3D text on which to set the value of camera facing.
    camera_facing : bool
      Value to set to camera facing.

    Raises
    ------
    CAPIUnknownError
      If an error occurs.

    """
    raise_if_version_too_old(
      "Setting if Text3D is camera facing",
      current_version=self.version,
      required_version=(1, 2))
    result = self.dll.ModellingSetText3DIsCameraFacing(lock, camera_facing)

    if result != 0:
      message = "Failed to set camera facing of 3D text."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def GetTextFontStyle(self, lock):
    """Returns the enum value for the font style.

    Parameters
    ----------
    lock : lock
      Lock on the 3D text for which the style should be returned.

    Returns
    -------
    int
      Enum value of the font style.

    """
    raise_if_version_too_old(
      "Getting font style",
      current_version=self.version,
      required_version=(1, 2))

    return self.dll.ModellingGetTextFontStyle(lock)

  def SetTextFontStyle(self, lock, new_style):
    """Sets the font style using the enum value.

    Parameters
    ----------
    lock : lock
      Lock on the 3D text for which the style should be set.
    new_style : int
      Style to set for the 3D text.

    Raises
    ------
    CAPIUnknownError
      If an error occurs.

    """
    raise_if_version_too_old(
      "Setting font style",
      current_version=self.version,
      required_version=(1, 2))
    result = self.dll.ModellingSetTextFontStyle(lock, new_style)

    if result != 0:
      message = "Failed to set font style of 3D text."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def GetAssociatedRasterCount(self, lock):
    """Returns the count of raster objects associated with the topology object.

    Parameters
    ----------
    lock : Lock
      Lock on the topology object to query rasters for.

    Returns
    -------
    int
      The count of rasters associated with the object.

    """
    raise_if_version_too_old(
      "Getting associated raster count",
      current_version=self.version,
      required_version=(1, 2))

    return self.dll.ModellingGetAssociatedRasterCount(lock)

  def GetAssociatedRasters(self, lock):
    """Returns a dictionary of raster objects associated with the topology
    object. The dictionary keys are numeric, however may not be consecutive(
    For example, a object could have rasters with ids 0, 1, 5, 105 and 255).
    The values are the ids of the raster objects.

    Parameters
    ----------
    lock: Lock
      Lock on the topology object to query rasters.

    Returns
    -------
    dict
      Dictionary where key is raster index and value is object id.

    Raises
    ------
    CApiUnknownError
      If an error occurs.

    """
    raise_if_version_too_old(
      "Getting associated rasters",
      current_version=self.version,
      required_version=(1, 2))

    raster_count = self.GetAssociatedRasterCount(lock)
    raster_indices = (ctypes.c_uint8 * raster_count)()
    raster_ids = (T_ObjectHandle * raster_count)()

    result = self.dll.ModellingGetAssociatedRasters(lock, raster_indices,
                                                    raster_ids)

    if result != 0:
      message = "Failed to get associated rasters."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)
    return dict(zip(raster_indices, raster_ids))

  def AssociateRaster(self, lock, raster, desired_index):
    """Associates a raster with the locked object.

    This does not set any of the information required to generate
    the point to pixel mapping. Use SetRasterControlTwoPoint (or equivalent)
    to set that information.

    Parameters
    ----------
    lock : Lock
      Lock on the object to associate the raster to.
    raster : T_ObjectHandle
      Object handle of the raster to associate.
    desired_index : int
      Desired index to give the raster. Rasters with higher indices appear
      on top of rasters with lower indices.

    Returns
    -------
    int
      Raster index the raster was given.

    Raises
    ------
    CApiUnknownError
      If an unknown error occurs.

    """
    raise_if_version_too_old(
      "Getting associated rasters",
      current_version=self.version,
      required_version=(1, 2))

    final_index = ctypes.c_uint8()
    result = self.dll.ModellingAssociateRaster(
      lock,
      raster,
      desired_index,
      ctypes.byref(final_index))
    if result != 0:
      message = "Failed to associate raster."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)
    return final_index

  def DissociateRaster(self, lock, raster):
    """Dissociates the raster with the locked object.

    Parameters
    ----------
    lock: Lock
      Lock on the topology object the raster should be dissociated from.
    raster : T_ObjectHandle
      Object handle of the raster which should be dissociated.

    Returns
    -------
    bool
      True if the raster was associated with the object,
      False otherwise.

    Raises
    ------
    CApiUnknownError
      If an unknown error occurs.

    """
    raise_if_version_too_old(
      "Getting associated rasters",
      current_version=self.version,
      required_version=(1, 3))

    result = self.dll.ModellingDissociateRaster(lock, raster)

    # A return code of 3 indicates the raster was not associated
    # with the object.
    if result == 3:
      return False

    if result != 0:
      message = "Failed to associate raster."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

    return True

  def RasterSetControlTwoPoint(self, lock, image_points, world_points, orientation):
    """Wrapper for associating a raster to a surface. This sets how the
    image points, world points and orientation will be used to project the
    raster onto a surface.

    This does not perform the actual association of the raster to the surface.
    You must call AssociateRaster to do that.
    Use RasterGetRegistration to query the image points, world points and
    orientation passed to this function.

    Parameters
    ----------
    lock : Lock
      Lock on the raster to set the two point control for.
    image_points : numpy.ndarray
      Array of shape (n, 2) representing the points on the image which
      match the points on the surface. Each row is of the form [X, Y].
    world_points : numpy.ndarray
      Array of shape (n, 3) representing the points in world space
      which match the points on the image. Each row is of the form [X, Y, Z].
    orientation : numpy.ndarray
      Orientation to use when projecting the raster onto the surface. This
      is a vector of the form [X, Y, Z].

    Raises
    ------
    ValueError
      If the number of image/world points is not valid for associating
      the raster to a surface or if orientation is not finite.
    ApplicationTooOldError
      If the C API used is not supported by the application.
    """
    point_count = min(image_points.shape[0], world_points.shape[0])
    if point_count < 2:
      raise ValueError("Two point association requires at least two points, "
                         f"given: {point_count}")
    c_image_points = (ctypes.c_double * (point_count * 2))()
    c_image_points[:] = image_points.astype(ctypes.c_double, copy=False).reshape(-1)
    c_world_points = (ctypes.c_double * (point_count * 3))()
    c_world_points[:] = world_points.astype(ctypes.c_double, copy=False).reshape(-1)
    c_orientation = (ctypes.c_double * 3)()
    c_orientation[:] = orientation.astype(ctypes.c_double, copy=False).reshape(-1)

    raise_if_version_too_old(
      "Setting raster registration points",
      current_version=self.version,
      required_version=(1, 3))

    result = self.dll.ModellingRasterSetControlTwoPoint(
      lock,
      c_image_points,
      c_world_points,
      point_count,
      c_orientation)

    if result == 3:
      raise ValueError("Failed to set registration points. The orientation "
                       "was not finite")

    if result != 0:
      message = "Failed to set registration points."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def GetRasterRegistrationType(self, lock):
    """Query the type of registration used to associate a raster with a
    Topology Object.

    Parameters
    ----------
    lock : Lock
      Lock on the raster to get the registration type for.

    Returns
    -------
    int
      Int representing the registration type. In particular:
      0 = no registration information set.
      3 = Two point registration.
      6 = Multi point registration.
      8 = Panoramic photograph to scan.

    Raises
    ------
    CApiUnknownError
      If an error occurs.
    ApplicationTooOldError
      If the C API used is not supported by the application.

    """
    raise_if_version_too_old(
      "Getting raster registration type",
      current_version=self.version,
      required_version=(1, 3))

    registration_type = ctypes.c_uint8()
    result = self.dll.ModellingGetRasterRegistrationType(
      lock,
      ctypes.byref(registration_type))

    if result != 0:
      message = "Failed to get registration type."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

    return registration_type.value

  def RasterGetRegistration(self, lock):
    """Wrapper for getting the raster registration point pairs.

    In particular, this will return the point pairs passed to
    RasterSetControlTwoPoint and RasterSetControlMultiPoint.

    Parameters
    ----------
    lock : Lock
      Lock on the raster to read registration information from.

    Returns
    -------
    tuple
      A tuple of the following form:
      (image_points, world_points, point_count, orientation) where
      image_points, world_points and orientation are ctypes.c_double arrays
      and point_count is the number of points in image_points and world_points.
    """
    raise_if_version_too_old(
      "Getting registration points",
      current_version=self.version,
      required_version=(1, 3))

    # Allocate enough for eight points by default. This should almost
    # always be enough points.
    original_point_count = 8
    point_count = ctypes.c_uint32(original_point_count)

    # Each image point is represented as two doubles.
    image_points = (ctypes.c_double * (2 * point_count.value))()
    # Each world point is represented as three doubles.
    world_points = (ctypes.c_double * (3 * point_count.value))()
    # Orientation is always three floats.
    orientation = (ctypes.c_double * 3)()

    result = self.dll.ModellingRasterGetRegistration(
      lock, image_points, world_points, ctypes.byref(point_count), orientation)

    if result == 5:
      # Buffer is too small. PointCount now contains the correct size.
      image_points = (ctypes.c_double * (2 * point_count.value))()
      world_points = (ctypes.c_double * (3 * point_count.value))()
      result = self.dll.ModellingRasterGetRegistration(
        lock, image_points, world_points, ctypes.byref(point_count), orientation)

    if result != 0:
      message = "Failed to get registration points."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

    final_point_count = point_count.value
    # If the original point count is greater than the final point count,
    # then there were less than eight points. This allocates eight
    # points by default, so the image and world point arrays have
    # unallocated memory at the end which needs to be removed.
    if final_point_count < original_point_count:
      image_points = image_points[:final_point_count * 2]
      world_points = world_points[:final_point_count * 3]
    return image_points, world_points, point_count.value, orientation

  def TangentPlaneType(self):
    """Returns the Type of Tangent Plane as stored in the project."""
    if self.version < (1, 3):
      return None
    return self.dll.ModellingTangentPlaneType()

  def NewTangentPlane(self):
    """Creates a new tangent plane and returns it."""
    raise_if_version_too_old("Creating a Discontinuity",
                             current_version=self.version,
                             required_version=(1, 3))
    return self.dll.ModellingNewTangentPlane()

  def SetTangentPlaneFromPoints(self, lock, points):
    """Sets the points of a tangent plane and re-triangulates it.

    Parameters
    ----------
    lock : Lock
      Lock on the tangent plane to assign points to.
    points : ndarray
      Numpy array of points to use.

    Raises
    ------
    CApiUnknownError
      If an error occurs.

    """
    raise_if_version_too_old("Setting discontinuity points",
                             current_version=self.version,
                             required_version=(1, 3))
    point_count = points.shape[0]
    c_points = (ctypes.c_double * (point_count * 3))()
    final_points = points.astype(ctypes.c_double, copy=False).reshape(-1)
    c_points[:] = final_points
    result = self.dll.ModellingSetTangentPlaneFromPoints(lock,
                                                         c_points,
                                                         point_count)

    if result != 0:
      message = "Failed to set discontinuity points"
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def TangentPlaneGetOrientation(self, lock):
    """Returns the orientation of the tangent plane.

    Parameters
    ----------
    Lock
      Lock on the tangent plane of which the orientation should be retrieved.

    Returns
    -------
    tuple
      The tuple (dip, dip direction). Both are in radians.

    Raises
    ------
    CApiUnknownError
      If an error occurs.

    """
    raise_if_version_too_old("Getting discontinuity dip and dip direction",
                             current_version=self.version,
                             required_version=(1, 3))
    dip = ctypes.c_double()
    dip_direction = ctypes.c_double()

    result = self.dll.ModellingTangentPlaneGetOrientation(
      lock,
      ctypes.byref(dip),
      ctypes.byref(dip_direction))

    if result != 0:
      message = "Failed to get discontinuity orientation."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)
    return (dip.value, dip_direction.value)

  def TangentPlaneSetOrientation(self, lock, dip, dip_direction):
    """Sets the orientation of the tangent plane.

    Parameters
    ----------
    Lock
      Write lock on the tangent plane of which the dip and dip direction
      should be set.
    dip
      Dip to assign to the tangent plane.
    dip_direction
      Dip direction to assign to the tangent plane.

    Raises
    ------
    CApiUnknownError
      If an error occurs.

    """
    raise_if_version_too_old("Setting discontinuity dip and dip direction",
                             current_version=self.version,
                             required_version=(1, 3))
    result = self.dll.ModellingTangentPlaneSetOrientation(lock, dip,
                                                          dip_direction)
    if result != 0:
      message = "Failed to set discontinuity orientation."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def TangentPlaneGetLength(self, lock):
    """Returns the length of the tangent plane.

    Parameters
    ----------
    lock : Lock
      Lock on the tangent plane to get the length of.

    Returns
    -------
    float
      The length of the tangent plane.

    Raises
    ------
    CApiUnknownError
      If an error occurs.

    """
    raise_if_version_too_old("Getting discontinuity length",
                             current_version=self.version,
                             required_version=(1, 3))
    length = ctypes.c_double()
    result = self.dll.ModellingTangentPlaneGetLength(lock,
                                                     ctypes.byref(length))

    if result != 0:
      message = "Failed to get discontinuity length."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)
    return length.value

  def TangentPlaneSetLength(self, lock, new_length):
    """Sets the length of a tangent plane. This will scale the plane
    to the new length.

    Parameters
    ----------
    lock : Lock
      Lock on the tangent plane whose length should be set.
    new_length : float
      The new length to set to the tangent plane.

    Raises
    ------
    CApiUnknownError
      If an error occurs.

    """
    raise_if_version_too_old("Getting discontinuity length",
                             current_version=self.version,
                             required_version=(1, 3))

    result = self.dll.ModellingTangentPlaneSetLength(lock, new_length)
    if result != 0:
      message = "Failed to set discontinuity length."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def TangentPlaneGetArea(self, lock):
    """Returns the area of a tangent plane.

    Parameters
    ----------
    lock : Lock
      Lock on the tangent plane whose area should be returned.

    Returns
    -------
    float
      The area of the tangent plane.

    Raises
    ------
    CApiUnknownError
      If an error occurs.

    """
    raise_if_version_too_old("Getting discontinuity area",
                             current_version=self.version,
                             required_version=(1, 3))

    area = ctypes.c_double()
    result = self.dll.ModellingTangentPlaneGetArea(lock, ctypes.byref(area))

    if result != 0:
      message = "Failed to get discontinuity area."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)
    return area.value

  def TangentPlaneGetLocation(self, lock):
    """Returns the location of a tangent plane.

    Parameters
    ----------
    lock : Lock
      Lock on the tangent plane whose location should be returned.

    Returns
    -------
    list
      The location of the tangent plane in the form [x, y, z].

    Raises
    ------
    CApiUnknownError
      If an error occurs.

    """
    raise_if_version_too_old("Getting discontinuity location",
                          current_version=self.version,
                          required_version=(1, 3))

    location = (ctypes.c_double * 3)()
    result = self.dll.ModellingTangentPlaneGetLocation(lock,
                                                       location)
    if result != 0:
      message = "Failed to get discontinuity location."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)
    return np.array(location)

  def TangentPlaneSetLocation(self, lock, x, y, z):
    """Sets the location of the tangent plane.

    Parameters
    ----------
    lock : Lock
      Lock on the tangent plane.
    x : float
      X component of the new location.
    y : float
      Y component of the new location.
    z : float
      Z component of the new location.

    Raises
    ------
    CApiUnknownError
      If an error occurs.

    """
    raise_if_version_too_old("Setting discontinuity location",
                             current_version=self.version,
                             required_version=(1, 3))

    location = (ctypes.c_double * 3)()
    location[0] = x
    location[1] = y
    location[2] = z

    result = self.dll.ModellingTangentPlaneSetLocation(lock,
                                                       location)
    if result != 0:
      message = "Failed to set discontinuity location."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def GetCoordinateSystem(self, lock):
    """Get the coordinate system of the object.

    Parameters
    ----------
    lock : Lock
      Lock on the object for which the coordinate system should be retrieved.

    Returns
    -------
    str
      "well known text" representation of the coordinate system. Or the
      blank string if the object does not have a coordinate system.
    numpy.ndarray
      11 floats representing the local transformation of the coordinate system.
      See set coordinate system for an explanation of what each float means.

    Raises
    ------
    FileNotFound
      If the proj database could not be found.
    CApiUnknownError
      If an unknown error occurs.

    """
    raise_if_version_too_old("Getting coordinate system",
                             current_version=self.version,
                             required_version=(1, 3))

    wkt_length = ctypes.c_uint32(0)
    local_transform = (ctypes.c_double * 11)()
    local_transform_length = ctypes.c_uint32(11)
    result = self.dll.ModellingGetCoordinateSystem(
      lock,
      None,
      ctypes.byref(wkt_length),
      local_transform,
      local_transform_length)

    if result == 0:
      # We gave it an empty buffer, but it returned success so the coordinate
      # system must not exist.
      return "", local_transform
    if result == 4:
      message = ("Failed to locate the proj db. The application may not "
                 "support coordinate systems.")
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise FileNotFoundError(message)

    # If the coordinate system is not empty, then result will be 5
    # and wkt_length will have been set to the length of the wkt string.
    if result != 5:
      message = "Failed to get size of coordinate system."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

    buffer = ctypes.create_string_buffer(wkt_length.value)

    result = self.dll.ModellingGetCoordinateSystem(
      lock,
      buffer,
      ctypes.byref(wkt_length),
      local_transform,
      local_transform_length)

    if result != 0:
      message = "Failed to get coordinate system."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

    return bytearray(buffer).decode('utf-8'), local_transform

  def SetCoordinateSystem(self, lock, wkt_string, local_transform):
    """Set the coordinate system of an object.

    Parameters
    ----------
    lock : Lock
      Lock on the object for which the coordinate system should be set.
    wkt_string : str
      "Well known text" string representing the coordinate system to set.
    local_transform : numpy.ndarray
      Numpy ndarray of shape (11,) representing the local transform.
      Items are as follows:
      0: Horizontal origin X
      1: Horizontal origin Y
      2: Horizontal scale factor
      3: Horizontal rotation
      4: Horizontal shift X
      5: Horizontal shift Y
      6: Vertical shift
      7: Vertical origin X
      8: Vertical origin Y
      9: Vertical slope X
      10: Vertical slope Y

    Raises
    ------
    ValueError
      If the application could not understand the coordinate system.
    FileNotFoundError
      If the proj database could not be found.
    CApiUnknownError
      If an unknown error occurs.

    """
    raise_if_version_too_old("Setting coordinate system",
                             current_version=self.version,
                             required_version=(1, 3))

    byte_string = wkt_string.encode('utf-8')
    wkt_length = len(byte_string)
    transform = (ctypes.c_double * 11)()
    local_transform_length = ctypes.c_uint32(11)
    transform[:] = local_transform
    result = self.dll.ModellingSetCoordinateSystem(
      lock,
      byte_string,
      wkt_length,
      transform,
      local_transform_length)

    if result == 3:
      message = ("The application could not understand the coordinate system. "
                 "It is either not supported or invalid.")
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise ValueError(message)
    if result == 4:
      message = ("Failed to locate the proj db. The application "
                 "may not support coordinate systems.")
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise FileNotFoundError(message)
    if result != 0:
      message = "Failed to set coordinate system."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def ClearCoordinateSystem(self, lock):
    """Clear the coordinate system of an object.

    Parameters
    ----------
    lock
      Edit lock on the object to clear the coordinate system for.
    """
    raise_if_version_too_old("Setting coordinate system",
                             current_version=self.version,
                             required_version=(1, 10))

    result = self.dll.ModellingClearCoordinateSystem(lock)

    if result != 0:
      message = "Failed to clear coordinate system."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def RibbonChainType(self):
    """Wrapper for getting the ribbon chain type."""
    if self.version < (1, 3):
      return None
    if self.version == (1, 3):
      # Various versions of Evolution include API 1.3 but don't include
      # this function, so check if it exists and ignore it if it doesn't.
      if not hasattr(self.dll, 'ModellingRibbonChainType'):
        return None
    return self.dll.ModellingRibbonChainType()

  def RibbonLoopType(self):
    """Wrapper for getting the ribbon loop type."""
    if self.version < (1, 3):
      return None
    if self.version == (1, 3):
      # Various versions of Evolution include API 1.3 but don't include
      # this function, so check if it exists and ignore it if it doesn't.
      if not hasattr(self.dll, 'ModellingRibbonLoopType'):
        return None
    return self.dll.ModellingRibbonLoopType()

  def GetMarkerHeight(self, lock: T_ReadHandle) -> float:
    """Get the height of a marker.

    Parameters
    ----------
    lock
      Lock on a marker to get the height for.

    Returns
    -------
    float
      The height of the marker.
    """
    raise_if_version_too_old("Setting marker height",
                             current_version=self.version,
                             required_version=(1, 4))

    return float(self.dll.ModellingGetMarkerHeight(lock))

  def SetMarkerHeight(self, lock: T_ReadHandle, height: float):
    """Set the height of a marker.

    Parameters
    ----------
    lock
      Lock on the marker to set the height for.
    height
      The height value to assign to the Marker.
    """
    raise_if_version_too_old("Setting marker height",
                             current_version=self.version,
                             required_version=(1, 4))

    self.dll.ModellingSetMarkerHeight(lock, height)

  def NewRibbonChain(self):
    """Create a new ribbon chain.

    Returns
    -------
    T_ObjectHandle
      Object handle for the new ribbon chain.
    """
    raise_if_version_too_old("Creating new ribbon chain",
                             current_version=self.version,
                             required_version=(1, 8))
    return self.dll.ModellingNewRibbonChain()

  def NewRibbonLoop(self):
    """Create a new ribbon loop.

    Returns
    -------
    T_ObjectHandle
      Object handle for the new ribbon loop.
    """
    raise_if_version_too_old("Creating new ribbon loop",
                             current_version=self.version,
                             required_version=(1, 8))
    return self.dll.ModellingNewRibbonLoop()

  def PointWidthsBeginR(self, lock):
    """Wrapper for getting read-only width array of a ribbon.

    Parameters
    ----------
    lock
      Lock on the ribbon to return the widths for.

    Returns
    -------
    ctypes.POINTER(ctypes.c_double)
      Pointer to an array of double containing the point widths for the
      ribbon.
    """
    raise_if_version_too_old("Getting ribbon width",
                             current_version=self.version,
                             required_version=(1, 8))
    return self.dll.ModellingPointWidthsBeginR(lock)

  def PointWidthsBeginRW(self, lock):
    """Wrapper for getting read/write width array of a ribbon.

    Parameters
    ----------
    lock
      Lock on the ribbon to return the widths for.

    Returns
    -------
    ctypes.POINTER(ctypes.c_double)
      Pointer to an array of double containing the point widths for the
      ribbon.
    """
    raise_if_version_too_old("Setting ribbon width",
                             current_version=self.version,
                             required_version=(1, 8))
    return self.dll.ModellingPointWidthsBeginRW(lock)

  def PointAnglesBeginR(self, lock):
    """Wrapper for getting read-only angles array of a ribbon.

    Parameters
    ----------
    lock
      Lock on the ribbon to return the angles for.

    Returns
    -------
    ctypes.POINTER(ctypes.c_double)
      Pointer to an array of double containing the point angles for the
      ribbon.
    """
    raise_if_version_too_old("Getting ribbon angles",
                             current_version=self.version,
                             required_version=(1, 8))
    return self.dll.ModellingPointAnglesBeginR(lock)

  def PointAnglesBeginRW(self, lock):
    """Wrapper for getting read/write angles array of a ribbon.

    Parameters
    ----------
    lock
      Lock on the ribbon to return the angles for.

    Returns
    -------
    ctypes.POINTER(ctypes.c_double)
      Pointer to an array of double containing the point angles for the
      ribbon.
    """
    raise_if_version_too_old("Setting ribbon angles",
                             current_version=self.version,
                             required_version=(1, 8))
    return self.dll.ModellingPointAnglesBeginRW(lock)

  def PointNormalsBeginR(self, lock):
    """Wrapper for getting ribbon point normals.

    Parameters
    ----------
    lock
      Lock on the ribbon to return the point normals for.

    Returns
    -------
    ctypes.POINTER(ctypes.c_double)
      Pointer to an array of double containing the point normals for the
      ribbon.
    """
    raise_if_version_too_old("Getting ribbon normals",
                             current_version=self.version,
                             required_version=(1, 8))
    return self.dll.ModellingPointNormalsBeginR(lock)

  def RaiseOnErrorCode(self):
    """Raises the last known error code returned by the modelling library.

    This should only be called after calling a C API function and that
    function expected an error. This typically means when the function returns
    a null pointer or null object ID when one isn't expected (like creating a
    object).

    Raises
    ------
    MemoryError
      If the cause for the error was due to memory pressure.
    CApiUnknownError
      If an error occurs.

    """

    # pylint: disable=too-few-public-methods
    class ErrorCodes:
      """Error codes a C API function could have returned."""
      NO_ERROR = 0
      """The "null" error code"""

      OUT_OF_SHARED_MEMORY = 7
      """The shared memory region is out-of-memory."""

    if self.version < (1, 5):
      # In older versions we assume that there was no error.
      error_code = ErrorCodes.NO_ERROR
    else:
      error_code = self.dll.ModellingErrorCode()


    if error_code == ErrorCodes.NO_ERROR:
      return

    error_message = self.dll.ModellingErrorMessage().decode('utf-8')

    if error_code == ErrorCodes.OUT_OF_SHARED_MEMORY:
      raise MemoryError(error_message)

    raise CApiUnknownError(error_message)

  def TangentPlaneGetPolarity(self, lock):
    """Get the polarity of a tangent plane.

    Parameters
    ----------
    lock
      Lock on the tangent plane to get the polarity for.

    Returns
    -------
    int
      An integer representing the polarity.
      -1 indicates Overturned.
      0 indicates Unknown.
      1 indicates Upright.
    """
    raise_if_version_too_old("Getting polarity.",
                             current_version=self.version,
                             required_version=(1, 8))

    polarity = ctypes.c_int32()
    result = self.dll.ModellingTangentPlaneGetPolarity(
      lock, ctypes.byref(polarity)
    )

    if result != 0:
      message = "Failed to get discontinuity polarity."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

    return polarity.value

  def TangentPlaneSetPolarity(self, lock, polarity):
    """Set the polarity of a tangent plane.

    Parameters
    ----------
    lock
      Lock on the tangent plane to set the polarity for.
    polarity
      The polarity to set for the tangent plane.
      -1 indicates Overturned.
      0 indicates Unknown.
      1 indicates Upright.
    """
    raise_if_version_too_old("Setting polarity.",
                             current_version=self.version,
                             required_version=(1, 8))

    result = self.dll.ModellingTangentPlaneSetPolarity(lock, polarity)

    if result != 0:
      message = "Failed to set discontinuity polarity."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def GetNaturalColour(self, lock):
    """Get the natural colour of a topology object.

    Parameters
    ----------
    lock
      Lock on the topology object to return the natural colour of.

    Returns
    -------
    tuple
      The tuple (red, green, blue) representing the natural colour
      of the object.
      Note that the natural colour lacks an alpha value.
    """
    raise_if_version_too_old("Getting natural colour.",
                             current_version=self.version,
                             required_version=(1, 8))

    natural_colour = (ctypes.c_uint8 * 3)()
    result = self.dll.ModellingGetNaturalColour(lock, natural_colour)

    if result != 0:
      message = "Failed to get natural colour."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

    return (natural_colour[0], natural_colour[1], natural_colour[2])

  def SetNaturalColour(self, lock, colour):
    """Set the natural colour of a topology object.

    Parameters
    ----------
    lock
      Lock on the topology object to set the natural colour of.
    colour
      The colour to set for the topology object. This should be of the
      from (Red, Green, Blue).
    """
    raise_if_version_too_old("Setting natural colour.",
                             current_version=self.version,
                             required_version=(1, 8))

    natural_colour = (ctypes.c_uint8 * 3)()
    natural_colour[:] = colour
    result = self.dll.ModellingSetNaturalColour(lock, natural_colour)

    if result != 0:
      message = "Failed to get natural colour."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def HasTopologyFrontColour(self, lock) -> bool:
    """Get if a topology object has a front colour.

    Parameters
    ----------
    lock
      Lock on the topology object to check if it has a front colour.

    Returns
    -------
    bool
      True if the object has a front colour, False if it doesn't.
    """
    raise_if_version_too_old("Checking if an object has two sided colouring",
                             current_version=self.version,
                             required_version=(1, 8))

    return self.dll.ModellingTopologyHasFrontColour(lock)

  def HasTopologyBackColour(self, lock) -> bool:
    """Get if a topology object has a back colour.

    Parameters
    ----------
    lock
      Lock on the topology object to check if it has a back colour.

    Returns
    -------
    bool
      True if the object has a back colour, False if it doesn't.
    """
    raise_if_version_too_old("Checking if an object has two sided colouring",
                             current_version=self.version,
                             required_version=(1, 8))

    return self.dll.ModellingTopologyHasBackColour(lock)

  def TopologySetHasFrontColour(self, lock, has_front_colour):
    """Set if a topology object has a front colour.

    Parameters
    ----------
    lock
      Lock on the topology object to set if it has a front colour.
    has_front_colour
      True if the object should be set to have a front colour,
      False if the object should be set to not have a front colour
      (And thus for the front of the object to be coloured to use the
      natural colour)
    """
    raise_if_version_too_old("Setting two sided colouring",
                             current_version=self.version,
                             required_version=(1, 8))

    result = self.dll.ModellingTopologySetHasFrontColour(lock, has_front_colour)

    if result != 0:
      message = "Failed to set two sided colouring."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def TopologySetHasBackColour(self, lock, has_back_colour):
    """Set if a topology object has a front colour.

    Parameters
    ----------
    lock
      Lock on the topology object to set if it has a back colour.
    has_back_colour
      True if the object should be set to have a back colour,
      False if the object should be set to not have a back colour
      (And thus for the back of the object to be coloured to use the
      natural colour)
    """
    raise_if_version_too_old("Setting two sided colouring",
                             current_version=self.version,
                             required_version=(1, 8))

    result = self.dll.ModellingTopologySetHasBackColour(lock, has_back_colour)

    if result != 0:
      message = "Failed to set two sided colouring."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def StringColourMapGetCaseSensitive(self, lock):
    """Get if a string colour map is case sensitive.

    If connected to an application which does not support querying the
    case sensitivity, this will always return True.

    Parameters
    ----------
    lock
      Lock on the string colour map to return if it is case sensitive.

    Returns
    -------
    bool
      True if the string colour map is case sensitive, False if it is case
      insensitive.
    """
    if self.version < (1, 8):
      return True

    try:
      return self.dll.ModellingStringColourMapGetCaseSensitive(lock)
    except AttributeError:
      return True

  def StringColourMapSetCaseSensitive(self, lock, is_case_sensitive):
    """Set if a string colour map is case sensitive.

    Parameters
    ----------
    lock
      Lock on the string colour map to return if it is case sensitive.
    is_case_sensitive
      Value to set for if the colour map is case sensitive.

    Raises
    ------
    CApiUnknownError
      If the colour map contains keys which only differ by case
      and is_case_sensitive=False.
    """
    if self.version < (1, 8):
      # For applications which do not support this function, the SDK assumes
      # colour maps are case sensitive so only raise an error if the user set
      # the colour map to not be case sensitive.
      if is_case_sensitive:
        return
      raise_if_version_too_old("Setting colour map case sensitivity",
                                current_version=self.version,
                                required_version=(1, 8))

    try:
      result = self.dll.ModellingStringColourMapSetCaseSensitive(
        lock, is_case_sensitive)
    except AttributeError:
      # See comment above about applications not supporting this function.
      if is_case_sensitive:
        return
      raise

    if result != 0:
      message = "Failed to set string colour map case sensitivity."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def NewEllipsoid(self):
    """Create a new Ellipsoid.

    Returns
    -------
    T_ObjectHandle
      Object ID of the newly created Ellipsoid.
    """
    raise_if_version_too_old("Creating a new ellipsoid.",
                             current_version=self.version,
                             required_version=(1, 8))

    return self.dll.ModellingNewEllipsoid()

  def GetEllipsoidSize(self, lock):
    """Get the size of an Ellipsoid.

    Parameters
    ----------
    lock
      Lock on the ellipsoid to get the size for.

    Returns
    -------
    tuple
      The tuple (A, B, C) representing the size of the ellipsoid.
      A = size in semi-major axis
      B = size in major axis
      C = size in minor axis
    """
    raise_if_version_too_old("Getting ellipsoid size.",
                             current_version=self.version,
                             required_version=(1, 8))

    a = self.dll.ModellingGetEllipsoidA(lock)
    b = self.dll.ModellingGetEllipsoidB(lock)
    c = self.dll.ModellingGetEllipsoidC(lock)

    return (a, b, c)

  def SetEllipsoidSize(self, lock, a, b, c):
    """Set the size of an ellipsoid.

    Parameters
    ----------
    lock
      Lock on the ellipsoid to set the size of.
    A
      Size in the semi-major axis.
    B
      Size in the major axis.
    C
      Size in the minor axis.

    Raises
    ------
    CApiUnknownError
      If A, B or C is less than or equal to zero.
    """
    raise_if_version_too_old("Setting ellipsoid size.",
                             current_version=self.version,
                             required_version=(1, 8))

    result = self.dll.ModellingSetEllipsoidABC(lock, a, b, c)
    if result != 0:
      message = "Failed to set ellipsoid size."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def GetEllipsoidCentre(self, lock):
    """Get the centre point of an ellipsoid.

    Parameters
    ----------
    lock
      Lock on the ellipsoid to return the centre for.

    Returns
    -------
    tuple[float, float, float]
      Tuple containing the X, Y and Z ordinates of the centre point of the
      ellipsoid.
    """
    raise_if_version_too_old("Getting ellipsoid centre.",
                             current_version=self.version,
                             required_version=(1, 8))

    c_centre = (ctypes.c_double * 3)()

    result = self.dll.ModellingGetEllipsoidCentre(lock, c_centre)

    if result != 0:
      message = "Failed to get ellipsoid centre."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

    return (c_centre[0], c_centre[1], c_centre[2])

  def SetEllipsoidCentre(self, lock, x, y, z):
    """Set the centre point of an ellipsoid.

    Parameters
    ----------
    lock
      Lock on the ellipsoid to set the centre for.
    x
      x ordinate of the centre point.
    y
      y ordinate of the centre point.
    z
      z ordinate of the centre point.
    """
    raise_if_version_too_old("Setting ellipsoid centre.",
                             current_version=self.version,
                             required_version=(1, 8))

    result = self.dll.ModellingSetEllipsoidCentre(lock, x, y, z)

    if result != 0:
      message = "Failed to set ellipsoid centre."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def GetEllipsoidRotation(self, lock):
    """Get the rotation of an ellipsoid.

    Parameters
    ----------
    lock
      Lock on the ellipsoid to return the rotation of.

    Returns
    -------
    tuple[float, float, float, float]
      Tuple containing the rotation of the ellipsoid in the form:
      (Q0, Q1, Q2, Q3).
    """
    raise_if_version_too_old("Getting ellipsoid rotation.",
                             current_version=self.version,
                             required_version=(1, 8))

    quaternions = (ctypes.c_double * 4)()
    result = self.dll.ModellingGetEllipsoidRotation(lock, quaternions)

    if result != 0:
      message = "Failed to get ellipsoid rotation."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

    return (quaternions[0], quaternions[1], quaternions[2], quaternions[3])

  def SetEllipsoidRotation(self, lock, q0, q1, q2, q3):
    """Set the rotation of an ellipsoid.

    Parameters
    ----------
    lock
      Edit lock on the ellipsoid to set the rotation for.
    q0
      First component of the quaternion representing the rotation.
    q1
      Second component of the quaternion representing the rotation.
    q2
      Third component of the quaternion representing the rotation.
    q3
      Fourth component of the quaternion representing the rotation.
    """
    raise_if_version_too_old("Setting ellipsoid rotation.",
                             current_version=self.version,
                             required_version=(1, 8))

    result = self.dll.ModellingSetEllipsoidRotation(lock, q0, q1, q2, q3)

    if result != 0:
      message = "Failed to set ellipsoid rotation."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

  def EdgeLoopAreaType(self):
    """Wrapper for getting the edge loop area type."""
    if self.version < (1, 3):
      return None
    if self.version == (1, 3):
      # Various versions of Evolution include API 1.3 but don't include
      # this function, so check if it exists and ignore it if it doesn't.
      if not hasattr(self.dll, 'ModellingEdgeLoopAreaType'):
        return None
    return self.dll.ModellingEdgeLoopAreaType()

  def NewEdgeLoopArea(self):
    """Wrapper for creating a new edge loop area object."""
    raise_if_version_too_old(
      "Creating EdgeLoopArea objects",
      self.version,
      (1, 10)
    )
    return self.dll.ModellingNewEdgeLoopArea()

  def EllipsoidType(self):
    """Wrapper for getting the ellipsoid type."""
    if self.version < (1, 3):
      return None
    if self.version == (1, 3):
      # Various versions of Evolution include API 1.3 but don't include
      # this function, so check if it exists and ignore it if it doesn't.
      if not hasattr(self.dll, 'ModellingEllipsoidType'):
        return None
    return self.dll.ModellingEllipsoidType()

  def SurfacePointToRasterCoordinateOverrideR(self, lock, raster_index):
    """Read access to a surface's raster coordinate override arrays.

    Parameters
    ----------
    lock
      Lock on the surface to read the raster coordinate override array for.
    raster_index
      Index of the raster to read the raster coordinate override array for.

    Returns
    -------
    ctypes.Array[float]
      Read-only array of raster coordinate override points for the raster
      with the given index.
    """
    raise_if_version_too_old(
      feature="Read raster coordinate override",
      current_version=self.version,
      required_version=(1, 10)
    )
    return self.dll.ModellingSurfacePointToRasterCoordinateOverrideR(
      lock, raster_index)

  def SurfacePointToRasterCoordinateOverrideRW(self, lock, raster_index):
    """Write access to a surface's raster coordinate override arrays.

    Parameters
    ----------
    lock
      Lock on the surface to read the raster coordinate override array for.
    raster_index
      Index of the raster to read the raster coordinate override array for.

    Returns
    -------
    ctypes.Array[float]
      Read/write Array of raster coordinate override points for the raster
      with the given index.
    """
    raise_if_version_too_old(
      feature="Read raster coordinate override",
      current_version=self.version,
      required_version=(1, 10)
    )
    return self.dll.ModellingSurfacePointToRasterCoordinateOverrideRW(
      lock, raster_index)

  def ColourMapGetColoursForValues(self, lock, values):
    """Wrapper for getting colours for values in a NumericColourMap.

    Parameters
    ----------
    lock
      Read lock on the colour map to read values for.
    values
      Sequence of floats of the values to return the colours for.

    Returns
    -------
    np.ndarray
      A numpy array containing the colour for each value in values.
      It has shape (len(values), 4) with each row containing the colour
      corresponding to the value in values at the corresponding index.
    """
    raise_if_version_too_old(
      feature="Read raster coordinate override",
      current_version=self.version,
      required_version=(1, 10)
    )

    value_count = len(values)
    c_values = (ctypes.c_double * value_count)(*values)
    c_colours = (ctypes.c_uint8 * (value_count * 4))()

    result = self.dll.ModellingColourMapGetColoursForValues(
      lock,
      value_count,
      c_values,
      c_colours
    )

    if result != 0:
      message = "Failed to get colours for map."
      self.log.error(message)
      self.log.info("Error code: %s", result)
      raise CApiUnknownError(message)

    result = np.array(c_colours, dtype=ctypes.c_uint8)
    result.shape = (-1, 4)
    return result

  def GetEdgeNetworkEdgeThickness(self, lock) -> float:
    """Get the edge thickness for a topology object."""
    raise_if_version_too_old(
      feature="Read edge thickness",
      current_version=self.version,
      required_version=(1, 11)
    )

    return self.dll.ModellingGetEdgeNetworkEdgeThickness(lock)

  def GetAnnotationText(self, lock: T_ReadHandle) -> str:
    """Get the text of an annotation object."""
    buf_size = self.dll.ModellingGetAnnotationText(lock, None, 0)
    str_buf = ctypes.create_string_buffer(buf_size)
    self.dll.ModellingGetAnnotationText(lock, str_buf, buf_size)
    return str_buf.value.decode("utf-8")

  def SetAnnotationText(self, lock: T_ReadHandle, text: str):
    """Save the text of an annotation object."""
    self.dll.ModellingSetAnnotationText(lock, text.encode("utf-8"))

  def GetAnnotationSize(self, lock: T_ReadHandle) -> float:
    """Get the size of an annotation."""
    # This wrapper just provides type hints.
    return self.dll.ModellingGetAnnotationSize(lock)

  def SetAnnotationSize(self, lock: T_ReadHandle, size: float):
    """Set the size of an annotation."""
    self.dll.ModellingSetAnnotationSize(lock, size)

  def GetAnnotationTextColour(self, lock: T_ReadHandle) -> tuple[int, int, int, int]:
    """Get the text colour as RGBA."""
    buffer = (ctypes.c_uint8 * 4)()
    self.dll.ModellingGetAnnotationTextColour(lock,ctypes.byref(buffer))
    return [buffer[0], buffer[1], buffer[2], buffer[3]] # type: ignore

  def SetAnnotationTextColour(self, lock: T_ReadHandle, colour: Sequence[int]):
    """Set the text colour with a sequence containing RGBA."""
    rgba_colour = (ctypes.c_uint8 * len(colour))(*colour)
    self.dll.ModellingSetAnnotationTextColour(lock, rgba_colour)

  def RemoveColourMap(self, lock: T_ReadHandle):
    """Remove the colour map from an object."""
    raise_if_version_too_old(
      feature="Removing colour map",
      current_version=self.version,
      required_version=(1, 11)
    )
    result = self.dll.ModellingRemoveColourMap(lock)
    if result != 0:
      # Failing to remove a colour map is probably not the end of the world,
      # so emit a warning instead of an error.
      warnings.warn(
        CApiUnknownWarning(f"Failed to remove colour map. Error code: {result}"))

  def SupportedFeatures(self, lock: T_ReadHandle) -> set[str]:
    """Return a set of the indices of the supported features."""
    supported_feature_names: set[str] = set()
    # Loop based on the feature count to avoid undefined behaviour.
    for index in range(self.dll.ModellingGetFeatureCount()):
      if self.dll.ModellingCanApplyFeature(lock, index):
        supported_feature_names.add(self._feature_index_to_name(index))

    return supported_feature_names

  def GetDisplayedFeature(self, lock: T_ReadHandle) -> str:
    """Get the displayed feature."""
    feature_id = self.dll.ModellingGetDisplayedFeature(lock)
    return self._feature_index_to_name(feature_id)

  def SetDisplayedFeature(self, lock: T_ReadHandle, name: str):
    """Set the displayed feature."""
    feature_id = self._feature_name_to_index(name)
    self.dll.ModellingSetDisplayedFeature(lock, feature_id)

  def GetFeatureName(self, index: int) -> str:
    """Get the name of a feature by index."""
    buffer = ctypes.create_string_buffer(0)
    length = self.dll.ModellingGetFeatureName(index, buffer, 0)
    buffer = ctypes.create_string_buffer(length)
    _ = self.dll.ModellingGetFeatureName(index, buffer, length)
    return bytearray(buffer).decode("utf-8")
