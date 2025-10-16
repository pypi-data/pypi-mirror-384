"""Package containing classes for loading DLLs from MDF-based applications.

Warnings
--------
Vendors and clients should not develop scripts or applications against
this module. The contents may change at any time without warning.
"""
###############################################################################
#
# (C) Copyright 2024, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

from contextlib import AbstractContextManager
import pathlib
import typing

from .errors import CApiDllLoadFailureError, NoConnectedApplicationError
from .internal.application_dll_directory import (
  ApplicationDllDirectory,
)

# The C API wrappers:
from .dataengine import DataEngineApi
from .data_transfer import DataTransferApi
from .drillholemodel import DrillholeModelApi
from .license import LicenseApi
from .mcp import McpApi
from .modelling import ModellingApi
from .scan import ScanApi
from .sdp import SdpApi
from .selection import SelectionApi
from .system import SystemApi
from .topology import TopologyApi
from .translation import TranslationApi
from .viewer import ViewerApi
from .visualisation import VisualisationApi
from .vulcan import VulcanApi

if typing.TYPE_CHECKING:
  from collections.abc import Sequence

  from .wrapper_base import WrapperBase

  WrapperT = typing.TypeVar("WrapperT", bound=WrapperBase)


class MdfDlls(AbstractContextManager):
  """Handles loading DLLs from MDF-based applications."""
  def __init__(self, dll_path: pathlib.Path) -> None:
    self.__dll_path = dll_path
    self.__dll_directory = ApplicationDllDirectory(dll_path)
    self.__loaded_dlls: dict[str, WrapperBase] = {}
    """Dlls which have been loaded by this object."""
    self.__has_drillhole_model: bool | None = None
    """If the drillhole model DLL is available.

    None = Have not checked if the dll is available.
    False = Not available.
    True = Available.
    """

  def __enter__(self) -> typing.Self:
    return self

  def __exit__(
    self,
    exc_type: type[BaseException] | None,
    exc_value: BaseException | None,
    traceback
  ) -> bool | None:
    self.unload()
    return None

  def _load_dll(
    self,
    wrapper_class: type[WrapperT]
  ) -> WrapperT:
    if not self.can_load_dlls:
      raise NoConnectedApplicationError(
        "This function cannot be accessed because the script has disconnected "
        "from the application. Ensure all functions which require a "
        "connected application are inside of the Project's `with` block."
      )
    key = wrapper_class.dll_name()
    wrapper = self.__loaded_dlls.get(key, None)
    if wrapper is not None:
      return wrapper # type: ignore
    wrapper = wrapper_class(self.__dll_directory)
    self.__loaded_dlls[key] = wrapper
    return wrapper

  def all_dlls(self) -> Sequence[WrapperBase]:
    """Load and returns a sequence of all of the application DLLs."""
    dlls = [
      self.dataengine,
      self.data_transfer,
      self.license,
      self.mcp,
      self.modelling,
      self.scan,
      self.sdp,
      self.selection,
      self.system,
      self.topology,
      self.translation,
      self.viewer,
      self.visualisation,
      self.vulcan
    ]
    try:
      dlls.append(self.drillhole_model)
    except CApiDllLoadFailureError:
      # The application doesn't have this DLL.
      pass
    return dlls

  def unload(self):
    """Unload the loaded DLLs, preventing further use.

    Calling this is equivalent to exiting this class in a context manager.
    """
    self.__dll_directory.close()

  @property
  def dll_path(self) -> pathlib.Path:
    """The DLL path passed to the constructor."""
    return self.__dll_path

  @property
  def can_load_dlls(self) -> bool:
    """True if DLLs can be loaded, False otherwise."""
    return not self.__dll_directory.is_closed

  @property
  def has_drillhole_model(self) -> bool:
    """True if the drillhole model DLL is available."""
    has_drillhole_model = self.__has_drillhole_model
    if has_drillhole_model is None:
      try:
        _ = self.drillhole_model
        has_drillhole_model = True
      except CApiDllLoadFailureError:
        has_drillhole_model = False
      self.__has_drillhole_model = has_drillhole_model
    return has_drillhole_model

  @property
  def dataengine(self) -> DataEngineApi:
    """The DataEngine DLL wrapper."""
    return self._load_dll(DataEngineApi)

  @property
  def data_transfer(self) -> DataTransferApi:
    """The data transfer DLL wrapper."""
    return self._load_dll(DataTransferApi)

  @property
  def drillhole_model(self) -> DrillholeModelApi:
    """The drillhole model DLL wrapper."""
    return self._load_dll(DrillholeModelApi)

  @property
  def license(self) -> LicenseApi:
    """The license DLL wrapper."""
    return self._load_dll(LicenseApi)

  @property
  def mcp(self) -> McpApi:
    """The MCP DLL wrapper."""
    return self._load_dll(McpApi)

  @property
  def modelling(self) -> ModellingApi:
    """The modelling DLL wrapper."""
    return self._load_dll(ModellingApi)

  @property
  def scan(self) -> ScanApi:
    """The scan DLL wrapper."""
    return self._load_dll(ScanApi)

  @property
  def sdp(self) -> SdpApi:
    """The spatial data processing DLL wrapper."""
    return self._load_dll(SdpApi)

  @property
  def selection(self) -> SelectionApi:
    """The selection DLL wrapper."""
    return self._load_dll(SelectionApi)

  @property
  def system(self) -> SystemApi:
    """The system DLL wrapper."""
    return self._load_dll(SystemApi)

  @property
  def topology(self) -> TopologyApi:
    """The topology DLL wrapper."""
    return self._load_dll(TopologyApi)

  @property
  def translation(self) -> TranslationApi:
    """The translation DLL wrapper."""
    return self._load_dll(TranslationApi)

  @property
  def viewer(self) -> ViewerApi:
    """The viewer DLL wrapper."""
    return self._load_dll(ViewerApi)

  @property
  def visualisation(self) -> VisualisationApi:
    """The visualisation DLL wrapper."""
    return self._load_dll(VisualisationApi)

  @property
  def vulcan(self) -> VulcanApi:
    """The Vulcan DLL wrapper."""
    dll = self._load_dll(VulcanApi)
    # :HACK: Prior to API version 1.10, the DLL directory path must be on path
    # for the Vulcan DLL to correctly load the DLLs required for
    # import / export.
    if dll.version < (1, 10):
      self.__dll_directory.add_to_path()
    return dll
