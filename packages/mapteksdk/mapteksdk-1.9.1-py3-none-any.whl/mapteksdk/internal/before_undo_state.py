"""Serialisation class for the before state.

This is used to communicate the before state of an object
to the application for undo/redo.

This is not part of undo.py because that file uses
from __future__ import annotations
Which means it cannot declare classes designed to be
serialised over the MCP.

This can't be declared in serialisation.py either,
because it depends on the data subpackage.

:TODO: SDK-860 Move this class into undo.py.

Warnings
--------
Vendors and clients should not develop scripts or applications against
this package. The contents may change at any time without warning.
"""
###############################################################################
#
# (C) Copyright 2023, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

import typing

from .comms import InlineMessage
from ..data import ObjectID

class BeforeUndoState(InlineMessage):
  """Information required to undo changes to an object.

  This is used to send the state of the object before changes were
  made to the application to enable for the change to the object
  to be undone.
  """

  before_id: ObjectID
  """The ID of a clone of the object before it was edited."""

  primary_children: set[ObjectID]
  """A set of the children which had before_id as a primary parent.

  This should be the children before any changes were made to the object.
  This must be an empty set if before_id is not a container.
  """

  def __init__(
      self,
      before_id: ObjectID,
      primary_children: typing.Optional[set[ObjectID]]=None) -> None:
    self.before_id = before_id
    if primary_children is not None:
      self.primary_children = primary_children
    else:
      self.primary_children = set()
