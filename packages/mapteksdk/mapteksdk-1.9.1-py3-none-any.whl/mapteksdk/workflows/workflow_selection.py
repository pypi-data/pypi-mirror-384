"""ConnectorType subclasses dependent on the data module."""
###############################################################################
#
# (C) Copyright 2021, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

from collections.abc import Iterable, Sequence, Iterator
import csv
import typing
import warnings

from ..capi import DataEngine
from ..capi.types import T_ObjectHandle
from ..data.objectid import ObjectID
from ..data.base import DataObject
from ..internal.util import default_type_error_message
from ..workflows.connector_type import ConnectorType

class WorkflowSelection(ConnectorType):
  """Class representing a read-only list of ObjectIDs.

  Pass this to declare_input_connector for input connectors expecting a
  selection - the lists of objects given by the 'Maptek Database Object'
  connectors of many components.

  Iterating over this object will iterate over the ObjectIDs in the
  selection.

  You should not access the contents of this object until after
  Project() has been called.

  Parameters
  ----------
  selection_string
    String representing the selection.
  use_active_selection
    If True, the selection_string will be ignored and when ids is called
    it will return the current active selection.
    Typically use WorkflowSelection.active_selection() instead of setting
    this parameter to True.

  Raises
  ------
  NoConnectedApplicationError
    If the contents are accessed before Project() has been called.
  ValueError
    If part of the selection cannot be converted to an ObjectID.

  Warnings
  --------
  Ensure the ObjectIDs passed to this class are from the same
  project as is opened with Project() otherwise the ObjectIDs may refer to a
  completely different object.

  Notes
  -----
  This class does not support object paths which contain quotation marks
  or commas.

  Examples
  --------
  Script which takes a selection of objects and returns their centroid
  via a list output connector. This script would have one input
  connector "Selection" which accepts a selection. There is also one output
  connector "Centroid" which will be set to the centroid of all of the points
  in the objects in the selection. Note that this script does not honour
  point selection.

  >>> from mapteksdk.project import Project
  >>> from mapteksdk.workflows import (WorkflowArgumentParser,
  ...                                  WorkflowSelection,
  ...                                  Point3DConnectorType)
  >>> import numpy as np
  >>> parser = WorkflowArgumentParser(
  ...     description="Get the centroid of objects with points")
  >>> parser.declare_input_connector(
  ...     "selection",
  ...     WorkflowSelection,
  ...     description="Objects to find the centroid of.")
  >>> parser.declare_output_connector(
  ...     "Centroid",
  ...     Point3DConnectorType,
  ...     description="The centroid of the points in the objects.")
  >>> parser.parse_arguments() # Must call before Project().
  >>> project = Project() # Must call before get_ids().
  >>> sums = np.zeros(3)
  >>> count = 0
  >>> for oid in parser["selection"]:
  ...     with project.read(oid) as read_object:
  ...         if not hasattr(read_object, "points"): continue
  ...         sums += np.sum(read_object.points, axis=0)
  ...         count += read_object.point_count
  >>> result = sums / count
  >>> parser.set_output("Centroid", result)
  >>> parser.flush_output()
  """
  def __init__(
      self,
      selection_string: str,
      use_active_selection: bool=False):
    if not isinstance(selection_string, str):
      raise TypeError(default_type_error_message("workflow selection",
                                                 selection_string,
                                                 str))

    self.__use_active_selection = use_active_selection
    parsed_selection = []
    if not self.__use_active_selection:
      # First parse the selection string using the csv library.
      # This correctly handles commas which are within quotes.
      # e.g. "/cad/name,with,commas" is handled correctly.
      csv_selection = list(csv.reader([selection_string],
                                      skipinitialspace=True))[0]

      # First remove leading and trailing quotes from every item in
      # the list.
      for item in csv_selection:
        if item.startswith(("'", '"')):
          item = item[1:]
        if item.endswith(("'", '"')):
          item = item[:-1]
        parsed_selection.append(item)

      # Handle object ids which weren't quoted.
      for i, item in enumerate(parsed_selection):
        if item.startswith(("OID", "\\orphan")):
          if ";" in item:
            # The object ID came from a newer application which replaced the
            # comma inside the object ID with a semicolon to make splitting
            # the string unambiguous. Return the semicolon to a comma so that
            # the string can be converted back into an ObjectID.
            parsed_selection[i] = parsed_selection[i].replace(";", ",")
          elif "," not in item:
            try:
              # The ObjectID came from an older application so the ObjectID
              # will either be in the form OID(I##, C##, T##) or
              # OID(I##, O##).
              # Because the list was split via commas this means the ObjectID
              # will have been split to either of the following lists:
              # ["OID(I##", "C##", "T##)"]
              # or
              # ["OID(I##", "O##)"]
              # We determine which by finding the closing bracket and then
              # this can glue the object ID back together again.
              if ")" in parsed_selection[i + 1]:
                parsed_selection[i:i+2] = [", ".join([parsed_selection[i],
                                                      parsed_selection[i + 1]])]
              else:
                parsed_selection[i:i+3] = [", ".join([parsed_selection[i],
                                                      parsed_selection[i + 1],
                                                      parsed_selection[i + 2]])]
            except IndexError as error:
              # This is not expected to happen.
              raise RuntimeError("Failed to parse partial Object ID: "
                                f"{item}") from error
    self.__selection = parsed_selection
    self.__ids: list[ObjectID[DataObject]] | None = None

  @classmethod
  def type_string(cls) -> str:
    return "DataEngineObject"

  @classmethod
  def json_dimensionality(cls) -> str:
    return "List"

  @classmethod
  def from_string(cls, string_value: str) -> WorkflowSelection:
    return WorkflowSelection(string_value)

  @classmethod
  def from_string_list(
      cls, selection: Sequence[str]) -> WorkflowSelection:
    """Create a workflow selection from a sequence of paths.

    Parameters
    ----------
    selection
      Sequence of paths to include in the selection.

    Returns
    -------
    WorkflowSelection
      Selection objects containing the sequence of paths.

    Notes
    -----
    This does not require for the script to be connected to an application
    to be called.
    """
    result = cls("")
    # pylint: disable=unused-private-member
    result.__selection = list(selection)
    return result

  @classmethod
  def to_json(cls, value: str | Iterable) -> list[str]:
    # If passed a string, use it as the selection.
    if isinstance(value, str):
      return [value]
    # If not given an iterable, insert it into a list.
    if not isinstance(value, Iterable):
      value = [value]
    results = []
    for item in value:
      if isinstance(item, str):
        results.append(item)
      elif isinstance(item, ObjectID):
        results.append(str(item.path))
      elif isinstance(item, DataObject):
        results.append(str(item.id.path))
      else:
        raise TypeError(default_type_error_message("selection", item,
                                                   (str, Iterable)))
    return results

  @classmethod
  def to_default_json(cls, value: typing.Any) -> str:
    if isinstance(value, cls):
      # pylint: disable=protected-access
      return ",".join(value._selection)
    raise TypeError(
      default_type_error_message(
        argument_name="default selection",
        actual_value=value,
        required_type=WorkflowSelection
      )
    )

  @classmethod
  def active_selection(cls) -> WorkflowSelection:
    """Construct a WorkflowSelection which contains the active selection.

    Reading the ids property on the returned WorkflowSelection will return the
    ids of the currently selected objects in the application when ids was
    first called on that instance. (i.e. repeated reads to ids will
    always return the same list).

    Notes
    -----
    The active selection is not read until the ids property of the returned
    object is accessed. This allows this constructor to be called without
    any connected application, thus allowing this to be used as a default
    value for connectors.

    Once the ids property has been accessed, accessing the property again
    will always return the same list, even if the active selection in the
    application changes.

    Examples
    --------
    The following example script prints the path and type of every
    object in the selection. If there is no value from the "selection"
    input (e.g. If the corresponding connector was deleted or the
    script is run from outside of a workflow) then it will use the active
    selection instead.

    >>> from mapteksdk.project import Project
    >>> from mapteksdk.workflows import (
    ...   WorkflowArgumentParser, WorkflowSelection)
    >>> if __name__ == "__main__":
    ...   parser = WorkflowArgumentParser()
    ...   parser.declare_input_connector(
    ...     "selection",
    ...     WorkflowSelection,
    ...     default=WorkflowSelection.active_selection()
    ...   )
    ...   parser.parse_arguments()
    ...   with Project() as project:
    ...     for oid in parser["selection"]:
    ...       print(oid.path, ":", oid.type_name)

    The returned object can be used anywhere in place of a WorkflowSelection.
    For example, the following script sets the output selection to be
    the active selection in the application:

    >>> from mapteksdk.workflows import (
    ...   WorkflowArgumentParser, WorkflowSelection)
    >>> from mapteksdk.project import Project
    >>> if __name__ == "__main__":
    ...   parser = WorkflowArgumentParser()
    ...   parser.declare_output_connector("selection", WorkflowSelection)
    ...   parser.parse_arguments()
    ...   with Project() as project:
    ...     parser.set_output("selection", WorkflowSelection.active_selection())
    """
    return cls("", use_active_selection=True)

  @property
  def selection(self) -> list[str]:
    """The input selection split into strings.

    Accessing the contents of this list is not recommended.

    * This list will have the same length as the list returned by ids
      (Assuming all the selected objects exist).
    * Each item in the list will be a string.
    * The contents of each string in the list are unspecified.
    * Accessing this will not raise an error when not connected to an
      application.
    """
    warnings.warn(
      "'WorkflowSelection.selection' is deprecated and will be removed in "
      "a future version of the SDK.",
      DeprecationWarning
    )
    return self._selection

  @property
  def _selection(self) -> list[str]:
    """The input selection split into strings.

    Each string is in a form which can be constructed into an ObjectID,
    potentially using functions on ObjectID which start with an underscore.
    """
    return self.__selection

  @property
  def ids(self) -> list[ObjectID[DataObject]]:
    """Return the IDs in the selection as a list.

    This must be called after Project() has been called. Object IDs only have
    meaning within a Project.

    Returns
    -------
    list of ObjectID
      ObjectIDs in the selection.

    Raises
    ------
    ValueError
      If any string cannot be converted to an ObjectID.
    NoConnectedApplicationError
      If called before Project() is called.
    """
    if self.__ids is None:
      if self.__use_active_selection:
        # Copied from Project.get_selected().
        data_engine = DataEngine()
        count = data_engine.GetSelectedObjectCount()
        object_array = (T_ObjectHandle * count)()
        data_engine.GetSelectedObjects(object_array)
        self.__ids = [ObjectID(buff) for buff in object_array]
      else:
        result = []
        for item in self._selection:
          # The ObjectID constructor needs the DLLs so will fail with a
          # NoConnectedApplicationError if they aren't loaded.
          try:
            # pylint: disable=protected-access;reason="No other way to convert."
            result.append(ObjectID._from_string(item))
          except ValueError:
            result.append(ObjectID.from_path(item))
          self.__ids = result
    return self.__ids

  def __getitem__(self, key: int) -> ObjectID[DataObject]:
    return self.ids[key]

  def __len__(self) -> int:
    return len(self.ids)

  def __iter__(self) -> Iterator[ObjectID[DataObject]]:
    return iter(self.ids)
