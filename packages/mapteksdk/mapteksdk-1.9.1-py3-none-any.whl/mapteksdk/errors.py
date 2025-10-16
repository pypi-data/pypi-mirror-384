"""Low level errors thrown by the functions in the SDK.

Users of the mapteksdk package should never throw these errors. Rather,
they are made available here to enable users to catch and handle them.
"""
###############################################################################
#
# (C) Copyright 2024, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
  from collections.abc import Sequence
  import pathlib

class ApplicationTooOldError(Exception):
  """Error raised if the application is too old to use certain functionality.

  Typically, this error indicates that the connected application is missing
  functionality which is required for the function which threw the exception
  to be used. In this case, upgrading the application to the newest version
  should resolve the error.

  The other case where this error will be raised is if the Python Script has
  connected to an application which does not officially support the Python
  SDK. In this case, switching to the newest version of an application which
  officially supports the Python SDK should resolve the error.

  Examples
  --------
  The main reason to catch this exception is if a script uses functionality
  which may not be supported by all target applications but it is still
  possible for the script to complete successfully (likely with reduced
  functionality). For example, the below fragment demonstrates how a script
  could read the edge thickness of an `EdgeNetwork`,
  defaulting to an edge thickness of 1.0 if the application doesn't support
  the property.

  >>> try:
  ...     thickness = edge_network.edge_thickness
  >>> except FunctionNotSupportedError:
  ...     # Treat the edge thickness as 1 if the application does not support
  ...     # reading it.
  ...     thickness = 1.0
  """
  @classmethod
  def with_default_message(cls, feature: str) -> typing.Self:
    """Construct a ApplicationTooOldError with the default message.

    The message will suggest that `feature` is not supported.

    Parameters
    ----------
    feature
      The feature which is not supported. This should start with a capital
      letter and not start with a full stop.
    """
    return cls(
      f"{feature} is not supported by the connected application. "
      "Updating the connected application to the newest version may resolve "
      "this error."
    )


class ImportFormatNotSupportedError(Exception):
  """Importing a file is not supported by the connected application.

  This may be because the application is too old for Python to be able to
  access the import functionality, or it may be because the connected
  application cannot import the given format.
  """
  @classmethod
  def from_path(cls, path: pathlib.Path) -> typing.Self:
    """Construct from a path."""
    return cls(
      f"Importing {path.suffix} files is not supported by the connected "
      "application."
    )


class FileImportError(Exception):
  """Error raised when an import of a file fails."""
  @classmethod
  def from_error_message(
    cls,
    path: pathlib.Path,
    messages: Sequence[str]
  ) -> typing.Self:
    """Construct an import error from a sequence of error messages."""
    if len(messages) == 0:
      return cls(
        f"Failed to import '{path}' due to an unknown error."
      )
    if len(messages) == 1:
      # The message should already include the path.
      return cls(messages[0])
    return cls(
      f"Failed to import '{path}' due to the following errors:\n"
      "\n".join(messages)
    )


class FileImportWarning(Warning):
  """Warning emitted when an import cannot be performed correctly.

  Typically, objects will still be imported from the file, but some
  information form the file may be lost.
  """
  @classmethod
  def from_warning_message(
    cls,
    path: pathlib.Path,
    warnings: Sequence[str]
  ) -> typing.Self:
    """Construct an import error from a sequence of warning messages."""
    if len(warnings) == 0:
      return cls(
        f"Empty warning while importing '{path}'."
      )
    if len(warnings) == 1:
      # The warning should already include the path.
      return cls(warnings[0])
    return cls(
      f"The import of '{path}' gave the following warnings:\n"
      "\n".join(warnings)
    )


class NoScanDataError(Exception):
  """The imported scan contains no data.

  The scan may be "image-only".
  """
  @classmethod
  def from_path(cls, path: pathlib.Path) -> typing.Self:
    return cls(
      f"Failed to import: {path}. "
      "The scan was empty or image-only."
    )
