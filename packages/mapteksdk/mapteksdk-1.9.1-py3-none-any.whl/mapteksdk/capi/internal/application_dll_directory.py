"""A class representing directories from which to load application DLLs.

Warnings
--------
Vendors and clients should not develop scripts or applications against
this module. The contents may change at any time without warning.
"""
from __future__ import annotations

import contextlib
import ctypes
import os
import pathlib
import typing

from .errors import DllDirectoryClosedError

class ApplicationDllDirectoryProtocol(
  contextlib.AbstractContextManager,
  typing.Protocol
):
  """A class representing directories from which to load application DLLs.

  Use this object in a context manager or call `close()` to ensure that
  DLL loading is cleaned up.

  Raises
  ------
  FileNotFoundError
    If the DLL directory could not be found.
  """

  @property
  def is_closed(self) -> bool:
    """True if the DLL directory has been closed."""
    raise NotImplementedError

  def load_dll(self, dll_name: str) -> ctypes.CDLL:
    """Load a DLL from the directory.

    Raises
    ------
    OSError
      If the DLL or one of its dependencies could not be found.
    DllDirectoryClosedError
      If the DLL directory has been closed.
    """
    raise NotImplementedError

  def add_to_path(self):
    """Add the DLL load paths to the PATH environment variable.

    Ideally, this would not be needed. The Vulcan DLL prior to C API version
    1.10 will only load DLL dependencies from PATH so sometimes this is
    needed.

    Raises
    ------
    DllDirectoryClosedError
      If this object has been closed.

    Notes
    -----
    Only one ApplicationDllDirectory instance can ever add its DLL load paths
    to the PATH environment variable.
    """
    raise NotImplementedError

  def close(self):
    """Close the DLL directory preventing further DLL loading.

    This deregisters the DLL directories as locations to load DLL
    dependencies from.

    This is the same as exiting a context manager for this class.
    """
    raise NotImplementedError


class ApplicationDllDirectory(ApplicationDllDirectoryProtocol):
  """Concrete implementation of ApplicationDllDirectoryProtocol."""
  _has_added_dlls_to_path: typing.ClassVar[bool] = False
  """If add_to_path has been called.

  This ensures the DLL directories are only added to PATH once.
  """

  def __init__(self, base_path: pathlib.Path) -> None:
    self._directory_paths: list[pathlib.Path] = []
    """Directories from which to load DLLs."""
    self._dll_directory_registrations: list[
      contextlib.AbstractContextManager] = []
    """DLL directory registrations for loading DLL dependencies."""
    self._closed = False
    """Whether this object has been closed.

    After the application DLL Directory has been closed, it is no longer
    possible to load new DLLs from it.
    """

    shlib_dir = base_path.parent / "shlib"
    if self._is_directory(shlib_dir):
      self._add_path_to_directory_paths(shlib_dir)
      eureka_path = shlib_dir / ".." / ".." / "eureka" / "shlib"
      eureka_path = eureka_path.resolve()

      if self._is_directory(eureka_path):
        self._add_path_to_directory_paths(eureka_path)
    elif self._is_directory(base_path):
      self._add_path_to_directory_paths(base_path)
    else:
      raise FileNotFoundError(
        f"Failed to find the application DLLs in '{base_path}'.")

  def __enter__(self) -> typing.Self:
    return self

  def __exit__(
    self,
    exc_type: type[BaseException] | None,
    exc_value: BaseException | None,
    traceback: typing.Any | None
  ) -> bool | None:
    if self._closed:
      return
    self._closed = True
    for manager in self._dll_directory_registrations:
      manager.__exit__(None, None, None)

  @property
  def is_closed(self) -> bool:
    return self._closed

  def load_dll(self, dll_name: str) -> ctypes.CDLL:
    if self._closed:
      raise DllDirectoryClosedError(
        "The DLL directory is closed."
      )
    last_error: OSError | None = None
    for base_path in self._directory_paths:
      try:
        return self._load_dll(str(base_path / dll_name))
      except OSError as error:
        last_error = error

    if last_error:
      raise last_error

    # The constructor would have errored if _directory_paths was empty.
    raise RuntimeError(
      "Failed to load dll due to reaching unreachable code."
    )

  def add_to_path(self):
    if self._closed:
      raise DllDirectoryClosedError(
        "The DLL directory is closed."
      )
    if self._has_added_dlls_to_path:
      return
    type(self)._has_added_dlls_to_path = True
    new_path = [str(dll_path) for dll_path in self._directory_paths]
    new_path.append(self._get_path())
    self._set_path(os.pathsep.join(new_path))

  def close(self):
    self.__exit__(None, None, None)

  def _add_path_to_directory_paths(self, path: pathlib.Path):
    """Add a path to `_directory_paths`.

    This also registers that DLL dependencies should be loaded from this path.
    """
    self._directory_paths.append(path)
    self._dll_directory_registrations.append(
      self._register_load_dlls_from(path)
    )

  def _register_load_dlls_from(
    self,
    path: pathlib.Path,
  ) -> contextlib.AbstractContextManager:
    """Register that DLL dependencies should be loaded from `path`."""
    return os.add_dll_directory(str(path))

  def _load_dll(self, dll_path: str) -> ctypes.CDLL:
    """Internal loading of a DLL.

    This is its own function to enable it to be replaced during testing.

    Raises
    ------
    OSError
      If the DLL could not be loaded.
    """
    return ctypes.CDLL(dll_path)

  def _is_directory(self, path: pathlib.Path) -> bool:
    """True if the specified path is a directory.

    This is its own function to enable it to be replaced during testing.
    """
    return path.is_dir()

  def _get_path(self) -> str:
    """Get the value of the PATH environment variable."""
    return os.environ["PATH"]

  def _set_path(self, new_path: str):
    """Set the value of the PATH environment variable."""
    os.environ["PATH"] = new_path
