"""Settings used for projects shared between multiple modules.

Currently these are shared between mcp and modelling

Warnings
--------
Vendors and clients should not develop scripts or applications against
this package. The contents may change at any time without warning.

"""
###############################################################################
#
# (C) Copyright 2020, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

# pylint: disable=too-few-public-methods
# pylint: disable=too-many-instance-attributes

from __future__ import annotations

from enum import IntEnum
import os
import pathlib
import typing

if typing.TYPE_CHECKING:
  from mapteksdk.internal.backends import Backend

class ProjectOpenMode(IntEnum):
  """Mode selection for opening a Project - open, create or open/create."""
  MEMORY_ONLY = 0
  OPEN_EXISTING = 1
  OPEN_EXISTING_THREAD = 4
  CREATE_NEW = 2
  OPEN_OR_CREATE = 3

class ProjectAccessMode(IntEnum):
  """Mode selection for Project access - read/write/try write then read."""
  READ_ONLY = 1
  READ_WRITE = 2
  TRY_WRITE = 3

class ProjectUnits(IntEnum):
  """Unit selection for a Project."""
  METRES = 1
  FEET = 2
  YARDS = 3

class ProjectBackendType(IntEnum):
  """Method of storage for backend database."""
  MAPTEK_DB = 4 # Sqlite (store as a .maptekdb)
  MAPTEK_OBJ = 5 # ObjectFile (store as a .maptekobj) Caution: Read only
  SHARED = 6 # Shared (share with existing locked Project)
  VULCAN_DGD_ISIS = 8 # VulcanDgdIsis (store in a .dgd.isis database)
  VULCAN_TEK_ISIS = 9 # VulcanTekIsis (store in a .tek.isis database)
  VULCAN_DIR = 10 # Vulcan (store in a Vulcan project directory)

class ProjectOptions:
  """Provide some options for how to setup the Project class.
  This is optional and only needed if trying to load a specific project
  and/or run automated tests.

  Parameters
  ----------
  project_path : str | pathlib.Path
    Path to maptekdb directory (new or existing, depending on open_mode).
  open_mode : ProjectOpenMode
    Method to use when opening a maptekdb database for operating within.
  access_mode : ProjectAccessMode
    Whether to access the database using read only, read/write, or attempt
    write then read on fail.
  backend_type : ProjectBackendType
    Method of storage for database.
  proj_units : ProjectUnits
    Unit selection for project.
  dll_path : str
    Path to locate dlls and dependencies. This is not needed if connecting to
    an existing application.
  allow_hidden_objects : bool
    Sets project attribute (of same name) for whether to allow the SDK to
    create objects that are hidden by applications (these objects start with
    a full stop in their name (e.g. '.hidden').
    Default is False.

  """
  def __init__(
    self,
    project_path: str | pathlib.Path,
    open_mode: ProjectOpenMode=ProjectOpenMode.OPEN_EXISTING,
    access_mode: ProjectAccessMode=ProjectAccessMode.READ_WRITE,
    backend_type: ProjectBackendType=ProjectBackendType.MAPTEK_DB,
    proj_units: ProjectUnits=ProjectUnits.METRES,
    dll_path: str | None=None,
    allow_hidden_objects: bool=False,
    existing_backend: Backend | None=None
  ) -> None:
    self.project_path = os.fspath(project_path)
    self.open_mode = open_mode
    self.access_mode = access_mode
    self.backend_type = backend_type
    self.proj_units = proj_units
    self.dll_path = dll_path
    self.account_broker_connector_path = None
    self.account_broker_session_parameters = None
    self.allow_hidden_objects = allow_hidden_objects
    self.existing_backend = existing_backend
