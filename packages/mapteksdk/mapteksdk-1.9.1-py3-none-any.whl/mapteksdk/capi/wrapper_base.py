"""Base class for C API wrappers.

Warnings
--------
Vendors and clients should not develop scripts or applications against
this module. The contents may change at any time without warning.

"""
###############################################################################
#
# (C) Copyright 2020, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

from __future__ import annotations

import ctypes
import logging
import typing

from .errors import (
  CApiDllLoadFailureError,
  NoConnectedApplicationError,
)
from .internal.errors import DllDirectoryClosedError

if typing.TYPE_CHECKING:
  from .internal.application_dll_directory import (
    ApplicationDllDirectoryProtocol,
  )

class WrapperBase:
  """Base class for C API wrappers.

  Contains code shared by all C API wrappers.

  Notes
  -----
  *Reminder*
  Changing the C API for the Python SDK, this can break the C# SDK.
  When changing the C API remember to make the corresponding changes
  to the C# SDK.

  When to change the major version of the C API
  This should be incremented after a change to the C API interface which
  is not backwards-compatible. Note that the major version does not and
  should not be incremented more than once per user-facing release.
  When the major version number is incremented, the minor version
  number should be set to zero.

  When to change the minor version number of the C API
  This should be incremented after a backwards compatible-change
  to the C API interface. This does not need to be done more than once
  per release (Either user facing or internal).

  To avoid conflicts when updating the version number, perform the update in
  its own commit and cherry pick that commit in other jobs which change
  the C API.

  Adding handling for a new major version of the C API
  1: Increment the C API version number in authorisation/CApiVersion.H.
  2: In each wrapper class, in the capi_functions declaration add
     a comment stating the new version number after the changes
     from the previous version number then add a blank dictionary
     to contain the changes in the new version.
  3: Update the minimum/maximum supported versions as required.

  Adding a new function to the C API
  1: Make the required changes to the C API.
  2: Change the version number of the C API if required (see above)
  3: Add the new function to the newest version of the C API in
     capi_functions.
     (Never edit the capi_functions for any version of the C API
      other than the newest - doing so will break backwards
      compatibility)
  4: Write a wrapper function for the new function. This function
     should behave correctly if the new function is called from
     an older but still supported version of the C API (Typically
     this should ignore the call, return a safe default value
     or raise an exception. Choose whichever is most appropriate).

  Changing a function in the C API (no function definition changes)
  1: Make the required changes in the C API.
  2: Document any visible changes in behaviour including the
     version number in the relevant docstrings.

  Changing a function in the C API (function definition changes)
  This is the same as for new. Make sure to use the same function
  name - definitions in later versions of the C API override older ones.
  Remember to update the wrappers with extra code to ensure compatibility
  with previous versions of the C API.

  Deleting a function in the C API
  This is the same as editing, except you set the return type of
  the function to "deleted" (no capital letters) of the function
  to delete.
  Note that a future version can un-delete a function by including
  a non-deleted function with the same name.

  Deprecating support for a version
  1: Update the minimum supported version as required.
  2: Merge the dictionary for the deprecated version of the C API
     into the oldest still supported version such that it contains
     the exact definitions of the C API in the oldest supported version
     of the C API.
  3: Remove/update any wrapper functions which supports the
     deprecated version.

  Parameters
  ----------
  dll_directory
    DLL directory to load the DLL containing the C API from.
  """
  def __init__(
    self,
    dll_directory: ApplicationDllDirectoryProtocol
  ):
    self.log: logging.Logger = logging.getLogger(
      # Don't include the API postfix.
      f"mapteksdk.capi.{type(self).__name__.lower()[:-3]}")
    dll_name = self.dll_name()
    if not dll_name.endswith(".dll"):
      dll_name = f"{dll_name}.dll"

    target_directory = dll_directory
    try:
      self.__dll = target_directory.load_dll(dll_name)
      self.log.debug("Loaded: %s", dll_name)
    except DllDirectoryClosedError:
      raise NoConnectedApplicationError(
        "This function cannot be accessed because the script has disconnected "
        "from the application. Ensure all functions which require a "
        "connected application are inside of the Project's `with` block."
      ) from None
    except OSError as os_error:
      self.log.info("Failed to load %s", dll_name)
      raise CApiDllLoadFailureError(
        f"Fatal: Cannot load {dll_name}") from os_error

    self.version: tuple[int, int] = self.load_version_information()
    self.check_version_is_supported()
    self.declare_dll_functions()
    self.log.info("Loaded %s version: %s", dll_name, self.version)

  def capi_functions(self) -> list[dict[str, tuple]]:
    """Returns a dictionary containing the functions present in the C API.

    The return value is a list of dictionaries where the dictionary
    at index i contains the functions which were changed in API version i.

    Returns
    -------
    list
      List of dictionaries representing the changes in the C API.
      In each dictionary, the key is the function name as written in the C API
      header file and the value is a tuple containing two elements.
      The first is the return type and the second is a list of argument types.
      This matches the format expected by declare_dll_function.

    Notes
    -----
    This function does not support the minor version numbers - those
    differences should be handled by wrapper functions.

    """
    raise NotImplementedError

  def available_capi_functions(self) -> dict[str, tuple]:
    """Returns all C API functions expected to be defined in the loaded dll.

    This is based on the version number reported by the DLL and the functions
    defined in capi_functions.

    Returns
    -------
    dict
      Dictionary of functions expected to be defined in the DLL.
      The key is the function name as written in the C API header file and the
      value is a tuple containing two elements.
      The first is the return type and the second is a list of argument types.
      This matches the format expected by declare_dll_function.
    """
    # Dictionary which will contain the functions which should be available
    # in the specified version of the C API.
    function_dict = {}

    # Generate the dictionary for the specified version.
    for changes in self.capi_functions()[:self.version[0] + 1]:
      function_dict.update(changes)

    return function_dict

  @staticmethod
  def method_prefix() -> str:
    """Returns the method prefix which is appended to function names.

    For example, in dataengine.py this function returns "DataEngine". Calling
    DataEngine.Function() would add this prefix to the function to get
    "DataEngineFunction" as the function to call in the C API.

    Returns
    -------
    str
      Prefix added by getattr.

    """
    raise NotImplementedError

  @staticmethod
  def dll_name() -> str:
    """The name of the DLL this wraps.

    This should not include the .dll extension.
    """
    raise NotImplementedError

  @property
  def dll(self) -> ctypes.CDLL:
    """Returns the DLL which this class wraps.

    Returns
    -------
    ctypes.cdll
      The dll this class wraps.

    """
    return self.__dll

  @staticmethod
  def oldest_supported_version() -> tuple[int, int]:
    """Returns the oldest C API version supported by the SDK.

    If the SDK attempts to connect to a version with a earlier
    version number than this an exception will be raised.

    Returns
    -------
    tuple
      A tuple with two elements representing the oldest
      supported version in the form (major, minor)

    """
    return (0, 0)

  @staticmethod
  def newest_supported_major_version() -> int:
    """Returns the highest major version number the SDK supports.

    Attempting to connect to an application with a higher major
    version number than returned by this function will cause an
    error to be raised.

    Returns
    -------
    int
      The highest major version number the SDK supports.

    Notes
    -----
    Ideally, if this function returns v, then the SDK should
    be able to support all C APIs with major version v including
    future versions. If a change would result in breaking this
    property, then the major version number should be incremented.

    """
    return 1

  def check_version_is_supported(self):
    """Raises a RuntimeError if version is not a supported version.

    If version is older than the oldest supported version or
    has a major version newer than the newest supported version it
    is considered not supported.
    """
    oldest_version = self.oldest_supported_version()
    newest_version = self.newest_supported_major_version()
    error_message = ""
    if self.version < oldest_version:
      error_message = ("The application is too old to be supported by the "
                       f"SDK.\nApplication C API version: {self.version}"
                       f"\nOldest supported version {oldest_version}")
    elif self.version[0] > newest_version:
      error_message = ("The application is too new to be supported by the "
                       f"SDK.\nApplication C API version: {self.version}"
                       f"\nNewest supported version {newest_version}")

    if error_message:
      raise RuntimeError(error_message)

  def load_version_information(self):
    """Loads the version information from the dll.

    The version is represented as a tuple of (major, minor). Versions can
    be compared using the < and > operators.

    Returns
    -------
    tuple
      Tuple containing two elements representing the version number.

    """
    try:
      major_version_function = getattr(self.dll,
                                       self.method_prefix() + "CApiVersion")
      major_version_function.restype = ctypes.c_uint32
      minor_version_function = getattr(
        self.dll, self.method_prefix() + "CApiMinorVersion")
      minor_version_function.restype = ctypes.c_uint32
      major = major_version_function()
      minor = minor_version_function()
      return (major, minor)
    except AttributeError:
      # The dll version not being found means version 0.0
      return (0, 0)

  def declare_dll_functions(self):
    """Declares all functions in expected to exist in the dll.

    Notes
    -----
    A function with a return type of the string constant "deleted"
    is ignored by this function.

    """
    # For each function, declare its restype and argtypes based
    # on the values in the dictionary/tuple.
    for name, parameters in self.available_capi_functions().items():
      if parameters[0] == "deleted":
        # Function was deleted, move onto the next one.
        continue
      try:
        # Declare the function with the return and arg types.
        dll_function = getattr(self.dll, name)
        dll_function.restype = parameters[0]
        dll_function.argtypes = parameters[1]
      except AttributeError:
        self.log.debug("%s not supported in DLL version.", name)

  def __getattr__(self, name):
    """Function called if a attribute which does not exist is requested.

    If there is a function message_prefix + name in the dll, that function
    is automatically returned. This automatically
    generates the trivial wrapper functions which require no special
    handling.

    """
    existing_function = getattr(self.dll, self.method_prefix() + name)
    if existing_function:
      return existing_function
    raise AttributeError
