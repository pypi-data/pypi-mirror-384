"""Provides different backends for a project.

The three main kinds of backends are:
- InMemoryBackend - this is a backend that does not have persistent storage of
  the data, once the project is unloaded the data is lost. If the data created
  is needed it needs to be exported out. This is commonly used for tests.
- ExistingBackend - the project is backed by a project that exists in an
  existing (running) application. This is the commonly used by users of this
  SDK.
- NewBackend - a new backend is created to host the project. A use case of this
  would be reading/writing to a Maptek Database that isn't opened in an
  application or the SDK is being used to create an application.

The alternative name would have been subsystem so as not to confuse these
backends with the concept of backends within the C++ side. For example, the
different project backends can be Maptek Database, Maptek Object, Vulcan
DGD/TEK Isis or a Vulcan project directory.
"""
###############################################################################
#
# (C) Copyright 2023, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

from __future__ import annotations

import ctypes
import datetime
import pathlib
import os
import sys

from . import account
from .options import ProjectOptions, ProjectBackendType
from .mcp import (ExistingMcpdInstance, McpdConnection, McpdDisconnectError,
                  ConnectionFailedError, Mcpd, connect_to_mcpd, find_mdf_hosts)
from .. import capi
from ..project.errors import ProjectConnectionFailureError


class Backend:
  """An abstract class for representing the different backends for projects.

  See the derived classes for specifics.

  An alternate name for this would be ProjectSubsystem.
  """

  def __init__(self, log):
    self.broker_session = None
    self.index = None
    self.licence = ''
    self.log = log

  @property
  def _data_engine_api(self) -> capi.DataEngineApi:
    """Access the DataEngine C API."""
    return capi.DataEngine()

  @property
  def _license_api(self) -> capi.LicenseApi:
    """Access the License C API."""
    return capi.License()

  def acquire_licence(self,
                      broker_connector_path: str | None,
                      connection_parameters: dict | None) -> str:
    """Acquire a licence for using the given backend.

    This uses the Licence DLL to check the supported licence format.

    This prefers to use the broker as it better handles concurrent access,
    sharing the licence, caching as well as borrowing. The situation where the
    broker isn't used is when mapteksdk.native package is used so there is no
    running application or Workbench and therefore it is unlikely there is the
    broker in-use.

    Parameters
    ----------
    broker_connector_path
      The path to where the Maptek Account Broker assemblies can be found.
      If None, the assemblies bundled with the Python SDK are used.
    connection_parameters
      Provides parameters sent to the Maptek Account broker. The parameters
      IgnoreBroker, APIToken and OverrideMaptekAccountServerLocation (for
      testing only) are applicable when connecting without the broker.

    Returns
    -------
    str
      The acquired licence.
    """
    connection_parameters = connection_parameters or {}

    def _load_native_version():
      """Return a version of the account module from mapteksdk.native package.

      If the mapteksdk.native package is not available this returns None.
      """
      native_account = sys.modules.get('mapteksdk.native.account')
      if native_account:
        return native_account

      try:
        from mapteksdk.native import account as native_account
        return native_account
      except (ModuleNotFoundError, ImportError):
        return None  # The broker must be used in this case.

    native_account = _load_native_version()
    if native_account:
      # If mapteksdk.native is installed and there is no broker installed use
      # it to request a licence from Maptek Account without the broker.
      #
      # Otherwise the broker is used.
      common_program_files = os.environ.get("CommonProgramFiles")
      components = [
        common_program_files, "Maptek", "MaptekAccountServices",
        "MaptekAccountBroker.exe"]

      ignore_broker = connection_parameters.get('IgnoreBroker', False)
      if (ignore_broker or not common_program_files or
          not pathlib.Path(*components).is_file()):
        if ignore_broker:
          self.log.info("The mapteksdk.native package is available and the "
                        "broker will be ignored even if it is installed.")
        else:
          self.log.info("The mapteksdk.native package is available and the "
                        "broker is not installed.")

        # Acquire licence straight from Maptek Account without the broker.
        host_id = self._license_api.host_id()
        supported_licence_format = self._license_api.supported_licence_format()
        host_id_version = self._license_api.host_id_version()

        self.broker_session = native_account.connect_to_maptek_account(
          host_id=host_id,
          api_token=connection_parameters.get("ApiToken", None),
          domain=connection_parameters.get(
            "OverrideMaptekAccountServerLocation",
            native_account.WebClient.MAPTEK_ACCOUNT),
        )

        with self.broker_session.acquire_extend_licence(
            supported_licence_format, host_id_version) as licence:
          self.log.info('Acquired licence for Maptek Extend')
          self.licence = licence.license_string
          return licence.license_string
    else:
      self.log.debug("The mapteksdk.native package is unavailable")

    return self.acquire_licence_from_broker(broker_connector_path,
                                            connection_parameters)

  def acquire_licence_from_broker(self,
                                  broker_connector_path: str | None,
                                  connection_parameters: dict | None) -> str:
    """Acquire a licence for using the given backend.

    This uses the Licence DLL to check the supported licence format.

    Parameters
    ----------
    broker_connector_path
      The path to where the Maptek Account Broker assemblies can be found.
      If None, the assemblies bundled with the Python SDK are used.
    connection_parameters
      Provides parameters sent to the Maptek Account broker.

    Returns
    -------
    str
      The acquired licence.
    """
    # First, try with an anonymous session. This allows the use of borrowed
    # licences when the user isn't logged into Maptek Account.
    #
    # Secondly, if that that fails then we try non-anonymous so the user is
    # prompted to log-in. Unless the caller has been explicit and said they
    # only want an anonymous session.
    required_parameters = {
        'AnonymousSession': True,
        'MaptekAccountUserName': '',
        'MaptekAccountAuthKey': '',
        'ApiToken': '',
      }
    if connection_parameters:
      force_parameters = connection_parameters.copy()
      force_parameters.update(required_parameters)
    else:
      force_parameters = required_parameters

    supported_licence_format = self._license_api.supported_licence_format()
    host_id_version = self._license_api.host_id_version()
    broker_error : ValueError | None = None
    for try_parameters in [force_parameters, connection_parameters]:
      try:
        self.broker_session = account.connect_to_maptek_account_broker(
          broker_connector_path, try_parameters)

        with self.broker_session.acquire_extend_licence(
            supported_licence_format, host_id_version) as licence:
          self.log.info('Acquired licence for Maptek Extend')
          self.licence = licence.license_string
          return licence.license_string
      except ValueError as error:
        # That failed, but we can try again this time without requiring it
        # to be anonymous to allow the user to login.
        if self.broker_session:
          self.broker_session.disconnect()

        # There are two options for how to log the message here. One is to be
        # generic to match how this code is written (which is rather generic)
        # so it would be future-proof, for example "Initial attempt to acquire
        # a licence has failed, trying again.". Two is to actually say the
        # intent at the time which was "Failed to find a borrowed licence.
        # Trying a live licence."
        self.log.info('Failed to find a borrowed licence. Trying a live '
                      'licence.')

        # However it is possible the caller has explicitly said be
        # anonymous in which case this won't make any difference.
        if connection_parameters and connection_parameters.get(
            'AnonymousSession', False):
          raise

        # Capture the error so it can throw if it was the last one.
        broker_error = error

    raise broker_error # type: ignore Variable set in except.

  def connect_to_project(self) -> None:
    """Connects to the project.

    In older versions of the applications, this would need to be called
    per-thread.

    This populates self.index with the index of the backend.

    Raises
    ------
    ProjectConnectionFailureError
      If connecting to the project fails.
    """
    raise NotImplementedError("Derived classes should implement this method")

  def disconnect_from_project(self) -> None:
    """Disconnect from the project.

    self.index is reset back to to None.

    After disconnecting from the project, it will then disconnect from the
    Maptek Account broker.

    Calling this more than once is acceptable and won't raise an error.
    """
    try:
      if self.index is not None:
        self._disconnect_from_project()
    finally:
      self.index = None
      if self.broker_session:
        self.broker_session.disconnect()
        self.broker_session = None

  def use_existing_connection(self, connection: McpdConnection):
    raise NotImplementedError

  @property
  def mcpd_instance(self) -> ExistingMcpdInstance | McpdConnection | None:
    """MCPD instance used by this backend.

    If None, this backend is not connected to to the mcpd. For certain
    subclasses, this will always be None.
    """
    raise NotImplementedError

  @property
  def has_project_explorer(self) -> bool:
    """True if this backend has a project explorer."""
    raise NotImplementedError

  def _disconnect_from_project(self) -> None:
    """Handle the backend specific disconnection from the project.

    The specific backend should handle any clean-up for the work done during
    connect_to_project().

    Implementations need to override this function.
    The overridden function should not call this function.
    """
    raise NotImplementedError("Derived classes should implement this method")


class InMemoryBackend(Backend):
  """A backend for the project that is stored in-memory only.

  The data is not written out to a file.  If any data should persist after
  the project is closed, it will need to be exported.
  """

  def connect_to_project(self) -> None:
    """Connects to the DataEngine.

    This creates a DataEngine in the current process.
    """
    # No executables or servers will be used. This means no mcpd or
    # backendServer will be launched or used.
    connected = self._data_engine_api.CreateLocal()
    if not connected:
      last_error = self._data_engine_api.ErrorMessage()
      error_message = ("There was an error while creating"
        f" memory-only project ({last_error})")
      self.log.critical(error_message)
      raise ProjectConnectionFailureError(error_message)

    self.index = 0
    self.log.info("Created memory-only DataEngine")

  def use_existing_connection(self, connection: McpdConnection):
    raise NotImplementedError(
      "Backend Observer does not support reusing an existing connection.")

  @property
  def mcpd_instance(self):
    return None

  @property
  def has_project_explorer(self) -> bool:
    return False

  def _disconnect_from_project(self):
    """Disconnects from the DataEngine."""
    # A project backed onto only a DataEngine isn't expected to have any other
    # clients. Its primary use is for tests and scripts which need to
    # open a DataEngine, create/import and save results then close it, i.e.
    # not in multi-process situations where the lifetime of the processes
    # are unknown.
    self.log.info("Disconnecting from an in-memory project.")
    close_backends_if_last_client = False
    self._data_engine_api.Disconnect(close_backends_if_last_client)


class ExistingBackend(Backend):
  """A backend for the project that is hosted by another application.

  The data is typically stored in to a Maptek Database (Under a .maptekdb
  directory).

  The application is expected to have the backend server running so this
  should not need to start one.
  """

  def __init__(self, log, mcpd_instance):
    super().__init__(log)
    self.__mcpd_instance = mcpd_instance

    # Populated by connect_to_project() or use_existing_connection()
    self.mcp_connection: McpdConnection | None = None

    # If an existing connection is given then it is not the responsibility
    # of this class to disconnect from it.
    self.connection_our_responsibility = True

  @classmethod
  def find_application_to_connect_to(cls, log) -> ExistingMcpdInstance | None:
    """Find a suitable application to connect to.

    This first checks environment variables set by the Maptek Workbench.
    It does this because when it runs a Python script it can recommend an
    application to connect to, such as the current active application.

    If those variables are not set then it looks at running application or
    more specifically the MCPD running as part of those applications.

    Parameters
    ----------
    log
      The logger for writing messages.
      If None then no logging is performed.

    Returns
    -------
    ExistingMcpdInstance
      The MCPD instance to connect to.
    None
      If there was no host application found.
    """
    dll_path = os.environ.get("SDK_OVERWRITE_BIN_PATH", "")
    socket_path = os.environ.get("SDK_OVERWRITE_MCP_PATH", "")
    if dll_path and socket_path:
      return ExistingMcpdInstance(-1, dll_path, socket_path)

    instances = find_mdf_hosts(log)
    if instances:
      return instances[0]

    return None

  def use_existing_connection(self, connection: McpdConnection):
    self.mcp_connection = connection
    self.connection_our_responsibility = True

  def connect_to_project(self) -> None:
    # Connect to the MCPD if an existing McpdConnection was not supplied.
    if not self.mcp_connection:
      self.mcp_connection = connect_to_mcpd(
      specific_mcpd=self.mcpd_instance,
      sdk_licence=self.licence,
      )

    # Connecting to an existing DataEngine session.
    create_new_session = False
    connected = self._data_engine_api.Connect(create_new_session)
    if not connected:
      last_error = self._data_engine_api.ErrorMessage()
      error_message = (
        f"There was an error connecting to the database ({last_error})")
      self.log.critical(error_message)
      raise ProjectConnectionFailureError(error_message)

    # The index of backend is not provided when connecting to an existing
    # application; however, it can be queried from the root object.
    backend_index = ctypes.c_uint16()
    if not self._data_engine_api.ObjectBackEnd(
        self._data_engine_api.RootContainer(), ctypes.byref(backend_index)):
      last_error = self._data_engine_api.ErrorMessage()
      error_message = (
        "Unable to determine the backend used by the application "
        f"due to the following error: {last_error}")
      self.log.critical(error_message)
      raise ProjectConnectionFailureError(error_message)

    self.index = backend_index

  @property
  def mcpd_instance(self):
    return self.__mcpd_instance

  @property
  def has_project_explorer(self) -> bool:
    return True

  def _disconnect_from_project(self) -> None:
    # The backend for the project is hosted by another application, we simply
    # need to disconnect from it. However if our connection was keeping the
    # backend alive we need to close it if we are the last one.
    self.log.info("Disconnecting from a project opened by an another "
                  "application.")
    close_backends_if_last_client = True
    self._data_engine_api.Disconnect(close_backends_if_last_client)

    if self.connection_our_responsibility:
      try:
        self.mcp_connection.disconnect()
      except McpdDisconnectError:
        # The exception is already logged, so it is safe to ignore it.
        pass


class BackendObserver(Backend):
  """A backend for the project that is an observer of the project.

  This backend will not connect to or disconnect from the DataEngine,
  neither will it start/stop a backendServer.

  The expected use case for this kind of backend is when there is another
  thread which connects to either an existing backend or creates one making
  this backend just an observer of the same DataEngine.

  In older versions of the application this case would have needed to
  connect and disconnect from the DataEngine.
  """
  def __init__(self, log, backend: Backend):
    super().__init__(log)
    self.__mcpd_instance = backend.mcpd_instance
    self.__has_project_explorer = backend.has_project_explorer

    # Populated by connect_to_project().
    self.mcp_connection: McpdConnection | None = None

  def connect_to_project(self) -> None:
    # Connect to the MCPD if there is one known.
    #
    # For a project that is backed by a Maptek Database there must be one,
    # however for a in-memory only backend there won't be.
    if not self.mcp_connection and self.mcpd_instance:
      self.mcp_connection = connect_to_mcpd(
        specific_mcpd=self.mcpd_instance,
        sdk_licence=self.licence,
      )

      # The index of backend is not provided when connecting to an existing
      # application; however, it can be queried from the root object.
      backend_index = ctypes.c_uint16()
      if not self._data_engine_api.ObjectBackEnd(
          self._data_engine_api.RootContainer(),
          ctypes.byref(backend_index)):
        last_error = self._data_engine_api.ErrorMessage()
        error_message = (
          "Unable to determine the backend used by the application "
          f"due to the following error: {last_error}")
        self.log.critical(error_message)
        raise ProjectConnectionFailureError(error_message)

      self.index = backend_index
    else:
      # Consider this as being an observer of an in-memory only backend.
      self.index = 0

  def use_existing_connection(self, connection: McpdConnection):
    raise NotImplementedError(
      "Backend Observer does not support reusing an existing connection.")

  @property
  def mcpd_instance(self):
    return self.__mcpd_instance

  @property
  def has_project_explorer(self) -> bool:
    return self.__has_project_explorer

  def _disconnect_from_project(self) -> None:
    self.log.info("Disconnecting from a project in-use by another thread.")
    if self.mcp_connection:
      try:
        self.mcp_connection.disconnect()
      except McpdDisconnectError:
        # The exception is already logged, so it is safe to ignore it.
        pass


class NewBackend(Backend):
  """A backend for the project that is created by Python.

  The data will be stored in a Maptek Database (Under a .maptekdb
  directory).
  """

  def __init__(self, log, mcpd_instance, options: ProjectOptions):
    super().__init__(log)
    self.options = options

    if isinstance(mcpd_instance, McpdConnection):
      raise TypeError('mcpd_instance should not be a connection. To use an '
                      'existing connection use_existing_connection() should '
                      'be called instead.')

    self.__mcpd_instance = mcpd_instance

    # Populated by connect_to_project().
    self.mcp_connection: McpdConnection | None = None

    # If an existing connection is given then it is not the responsibility
    # of this class to disconnect from it.
    self.connection_our_responsibility = True

    # Populated by connect_to_project() if there is no existing instance or
    # connection.
    self._mcpd: Mcpd | None = None

  def use_existing_connection(self, connection: McpdConnection):
    self.mcp_connection = connection
    self.connection_our_responsibility = False

  def connect_to_project(self) -> None:
    # This expects that a connection is already made to the mcpd.exe and
    # it will be able to launch the backendServer.

    # Connect to the MCPD if an existing McpdConnection was not supplied.
    if not self.mcp_connection:
      if not self.mcpd_instance:
        # Account for the development environment where the mcpd executable is
        # in a different directory from the DLLs.
        if os.path.isfile(os.path.join(self.options.dll_path, Mcpd.EXE_NAME)):
          mcpd_path = self.options.dll_path
        else:
          mcpd_path = os.path.join(self.options.dll_path, '..', 'bin')

        # The MCPD has different licencing requirements then the Python SDK
        # itself.
        licence_for_mcpd = self._acquire_mdf_licence()
        self._mcpd = Mcpd(
          mcpd_path=mcpd_path,
          mcpd_licence=licence_for_mcpd,
          dll_path=self.options.dll_path,
        )
        self.__mcpd_instance = self._mcpd.instance

      try:
        self.mcp_connection = connect_to_mcpd(
          specific_mcpd=self.__mcpd_instance,
          sdk_licence=self.licence,
          )
      except ConnectionFailedError:
        # If the connection failed, it is most likely that the mcpd failed
        # to start-up correctly.
        #
        # Shutdown the mcpd so it isn't left running in the background.
        self._mcpd.mcpd_process.terminate()
        self._mcpd.mcpd_process.wait()
        raise

    # Start a backend server.
    if 'MDF_BIN' not in os.environ:
      expected_path = os.path.join(self.options.dll_path, 'mcpd.exe')
      if os.path.exists(expected_path):
        os.environ['MDF_BIN'] = os.path.abspath(expected_path)
      else:
        # This accounts for a situation that is unique to the
        # under-development versions of the software.
        if os.path.exists(os.path.join(self.options.dll_path, '..', 'bin',
                                       'mcpd.exe')):
          os.environ['MDF_BIN'] = os.path.abspath(os.path.join(
            self.options.dll_path, '..', 'bin'))
        else:
          error_message = "Failed to register backend server - environment " + \
            "variable MDF_BIN not set."
          self.log.critical(error_message)
          raise ProjectConnectionFailureError(error_message)

    # Ideally, the absolute path would be provided to the backendServer,
    # however the underlying function doesn't handle spaces. Using an
    # environment variable allows the given string to have no spaces but
    # for the path to contain spaces when it is expanded.
    backend_registered = self.mcp_connection.register_server(
      '$MDF_BIN/backendServer.exe')
    if not backend_registered:
      error_message = "Failed to register backend server"
      self.log.critical(error_message)
      raise ProjectConnectionFailureError(error_message)

    # Ensure there are no stale lock files.
    if not self._data_engine_api.DeleteStaleLockFile(
        self.options.project_path.encode('utf-8')):
      last_error = self._data_engine_api.ErrorMessage()
      self.log.error(
        "There was a problem ensuring no stale lock files "
        "had been left in the project. Error message: %s", last_error)

      # Try sharing the project?
      self.options.backend_type = ProjectBackendType.SHARED
      self.log.warning('Attempting to share the project "%s"',
                        self.options.project_path)

    # Create or open project.
    self.index = self._data_engine_api.OpenProject(
      self.options.project_path.encode('utf-8'),
      self.options.open_mode,
      self.options.access_mode,
      self.options.backend_type,
      self.options.proj_units)
    if self.index == 0:
      last_error = self._data_engine_api.ErrorMessage()
      error_message = ("There was a problem using the requested database "
                       "load or creation settings. "
                       f"Error message: {last_error}")
      self.log.critical(error_message)
      self.index = None
      raise ProjectConnectionFailureError(error_message)

    # Connecting to an existing DataEngine session (the session created by the
    # backendServer when the project was opened).
    create_new_session = False
    connected = self._data_engine_api.Connect(create_new_session)
    if not connected:
      last_error = self._data_engine_api.ErrorMessage()
      error_message = (
        f"There was an error connecting to the database ({last_error})")
      self.log.critical(error_message)
      raise ProjectConnectionFailureError(error_message)

  @property
  def mcpd_instance(self):
    return self.__mcpd_instance

  @property
  def has_project_explorer(self) -> bool:
    return False

  def _acquire_mdf_licence(self):
    """Acquire a licence to run the MDF executables."""
    supported_licence_format = self._license_api.supported_licence_format()
    host_id_version = self._license_api.host_id_version()
    version_major, version_minor = self._license_api.version
    product = self.broker_session.product_information(
      # The name corresponds to the application ID.
      name='Maptek.SDK.Native',
      display_name='Extend - Native',
      version_label=f'{version_major}.{version_minor}',
      license_format=supported_licence_format,
      host_id_version=host_id_version,
      # This ideally would be the date of release of the corresponding MDF
      # application, this is difficult to determine so for now we use the
      # date when this feature was first added.
      release_date=datetime.datetime(2023, 9, 27,
                                     tzinfo=datetime.timezone.utc),
    )

    with self.broker_session.acquire_licence(product, ['MDF140',
                                                       'SDK',
                                                       'SDKNative']) as licence:
      self.log.info('Acquired licence for the native package for Maptek '
                    'Extend')
      return licence.license_string

  def _disconnect_from_project(self) -> None:
    if self.index is None:
      return  # No project to disconnect from.
    if self.index == 0:
      raise ValueError("Unexpected backend index")

    self.log.info("Closing project with backend index: %s", self.index)
    self._data_engine_api.CloseProject(self.index)

    if self.connection_our_responsibility:
      try:
        self.mcp_connection.disconnect()
      except McpdDisconnectError:
        # The exception is already logged, so it is safe to ignore it.
        pass

    self.mcp_connection = None

    if self._mcpd:
      self._mcpd.close()
      self._mcpd = None
