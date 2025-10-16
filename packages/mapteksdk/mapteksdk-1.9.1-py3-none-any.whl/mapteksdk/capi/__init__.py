"""Wrappers for the MDF (Maptek Development Framework) C API.

Using the C API:
To access a function called: LibraryFunctionName in the dll library you
should call:
Library().FunctionName(arguments)
In particular, note that the Library prefix is dropped.

Warnings
--------
Vendors and clients should not develop scripts or applications against
this package. The contents may change at any time without warning.

"""
###############################################################################
#
# (C) Copyright 2020, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

from .dll_loading import get_application_dlls

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

# pylint: disable=invalid-name
# The names of these functions match the names of the C API wrapper classes
# when they were singletons.

# :TODO: Ideally, these functions would not need to exist and everything
# would go through get_application_dlls(), but changing everything over
# to do that is a big job which will provide little to no benefit.

def DataEngine() -> DataEngineApi:
  """Get the DataEngine API for the connected application.

  Raises
  ------
  NoConnectedApplicationError
    If the Python script is not currently connected to an application.
  """
  dlls = get_application_dlls()
  return dlls.dataengine

def DataTransfer() -> DataTransferApi:
  """Get the data transfer API for the connected application.

  Raises
  ------
  NoConnectedApplicationError
    If the Python script is not currently connected to an application.
  """
  dlls = get_application_dlls()
  return dlls.data_transfer

def DrillholeModel() -> DrillholeModelApi:
  """Get the drillhole model API for the connected application.

  Raises
  ------
  NoConnectedApplicationError
    If the Python script is not currently connected to an application.
  CApiDllLoadFailureError
    If the connected application is not GeologyCore.
  """
  dlls = get_application_dlls()
  return dlls.drillhole_model

def License() -> LicenseApi:
  """Get the license API for the connected application.

  Raises
  ------
  NoConnectedApplicationError
    If the Python script is not currently connected to an application.
  """
  dlls = get_application_dlls()
  return dlls.license

def Mcp() -> McpApi:
  """Get the MCP API for the connected application.

  Raises
  ------
  NoConnectedApplicationError
    If the Python script is not currently connected to an application.
  """
  dlls = get_application_dlls()
  return dlls.mcp

def Modelling() -> ModellingApi:
  """Get the modelling API for the connected application.

  Raises
  ------
  NoConnectedApplicationError
    If the Python script is not currently connected to an application.
  """
  dlls = get_application_dlls()
  return dlls.modelling

def Scan() -> ScanApi:
  """Get the scan API for the connected application.

  Raises
  ------
  NoConnectedApplicationError
    If the Python script is not currently connected to an application.
  """
  dlls = get_application_dlls()
  return dlls.scan

def Sdp() -> SdpApi:
  """Get the spatial data processing API for the connected application.

  Raises
  ------
  NoConnectedApplicationError
    If the Python script is not currently connected to an application.
  """
  dlls = get_application_dlls()
  return dlls.sdp

def Selection() -> SelectionApi:
  """Get the selection API for the connected application.

  Raises
  ------
  NoConnectedApplicationError
    If the Python script is not currently connected to an application.
  """
  dlls = get_application_dlls()
  return dlls.selection

def System() -> SystemApi:
  """Get the system API for the connected application.

  Raises
  ------
  NoConnectedApplicationError
    If the Python script is not currently connected to an application.
  """
  dlls = get_application_dlls()
  return dlls.system

def Topology() -> TopologyApi:
  """Get the topology API for the connected application.

  Raises
  ------
  NoConnectedApplicationError
    If the Python script is not currently connected to an application.
  """
  dlls = get_application_dlls()
  return dlls.topology

def Translation() -> TranslationApi:
  """Get the translation API for the connected application.

  Raises
  ------
  NoConnectedApplicationError
    If the Python script is not currently connected to an application.
  """
  dlls = get_application_dlls()
  return dlls.translation

def Viewer() -> ViewerApi:
  """Get the viewer API for the connected application.

  Raises
  ------
  NoConnectedApplicationError
    If the Python script is not currently connected to an application.
  """
  dlls = get_application_dlls()
  return dlls.viewer

def Visualisation() -> VisualisationApi:
  """Get the visualisation API for the connected application.

  Raises
  ------
  NoConnectedApplicationError
    If the Python script is not currently connected to an application.
  """
  dlls = get_application_dlls()
  return dlls.visualisation

def Vulcan() -> VulcanApi:
  """Get the Vulcan API for the connected application.

  Raises
  ------
  NoConnectedApplicationError
    If the Python script is not currently connected to an application.
  """
  dlls = get_application_dlls()
  return dlls.vulcan
