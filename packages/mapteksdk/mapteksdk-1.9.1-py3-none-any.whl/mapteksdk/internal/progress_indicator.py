"""Module containing the progress indicator class."""
###############################################################################
#
# (C) Copyright 2024, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import typing

from mapteksdk.internal.transaction_elemental import (
  ProgressIndicatorTransaction,
)
from mapteksdk.internal.transaction_errors import (
  TransactionSetUpError
)
from mapteksdk.internal.transaction_manager_protocol import (
  TransactionManagerProtocol,
)
from mapteksdk.internal.qualifiers import Qualifiers
from mapteksdk.progress_indicator import (
  ProgressIndicator,
  ProgressIndicatorNotSupportedError,
  ProgressFinishedError,
  ProgressCancelledError,
)

class ProgressIndicatorConcrete(ProgressIndicator):
  """Concrete implementation of Progress Indicator.

  This should not be instantiated directly. Use Project.progress_indicator()
  instead.

  Parameters
  ----------
  max_progress
    The maximum progress for the progress indicator.
  title
    The title for the progress indicator window.
    If None, a default will be used.
    This is not used if background=True.
  message
    The initial message which will appear above the progress indicator.
    If None, the progress indicator will have no message.
  background
    If False (default), the progress indicator will appear as a window in
    the connected application.
    If True, the progress indicator will appear in the status bar.
    Setting this to true is appropriate for background operations which still
    should display progress or long-running operations.

  Raises
  ------
  ValueError
    If max_progress is less than or equal to zero.
  """
  _FAKE_PROGRESS = -100
  """Constant used to indicate fake progress."""

  def __init__(
    self,
    max_progress: int=100,
    *,
    title: str | None=None,
    message: str | None=None,
    background: bool=False,
    manager: TransactionManagerProtocol,
  ) -> None:
    if max_progress <= 0:
      raise ValueError(
        "Maximum progress value must be greater than zero."
      )
    self.__transaction: ProgressIndicatorTransaction
    self.__transaction = manager.create_transaction(
      ProgressIndicatorTransaction
    )
    if title:
      self.__transaction.title = title
    if message:
      self.__transaction.message = message
    if background:
      self.__transaction.set_persistent()
    try:
      self.__transaction.send()
    except TransactionSetUpError as error:
      self.__transaction.__exit__(None, None, None)
      raise ProgressIndicatorNotSupportedError(
        "Failed to create a progress indicator. "
        "The application may not support progress indicators or it may be "
        "incompatible with this version of mapteksdk."
      ) from error
    self.__progress: int = 0
    """The current progress value of the indicator."""
    self.__previous_progress: int = 0
    """Previous progress value sent to the application.

    This is used for rate limiting. If the progress value hasn't changed,
    then no synchronise message will be sent.
    """
    self.__max_progress: int = int(max_progress)
    """Maximum value of the progress indicator."""
    self.__active = True
    """If the context manager has been exited."""

  def __enter__(self) -> typing.Self:
    return self

  def __exit__(
    self,
    exc_type: type[BaseException] | None,
    exc_value: BaseException | None,
    traceback
  ) -> bool | None:
    self.__transaction.__exit__(None, None, None)
    self.__active = False

  def _update(
    self,
    *,
    progress: int | None=None,
    message: str | None=None
  ):
    """Internal update of the server-side values.

    Parameters
    ----------
    progress
      How full the progress indicator should be between 0 and 100 for empty
      and full respectively.
      If None, the progress will not be updated.
    message
      The message to display beside the progress indicator.
      If None, the message will not be updated.
    """
    new_qualifiers = []
    if progress is not None:
      # If the progress hasn't changed, don't update the indicator.
      # This assumes you aren't updating progress and message at the same
      # time.
      if progress == self.__previous_progress:
        return
      self.__previous_progress = progress
      new_body = self.__transaction.body_type()()
      new_body.progress = progress
      new_body.is_cancellable = True
    else:
      new_body = None

    if message is not None:
      new_qualifiers.append(
        Qualifiers.message(message)
      )

    try:
      self.__transaction.synchronise(new_body, new_qualifiers or None)
    except RuntimeError:
      if self.__active:
        raise ProgressCancelledError(
          "The operation has been cancelled by the user."
        ) from None
      raise ProgressFinishedError(
        "Cannot update progress indicator after it has been closed."
      ) from None

  @property
  def _internal_progress(self) -> int:
    """How full the progress indicator is.

    This will be 0 for an empty progress indicator and 100 for a full progress
    indicator.

    Notes
    -----
    This is not updated when `fake_progress()` is called. This ensures that if
    `add_progress()` is called after `fake_progress()`, the progress indicator
    will remember how full the progress indicator was before `fake_progress()`
    was called.
    """
    return (self.__progress * 100) // self.__max_progress

  @property
  def is_cancelled(self) -> bool:
    return self.__transaction.is_cancelled

  def set_progress(self, progress: int):
    try:
      actual_progress = int(progress)
    except (ValueError, TypeError):
      raise ValueError(
        "Progress must be a number."
      ) from None

    if actual_progress < 0:
      raise ValueError(
        "Progress value must be positive."
      )
    if actual_progress > self.__max_progress:
      raise ValueError(
        f"Progress value must be less than {self.__max_progress}."
      )
    self.__progress = actual_progress
    self._update(progress=self._internal_progress)

  def add_progress(self, progress: int=1):
    new_progress = self.__progress + progress
    new_progress = min(new_progress, self.__max_progress)
    new_progress = max(new_progress, 0)
    self.set_progress(new_progress)

  def fake_progress(self):
    self._update(progress=self._FAKE_PROGRESS)

  def update_message(self, new_message: str):
    self._update(message=new_message)
