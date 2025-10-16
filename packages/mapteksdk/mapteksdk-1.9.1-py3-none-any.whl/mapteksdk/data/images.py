"""Image data objects.

Image objects are used to apply complicated textures to other objects.
"""
###############################################################################
#
# (C) Copyright 2020, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import ctypes
import logging
import pathlib
import typing
import warnings

import numpy as np
from PIL import Image

from ..capi import Visualisation, VisualisationApi
from ..internal.data_property import DataProperty, DataPropertyConfiguration
from ..internal.lock import LockType
from ..internal.util import default_type_error_message
from ..internal.view_data_property import (
  ViewDataProperty,
  ViewDataPropertyConfiguration,
)
from .base import DataObject, StaticType
from .errors import ApplicationTooOldError
from .objectid import ObjectID
from .image_registration import (
  RasterRegistrationTwoPoint, RasterRegistrationMultiPoint,
  RasterRegistrationNone, RasterRegistrationUnsupported,
  RasterRegistrationOverride
)
from .image_registration_interface import RasterRegistration

if typing.TYPE_CHECKING:
  from ..common.typing import (
    ColourArray,
    ColourArrayLike,
    ColourArray3d,
    ColourArray3dLike,
  )

log = logging.getLogger("mapteksdk.data")

class Raster(DataObject):
  """Class representing raster images which can be draped onto other objects.

  Topology objects which support raster association possess an associate_raster
  function which accepts a Raster and a RasterRegistration object which allows
  the raster to be draped onto that object.

  Parameters
  ----------
  width
    The width of the raster.
  height
    The height of the raster.
  image
    The path to an image file. The image will be opened using pillow and
    used to populate the pixels, width and height of the raster.
    Alternatively, this can be a PIL.Image.Image object which will be
    used to populate the pixels, width and height of the raster.
    If this argument is specified also specifying the width and height
    arguments will raise an error.

  Raises
  ------
  TypeError
    If image is not a string, pathlib.Path or Pil.Image.Image.
  ValueError
    If image is specified and width or height is specified.
  FileNotFoundError
    If image is the path to a non-existent file.
  PIL.UnidentifiedImageError
    If image is the path to a file which pillow does not recognise as an
    image.
  PIL.DecompressionBombError
    If image is the path to an image file which seems to be a "decompression
    bomb" - a maliciously crafted file intended to crash or otherwise
    disrupt the application when it is imported.

  Notes
  -----
  This object provides a consistent interface to the pixels of the raster image
  regardless of the underlying format. If the underlying format is
  JPEG or another format which does not support alpha, the alpha will always
  be read as 255 and any changes to the alpha components will be ignored.

  See Also
  --------
  mapteksdk.data.facets.Surface.associate_raster: associate a raster with
    a surface.
  :documentation:`raster` : Help page for this class.

  Examples
  --------
  Create a Raster sourcing the dimensions and pixels of the raster from
  a file called image.png.

  >>> from mapteksdk.project import Project
  >>> from mapteksdk.data import Raster
  >>> project = Project()
  >>> # Raster typically have a path of None because they are associated
  >>> # with other objects.
  >>> with project.new(None, Raster(image="path/to/image.jpg")) as raster:
  ...     # Perform operations on the raster here and associate it with
  ...     # an object.
  ...     pass
  """
  def __init__(
      self,
      object_id: ObjectID[Raster] | None=None,
      lock_type: LockType=LockType.READWRITE,
      width: int | None=None,
      height: int | None=None,
      *,
      image: str | Image.Image | pathlib.Path | None=None):
    self.__is_new: bool = not object_id
    self.__error_on_access_pixels: bool = False
    self.__dimensions: tuple[int, int] | None = None
    self.__registration: RasterRegistration | None = None
    self.__title: str | None = None
    initial_pixels = None
    if self.__is_new:
      if image is not None:
        if width is not None or height is not None:
          message = (
            "Specifying width/height and the image parameter is not supported. "
            "To resize the loaded image, use the resize() function.")
          raise ValueError(message)
        if isinstance(image, Image.Image):
          initial_pixels = self.__construct_from_pillow_image(image)
        else:
          initial_pixels = self.__construct_from_image_path(image)
      else:
        initial_pixels = self.__construct_from_width_and_height(width, height)

      try:
        assert self.__dimensions is not None
        object_id = ObjectID(self._visualisation().NewRaster2D(
          self.__dimensions[0], self.__dimensions[1], False))
      except ctypes.ArgumentError as error:
        raise TypeError("Width and height must be integers. "
                        f"Given dimensions: {self.__dimensions}") from error
    super().__init__(object_id, lock_type)

    def read_pixel_count(lock):
      """Read the pixel count for a raster."""
      width, height = self._visualisation().ReadRaster2DDimensions(lock)
      return width * height

    # This doesn't set save_function because
    # self._visualisation().SetRaster2DPixels does not return a RW array, so
    # it is not compatible with DataProperty.
    # The save must be handled externally to DataProperty.
    self.__pixels: DataProperty = DataProperty(
      self._lock,
      DataPropertyConfiguration(
        name="pixels",
        dtype=ctypes.c_uint8,
        default=0,
        column_count=4,
        load_function=self._visualisation().GetRaster2DPixels,
        save_function=None,
        cached_primitive_count_function=lambda: self.pixel_count,
        primitive_count_function=read_pixel_count,
        set_primitive_count_function=None,
        is_colour_property=True,
        immutable=False
      ),
      initial_values=initial_pixels
    )

    self.__pixels_2d: ViewDataProperty = ViewDataProperty(
      ViewDataPropertyConfiguration(
        "pixels 2d",
        self.__pixels,
        lambda: (self.height, self.width, 4)
      )
    )

  def __construct_from_width_and_height(
      self,
      width: int | None,
      height: int | None
      ) -> np.ndarray:
    """Initialises the Raster to an empty image with the specified dimensions.

    In this case, empty indicates all pixels are set to transparent black.

    Parameters
    ----------
    width
      The width of the raster.
    height
      The height of the raster.
    """
    # :TODO: 2021-09-14 SDK-588: Change these cases
    # to raise a DegenerateTopologyError.
    if width is None:
      message = ("Width default argument is deprecated "
                "and will be removed in a future version.")
      warnings.warn(DeprecationWarning(message))
      width = 1
    if height is None:
      message = ("Width default argument is deprecated "
                "and will be removed in a future version.")
      warnings.warn(DeprecationWarning(message))
      height = 1
    if width < 1:
      raise ValueError(f"Invalid width: {width}. Must be greater than zero.")
    if height < 1:
      raise ValueError(
        f"Invalid height: {height}. Must be greater than zero.")

    self.__dimensions = (width, height)

    return np.zeros((self.height * self.width, 4), dtype=ctypes.c_uint8)

  def __construct_from_image_path(self, image_path: str | pathlib.Path
      ) -> np.ndarray:
    """Populates the raster based on the image at the specified path.

    The pixels of the image will be read from the file using pillow and assigned
    to the pixels of the Raster. The dimensions of the image file are
    used to define the dimensions of the raster.

    Parameters
    ----------
    image_path
      Path to the image to use to populate the raster.
    """
    try:
      with Image.open(image_path, "r") as image:
        return self.__construct_from_pillow_image(image)
    except AttributeError as error:
      raise TypeError(f"Invalid image path: {image_path}") from error

  def __construct_from_pillow_image(self, image: Image.Image) -> np.ndarray:
    """Populates the raster using an Image object from pillow (PIL).

    The pixels of the image are assigned to the pixels of the raster. The
    image is also used to define the dimensions of the raster.

    Parameters
    ----------
    image
      The image object to use to populate the Raster.
    """
    # Convert the image to RGBA to match the representation used by the SDK.
    image = image.convert("RGBA")
    pixels = np.array(image)
    pixels = np.flip(pixels, axis=0)
    self.__dimensions = (image.width, image.height)
    return pixels.reshape(-1, 4)

  @staticmethod
  def _visualisation() -> VisualisationApi:
    """Access the Visualisation C API."""
    return Visualisation()

  @classmethod
  def static_type(cls) -> StaticType:
    """Return the type of raster as stored in a Project.

    This can be used for determining if the type of an object is a raster.
    """
    return cls._modelling_api().ImageType()

  @property
  def width(self) -> int:
    """The width of the raster. This is the number of pixels in each row."""
    if self.__dimensions is None:
      self.__dimensions = self._visualisation().ReadRaster2DDimensions(
        self._lock.lock)
    return self.__dimensions[0]

  @property
  def height(self) -> int:
    """The height of the raster. This is the number of pixels in each column."""
    if self.__dimensions is None:
      self.__dimensions = self._visualisation().ReadRaster2DDimensions(
        self._lock.lock)
    return self.__dimensions[1]

  def resize(self, new_width: int, new_height: int, resize_image: bool=True):
    """Resizes the raster to the new width and height.

    Parameters
    ----------
    new_width
      The new width for the raster. Pass None to keep the width unchanged.
    new_height
      The new height for the raster. Pass None to keep the height unchanged.
    resize_image
      If True (default) The raster will be resized to fill the new size using
      a simple nearest neighbour search if the size is reduced, or
      simple bilinear interpolation. This will also change the format
      to JPEG (and hence the alpha component of the pixels will be discarded).
      If False, the current pixels are discarded and replaced with transparent
      white (or white if the format does not support transparency). This will
      not change the underlying format.

    Raises
    ------
    TypeError
      If width or height cannot be converted to an integer.
    ValueError
      If width or height is less than one.
    RuntimeError
      If called when creating a new raster.

    Warnings
    --------
    After calling resize with resize_image=True it is an error to access
    pixels or pixels_2d until the object is closed and reopened.

    Examples
    --------
    Halve the size of all rasters on an object. Note that because
    resize_image is true, the existing pixels will be changed to make
    a smaller version of the image.

    >>> from mapteksdk.project import Project
    >>> project = Project()
    >>> with project.read("surfaces/target") as read_object:
    >>>     for raster in read_object.rasters.values():
    ...         with project.edit(raster) as edit_raster:
    ...             edit_raster.resize(edit_raster.width // 2,
    ...                                edit_raster.height // 2,
    ...                                resize_image=True)
    """
    # Resizing during new causes an access violation.
    if self.__is_new:
      raise RuntimeError("Cannot resize when creating new raster.")
    new_width = int(new_width)
    new_height = int(new_height)

    if new_width < 1 or new_height < 1:
      raise ValueError(f"Invalid size for raster: {new_width}, {new_height}. "
                       "Width and height must be greater than zero.")

    self.__dimensions = (new_width, new_height)

    if resize_image:
      if self.width == new_width or self.height == new_height:
        if self._visualisation().version < (1, 3):
          log.warning("There is a bug in PointStudio 2021 and other "
                      "applications where resizing an image without changing "
                      "both width and height is ignored.")
      self._visualisation().Raster2DResize(self._lock.lock, new_width, new_height)
      self.__pixels.values = None
      self.__error_on_access_pixels = True
    else:
      self.__pixels.values = np.zeros((new_width * new_height, 4))

  @property
  def pixel_count(self) -> int:
    """The total number of pixels in the raster."""
    return self.height * self.width

  @property
  def pixels(self) -> ColourArray:
    """The pixels of the raster.

    This pixels are represented as a numpy array of shape (pixel_count, 4)
    where each row is the colour of a pixel in the form:
    [Red, Green, Blue, Alpha].

    See pixels_2d for the pixels reshaped to match the width and height of
    the raster.

    Raises
    ------
    RuntimeError
      If accessed after calling resize with resize_image = True.

    Examples
    --------
    Accessing the pixels via this function is best when the two dimensional
    nature of the raster is not relevant or useful. The below example shows
    removing the green component from all of the pixels in an raster. Has no
    effect if the object at surfaces/target does not have an associated
    raster.

    >>> from mapteksdk.project import Project
    >>> project = Project()
    >>> with project.read("surfaces/target") as read_object:
    >>>     for raster in read_object.rasters.values():
    ...         with project.edit(raster) as edit_raster:
    ...             edit_raster.pixels[:, 1] = 0
    """
    if self.__error_on_access_pixels:
      raise RuntimeError("Cannot read pixels after resizing with "
                         "resize_image = True. You must close the "
                         "object before accessing pixels.")
    return self.__pixels.values

  @pixels.setter
  def pixels(self, new_pixels: ColourArrayLike):
    self.__pixels.values = new_pixels

  @property
  def pixels_2d(self) -> ColourArray3d:
    """The pixels reshaped to match the width and height of the raster.

    pixels_2d[0][0] is the colour of the pixel in the bottom left hand
    corner of the raster. pixels_2d[i][j] is the colour of the pixel i
    pixels to the right of the bottom left hand corner and j pixels
    above the bottom left hand corner.

    The returned array will have shape (height, width, 4).

    Raises
    ------
    ValueError
      If set using a string which cannot be converted to an integer.
    ValueError
      If set to a value which cannot be broadcast to the right shape.
    TypeError
      If set to a value which cannot be converted to an integer.

    Notes
    -----
    This returns the pixels in an ideal format to be passed to the
    raster.fromarray function in the 3rd party pillow library.

    Examples
    --------
    As pixels_2d allows access to the two dimensional nature of the raster,
    it can allow different transformations to be applied to different
    parts of the raster. The example below performs a different transformation
    to each quarter of the raster. Has no effect if the object at
    surfaces/target has no associated rasters.

    >>> from mapteksdk.project import Project
    >>> project = Project()
    >>> with project.read("surfaces/target") as read_object:
    ...     for raster in read_object.rasters.values():
    ...         with project.edit(raster) as edit_raster:
    ...             width = edit_raster.width
    ...             height = edit_raster.height
    ...             half_width = edit_raster.width // 2
    ...             half_height = edit_raster.height // 2
    ...             # Remove red from the bottom left hand corner.
    ...             edit_raster.pixels_2d[0:half_height, 0:half_width, 0] = 0
    ...             # Remove green from the top left hand corner.
    ...             edit_raster.pixels_2d[half_height:height,
    ...                                   0:half_width, 1] = 0
    ...             # Remove blue from the bottom right hand corner.
    ...             edit_raster.pixels_2d[0:half_height,
    ...                                   half_width:width, 2] = 0
    ...             # Maximizes the red component in the top right hand corner.
    ...             edit_raster.pixels_2d[half_height:height,
    ...                                   half_width:width, 0] = 255
    """
    if self.__error_on_access_pixels:
      raise RuntimeError("Cannot read pixels after resizing with "
                         "resize_image = True. You must close the "
                         "object before accessing pixels.")
    return self.__pixels_2d.values

  @pixels_2d.setter
  def pixels_2d(self, new_pixels_2d: ColourArray3dLike):
    self.pixels_2d[:] = new_pixels_2d

  @property
  def title(self) -> str:
    """The title of the raster.

    This is shown in the manage images panel. Generally this is the name
    of the file the raster was imported from.
    """
    if self.__title is None:
      self.__title = self._load_title()
    return self.__title

  @title.setter
  def title(self, value: str):
    self.__title = str(value)

  def to_pillow(self) -> Image.Image:
    """Returns a Pillow.Image.Image object of the Raster.

    Returns
    -------
    PIL.Image.Image
      A pillow image object with the same pixels as the raster.

    Notes
    -----
    Changing the returned object will not affect the Raster.

    Examples
    --------
    WARNING: These examples are incomplete and will not run by themselves.
    They assume a Project instance called project has been created and that
    raster_id has been set to the ObjectID of a raster object.

    Save the pixels of the raster to a PNG file.

    >>> with project.read(raster_id) as raster:
    ...     pillow_image = raster.to_pillow()
    ...     pillow_image.save(f"{raster.title}.png", "png")

    Show the raster to the user in the standard image viewer.

    >>> with project.read(raster_id) as raster:
    ...     pillow_image = raster.to_pillow()
    ...     pillow_image.show()
    """
    # Flip the pixels. Otherwise the image ends up upside down.
    flipped_pixels = np.flip(self.pixels_2d, axis=0)
    return Image.fromarray(flipped_pixels, mode="RGBA")

  @property
  def registration(self) -> RasterRegistration:
    """Returns the registration for this raster.

    The registration is an object which defines how the raster is draped
    onto Topology Objects.

    If no raster registration is set, this will return a RasterRegistrationNone
    object. If raster registration is set, but the SDK does not support the
    type of registration (or if the application is too old for the SDK to
    read the registration information), it will return a
    RasterRegistrationUnsupported object. Otherwise it will return a
    RasterRegistration subclass representing the existing registration.

    Raises
    ------
    TypeError
      If set to a value which is not a RasterRegistration.
    ValueError
      If set to an invalid RasterRegistration.

    Notes
    -----
    You should not assign to this property directly. Instead pass the
    registration to the associate_raster() function of the object you would
    like to associate the raster with.
    """
    if self.__registration is None:
      self.__registration = self._load_registration_information()
    return self.__registration

  @registration.setter
  def registration(self, value: RasterRegistration):
    if not isinstance(value, RasterRegistration):
      raise TypeError(
        default_type_error_message(
          argument_name="registration",
          actual_value=value,
          required_type=RasterRegistration
        )
      )
    value.raise_if_invalid()
    value.raster = self
    self.__registration = value

  def _save_title(self, title: str):
    """Save the title of the raster to the Project.

    Parameters
    ----------
    title
      The title to save to the Project.
    """
    self._visualisation().RasterSetTitle(self._lock.lock, title)

  def _load_title(self) -> str:
    """Load the title of the raster from the Project.

    Returns
    -------
    str
      The title of the raster.
    """
    return self._visualisation().RasterGetTitle(self._lock.lock)

  def _load_registration_information(self) -> RasterRegistration:
    """Loads the registration information from the project.

    This sets the image points, world points and orientation used
    to register the raster onto an object. This will not override
    any existing values.
    """
    registration_type = self._modelling_api().GetRasterRegistrationType(self._lock.lock)
    registration_types = {
      0 : RasterRegistrationNone,
      3 : RasterRegistrationTwoPoint,
      6 : RasterRegistrationMultiPoint
    }

    # pylint: disable=protected-access
    registration_type = registration_types.get(
      registration_type, RasterRegistrationUnsupported)

    try:
      # :HACK: 2023-04-17 The registration type reported for
      # RasterRegistrationOverride is the same as for RasterRegistrationNone.
      if registration_type is RasterRegistrationNone:
        try:
          return RasterRegistrationOverride._load(self)
        except ValueError:
          pass

      return registration_type._load(self)
    except ApplicationTooOldError:
      # The function in the C API required to load the registration
      # information is not present in the application. Return an
      # unsupported registration.
      return RasterRegistrationUnsupported()

  def _save(self):
    """Saves changes to the raster to the Project."""
    self._raise_if_save_in_read_only()
    if self.__pixels.are_values_cached:
      self._visualisation().SetRaster2DPixels(self._lock.lock, self.pixels,
                                        self.width, self.height)
    if self.__registration is not None:
      registration = self.registration
      registration.raise_if_invalid()
      # pylint: disable=protected-access
      registration._save()

    if self.__title is not None:
      self._save_title(self.__title)
    self._invalidate_properties()

  def _extra_invalidate_properties(self):
    self.__pixels.invalidate()
    self.__pixels_2d.invalidate()
    self.__dimensions = None
    self.__registration = None

  def _record_object_size_telemetry(self):
    self._record_size_for("Pixels", self.pixel_count)
