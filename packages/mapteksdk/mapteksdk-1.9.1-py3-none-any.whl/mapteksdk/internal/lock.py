"""Read/write lock functionality for project operations.

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
import typing

from enum import IntEnum

if typing.TYPE_CHECKING:
  from ..capi import DataEngineApi


class ObjectClosedError(Exception):
  """Error raised when accessing a closed object."""
  def __init__(self, message=None):
    if message is None:
      message = (
        "Cannot access a closed object. \n"
        "The object was accessed after the Project.new(), "
        "read() or edit() block was finished or after "
        "close() was called."
      )
    super().__init__(message)


class LockType(IntEnum):
  """Used to set mode for object instance to be read-only or read-write."""
  READ = 1
  READWRITE = 2

class ReadLock:
  """Provides a read lock over MDF objects to allow reading from objects
  within the Project.

  Parameters
  ----------
  handle : T_ObjectHandle
    The handle for the object to open for reading.

  """
  def __init__(self, handle, data_engine: DataEngineApi):
    self.handle = handle
    self._data_engine = data_engine
    self._lock = self._data_engine.ReadObject(handle)
    if not self._lock:
      last_error = self._data_engine.ErrorMessage()
      raise ValueError(f'Could not open object for read [{last_error}].')

  def __enter__(self):
    return self

  @property
  def is_closed(self):
    """Return True if the lock has been closed (the lock has been released)."""
    return not bool(self._lock)

  @property
  def lock(self):
    """Return the underlying handle to the lock."""
    if not self._lock:
      raise ObjectClosedError()
    return self._lock

  def close(self):
    """Close and dispose of object read lock."""
    if not self.is_closed:
      self._data_engine.CloseObject(self.lock)
      self._lock = None

  def __exit__(self, exc_type, exc_value, traceback):
    self.close()

class WriteLock:
  """Provides a write lock over MDF objects to allow writing to objects
  within the Project.

  Parameters
  ----------
  handle : T_ObjectHandle
    The handle for the object to open for writing (and reading).
  rollback_on_error : bool
    If true and there is an error that occurs when closing the lock
    it will rollback any unsaved changes made.

  """
  def __init__(
    self,
    handle,
    data_engine: DataEngineApi,
    *,
    rollback_on_error=False
  ):
    self.handle = handle
    self._data_engine = data_engine
    self.rollback_on_error = rollback_on_error
    self._lock = self._data_engine.EditObject(handle)
    if not self._lock:
      last_error = self._data_engine.ErrorMessage()
      raise ValueError(
        f'Could not open object for edit (write) [{last_error}].')

  def __enter__(self):
    return self

  @property
  def is_closed(self):
    """Return True if the lock has been closed (the lock has been released)."""
    return not bool(self._lock)

  @property
  def lock(self):
    """Return the underlying handle to the lock."""
    if not self._lock:
      raise ObjectClosedError()
    return self._lock

  def cancel(self):
    """Cancel any changes pending changes to the object."""
    self._data_engine.CancelObjectCommit(self.lock)

  def close(self):
    """Close and dispose of object write lock."""
    if not self.is_closed:
      self._data_engine.CloseObject(self.lock)
      self._lock = None

  def __exit__(self, exc_type, exc_value, traceback):
    try:
      # Check if an exception (error) has occurred.
      if exc_type is not None and self.rollback_on_error:
        # Rollback any unsaved changes.
        if not self.is_closed:
          self._data_engine.CancelObjectCommit(self.lock)
    finally:
      self.close()
