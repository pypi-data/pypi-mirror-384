"""Interface for raster registration."""
###############################################################################
#
# (C) Copyright 2023, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import typing

from .errors import RegistrationTypeNotSupportedError

if typing.TYPE_CHECKING:
  from .base import Topology
  from .images import Raster
  import sys
  if sys.version_info >= (3, 11):
    from typing import Self
  else:
    Self = typing.Any

class RasterRegistration:
  """Interface for raster registration.

  This is useful for type checking.

  Warnings
  --------
  Vendors and clients should not attempt to create classes which implement
  this interface. This class is primarily included in the public
  interface for type checking purposes. You should use the subclasses
  defined in image_registration.py.
  """
  def __init__(self):
    self.__raster: Raster | None = None

  @property
  def raster(self) -> Raster | None:
    """The raster which this registration is used by.

    The raster returned by the object may be closed.
    This will be None if this registration is not used by any rasters.

    Raises
    ------
    ValueError
      If set when the registration is already being used by a Raster object.
    """
    return self.__raster

  @raster.setter
  def raster(self, new_raster: Raster):
    if self.__raster is not None:
      raise ValueError("Cannot assign raster registration to multiple rasters.")
    self.__raster = new_raster

  @property
  def is_valid(self) -> bool:
    """True if the object is valid."""
    try:
      self.raise_if_invalid()
    except ValueError:
      return False
    return True

  def raise_if_invalid(self):
    """Checks if the registration is invalid.

    Raises a ValueError if the registration is detected to be invalid.

    If is_valid is False then calling this function will raise a ValueError
    containing information on why the registration is considered invalid.

    Raises
    ------
    ValueError
      If the raster is invalid.
    """
    raise NotImplementedError

  def copy(self) -> Self:
    """Create a copy of this object.

    As of mapteksdk 1.6, a RasterRegistration object can only be associated
    with one object. Thus a copy is made when attempting to copy registration
    from one object to another. This function performs this copy.

    Returns
    -------
    Self
      A copy of this object. This copies everything except the link
      to the associated object, allowing for the copy to be associated
      with a different object.

    Raises
    ------
    ValueError
      If the registration is invalid.
    RuntimeError
      If the registration type doesn't support being copied.
    """
    raise NotImplementedError

  def _register(
      self, raster: Raster, topology: Topology, desired_index: int) -> int:
    """Use this object to register a raster with a DataObject.

    Parameters
    ----------
    raster
      The raster to register to the object.
    topology
      The Topology subclass to register the raster to.
    desired_index
      The desired raster index.

    Returns
    -------
    int
      The actual raster index given to the associated raster.
      This will be the desired_index if it is available, otherwise it will be
      a different available index

    Notes
    -----
    This raises RegistrationTypeNotSupportedError by default. Child classes
    should override this function.

    Raises
    ------
    RegistrationTypeNotSupportedError
      If this registration type is not supported by the given data_object.
    """
    raise RegistrationTypeNotSupportedError(type(self))

  def _save(self):
    """Save the registration to the application.

    This should not be called directly. Call save on the Raster
    object instead.
    """
    raise NotImplementedError

  @classmethod
  def _load(cls, raster: Raster) -> Self:
    """Load the registration for an open Raster.

    This assumes that the raster uses this type of raster registration.

    Parameters
    ----------
    raster
      Raster to load the registration for. This will also assign this
      raster to the returned RasterRegistration object's raster property.

    Returns
    -------
    Self
      Instance of this class representing the raster registration of
      the given raster.
    """
    raise NotImplementedError
