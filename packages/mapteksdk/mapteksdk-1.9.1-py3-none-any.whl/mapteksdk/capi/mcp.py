"""Interface for the MDF MCP (Master Control Program) library.

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
import typing

from .types import T_SocketFileMutexHandle, \
 _Opaque, T_TextHandle, T_MessageHandle
from .wrapper_base import WrapperBase

if typing.TYPE_CHECKING:
  from .internal.application_dll_directory import (
    ApplicationDllDirectoryProtocol,
  )


class McpApi(WrapperBase):
  """Access to the application master control program API.

  This should be accessed through get_application_dlls() for new code.
  """
  def __init__(self, dll_directory: ApplicationDllDirectoryProtocol):
    super().__init__(dll_directory)

    # Manually created wrapper functions.
    self.dll.Callback = ctypes.CFUNCTYPE(None, ctypes.POINTER(_Opaque))
    self.timer_callback_prototype = ctypes.CFUNCTYPE(None, ctypes.POINTER(_Opaque))
    try:
      self.dll.McpAddCallbackOnTimer.argtypes = [
        ctypes.c_double,
        ctypes.c_uint64,
        self.timer_callback_prototype]
      self.dll.McpAddCallbackOnMessage.restype = ctypes.c_void_p
      self.dll.McpAddCallbackOnMessage.argtypes = [
        ctypes.c_char_p,
        self.dll.Callback]
      self.dll.McpAddCallbackOnTimer.restype = ctypes.POINTER(_Opaque)
      self.dll.McpServiceEvents.restype = None
      self.dll.McpRemoveCallback.restype = None
      self.dll.McpRemoveCallback.argtypes = [ctypes.c_void_p]
      self.dll.McpRemoveCallbackOnMessage.restype = None
      self.dll.McpRemoveCallbackOnMessage.argtypes = [ctypes.c_char_p, ctypes.c_void_p]
    except:
      self.log.error("Failed to properly load MCP dll")
      raise

  @staticmethod
  def method_prefix():
    return "Mcp"

  @staticmethod
  def dll_name() -> str:
    return "mdf_mcp"

  def capi_functions(self):
    return [
      # Functions changed in version 0.
      # Format:
      # "name" : (return_type, arg_types)
      {"McpConnect" : (ctypes.c_bool, [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ]),
       "McpDisconnect" : (None, None),
       "McpIsConnected" : (ctypes.c_bool, None),
       "McpSoftShutdown" : (None, None),
       "McpForceShutdown" : (None, None),
       "McpSetKillable" : (None, [ctypes.c_bool, ]),
       "McpRegisterServer" : (ctypes.c_bool, [ctypes.c_char_p, ]),
       "McpNewServer" : (ctypes.c_bool, [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint32, ]),
       "McpNewSocketFile" : (T_SocketFileMutexHandle, [ctypes.c_char_p, ctypes.c_uint32, ]),
       "McpUnlockSocketFile" : (None, [T_SocketFileMutexHandle, ]),
       "McpNewMessage" : (T_MessageHandle, [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_bool, ]),
       "McpNewSubMessage" : (T_MessageHandle, None),
       "McpAppendBool" : (None, [T_MessageHandle, ctypes.c_bool, ]),
       "McpAppendUInt" : (None, [T_MessageHandle, ctypes.c_uint64, ctypes.c_uint8, ]),
       "McpAppendSInt" : (None, [T_MessageHandle, ctypes.c_int64, ctypes.c_uint8, ]),
       "McpAppendDouble" : (None, [T_MessageHandle, ctypes.c_double, ]),
       "McpAppendFloat" : (None, [T_MessageHandle, ctypes.c_float, ]),
       "McpAppendTimeDouble" : (None, [T_MessageHandle, ctypes.c_double, ]),
       "McpAppendString" : (None, [T_MessageHandle, ctypes.c_char_p, ]),
       "McpAppendByteArray" : (None, [T_MessageHandle, ctypes.c_void_p, ctypes.c_uint32, ]),
       "McpAppendText" : (None, [T_MessageHandle, T_TextHandle, ]),
       "McpAppendSubMessage" : (None, [T_MessageHandle, T_MessageHandle, ]),
       "McpSend" : (None, [T_MessageHandle, ]),
       "McpSendAndGetResponseBlocking" : (T_MessageHandle, [T_MessageHandle, ]),
       "McpIsBool" : (ctypes.c_bool, [T_MessageHandle, ]),
       "McpExtractBool" : (ctypes.c_bool, [T_MessageHandle, ]),
       "McpIsUInt" : (ctypes.c_bool, [T_MessageHandle, ]),
       "McpExtractUInt" : (ctypes.c_uint64, [T_MessageHandle, ]),
       "McpIsFloat" : (ctypes.c_bool, [T_MessageHandle, ]),
       "McpExtractFloat" : (ctypes.c_double, [T_MessageHandle, ]),
       "McpExtractTimeDouble" : (ctypes.c_double, [T_MessageHandle, ]),
       "McpIsSInt" : (ctypes.c_bool, [T_MessageHandle, ]),
       "McpExtractSInt" : (ctypes.c_int64, [T_MessageHandle, ]),
       "McpIsString" : (ctypes.c_bool, [T_MessageHandle, ]),
       "McpExtractString" : (None, [T_MessageHandle, ctypes.c_char_p, ctypes.c_uint64, ]),
       "McpGetNextStringLength" : (ctypes.c_uint32, [T_MessageHandle, ]),
       "McpIsByteArray" : (ctypes.c_bool, [T_MessageHandle, ]),
       "McpExtractByteArray" : (None, [T_MessageHandle, ctypes.c_void_p, ctypes.c_uint64, ]),
       "McpGetNextByteArrayLength" : (ctypes.c_uint32, [T_MessageHandle, ]),
       "McpFreeMessage" : (None, [T_MessageHandle, ]),
       "McpIsEom" : (ctypes.c_bool, [T_MessageHandle, ]),
       "McpIsSubMessage" : (ctypes.c_bool, [T_MessageHandle, ]),
       "McpExtractSubMessage" : (T_MessageHandle, [T_MessageHandle, ]),
       "McpIsText" : (ctypes.c_bool, [T_MessageHandle, ]),
       "McpExtractText" : (T_TextHandle, [T_MessageHandle, ]),
       "McpIsSessionVariableSet" : (ctypes.c_bool, [ctypes.c_char_p, ]),
       "McpServiceEvents" : (None, None),
       "McpServicePendingEvents" : (None, None),
       "McpGetMessageSender" : (ctypes.c_uint64, [T_MessageHandle, ctypes.c_char_p, ctypes.c_uint64, ]),
       "McpGetMessageSenderAuthorisationName" : (ctypes.c_uint64, [T_MessageHandle, ctypes.c_char_p, ctypes.c_uint64, ]),
       "McpBeginReply" : (T_MessageHandle, [T_MessageHandle, ]),
       "McpAnyFutureEventMatches" : (ctypes.c_bool, [T_MessageHandle, ctypes.c_bool, ]),
       "McpCreateSubMessage" : (T_MessageHandle, [ctypes.c_void_p, ctypes.c_uint32, ]),
       "McpGetSubMessageData" : (ctypes.c_uint32, [T_MessageHandle, ctypes.c_void_p, ctypes.c_uint32, ]),
       "McpEnableCrashReporting" : (None, [ctypes.c_bool, ]),
       "McpEmulateCrash" : (None, None),
       "McpGetSystemInformation" : (ctypes.c_uint32, [ctypes.c_char_p, ]),},
      # Functions changed in version 1.
      {"McpCApiVersion" : (ctypes.c_uint32, None),
       "McpCApiMinorVersion" : (ctypes.c_uint32, None),}
    ]
