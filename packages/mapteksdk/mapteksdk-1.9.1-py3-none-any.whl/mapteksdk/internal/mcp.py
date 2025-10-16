"""Support for Master Control Program (MCP).

This is for lower bandwidth "message passing" for synchronisation purposes,
small volume data transfer and general communication.

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
from __future__ import annotations

import base64
import collections
import ctypes
import logging
import os
import re
import subprocess
import tempfile
from types import TracebackType
import typing

import psutil

from ..capi import Mcp as McpDll

if typing.TYPE_CHECKING:
  from collections.abc import Callable

# pylint: disable=missing-docstring
# pylint: disable=too-many-instance-attributes
# pylint: disable=too-few-public-methods
DEFAULT_LICENCE = "<xml>ViewOnlyLicence</xml>"
MCP_NAME_REGEX = re.compile('[a-z][a-zA-Z0-9]')

ExistingMcpdInstance = collections.namedtuple(
  'ExistingMcpdInstance', ('mcpd_process_id', 'bin_path', 'mcp_socket_path'))
ExistingMcpdInstance.mcpd_process_id.__doc__ = 'The process ID of the mcpd ' + \
  'process.'
ExistingMcpdInstance.bin_path.__doc__ = 'The path to the bin directory for ' + \
  'host application (the directory with mcpd.exe)'
ExistingMcpdInstance.mcp_socket_path.__doc__ = 'The path to MCP socket file'


class ConnectionFailedError(Exception):
  """Error raised when failing to connect to the MCP."""

  def __init__(self, name: str, socket_path: str):
    super().__init__(f'Failed to connect as {name} to mcpd at {socket_path}.')
    self.name = name
    self.socket_path = socket_path


class McpdDisconnectError(Exception):
  """Error raised when disconnecting from the MCP."""


class NoHostApplicationError(OSError):
  """Error raised when there are no host applications to connect to.

  This inherits from OSError for backwards compatibility reasons.
  """


class McpCallback:
  """Python class representing a MCP callback.

  When the event is triggered, the given callback is called.

  Parameters
  ----------
  event_name
    The name of the event which should cause the callback to be called.
  callback
    Callback to call when the event occurs.
  mcp
    The MCP DLL which to use to add the callback.
    If None (default), then the singleton will be used.
  """
  def __init__(
      self,
      event_name: str,
      callback: Callable[[typing.Any], None],
      mcp: McpDll | None=None) -> None:
    self.__event_name = event_name
    self.__mcp = mcp or McpDll()
    self.__callback = self.__mcp.dll.Callback(callback)
    self.__callback_handle = self.__mcp.dll.McpAddCallbackOnMessage(
        event_name.encode("utf-8"),
        self.__callback,
    )

  def __enter__(self) -> "typing.Self":
    return self

  def __exit__(
      self,
      __exc_type: "type[BaseException] | None",
      __exc_value: "BaseException | None",
      __traceback: "TracebackType | None") -> "bool | None":
    self.__mcp.dll.McpRemoveCallbackOnMessage(
        self.__event_name.encode("utf-8"), self.__callback_handle)


class Mcpd:
  """Spawns the Master Control Program Daemon (MCPD).

  Call close() when it is no longer needed.

  This does not connect to the newly spawned mcpd.
  It is the caller's responsibility for calling register_dll_directory().

  Parameters
  ----------
  mcpd_path
    Path to the mcpd.exe executable.
  mcpd_licence
    The licence string for the the mcpd itself.
    The standard behaviour for the mcpd is to require the MDF140 feature code,
    as clients connecting to it will connect using that feature code.
  dll_path : str
    Path to locate DLLs and dependencies of mcpd.exe.
  """

  EXE_NAME = "mcpd.exe"

  def __init__(self, mcpd_path: str, mcpd_licence: str, dll_path: str) -> None:
    self.socket_mutex_handle = None
    self.socket_path: str = ''
    self.mcpd_path = mcpd_path
    self.dll_path = dll_path
    self.log = logging.getLogger("mapteksdk.internal.mcp")

    # If the licence uses Maptek Account then it will be stored in a file for
    # the mcpd process.
    self.account_license_path: str = ''

    self.mcpd_process = self.__spawn_mcpd_process(mcpd_licence)
    self.log.info("Started mcpd: %s", self.mcpd_process.pid)

  @property
  def instance(self) -> ExistingMcpdInstance:
    """An ExistingMcpdInstance that refers to this mcpd instance."""
    # The dll_path is used rather than the bin path (mcpd_path) because when
    # connecting to this instance the DLL path is preferable if it is
    # different from the mcpd_path.
    return ExistingMcpdInstance(
      self.mcpd_process.pid, self.dll_path, self.socket_path)

  def close(self):
    """Close down the mcpd.

    This requires the DLLs.
    """
    if self.account_license_path and os.path.exists(self.account_license_path):
      # As Python created the file, it is responsible for deleting the file.
      os.unlink(self.account_license_path)

    if self.mcpd_process:
      # :HACK: 2022-03-28 This should use McpDll().SoftShutDown()
      # and wait for the mcpd.exe process to exit (only killing it as
      # a last resort) so that mcpd.exe has time to clean up. We haven't been
      # able to get the above working.
      #
      # To use SoftShutDown() we would need a connection to the mcpd.
      self.log.info("Closing down process ID: %s", self.mcpd_process.pid)
      try:
        self.mcpd_process.terminate()
        # Wait for the spawned mcp to exit. Otherwise the mcp process will be
        # kept alive until the calling process exits, waiting for the calling
        # process to read the return code.
        self.mcpd_process.wait()
      except Exception as original_error:
        error = McpdDisconnectError("Error unloading mcpd.exe")
        self.log.info(error)
        raise error from original_error

    # Remove socket files created for this mcpd.
    if self.socket_mutex_handle:
      self.log.info("Unlocking socket: %s", self.socket_path)
      try:
        McpDll().UnlockSocketFile(self.socket_mutex_handle)
      except Exception as original_error:
        error = McpdDisconnectError("Error unlocking socket file")
        self.log.info(error)
        raise error from original_error
      self.socket_mutex_handle = None

  def __spawn_mcpd_process(self, mcpd_licence) -> subprocess.Popen:
    """Spawn the mcpd process to allow Python to connect to.

    This can be used to conduct unit tests or prototype design
    against, without a host MDF application present.

    This does not connect the current thread to the mcpd. Use
    McpdConnection.

    See Also
    --------
    McpdConnection : Finds applications to connect to.
    """
    mcpd_licence = mcpd_licence or DEFAULT_LICENCE

    try:
      # Create and lock a new socket file to use with this mcpd session.
      buf_size = 511 #512-1
      str_buffer = ctypes.create_string_buffer(buf_size)
      self.socket_mutex_handle = McpDll().NewSocketFile(str_buffer, buf_size)
      self.socket_path = str_buffer.value.decode("utf-8")

      # Set-up the environment for the new process.
      mcpd_environment = os.environ.copy()
      mcpd_environment['MDF_BIN'] = os.path.abspath(self.mcpd_path)
      mcpd_environment['MDF_SHLIB'] = self.dll_path
      mcpd_environment['MDF_MCP_SOCKET'] = self.socket_path
      # Add the DLL path to the PATH environment variable to ensure
      # mcpd.exe can find its dependencies.
      mcpd_environment['PATH'] = os.pathsep.join([
        self.dll_path, mcpd_environment['PATH']])

      # If any of the environment variables exist due to a previous Project
      # class construction is still in the environment, then remove them.
      if 'MDF_ACTIVE_PACKAGE' in mcpd_environment:
        mcpd_environment.pop('MDF_ACTIVE_PACKAGE')
      if 'MDF_MAPTEK_ACCOUNT_LICENSING' in mcpd_environment:
        mcpd_environment.pop('MDF_MAPTEK_ACCOUNT_LICENSING')
      if 'MDF_MAPTEK_ACCOUNT_LICENCE_PATH' in mcpd_environment:
        mcpd_environment.pop('MDF_MAPTEK_ACCOUNT_LICENCE_PATH')

      # Licences come as either XML or JSON where XML is used for the
      # legacy licences (floating licence server and dongle) and the latter for
      # Maptek Account. This is a simple check to determine which is used.
      is_legacy_licence = mcpd_licence.startswith('<')
      is_maptek_account_licence = not is_legacy_licence
      is_maptek_account_licence_written_to_file = McpDll().version < (1, 10)
      if not is_maptek_account_licence_written_to_file:
        McpDll().SetIsUsingMaptekAccountLicensing(is_maptek_account_licence)

      if is_legacy_licence:
        # Pass the legacy licence via an environment variable.
        mcpd_environment['MDF_ACTIVE_PACKAGE'] = mcpd_licence
      elif McpDll().version < (1, 6):
        # Older versions of the software don't support passing the licence via
        # a file and uses an environment variable instead.
        mcpd_environment['MDF_ACTIVE_LICENCE_SET'] = mcpd_licence
      elif is_maptek_account_licence_written_to_file:
        # Write the license to a temporary file and add it to the environment
        # so that mcpd.exe can read it.
        with tempfile.NamedTemporaryFile("w", delete=False) as file:
          file.write(mcpd_licence)
          file.flush()
          mcpd_environment['MDF_MAPTEK_ACCOUNT_LICENCE_PATH'] = file.name
      else:
        # Flag that a Maptek Account licence is in use.
        mcpd_environment['MDF_MAPTEK_ACCOUNT_LICENSING'] = '1'

      process = subprocess.Popen(
        os.path.join(self.mcpd_path, Mcpd.EXE_NAME),
        env=mcpd_environment,
        stdin=subprocess.PIPE)

      if is_maptek_account_licence and not is_maptek_account_licence_written_to_file:
        # Pass the Maptek Account license to the launcher via base64
        # encoded standard input.
        mcpd_licence_base64 = base64.b64encode(mcpd_licence.encode('utf-8'))

        # The stdin argument was set to PIPE. This means stdin cannot be None.
        process.stdin.write(mcpd_licence_base64) # type: ignore

      # This needs to be closed regardless of if it is being written to.
      process.stdin.close() # type: ignore
      return process
    except OSError as os_error:
      self.log.error("Unable to load the MCP or UI dll")
      self.log.error(os_error)
      raise

class McpdConnection:
  """Represents a connection between a thread and the MCPD.

  Use connect_to_mcpd() to establish a connection to the MCPD.

  The MCPD is the Master Control Program Daemon.

  The MCPD is typically started by a Maptek application but it can also be
  started by the Mcpd class.

  Parameters
  ----------
  specific_mcpd
    The specified instance provides the information to connect to the mcpd.
    This is the path to the DLLs to use such that the mdf_mcp.dll can be found
    and the socket path which is used to specify which mcpd to connect to.
  mdf_licence
    Licence string to operate with the SDK.
  name
    The name to use for registering/connecting with the mcpd.
    This is used to identify the sender of the messages.
    The name must start with a-z and the rest must only contain a-zA-Z0-9.
  """
  def __init__(self, specific_mcpd: ExistingMcpdInstance, name: str,
               sdk_licence: str):
    self.log = logging.getLogger("mapteksdk.internal.mcp")
    self.is_connected = True  # Assume we are connected if we reached this.
    self.licence = sdk_licence
    self.mcpd_pid = specific_mcpd.mcpd_process_id
    self.name = name
    self.socket_path: str = specific_mcpd.mcp_socket_path

  def register_server(self, server_name):
    """Register MDF servers with mcpd.

    If server_name contains environment variable names, they must be present
    in the environment of the Python process.

    Parameters
    ----------
    server_name : string
      Name of server without .exe, case sensitive.
      E.g. 'backendServer' or 'viewerServer'.

    Returns
    --------
    bool
      True if successful, False if failed.

    """
    self.log.info("Register server %s", server_name)
    return McpDll().RegisterServer(('server ' + server_name).encode('utf-8'))

  def disconnect(self):
    """Disconnect from the mcpd.exe instance."""
    self.log.info("Disconnecting from mcpd (process ID: %d)", self.mcpd_pid)
    McpDll().Disconnect()
    self.is_connected = False


def connect_to_mcpd(specific_mcpd: ExistingMcpdInstance,
                    sdk_licence: str,
                    name: str = "python") -> McpdConnection:
  """Connect to a running mcpd.

  Parameters
  ------------
  name : str
    The name to use for registering with the mcpd.
    The name must start with a-z and the rest must only contain a-zA-Z0-9.
  sdk_licence: str
    The licence which must contain the authorisation to use the SDK product.

  Raises
  ------
  ConnectionFailedError
    If the given mcpd could not be connected to.
  ValueError
    If name doesn't start with a to z (lower-case only) or contains a
    character that is not a to z, A to Z or 0 to 9.

  Returns
  -----------
  McpdConnection
    The connection to the MCPD.
  """
  log = logging.getLogger("mapteksdk.internal.mcp")

  if not name:
    log.error('name used to connect to the mcpd was empty.')
    raise ValueError('The name must not be empty.')

  if not MCP_NAME_REGEX.match(name):
    log.error('name used to connect to the mcpd was invalid (%s).', name)
    raise ValueError(
      'The name is invalid, it must start with a lower-case letter (a-z) and '
      'only contain letters a to z in upper or lower case and the digits 0 '
      'to 9.')

  # The default licence will not work with an application and requires a
  # special mode for this licence to be usable. An Extend licence is required
  # however that is not set here but by the caller.

  # :WORKAROUND: This should use sdk_licence if it is non-empty otherwise
  # DEFAULT_LICENCE as a fallback. However to support current versions of
  # Maptek Evolution (as of 2023), this needs to be DEFAULT_LICENCE.
  #
  # By always passing this value it avoids needing to detect when Evolution
  # is used to select the default licence. This allows Evolution to work and
  # doesn't break other applications as they don't validate the licence given
  # and instead check the Extend licence.
  sdk_licence = DEFAULT_LICENCE

  log.info("Connecting as %s to mcpd %s", name, specific_mcpd.mcp_socket_path)
  is_connected = McpDll().Connect(
    specific_mcpd.mcp_socket_path.encode('utf-8'),
    name.encode('utf-8'),
    sdk_licence.encode('utf-8'))
  log.info("MCP connected? %r, PID: %i", is_connected,
           specific_mcpd.mcpd_process_id)

  if not is_connected:
    raise ConnectionFailedError(name, specific_mcpd.mcp_socket_path)

  return McpdConnection(specific_mcpd, name, sdk_licence)

def find_ps_by_exe(exe_name=Mcpd.EXE_NAME):
  """Find running processes by file name.

  Parameters
  ----------
  exe_name : str
    Name of executable (defaults to typical name of the file for the mcpd).

  Returns
  -------
  list
    Processes with given name, ordered descending by start time.
  """
  results = []
  current_user_name = psutil.Process().username()
  # attrs filters the properties down only to those in the list.
  for process in psutil.process_iter(attrs=[
      "name", "pid", "environ", "username"
      ]):
    try:
      # Cannot connect to processes owned by other users.
      if process.username() != current_user_name:
        continue
      if process.name() == exe_name:
        results.append(process)
    except (psutil.AccessDenied, psutil.NoSuchProcess):
      # Skip processes the script doesn't have permission to access
      # or which no longer exist.
      continue
  # sort by process start time
  results = sorted(results, key=psutil.Process.create_time, reverse=True)
  return results

def find_mdf_hosts(logger: logging.Logger | None=None):
  """Searches for running mcpd.exe processes to try and best determine
  which application to connect to and where to find its DLLs.

  Parameters
  ----------
  logger : logging.Logger
    The logger for writing messages.
    If None then no logging is performed.

  Returns
  -------
  list of ExistingMcpdInstance
    The list of candidate hosts (mcpd) that are running.
    An empty list will be returned if there are no candidates found.
  """
  # Locate running mcpd.exe list ordered by start time (descending)
  mcpd_processes = find_ps_by_exe(Mcpd.EXE_NAME)

  results = []
  for process in mcpd_processes:
    try:
      bin_path = os.path.dirname(process.exe())
      pid = process.pid

      closest_mcp_file = process.environ().get('MDF_MCP_SOCKET', '')
      if logger:
        if closest_mcp_file:
          logger.debug(
            'Found MCP socket file (%s) used by process %d', closest_mcp_file,
            pid)
        else:
          logger.warning(
            'Unable to find the MCP socket file used by process %d',
            pid)
    except psutil.AccessDenied as error:
      # According to the psutil documentation, calling any function on a
      # psutil.Process object can raise this exception.
      if logger:
        logger.info(error)
        # For 32 bit Python, a ctypes.c_void_p will have a size of 4 bytes.
        if ctypes.sizeof(ctypes.c_void_p) == 4:
          # :NOTE: This assumes that Maptek does not release 32 bit versions
          # of applications, so the cause of the error must be failing
          # to connect to a 64 bit application from a 32 bit Python.
          logger.error(
            "Cannot connect to '%s'. "
            "Cannot connect to 64 bit application from 32 bit Python.",
            process.exe()
          )
        else:
          logger.exception(
            "Access denied when attempting to connect to '%s'. "
            "It may belong to another user.", process.exe()
          )
      continue
    except psutil.NoSuchProcess:
      # The application was closed since find_ps_by_exe() returned.
      # Skip it.
      if logger:
        logger.warning(
          "Skipping connecting to '%s' because the application was closed.",
          process.exe()
      )
      continue

    if closest_mcp_file:
      results.append(ExistingMcpdInstance(pid, bin_path, closest_mcp_file))

  return results
