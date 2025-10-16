"""Interface for the MDF system library.

Warnings
--------
Vendors and clients should not develop scripts or applications against
this module. The contents may change at any time without warning.

"""
###############################################################################
#
# (C) Copyright 2020, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

# pylint: disable=line-too-long
import ctypes

from .wrapper_base import WrapperBase


class SystemApi(WrapperBase):
  """Access to the application system API.

  This should be accessed through get_application_dlls() for new code.
  """
  @staticmethod
  def method_prefix():
    return "System"

  @staticmethod
  def dll_name() -> str:
    return "mdf_system"

  def capi_functions(self):
    return [
      # Functions changed in version 0.
      # Format:
      # "name" : (return_type, arg_types)
      {"SystemFlagInWorkbench" : (None, None),
       "SystemSetApplicationInformation" : (ctypes.c_void_p, [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ]),
       "SystemSetEtcPath" : (None, [ctypes.c_char_p, ]),
       "SystemSetBinPath" : (None, [ctypes.c_char_p, ]),
       "SystemNotifyEnvironmentChanged" : (None, None),
       "SystemBanEnvironmentUse" : (None, [ctypes.c_char_p, ]),
       "SystemAddToEnvironmentWhiteList" : (None, [ctypes.c_char_p, ]),
       "SystemHostId" : (ctypes.c_int32, [ctypes.c_char_p, ctypes.c_uint32, ]),
       "SystemLogFilePath" : (ctypes.c_int32, [ctypes.c_char_p, ctypes.c_uint32, ]),
       "SystemApplicationLogFilePath" : (ctypes.c_int32, [ctypes.c_char_p, ctypes.c_uint32, ]),
       "SystemBaseConfigurationDirectory" : (ctypes.c_int32, [ctypes.c_char_p, ctypes.c_uint32, ]),
       "SystemApplicationVersionSuffix" : (ctypes.c_int32, [ctypes.c_char_p, ctypes.c_uint32, ]),
       "SystemBranchVersion" : (ctypes.c_int32, [ctypes.c_char_p, ctypes.c_uint32, ]),
       "SystemBuildId" : (ctypes.c_int32, [ctypes.c_char_p, ctypes.c_uint32, ]),
       "SystemApplicationFeatureStrings" : (ctypes.c_int32, [ctypes.c_char_p, ctypes.c_uint32, ]),},
      # Functions changed in version 1.
      {}
    ]
