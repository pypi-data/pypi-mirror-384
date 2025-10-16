"""Errors raised by the project module."""
###############################################################################
#
# (C) Copyright 2020, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

from ..errors import ApplicationTooOldError

class DeleteRootError(Exception):
  """Error raised when you attempt to delete the root container."""

class ObjectDoesNotExistError(Exception):
  """Error raised when attempting an operation on an object which
  does not exist.

  """

class TypeMismatchError(TypeError):
  """Error raised when the type in the Project doesn't match.

  This is raised by Project.read() and Project.edit() when the actual type
  of the object in the Project does not match the expected type of that object.

  Parameters
  ----------
  expected_type
    The expected type for the object.
  actual_type
    The actual type of the object.
  """
  def __init__(self, expected_type: type, actual_type: type):
    self.expected_type = expected_type
    self.actual_type = actual_type
    expected_type_name = expected_type.__name__
    actual_type_name = actual_type.__name__
    super().__init__(
      f"Failed to open object. It was an {actual_type_name} instead "
      f"of a {expected_type_name}."
    )

class NoHostApplicationError(OSError):
  """Error raised when there are no host applications to connect to.

  This inherits from OSError for backwards compatibility reasons.
  """

class ProjectConnectionFailureError(Exception):
  """Error raised when connecting to the project fails."""

class NoRecycleBinError(ObjectDoesNotExistError):
  """Error raised when attempting an operation on the recycle bin which does
  not exist.
  """

class InvalidParentError(Exception):
  """Error raised when an object can't be the parent of another object.

  This is raised when adding an object to an object that can't be a parent.
  """
  def __init__(self, variable_name: str, path_to_parent: str):
    self.path = path_to_parent
    super().__init__(
      f"{variable_name} can not be added at {path_to_parent}, as the path is invalid.\n"
      "Check that the path for where to add the objects is correct and "
      "doesn't contain a object that can't have children.")
