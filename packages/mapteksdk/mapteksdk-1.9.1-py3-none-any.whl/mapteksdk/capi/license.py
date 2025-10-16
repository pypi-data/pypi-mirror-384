"""Interface for the MDF license library.

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
import enum

from .wrapper_base import WrapperBase


class ReturnValues(enum.IntEnum):
  """Represents possible return values for functions in mdf_license.dll."""
  NONE_FOUND_ERROR = -4
  BUFFER_TO_SMALL_ERROR = -3
  OTHER_ERROR = -1
  FAILURE = 0
  SUCCESS = 1


class LicenseApi(WrapperBase):
  """Access to the application license API.

  This should be accessed through get_application_dlls() for new code.
  """
  @staticmethod
  def method_prefix():
    return "Licence"

  @staticmethod
  def dll_name() -> str:
    return "mdf_license"

  def supported_licence_format(self):
    """Return string of the supported licence format."""
    supported_format_size = ctypes.c_uint32(10)
    supported_format = ctypes.create_string_buffer(supported_format_size.value)
    result = self.GetFormat(
      supported_format,
      ctypes.byref(supported_format_size))
    if result == -3:
      # The buffer was too small; try again with buffer of the correct size.
      supported_format = ctypes.create_string_buffer(supported_format_size.value)
      result = self.GetFormat(
        supported_format,
        ctypes.byref(supported_format_size))

    if result != 1:
      raise ValueError('Could not determine supported licence format.')

    return bytearray(supported_format.value).decode('utf-8')

  def host_id(self) -> str:
    """Return a unique identifier for this machine (host).

    Raises
    ------
    ValueError
      If the host ID could not be found.
    """
    def check_for_errors(return_value):
      if return_value == ReturnValues.NONE_FOUND_ERROR:
        raise ValueError("No host ID found.")
      if return_value == ReturnValues.OTHER_ERROR:
        raise ValueError("Unable to determine host ID.")
      return return_value

    next_version_function = getattr(
      self.dll, 'LicenceSystemHostIdNewestVersion', None)

    # IF this function exists it means SystemHostId() requires the version.
    if next_version_function:
      host_id_version = next_version_function()
      host_id_function = lambda host_id, size: self.SystemHostId(
        host_id, size, host_id_version)
    else:
      host_id_function = self.SystemHostId

    host_id_size = 4
    host_id = ctypes.create_string_buffer(host_id_size)

    expected_host_id_size = host_id_function(host_id, host_id_size)
    check_for_errors(expected_host_id_size)
    if expected_host_id_size and expected_host_id_size != host_id_size:
      # If the buffer was the wrong size, try again with the right size.
      host_id = ctypes.create_string_buffer(expected_host_id_size)
      expected_host_id_size = host_id_function(host_id, expected_host_id_size)
      check_for_errors(expected_host_id_size)
    return bytearray(host_id.value).decode('utf-8')

  def host_id_version(self) -> int:
    """Returns the newest host ID version supported by the loaded DLL."""
    newest_version_function = getattr(
      self.dll, 'LicenceSystemHostIdNewestVersion', None)
    if newest_version_function:
      return newest_version_function()

    # If the function is not in the DLL it means the DLL uses version 0.
    return 0

  def capi_functions(self):
    return [
      # Functions changed in version 0.
      # Format:
      # "name" : (return_type, arg_types)
      {"LicenceGetFormat" : (ctypes.c_int64, [ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint32), ]),
       "LicenceGetFormatOfLicenceString" : (ctypes.c_int64, [ctypes.c_char_p, ctypes.c_uint32, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint32), ]),
       "LicenceGetLicenceHostInformation" : (ctypes.c_int64, [ctypes.c_char_p, ctypes.c_uint32, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint32), ]),
       "LicenceSystemHostId" : (ctypes.c_int32, [ctypes.c_char_p, ctypes.c_uint32, ]),
       "LicenceCheckLicence" : (ctypes.c_int64, [ctypes.c_char_p, ctypes.c_uint32, ctypes.c_char_p, ctypes.c_uint32, ctypes.c_uint64, ctypes.c_bool, ]),
       "LicenceCheckLicenceAllProducts" : (ctypes.c_int64, [ctypes.c_char_p, ctypes.c_uint32, ctypes.c_uint64, ctypes.c_bool, ]),
       "LicenceGetProductLicenceByFeatures" : (ctypes.c_int64, [ctypes.c_char_p, ctypes.c_uint32, ctypes.c_char_p, ctypes.c_uint32, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint32), ]),
       "LicenceGetFilePath" : (ctypes.c_uint32, [ctypes.c_uint32, ctypes.c_char_p, ctypes.c_uint32, ]),
       "LicenceGetDongles" : (ctypes.c_int64, [ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint32), ]),
       "LicenceDongleHasRecordSpace" : (ctypes.c_int64, [ctypes.c_char_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ]),
       "LicenceGetDongleByName" : (ctypes.c_int64, [ctypes.c_char_p, ctypes.c_uint32, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint32), ]),
       "LicenceGetUninitialisedVulcanDongles" : (ctypes.c_int64, [ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint32), ]),
       "LicenceInitialiseVulcanDongle" : (ctypes.c_int64, [ctypes.c_char_p, ctypes.c_uint32, ctypes.c_char_p, ctypes.c_uint32, ctypes.c_uint64, ]),
       "LicenceGetTpmId" : (ctypes.c_int64, [ctypes.c_char_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_bool), ]),
       "LicenceIsTpmHybrid" : (ctypes.c_int64, None),
       "LicenceTpmHasRecordSpace" : (ctypes.c_int64, [ctypes.c_uint32, ctypes.c_uint32, ]),
       "LicenceBorrowLicenceSet" : (ctypes.c_int64, [ctypes.c_char_p, ctypes.c_uint32, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint64, ctypes.c_bool, ]),
       "LicenceReturnLicenceSet" : (ctypes.c_int64, [ctypes.c_char_p, ctypes.c_uint32, ]),
       "LicenceGetLastError" : (ctypes.c_int64, [ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_void_p), ]),
       "LicenceGetFeatures" : (ctypes.c_int64, [ctypes.c_char_p, ctypes.c_uint32, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint64, ]),
       "LicenceRemoveExpiredTpmLicences" : (ctypes.c_int64, [ctypes.c_uint64, ]),
       "LicenceRemoveExpiredDongleLicences" : (ctypes.c_int64, [ctypes.c_char_p, ctypes.c_uint32, ctypes.c_uint64, ]),
       "LicenceGetHaspDriverVersion" : (ctypes.c_int64, [ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint32), ]),},
      # Functions changed in version 1.
      {"LicenceCApiVersion" : (ctypes.c_uint32, None),
       "LicenceCApiMinorVersion" : (ctypes.c_uint32, None),
       "LicenceSystemHostIdNewestVersion" : (ctypes.c_int32, None),
      }
    ]

