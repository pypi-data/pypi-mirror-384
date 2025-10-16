"""Functions for importing and exporting data."""
###############################################################################
#
# (C) Copyright 2020, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

from __future__ import annotations

from collections.abc import Callable
import logging
import os
import pathlib
import typing

from PIL import UnidentifiedImageError

from ..capi import DataEngine, Vulcan, DataTransfer
from ..capi.data_transfer import CApiInputNotSupportedError
from ..capi.errors import (
  CApiError,
  CApiCorruptDataError,
)
from ..errors import FileImportError, NoScanDataError
from ..internal.import_operation import ImportOperation
from ..internal.io import validate_path as _validate_path
from ..internal.util import default_type_error_message
from ..internal.world_file import WorldFile, CorruptWorldFileError
from .block_model_definition import BlockModelDefinition
from .base import DataObject, Topology
from .cells import GridSurface
from .containers import VisualContainer
from .coordinate_systems import CoordinateSystem
from .errors import FileCorruptError
from .facets import Surface
from .images import Raster
from .objectid import ObjectID
from .primitives.block_properties import BlockProperties
from .typing import ImportedObject
from .scans import Scan
from .units import DistanceUnit

if typing.TYPE_CHECKING:
  from collections.abc import Sequence

  from .annotations import Text3D
  from .colourmaps import NumericColourMap, StringColourMap
  from .edges import Polyline, Polygon, EdgeNetwork
  from .points import PointSet

  # pylint: disable=abstract-method
  class AnyBlockModel(BlockProperties, DataObject):
    """Used to type hint any block model.

    As a return type, this indicates the function returns an object which
    inherits from DataObject and BlockProperties. The type doesn't exist
    at runtime and is not fully implemented.
    """

LOG = logging.getLogger("mapteksdk.data.io")

_IMAGE_FORMATS: set[str] = {
  ".png",
  ".jpg",
  ".jpeg",
  ".bmp",
  ".tif",
  ".tiff",
  ".tga"
}
"""Image formats which import should delegate to import_image()."""

_EXTENSION_TO_WORLD_EXTENSION: dict[str, str] = {
  ".png" : ".pgw",
  ".jpg" : ".jpw",
  ".jpeg" : ".jpw",
  ".bmp" : ".bpw",
  ".tif" : ".tfw",
  ".tiff" : ".tfw",
}
"""Dictionary which maps image extensions to their world file extensions."""


class _Unspecified:
  """Class representing an input is unspecified.

  All instances of this class compare as equal to each other.
  """
  def __eq__(self, value: object) -> bool:
    return isinstance(value, _Unspecified)


class ImportMissingInputError(Exception):
  """One or more inputs required to import the file are missing."""


def _validate_path_dgd_isis(path: str | os.PathLike) -> pathlib.Path:
  """Alternate validate path for dgd.isis files.

  This format requires two file extensions, so it cannot use the normal
  `_validate_path()` function.
  """
  if not isinstance(path, pathlib.Path):
    path = pathlib.Path(path)
  suffixes = path.suffixes
  if len(suffixes) == 0:
    raise ValueError(
      f"Failed to import '{path}'. Expected the extension to be dgd.isis."
    )
  if len(suffixes) == 1:
    raise ValueError(
      f"Failed to import '{path}'. Expected the extension to be dgd.isis."
    )
  if suffixes[-2].casefold() != ".dgd" or suffixes[-1].casefold() != ".isis":
    raise ValueError(
      f"Failed to import '{path}'. Expected the extension to be dgd.isis."
    )
  return path


def _find_world_file(image_path: pathlib.Path) -> pathlib.Path:
  """Find the world file corresponding to `image_path`."""
  extension = image_path.suffix
  try:
    world_extension = _EXTENSION_TO_WORLD_EXTENSION[extension]
  except KeyError:
    raise FileNotFoundError(
      f"Failed to find world file for: {image_path}"
    ) from None

  return image_path.with_suffix(world_extension)


def _supply_input_safe(function: Callable[[], None], unit_name: str):
  """Supply an input to an import operation safely.

  This will catch any `CApiInputNotSupportedError` raised by `function`
  and emit an `UnusedInputWarning` instead.
  """
  try:
    function()
  except CApiInputNotSupportedError:
    LOG.info(
      "A %s input was applied, but the import did not support it.",
      unit_name
    )

def import_any(
  path: str | pathlib.Path,
  unit: DistanceUnit | None = None,
  coordinate_system: CoordinateSystem | _Unspecified | None  = _Unspecified()
) -> Sequence[ImportedObject[DataObject]]:
  """Import any format supported by the application's import framework.

  Unlike other import functions, the inputs aside from `path` may be ignored
  if the import of the file at `path` does not require that input.

  Parameters
  ----------
  path
    Path to the file to import.
  unit
    The unit to use for the import.
    If None (default), this indicates that the import of this format
    does not require a unit (e.g. The file always stores the values
    in metres or the file contains non-spatial data which units
    do not apply to, such as colour maps).
  coordinate_system
    The coordinate system to use for the import.
    This should be set to None to provide "no coordinate system".
    This is unspecified by default, which indicates that the import of this
    file format does not require a coordinate system (e.g. The coordinate
    system is stored within the file or the file contains non-spatial data
    which coordinate systems do not apply to, such as colour maps).

  Returns
  -------
  Sequence[ImportedObject]
    Sequence of ImportedObject named tuples with one item per imported object.

  Raises
  ------
  FileNotFoundError
    If the file at `path` does not exist.
  ImportMissingInputError
    If the import of the file at `path` requires an input which has not been
    supplied.
    Note that this will be raised in cases where the import requires an
    additional input which cannot be provided through this function.
  FileImportError
    If there was an error importing `path`.
    The error message is often (but not always) provided by the application
    so may be translated into the user's selected language.

  Warns
  -----
  FileImportWarning
    If one or more objects could not be imported correctly.

  Notes
  -----
  This delegates the import of common image formats to the pillow library
  instead of using the application's importer for image formats.
  """
  actual_path = pathlib.Path(path)
  if actual_path.suffix.casefold() in _IMAGE_FORMATS:
    return [import_image(actual_path)]
  with ImportOperation(actual_path, data_transfer=DataTransfer()) as operation:
    if unit is not None:
      _supply_input_safe(lambda: operation.supply_unit(unit), "unit")
    if not isinstance(coordinate_system, _Unspecified):
      _supply_input_safe(lambda: operation.supply_coordinate_system(
        coordinate_system
      ),
      "coordinate system"
    )
    if not operation.are_required_inputs_supplied():
      raise ImportMissingInputError(
        "Not all required inputs were supplied."
      )
    imported_objects = operation.import_all_objects()
  return imported_objects

def import_00t(
  path: str | pathlib.Path,
  unit: DistanceUnit = DistanceUnit.METRE
) -> ObjectID[Surface]:
  """Import a Maptek Vulcan Triangulation file (00t) into the project.

  Parameters
  ----------
  path
    Path to file to import.
  unit
    The unit used when exporting the file.

  Returns
  -------
  ObjectID
    The ID of the imported object.

  Raises
  ------
  FileNotFoundError
    If the file does not exist.
  TypeError
    If path cannot be converted to a pathlib.Path.
    If the unit is not an instance of DistanceUnit.
  RuntimeError
    If there is a problem importing the file.

  Notes
  -----
  The imported object is not automatically placed inside a container.
  A call to project.add_object() is required to add it to a container.

  """
  LOG.info("Importing Vulcan Triangulation (00t): %s", path)

  if not isinstance(path, pathlib.Path):
    path = pathlib.Path(path)

  if not isinstance(unit, DistanceUnit):
    raise TypeError(default_type_error_message("unit", unit, DistanceUnit))

  if not path.is_file():
    raise FileNotFoundError(f"Could not find file: {path}")

  vulcan = Vulcan()

  imported_object = vulcan.Read00tFile(
    str(path).encode("utf-8"), unit.value)

  if imported_object.value == 0:
    message = vulcan.ErrorMessage().decode('utf-8')
    LOG.error(
      "A problem occurred when importing the 00t: %s. %s", path, message)
    raise RuntimeError(message)
  return ObjectID(imported_object)


def export_00t(
  object_id: ObjectID[Surface],
  path: str | pathlib.Path,
  unit: DistanceUnit = DistanceUnit.METRE
):
  """Export a Surface to a Vulcan Triangulation (00t).

  Parameters
  ----------
  object_id
    The ID of the surface to export.
  path
    Where to save the 00t.
  unit
    Unit to use when exporting the file.

  Raises
  ------
  TypeError
    If the unit is not a DistanceUnit.
  RuntimeError
    If there was a problem exporting the file.

  Notes
  -----
  Changed in version 1.4 - This function no longer returns a value.
  Prior to 1.4, this would return True on success and raise an exception
  on failure (It could never return False).
  """
  LOG.info("Exporting Vulcan Triangulation (00t): %s", path)
  if not isinstance(path, pathlib.Path):
    path = pathlib.Path(path)

  if not isinstance(unit, DistanceUnit):
    raise TypeError(default_type_error_message("unit", unit, DistanceUnit))

  vulcan = Vulcan()
  result = vulcan.Write00tFile(object_id.handle,
                                 str(path).encode('utf-8'),
                                 unit.value)
  if not result:
    # This may be because the type of object can't be exported to a 00t or
    # because there was a problem trying to read the object or write to the
    # 00t.
    message = vulcan.ErrorMessage().decode('utf-8')
    LOG.error("The 00t could not be exported: %s. %s", path, message)
    raise RuntimeError(message)


def import_bmf(
  path: str | pathlib.Path,
  unit: DistanceUnit = DistanceUnit.METRE
) -> ObjectID[AnyBlockModel]:
  """Import a Maptek Block Model File (bmf) into the project.

  Parameters
  ----------
  path
    Path to file to import.
  unit
    Unit to use when importing the file.

  Returns
  -------
  ObjectID
    The ID of the imported object.

  Raises
  ------
  TypeError
    If path could not be converted to a pathlib.Path.
    If the unit is not an instance of DistanceUnit.
  FileNotFoundError
    If the file does not exist.
  RuntimeError
    If there is a problem importing the file.

  Notes
  -----
  The ObjectID returned by this function is type hinted as
  ObjectID[BlockProperties, DataObject] because all supported block models are
  expected to inherit from BlockProperties and DataObject. This means
  autocompletion should only suggest properties which are shared by all
  block models. The type hint may be incorrect if the bmf contains a block model
  not supported by the SDK.

  """
  LOG.info("Importing Vulcan Block Model (bmf): %s", path)

  if not isinstance(path, pathlib.Path):
    path = pathlib.Path(path)

  if not isinstance(unit, DistanceUnit):
    raise TypeError(default_type_error_message("unit", unit, DistanceUnit))

  if not path.is_file():
    raise FileNotFoundError(f"Could not find file: {path}")

  vulcan = Vulcan()
  imported_object = vulcan.ReadBmfFile(str(path).encode('utf-8'),
                                         unit.value)
  if imported_object.value == 0:
    message = vulcan.ErrorMessage().decode('utf-8')
    LOG.error("A problem occurred when importing the BMF: %s", message)
    raise RuntimeError(message)
  return ObjectID(imported_object)


def export_bmf(
  object_id: ObjectID[BlockProperties | DataObject],
  path: str | pathlib.Path,
  unit: DistanceUnit = DistanceUnit.METRE
):
  """Export a block model to a Maptek Block Model File (bmf).

  Parameters
  ----------
  object_id
    The ID of the block model to export as a bmf.
  path
    Where to save the bmf file.
  unit
    Unit to use when exporting the file.

  Returns
  -------
  bool
    True if the export was a success. This never returns false - if
    the import fails an exception will be raised.

  Raises
  ------
  TypeError
    If unit is not a DistanceUnit.
  RuntimeError
    If there was a problem exporting the file.

  Notes
  -----
  Changed in version 1.4 - This function no longer returns a value.
  Prior to 1.4, this would return True on success and raise an exception
  on failure (It could never return False).
  """
  LOG.info("Exporting Vulcan Block Model (bmf): %s", path)
  if not isinstance(path, pathlib.Path):
    path = pathlib.Path(path)

  if not isinstance(unit, DistanceUnit):
    raise TypeError(default_type_error_message("unit", unit, DistanceUnit))

  vulcan = Vulcan()
  result = vulcan.WriteBmfFile(object_id.handle,
                                 str(path).encode('utf-8'),
                                 unit.value)
  if not result:
    # This may be because the type of object can't be exported to a bmf or
    # because there was a problem trying to read the object or write to the
    # bmf.
    message = vulcan.ErrorMessage().decode('utf-8')
    LOG.error("The BMF could not be exported to %s. %s", path, message)
    raise RuntimeError(message)


def import_bdf(
  path: os.PathLike | str,
  unit: DistanceUnit = DistanceUnit.METRE
) -> ObjectID[BlockModelDefinition]:
  """Import a block model definition from a bdf file.

  Parameters
  ----------
  path
    The path to the bdf file to import.

  Returns
  -------
  ObjectID[BlockModelDefinition]
    Object ID of the imported block model definition. This will not be placed
    in the project. Use `Project.add_object()` to set its path in the project.
  unit
    The unit to read the imported bdf in. This is metres by default.

  Raises
  ------
  FileNotFoundError
    If the file does not exist or is a directory.
  FileCorruptError
    If the file is not a bdf file or the file is corrupt.
  RuntimeError
    If an unknown error occurs.
  """
  if not isinstance(path, pathlib.Path):
    path = pathlib.Path(path)

  try:
    return ObjectID(Vulcan().ImportBlockModelDefinition(path, unit))
  except CApiCorruptDataError as error:
    raise FileCorruptError(str(error)) from None
  except CApiError as error:
    # Suppress the internal C API errors from appearing in the stack trace
    # but reuse the error message.
    raise RuntimeError(str(error)) from None

def export_bdf(
  oid: ObjectID[BlockModelDefinition],
  path: os.PathLike | str,
  unit: DistanceUnit = DistanceUnit.METRE
):
  """Export a block model definition into a bdf file.

  Parameters
  ----------
  oid
    Object ID of the block model definition to export.
  path
    Path to the file to export the block model definition to.
  unit
    Unit to export the BDF in. This is metres by default.

  Raises
  ------
  TypeError
    If `oid` is not a block model definition object.
  RuntimeError
    If an unknown error occurs.
  ValueError
    If `unit` is not supported by the connected application.
  """
  if not isinstance(path, pathlib.Path):
    path = pathlib.Path(path)

  try:
    if not oid.is_a(BlockModelDefinition):
      raise TypeError(f"Cannot export a {oid.type_name} to a bdf file.")
    Vulcan().ExportBlockModelDefinition(oid, path, unit)
  except ValueError:
    # Re-raise the exception with additional information regarding what the
    # unsupported unit was.
    raise ValueError(
      "The connected application does not support exporting block model "
      f"definitions with unit: '{unit}'."
    ) from None
  except CApiError as error:
    # Suppress the internal C API errors from appearing in the stack trace
    # but reuse the error message.
    raise RuntimeError(str(error)) from None


def import_maptekobj(path: str | pathlib.Path
    ) -> ObjectID[DataObject]:
  """Import a Maptek Object file (maptekobj) into the project.

  Parameters
  ----------
  path
    Path to file to import.

  Returns
  -------
  ObjectID
    The ID of the imported object.

  Raises
  ------
  FileNotFoundError
    If the file does not exist.
  RuntimeError
    If there is a problem importing the file.
  TypeError
    If path cannot be converted to a pathlib.Path object.

  """
  LOG.info("Importing Maptek Object file (maptekobj): %s", path)

  if not isinstance(path, pathlib.Path):
    path = pathlib.Path(path)

  if not path.is_file():
    raise FileNotFoundError(f"Could not find file: {path}")

  data_engine = DataEngine()
  imported_object = data_engine.ReadMaptekObjFile(
    str(path).encode('utf-8'))
  if imported_object.value == 0:
    last_error = data_engine.ErrorMessage()
    LOG.error("A problem occurred (%s) when importing %s", last_error, path)
    raise RuntimeError(last_error)

  return ObjectID(imported_object)


def export_maptekobj(
    object_id: ObjectID[DataObject],
    path: str | pathlib.Path):
  """Export an object to a Maptek Object file (maptekobj).

  Unlike 00t and bmf any object (even containers) can be exported to a maptekobj
  file.

  Parameters
  ----------
  object_id
    The ID of the object to export.
  path
    Where to save the maptekobj file.

  Returns
  -------
  bool
    True if the export was a success. This never returns false - if
    the import fails an exception will be raised.

  Raises
  ------
  RuntimeError
    If there was a problem exporting the file.

  Notes
  -----
  Changed in version 1.4 - This function no longer returns a value.
  Prior to 1.4, this would return True on success and raise an exception
  on failure (It could never return False).
  """
  LOG.info("Exporting Maptek Object file (maptekobj): %s", path)
  if not isinstance(path, pathlib.Path):
    path = pathlib.Path(path)

  data_engine = DataEngine()
  result = data_engine.CreateMaptekObjFile(
    str(path).encode('utf-8'), object_id.handle)
  if not result:
    last_error = data_engine.ErrorMessage()
    LOG.error("A problem occurred (%s) when importing %s", last_error, path)
    raise RuntimeError(last_error)

def import_hgt(path: str | os.PathLike) -> ImportedObject[GridSurface]:
  """Import a HGT file.

  This format was used by NASA's Shuttle Radar Topography Mission.

  Parameters
  ----------
  path
    The path to the HGT file to read.

  Returns
  -------
  ImportedObject
    The grid surface imported from the hgt file.

  Raises
  ------
  ValueError
    If `path` does not have the .hgt extension.
  FileNotFoundError
    If there is no file at `path`.
  FileImportError
    If there was an error importing `path`.
    The error message is often (but not always) provided by the application
    so may be translated into the user's selected language.
  ImportFormatNotSupportedError
    If the connected application does not support importing this format.

  Warns
  -----
  FileImportWarning
    If one or more objects could not be imported correctly.
  """
  path = _validate_path(path, ".hgt")
  with ImportOperation(path, data_transfer=DataTransfer()) as operation:
    oids = operation.import_all_objects()
  if len(oids) == 0:
    raise FileImportError(
      f"Failed to import: {path}"
    )
  # There should only be one object per hgt file.
  return oids[0]

def import_kml(path: str | os.PathLike) -> ImportedObject[VisualContainer]:
  """Import a KML file.

  KML stands for Keyhole Markup Language.

  Parameters
  ----------
  path
    The path to the KML file to read.

  Returns
  -------
  ImportedObject
    A container containing all of the imported objects.

  Raises
  ------
  ValueError
    If `path` does not have the .kml extension.
  FileNotFoundError
    If there is no file at `path`.
  FileImportError
    If there was an error importing `path`.
    The error message is often (but not always) provided by the application
    so may be translated into the user's selected language.
  ImportFormatNotSupportedError
    If the connected application does not support importing this format.

  Warns
  -----
  FileImportWarning
    If one or more objects could not be imported correctly.
  """
  path = _validate_path(path, ".kml")
  with ImportOperation(path, data_transfer=DataTransfer()) as operation:
    oids = operation.import_all_objects()
  if len(oids) == 0:
    raise FileImportError(
      f"Failed to import: {path}"
    )
  # There should only be one object per KML file which is the container.
  return oids[0]

def import_obj(
  path: str | os.PathLike,
  *,
  coordinate_system: CoordinateSystem | None = None,
  unit: DistanceUnit = DistanceUnit.METRE,
) -> Sequence[ImportedObject[Topology]]:
  """Import from an .obj file.

  This file type is used to exchange 3D models intended for visualization,
  3D printing, and extended reality applications. The data consists of sets
  of adjacent triangles that together define a tessellated geometric surface.

  More details can be found on the US Library of Congress Reference page for
  the format here:
  https://www.loc.gov/preservation/digital/formats/fdd/fdd000507.shtml

  Parameters
  ----------
  path
    The path to the .obj file to read.
  coordinate_system
    The coordinate system which the imported objects are in.
    Setting this parameter does not trigger a coordinate system conversion.
    This is no coordinate system by default.
  unit
    The unit the file is stored in. This is metres by default.

  Returns
  -------
  Sequence[ImportedObject]
    A container containing the imported objects.

  Raises
  ------
  ValueError
    If `path` does not have the .obj extension.
  FileNotFoundError
    If there is no file at `path`.
  FileImportError
    If there was an error importing `path`.
    The error message is often (but not always) provided by the application
    so may be translated into the user's selected language.
  ImportFormatNotSupportedError
    If the connected application does not support importing this format.

  Warns
  -----
  FileImportWarning
    If one or more objects could not be imported correctly.
  """
  path = _validate_path(path, ".obj")

  with ImportOperation(path, data_transfer=DataTransfer()) as operation:
    operation.supply_unit(unit)
    operation.supply_coordinate_system(coordinate_system)
    return operation.import_all_objects()

def import_shp(
  path: str | os.PathLike,
  coordinate_system: CoordinateSystem | None = None,
) -> ImportedObject[Topology]:
  """Import an ESRI shapefile.

  A shapefile stores non-topological geometry and attribute information for
  the spatial features in a data set.

  All shapes within the file will be merged into a single object.

  For more details, see the ESRI documentation for the format:
  https://www.esri.com/content/dam/esrisites/sitecore-archive/Files/Pdfs/library/whitepapers/pdfs/shapefile.pdf

  Parameters
  ----------
  path
    The path to the .shp file to read.
  coordinate_system
    The coordinate system which the imported objects are in.
    Setting this parameter does not trigger a coordinate system conversion.
    This is no coordinate system by default.

  Returns
  -------
  ImportedObject
    The imported object. All shapes in the shapefile will be merged into a
    single object.

  Raises
  ------
  ValueError
    If `path` does not have the .shp extension.
  FileNotFoundError
    If there is no file at `path`.
  FileImportError
    If there was an error importing `path`.
    The error message is often (but not always) provided by the application
    so may be translated into the user's selected language.
  ImportFormatNotSupportedError
    If the connected application does not support importing this format.

  Warns
  -----
  FileImportWarning
    If one or more objects could not be imported correctly.
  """
  path = _validate_path(path, ".shp")
  with ImportOperation(path, data_transfer=DataTransfer()) as operation:
    try:
      operation.supply_unit(DistanceUnit.METRE)
    except CApiInputNotSupportedError:
      # The shapefile importer ignores the unit.
      # If the unit is removed in a future application version, ignore the
      # resulting error.
      pass
    operation.supply_coordinate_system(coordinate_system)
    # There is also a "Merge choice" input which controls whether the objects
    # are combined into a single one. Python leaves it to the default
    # (True).
    oids = operation.import_all_objects()
  if len(oids) == 0:
    raise FileImportError(
      f"Failed to import: {path}"
    )
  return oids[0]


def import_ply(
  path: str | os.PathLike
) -> ImportedObject[Surface] | ImportedObject[Scan] | ImportedObject[PointSet]:
  """Import a Stanford University PLY file.

  PLY files are designed to provide a format that is simple and easy to
  implement but general enough to be useful for a wide range of models.

  This will import the basic geometry defined in the importer, but because
  the format is too general any other information in the file may not be
  imported.

  Parameters
  ----------
  path
    The path to the file to import.

  Returns
  -------
  ImportedObject
    The imported object.
    Depending on how the geometry is defined in the file, this will either be
    a `Surface`, `Scan` or a `PointSet`.

  Raises
  ------
  ValueError
    If `path` does not have the .ply extension.
  FileNotFoundError
    If there is no file at `path`.
  FileImportError
    If there was an error importing `path`.
    The error message is often (but not always) provided by the application
    so may be translated into the user's selected language.
  ImportFormatNotSupportedError
    If the connected application does not support importing this format.

  Warns
  -----
  FileImportWarning
    If one or more objects could not be imported correctly.
  """
  path = _validate_path(path, ".ply")
  with ImportOperation(path, data_transfer=DataTransfer()) as operation:
    oids = operation.import_all_objects()
  if len(oids) == 0:
    raise FileImportError(
      f"Failed to import: {path}"
    )
  # A PLY file only contains a single object.
  return oids[0]


def import_3dv(
  path: str | os.PathLike,
  *,
  coordinate_system: CoordinateSystem | None = None,
) -> ImportedObject[Scan]:
  """Import a 3dv file.

  This imports files in the Optech gridded ASCII scan format

  Parameters
  ----------
  path
    The path to the file to import.
  coordinate_system
    The coordinate system which the imported objects are in.
    Setting this parameter does not trigger a coordinate system conversion.
    This is no coordinate system by default.

  Returns
  -------
  ImportedObject
    The imported scan.

  Raises
  ------
  NoScanDataError
    If the scan file contains no scan data (e.g. It is image-only).
  ValueError
    If `path` does not have the .3dv extension.
  FileNotFoundError
    If there is no file at `path`.
  FileImportError
    If there was an error importing `path`.
    The error message is often (but not always) provided by the application
    so may be translated into the user's selected language.
  ImportFormatNotSupportedError
    If the connected application does not support importing this format.

  Warns
  -----
  FileImportWarning
    If one or more objects could not be imported correctly.
  """
  path = _validate_path(path, ".3dv")
  with ImportOperation(path, data_transfer=DataTransfer()) as operation:
    operation.supply_coordinate_system(coordinate_system)
    imported_objects = operation.import_all_objects()
  if len(imported_objects) == 0:
    raise FileImportError(
      f"Failed to import: {path}"
    )
  # A 3dv file only contains a single object.
  imported_object = imported_objects[0]
  if not imported_object.oid.is_a(Scan):
    DataEngine().DeleteObject(imported_object.oid.handle)
    raise NoScanDataError.from_path(path)

  return imported_object


def import_3dp(
  path: str | os.PathLike,
) -> ImportedObject[Scan]:
  """Imports a Maptek 3dp file.

  The scan format used by Maptek's 4400 series of scanners. Any scan in
  PointStudio can be exported as a 3dp which means 3dp files may not
  come from scanners.

  Parameters
  ----------
  path
    The path to the file to import.

  Returns
  -------
  ImportedObject
    The imported scan.

  Raises
  ------
  NoScanDataError
    If the scan file contains no scan data (e.g. It is image-only).
  ValueError
    If `path` does not have the .3dp extension.
  FileNotFoundError
    If there is no file at `path`.
  FileImportError
    If there was an error importing `path`.
    The error message is often (but not always) provided by the application
    so may be translated into the user's selected language.
  ImportFormatNotSupportedError
    If the connected application does not support importing this format.

  Warns
  -----
  FileImportWarning
    If one or more objects could not be imported correctly.
  """
  path = _validate_path(path, ".3dp")
  with ImportOperation(path, data_transfer=DataTransfer()) as operation:
    imported_objects = operation.import_all_objects()
  if len(imported_objects) == 0:
    raise FileImportError(
      f"Failed to import: {path}"
    )
  # A 3dp file only contains a single scan.
  imported_object = imported_objects[0]
  if not imported_object.oid.is_a(Scan):
    DataEngine().DeleteObject(imported_object.oid.handle)
    raise NoScanDataError.from_path(path)

  return imported_object


def import_r3s(
  path: str | os.PathLike,
) -> ImportedObject[Scan]:
  """Imports a Maptek r3s file.

  This is the scan format used by Maptek Gen 3 Scanners. Scans cannot be
  exported in this format, so they always come from a scanner.

  Parameters
  ----------
  path
    The path to the file to import.

  Returns
  -------
  ImportedObject
    The imported scan.

  Raises
  ------
  NoScanDataError
    If the scan file contains no scan data (e.g. It is image-only).
  ValueError
    If `path` does not have the .r3s extension.
  FileNotFoundError
    If there is no file at `path`.
  FileImportError
    If there was an error importing `path`.
    The error message is often (but not always) provided by the application
    so may be translated into the user's selected language.
  ImportFormatNotSupportedError
    If the connected application does not support importing this format.

  Warns
  -----
  FileImportWarning
    If one or more objects could not be imported correctly.
  """
  path = _validate_path(path, ".r3s")
  with ImportOperation(path, data_transfer=DataTransfer()) as operation:
    imported_objects = operation.import_all_objects()
  if len(imported_objects) == 0:
    raise FileImportError(
      f"Failed to import: {path}"
    )
  # An r3s file only contains a single scan.
  imported_object = imported_objects[0]
  if not imported_object.oid.is_a(Scan):
    DataEngine().DeleteObject(imported_object.oid.handle)
    raise NoScanDataError.from_path(path)
  return imported_object


def import_3dr(
  path: str | os.PathLike,
  *,
  coordinate_system: CoordinateSystem | None = None,
) -> ImportedObject[Scan]:
  """Import a 3dr file.

  This is the scan format used by Maptek's 8000 series scanners. Scans cannot
  be exported in this format, so they always come from a scanner.

  Parameters
  ----------
  path
    The path to the file to import.
  coordinate_system
    The coordinate system which the imported objects are in.
    Setting this parameter does not trigger a coordinate system conversion.
    This is no coordinate system by default.

  Returns
  -------
  ImportedObject
    The imported scan.

  Raises
  ------
  NoScanDataError
    If the scan file contains no scan data (e.g. It is image-only).
  ValueError
    If `path` does not have the .3dr extension.
  FileNotFoundError
    If there is no file at `path`.
  FileImportError
    If there was an error importing `path`.
    The error message is often (but not always) provided by the application
    so may be translated into the user's selected language.
  ImportFormatNotSupportedError
    If the connected application does not support importing this format.

  Warns
  -----
  FileImportWarning
    If one or more objects could not be imported correctly.
  """
  path = _validate_path(path, ".3dr")
  with ImportOperation(path, data_transfer=DataTransfer()) as operation:
    operation.supply_coordinate_system(coordinate_system)
    imported_objects = operation.import_all_objects()
  if len(imported_objects) == 0:
    raise FileImportError(
      f"Failed to import: {path}"
    )
  # A 3dr file only contains a single object.
  imported_object = imported_objects[0]
  if not imported_object.oid.is_a(Scan):
    DataEngine().DeleteObject(imported_object.oid.handle)
    raise NoScanDataError.from_path(path)
  return imported_object


def import_3di(
  path: str | os.PathLike,
  *,
  coordinate_system: CoordinateSystem | None = None,
  unit: DistanceUnit = DistanceUnit.METRE,
) -> ImportedObject[Scan]:
  """Import a 3di file.

  One of Maptek's proprietary scan formats. This is a legacy format.

  Parameters
  ----------
  path
    The path to the file to import.
  coordinate_system
    The coordinate system which the imported objects are in.
    Setting this parameter does not trigger a coordinate system conversion.
    This is no coordinate system by default.
  unit
    The unit the file is stored in. This is metres by default.

  Returns
  -------
  ImportedObject
    The imported scan.

  Raises
  ------
  NoScanDataError
    If the scan file contains no scan data (e.g. It is image-only).
  ValueError
    If `path` does not have the .3di extension.
  FileNotFoundError
    If there is no file at `path`.
  FileImportError
    If there was an error importing `path`.
    The error message is often (but not always) provided by the application
    so may be translated into the user's selected language.
  ImportFormatNotSupportedError
    If the connected application does not support importing this format.

  Warns
  -----
  FileImportWarning
    If one or more objects could not be imported correctly.
  """
  path = _validate_path(path, ".3di")
  with ImportOperation(path, data_transfer=DataTransfer()) as operation:
    operation.supply_coordinate_system(coordinate_system)
    operation.supply_unit(unit)
    imported_objects = operation.import_all_objects()
  if len(imported_objects) == 0:
    raise FileImportError(
      f"Failed to import: {path}"
    )
  # A 3di file only contains a single object.
  imported_object = imported_objects[0]
  if not imported_object.oid.is_a(Scan):
    DataEngine().DeleteObject(imported_object.oid.handle)
    raise NoScanDataError.from_path(path)
  return imported_object


def import_las_scan(
  path: str | os.PathLike,
  *,
  coordinate_system: CoordinateSystem | None = None,
  unit: DistanceUnit = DistanceUnit.METRE,
) -> ImportedObject[Scan]:
  """Import a las scan.

  This is an open, binary format specified by the American Society for
  Photogrammetry and Remote Sending.

  More details can be found on the US Library of Congress Reference page for
  the format here:
  https://www.loc.gov/preservation/digital/formats/fdd/fdd000418.shtml

  Parameters
  ----------
  path
    The path to the file to import. This can be a las or a laz file.
  coordinate_system
    The coordinate system which the imported objects are in.
    Setting this parameter does not trigger a coordinate system conversion.
    This is no coordinate system by default.
  unit
    The unit the file is stored in. This is metres by default.
    Some las scan files include information about the units within the file.
    If this information is found, the unit supplied to this parameter will
    be ignored.

  Returns
  -------
  ImportedObject
    The imported scan.

  Raises
  ------
  NoScanDataError
    If the scan file contains no scan data (e.g. It is image-only).
  ValueError
    If `path` does not have the .las or .laz extension.
  FileNotFoundError
    If there is no file at `path`.
  FileImportError
    If there was an error importing `path`.
    The error message is often (but not always) provided by the application
    so may be translated into the user's selected language.
  ImportFormatNotSupportedError
    If the connected application does not support importing this format.

  Warns
  -----
  FileImportWarning
    If one or more objects could not be imported correctly.
  """
  path = _validate_path(path, (".las", ".laz"))
  with ImportOperation(path, data_transfer=DataTransfer()) as operation:
    operation.supply_coordinate_system(coordinate_system)
    operation.supply_unit(unit)
    imported_objects = operation.import_all_objects()
  if len(imported_objects) == 0:
    raise FileImportError(
      f"Failed to import: {path}"
    )
  # A las file only contains a single object.
  imported_object = imported_objects[0]
  if not imported_object.oid.is_a(Scan):
    DataEngine().DeleteObject(imported_object.oid.handle)
    raise NoScanDataError.from_path(path)
  return imported_object


def import_autocad_drawing_file(
  path: str | os.PathLike,
  *,
  coordinate_system: CoordinateSystem | None = None,
  unit: DistanceUnit = DistanceUnit.METRE,
) -> Sequence[
    ImportedObject[
      PointSet | Polyline | Polygon | EdgeNetwork | Surface | Text3D
    ]
  ]:
  """Import an Autodesk AutoCAD drawing file (.dwg).

  These files store 2 or 3 dimensional design data. They can store multiple
  objects of different types in one file.

  Parameters
  ----------
  path
    The path to the file to import.
  coordinate_system
    The coordinate system which the imported objects are in.
    Setting this parameter does not trigger a coordinate system conversion.
    This is no coordinate system by default.
  unit
    The unit the file is stored in. This is metres by default.

  Returns
  -------
  Sequence[ImportedObject]
    A sequence containing the imported objects. This can include
    `PointSet`, `Polyline`, `Polygon`, `EdgeNetwork`, `Surface` or `Text3D`.
    The sequence may contain objects of different types.

  Raises
  ------
  ValueError
    If `path` does not have the .dwg extension.
  FileNotFoundError
    If there is no file at `path`.
  FileImportError
    If there was an error importing `path`.
    The error message is often (but not always) provided by the application
    so may be translated into the user's selected language.
  ImportFormatNotSupportedError
    If the connected application does not support importing this format.

  Warns
  -----
  FileImportWarning
    If one or more objects could not be imported correctly.
  """
  path = _validate_path(path, ".dwg")
  with ImportOperation(path, data_transfer=DataTransfer()) as operation:
    operation.supply_coordinate_system(coordinate_system)
    operation.supply_unit(unit)
    oids = operation.import_all_objects()
  if len(oids) == 0:
    raise FileImportError(
      f"Failed to import: {path}"
    )
  return oids


def import_autocad_exchange_file(
  path: str | os.PathLike,
  *,
  coordinate_system: CoordinateSystem | None = None,
  unit: DistanceUnit = DistanceUnit.METRE,
) -> Sequence[
    ImportedObject[
      PointSet | Polyline | Polygon | EdgeNetwork | Surface | Text3D
    ]
  ]:
  """Import an Autodesk AutoCAD exchange file (.dxf or .dxb).

  These files store 2 or 3 dimensional design data. They can store multiple
  objects of different types in one file.

  Parameters
  ----------
  path
    The path to the file to import.
  coordinate_system
    The coordinate system which the imported objects are in.
    Setting this parameter does not trigger a coordinate system conversion.
    This is no coordinate system by default.
  unit
    The unit the file is stored in. This is metres by default.

  Returns
  -------
  Sequence[ImportedObject]
    A sequence containing the imported objects. This can include
    `PointSet`, `Polyline`, `Polygon`, `EdgeNetwork`, `Surface` or `Text3D`.
    The sequence may contain objects of different types.

  Raises
  ------
  ValueError
    If the extension of `path` is not .dxf or .dxb.
  FileNotFoundError
    If there is no file at `path`.
  FileImportError
    If there was an error importing `path`.
    The error message is often (but not always) provided by the application
    so may be translated into the user's selected language.
  ImportFormatNotSupportedError
    If the connected application does not support importing this format.

  Warns
  -----
  FileImportWarning
    If one or more objects could not be imported correctly.
  """
  path = _validate_path(path, (".dxb", ".dxf"))
  with ImportOperation(path, data_transfer=DataTransfer()) as operation:
    operation.supply_coordinate_system(coordinate_system)
    operation.supply_unit(unit)
    oids = operation.import_all_objects()
  if len(oids) == 0:
    raise FileImportError(
      f"Failed to import: {path}"
    )
  return oids


def import_ecw(
  path: str | os.PathLike,
) -> ImportedObject[Surface]:
  """Imports a ecw file.

  Import an ECW (Enhanced Compression Wavelet) file developed by Hexagon
  Geospatial as a rastered surface. This format is typically used for aerial
  photography and satellite imagery.

  Parameters
  ----------
  path
    The path to the file to import.

  Returns
  -------
  ImportedObject
    The imported surface. This will always have a raster applied containing
    the image read from the ecw file.

  Raises
  ------
  ValueError
    If `path` does not have the .ecw extension.
  FileNotFoundError
    If there is no file at `path`.
  FileImportError
    If there was an error importing `path`.
    The error message is often (but not always) provided by the application
    so may be translated into the user's selected language.
  ImportFormatNotSupportedError
    If the connected application does not support importing this format.

  Warns
  -----
  FileImportWarning
    If one or more objects could not be imported correctly.
  """
  path = _validate_path(path, ".ecw")
  with ImportOperation(path, data_transfer=DataTransfer()) as operation:
    oids = operation.import_all_objects()
  if len(oids) == 0:
    raise FileImportError(
      f"Failed to import: {path}"
    )
  # An ecw file only contains a single surface.
  return oids[0]


def import_jp2(
  path: str | os.PathLike,
) -> ImportedObject[Surface]:
  """Imports a jp2 file.

  Import a JPEG 2000 (Joint Photographic Experts Group) image file as a
  rastered surface.

  JPEG 2000 was designed as an improved version of the widely used JPEG image
  format (.jpg or .jpeg) however the ubiquity of the original JPEG format
  means jp2 is not widely supported.

  Parameters
  ----------
  path
    The path to the file to import.

  Returns
  -------
  ImportedObject
    The imported surface. This will always have a raster applied containing
    the image read from the jp2 file.

  Raises
  ------
  ValueError
    If `path` does not have the .jp2 extension.
  FileNotFoundError
    If there is no file at `path`.
  FileImportError
    If there was an error importing `path`.
    The error message is often (but not always) provided by the application
    so may be translated into the user's selected language.
  ImportFormatNotSupportedError
    If the connected application does not support importing this format.

  Warns
  -----
  FileImportWarning
    If one or more objects could not be imported correctly.

  Notes
  -----
  These files can also be imported via the pillow library.
  """
  path = _validate_path(path, ".jp2")
  with ImportOperation(path, data_transfer=DataTransfer()) as operation:
    oids = operation.import_all_objects()
  if len(oids) == 0:
    raise FileImportError(
      f"Failed to import: {path}"
    )
  # An jp2 file only contains a single surface.
  return oids[0]


def import_scd(
  path: str | os.PathLike,
) -> Sequence[ImportedObject[NumericColourMap | StringColourMap]]:
  """Imports a Vulcan scd file.

  This format is used by Maptek Vulcan to store colour maps.

  Parameters
  ----------
  path
    The path to the file to import.

  Returns
  -------
  Sequence[ImportedObject]
    A sequence containing the object IDs of the imported colour maps.

  Raises
  ------
  ValueError
    If `path` does not have the .scd extension.
  FileNotFoundError
    If there is no file at `path`.
  FileImportError
    If there was an error importing `path`.
    The error message is often (but not always) provided by the application
    so may be translated into the user's selected language.
  ImportFormatNotSupportedError
    If the connected application does not support importing this format.

  Warns
  -----
  FileImportWarning
    If one or more objects could not be imported correctly.
  """
  path = _validate_path(path, ".scd")
  with ImportOperation(path, data_transfer=DataTransfer()) as operation:
    oids = operation.import_all_objects()
  if len(oids) == 0:
    raise FileImportError(
      f"Failed to import: {path}"
    )
  return oids


def import_arch_d(
  path: str | os.PathLike,
  *,
  coordinate_system: CoordinateSystem | None = None,
  unit: DistanceUnit = DistanceUnit.METRE,
) -> Sequence[ImportedObject[VisualContainer]]:
  """Import an arch_d file.

  Import data from an Envisage archive file used by Maptek Vulcan.

  Parameters
  ----------
  path
    The path to the file to import.
  coordinate_system
    The coordinate system which the imported objects are in.
    Setting this parameter does not trigger a coordinate system conversion.
    This is no coordinate system by default.
  unit
    The unit the file is stored in. This is metres by default.

  Returns
  -------
  Sequence[ImportedObject]
    Sequence of imported objects. Each is a container representing a layer
    imported from the file.

  Raises
  ------
  ValueError
    If `path` does not have the .arch_d extension.
  FileNotFoundError
    If there is no file at `path`.
  FileImportError
    If there was an error importing `path`.
    The error message is often (but not always) provided by the application
    so may be translated into the user's selected language.
  ImportFormatNotSupportedError
    If the connected application does not support importing this format.

  Warns
  -----
  FileImportWarning
    If one or more objects could not be imported correctly.
  """
  path = _validate_path(path, ".arch_d")
  with ImportOperation(path, data_transfer=DataTransfer()) as operation:
    operation.supply_coordinate_system(coordinate_system)
    operation.supply_unit(unit)
    oids = operation.import_all_objects()
  return oids


def import_dgd_isis(
  path: str | os.PathLike,
  *,
  coordinate_system: CoordinateSystem | None = None,
  unit: DistanceUnit = DistanceUnit.METRE,
) -> Sequence[ImportedObject[VisualContainer]]:
  """Import a dgd.isis file.

  Import data from a Vulcan design database file. Currently, all supported
  objects from all layers are imported.

  Parameters
  ----------
  path
    The path to the file to import.
  coordinate_system
    The coordinate system which the imported objects are in.
    Setting this parameter does not trigger a coordinate system conversion.
    This is no coordinate system by default.
  unit
    The unit the file is stored in. This is metres by default.

  Returns
  -------
  Sequence[ImportedObject]
    A sequence of `ObjectID`s of `VisualContainer` objects. There is one
    container per layer in the design database.

  Raises
  ------
  ValueError
    If `path` does not have the .dgd.isis extension.
  FileNotFoundError
    If there is no file at `path`.
  FileImportError
    If there was an error importing `path`.
    The error message is often (but not always) provided by the application
    so may be translated into the user's selected language.
  ImportFormatNotSupportedError
    If the connected application does not support importing this format.

  Warns
  -----
  FileImportWarning
    If one or more objects could not be imported correctly.
  """
  path = _validate_path_dgd_isis(path)
  with ImportOperation(path, data_transfer=DataTransfer()) as operation:
    operation.supply_coordinate_system(coordinate_system)
    operation.supply_unit(unit)
    oids = operation.import_all_objects()
  return oids


def import_image(
  path: str | os.PathLike,
) -> ImportedObject[Raster]:
  """Import a raster from an image file.

  Unlike the other import functions in this package, this uses the Pillow
  package instead of the application's importer.

  Parameters
  ----------
  path
    The path to the file to import.

  Returns
  -------
  ImportedObject
    The imported raster.

  Raises
  ------
  ValueError
    If `path` is not to a supported image file.
  FileNotFoundError
    If there is no file at `path`.
  """
  if not isinstance(path, pathlib.Path):
    path = pathlib.Path(path)
  try:
    with Raster(image=path) as raster:
      raster.save()
      return ImportedObject(path.stem, raster.id)
  except UnidentifiedImageError as error:
    raise ValueError(f"Unsupported image file: {path}") from error


def import_image_with_world_file(
  image_path: str | os.PathLike,
  world_file_path: str | os.PathLike | None = None
) -> ImportedObject[Surface]:
  """Import an image file with an associated world file.

  The image will be applied as a raster to a rectangular surface at a location
  defined by the world file.

  Parameters
  ----------
  image_path
    Path to the image file to import.
    This must be a jpg, png, bmp, tif or tiff file.
  world_file_path
    Path to the world file to import.
    If None, this function will search for a world file with the same name
    as the image file.
    To import using an image with the .wld extension, you must explicitly
    set the `world_file_path` parameters.

  Returns
  -------
  ImportedObject
    The surface imported based on the world file with a raster based on the
    image file applied.

  Raises
  ------
  FileNotFoundError
    If the image or world file cannot be found.
  CorruptFileError
    If the world file is corrupt.

  Notes
  -----
  The following table outlines the expected extensions for world files
  based on the associated image file:

  +--------------+-------------------+
  | Image format | World file format |
  +==============+===================+
  | jpg / jpeg   | jpw               |
  +--------------+-------------------+
  | png          | pgw               |
  +--------------+-------------------+
  | bmp          | bpw               |
  +--------------+-------------------+
  | tif / tiff   | tfw               |
  +--------------+-------------------+
  | any          | wld               |
  +--------------+-------------------+

  """
  image_path = _validate_path(
    image_path,
    (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff")
  )
  if world_file_path is None:
    world_file_path = _find_world_file(image_path)
  world_file_path = _validate_path(
    world_file_path,
    (".jpw", ".pgw", ".bpw", ".tfw", ".wld")
  )
  if not image_path.exists():
    raise FileNotFoundError(f"Could not find: {image_path}")

  try:
    with open(world_file_path, "r", encoding="utf-8") as world_contents:
      world_file = WorldFile(world_contents)
  except CorruptWorldFileError as error:
    raise FileCorruptError(
      f"Failed to import corrupt world file: {world_file_path}"
    ) from error
  with Surface() as surface:
    with Raster(image=image_path) as raster:
      try:
        world_file.resize_canvas_for_raster(surface, raster)
      except ValueError as error:
        raise FileCorruptError(
          f"Failed to import corrupt world file: {world_file_path}"
        ) from error
      raster.save()
      surface.save()

  return ImportedObject(image_path.stem, surface.id)
