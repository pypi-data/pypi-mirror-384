"""Generic errors raised by classes in this packages.

More specialised errors are placed in other modules.

"""
###############################################################################
#
# (C) Copyright 2020, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from ..errors import ApplicationTooOldError


class ReadOnlyError(Exception):
  """Exception raised when operation fails due to being read-only"""
  def __init__(self, message=None):
    if message is None:
      message = "Operation is not available in read-only mode"
    super().__init__(message)


class CannotSaveInReadOnlyModeError(Exception):
  """Error raised when attempting to save an object in read only mode."""
  def __init__(self, message=None):
    if message is None:
      message = "Cannot save objects in read only mode"
    super().__init__(message)


class DegenerateTopologyError(Exception):
  """Error raised when creating an object with degenerate topology."""


class InvalidColourMapError(Exception):
  """Error raised when creating an invalid colour map."""


class RegistrationTypeNotSupportedError(ApplicationTooOldError):
  """Error raised when a type of raster registration is not supported."""
  def __init__(self, unsupported_type):
    message = (f"Registration type: {unsupported_type} is not supported by "
               "the object.")
    super().__init__(message)


class AlreadyAssociatedError(Exception):
  """Error raised when a associating a Raster which is already associated.

  The Raster may be associated with another object or be already
  associated with the same object.

  """


class NonOrphanRasterError(Exception):
  """Error raised when associating a raster which is not an orphan."""


class ObjectNotSupportedError(Exception):
  """Error raised when an object is not supported.

  Notes
  -----
  This does not inherit from ApplicationTooOldError. This error likely
  means Python has connected to a application which does not support
  the object in question.
  """
  def __init__(self, unsupported_type: type):
    self.unsupported_type = unsupported_type
    message = (
      f"'{unsupported_type.__name__}' is not supported in the application."
    )

    super().__init__(message)


class StaleDataError(Exception):
  """Error raised when accessing data which might be stale.

  A property is considered 'stale' if it is derived from another property
  and that property has changed but the derived property's has not been
  updated based on the change.
  """


class AppendPointsNotSupportedError(Exception):
  """Exception raised when appending points is not supported."""


class AmbiguousNameError(ValueError):
  """Error raised when a primitive attribute is given an ambiguous name.

  This is raised when attempting to create a primitive attribute with
  the same name as an existing attribute, but different metadata.
  """


class FileCorruptError(Exception):
  """Error raised when an imported file is corrupt."""


class AlreadyOpenedError(RuntimeError):
  """Error raised when attempting to open an object multiple times."""
