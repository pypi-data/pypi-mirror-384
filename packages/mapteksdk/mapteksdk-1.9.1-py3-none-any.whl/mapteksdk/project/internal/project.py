"""Implementation of the Project class."""
###############################################################################
#
# (C) Copyright 2024, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

from __future__ import annotations

import atexit
from collections.abc import Generator, Iterable, Sequence, Callable, Mapping
from contextlib import contextmanager
from functools import partial
import logging
import os
import pathlib
import posixpath
import typing

from ... import capi
from ...capi.dll_loading import enable_dll_loading
from ...capi.types import T_ObjectHandle
from ...capi.util import CApiDllLoadFailureError
from ...data import (
  BlockModelDefinition,
  ChangeReasons,
  Container,
  DataObject,
  DenseBlockModel,
  Discontinuity,
  EdgeNetwork,
  Ellipsoid,
  FilledPolygon,
  GridSurface,
  Marker,
  NumericColourMap,
  PointSet,
  Polygon,
  Polyline,
  Raster,
  RibbonChain,
  RibbonLoop,
  Scan,
  SelectionFile,
  _SelectionGroup,
  SparseBlockModel,
  StandardContainer,
  StringColourMap,
  SubblockedBlockModel,
  Surface,
  Text2D,
  Text3D,
  Topology,
  VisualContainer,
)
from ...data.containers import ChildView
from ...data.objectid import ObjectID
from ...geologycore import Drillhole, DrillholeDatabase
from ...internal.comms import default_manager
from ...internal.lock import ReadLock, WriteLock, LockType
from ...internal.logger import configure_log
from ...internal.mcp import (
  ExistingMcpdInstance,
  McpdConnection,
  find_mdf_hosts,
)
from ...internal.options import (ProjectOptions, ProjectOpenMode)
from ...internal.overwrite import add_objects_with_overwrite
from ...internal.path_helpers import (
  check_path_component_validity,
  valid_path,
  HiddenObjectPermissionError,
)
from ...internal.progress_indicator import ProgressIndicatorConcrete
from ...internal.telemetry import (
  enable_telemetry,
  get_telemetry,
  TelemetryProtocol,
)
from ...internal.transaction_manager import TransactionManager
from ...internal.undo import UndoStack, UndoNotSupportedError
from ...internal.util import default_type_error_message
from ...internal.backends import (ExistingBackend, InMemoryBackend, NewBackend,
                                 BackendObserver)
from ...overwrite_modes import OverwriteMode
from ...progress_indicator import ProgressIndicator
from ...labs.cells import SparseIrregularCellNetwork
from ..errors import (DeleteRootError, ObjectDoesNotExistError,
                     NoHostApplicationError, ProjectConnectionFailureError,
                     ApplicationTooOldError, TypeMismatchError,
                     NoRecycleBinError, InvalidParentError)
from ..selection import Selection
from .type_guards import is_a_standard_container, is_a_container, is_a

# pylint: disable=too-many-public-methods
# pylint: disable=too-many-branches
# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-lines
# pylint: disable=too-many-statements

ObjectT = typing.TypeVar('ObjectT', bound=DataObject)
"""Type hint used for arguments which are subclasses of DataObject."""

ObjectIdT = typing.TypeVar("ObjectIdT", bound=DataObject)
"""Type hint used for ObjectID of any DataObject subclass.

Note that ObjectT and ObjectIdT may not refer to the same type for certain
functions.
"""

class Project:
  """Main class to connect to an instance of an MDF application.
  Project() establishes the communication protocol and provides base
  functionality into the application, such as object naming, locating,
  copying and deleting.

  Parameters
  ----------
  options
    Optional specification of project and connection
    settings. Used for unit testing to start a new database and
    processes without an MDF host application already running.
  existing_mcpd
    If None (default) then the latest relevant application that was launched
    will be connected to. This is equivalent to passing in
    Project.find_running_applications()[0].

    Otherwise it may be ExistingMcpdInstance which refers to the host
    application to connect to otherwise a McpdConnection which is an
    existing connection to a host application (its mcpd) and the project
    within that application will be used.

  Raises
  ------
  ProjectConnectionFailureError
    If the script fails to connect to the project. Generally this is
    because there is no application running, or the specified application
    is no longer running.
  """

  # Keep track of if the logging has been configured.
  # See configure_log for details.
  _configured_logging = False

  def __init__(
      self,
      options: ProjectOptions | None=None,
      existing_mcpd: ExistingMcpdInstance | McpdConnection | None=None):

    # The types listed here are the default types expected to be available
    # in every application the SDK can connect to.
    self.__types_for_data: list[tuple[int, type[DataObject]]] = [
      (7, Scan),
      (6, SubblockedBlockModel),
      (6, SparseIrregularCellNetwork),
      (6, SparseBlockModel),
      (6, GridSurface),
      (6, DenseBlockModel),
      (5, Text3D),
      (5, Text2D),
      (5, RibbonChain),
      (5, RibbonLoop),
      (5, BlockModelDefinition),
      (4, Surface),
      (4, StandardContainer),
      (4, Polyline),
      (4, Polygon),
      (4, PointSet),
      (4, Marker),
      (4, EdgeNetwork),
      (4, Discontinuity),
      (4, Ellipsoid),
      (4, FilledPolygon),
      (4, _SelectionGroup),
      (3, VisualContainer),
      (3, StringColourMap),
      (3, Raster),
      (3, NumericColourMap),
      (3, SelectionFile),
    ]
    """Sorted list of types openable by the Project class.

    Each element in the list is a tuple of the form (priority, type)
    where priority is the number of base classes between the type
    and deC_Object (The ultimate base class of all objects stored in
    a maptekdb).

    Derived classes have higher priority than their bases and will be checked
    before their base classes. This ensures that Project.edit() and
    Project.read() will open an object as the most derived possible type.

    Use Project.register_types() to add additional types to this list.
    """
    self.__backend = None

    # :TRICKY: atexit.register to ensure project is properly unloaded at exit.
    # By implementing the standard logging library, __del__ and __exit__ are
    # no longer guaranteed to be called. During unit testing, spawned mcpd.exe
    # and backendserver.exe would remain open indefinitely after the unit tests
    # finished - preventing subsequent runs.
    # Not an issue if connecting to an existing host application.
    self._exit_function = atexit.register(self.unload_project)

    try:
      # Configure all the MDF loggers with defaults. This is done when the user
      # creates the Project() instance so they don't need to do it themselves
      # and so by default we can have consistent logging.
      #
      # Only configure the logging once as otherwise output will be duplicated
      # as it set-up multiple log handlers.
      if not Project._configured_logging:
        configure_log(logging.getLogger('mapteksdk'))
        Project._configured_logging = True
    finally:
      self.log = logging.getLogger('mapteksdk.project')

    self.__telemetry_enabled = enable_telemetry()

    # If no options are provided, there are some default options we expect.
    if not options:
      options = ProjectOptions('')

    # If connecting to an existing mcpd, determine which one and set up the
    # DLL load path. This will finding a mcpd to connect to if one was not
    # provided already.
    #
    # Connecting to an mcpd is not required if using a memory-only project.
    if options.open_mode is ProjectOpenMode.OPEN_EXISTING:
      # No DLL path should be set as the MDF DLLs from the existing mcpd
      # should be used to ensure compatibility.
      #
      # If the plan is to connect to an existing mcpd, then finding one will
      # discover the DLLs required.
      #
      # If creating a new mcpd, then the DLL path should already be set.
      # Unless a new mode is supported where an existing mcpd (application) is
      # found first then it is used to start it.
      if not existing_mcpd:
        existing_mcpd = ExistingBackend.find_application_to_connect_to(self.log)
        if not existing_mcpd:
          error_message = "No host applications found running to connect to."
          self.log.error(error_message)
          raise NoHostApplicationError(error_message)

    if existing_mcpd and not isinstance(existing_mcpd, McpdConnection):
      # The connection hasn't been established yet so the DLL path isn't
      # configured either.
      options.dll_path = existing_mcpd[1]

    if (not options.dll_path and
        options.open_mode is not ProjectOpenMode.OPEN_EXISTING_THREAD):
      raise ProjectConnectionFailureError(
          "Failed to locate folder containing required DLLs. "
          "No search paths could be determined.")

    if options.open_mode is ProjectOpenMode.MEMORY_ONLY:
      self.__backend = InMemoryBackend(self.log)
    elif options.open_mode is ProjectOpenMode.OPEN_EXISTING:
      self.__backend = ExistingBackend(self.log, existing_mcpd)
    elif options.open_mode is ProjectOpenMode.OPEN_EXISTING_THREAD:
      parent_backend = options.existing_backend
      if not parent_backend:
        raise ProjectConnectionFailureError(
          "Cannot connect to the Project on a thread if the initial "
          "project is not connected."
        )
      self.__backend = BackendObserver(self.log, parent_backend)
    elif options.open_mode in (ProjectOpenMode.CREATE_NEW,
                               ProjectOpenMode.OPEN_OR_CREATE):
      self.__backend = NewBackend(
        self.log,
        existing_mcpd if isinstance(
          existing_mcpd, ExistingMcpdInstance) else None,
        options)
    else:
      raise ValueError("Unrecognized open mode: {options.open_mode}.")

    # When opening an existing project on another thread, the DLLs are
    # expected to already be registered by the first thread.
    if not isinstance(self.__backend, BackendObserver):
      dll_path = options.dll_path
      if dll_path is None:
        raise ProjectConnectionFailureError(
          "Cannot connect to an application if the dll path is not supplied."
        )
      try:
        self.__dll_directory = enable_dll_loading(
          pathlib.Path(dll_path))
      except FileNotFoundError as error:
        raise ProjectConnectionFailureError(
          "Failed to locate folder containing required DLLs. "
        ) from error

    try:
      licence = self.__backend.acquire_licence(
        options.account_broker_connector_path,
        options.account_broker_session_parameters)

      os.environ["MDF_ACTIVE_PACKAGE"] = licence
      os.environ["MDF_EXTEND_LICENCE_STRING"] = licence

      self.options = options
      self.allow_hidden_objects = self.options.allow_hidden_objects

      if isinstance(existing_mcpd, McpdConnection):
        self.__backend.use_existing_connection(existing_mcpd)

      self.__load_dlls_with_dataengine_types()
      self.__backend.connect_to_project()

      # Store easy access for project's root object.
      self.root_id = ObjectID(self._data_engine_api.RootContainer())
      self.__undo_stack: UndoStack | None = None
      """The current undo stack.

      This is None if the Project class is not currently within a
      Project.undo() context manager.
      """
    except:
      # If an error occurs then unload the project. The unload function is
      # capable of dealing with the incomplete state and will handle undoing
      # what was successfully done prior to the error.
      self.unload_project()
      raise

  def __enter__(self):
    self.log.debug("__enter__ called")
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    self.log.debug("__exit__ called")
    self.unload_project()

  def __load_dlls_with_dataengine_types(self) -> None:
    """Loads the DLLs which contain DataEngine types.

    This must be called before connecting to the DataEngine. Once the
    script has connected, it is an error to load DLLs which contain
    DataEngine types.
    """
    _ = self._data_engine_api
    _ = self._modelling_api
    _ = self._selection_api
    _ = self._scan_api
    _ = self._viewer_api
    _ = self._vulcan_api

    # The DrillholeModel DLL is only available when connecting to Vulcan
    # GeologyCore. Failing to load it thus should not be treated as an error.
    try:
      drillhole_version = self._drillhole_model_api.version
      # Only add the Drillhole and DrillholeDatabase classes if they are
      # supported by the C API.
      if drillhole_version >= (1, 7):
        # Register the drillhole types as openable.
        self._register_types([
          (6, Drillhole),
          (4, DrillholeDatabase)
        ])
      else:
        self.log.info(
          "The drillhole types are not available. The drillhole model DLL is "
          "too old.")
    except CApiDllLoadFailureError:
      self.log.info(
        "The drillhole types are not available. The drillhole model DLL "
        "could not be loaded.")

  @typing.overload
  def __find_from(
      self,
      object_id: ObjectID[Container],
      names: list[str],
      create_if_not_found: typing.Literal[False]) -> ObjectID[Container] | None:
    ...

  @typing.overload
  def __find_from(
      self,
      object_id: ObjectID[Container],
      names: list[str],
      create_if_not_found: typing.Literal[True]) -> ObjectID[Container]:
    ...

  @typing.overload
  def __find_from(
      self,
      object_id: ObjectID[Container],
      names: list[str],
      create_if_not_found: bool) -> ObjectID[Container] | None:
    ...

  def __find_from(
    self,
    object_id: ObjectID[Container],
    names: list[str],
    create_if_not_found: bool) -> ObjectID[Container] | None:
    """Internal function for find_object() and
    _find_object_or_create_if_missing().

    Parameters
    ----------
    object_id
      The ID of the object to start at.
    names
      list of container paths to recursively search through
      and / or create if not found (if create_if_not_found)
      e.g. ['surfaces', 'new container', 'surfaces 2'].
    create_if_not_found
      Create specified path if it doesn't exist.

    Returns
    -------
    ObjectID
      Object ID of the object if found.
    None
      Object could not be found including if the object couldn't be
      created when it's not found.
      The path can't be created if the object is not a container or is
      a topology which shouldn't be treated as a container (unless
      allow_hidden_objects is True).

    Raises
    ------
    Exception
      Error trying to create path that didn't exist (unknown error).
    ValueError
      A new path needs to be created and will result in
      creating hidden objects (i.e. start with '.') when
      project attribute allow_hidden_objects is False.

    """
    if not names:
      return object_id

    if not object_id.is_a(Container):
      self.log.info("The path %s can not be created as the object before it "
                    "is not a container",
                    '/'.join(names))
      # names could not be found.
      return None

    if object_id.is_a(Topology) and not self.allow_hidden_objects:
      # Treat it as if the object couldn't be found (specifically the
      # container).
      #
      # This prevents creating a container within a topology object.
      self.log.info("The path %s can not be created as the object before it "
                    "is a topology and allow_hidden_objects is False.",
                    '/'.join(names))
      return None

    with ReadLock(object_id.handle, self._data_engine_api) as r_lock:
      found = ObjectID(self._data_engine_api.ContainerFind(
        r_lock.lock, names[0]))

    if not found and create_if_not_found:
      self.log.info("The path %s didn't exist so attempting to create it.",
                    '/'.join(names))

      if not self.allow_hidden_objects:
        # Check that none of the objects created would be hidden.
        if any(name.startswith('.') for name in names):
          raise ValueError("Invalid path provided. No object name may start "
                           "with '.' as that would be a hidden object.")

      # Create a new container for each part of the path (as none of them
      # exist)
      new_containers = [
        ObjectID(self._modelling_api.NewVisualContainer())
        for _ in range(len(names))
      ]

      # Add each new container to the container before it.
      new_parents = [object_id] + new_containers[:-1]
      for parent, child, name in zip(reversed(new_parents),
                                     reversed(new_containers),
                                     reversed(names)):
        def add_to_container(w_lock: WriteLock):
          # pylint: disable=cell-var-from-loop
          # Using the loop variable is fine because this is called immediately.
          self._data_engine_api.ContainerAppend(
            w_lock.lock,
            name,
            self.__get_obj_handle(child),
            True)
        self._run_with_undo(parent, add_to_container)

      return new_containers[-1]

    if not found and not create_if_not_found:
      # It doesn't exist and the caller wants to know
      return None
    return self.__find_from(found, names[1:], create_if_not_found)

  def _register_types(self, new_types: list[tuple[int, type]]) -> None:
    """Register types to be openable via Project.edit() and Project.read().

    This maintains the sort order of the list of openable types.

    Parameters
    ----------
    new_types
      List of tuples of the form (priority, type) where priority is the
      priority of the new type and type is the new openable type.
      The new type must inherit from DataObject.
    """
    self.__types_for_data.extend(new_types)
    # This is using sort instead of "bisect.insort" because reversing
    # insort requires Python 3.10.
    self.__types_for_data.sort(key=lambda x: x[0], reverse=True)

  @property
  def _data_engine_api(self) -> capi.DataEngineApi:
    """Access the DataEngine C API."""
    return capi.DataEngine()

  @property
  def _modelling_api(self) -> capi.ModellingApi:
    """Access the Modelling C API."""
    return capi.Modelling()

  @property
  def _selection_api(self) -> capi.SelectionApi:
    """Access the Selection C API."""
    return capi.Selection()

  @property
  def _scan_api(self) -> capi.ScanApi:
    """Access the Scan C API."""
    return capi.Scan()

  @property
  def _viewer_api(self) -> capi.ViewerApi:
    """Access the Viewer C API."""
    return capi.Viewer()

  @property
  def _vulcan_api(self) -> capi.VulcanApi:
    """Access the Vulcan C API."""
    return capi.Vulcan()

  @property
  def _drillhole_model_api(self) -> capi.DrillholeModelApi:
    """Access the Drillhole Model C API."""
    return capi.DrillholeModel()

  @property
  def _backend(
    self
  ) -> NewBackend | BackendObserver | ExistingBackend | InMemoryBackend:
    """The backend used by this object."""
    if self.__backend is None:
      # This should be unreachable, because the backend is only None before
      # the backend is constructed in the constructor.
      raise RuntimeError(
        "No backend available."
      )
    return self.__backend

  @property
  def _telemetry(self) -> TelemetryProtocol:
    """Access an object which can be used to record telemetry."""
    return get_telemetry()

  def _record_function_call_telemetry(self, name: str):
    """Record function call telemetry for `name`.

    This automatically prefixes the telemetry with "Project." so that the
    caller does not need to do so.
    """
    self._telemetry.record_function_call(f"Project.{name}")

  def unload_project(self) -> None:
    """Call the mcp class to unload a spawned mcp instance (i.e. when not
    using a host application like Eureka or PointStudio).
    Use this when finished operating on a project that has
    ProjectOptions that requested an mcpd_mode of CREATE_NEW.

    Also unloads dataengine created with same methods.

    Failure to call this un-loader may leave orphan mcpd.exe processes
    running on the machine.

    """
    self.log.info("unload_project() called")
    if self.__backend:
      self.__backend.disconnect_from_project()

    try:
      self.__dll_directory.unload()
    except AttributeError:
      # The constructor failed before setting this.
      pass

    if 'MDF_ACTIVE_PACKAGE' in os.environ:
      del os.environ["MDF_ACTIVE_PACKAGE"]
    if 'MDF_EXTEND_LICENCE_STRING' in os.environ:
      del os.environ["MDF_EXTEND_LICENCE_STRING"]

    self.__telemetry_enabled.__exit__(None, None, None)

    # The project has been unloaded so it doesn't need to be done when the
    # interpreter terminates.
    if self._exit_function:
      atexit.unregister(self._exit_function)
      self._exit_function = None

  @property
  def api_version(self) -> tuple[int, int]:
    """Returns the API version reported by the application.

    Returns
    -------
    tuple
      The API version of the application in the form: (major, minor).

    Notes
    -----
    The following table summarises the API version for officially supported
    applications:

    +---------------------------+-------------+
    | Application               | api_version |
    +===========================+=============+
    | Eureka 2020               | (1, 1)      |
    +---------------------------+-------------+
    | PointStudio 2020          | (1, 1)      |
    +---------------------------+-------------+
    | PointStudio 2021          | (1, 2)      |
    +---------------------------+-------------+
    | PointStudio 2021.1        | (1, 3)      |
    +---------------------------+-------------+
    | PointStudio 2022          | (1, 3)      |
    +---------------------------+-------------+
    | PointStudio 2022.0.1      | (1, 3)      |
    +---------------------------+-------------+
    | PointStudio 2022.1        | (1, 3)      |
    +---------------------------+-------------+
    | PointStudio 2023          | (1, 7)      |
    +---------------------------+-------------+
    | PointStudio 2024          | (1, 10)     |
    +---------------------------+-------------+
    | Vulcan GeologyCore 2021   | (1, 4)      |
    +---------------------------+-------------+
    | Vulcan GeologyCore 2021.1 | (1, 4)      |
    +---------------------------+-------------+
    | Vulcan GeologyCore 2022   | (1, 5)      |
    +---------------------------+-------------+
    | Vulcan GeologyCore 2022.1 | (1, 7)      |
    +---------------------------+-------------+
    | Vulcan GeologyCore 2023   | (1, 7)      |
    +---------------------------+-------------+
    | Vulcan GeologyCore 2023.1 | (1, 9)      |
    +---------------------------+-------------+
    | GeologyCore 2024          | (1, 10)     |
    +---------------------------+-------------+

    Earlier applications will have an API version of (0, 0). It is not
    recommended to connect to applications with API versions less than (1, 1).
    """
    self._record_function_call_telemetry("api_version")
    # Though each C API could have its own version, currently they all
    # return the same version.
    return self._modelling_api.version

  def raise_if_version_below(self, version: tuple[int, int]) -> None:
    """Raises an error if the script has connected to an application whose
    version is lower than the specified version.

    This allows for scripts to exit early when attaching to an application
    which does not support the required data types.

    Parameters
    ----------
    version
      A tuple (major, minor). If the API version is less than this tuple
      an error will be raised.

    Raises
    ------
    ApplicationTooOldError
      If the API version is lower than the specified version.

    Examples
    --------
    Exit if the application does not support GridSurface (api_version is
    less than (1, 2)).

    >>> from mapteksdk.project import Project
    >>> project = Project()
    >>> project.raise_if_version_below((1, 2))

    It is also possible to catch this error and add extra information.

    >>> from mapteksdk.project import Project, ApplicationTooOldError
    >>> project = Project()
    >>> try:
    ...     project.raise_if_version_below((1, 2))
    >>> except ApplicationTooOldError as error:
    ...     raise SystemExit("The attached application does not support "
    ...                      "irregular grids") from error

    """
    self._record_function_call_telemetry("raise_if_version_below")
    if self.api_version < version:
      message = (f"API version is too old: {self.api_version}. "
                 f"This script requires an API version of at least: {version}")
      raise ApplicationTooOldError(message)

  def find_object(self, path: str) -> ObjectID[DataObject] | None:
    """Find the ObjectID of the object at the given path.

    Parameters
    ----------
    path
      Path to the object.

    Returns
    -------
    ObjectID
      The ID of the object at the given path.
    None
      If there was no object at path.

    """
    self._record_function_call_telemetry("find_object")
    parts = path.strip("/").split("/")
    # Remove empty strings (e.g. /surfaces/ = '', surfaces, '')
    parts = list(filter(None, parts))
    return self.__find_from(self.root_id, parts, create_if_not_found=False)

  def _find_object_or_create_if_missing(self, path: str
      ) -> ObjectID[Container]:
    """Find object ID of the object at the given path.

    Parameters
    ----------
    path
      The path to the object to get or create.

    Returns
    -------
    ObjectID
      The ID of the object at the given path.
    None
      If the path doesn't exist.

    """
    parts = path.strip("/").split("/")
    # Remove empty strings (e.g. /surfaces/ = '', surfaces, '')
    parts = list(filter(None, parts))
    return self.__find_from(self.root_id, parts, create_if_not_found=True)

  @contextmanager
  @typing.overload
  def read(self, path_or_id: str) -> Generator[DataObject, None, None]:
    ...

  @contextmanager
  @typing.overload
  def read(self, path_or_id: ObjectID[ObjectIdT]
      ) -> Generator[ObjectIdT, None, None]:
    ...

  @contextmanager
  @typing.overload
  def read(self, path_or_id: str, expected_object_type: type[ObjectT]
      ) -> Generator[ObjectT, None, None]:
    ...

  @contextmanager
  @typing.overload
  def read(
      self,
      path_or_id: ObjectID[ObjectIdT],
      expected_object_type: type[ObjectT]
      ) -> Generator[ObjectT, None, None]:
    ...

  @contextmanager
  def read(self,
      path_or_id: str | ObjectID[ObjectIdT],
      expected_object_type: type[ObjectT] | None = None
      ) -> Generator[DataObject | ObjectIdT | ObjectT, None, None]:
    """Open an existing object in read-only mode.

    In read-only mode the values in the object can be read, but no changes can
    be saved. Use this function instead of edit() if you do not intend to make
    any changes to the object.

    If this is called using a with statement, close() is called
    automatically at the end of the with block.

    Parameters
    ----------
    path_or_id
      The path or the ID of the object to open.
    expected_object_type
      The expected type for the object. If None (default), then the type will
      be determined automatically.
      If set to a DataObject subclass, the object will be opened as that
      subclass. If the object is not of this type, a TypeMismatchError will
      be raised.

    Raises
    ------
    ObjectDoesNotExistError
      If path_or_id is not an existent object.
    TypeMismatchError
      If expected_object_type is specified and path_or_id refers to an object
      which cannot be opened as that type.
    TypeError
      If path_or_id is an unsupported object.

    Examples
    --------
    Read an object at path/to/object/to/read and then print out the
    point, edge and facet counts of the object.

    >>> from mapteksdk.project import Project
    >>> project = Project()
    >>> path = "path/to/object/to/read"
    >>> with project.read(path) as read_object:
    ...     if hasattr(read_object, "point_count"):
    ...         print(f"{path} contains {read_object.point_count} points")
    ...     if hasattr(read_object, "edge_count"):
    ...         print(f"{path} contains {read_object.edge_count} edges")
    ...     if hasattr(read_object, "facet_count"):
    ...         print(f"{path} contains {read_object.facet_count} facets")
    ...     if hasattr(read_object, "cell_count"):
    ...         print(f"{path} contains {read_object.cell_count} blocks")
    ...     if hasattr(read_object, "block_count"):
    ...         print(f"{path} contains {read_object.block_count} blocks")

    The optional expected_object_type parameter can be used to ensure that
    the read object is of a specified type. This will cause Project.read()
    to raise an error if the object is not of the specified type, however it
    also guarantees that within the with block the read object will be of
    the specified type. This is demonstrated by the following example:

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import Surface
    >>> path = "path/to/object/to/read"
    >>> with Project() as project:
    ...     # Because the second argument was set to Surface, this will raise
    ...     # an error if the object is not a Surface.
    ...     with project.read(path, Surface) as surface:
    ...         # The surface variable is guaranteed to be a surface here,
    ...         # so it is not necessary to check if the object has these
    ...         # properties.
    ...         print(f"{path} contains {surface.point_count} points")
    ...         print(f"{path} contains {surface.edge_count} edges")
    ...         print(f"{path} contains {surface.facet_count} facets")
    """
    self._record_function_call_telemetry("read")
    if isinstance(path_or_id, ObjectID):
      object_id = path_or_id
    else:
      object_id = self.find_object(path_or_id)

    if not object_id or not object_id.exists:
      error_msg = f"Tried to read an object that doesn't exist: {path_or_id}"
      self.log.error(error_msg)
      raise ObjectDoesNotExistError(error_msg)

    if expected_object_type:
      # If the object type was specified raise an error if the object is
      # not of that type.
      # pylint: disable=protected-access
      if object_id._is_exactly_a(expected_object_type):
        object_type = expected_object_type
      else:
        actual_object_type = self._type_for_object(object_id)
        raise TypeMismatchError(expected_object_type, actual_object_type)
    else:
      # The object type was not specified, so derive it.
      object_type = self._type_for_object(object_id)

    opened_object = object_type(object_id, LockType.READ)
    try:
      yield opened_object
    finally:
      opened_object.close()

  @contextmanager
  def new(
      self,
      object_path: str | None,
      object_class: type[ObjectT] | ObjectT ,
      overwrite: bool | OverwriteMode=OverwriteMode.ERROR
      ) -> Generator[ObjectT, None, None]:
    """Create a new object and add it to the project. Note that
    changes made to the created object will not appear in the
    view until save() or close() is called.

    If this is called using a with statement, save() and close()
    are called automatically at the end of the with block.

    Parameters
    ----------
    object_path
      Full path for new object. e.g. "surfaces/generated/new surface 1"
      If None, the new object will not be assigned a path and will
      only be available through its object ID.
    object_class
      The type of the object to create. (e.g. Surface).
    overwrite
      How to handle attempting to add an object when there is already
      an object at full_path. See the documentation of OverwriteMode for
      more details on each option.
      The default is to raise an error if there is already an object
      at full_path.
      For backwards compatibility:
      Setting this to True is considered an alias for OverwriteMode.OVERWRITE.
      Setting this to False is considered an alias for OverwriteMode.ERROR.

    Yields
    ------
    DataObject
      The newly created object. The type of this will be object_class.

    Raises
    ------
    ValueError
      If an object already exists at new_path and overwrite = False.
    ValueError
      If object path is blank, '.' or '/'.
    TypeError
      If creating an object of the given type is not supported.
    NotImplementedError
      If creating an object of the given type is not implemented but may
      be implemented in a future version of the SDK.
    InvalidParentError
      If object_path contains an object that can't be a parent of the new
      object.

    Notes
    -----
    If an exception is raised while creating the object the object will
    not be saved.

    If you do not assign a path to an object on creation, project.add_object()
    can be used to assign a path to the object after creation.

    Examples
    --------
    Create a new surface and set it to be a square with side length
    of two and centred at the origin.

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import Surface
    >>> project = Project()
    >>> points = [[-1, -1, 0], [1, -1, 0], [-1, 1, 0], [1, 1, 0]]
    >>> facets = [[0, 1, 2], [1, 2, 3]]
    >>> with project.new("surfaces/square", Surface) as new_surface:
    ...   new_surface.points = points
    ...   new_surface.facets = facets
    ...   # new_surface.close is called implicitly here.

    """
    self._record_function_call_telemetry("new")
    # Background process:
    # Create empty object of provided type, get new handle & open write lock
    # with [yield >> user populates with data]
    # finally [done] >> Add to project
    if isinstance(object_class, type):
      # :TRICKY: Check if the user passed in a type, like Surface,
      # or instance of that type, like Surface(). This is
      # required to support more complicated types that require
      # constructor parameters to be useful (like DenseBlockModel(...)).
      # If not an instance, then create one:
      new_object = object_class(lock_type=LockType.READWRITE) # type: ignore
    else:
      new_object = object_class
    try:
      yield new_object
      # :NOTE: Jayden Boskell 2022-02-03 This isn't a
      # try...expect ObjectClosedError block because that could catch
      # developer errors where save() throw an ObjectClosedError.
      if not new_object.closed:
        new_object.save()
      if object_path is not None:
        # The new object does not yet exist as an item in the Project
        # add it now.
        self.add_object(object_path, new_object, overwrite=overwrite)
      new_object.close()
    except:
      # If there was an exception the object is an orphan,
      # so delete it then re-raise the exception.
      new_object.close()
      self._delete(new_object, True)
      raise

  @contextmanager
  @typing.overload
  def edit(self, path_or_id: str) -> Generator[DataObject, None, None]:
    ...

  @contextmanager
  @typing.overload
  def edit(self, path_or_id: ObjectID[ObjectIdT]
      ) -> Generator[ObjectIdT, None, None]:
    ...

  @contextmanager
  @typing.overload
  def edit(self, path_or_id: str, expected_object_type: type[ObjectT]
      ) -> Generator[ObjectT, None, None]:
    ...

  @contextmanager
  @typing.overload
  def edit(
      self,
      path_or_id: ObjectID[ObjectIdT],
      expected_object_type: type[ObjectT]
      ) -> Generator[ObjectT, None, None]:
    ...

  @contextmanager
  def edit(
      self,
      path_or_id: str | ObjectID[ObjectIdT],
      expected_object_type: type[ObjectT] | None = None
      ) -> Generator[DataObject | ObjectIdT | ObjectT, None, None]:
    """Open an existing object in read/write mode.

    Unlike read, this allows changes to be made to the object. Note that
    changes made will not appear in the view until save() or close() is called.

    If this is called using a with statement, save() and close()
    are called automatically at the end of the with block.

    Parameters
    ----------
    path_or_id
      Path or ID of the object to edit.
    expected_object_type
      The expected type for the object. If None (default), then the type will
      be determined automatically.
      If set to a DataObject subclass, the object will be opened as that
      subclass. If the object is not of this type, a TypeMismatchError will
      be raised.

    Yields
    ------
    DataObject
      The object at the specified path opened for editing.

    Raises
    ------
    ObjectDoesNotExistError
      If the object to edit does not exist.
    TypeMismatchError
      If expected_object_type is specified and path_or_id refers to an object
      which cannot be opened as that type.
    TypeError
      If the object type is not supported.

    Notes
    -----
    If an exception is raised while editing an object, any changes made
    inside the with block are not saved.

    Examples
    --------
    Edit the surface created in the example for project.new to a hourglass
    shape instead of a square.

    >>> from mapteksdk.project import Project
    >>> points = [[-1, -1, 0], [1, -1, 0], [-1, 1, 0], [1, 1, 0], [0, 0, 0]]
    >>> facets = [[0, 1, 4], [2, 3, 4]]
    >>> project = Project()
    >>> with project.edit("surfaces/square") as edit_surface:
    ...     edit_surface.points = points
    ...     edit_surface.facets = facets
    ...     # edit_surface.close is called implicitly here.

    One problem with the above example is that if the object at
    "surfaces/square" is not a Surface it will fail.
    e.g. If "surfaces/square" is a Polyline, Polygon or EdgeNetwork:

      * The assignment to "points" would succeed because these objects
        have points, just like a surface.
      * The assignment to "facets" would fail silently because Python allows
        the assignment even though the object does not have facets.
      * The script would exit with a success even though it actually failed
        to set the facets.

    This can be avoided by specifying the expected type of the object when
    opening it. This ensures that if the object is of an unexpected type, the
    script will fail before any changes have been made to the object. By failing
    quickly, the chances of unintentional changes are minimised.
    A fixed version of the above example is shown below:

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.data import Surface
    >>> points = [[-1, -1, 0], [1, -1, 0], [-1, 1, 0], [1, 1, 0], [0, 0, 0]]
    >>> facets = [[0, 1, 4], [2, 3, 4]]
    >>> project = Project()
    >>> # The second argument of Surface means this will fail immediately
    >>> # with an exception if the object at "surfaces/square" is not
    >>> # a surface.
    >>> with project.edit("surfaces/square", Surface) as edit_surface:
    ...     edit_surface.points = points
    ...     edit_surface.facets = facets
    """
    self._record_function_call_telemetry("edit")
    if isinstance(path_or_id, ObjectID):
      object_id = path_or_id
    else:
      object_id = self.find_object(path_or_id)

    if not object_id or not object_id.exists:
      error_msg = f"Tried to edit an object that doesn't exist: {path_or_id}"
      self.log.error(error_msg)
      raise ObjectDoesNotExistError(error_msg)

    if expected_object_type:
      # If the object type was specified raise an error if the object is
      # not of that type.
      # pylint: disable=protected-access
      if object_id._is_exactly_a(expected_object_type):
        object_type = expected_object_type
      else:
        actual_object_type = self._type_for_object(object_id)
        raise TypeMismatchError(expected_object_type, actual_object_type)
    else:
      # The object type was not specified, so derive it.
      object_type = self._type_for_object(object_id)

    # :NOTE: This won't work with self._run_with_undo() because of the
    # yield statement.
    undo_stack = self.__undo_stack
    if undo_stack is not None:
      undo_stack.raise_if_closed()
      clone_id, primary_children = self._get_before_state(object_id)
    else:
      clone_id, primary_children = (None, None)

    opened_object = object_type(object_id, LockType.READWRITE)
    try:
      yield opened_object
      # :NOTE: Jayden Boskell 2022-02-03 This isn't a
      # try...expect ObjectClosedError block because that could catch
      # developer errors where save() throw an ObjectClosedError.
      if not opened_object.closed:
        change_reasons = opened_object.save()

        if (undo_stack is not None
            and clone_id is not None
            and primary_children is not None):
          undo_stack.add_operation(
            clone_id,
            object_id,
            change_reasons,
            primary_children,
          )

    except:
      # Only some object types require cancelling the pending changes to an
      # object here, as many are written in such a way that the changes are
      # deferred until save().
      cancel = getattr(opened_object, 'cancel', None)
      if cancel and not opened_object.closed:
        cancel()

      raise
    finally:
      opened_object.close()

  @contextmanager
  def new_or_edit(
      self,
      path: str,
      object_class: ObjectT | type[ObjectT],
      overwrite: bool | OverwriteMode=OverwriteMode.ERROR
      ) -> Generator[ObjectT, None, None]:
    """Create the object or open it if it already exists.

    This function works as project.new if the specified object does not
    exist. Otherwise it acts as project.edit.

    Parameters
    ----------
    path
      Path to the object to create or edit.
    object_class
      Class of the object to create or edit.
    overwrite
      How to handle attempting to add an object when there is already
      an object at full_path. See the documentation of OverwriteMode for
      more details on each option.
      The default is to raise an error if there is already an object
      at full_path.
      For backwards compatibility:
      Setting this to True is considered an alias for OverwriteMode.OVERWRITE.
      Setting this to False is considered an alias for OverwriteMode.ERROR.

    Yields
    ------
    DataObject
      The newly created object or the object at the specified path.

    Raises
    ------
    ValueError
      If overwrite=False and there exists an object at path whose
      type is not object class.
    AttributeError
      If path is not a string.
    InvalidParentError
      If object_path contains an object that can't be a parent of the new
      object.

    """
    self._record_function_call_telemetry("new_or_edit")
    existing_id = self.find_object(path)

    # Edit if there is an object of the correct type at path. Otherwise
    # attempt to create a new object of the correct type at path.
    if existing_id and is_a(existing_id, object_class):
      with self.edit(existing_id) as opened_object:
        yield opened_object
    else:
      with self.new(path, object_class, overwrite) as opened_object:
        yield opened_object

  @contextmanager
  def undo(self) -> Generator[UndoStack, None, None]:
    """Allow operations within the with block to be undone in the application.

    This can only undo changes made by Project.edit(). It cannot
    undo object creation via Project.new(), nor can it undo changes
    made via any other functions in the project class.

    Parameters
    ----------
    _send
      If True (default), the undo operation is registered with the application
      when the with block ends.
      If False, the undo operation is not registered with the application.

    Raises
    ------
    UndoNotSupportedError
      If an unsupported object is edited during the with block.
      This includes VisualContainer and StandardContainer.

    Notes
    -----
    If an error occurs within a Project.undo() block, any changes which
    were successfully made within the block can be undone in the application.
    This may be changed in a future version of the SDK.

    Examples
    --------
    To make an edit to an object undoable, the Project.edit() block must be
    inside of the Project.undo() block. For example, to make a single
    edit block undoable:

    >>> from mapteksdk.project import Project
    >>> project = Project()
    >>> with project.undo(), project.edit("path/to/object"):
    ...     # The changes made inside this block will be undone when undo
    ...     # is pressed.
    ...     pass

    Using multiple project.undo() blocks allows for the script to create
    multiple undoable changes. For example, to fully undo the following
    script would require pressing undo twice:

    >>> from mapteksdk.project import Project
    >>> project = Project()
    >>> with project.undo(), project.edit("path/to/first/object"):
    ...     # A second press of the undo button is required to undo
    ...     # this change.
    ...     pass
    >>> with project.undo(), project.edit("path/to/second/object"):
    ...     # The first press of undo will undo this change.
    ...     pass

    Alternatively, to have multiple edits be undone with a single press of
    the undo button, place all of the project.edit() blocks inside of
    the same project.edit() block:

    >>> from mapteksdk.project import Project
    >>> project = Project()
    >>> # The two edits share an undo() block, so one click of undo will
    >>> # undo both changes.
    >>> with project.undo():
    ...     with project.edit("path/to/first/object"):
    ...         pass
    ...     with project.edit("path/to/second/object"):
    ...         pass
    """
    self._record_function_call_telemetry("undo")
    self.raise_if_version_below((1, 10))
    if self.__undo_stack is not None:
      yield self.__undo_stack
      # The outer context manager will handle sending the changes to the
      # server if required.
      return

    undo_stack = UndoStack()
    self.__undo_stack = undo_stack
    try:
      yield undo_stack
    finally:
      try:
        # This is in the finally block to ensure that the stack is still
        # sent even when an error occurs. But don't send the stack if it
        # has already been sent to the application.
        if not undo_stack.was_sent:
          undo_stack.send_to_application()
      finally:
        undo_stack.close()
        self.__undo_stack = None

  @typing.overload
  def __get_obj_handle(
    self,
    object_or_handle: DataObject
  ) -> T_ObjectHandle:
    ...

  @typing.overload
  def __get_obj_handle(
    self,
    object_or_handle: ObjectID[DataObject]
  ) -> T_ObjectHandle:
    ...

  @typing.overload
  def __get_obj_handle(
    self,
    object_or_handle: T_ObjectHandle
  ) -> T_ObjectHandle:
    ...

  @typing.overload
  def __get_obj_handle(
    self,
    object_or_handle: str
  ) -> T_ObjectHandle | None:
    ...

  def __get_obj_handle(
    self,
    object_or_handle: DataObject | ObjectID[DataObject] | T_ObjectHandle | str
  ) -> T_ObjectHandle | None:
    """Helper to retrieve T_ObjectHandle for passing to the C API.

    Parameters
    ----------
    object_or_handle
      Object with a handle, ID of an object, object handle or path to object.

    Returns
    -------
    T_ObjectHandle
      The object handle.
    None
      On exception.

    """
    if object_or_handle is None:
      return None

    if isinstance(object_or_handle, ObjectID):
      return object_or_handle.handle

    if isinstance(object_or_handle, str):
      object_id = self.find_object(object_or_handle)
      return None if object_id is None else object_id.handle

    if isinstance(object_or_handle, T_ObjectHandle):
      return object_or_handle

    return object_or_handle.id.handle

  def __get_oid(
      self,
      path_or_object: DataObject | ObjectID[DataObject] | str
  ) -> ObjectID[DataObject]:
    """Get the ObjectID for the given input.

    Parameters
    ----------
    path_or_object
      One of the following:
      * A DataObject subclass.
      * An ObjectID.
      * The handle of an open object.
      * The path to an object.

    Returns
    -------
    ObjectID
      Object id associated with the input.

    Raises
    ------
    ValueError
      If an input object does not exist.
    TypeError
      If an input is not a supported type.
    """
    if isinstance(path_or_object, ObjectID):
      oid = path_or_object
    elif isinstance(path_or_object, str):
      oid = self.find_object(path_or_object)
    elif isinstance(path_or_object, DataObject):
      oid = path_or_object.id
    else:
      raise TypeError(
        default_type_error_message(
          argument_name="path_or_object",
          actual_value=path_or_object,
          required_type=(DataObject, ObjectID, str)
        )
      )
    if oid is None or not oid.exists:
      raise ValueError(
        "The specified object did not exist."
      )
    return oid


  @typing.overload
  def add_object(
      self,
      full_path: str,
      new_object: ObjectID[ObjectIdT],
      overwrite: bool | OverwriteMode=OverwriteMode.ERROR
      ) -> ObjectID[ObjectIdT]:
    ...

  @typing.overload
  def add_object(
      self,
      full_path: str,
      new_object: ObjectT,
      overwrite: bool | OverwriteMode=OverwriteMode.ERROR) -> ObjectID[ObjectT]:
    ...

  def add_object(
      self,
      full_path: str,
      new_object: ObjectT | ObjectID[ObjectIdT],
      overwrite: bool | OverwriteMode=OverwriteMode.ERROR
      ) -> ObjectID[ObjectT | ObjectIdT]:
    r"""Adds a new DataObject to the project.

    Normally this is not necessary because Project.new() will add the object
    for you. This should only need to be called if Project.new() was called
    with path = None or after a call to a function from the mapteksdk.io module.

    Parameters
    ----------
    full_path
      Full path to the new object (e.g. '/surfaces/new obj').
    new_object : DataObject or ObjectID
      Instance or ObjectID of the object to store at full_path.
    overwrite
      How to handle attempting to add an object when there is already
      an object at full_path. See the documentation of OverwriteMode for
      more details on each option.
      The default is to raise an error if there is already an object
      at full_path.
      For backwards compatibility:
      Setting this to True is considered an alias for OverwriteMode.OVERWRITE.
      Setting this to False is considered an alias for OverwriteMode.ERROR.

    Returns
    -------
    ObjectID
      ID of newly stored object. This will be the object ID of
      new_object.

    Raises
    ------
    ValueError
      If invalid object name (E.g. '/', '', or (starting with) '.' when
      project options don't allow hidden objects).
    ValueError
      If path contains back slashes (\).
    ValueError
      If overwrite=False and there is already an object at full_path.
    TypeError
      If full_path is not a string.
    TypeError
      If new_object is not a DataObject or ObjectID
    InvalidParentError
      If new_object is being added to an object that is not a container.
      Topology objects are not considered containers when the project options
      don't allow hidden objects. The fact that they're containers is a
      implementation detail and they're not portrayed as containers to end
      users in the applications.

    Notes
    -----
    Has no effect if new_object is already at full_path.
    """
    self._record_function_call_telemetry("add_object")
    if not isinstance(full_path, str):
      raise TypeError(
        default_type_error_message("full_path", full_path, str)
      )
    container_path, object_name = valid_path(
      full_path,
      allow_hidden_objects=self.allow_hidden_objects
    )
    result = self.add_objects(
      container_path,
      [(object_name, new_object)],
      overwrite=overwrite
    )
    # add_objects() will return the correct ObjectID.
    return result[0] # type: ignore

  def add_objects(
    self,
    destination_container: str,
    new_objects: Iterable[tuple[str, ObjectID[DataObject] | DataObject]] |
                 Mapping[str, ObjectID[DataObject] | DataObject],
    overwrite: bool | OverwriteMode=OverwriteMode.ERROR
  ) -> list[ObjectID[DataObject]]:
    r"""Adds multiple objects into the project.

    This can be used to batch the insertions. Most likely you will want to use
    this with an object that hasn't been added to the project before. You can
    avoid adding new objects to the project when calling Project.new() by
    providing a path of None.

    This is treated as an atomic operation so either all objects are added or
    none are added. This means if there is a problem with adding one of the
    objects then none of the objects will be added and the destination
    container will remain unchanged.

    Parameters
    ----------
    destination_container
      Full path to the container where the objects will be added.
    new_objects
      If new_objects is a dictionary then the keys are names and the values
      are the objects to add.
      If new_objects is a list then the list should contain (name, object)
      pairs.
      The objects can be either DataObject or ObjectID.
    overwrite
      How to handle attempting to add an object with a name which is already
      used in the container. See the documentation of OverwriteMode for
      more details on each option.
      The default is to raise an error if there is already an object
      with the given name.
      For backwards compatibility:
      Setting this to True is considered an alias for OverwriteMode.OVERWRITE.
      Setting this to False is considered an alias for OverwriteMode.ERROR.

    Returns
    -------
    list
      A list of object IDs of newly added objects.
      This will be in the same order as add_objects().
      If an object was already in the container under that name it will still
      be returned even when it wasn't added.

    Raises
    ------
    ValueError
      If invalid object name (E.g. '/', '', or (starting with) '.' when
      project options don't allow hidden objects).
    ValueError
      If paths contains back slashes (\).
    ValueError
      If overwrite=False and there is already an object in the destination
      container with that name and it is not the object being added.
    InvalidParentError
      If destination_container or an object in the path is not a container.
      Topology objects are not considered containers when the project options
      don't allow hidden objects. The fact that they're containers is a
      implementation detail and they're not portrayed as containers to end
      users in the applications.

    Warnings
    --------
    For older versions of the application, if an error occurs any objects added
    prior to the object which triggered the error will still be added.

    Notes
    -----
    If any object in new_objects is already in the destination container with
    the specified name, it will be left unchanged.
    """
    self._record_function_call_telemetry("add_objects")
    if destination_container in ("", "/"):
      container_object = self.root_id
    else:
      parent_name, container_name = valid_path(
        destination_container, self.allow_hidden_objects)
      container_object = self._find_object_or_create_if_missing(
        posixpath.join(parent_name, container_name))

    if not container_object:
      raise InvalidParentError("new_object", destination_container)

    if not container_object.is_a(Container) or (
        container_object.is_a(Topology) and not self.allow_hidden_objects):
      raise InvalidParentError("new_objects", destination_container)

    if not isinstance(overwrite, OverwriteMode):
      if overwrite:
        overwrite = OverwriteMode.OVERWRITE
      else:
        overwrite = OverwriteMode.ERROR

    try:
      if isinstance(new_objects, Mapping):
        # Mapping[tuple[str, ObjectID], typing.Any] is a
        # Iterable[tuple[str, ObjectID]]. If such a value was passed to this
        # function, it would pass static type checking.
        # In that case, items would be set to be an
        # ItemsView[tuple[str, ObjectID], typing.Any] instead of an
        # ItemsView[str, ObjectID] which would result in an AttributeError
        # during the dictionary comprehension, which is caught and converted
        # into a type error.
        items = new_objects.items()
      else:
        items = new_objects
      object_ids_to_add: list[tuple[str, ObjectID[DataObject]]] = [
        (
          name,
          new_object if isinstance(new_object, ObjectID) else new_object.id
        )
        for name, new_object in items
      ] # type: ignore
    except AttributeError:
      raise TypeError(
        "new_objects contained an object which was not an ObjectID "
        "or a DataObject subclass."
      ) from None

    self._run_with_undo(
      container_object,
      partial(
        # pylint: disable=protected-access
        add_objects_with_overwrite,
        objects_to_add=object_ids_to_add,
        allow_hidden_objects=self.allow_hidden_objects,
        overwrite=overwrite
      )
    )

    return [oid for _, oid in object_ids_to_add]

  def get_children(self, path_or_id: str | ObjectID[DataObject]=""
      ) -> ChildView:
    """Return the children of the container at path as (name, id) pairs.

    Parameters
    ----------
    path_or_id
      The path or object ID of the container to work with.

    Returns
    -------
    ChildView
      Provides a sequence that can be iterated over to provide the
      (name, id) for each child. It also provides name() and ids() functions
      for querying just the names and object IDs respectively.

    Raises
    ------
    ObjectDoesNotExistError
      If the path does not exist in the project.
    TypeError
      If the path is not a container.
    ValueError
      If the path is a container but not suitable for accessing its children.

    """
    self._record_function_call_telemetry("get_children")

    if isinstance(path_or_id, str):
      if path_or_id and path_or_id != '/':
        container = self.find_object(path_or_id)
      else:
        container = self.root_id
    else:
      container = path_or_id
      path_or_id = '/'

    if not container:
      message_template = '"%s" is not in the project.'
      self.log.error(message_template, path_or_id)
      raise ObjectDoesNotExistError(message_template % path_or_id)

    if not container.is_a(Container):
      message_template = 'The object "%s" (%s) is not a container.'
      self.log.error(message_template, path_or_id, container)
      raise TypeError(
        default_type_error_message(
          argument_name="path_or_id",
          actual_value=path_or_id,
          required_type=(str, ObjectID[Container])
        )
      )

    # TODO: Prevent the users from querying the children of certain objects
    # that they don't see as being containers like edge chain/loops
    # (topologies). This issue is tracked by SDK-46.

    with self.read(ObjectID(self.__get_obj_handle(container))) as container:
      container.allow_hidden_objects = self.allow_hidden_objects
      return ChildView(container.items())

  def get_descendants(self, path_or_id: str | ObjectID[Container]=""
      ) -> ChildView:
    """Return all descendants of the container at path as (name, id) pairs.

    Parameters
    ----------
    path_or_id
      The path or object ID of the container to work with.

    Returns
    -------
    ChildView
      Provides a sequence that can be iterated over to provide the
      (name, id) for each child. It also provides name() and ids() functions
      for querying just the names and object IDs respectively.

    Raises
    ------
    KeyError
      If the path does not exist in the project.
    TypeError
      If the path is not a container.
    ValueError
      If the path is a container but not suitable for accessing its children.

    """
    self._record_function_call_telemetry("get_descendants")
    def list_all_descendants(parent: str | ObjectID[Container]
        ) -> list[tuple[str, ObjectID[DataObject]]]:
      # Recursive function to retrieve all children of all VisualContainers
      results = []
      for child_name, child_id in self.get_children(parent):
        results.append((child_name, child_id))
        if child_id.is_a(VisualContainer):
          if isinstance(parent, str):
            # if provided, use a path to define the next level of the family,
            # avoiding any issue where an ObjectID has multiple paths.
            path = posixpath.join(parent, child_name)
            results.extend(list_all_descendants(path))
          else:
            results.extend(list_all_descendants(child_id))
      return results
    return ChildView(list_all_descendants(path_or_id))

  @typing.overload
  def copy_object(
      self,
      object_to_clone: ObjectID[ObjectIdT],
      new_path: str,
      overwrite: bool | OverwriteMode=OverwriteMode.ERROR,
      allow_standard_containers: bool=False) -> ObjectID[ObjectIdT]:
    ...

  @typing.overload
  def copy_object(
      self,
      object_to_clone: str,
      new_path: str,
      overwrite: bool | OverwriteMode=OverwriteMode.ERROR,
      allow_standard_containers: bool=False) -> ObjectID[DataObject]:
    ...

  @typing.overload
  def copy_object(
      self,
      object_to_clone: ObjectT,
      new_path: str,
      overwrite: bool | OverwriteMode=OverwriteMode.ERROR,
      allow_standard_containers: bool=False) -> ObjectID[ObjectT]:
    ...

  @typing.overload
  def copy_object(
      self,
      object_to_clone: ObjectID[ObjectIdT],
      new_path: None,
      overwrite: bool | OverwriteMode=OverwriteMode.ERROR,
      allow_standard_containers: bool=False) -> ObjectID[ObjectIdT]:
    ...

  @typing.overload
  def copy_object(
      self,
      object_to_clone: str,
      new_path: None,
      overwrite: bool | OverwriteMode=OverwriteMode.ERROR,
      allow_standard_containers: bool=False) -> ObjectID[DataObject]:
    ...

  @typing.overload
  def copy_object(
      self,
      object_to_clone: ObjectT,
      new_path: None,
      overwrite: bool | OverwriteMode=OverwriteMode.ERROR,
      allow_standard_containers: bool=False) -> ObjectID[ObjectT]:
    ...

  def copy_object(
      self,
      object_to_clone: ObjectT | ObjectID[ObjectIdT] | str,
      new_path: str | None,
      overwrite: bool | OverwriteMode=OverwriteMode.ERROR,
      allow_standard_containers: bool=False) -> ObjectID[
        ObjectIdT | ObjectT | DataObject] | None:
    """Deep clone DataObject to a new object (and ObjectID).

    If this is called on a container, it will also copy all of the
    container's contents.

    Parameters
    ----------
    object_to_clone
      The object to clone or the ID for the object to clone
      or a str representing the path to the object.
    new_path
      Full path to place the copy (e.g. 'surfaces/new/my copy').
      Set as None to make the copied object an orphan. This is useful when
      copying a large number of objects because it is more efficient
      to add each object to the container as a batch using `add_objects()`.
    overwrite
      How to handle attempting to add an object when there is already
      an object at full_path. See the documentation of OverwriteMode for
      more details on each option.
      The default is to raise an error if there is already an object
      at full_path.
      For backwards compatibility:
      Setting this to True is considered an alias for OverwriteMode.OVERWRITE.
      Setting this to False is considered an alias for OverwriteMode.ERROR.
    allow_standard_containers
      If False (default) then attempting to copy a standard container
      will create a visual container instead.
      If True (not recommended) copying a standard container will
      create a new standard container.

    Returns
    -------
    ObjectID
      Id of new object (The clone).
    None
      If the operation failed.

    Raises
    ------
    ObjectDoesNotExistError
      If object_to_clone does not exist.
    ValueError
      If an object already exists at new_path and overwrite = False.
    RuntimeError
      If object_to_clone is a DataObject subclass and it is open with
      Project.edit().

    """
    self._record_function_call_telemetry("copy_object")
    source_id = object_to_clone
    if isinstance(object_to_clone, str):
      source_id = self.find_object(object_to_clone)
    elif isinstance(object_to_clone, DataObject):
      # pylint: disable=protected-access
      # Error if the object is opened for editing. Because the changes
      # made in the SDK are cached until save() is called, copying an
      # object open for editing has surprising behaviour where it will
      # copy the object as it was before it was opened for editing.
      if (object_to_clone.lock_type is LockType.READWRITE
          and not object_to_clone.closed):
        raise RuntimeError("Cannot copy an object open for editing.")
      source_id = object_to_clone.id

    # This allows type(None) because the None case is handled by the
    # next if statement.
    if not isinstance(source_id, (ObjectID, type(None))):
      raise TypeError(default_type_error_message(
        "object_to_clone",
        object_to_clone,
        ObjectID))

    if source_id is None or not source_id.exists:
      raise ObjectDoesNotExistError(
          f"Cannot copy non-existent object: '{object_to_clone}'"
        )

    if not isinstance(new_path, (str, type(None))):
      raise TypeError(default_type_error_message("new_path", new_path, str))

    # Special handling for standard containers.
    #
    # Copying a standard container creates a visual container instead
    # of a standard container. This is what happens in the application when
    # the user user copies and pastes a standard container.
    #
    # If allow_standard_containers then this is not done and a new standard
    # container will created.
    if is_a_standard_container(source_id) and not allow_standard_containers:
      # pylint thinks source is a scan.
      # pylint: disable=no-member
      with self.read(source_id) as source:
        # It is hard to know why the container had hidden objects and thus if
        # they should always be copied. The behaviour to date has been to only
        # copy hidden objects if its allowed.
        source.allow_hidden_objects = self.allow_hidden_objects
        source_children = source.items()

      with self.new(new_path, VisualContainer, overwrite=False) as copy:
        # Clone each object in the standard container and add to copy.
        for child_name, child_id in source_children:
          copied_child_id = self.copy_object(child_id, new_path=None)
          copy.append((child_name, copied_child_id))

      return copy.id

    old_handle = self.__get_obj_handle(source_id)
    with ReadLock(old_handle, self._data_engine_api) as r_lock:
      copyobj = ObjectID(self._data_engine_api.CloneObject(r_lock.lock, 0))
      if not copyobj:
        last_error = self._data_engine_api.ErrorMessage()
        self.log.error('Failed to clone object %s because %s',
                       object_to_clone, last_error)

    self.log.debug("Deep copy %s to %s",
                   old_handle,
                   new_path if new_path is not None else "[Backend Object]")
    if new_path is not None:
      return self.add_object(new_path, copyobj, overwrite=overwrite)
    return copyobj

  def rename_object(
      self,
      object_to_rename: DataObject | ObjectID[DataObject] | str,
      new_name: str,
      overwrite: bool | OverwriteMode=OverwriteMode.ERROR,
      allow_standard_containers: bool=False) -> bool:
    """Rename (and/or move) an object.

    Renaming an object to its own name has no effect.

    Parameters
    ----------
    object_to_rename
      The object to rename or
      the ID of the object to rename or
      full path to object in the Project.
    new_name
      new name for object.
      Standalone name (e.g. 'new tri') will keep root path.
      Full path (e.g. 'surfaces/new tri') will change location.
      Prefix with '/' (e.g. '/new tri' to move to the root
      container).
    overwrite
      How to handle attempting to add an object when there is already
      an object at full_path. See the documentation of OverwriteMode for
      more details on each option.
      The default is to raise an error if there is already an object
      at full_path.
      For backwards compatibility:
      Setting this to True is considered an alias for OverwriteMode.OVERWRITE.
      Setting this to False is considered an alias for OverwriteMode.ERROR.
    allow_standard_containers
      If False (default) then attempting to rename a standard container
      will create a new container and move everything in the standard
      container into the new container.
      If True (not recommended) standard containers can be renamed.

    Returns
    -------
    bool
      True if rename/move successful,
      False if failed (overwrite checks failed).

    Raises
    ------
    ValueError
      New object name begins with full stop when project
      attribute allow_hidden_objects is False (default).
    ValueError
      New object name can't be '.'.
    ValueError
      If there is already an object at new_name and overwrite=False.
    ObjectDoesNotExistError
      Attempting to rename an object that doesn't exist.
    DeleteRootError
      Attempting to rename root container.

    Notes
    -----
    new_name can not start with a full stop '.' when allow_hidden_objects is
    False and cannot be '/' or '' or '.'.

    """
    self._record_function_call_telemetry("rename_object")
    object_to_rename = ObjectID(self.__get_obj_handle(object_to_rename))

    # Safety checks:
    if not object_to_rename:
      error_message = "Unable to locate object for renaming"
      self.log.error(error_message)
      raise ObjectDoesNotExistError(error_message)

    if object_to_rename == self.root_id:
      error_message = "Can't rename root container"
      self.log.error(error_message)
      raise DeleteRootError(error_message)

    # Special handling for standard containers.
    # Rename creates a new visual container and moves the standard container's
    # contents into the copy.
    # If allow_standard_containers, this is bypassed.
    if is_a_standard_container(object_to_rename) \
      and not allow_standard_containers:

      # pylint thinks source is a scan.
      # pylint: disable=no-member
      with self.edit(object_to_rename) as standard_container:
        with self.new(new_name, VisualContainer,
                      overwrite=overwrite) as new_container:

          for child in standard_container.items():
            new_container.append(child)

        standard_container.clear()

      return True

    # Shift/rename object or container:
    old_parent = object_to_rename.parent
    if old_parent:
      old_parent_path = old_parent.path
    else:
      old_parent_path = ''  # The object is not in a container.

    new_parent_path, new_obj_name = valid_path(
      new_name, self.allow_hidden_objects)
    new_parent_is_root = new_parent_path == '' and new_name.startswith('/')

    if not new_parent_path and not new_parent_is_root:
      new_parent_path = old_parent_path

    old_path = object_to_rename.path.strip('/')
    new_path = (new_parent_path + "/" + new_obj_name).strip('/')

    if old_path == new_path:
      # Moving the object to where it already is. Nothing needs to be done.
      return True

    if overwrite is OverwriteMode.ERROR and self.find_object(new_path):
      raise ValueError(
        f"There is already an object at {new_path}."
      )

    if old_parent and old_path:
      # If the object is in a container then we check to ensure its in a path
      # that should be manipulated (accounting for if it is within a hidden
      # container).
      #
      # The path of an orphan is invalid, orphans must use object ID or be
      # a path relative to a starting object ID.
      if old_parent.is_orphan:
        if not self.allow_hidden_objects:
          # Check that none of the ancestors or the object to rename are
          # hidden objects.
          names = [object_to_rename.name]
          ancestor = old_parent
          while ancestor.parent:
            names.append(ancestor.name)
            ancestor = ancestor.parent

          if any(name.startswith(".") for name in names):
            raise ValueError("Cannot move a hidden objects.")
      else:
        try:
          valid_path(old_path, self.allow_hidden_objects)
        except HiddenObjectPermissionError:
          message = f"The object to rename is hidden ({old_path}) and " + \
            "can't be renamed."
          raise ValueError(message) from None

    def remove_from_container(w_lock: WriteLock):
      try:
        self._data_engine_api.ContainerRemoveObject(
      w_lock.lock, object_to_rename.handle, False)
      except OSError:
        self.log.exception(
          "Error while removing object %r from container %r",
          old_parent, object_to_rename)

    # If the object didn't have a parent, then it wasn't in a container so
    # there is no need to remove it from a container.
    if old_parent:
      self._run_with_undo(
        old_parent,
        remove_from_container
      )

    # :TRICKY: add_object() will make object_to_rename a primary
    # child of the destination container, so it must be called
    # after the before state of the source container is generated.
    # This ensures that the primary children of the source container
    # will be generated correctly.
    self.add_object(
      new_path,
      object_to_rename,
      overwrite=overwrite)

    return True

  def delete_container_contents(
      self,
      container: ObjectID[VisualContainer] | str):
    """Deletes all the contents of a container.

    Any child objects that are not in another container will be deleted.

    Parameters
    ----------
    container
      the object to delete or
      the ID for the object to delete or
      path to container (e.g. '/surfaces/old').

    Raises
    ------
    ObjectDoesNotExistError
      If container is not an existent object.
    """
    self._record_function_call_telemetry("delete_container_contents")
    self.log.info("Delete container contents: %s", container)
    with self.edit(container) as editable_container: # type: ignore
      editable_container: Container
      editable_container.allow_hidden_objects = self.allow_hidden_objects
      editable_container.clear()

  def new_visual_container(
      self, parent_container: str, container_name: str
      ) -> ObjectID[VisualContainer]:
    """Creates a new visual container.

    Parameters
    ----------
    parent_container
      The path to the parent container or the parent container.
    container_name
      New container name.

    Returns
    -------
    ObjectID
      The object ID for newly created container.

    Raises
    ------
    ValueError
      When attempting to create a container name or part of path
      that would result in hidden objects (i.e. starts with '.')
      and allow_hidden_objects is False.
    ValueError
      If the container name contains "/" characters.
    ValueError
      If there is already an object called container_name in parent_container.
    InvalidParentError
      If object_path contains an object that can't be a parent of the new
      object.

    Examples
    --------
    To add a visual container to the root container, use "/" as the parent
    container name. The following example creates a container called
    "example_container" in the root container.

    >>> from mapteksdk.project import Project
    >>> project = Project()
    >>> project.new_visual_container("/", "example_container")

    To add a visual container to another container, use the path to
    that container as the container name. The following example
    creates a container called "sub_container" in the "example_container"
    created in the previous example.

    >>> from mapteksdk.project import Project
    >>> project = Project()
    >>> project.new_visual_container("example_container", "sub_container")

    This is the full path to that container if that container is in another
    container. The following example creates a container called
    "sub_sub_container" inside the "sub_container" created in the
    previous example. In particular, note that the path to "sub_container"
    includes a "/" because it is inside of another container.

    >>> from mapteksdk.project import Project
    >>> project = Project()
    >>> project.new_visual_container(
    ...     "example_container/sub_container",
    ...     "sub_sub_container"
    ... )
    """
    self._record_function_call_telemetry("new_visual_container")
    if parent_container not in ["", "/"]:
      parent_container = "/".join(valid_path(
        parent_container, self.allow_hidden_objects))
    elif parent_container == "/":
      # Always refer to the root container as a blank parent name.
      # Referring to it as a slash results in two slashes at the start
      # of the path, which is invalid.
      parent_container = ""
    check_path_component_validity(container_name, self.allow_hidden_objects)

    new_container = ObjectID(self._modelling_api.NewVisualContainer())

    # add_object() will create the container hierarchy up to and including
    # parent_container.
    self.add_object(f"{parent_container}/{container_name}", new_container)
    self.log.info("Created new container: [%s] under [%s]",
                  container_name,
                  parent_container)
    return new_container

  def delete(
      self,
      mdf_object_or_name: str | DataObject | ObjectID[DataObject],
      allow_standard_containers: bool=False) -> bool:
    """Deletes the given object.

    Parameters
    ----------
    mdf_object_or_name
      Container name, instance of object as DataObject or
      ObjectID of the object.

    allow_standard_containers
      If False (default) then attempting to delete a standard
      container will result in the container contents being deleted.
      If True then standard containers will be deleted. See warnings
      for why you shouldn't do this.

    Returns
    -------
    bool
      True if deleted successfully or False if not.

    Raises
    ------
    DeleteRootError
      If the object provided is the root container.
    UndoNotSupportedError
      If called inside of a Project.undo() block. This permanently deletes
      objects, so it cannot be undone. For an undoable delete, use
      Project.recycle().
    RuntimeError
      If the the object can't be deleted. The most common cause is something
      is writing to the object at this time.

    Warnings
    --------
    Deleting a standard container created by a Maptek application
    may cause the application to crash. The allow_standard_containers
    flag should only be used to delete standard containers you have created
    yourself (It is not recommended to create your own standard containers).

    """
    self._record_function_call_telemetry("delete")
    if self.__undo_stack is not None:
      raise UndoNotSupportedError(
        "Project.delete() cannot be called inside of a Project.undo() block. "
        "Call Project.recycle() instead."
      )
    self.log.info("Delete object: %s", mdf_object_or_name)
    try:
      if isinstance(mdf_object_or_name, str):
        object_id = self.find_object(mdf_object_or_name)
        if object_id:
          self._delete(object_id, allow_standard_containers)
      else:
        self._delete(mdf_object_or_name, allow_standard_containers)
      return True
    except RuntimeError as error:
      self.log.error("Error deleting object: %s [%s]",
                     mdf_object_or_name, error)
      raise

  def _delete(
      self,
      mdf_object: DataObject | ObjectID[DataObject],
      allow_standard_containers: bool) -> None:
    """Internal delete - by object (not string).

    Parameters
    ----------
    mdf_object
      The object to delete.
    allow_standard_containers
      If False (default) then attempting to delete a standard
      container will result in the container contents being deleted.
      If True then standard containers will be deleted.

    Raises
    ------
    DeleteRootError
      If the object provided is the root container.
    RuntimeError
      If the the object can't be deleted. The most common cause is something
      is writing to the object at this time.
    """
    handle = self.__get_obj_handle(mdf_object)
    if handle is None:
      return
    object_id = ObjectID(handle)
    if object_id == self.root_id:
      raise DeleteRootError("You cannot delete the root container.")

    # Special handling for standard containers.
    # Deleting a standard container deletes its contents
    # and leaves the container untouched.
    # If allow_standard_containers, this is bypassed.
    if is_a_standard_container(object_id) and not allow_standard_containers:
      self.delete_container_contents(object_id)
      return

    # Special handling for the recycle bin. Only delete its contents.
    if object_id and object_id == self.recycle_bin_id:
      self.delete_container_contents(object_id)
      return

    success = self._data_engine_api.DeleteObject(handle)
    if not success:
      error = self._data_engine_api.ErrorMessage()
      raise RuntimeError(error)

  def _type_for_object(
      self,
      object_handle: DataObject | ObjectID[DataObject]) -> type:
    """Return the type of an object based on the object ID without needing
    to read the object.

    Parameters
    ----------
    object_handle
      The object to query the type for.

    Returns
    --------
    type
      The DataObject type e.g. Surface, Marker as type only.

    Raises
    ------
    TypeError
      If the object handle is of a type that isn't known or supported.
    ObjectDoesNotExistError
      If object_handle does not refer to a valid object.

    """
    handle = self.__get_obj_handle(object_handle)
    if handle is None:
      error_message = "Unable to locate object"
      self.log.error(error_message)
      raise ObjectDoesNotExistError(error_message)

    object_type = self._data_engine_api.ObjectDynamicType(handle)

    # The types for data list is sorted such that iterating over it
    # will check derived types before base types.
    for _, class_type in self.__types_for_data:
      try:
        type_index = class_type.static_type()
        if self._data_engine_api.TypeIsA(object_type, type_index):
          return class_type
      except (CApiDllLoadFailureError, ApplicationTooOldError):
        # The application doesn't support this type, either because the
        # application doesn't support it (e.g. PointStudio doesn't support
        # Drillholes) or the C API is too old to read the type.
        # Move onto the next type.
        continue

    # This doesn't use an is_a() because we want to handle the case where a
    # plain container was created. Typically a Container is a base-class
    # of higher level types and treating them as such wouldn't be ideal.
    if object_type.value == Container.static_type().value:
      return Container

    raise TypeError('Unsupported object type')

  def get_selected(self) -> Selection[DataObject]:
    """Return the IDs of the selected objects.

    When connected to an existing application, these are the objects selected
    in that application (via the explorer, view or some other method).

    Returns
    -------
    Selection
      A list of selected ObjectIDs.

    """
    self._record_function_call_telemetry("get_selected")
    return Selection.active_selection()

  def set_selected(
      self,
      object_ids_or_paths:
        Selection |
        Sequence[str | ObjectID[DataObject] | DataObject] |
        str |
        ObjectID[DataObject] | None=None,
      include_descendants: bool=True) -> None:
    """Set active project selection to one or more objects.

    If None specified, selection will be cleared.
    If objects are provided but are not valid, they will not be selected.
    No action will be taken if entire selection specified is invalid.
    Any VisualContainer objects specified will include their descendants.

    Parameters
    ----------
    mdf_objects_or_paths
      List of object paths to select, List of ObjectID to select,
      path to object to select, ObjectID of object to select.
      Pass None or an empty list to clear the existing selection.
    include_descendants
      whether to also select descendants of any VisualContainer provided
      within the selection criteria (default=True).

    Raises
    -------
    ValueError
      If any or all objects within the selection specified is invalid.

    Warning
    -------
    If this is called inside of a Project.undo() block it must either be the
    first or last undoable function in the block.

    Notes
    -----
    If this is called inside a Project.undo() block, then the selection change
    can be undone.
    """
    self._record_function_call_telemetry("set_selected")
    # The changes are only undoable if called in a Project.undo() block.
    allow_undo = False
    undo_stack = self.__undo_stack
    if undo_stack is not None:
      allow_undo = True
      if len(undo_stack) != 0:
        undo_stack.close(
          error_message="The call to Project.set_selected() must either be "
            "the first or last call in a Project.undo() block."
        )
        undo_stack.send_to_application()

    if not object_ids_or_paths:
      # Clear selection
      self.log.info("Clearing active object selection")
      self._data_engine_api.SetSelectedObjects(None, 0)
    else:
      # List of selected visual containers.
      containers: list[ObjectID[Container]] = []
      # Handles of the selected objects.
      selected_oids: list[ObjectID[DataObject]] = []
      if not isinstance(object_ids_or_paths, Iterable) or \
          isinstance(object_ids_or_paths, str):
        object_ids_or_paths = [object_ids_or_paths]

      # Ensure all objects provided are valid and exist
      for path_or_id in object_ids_or_paths:
        try:
          oid = self.__get_oid(path_or_id)
          if oid.is_a(VisualContainer):
            containers.append(oid) # type: ignore
          selected_oids.append(oid)
        except (ValueError, TypeError):
          error_msg = (
            f"An invalid object ({path_or_id}) was specified for "
            "selection.\nVerify objects specified in the "
            "selection are valid and still exist.")
          self.log.error(error_msg)
          raise ValueError(error_msg) from None

      if include_descendants:
        # Include handles of descendant objects for any VisualContainer objects
        # specified and their children.
        descendants: list[ObjectID[DataObject]] = []
        for path_or_id in containers:
          descendants.extend(self.get_descendants(path_or_id).ids())
        if descendants:
          self.log.info("Adding %d descendant objects to selection",
                        len(descendants))
          selected_oids.extend(child for child in descendants)

      selection = Selection(selected_oids)

      # Only update the explorer if connected to an application.
      #
      # This does not take into account if NewBackend is used with a uiServer.
      update_explorer = False
      if self.__backend and self.__backend.has_project_explorer:
        update_explorer = True

      # pylint: disable=protected-access
      selection._make_active_selection(
        update_explorer=update_explorer,
        allow_undo=allow_undo
      )

  @property
  def recycle_bin_id(self) -> ObjectID:
    """The object ID of the recycle bin.

    Returns
    -------
    ObjectID
      The ID of the recycle bin object.

    Raises
    ------
    NoRecycleBinError
      The project has no recycle bin.

    See Also
    --------
    recycle: Move an object to the recycle bin.
    """
    self._record_function_call_telemetry("recycle_bin_id")
    if self._data_engine_api.version >= (1, 8):
      recycle_bin = ObjectID(self._data_engine_api.RecycleBin(
        self._backend.index))
    else:
      # For older versions of the applications that don't have the C API
      # function, use an alternative.
      recycle_bin = self.__find_from(
        self.root_id, ['.system', 'Recycle Bin'], create_if_not_found=False)

    if not recycle_bin:
      raise NoRecycleBinError()

    return recycle_bin

  def recycle(self, object_to_recycle: DataObject | ObjectID[DataObject]):
    """Move the given object to the recycle bin.

    This does not provide the ability to recycle a standard container because
    the user will be unable to move the item out of the recycle bin.

    Raises
    ------
    NoRecycleBinError
      The project has no recycle bin.
    """
    self._record_function_call_telemetry("recycle")
    object_to_recycle = ObjectID(self.__get_obj_handle(object_to_recycle))
    object_to_recycle_name = object_to_recycle.name

    # This does not honour the user operations that can be set either per-type
    # or per-object, which would otherwise prevent the user from moving the
    # object to the recycle bin (known as deleting it in the software).

    if is_a_standard_container(object_to_recycle):
      # Collect up the children and remove them from the container.
      children_to_recycle = self.get_children(object_to_recycle).ids()
      for child in children_to_recycle:
        self.recycle(child)

      return

    recycle_bin = self.recycle_bin_id

    # Remove the object from its parents.
    parent = object_to_recycle.parent
    while parent and not parent.is_orphan:
      def remove_from_parent(w_lock: WriteLock):
        self._data_engine_api.ContainerRemoveObject(
          w_lock.lock, object_to_recycle.handle, True)
      self._run_with_undo(parent, remove_from_parent)
      parent = object_to_recycle.parent

    # Add the object to the recycle bin.
    def add_to_recycle_bin(w_lock: WriteLock):
      # Compute a new name that is suitable for it to have in the recycle bin,
      # as names must be unique within a given container.
      name_in_recycle_bin = object_to_recycle_name
      suffix = 2
      while self._data_engine_api.ContainerFind(
          w_lock.lock,
          name_in_recycle_bin):

        name_in_recycle_bin = f'{object_to_recycle_name} {suffix}'
        suffix += 1

      self._data_engine_api.ContainerAppend(
        w_lock.lock,
        name_in_recycle_bin,
        self.__get_obj_handle(object_to_recycle),
        False)
    self._run_with_undo(recycle_bin, add_to_recycle_bin)

  def is_recycled(self, mdf_object: DataObject | ObjectID[DataObject]) -> bool:
    """Check if an object is in the recycle bin.

    Parameters
    ----------
    mdf_object
      Object to check.

    Returns
    -------
    bool
      True if the object is in the recycle bin (deleted)
      and False if it is not.

    """
    self._record_function_call_telemetry("is_recycled")
    handle = self.__get_obj_handle(mdf_object)
    return self._data_engine_api.ObjectHandleIsInRecycleBin(handle)

  def type_name(self, path_or_id: str | ObjectID[DataObject]) -> str:
    """Return the type name of an object.

    This name is for diagnostics purposes only. Do not use it to alter the
    behaviour of your code. If you wish to check if an object is of a given
    type, use ObjectID.is_a() instead.

    Parameters
    ----------
    path_or_id
      The path or the ID of the object to query its type's name.

    Returns
    -------
    str
      The name of the type of the given object.

    See Also
    --------
    mapteksdk.data.objectid.ObjectID.is_a : Check if the type of an object is
      the expected type.
    """
    self._record_function_call_telemetry("type_name")
    mdf_object = self.__get_obj_handle(path_or_id)
    dynamic_type = self._data_engine_api.ObjectDynamicType(mdf_object)
    raw_type_name: str = self._data_engine_api.TypeName(
      dynamic_type).decode('utf-8')

    # Tidy up certain names for users of the Python SDK.
    raw_to_friendly_name = {
      '3DContainer': 'VisualContainer',
      '3DEdgeChain': 'Polyline',
      '3DEdgeNetwork': 'EdgeNetwork',
      '3DNonBrowseableContainer': 'NonBrowseableContainer',
      '3DPointSet': 'PointSet',
      'BlockNetworkDenseRegular': 'DenseBlockModel',
      'BlockNetworkDenseSubblocked': 'SubblockedBlockModel',
      'EdgeLoop': 'Polygon',
      'RangeImage': 'Scan',
      'StandardContainer': 'StandardContainer',
      'TangentPlane': 'Discontinuity',
    }

    # Exclude the old (and obsolete) revision number.
    raw_type_name = raw_type_name.partition('_r')[0]

    return raw_to_friendly_name.get(raw_type_name, raw_type_name)

  def project_path(self) -> pathlib.Path:
    """The project path for this object.

    Typically, this will return the path to the primary .maptekdb open in
    the connected application.

    Returns
    -------
    pathlib.Path
      The project path for this object.

    Raises
    ------
    FileNotFoundError
      If this object does not have a project path.
    """
    self._record_function_call_telemetry("project_path")
    path_string = self._data_engine_api.ProjectPath(self._backend.index)
    if path_string:
      return pathlib.Path(path_string)
    raise FileNotFoundError("This Project does not have a project path.")

  @contextmanager
  def progress_indicator(
    self,
    max_progress: int=100,
    *,
    title: str | None=None,
    message: str | None=None,
    background: bool=False,
  ) -> Generator[ProgressIndicator, None, None]:
    """Create a progress indicator in the connected application.

    This allows for scripts to display progress to the user in a visual way.
    The progress indicator is initially empty. When `max_progress` units of
    progress are added to the indicator via the `add_progress()` or
    `set_progress()` function, the progress indicator will appear full.

    This should always be used in a with block. When the with block is exited,
    the progress indicator will be closed.

    Parameters
    ----------
    max_progress
      The maximum progress for the progress indicator.
    title
      The title for the progress indicator window.
      If None, a default will be used.
      This is not used if background=True.
    message
      The initial message which will appear above the progress indicator.
      If None, the progress indicator will have no message.
    background
      If False (default), the progress indicator will appear as a window in
      the connected application.
      If True, the progress indicator will appear in the status bar.
      Setting this to true is appropriate for background operations which still
      should display progress or long-running operations.

    Raises
    ------
    ValueError
      If max_progress is less than or equal to zero.

    Examples
    --------
    The following example demonstrates a script which processes surfaces one at
    a time and updates a progress indicator after processing each surface.

    >>> def process_surface(surface_id: ObjectID[Surface]):
    ...     # Process the surface here.
    ...     pass
    ...
    >>> surfaces: list[ObjectID[Surface]]
    >>> with project.progress_indicator(
    ...     max_progress=len(surfaces),
    ...     title="Process Surfaces",
    ...     message="Processing",
    ...  ) as progress_indicator:
    ...     for surface in surfaces:
    ...         process_surface(surface)
    ...         progress_indicator.add_progress()

    Note that in the above example, progress is added to the indicated after
    each call to process_surface(). If the progress were added before the call
    to process_surface(), then the progress indicator would appear full while
    the last surface is being processed which is misleading.
    """
    self._record_function_call_telemetry("progress_indicator")
    with TransactionManager(default_manager()) as manager:
      with ProgressIndicatorConcrete(
        max_progress=max_progress,
        title=title,
        message=message,
        background=background,
        manager=manager,
      ) as indicator:
        yield indicator

  def _get_before_state(
      self,
      oid: ObjectID[ObjectT]
      ) -> tuple[ObjectID[ObjectT], set[ObjectID[DataObject]]]:
    """Get the before state required to undo changes to the object.

    Parameters
    ----------
    oid
      The ObjectID of the object changes of which can be undone.

    Returns
    -------
    tuple[ObjectID, set[ObjectID]]
      A tuple where the first element is the ObjectID of a clone
      of the object before any changes were made and where the
      second element is a set of primary children of the object.
      The set will be empty of oid is not a container.
    """
    if oid.is_a((Drillhole, DrillholeDatabase)):
      raise UndoNotSupportedError(
        f"Undoing changes to a {oid.type_name} is not supported."
      )
    primary_children: set[ObjectID[DataObject]] = set()
    if is_a_container(oid):
      with self.read(oid) as container:
        # pylint: disable=no-member
        for child_id in container.ids():
          if child_id.parent == container.id:
            primary_children.add(child_id)
        # pylint: disable=protected-access
        return ObjectID(
          self._data_engine_api.ShallowCloneObject(container._lock.lock)
          ), primary_children
    return self.copy_object(oid, None), primary_children

  def _run_with_undo(
      self,
      oid: ObjectID[DataObject],
      function_to_run: Callable[[WriteLock], None]):
    """Run a function which accepts a WriteLock and add to undo stack.

    This will not add to the undo stack if it does not exists.

    Parameters
    ----------
    oid
      Object ID to use to open the WriteLock. Only changes to this object
      will be undoable.
    function_to_run
      Function which accepts a WriteLock. This should not checkpoint the
      object. Any changes it makes to the object will be undoable if this
      is called inside of a Project.undo() block.

    Raises
    ------
    StackClosedError
      If the current undo stack is closed.
    """
    undo_stack = self.__undo_stack
    if undo_stack is not None:
      undo_stack.raise_if_closed()
      before_id, primary_children = self._get_before_state(oid)
    else:
      before_id = None
      primary_children = set()

    with WriteLock(
        oid.handle, self._data_engine_api, rollback_on_error=True) as w_lock:
      function_to_run(w_lock)
      change_reasons = ChangeReasons(
        self._data_engine_api.Checkpoint(w_lock.lock))

    if undo_stack is not None and before_id is not None:
      undo_stack.add_operation(
        before_id,
        oid,
        change_reasons,
        primary_children,
      )

  @classmethod
  def open_on_thread(cls, existing_project: Project) -> Project:
    """Open the project on another thread.

    The expectation is the project has already been opened/connected on
    a thread already. This thread should not out live the project on
    the other thread as it is responsible for unloading the project.

    Raises
    ------
    ApplicationTooOldError
      If the API version is too low to support this.
    """
    existing_project.raise_if_version_below((1,  10))

    # pylint: disable=protected-access
    parent_backend = existing_project._backend
    if not parent_backend:
      # This case is not possible in normal usage.
      raise ValueError("The existing project has no backend.")

    options = ProjectOptions(
      "",

      open_mode=ProjectOpenMode.OPEN_EXISTING_THREAD,

      # Don't provide the DLLs as they have already been loaded by
      # existing_project.
      dll_path=None,
      existing_backend=parent_backend,
    )

    return Project(options)

  @staticmethod
  def find_running_applications() -> list[ExistingMcpdInstance]:
    """Return a list of applications that are candidates to be connected to.

    No checking is performed on the application to determine if it is suitable
    to connect to. For example, if the product is too old to support the SDK.

    Once you select which application is suitable then pass the result as the
    existing_mcpd parameter of the Project class's constructor.

    The list is ordered based on the creation time of the mcpd process with the
    latest time appearing first in the list.

    Returns
    -------
    list of ExistingMcpdInstance
      The list of candidate applications (host) that are running.

    Raises
    ------
    NoHostApplicationError
      No host applications found running to connect to.

    Examples
    --------
    Finds the running applications and chooses the oldest one.

    >>> from mapteksdk.project import Project
    >>> applications = Project.find_running_applications()
    >>> project = Project(existing_mcpd=applications[-1])

    """
    logger = logging.getLogger('mapteksdk.project')
    instances = find_mdf_hosts(logger)
    if not instances:
      error_message = "No host applications found running to connect to."
      logger.error(error_message)
      raise NoHostApplicationError(error_message)
    return instances
