"""Functions for importing and exporting PointStudio-specific data."""
###############################################################################
#
# (C) Copyright 2024, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import os
import typing

from ..capi import DataEngine, DataTransfer
from ..data import (
  CoordinateSystem,
  DistanceUnit,
  Scan,
)
from ..data.typing import ImportedObject
from ..errors import FileImportError, NoScanDataError
from ..internal.import_operation import ImportOperation
from ..internal.io import validate_path as _validate_path

if typing.TYPE_CHECKING:
  from collections.abc import Sequence

def import_e57_scan(
  path: str | os.PathLike,
  *,
  coordinate_system: CoordinateSystem | None = None,
) -> ImportedObject[Scan]:
  """Import an e57 file.

  This is a compact, vendor-neutral format for storing point clouds, images
  and metadata produced by 3D imaging systems such as laser scanners.

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
    If `path` does not have the .e57 extension.
  FileNotFoundError
    If there is no file at `path`.
  FileImportError
    If there was an error importing `path`.
    The error message is often (but not always) provided by the application
    so may be translated into the user's selected language.
    This will be thrown if Faro LS is not installed on your computer.
  ImportFormatNotSupportedError
    If the connected application does not support importing this format.
    This will always be raised if the script is not connected to PointStudio.

  Warns
  -----
  FileImportWarning
    If one or more objects could not be imported correctly.
  """
  path = _validate_path(path, ".e57")
  with ImportOperation(path, data_transfer=DataTransfer()) as operation:
    operation.supply_coordinate_system(coordinate_system)
    imported_objects = operation.import_all_objects()
  if len(imported_objects) == 0:
    raise FileImportError(
      f"Failed to import: {path}"
    )
  # An e57 file only contains a single object.
  imported_object = imported_objects[0]
  if not imported_object.oid.is_a(Scan):
    DataEngine().DeleteObject(imported_object.oid.handle)
    raise NoScanDataError.from_path(path)
  return imported_object


def import_fls_scan(
  path: str | os.PathLike,
  *,
  coordinate_system: CoordinateSystem | None = None,
) -> ImportedObject[Scan]:
  """Import a Faro fls scan file.

  This requires Faro LS driver to be installed on your computer to function.

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
    If `path` does not have the .fls extension.
  FileNotFoundError
    If there is no file at `path`.
  FileImportError
    If there was an error importing `path`.
    The error message is often (but not always) provided by the application
    so may be translated into the user's selected language.
    This will be thrown if Faro LS is not installed on your computer.
  ImportFormatNotSupportedError
    If the connected application does not support importing this format.
    This will always be raised if the script is not connected to PointStudio.

  Warns
  -----
  FileImportWarning
    If one or more objects could not be imported correctly.
  """
  path = _validate_path(path, ".fls")
  with ImportOperation(path, data_transfer=DataTransfer()) as operation:
    operation.supply_coordinate_system(coordinate_system)
    imported_objects = operation.import_all_objects()
  if len(imported_objects) == 0:
    raise FileImportError(
      f"Failed to import: {path}"
    )
  # A fls file only contains a single object.
  imported_object = imported_objects[0]
  if not imported_object.oid.is_a(Scan):
    DataEngine().DeleteObject(imported_object.oid.handle)
    raise NoScanDataError.from_path(path)
  return imported_object


def import_optech_ixf_scan(
  path: str | os.PathLike,
  *,
  coordinate_system: CoordinateSystem | None = None,
) -> Sequence[ImportedObject[Scan]]:
  """Import an Optech IXF file.

  This is a scan format used by certain Optech laser scanners.
  Unlike many other scan formats, this can contain multiple scans in a single
  file.

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
  Sequence[ImportedObject]
    Sequence containing the imported scans.

  Raises
  ------
  NoScanDataError
    If any scan contains no scan data (e.g. It is image-only).
  ValueError
    If `path` does not have the .ixf extension.
  FileNotFoundError
    If there is no file at `path`.
  FileImportError
    If there was an error importing `path`.
    The error message is often (but not always) provided by the application
    so may be translated into the user's selected language.
  ImportFormatNotSupportedError
    If the connected application does not support importing this format.
    This will always be raised if the script is not connected to PointStudio.

  Warns
  -----
  FileImportWarning
    If one or more objects could not be imported correctly.

  Notes
  -----
  As of writing, 2024-10-25, the importer in PointStudio for this format allows
  the user to provide a unit but ignores the provided unit. If providing a unit
  for this format would be useful for you, use request support to make this
  known.
  """
  # :TODO: ISD-23271 - Allow this import to use a unit.
  path = _validate_path(path, ".ixf")
  with ImportOperation(path, data_transfer=DataTransfer()) as operation:
    operation.supply_coordinate_system(coordinate_system)
    # The unit is ignored on the C++ side.
    operation.supply_unit(DistanceUnit.METRE)
    imported_objects = operation.import_all_objects()
  if len(imported_objects) == 0:
    raise FileImportError(
      f"Failed to import: {path}"
    )
  if any(
    not imported_object.oid.is_a(Scan)
    for imported_object in imported_objects
  ):
    for imported_object in imported_objects:
      DataEngine().DeleteObject(imported_object.oid.handle)
    raise NoScanDataError.from_path(path)
  return imported_objects


def import_ascii_mdl_scan(
  path: str | os.PathLike,
  *,
  coordinate_system: CoordinateSystem | None = None,
) -> ImportedObject[Scan]:
  """Import an ASCII MDL scan file (.asc).

  Imports a text-based scan file from a C-ALS scanner.

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
    If `path` does not have the .asc extension.
  FileNotFoundError
    If there is no file at `path`.
  FileImportError
    If there was an error importing `path`.
    The error message is often (but not always) provided by the application
    so may be translated into the user's selected language.
  ImportFormatNotSupportedError
    If the connected application does not support importing this format.
    This will always be raised if the script is not connected to PointStudio.

  Warns
  -----
  FileImportWarning
    If one or more objects could not be imported correctly.

  Notes
  -----
  As of writing, 2024-10-25, the importer in PointStudio for this format allows
  the user to provide a unit but ignores the provided unit. If providing a unit
  for this format would be useful for you, use request support to make this
  known.
  """
  # :TODO: ISD-23272 - Allow this import to use a unit.
  path = _validate_path(path, ".asc")
  with ImportOperation(path, data_transfer=DataTransfer()) as operation:
    operation.supply_coordinate_system(coordinate_system)
    operation.supply_unit(DistanceUnit.METRE)
    imported_objects = operation.import_all_objects()
  if len(imported_objects) == 0:
    raise FileImportError(
      f"Failed to import: {path}"
    )
  # An asc file only contains a single object.
  imported_object = imported_objects[0]
  if not imported_object.oid.is_a(Scan):
    DataEngine().DeleteObject(imported_object.oid.handle)
    raise NoScanDataError.from_path(path)
  return imported_object


def import_legacy_mantis_scan(
  path: str | os.PathLike,
  *,
  coordinate_system: CoordinateSystem | None = None,
) -> ImportedObject[Scan]:
  """Import a legacy mantis scan file.

  These scans are split between two files - one with the .mpc extension and
  one with the .toc extension. This function requires both to be in the same
  file for the scan to be successfully imported.

  This is Mantis Vision's legacy file format used by their older scanners.
  Newer Mantis Vision scanners use .mvx files, which as of writing
  (2024-10-23), cannot be imported into Maptek Software.

  Parameters
  ----------
  path
    The path to the file to import. This can be the path to the .mpc or the
    .toc file.
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
    If the extension of `path` is not .mpc or .toc.
  FileNotFoundError
    If there is no file at `path`.
  FileImportError
    If there was an error importing `path`.
    The error message is often (but not always) provided by the application
    so may be translated into the user's selected language.
  ImportFormatNotSupportedError
    If the connected application does not support importing this format.
    This will always be raised if the script is not connected to PointStudio.

  Warns
  -----
  FileImportWarning
    If one or more objects could not be imported correctly.

  Notes
  -----
  This always imports all points from the scan file.
  """
  path = _validate_path(path, (".mpc", ".toc"))
  with ImportOperation(path, data_transfer=DataTransfer()) as operation:
    operation.supply_coordinate_system(coordinate_system)
    imported_objects = operation.import_all_objects()
  if len(imported_objects) == 0:
    raise FileImportError(
      f"Failed to import: {path}"
    )
  # This format only contains a single scan.
  imported_object = imported_objects[0]
  if not imported_object.oid.is_a(Scan):
    DataEngine().DeleteObject(imported_object.oid.handle)
    raise NoScanDataError.from_path(path)
  return imported_object


def import_cyclone_ptg_scan(
  path: str | os.PathLike,
  *,
  coordinate_system: CoordinateSystem | None = None,
) -> Sequence[ImportedObject[Scan]]:
  """Import scans from a Cyclone ptg scan.

  There are two types of ptg files:

  * Data file - Contains a single scan.
  * Index file - Contains references to multiple data files.

  This function handles both - when importing an index file, it will return
  all the scans referred to by the index file.

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
  Sequence[ImportedObject]
    Sequence containing the imported scans.

  Raises
  ------
  NoScanDataError
    If any scan contains no scan data (e.g. It is image-only).
  ValueError
    If `path` does not have the .ptg extension.
  FileNotFoundError
    If there is no file at `path`.
  FileImportError
    If there was an error importing `path`.
    The error message is often (but not always) provided by the application
    so may be translated into the user's selected language.
  ImportFormatNotSupportedError
    If the connected application does not support importing this format.
    This will always be raised if the script is not connected to PointStudio.

  Warns
  -----
  FileImportWarning
    If one or more objects could not be imported correctly.
  """
  path = _validate_path(path, ".ptg")
  with ImportOperation(path, data_transfer=DataTransfer()) as operation:
    operation.supply_coordinate_system(coordinate_system)
    imported_objects = operation.import_all_objects()
  if len(imported_objects) == 0:
    raise FileImportError(
      f"Failed to import: {path}"
    )
  if any(
    not imported_object.oid.is_a(Scan)
    for imported_object in imported_objects
  ):
    for imported_object in imported_objects:
      DataEngine().DeleteObject(imported_object.oid.handle)
    raise NoScanDataError.from_path(path)
  return imported_objects


def import_cyclone_ptx_scan(
  path: str | os.PathLike,
  *,
  coordinate_system: CoordinateSystem | None = None,
) -> Sequence[ImportedObject[Scan]]:
  """Import scans from a Cyclone ptx scan.

  This is a text-based interchange format.

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
  Sequence[ImportedObject]
    Sequence containing the imported scans.

  Raises
  ------
  NoScanDataError
    If any scan contains no scan data (e.g. It is image-only).
  ValueError
    If `path` does not have the .ptx extension.
  FileNotFoundError
    If there is no file at `path`.
  FileImportError
    If there was an error importing `path`.
    The error message is often (but not always) provided by the application
    so may be translated into the user's selected language.
  ImportFormatNotSupportedError
    If the connected application does not support importing this format.
    This will always be raised if the script is not connected to PointStudio.

  Warns
  -----
  FileImportWarning
    If one or more objects could not be imported correctly.
  """
  path = _validate_path(path, ".ptx")
  with ImportOperation(path, data_transfer=DataTransfer()) as operation:
    operation.supply_coordinate_system(coordinate_system)
    imported_objects = operation.import_all_objects()
  if len(imported_objects) == 0:
    raise FileImportError(
      f"Failed to import: {path}"
    )
  if any(
    not imported_object.oid.is_a(Scan)
    for imported_object in imported_objects
  ):
    for imported_object in imported_objects:
      DataEngine().DeleteObject(imported_object.oid.handle)
    raise NoScanDataError.from_path(path)
  return imported_objects


def import_zfs_scan(
  path: str | os.PathLike,
  *,
  coordinate_system: CoordinateSystem | None = None,
) -> ImportedObject[Scan]:
  """Import a zfs file.

  These are Zoller & Froehlich scan file.

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
    If `path` does not have the .zfs extension.
  FileNotFoundError
    If there is no file at `path`.
  FileImportError
    If there was an error importing `path`.
    The error message is often (but not always) provided by the application
    so may be translated into the user's selected language.
  ImportFormatNotSupportedError
    If the connected application does not support importing this format.
    This will always be raised if the script is not connected to PointStudio.

  Warns
  -----
  FileImportWarning
    If one or more objects could not be imported correctly.
  """
  path = _validate_path(path, ".zfs")
  with ImportOperation(path, data_transfer=DataTransfer()) as operation:
    operation.supply_coordinate_system(coordinate_system)
    imported_objects = operation.import_all_objects()
  if len(imported_objects) == 0:
    raise FileImportError(
      f"Failed to import: {path}"
    )
  # A zfs file only contains a single object.
  imported_object = imported_objects[0]
  if not imported_object.oid.is_a(Scan):
    DataEngine().DeleteObject(imported_object.oid.handle)
    raise NoScanDataError.from_path(path)
  return imported_object
