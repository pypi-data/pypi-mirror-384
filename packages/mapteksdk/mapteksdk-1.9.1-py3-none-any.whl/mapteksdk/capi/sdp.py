"""Interface for the MDF spatial data processing library.

Warnings
--------
Vendors and clients should not develop scripts or applications against
this module. The contents may change at any time without warning.

"""
###############################################################################
#
# (C) Copyright 2021, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

# pylint: disable=line-too-long
# pylint: disable=invalid-name;reason=Names match C++ names.
import ctypes

from ..errors import ApplicationTooOldError
from .errors import CApiUnknownError
from .types import T_ReadHandle
from .util import raise_if_version_too_old

from .wrapper_base import WrapperBase


class SdpApi(WrapperBase):
  """Access to the application spatial data processing API.

  This should be accessed through get_application_dlls() for new code.
  """
  @staticmethod
  def method_prefix():
    return "Sdp"

  @staticmethod
  def dll_name() -> str:
    return "mdf_sdp"

  def capi_functions(self):
    return [
      # Functions changed in version 0.
      # Format:
      # "name" : (return_type, arg_types)
      {},
      # Functions changed in version 1.
      {"SdpCApiVersion" : (ctypes.c_uint32, None),
       "SdpCApiMinorVersion" : (ctypes.c_uint32, None),
       "SdpRasterSetControlMultiPoint" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_uint32, ]),
      # Functions changed in version 1.12
      "SdpApplyColourScheme" : (ctypes.c_uint8, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint8, ctypes.c_uint8, ctypes.c_char_p, ]),
      },
    ]

  def _apply_colour_scheme(self, lock, scheme: int, attribute_name: str, primitive_type: int):
    raise_if_version_too_old(
      "Applying a colour scheme",
      self.version,
      (1, 12),
    )

    result = self.dll.SdpApplyColourScheme(
      lock,
      scheme,
      primitive_type,
      attribute_name.encode("utf-8")
    )

    if result == 6:
      raise ApplicationTooOldError(
        "The application does not support the selected colour scheme."
      )
    if result != 0:
      raise CApiUnknownError("Failed to set colour scheme.")

  def CApiVersion(self):
    """Returns the API version for the sdp DLL."""
    raise_if_version_too_old("Spatial data processing", self.version, (1, 3))

    return self.dll.SdpCApiVersion()

  def CApiMinorVersion(self):
    """Returns the minor API version for the sdp DLL."""
    raise_if_version_too_old("Spatial data processing", self.version, (1, 3))

    return self.dll.SdpCApiMinorVersion()

  def RasterSetControlMultiPoint(self, lock, world_points, image_points):
    """Set raster control using the perspective algorithm which takes
    eight or more world and image points.

    Parameters
    ----------
    world_points : numpy.ndarray
      The world points to use to set the control.
    image_points : numpy.ndarray
      The image points to use to set the control.

    """
    raise_if_version_too_old("Multi point raster association",
                             self.version,
                             (1, 3))

    # Use the minimum size as the point count.
    point_count = min(world_points.shape[0], image_points.shape[0])
    if point_count < 8:
      raise ValueError("Multi point association requires at least eight points, "
                       f"given: {point_count}")

    c_image_points = (ctypes.c_double * (point_count * 2))()
    c_image_points[:] = image_points.astype(ctypes.c_double, copy=False).reshape(-1)
    c_world_points = (ctypes.c_double * (point_count * 3))()
    c_world_points[:] = world_points.astype(ctypes.c_double, copy=False).reshape(-1)

    result = self.dll.SdpRasterSetControlMultiPoint(lock,
                                                    c_image_points,
                                                    c_world_points,
                                                    point_count)

    if result == 3:
      raise ValueError("Failed to associate raster: Positioning error")
    if result != 0:
      raise CApiUnknownError("Failed to set multi-point registration")

  def ApplyPointColourScheme(self, lock, scheme: int, attribute_name: str):
    """Apply a colour scheme based on point attributes.

    Parameters
    ----------
    lock
      Open read write lock on the object to apply the scheme to.
    scheme
      ID of the scheme to apply.
    attribute_name
      The name of the point attribute to colour by.
    """
    self._apply_colour_scheme(lock, scheme, attribute_name, 0)

  def ApplyEdgeColourScheme(self, lock, scheme: int, attribute_name: str):
    """Apply a colour scheme based on edge attributes.

    Parameters
    ----------
    lock
      Open read write lock on the object to apply the scheme to.
    scheme
      ID of the scheme to apply.
    attribute_name
      The name of the edge attribute to colour by.
    """
    self._apply_colour_scheme(lock, scheme, attribute_name, 1)

  def ApplyFacetColourScheme(self, lock, scheme: int, attribute_name: str):
    """Apply a colour scheme based on facet attributes.

    Parameters
    ----------
    lock
      Open read write lock on the object to apply the scheme to.
    scheme
      ID of the scheme to apply.
    attribute_name
      The name of the facet attribute to colour by.
    """
    self._apply_colour_scheme(lock, scheme, attribute_name, 2)

  def ApplyCellColourScheme(self, lock, scheme: int, attribute_name: str):
    """Apply a colour scheme based on cell attributes.

    Parameters
    ----------
    lock
      Open read write lock on the object to apply the scheme to.
    scheme
      ID of the scheme to apply.
    attribute_name
      The name of the facet attribute to colour by.
    """
    self._apply_colour_scheme(lock, scheme, attribute_name, 3)

  def ApplyBlockColourScheme(self, lock, scheme: int, attribute_name: str):
    """Apply a colour scheme based on block attributes.

    Parameters
    ----------
    lock
      Open read write lock on the object to apply the scheme to.
    scheme
      ID of the scheme to apply.
    attribute_name
      The name of the block attribute to colour by.
    """
    self._apply_colour_scheme(lock, scheme, attribute_name, 4)
