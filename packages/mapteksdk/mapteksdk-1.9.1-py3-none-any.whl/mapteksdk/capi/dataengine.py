"""Interface for the MDF dataengine library.

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
# pylint: disable=invalid-name;reason=Names match C++ names.
import ctypes
import datetime
import typing

from .errors import CApiUnknownError
from .types import (T_ReadHandle, T_ObjectHandle, T_NodePathHandle,
                    T_AttributeId, T_AttributeValueType, T_ContainerIterator,
                    T_TypeIndex, T_MessageHandle, T_ObjectWatcherHandle)
from .util import raise_if_version_too_old
from .wrapper_base import WrapperBase

if typing.TYPE_CHECKING:
  from collections.abc import Sequence, Callable


class DataEngineApi(WrapperBase):
  """Access to the application data engine API.

  This should be accessed through get_application_dlls() for new code.
  """
  @staticmethod
  def method_prefix():
    return "DataEngine"

  @staticmethod
  def dll_name() -> str:
    return "mdf_dataengine"

  def capi_functions(self):
    return [
      # Functions changed in version 0.
      # Format:
      # "name" : (return_type, arg_types)
      {"DataEngineErrorCode" : (ctypes.c_uint32, None),
       "DataEngineErrorMessage" : (ctypes.c_char_p, None),
       "DataEngineConnect" : (ctypes.c_bool, [ctypes.c_bool, ]),
       "DataEngineCreateLocal" : (ctypes.c_bool, None),
       "DataEngineOpenProject" : (ctypes.c_uint16, [ctypes.c_char_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ]),
       "DataEngineCloseProject" : (None, [ctypes.c_uint16, ]),
       "DataEngineDisconnect" : (None, [ctypes.c_bool, ]),
       "DataEngineDeleteStaleLockFile" : (ctypes.c_bool, [ctypes.c_char_p, ]),
       "DataEngineFlushProject" : (ctypes.c_bool, [ctypes.c_uint16, ]),
       "DataEngineObjectHandleFromString" : (ctypes.c_bool, [ctypes.c_char_p, ctypes.POINTER(T_ObjectHandle), ]),
       "DataEngineObjectHandleIcon" : (ctypes.c_uint32, [T_ObjectHandle, ctypes.c_char_p, ctypes.c_uint64, ]),
       "DataEngineObjectHandleFromNodePath" : (ctypes.c_bool, [T_NodePathHandle, ctypes.POINTER(T_ObjectHandle), ]),
       "DataEngineObjectHandleNodePath" : (T_NodePathHandle, [T_ObjectHandle, ]),
       "DataEngineObjectParentId" : (T_ObjectHandle, [T_ObjectHandle, ]),
       "DataEngineProjectRoot" : (T_ObjectHandle, [ctypes.c_uint16, ]),
       "DataEngineObjectHandleIsOrphan" : (ctypes.c_bool, [T_ObjectHandle, ]),
       "DataEngineObjectHandleExists" : (ctypes.c_bool, [T_ObjectHandle, ]),
       "DataEngineObjectHandleIsInRecycleBin" : (ctypes.c_bool, [T_ObjectHandle, ]),
       "DataEngineObjectBackEnd" : (ctypes.c_bool, [T_ObjectHandle, ctypes.POINTER(ctypes.c_uint16), ]),
       "DataEngineObjectDynamicType" : (T_TypeIndex, [T_ObjectHandle, ]),
       "DataEngineObjectIsLocked" : (ctypes.c_bool, [T_ObjectHandle, ]),
       "DataEngineNullType" : (T_TypeIndex, None),
       "DataEngineObjectType" : (T_TypeIndex, None),
       "DataEngineContainerType" : (T_TypeIndex, None),
       "DataEngineSlabType" : (T_TypeIndex, None),
       "DataEngineSlabOfBoolType" : (T_TypeIndex, None),
       "DataEngineSlabOfInt8uType" : (T_TypeIndex, None),
       "DataEngineSlabOfInt8sType" : (T_TypeIndex, None),
       "DataEngineSlabOfInt16uType" : (T_TypeIndex, None),
       "DataEngineSlabOfInt16sType" : (T_TypeIndex, None),
       "DataEngineSlabOfInt32uType" : (T_TypeIndex, None),
       "DataEngineSlabOfInt32sType" : (T_TypeIndex, None),
       "DataEngineSlabOfInt64uType" : (T_TypeIndex, None),
       "DataEngineSlabOfInt64sType" : (T_TypeIndex, None),
       "DataEngineSlabOfFloat32Type" : (T_TypeIndex, None),
       "DataEngineSlabOfFloat64Type" : (T_TypeIndex, None),
       "DataEngineSlabOfStringType" : (T_TypeIndex, None),
       "DataEngineSlabOfObjectIdType" : (T_TypeIndex, None),
       "DataEngineTypeParent" : (T_TypeIndex, [T_TypeIndex, ]),
       "DataEngineTypeName" : (ctypes.c_char_p, [T_TypeIndex, ]),
       "DataEngineFindTypeByName" : (T_TypeIndex, [ctypes.c_char_p, ]),
       "DataEngineTypeIsA" : (ctypes.c_bool, [T_TypeIndex, T_TypeIndex, ]),
       "DataEngineObjectWatcherFree" : (None, [T_ObjectWatcherHandle, ]),
       "DataEngineObjectWatcherNewContentAndChildWatcher" : (T_ObjectWatcherHandle, [T_ObjectHandle, ctypes.c_void_p, ]),
       "DataEngineObjectWatcherNewNameWatcher" : (T_ObjectWatcherHandle, [T_ObjectHandle, ctypes.c_void_p, ]),
       "DataEngineObjectWatcherNewPathWatcher" : (T_ObjectWatcherHandle, [T_ObjectHandle, ctypes.c_void_p, ]),
       "DataEngineNodePathFree" : (None, [T_NodePathHandle, ]),
       "DataEngineNodePathLeaf" : (ctypes.c_uint32, [T_NodePathHandle, ctypes.c_char_p, ctypes.c_uint64, ]),
       "DataEngineNodePathStem" : (T_NodePathHandle, [T_NodePathHandle, ]),
       "DataEngineNodePathHead" : (ctypes.c_uint32, [T_NodePathHandle, ctypes.c_char_p, ctypes.c_uint64, ]),
       "DataEngineNodePathTail" : (T_NodePathHandle, [T_NodePathHandle, ]),
       "DataEngineNodePathIsValid" : (ctypes.c_bool, [T_NodePathHandle, ]),
       "DataEngineNodePathIsNull" : (ctypes.c_bool, [T_NodePathHandle, ]),
       "DataEngineNodePathIsRoot" : (ctypes.c_bool, [T_NodePathHandle, ]),
       "DataEngineNodePathIsHidden" : (ctypes.c_bool, [T_NodePathHandle, ]),
       "DataEngineNodePathToString" : (ctypes.c_uint32, [T_NodePathHandle, ctypes.c_char_p, ctypes.c_uint64, ]),
       "DataEngineNodePathFromString" : (T_NodePathHandle, [ctypes.c_char_p, ]),
       "DataEngineNodePathEquality" : (ctypes.c_bool, [T_NodePathHandle, T_NodePathHandle, ]),
       "DataEngineReadObject" : (ctypes.POINTER(T_ReadHandle), [T_ObjectHandle, ]),
       "DataEngineEditObject" : (ctypes.POINTER(T_ReadHandle), [T_ObjectHandle, ]),
       "DataEngineCloseObject" : (None, [ctypes.POINTER(T_ReadHandle), ]),
       "DataEngineDeleteObject" : (ctypes.c_bool, [T_ObjectHandle, ]),
       "DataEngineCloneObject" : (T_ObjectHandle, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint16, ]),
       "DataEngineAssignObject" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(T_ReadHandle), ]),
       "DataEngineGetObjectCreationDateTime" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_int64), ]),
       "DataEngineGetObjectModificationDateTime" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_int64), ]),
       "DataEngineGetObjectRevisionNumber" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_uint32), ]),
       "DataEngineGetObjectIdRevisionNumber" : (ctypes.c_bool, [T_ObjectHandle, ctypes.POINTER(ctypes.c_uint32), ]),
       "DataEngineObjectToJson" : (ctypes.c_uint32, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ctypes.c_uint64, ]),
       "DataEngineCreateContainer" : (T_ObjectHandle, None),
       "DataEngineIsContainer" : (ctypes.c_bool, [T_ObjectHandle, ]),
       "DataEngineContainerElementCount" : (ctypes.c_uint32, [ctypes.POINTER(T_ReadHandle), ]),
       "DataEngineContainerFind" : (T_ObjectHandle, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "DataEngineContainerBegin" : (T_ContainerIterator, [ctypes.POINTER(T_ReadHandle), ]),
       "DataEngineContainerEnd" : (T_ContainerIterator, [ctypes.POINTER(T_ReadHandle), ]),
       "DataEngineContainerPreviousElement" : (T_ContainerIterator, [ctypes.POINTER(T_ReadHandle), T_ContainerIterator, ]),
       "DataEngineContainerNextElement" : (T_ContainerIterator, [ctypes.POINTER(T_ReadHandle), T_ContainerIterator, ]),
       "DataEngineContainerFindElement" : (T_ContainerIterator, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "DataEngineContainerElementName" : (ctypes.c_uint32, [ctypes.POINTER(T_ReadHandle), T_ContainerIterator, ctypes.c_char_p, ctypes.c_uint64, ]),
       "DataEngineContainerElementObject" : (T_ObjectHandle, [ctypes.POINTER(T_ReadHandle), T_ContainerIterator, ]),
       "DataEngineContainerInsert" : (T_ContainerIterator, [ctypes.POINTER(T_ReadHandle), T_ContainerIterator, ctypes.c_char_p, T_ObjectHandle, ctypes.c_bool, ]),
       "DataEngineContainerAppend" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, T_ObjectHandle, ctypes.c_bool, ]),
       "DataEngineContainerRemoveElement" : (T_ContainerIterator, [ctypes.POINTER(T_ReadHandle), T_ContainerIterator, ctypes.c_bool, ]),
       "DataEngineContainerRemove" : (T_ObjectHandle, [ctypes.POINTER(T_ReadHandle), ctypes.c_char_p, ]),
       "DataEngineContainerRemoveObject" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), T_ObjectHandle, ctypes.c_bool, ]),
       "DataEngineContainerReplaceElement" : (T_ContainerIterator, [ctypes.POINTER(T_ReadHandle), T_ContainerIterator, T_ObjectHandle, ]),
       "DataEngineContainerReplaceObject" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), T_ObjectHandle, T_ObjectHandle, ctypes.c_bool, ]),
       "DataEngineContainerPurge" : (None, [ctypes.POINTER(T_ReadHandle), ]),
       "DataEngineSlabOfBoolCreate" : (T_ObjectHandle, None),
       "DataEngineSlabOfInt8uCreate" : (T_ObjectHandle, None),
       "DataEngineSlabOfInt8sCreate" : (T_ObjectHandle, None),
       "DataEngineSlabOfInt16uCreate" : (T_ObjectHandle, None),
       "DataEngineSlabOfInt16sCreate" : (T_ObjectHandle, None),
       "DataEngineSlabOfInt32uCreate" : (T_ObjectHandle, None),
       "DataEngineSlabOfInt32sCreate" : (T_ObjectHandle, None),
       "DataEngineSlabOfInt64uCreate" : (T_ObjectHandle, None),
       "DataEngineSlabOfInt64sCreate" : (T_ObjectHandle, None),
       "DataEngineSlabOfFloat32Create" : (T_ObjectHandle, None),
       "DataEngineSlabOfFloat64Create" : (T_ObjectHandle, None),
       "DataEngineSlabOfStringCreate" : (T_ObjectHandle, None),
       "DataEngineSlabOfObjectIdCreate" : (T_ObjectHandle, None),
       "DataEngineSlabElementCount" : (ctypes.c_uint64, [ctypes.POINTER(T_ReadHandle), ]),
       "DataEngineSlabSetElementCount" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint64, ]),
       "DataEngineSlabOfBoolArrayBeginR" : (ctypes.POINTER(ctypes.c_bool), [ctypes.POINTER(T_ReadHandle), ]),
       "DataEngineSlabOfInt8uArrayBeginR" : (ctypes.POINTER(ctypes.c_uint8), [ctypes.POINTER(T_ReadHandle), ]),
       "DataEngineSlabOfInt8sArrayBeginR" : (ctypes.POINTER(ctypes.c_int8), [ctypes.POINTER(T_ReadHandle), ]),
       "DataEngineSlabOfInt16uArrayBeginR" : (ctypes.POINTER(ctypes.c_uint16), [ctypes.POINTER(T_ReadHandle), ]),
       "DataEngineSlabOfInt16sArrayBeginR" : (ctypes.POINTER(ctypes.c_int16), [ctypes.POINTER(T_ReadHandle), ]),
       "DataEngineSlabOfInt32uArrayBeginR" : (ctypes.POINTER(ctypes.c_uint32), [ctypes.POINTER(T_ReadHandle), ]),
       "DataEngineSlabOfInt32sArrayBeginR" : (ctypes.POINTER(ctypes.c_int32), [ctypes.POINTER(T_ReadHandle), ]),
       "DataEngineSlabOfInt64uArrayBeginR" : (ctypes.POINTER(ctypes.c_uint64), [ctypes.POINTER(T_ReadHandle), ]),
       "DataEngineSlabOfInt64sArrayBeginR" : (ctypes.POINTER(ctypes.c_int64), [ctypes.POINTER(T_ReadHandle), ]),
       "DataEngineSlabOfFloat32ArrayBeginR" : (ctypes.POINTER(ctypes.c_float), [ctypes.POINTER(T_ReadHandle), ]),
       "DataEngineSlabOfFloat64ArrayBeginR" : (ctypes.POINTER(ctypes.c_double), [ctypes.POINTER(T_ReadHandle), ]),
       "DataEngineSlabOfObjectIdArrayBeginR" : (ctypes.POINTER(T_ObjectHandle), [ctypes.POINTER(T_ReadHandle), ]),
       "DataEngineSlabOfBoolArrayBeginRW" : (ctypes.POINTER(ctypes.c_bool), [ctypes.POINTER(T_ReadHandle), ]),
       "DataEngineSlabOfInt8uArrayBeginRW" : (ctypes.POINTER(ctypes.c_uint8), [ctypes.POINTER(T_ReadHandle), ]),
       "DataEngineSlabOfInt8sArrayBeginRW" : (ctypes.POINTER(ctypes.c_int8), [ctypes.POINTER(T_ReadHandle), ]),
       "DataEngineSlabOfInt16uArrayBeginRW" : (ctypes.POINTER(ctypes.c_uint16), [ctypes.POINTER(T_ReadHandle), ]),
       "DataEngineSlabOfInt16sArrayBeginRW" : (ctypes.POINTER(ctypes.c_int16), [ctypes.POINTER(T_ReadHandle), ]),
       "DataEngineSlabOfInt32uArrayBeginRW" : (ctypes.POINTER(ctypes.c_uint32), [ctypes.POINTER(T_ReadHandle), ]),
       "DataEngineSlabOfInt32sArrayBeginRW" : (ctypes.POINTER(ctypes.c_int32), [ctypes.POINTER(T_ReadHandle), ]),
       "DataEngineSlabOfInt64uArrayBeginRW" : (ctypes.POINTER(ctypes.c_uint64), [ctypes.POINTER(T_ReadHandle), ]),
       "DataEngineSlabOfInt64sArrayBeginRW" : (ctypes.POINTER(ctypes.c_int64), [ctypes.POINTER(T_ReadHandle), ]),
       "DataEngineSlabOfFloat32ArrayBeginRW" : (ctypes.POINTER(ctypes.c_float), [ctypes.POINTER(T_ReadHandle), ]),
       "DataEngineSlabOfFloat64ArrayBeginRW" : (ctypes.POINTER(ctypes.c_double), [ctypes.POINTER(T_ReadHandle), ]),
       "DataEngineSlabOfObjectIdArrayBeginRW" : (ctypes.POINTER(T_ObjectHandle), [ctypes.POINTER(T_ReadHandle), ]),
       "DataEngineSlabOfBoolReadValues" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(ctypes.c_bool), ]),
       "DataEngineSlabOfInt8uReadValues" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint8), ]),
       "DataEngineSlabOfInt8sReadValues" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(ctypes.c_int8), ]),
       "DataEngineSlabOfInt16uReadValues" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint16), ]),
       "DataEngineSlabOfInt16sReadValues" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(ctypes.c_int16), ]),
       "DataEngineSlabOfInt32uReadValues" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint32), ]),
       "DataEngineSlabOfInt32sReadValues" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(ctypes.c_int32), ]),
       "DataEngineSlabOfInt64uReadValues" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ]),
       "DataEngineSlabOfInt64sReadValues" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(ctypes.c_int64), ]),
       "DataEngineSlabOfFloat32ReadValues" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(ctypes.c_float), ]),
       "DataEngineSlabOfFloat64ReadValues" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(ctypes.c_double), ]),
       "DataEngineSlabOfObjectIdReadValues" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(T_ObjectHandle), ]),
       "DataEngineSlabOfBoolSetValues" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(ctypes.c_bool), ]),
       "DataEngineSlabOfInt8uSetValues" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint8), ]),
       "DataEngineSlabOfInt8sSetValues" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(ctypes.c_int8), ]),
       "DataEngineSlabOfInt16uSetValues" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint16), ]),
       "DataEngineSlabOfInt16sSetValues" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(ctypes.c_int16), ]),
       "DataEngineSlabOfInt32uSetValues" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint32), ]),
       "DataEngineSlabOfInt32sSetValues" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(ctypes.c_int32), ]),
       "DataEngineSlabOfInt64uSetValues" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ]),
       "DataEngineSlabOfInt64sSetValues" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(ctypes.c_int64), ]),
       "DataEngineSlabOfFloat32SetValues" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(ctypes.c_float), ]),
       "DataEngineSlabOfFloat64SetValues" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(ctypes.c_double), ]),
       "DataEngineSlabOfObjectIdSetValues" : (None, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint64, ctypes.c_uint64, ctypes.POINTER(T_ObjectHandle), ]),
       "DataEngineSlabOfStringReadValue" : (ctypes.c_uint64, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint64, ctypes.c_char_p, ctypes.c_uint64, ]),
       "DataEngineSlabOfStringSetValue" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), ctypes.c_uint64, ctypes.c_char_p, ctypes.c_uint64, ]),
       "DataEngineGetAttributeId" : (T_AttributeId, [ctypes.c_char_p, ]),
       "DataEngineGetAttributeName" : (ctypes.c_uint64, [T_AttributeId, ctypes.c_char_p, ctypes.c_uint64, ]),
       "DataEngineGetAttributeList" : (ctypes.c_uint64, [ctypes.POINTER(T_ReadHandle), ctypes.c_void_p, ctypes.c_uint64, ]),
       "DataEngineGetAttributeValueType" : (T_AttributeValueType, [ctypes.POINTER(T_ReadHandle), T_AttributeId, ]),
       "DataEngineGetAttributeValueBool" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), T_AttributeId, ctypes.POINTER(ctypes.c_bool), ]),
       "DataEngineGetAttributeValueInt8s" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), T_AttributeId, ctypes.POINTER(ctypes.c_int8), ]),
       "DataEngineGetAttributeValueInt8u" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), T_AttributeId, ctypes.POINTER(ctypes.c_uint8), ]),
       "DataEngineGetAttributeValueInt16s" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), T_AttributeId, ctypes.POINTER(ctypes.c_int16), ]),
       "DataEngineGetAttributeValueInt16u" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), T_AttributeId, ctypes.POINTER(ctypes.c_uint16), ]),
       "DataEngineGetAttributeValueInt32s" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), T_AttributeId, ctypes.POINTER(ctypes.c_int32), ]),
       "DataEngineGetAttributeValueInt32u" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), T_AttributeId, ctypes.POINTER(ctypes.c_uint32), ]),
       "DataEngineGetAttributeValueInt64s" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), T_AttributeId, ctypes.POINTER(ctypes.c_int64), ]),
       "DataEngineGetAttributeValueInt64u" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), T_AttributeId, ctypes.POINTER(ctypes.c_uint64), ]),
       "DataEngineGetAttributeValueFloat32" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), T_AttributeId, ctypes.POINTER(ctypes.c_float), ]),
       "DataEngineGetAttributeValueFloat64" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), T_AttributeId, ctypes.POINTER(ctypes.c_double), ]),
       "DataEngineGetAttributeValueDateTime" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), T_AttributeId, ctypes.POINTER(ctypes.c_int64), ]),
       "DataEngineGetAttributeValueDate" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), T_AttributeId, ctypes.POINTER(ctypes.c_int32), ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8), ]),
       "DataEngineGetAttributeValueString" : (ctypes.c_uint64, [ctypes.POINTER(T_ReadHandle), T_AttributeId, ctypes.c_char_p, ctypes.c_uint64, ]),
       "DataEngineSetAttributeNull" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), T_AttributeId, ]),
       "DataEngineSetAttributeBool" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), T_AttributeId, ctypes.c_bool, ]),
       "DataEngineSetAttributeInt8s" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), T_AttributeId, ctypes.c_int8, ]),
       "DataEngineSetAttributeInt8u" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), T_AttributeId, ctypes.c_uint8, ]),
       "DataEngineSetAttributeInt16s" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), T_AttributeId, ctypes.c_int16, ]),
       "DataEngineSetAttributeInt16u" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), T_AttributeId, ctypes.c_uint16, ]),
       "DataEngineSetAttributeInt32s" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), T_AttributeId, ctypes.c_int32, ]),
       "DataEngineSetAttributeInt32u" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), T_AttributeId, ctypes.c_uint32, ]),
       "DataEngineSetAttributeInt64s" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), T_AttributeId, ctypes.c_int64, ]),
       "DataEngineSetAttributeInt64u" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), T_AttributeId, ctypes.c_uint64, ]),
       "DataEngineSetAttributeFloat32" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), T_AttributeId, ctypes.c_float, ]),
       "DataEngineSetAttributeFloat64" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), T_AttributeId, ctypes.c_double, ]),
       "DataEngineSetAttributeDateTime" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), T_AttributeId, ctypes.c_int64, ]),
       "DataEngineSetAttributeDate" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), T_AttributeId, ctypes.c_int32, ctypes.c_uint8, ctypes.c_uint8, ]),
       "DataEngineSetAttributeString" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), T_AttributeId, ctypes.c_char_p, ]),
       "DataEngineDeleteAttribute" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), T_AttributeId, ]),
       "DataEngineDeleteAllAttributes" : (ctypes.c_bool, [ctypes.POINTER(T_ReadHandle), ]),
       "DataEngineRootContainer" : (T_ObjectHandle, None),
       "DataEngineAppendHandleToMessage" : (None, [T_MessageHandle, T_ObjectHandle, ]),
       "DataEngineCreateMaptekObjFile" : (ctypes.c_bool, [ctypes.c_char_p, T_ObjectHandle, ]),
       "DataEngineCreateMaptekObjJsonFile" : (ctypes.c_bool, [ctypes.c_char_p, T_ObjectHandle, ]),
       "DataEngineReadMaptekObjFile" : (T_ObjectHandle, [ctypes.c_char_p, ]),
       "DataEngineGetSelectedObjectCount" : (ctypes.c_uint32, None),
       "DataEngineGetSelectedObjects" : (None, [ctypes.POINTER(T_ObjectHandle), ]),
       "DataEngineSetSelectedObject" : (None, [T_ObjectHandle, ]),
       "DataEngineSetSelectedObjects" : (None, [ctypes.POINTER(T_ObjectHandle), ctypes.c_uint32, ])},
      # Functions changed in version 1.
      {"DataEngineCApiVersion" : (ctypes.c_uint32, None),
       "DataEngineCApiMinorVersion" : (ctypes.c_uint32, None),

       # New in API version 1.6.
       #
       # The argument should really be a T_EditHandle but
       # DataEngineEditObject() returns a T_ReadHandle. In part because there
       # are cases where a T_EditHandle and T_ReadHandle can be used.
       "DataEngineCancelObjectCommit" : (ctypes.c_uint32, [ctypes.POINTER(T_ReadHandle)]),

       # New in API version 1.8.
       "DataEngineRecycleBin" : (T_ObjectHandle, [ctypes.c_uint16]),

       # New in API version 1.9.
       "DataEngineProjectPath" : (ctypes.c_uint32, [ctypes.c_uint16, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint32), ]),
       "DataEngineCheckpoint" : (ctypes.c_uint32, [ctypes.POINTER(T_ReadHandle), ctypes.POINTER(ctypes.c_uint32), ]),

       # New in API version 1.10:
       "DataEngineShallowCloneObject" : (T_ObjectHandle, [ctypes.POINTER(T_ReadHandle), ]),

       # New in API version 1.12:
       "DataEngineNewObject" : (T_ObjectHandle, [T_TypeIndex, ]),
       }
    ]

  def Disconnect(self, *args):
    """Handles backwards compatibility with disconnecting from a project."""
    if self.version < (1, 1):
      # There was a bug with this function that meant it would leave the
      # application is a bad state which often result in it crashing.
      self.log.warning("Unable to disconnect from project. This means "
                       "connecting to another project won't work.")
      return

    self.dll.DataEngineDisconnect(*args)

  def ErrorMessage(self) -> str:
    """Get the last error message logged by a C API function.

    This should only be called after calling a C API function which can fail.
    Otherwise, the value may be irrelevant.
    """
    return self.dll.DataEngineErrorMessage().decode("utf-8")

  def TypeIsA(self, object_type, type_index):
    """Wrapper for checking the type of an object."""
    if type_index is None:
      return False
    return self.dll.DataEngineTypeIsA(object_type, type_index)

  def RootContainer(self) -> T_ObjectHandle:
    """Return the object handle for the root container.

    It is not valid to call this function without first creating or opening
    a DataEngine.
    """
    # Older versions of the software will most likely cause the Python process
    # to crash. This is a sign that the mapteksdk developers made a mistake
    # rather than the end user or the end user managed find an untested path
    # that avoided opening the DataEngine.
    object_handle = self.dll.DataEngineRootContainer()

    if not object_handle:
      raise CApiUnknownError(self.dll.DataEngineErrorMessage())

    return object_handle

  def GetAttributeList(self, lock) -> Sequence[int]:
    """Get a sequence of the ids of the attributes on the object open with `lock`."""
    attribute_count = self.dll.DataEngineGetAttributeList(lock, None, 0)
    buffer = (ctypes.c_uint32 * attribute_count)()
    self.dll.DataEngineGetAttributeList(
      lock,
      buffer,
      attribute_count,
    )
    return buffer

  def GetAttributeName(self, attribute_id: int) -> str:
    """Get the name of the attribute with id `attribute_id`."""
    required_buffer_size = self.dll.DataEngineGetAttributeName(attribute_id, None, 0)
    buffer = ctypes.create_string_buffer(required_buffer_size)
    self.dll.DataEngineGetAttributeName(attribute_id, buffer, required_buffer_size)
    return buffer.value.decode("utf-8")

  def GetAttributeValueType(self, lock, attribute_id: int) -> int:
    """Get the type ID of the attribute with id `attribute_id`."""
    return self.dll.DataEngineGetAttributeValueType(lock, attribute_id).value

  def GetAttributeId(self, name: str) -> int:
    """Get the id of the `name` attribute."""
    return self.dll.DataEngineGetAttributeId(name.encode("utf-8")).value

  def DeleteAttribute(self, lock, attribute_id: int):
    """Delete the attribute with the given id from `lock`.

    Raises
    ------
    RuntimeError
      If the attribute cannot be deleted.
    """
    success = self.dll.DataEngineDeleteAttribute(lock, attribute_id)
    if not success:
      message = self.ErrorMessage()
      raise RuntimeError(
        "Failed to delete object attribute due to the following "
        f"error: {message}."
      )

  def DeleteAllAttributes(self, lock):
    """Delete all object attributes from `lock`.

    Raises
    ------
    RuntimeError
      If the object attributes could not be deleted.
    """
    success = self.dll.DataEngineDeleteAllAttributes(lock)
    if not success:
      message = self.ErrorMessage()
      raise RuntimeError(
        f"Failed to delete all attributes due to the following error: "
        f"{message}")

  def GetAttributeValueBool(self, lock, attribute_id: int) -> bool:
    """Get the value of a bool primitive attribute."""
    buffer = ctypes.c_bool()
    success =  self.dll.DataEngineGetAttributeValueBool(lock, attribute_id, ctypes.byref(buffer))
    if not success:
      raise KeyError(f"Object attribute: {attribute_id} does not exist.")
    return buffer.value

  def GetAttributeValueInt8s(self, lock, attribute_id: int) -> int:
    """Get the value of a 8 bit signed integer primitive attribute."""
    buffer = ctypes.c_int8()
    success =  self.dll.DataEngineGetAttributeValueInt8s(lock, attribute_id, ctypes.byref(buffer))
    if not success:
      raise KeyError(f"Object attribute: {attribute_id} does not exist.")
    return buffer.value

  def GetAttributeValueInt16s(self, lock, attribute_id: int) -> int:
    """Get the value of a 16 bit signed integer primitive attribute."""
    buffer = ctypes.c_int16()
    success =  self.dll.DataEngineGetAttributeValueInt16s(lock, attribute_id, ctypes.byref(buffer))
    if not success:
      raise KeyError(f"Object attribute: {attribute_id} does not exist.")
    return buffer.value

  def GetAttributeValueInt32s(self, lock, attribute_id: int) -> int:
    """Get the value of a 32 bit signed integer primitive attribute."""
    buffer = ctypes.c_int32()
    success =  self.dll.DataEngineGetAttributeValueInt32s(lock, attribute_id, ctypes.byref(buffer))
    if not success:
      raise KeyError(f"Object attribute: {attribute_id} does not exist.")
    return buffer.value

  def GetAttributeValueInt64s(self, lock, attribute_id: int) -> int:
    """Get the value of a 64 bit signed integer primitive attribute."""
    buffer = ctypes.c_int64()
    success =  self.dll.DataEngineGetAttributeValueInt64s(lock, attribute_id, ctypes.byref(buffer))
    if not success:
      raise KeyError(f"Object attribute: {attribute_id} does not exist.")
    return buffer.value

  def GetAttributeValueInt8u(self, lock, attribute_id: int) -> int:
    """Get the value of a 8 bit unsigned integer primitive attribute."""
    buffer = ctypes.c_uint8()
    success =  self.dll.DataEngineGetAttributeValueInt8u(lock, attribute_id, ctypes.byref(buffer))
    if not success:
      raise KeyError(f"Object attribute: {attribute_id} does not exist.")
    return buffer.value

  def GetAttributeValueInt16u(self, lock, attribute_id: int) -> int:
    """Get the value of a 16 bit unsigned integer primitive attribute."""
    buffer = ctypes.c_uint16()
    success =  self.dll.DataEngineGetAttributeValueInt16u(lock, attribute_id, ctypes.byref(buffer))
    if not success:
      raise KeyError(f"Object attribute: {attribute_id} does not exist.")
    return buffer.value

  def GetAttributeValueInt32u(self, lock, attribute_id: int) -> int:
    """Get the value of a 32 bit unsigned integer primitive attribute."""
    buffer = ctypes.c_uint32()
    success =  self.dll.DataEngineGetAttributeValueInt32u(lock, attribute_id, ctypes.byref(buffer))
    if not success:
      raise KeyError(f"Object attribute: {attribute_id} does not exist.")
    return buffer.value

  def GetAttributeValueInt64u(self, lock, attribute_id: int) -> int:
    """Get the value of a 64 bit unsigned integer primitive attribute."""
    buffer = ctypes.c_uint64()
    success =  self.dll.DataEngineGetAttributeValueInt64u(lock, attribute_id, ctypes.byref(buffer))
    if not success:
      raise KeyError(f"Object attribute: {attribute_id} does not exist.")
    return buffer.value

  def GetAttributeValueFloat32(self, lock, attribute_id: int) -> float:
    """Get the value of a 32 bit float primitive attribute."""
    buffer = ctypes.c_float()
    success =  self.dll.DataEngineGetAttributeValueFloat32(lock, attribute_id, ctypes.byref(buffer))
    if not success:
      raise KeyError(f"Object attribute: {attribute_id} does not exist.")
    return buffer.value

  def GetAttributeValueFloat64(self, lock, attribute_id: int) -> float:
    """Get the value of a 64 bit float primitive attribute."""
    buffer = ctypes.c_double()
    success =  self.dll.DataEngineGetAttributeValueFloat64(lock, attribute_id, ctypes.byref(buffer))
    if not success:
      raise KeyError(f"Object attribute: {attribute_id} does not exist.")
    return buffer.value

  def GetAttributeValueString(self, lock, attribute_id: int) -> str:
    """Get the value of a string primitive attribute."""
    buffer_size = self.dll.DataEngineGetAttributeValueString(lock, attribute_id, None, 0)

    buffer = ctypes.create_string_buffer(buffer_size)
    self.dll.DataEngineGetAttributeValueString(lock, attribute_id, buffer, buffer_size)
    return buffer.value.decode("utf-8")

  def GetAttributeValueDateTime(self, lock, attribute_id: int) -> datetime.datetime:
    """Get the value of a datetime primitive attribute."""
    buffer = ctypes.c_int64()
    success =  self.dll.DataEngineGetAttributeValueDateTime(lock, attribute_id, ctypes.byref(buffer))
    if not success:
      raise KeyError(f"Object attribute: {attribute_id} does not exist.")
    value = datetime.datetime.fromtimestamp(
      buffer.value / 1000000,
      datetime.timezone.utc
    )
    value = value.replace(tzinfo=None)  # Remove timezone awareness.
    return value

  def GetAttributeValueDate(self, lock, attribute_id: int) -> datetime.date:
    """Get the value of a date primitive attribute."""
    year = ctypes.c_int32()
    month = ctypes.c_uint8()
    day = ctypes.c_uint8()
    success = self.dll.DataEngineGetAttributeValueDate(
      lock,
      attribute_id,
      ctypes.byref(year),
      ctypes.byref(month),
      ctypes.byref(day)
      )
    if not success:
      raise KeyError(f"Object attribute: {attribute_id} does not exist.")
    return datetime.date(year.value, month.value, day.value)

  def SetAttributeNull(self, lock, attribute_id: int, _: typing.Any = None) -> bool:
    """Set `attribute_id` to be a null attribute."""
    return self.dll.DataEngineSetAttributeNull(lock, attribute_id)

  def SetAttributeString(self, lock, attribute_id: int, data: str) -> bool:
    """Set a string object attribute."""
    try:
      return self.dll.DataEngineSetAttributeString(lock, attribute_id, data.encode("utf-8"))
    except AttributeError:
      raise TypeError(
        f"Could not convert {data} to UTF-8 string.") from None

  def SetAttributeDateTime(self, lock, attribute_id: int, data: datetime.datetime) -> bool:
    """Set a date time object attribute."""
    data = data.replace(tzinfo=datetime.timezone.utc)
    return self.dll.DataEngineSetAttributeDateTime(
      lock,
      attribute_id,
      int(data.timestamp() * 1000000)
    )

  def SetAttributeDate(self, lock, attribute_id: int, data: datetime.date) -> bool:
    """Set a date object attribute."""
    return self.dll.DataEngineSetAttributeDate(
      lock,
      attribute_id,
      data.year,
      data.month,
      data.day
    )

  def SetAttributeBool(self, lock, attribute_id: int, data: bool) -> bool:
    """Set a bool object attribute."""
    return self.dll.DataEngineSetAttributeBool(lock, attribute_id, data)

  def SetAttributeInt8s(self, lock, attribute_id: int, data: int) -> bool:
    """Set a 8 bit signed object attribute."""
    return self.dll.DataEngineSetAttributeInt8s(lock, attribute_id, data)

  def SetAttributeInt16s(self, lock, attribute_id: int, data: int) -> bool:
    """Set a 16 bit signed object attribute."""
    return self.dll.DataEngineSetAttributeInt16s(lock, attribute_id, data)

  def SetAttributeInt32s(self, lock, attribute_id: int, data: int) -> bool:
    """Set a 32 bit signed object attribute."""
    return self.dll.DataEngineSetAttributeInt32s(lock, attribute_id, data)

  def SetAttributeInt64s(self, lock, attribute_id: int, data: int) -> bool:
    """Set a 64 bit signed object attribute."""
    return self.dll.DataEngineSetAttributeInt64s(lock, attribute_id, data)

  def SetAttributeInt8u(self, lock, attribute_id: int, data: int) -> bool:
    """Set a 8 bit unsigned object attribute."""
    return self.dll.DataEngineSetAttributeInt8u(lock, attribute_id, data)

  def SetAttributeInt16u(self, lock, attribute_id: int, data: int) -> bool:
    """Set a 16 bit unsigned object attribute."""
    return self.dll.DataEngineSetAttributeInt16u(lock, attribute_id, data)

  def SetAttributeInt32u(self, lock, attribute_id: int, data: int) -> bool:
    """Set a 32 bit unsigned object attribute."""
    return self.dll.DataEngineSetAttributeInt32u(lock, attribute_id, data)

  def SetAttributeInt64u(self, lock, attribute_id: int, data: int) -> bool:
    """Set a 64 bit unsigned object attribute."""
    return self.dll.DataEngineSetAttributeInt64u(lock, attribute_id, data)

  def SetAttributeFloat32(self, lock, attribute_id: int, data: int) -> bool:
    """Set a 32 bit float object attribute."""
    return self.dll.DataEngineSetAttributeFloat32(lock, attribute_id, data)

  def SetAttributeFloat64(self, lock, attribute_id: int, data: int) -> bool:
    """Set a 64 bit float object attribute."""
    return self.dll.DataEngineSetAttributeFloat64(lock, attribute_id, data)

  def CancelObjectCommit(self, edit_handle):
    """Handles backwards compatibility by ignoring the cancel."""
    if self.version < (1, 6):
      # Do nothing, ignore the cancel in older versions.
      self.log.warning("Cannot cancel the commit of an object due to old "
                       "application version. Some changes may still be "
                       "committed.")
      return None

    if not edit_handle:
      raise ValueError('The edit handle must not be 0')

    return self.dll.DataEngineCancelObjectCommit(edit_handle)

  def GetObjectRevisionNumber(self, read_handle):
    """Get the revision number of an open object.

    Parameters
    ----------
    read_handle : lock
      Read lock on the object whose revision number should be returned.

    Returns
    -------
    int
      The object's revision number.
      This will be None if the application is too old.
    """
    if self.version < (1, 7):
      return None

    revision_number = ctypes.c_uint32(0)
    result = self.dll.DataEngineGetObjectRevisionNumber(
      read_handle, ctypes.byref(revision_number))

    if not result:
      raise CApiUnknownError(self.dll.DataEngineErrorMessage())

    return revision_number.value

  def GetObjectIdRevisionNumber(self, handle):
    """Get the revision number of an object id.

    This allows the revision number to be queried without opening the object.

    Parameters
    ----------
    handle : T_ObjectHandle
      Read lock on the object whose revision number should be returned.

    Returns
    -------
    int
      The object's revision number.
      This will be None if the application is too old.
    """
    if self.version < (1, 7):
      return None

    revision_number = ctypes.c_uint32(0)
    result = self.dll.DataEngineGetObjectIdRevisionNumber(
      handle, ctypes.byref(revision_number))

    if not result:
      raise CApiUnknownError(self.dll.DataEngineErrorMessage())

    return revision_number.value

  def ProjectPath(self, backend_index):
    """Get the project path for the specified backend.

    Parameters
    ----------
    backend_index
      The index of the backend to return the project path for.

    Returns
    -------
    str
      Project path for the specified backend. This will be empty if
      the backend has no project path (e.g. Memory-only projects).
    """
    try:
      # Pass a length of zero to get the C API to set project_path_length
      # to the required length of the project path.
      project_path_length = ctypes.c_uint32(0)
      failure = self.dll.DataEngineProjectPath(
        backend_index,
        None, # A null pointer.
        ctypes.byref(project_path_length))

      if failure:
        raise CApiUnknownError(self.dll.DataEngineErrorMessage())

      # Create an appropriately sized buffer to hold the project path.
      project_path_buffer = ctypes.create_string_buffer(
        project_path_length.value)
      failure = self.dll.DataEngineProjectPath(
        backend_index,
        project_path_buffer,
        ctypes.byref(project_path_length))

      if failure:
        raise CApiUnknownError(self.dll.DataEngineErrorMessage())

      return project_path_buffer.value.decode("utf-8")
    except AttributeError:
      raise_if_version_too_old(
        feature="Get path to maptekdb",
        current_version=self.version,
        required_version=(1, 9)
      )

  def Checkpoint(self, handle):
    """Checkpoint the changes to an object.

    This makes the changes visible to new readers of the object.

    Parameters
    ----------
    handle : T_EditHandle
      Edit handle on the object to checkpoint.

    Returns
    -------
    ctypes.c_uint32
      Integer containing the flags for the change reasons provided
      by the checkpoint operation.
    """
    if self.version < (1, 9):
      return 0

    change_reasons = ctypes.c_uint32(0)

    try:
      failure = self.dll.DataEngineCheckpoint(
        handle, ctypes.byref(change_reasons))
    except AttributeError:
      return 0

    if failure:
      raise CApiUnknownError(self.dll.DataEngineErrorMessage())

    return change_reasons.value

  def ShallowCloneObject(self, handle):
    """Perform a shallow clone of a container.

    Unlike CloneObject, this does not clone the objects inside of the container.
    Thus, the clone contains the same objects as the original container.

    Parameters
    ----------
    handle
      Handle on the container to clone.

    Returns
    -------
    handle
      The shallow clone of the container.
    """
    try:
      return self.dll.DataEngineShallowCloneObject(handle)
    except AttributeError:
      raise_if_version_too_old(
        feature="Shallow clone container",
        current_version=self.version,
        required_version=(1, 10)
      )
      # Re-raise the original exception if the above didn't raise
      # an exception. This should only happen when using a development
      # application with only part of this API version implemented.
      raise

  def NewObject(self, type_index: int) -> T_ObjectHandle:
    """Create a new object of the type with the given index.

    Raises
    ------
    CApiUnknownError
      If the object could not be created.
    """
    raise_if_version_too_old("create object", self.version, (1, 12))

    handle = self.dll.DataEngineNewObject(type_index)

    if not handle:
      raise CApiUnknownError(self.dll.DataEngineErrorMessage())

    return handle

  def GetContainerContents(
    self,
    lock,
    should_include_name: Callable[[str], bool] = lambda _: True
  ) -> Sequence[tuple[str, T_ObjectHandle]]:
    """Query the contents of the container open with `lock`.

    Parameters
    ----------
    lock
      Lock on the container to read the contents of.
    should_include_name
      Function which returns True if the given name should be included in the
      output.
      This is a function which always return True by default.

    Returns
    -------
    Sequence
      A sequence containing tuples where the first element is the name and the
      second element is the object handle for each object in the container
      where `should_include_name` returned True.
    """
    object_handles = []

    iterator = self.dll.DataEngineContainerBegin(lock)
    end = self.dll.DataEngineContainerEnd(lock)
    while iterator.value != end.value:
      buf_size = self.dll.DataEngineContainerElementName(
        lock,
        iterator,
        None,
        0)
      name_buffer = ctypes.create_string_buffer(buf_size)
      self.dll.DataEngineContainerElementName(
        lock,
        iterator,
        name_buffer,
        buf_size
      )
      name = name_buffer.value.decode("utf-8")
      if should_include_name(name):
        handle = self.dll.DataEngineContainerElementObject(lock, iterator)
        object_handles.append((name, handle))
      iterator = self.dll.DataEngineContainerNextElement(lock, iterator)
    return object_handles

  def ContainerAppend(self, lock, name: str, handle: T_ObjectHandle, force_primary_parenting: bool):
    """Append `handle` to the container open with `lock` with the given `name`.

    Parameters
    ----------
    lock
      Lock on the container to append to.
    name
      The name to give the object in the container.
    handle
      The handle on the object to append.
    force_primary_parenting
      If the appended object should be forced to have the container as a primary parent.
    """
    self.dll.DataEngineContainerAppend(
      lock,
      name.encode("utf-8"),
      handle,
      force_primary_parenting
    )

  def ContainerRemove(self, lock, name: str):
    """Remove the item with `name` from the container open with `lock`."""
    try:
      self.dll.DataEngineContainerRemove(
        lock,
        name.encode("utf-8")
      )
    except (AttributeError, ctypes.ArgumentError) as error:
      raise TypeError(
        "Invalid parameters for ContainerRemove."
      ) from error

  def ContainerRemoveObject(
    self,
    lock,
    handle: T_ObjectHandle,
    remove_all: bool
  ) -> bool:
    """Remove `handle` from the container open with `lock`.

    If `remove_all` is False, only the first occurrence of `handle` is removed.
    Otherwise, all occurrences are removed.

    Returns
    -------
    bool
      True if `handle` was removed.
      False if `handle` was not in the container.
    """
    return self.dll.DataEngineContainerRemoveObject(
      lock,
      handle,
      remove_all
    )

  def ContainerPurge(self, lock):
    """Remove all the contents from the container open with `lock`."""
    self.dll.DataEngineContainerPurge(lock)

  def ContainerElementCount(self, lock) -> int:
    """Query the count of elements in the container."""
    return self.dll.DataEngineContainerElementCount(lock)

  def ContainerFind(self, lock, name: str) -> T_ObjectHandle:
    """Find an object in the container open with `lock` with `name`.

    Returns
    -------
    T_ObjectHandle
      Object handle of the found object. This will be the null handle
      if the object is not in the container.
    """
    return self.dll.DataEngineContainerFind(
      lock,
      name.encode("utf-8")
    )
