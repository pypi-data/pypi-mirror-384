"""Classes designed for sending writable selections over the MCP.

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

from collections.abc import Sequence
import enum
import typing

from ..data import ObjectID
from .comms import SubMessage
from .serialisation import FixedInteger32Mixin


class SelectionType(FixedInteger32Mixin, enum.Flag):
  """The type of the writable selection."""
  NONE = 0
  """Nothing is selected."""
  POINT = 1 << 0
  """Point primitives are selected."""
  EDGE = 1 << 1
  """Edge primitives are selected."""
  FACET = 1 << 2
  """Facet primitives are selected."""
  CELL = 1 << 3
  """Cell primitives are selected."""
  TETRA = 1 << 4
  """Tetra primitives are selected."""
  BLOCK = 1 << 5
  """Block primitives are selected."""
  OBJECT = 1 << 6
  """Objects are selected."""


class WritableSelection(SubMessage, Sequence):
  """A selection intended to be sent in an MCP message."""
  class InternalSelection(SubMessage):
    """A data group containing a repeating field of ObjectID."""
    @classmethod
    def repeating_field_type(cls):
      return ObjectID

    @property
    def selection(self) -> Sequence[ObjectID]:
      return self.repeating_field_values

    @selection.setter
    def selection(self, values: Sequence[ObjectID]):
      self.repeating_field_values = values

  internal_selection: InternalSelection
  """The selected objects."""
  selection_type: SelectionType
  """The ctypes type of the selection ready for serialisation.

  Use the selection_type property to get the enum value.
  """
  # If the internal selection type is not NONE or OBJECT, then there is
  # another repeating field of ObjectID containing the objects which
  # have primitives selected (a subset of _internal_selection).
  # As of 2023-06-16 there is no good way to represent this on the Python SDK
  # side.
  # Fortunately, it is not needed for setting an object selection.
  # _primitive_selection: typing.Optional[InternalSelection]

  @classmethod
  def from_selection(cls, selection: "Sequence[ObjectID]") -> "typing.Self":
    """Construct from a sequence of ObjectID.

    This does not support primitive selections.

    Parameters
    ----------
    selection
      The ObjectIDs to contain in this selection.
    """
    result = cls()
    result.internal_selection = cls.InternalSelection()
    result.internal_selection.selection = selection
    selection_type = (
      SelectionType.OBJECT if len(selection) > 0 else SelectionType.NONE)
    result.selection_type = selection_type
    return result


  def __getitem__(self, index) -> tuple[ObjectID, SelectionType]:
    return self.internal_selection.selection[index]

  def __len__(self) -> int:
    return len(self.internal_selection.selection)

  def __eq__(self, __value: object) -> bool:
    if not isinstance(__value, WritableSelection):
      return False
    if self.selection_type != __value.selection_type:
      return False
    if len(self) != len(__value):
      return False
    for left, right in zip(self, __value):
      if left != right:
        return False
    return True

  def __str__(self) -> str:
    return (f"WritableSelection({self.selection_type},"
      f"{self.internal_selection.selection})")
