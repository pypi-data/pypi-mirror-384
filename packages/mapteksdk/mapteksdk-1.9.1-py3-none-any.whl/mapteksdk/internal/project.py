"""Functionally for hosting a project from Python rather than an application.

These are candidates for mapteksdk.project intended for system integrators and
advanced users of the Python SDK.
"""
###############################################################################
#
# (C) Copyright 2023, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

from __future__ import annotations

import os
import pathlib

from mapteksdk.project import Project
from .options import ProjectOptions, ProjectOpenMode
from .mcp import McpdConnection


def create_new_database(
    database_path: str | pathlib.Path, *,
    bin_path: str | pathlib.Path | None = None,
    mcpd_connection:  McpdConnection | None = None) -> Project:
  """Create a new database at database_path and open it.

  This starts the necessary services for reading/writing data to the database.

  The database cannot be called index.maptekdb. This name is reserved for the
  name of the index file within a database.

  Parameters
  ----------
  database_path
      Path to maptekdb directory
  bin_path
      The path to the binaries to use to create and open the maptekdb.
  mcpd_connection
      Optionally, an existing MCPD connection. This can be used if an MCPD has
      already been started and hasn't already opened a database/DataEngine. If
      it is not provided the MCPD will be started.

  Raises
  ------
  ValueError
    If the database_path does not end with .maptekdb or the name is
    index.maptekdb.
  FileExistsError
    If there is already a database at the given path.
  ProjectConnectionFailureError
    If there was a problem connecting the MCPD provided by mcpd_connection or
    the one started by this function.

  Returns
  -------
  Project
    A Project referencing the database at the given location.
    The project needs to be unloaded in order to shutdown the services
    started.
  """
  if not os.path.basename(database_path).endswith('.maptekdb'):
    # This is the convention Maptek uses to identify folders which represent
    # a Maptek database.
    raise ValueError('The path to the database must end in .maptekdb')

  if os.path.basename(database_path) == 'index.maptekdb':
    raise ValueError('The database can not be named index.maptekdb. That name '
                     'is reserved for the index file within a Maptek '
                     'Database.')

  if os.path.exists(database_path):
    raise FileExistsError(f'The given path ({database_path}) already exists.')

  if not bin_path:
    bin_path = _bin_from_native()

  # This uses the pre-existing way of having the project class handle this
  # situation. This may be improved in the future.
  options = ProjectOptions(
    database_path,
    open_mode=ProjectOpenMode.CREATE_NEW,
    dll_path=bin_path,
    )

  return Project(options, existing_mcpd=mcpd_connection)


def open_database(database_path: str | pathlib.Path,
                  *,
                  create_if_missing: bool = False,
                  bin_path: str | pathlib.Path | None = None,
                  mcpd_connection:  McpdConnection | None = None):
  """Open the provided database.

  This can optionally create the database if it doesn't exist by using the
  create_if_missing parameter.

  Parameters
  ----------
  database_path
      Path to maptekdb directory
  create_if_missing
      If True and there is no database at database_path then a new database
      will be created.
  bin_path
      The path to the binaries to use to create and open the maptekdb.
  mcpd_connection
      Optionally, an existing MCPD connection. This can be used if an MCPD has
      already been started and hasn't already opened a database/DataEngine. If
      it is not provided the MCPD will be started.

  Raises
  ------
  FileNotFoundError
      If there is no database at the given path and create_if_missing is
      False.

  ProjectConnectionFailureError
    If there was a problem connecting the MCPD provided by mcpd_connection or
    the one started by this function.

  Returns
  -------
  Project
    A Project referencing the database at the given location.
    The project needs to be unloaded in-order to shutdown the services started.
  """
  if os.path.basename(database_path) == 'index.maptekdb':
    # The index.maptekdb is the index file. We only need the maptekdb.
    #
    # Assume the parent directory is the maptekdb.
    database_path = os.path.dirname(database_path)

  if not os.path.exists(database_path):
    if create_if_missing:
      return create_new_database(
        database_path, bin_path=bin_path, mcpd_connection=mcpd_connection)

    raise FileNotFoundError('The database does not exist.')

  if not bin_path:
    bin_path = _bin_from_native()

  # This uses the pre-existing way of having the project class handle this
  # situation. This may be improved in the future.
  options = ProjectOptions(
    database_path,
    open_mode=ProjectOpenMode.OPEN_OR_CREATE,
    dll_path=bin_path,
    )

  return Project(options, existing_mcpd=mcpd_connection)


def _bin_from_native() -> pathlib.Path | None:
  """Determine the bin path from native package if available.

  Returns
  -------
  pathlib.Path
    The path to the binaries provided by the mapteksdk.native package if
    it is available and importable as well
  None
    If the the mapteksdk.native package is not available.
  """
  try:
    # pylint: disable=import-outside-toplevel
    # This import should only be done if it is needed rather than always being
    # tried at global scope of this module. This package is an optional
    # dependency so it is expected to be missing.
    import mapteksdk.native

    # pylint: disable=no-member
    # pylint won't be able to see inside this package.
    return mapteksdk.native.bin_path()
  except ImportError:
    return None
