"""Core functionality for connecting to a Maptek MDF-based application.

This handles connecting to the application and initialises internal
dependencies. The Project class provides methods for interacting with user
facing objects and data within the application.

"""
###############################################################################
#
# (C) Copyright 2020, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

# Imports retained for backwards compatibility for when the Project class
# was in this file.
from .errors import (
  DeleteRootError,
  ObjectDoesNotExistError,
  NoHostApplicationError,
  ProjectConnectionFailureError,
  ApplicationTooOldError,
  TypeMismatchError,
  NoRecycleBinError,
  InvalidParentError,
)
from .internal.project import Project
from .selection import Selection
from ..overwrite_modes import OverwriteMode


# Only the Project class will be documented for this page.
__all__ = [
  "Project",
]
