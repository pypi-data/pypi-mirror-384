"""Experimental implementation of sparse cell networks.

Currently only supports type queries.

"""
###############################################################################
#
# (C) Copyright 2020, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

import ctypes
import logging

from ..internal.lock import LockType
from ..data.base import Topology, StaticType
from ..data.objectid import ObjectID

log = logging.getLogger("mapteksdk.data.cells")
# =========================================================================
#
#                        CELL NETWORK BASE CLASS
#
# =========================================================================
class CellNetworkBase(Topology):
  """Cell Network Base Class."""
  def __init__(self, object_id=None, lock_type=LockType.READWRITE):
    super().__init__(object_id, lock_type)
    self.__cell_count = None
    if self.id:
      self.__cell_count = self._modelling_api().ReadCellCount(self._lock.lock)

  @property
  def cell_count(self):
    """Returns the number of cells within cell network.

    Returns
    -------
    int
      The number of cells within the cell network.

    """
    if self.__cell_count is None and self.id is not None:
      self.__cell_count = self._modelling_api().ReadCellCount(self._lock.lock)
    return self.__cell_count

  def _extra_invalidate_properties(self):
    # TODO: Implement _extra_invalidate_properties()
    raise NotImplementedError()

  def _save(self):
    # TODO: Implement _save()
    log.warning("_save() not yet implemented on CellNetworkBase()")

  def _get_cell_count(self):
    """Get the number of cells in the object.

    Returns
    -------
    int
      The number of cells in the model.

    """
    return self._modelling_api().ReadCellCount(self._lock.lock)

  def _remove_cell(self, cell_index):
    """Flag single Cell index for removal when the lock is closed.

    Parameters
    ----------
    cell_index : long
      Index of cell to remove.

    Returns
    -------
    bool
      True if successful.

    Raises
    ------
    ReadOnlyError
      If called on an object not open for editing. This error indicates an
      issue with the script and should not be caught.

    Notes
    -----
    Changes may not be reflected until context manager is closed
    or reconciler called.

    """
    return self._modelling_api().RemoveCell(self._lock.lock, cell_index)


# =========================================================================
#
#                      SPARSE IRREGULAR CELLNETWORK CLASS
#
# =========================================================================
class SparseIrregularCellNetwork(CellNetworkBase):
  """Sparse irregular cell network.

  Parameters
  ----------
  row_count : int
    Count of rows.
  col_count : int
    Count of rows.
  valid_cell_map : ndarray or array
    1D array of bools representing which
    cells in the cell network will be considered valid (True)
    or as nulls (False).

  Raises
  ------
  Exception
    On failure to create.

  See Also
  --------
  CellNetworkBase : Base class for Cell Networks.

  Notes
  -----
  row_count, col_count and valid_cell_map parameters
  need only be specified if creating a new network.

  """
  # pylint: disable=dangerous-default-value
  def __init__(self, object_id=None, lock_type=LockType.READWRITE,
               row_count=0, col_count=0, valid_cell_map=[]):
    if object_id is None:
      arr_type = ctypes.c_bool * row_count * col_count
      bool_array = arr_type(*valid_cell_map)

      object_id = ObjectID(
        self._modelling_api().NewSparseIrregularCellNetwork(
          row_count, col_count, bool_array))

      if object_id is None:
        error_msg = 'Cannot create sparse irregular cell network'
        log.error(error_msg)
        raise RuntimeError(error_msg)

    super().__init__(object_id, lock_type)

  @classmethod
  def static_type(cls) -> StaticType:
    """Return the type of sparse irregular cell network as stored in a Project.

    This can be used for determining if the type of an object is a sparse
    irregular cell network.

    """
    return cls._modelling_api().SparseIrregularCellNetworkType()

  def _extra_invalidate_properties(self):
    # There are no properties to invalidate.
    pass
