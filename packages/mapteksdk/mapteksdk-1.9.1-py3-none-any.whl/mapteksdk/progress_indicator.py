"""Module containing the protocol and errors for progress indicators."""
###############################################################################
#
# (C) Copyright 2024, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

from contextlib import AbstractContextManager
import typing

from .errors import ApplicationTooOldError


class ProgressIndicatorNotSupportedError(ApplicationTooOldError):
  """Error raised if progress indicators aren't supported."""


class ProgressCancelledError(Exception):
  """Error raised if the user cancels the progress indicator."""


class ProgressFinishedError(Exception):
  """Error raised if accessing the progress indicator after it is closed.
  """


class ProgressIndicator(AbstractContextManager, typing.Protocol):
  """A user interface element for displaying progress to the user.

  Typically this is displayed as a bar which fills up as progress is made.
  The window (or other UI element used to display progress) is closed when
  the context manager is exited.
  """
  @property
  def is_cancelled(self) -> bool:
    """If the progress indicator has been cancelled."""
    raise NotImplementedError

  def set_progress(self, progress: int):
    """Set progress displayed in the user interface.

    Parameters
    ----------
    progress
      The percentage complete of the indicator as a number between zero and
      the maximum progress of the indicator.
      Zero indicates no progress (The indicator should be empty) and the
      maximum value indicates completion (The indicator should be full).

    Raises
    ------
    ValueError
      If progress is not a number, is less than zero or greater than the
      maximum progress.
    ProgressCancelledError
      If the user has cancelled the progress indicator in the connected
      application.
    """

  def add_progress(self, progress: int=1):
    """Add progress to the indicator.

    By default, this will add one unit of progress to the indicator.
    It is possible, but not usually necessary, to add more than one unit of
    progress at once by passing the amount of progress to add.

    Parameters
    ----------
    progress
      The amount of progress to add to the indicator.
      This is 1 by default.
      If this is a negative number, progress will be removed from the
      indicator.
      If this would make the progress greater than the maximum or less than 0,
      then the progress will be set to the maximum or 0 respectively.

    Raises
    ------
    ProgressCancelledError
      If the user has cancelled the progress indicator in the connected
      application.
    """
    raise NotImplementedError

  def fake_progress(self):
    """Set the indicator to display fake progress.

    This is useful to provide feedback to the user that something is happening
    when running part of an operation which does not support progress
    indication.

    Call set_progress() or add_progress() to cancel the fake progress.

    Raises
    ------
    ProgressCancelledError
      If the user has cancelled the progress indicator in the connected
      application.
    """
    raise NotImplementedError

  def update_message(self, new_message: str):
    """Update the message displayed with the progress indicator.

    Raises
    ------
    ProgressCancelledError
      If the user has cancelled the progress indicator in the connected
      application.
    """
    raise NotImplementedError
