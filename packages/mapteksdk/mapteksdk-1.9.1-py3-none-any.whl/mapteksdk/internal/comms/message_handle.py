"""High level class for handling message handles.

Warnings
--------
Vendors and clients should not develop scripts or applications against
this package. The contents may change at any time without warning.
"""
###############################################################################
#
# (C) Copyright 2024, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

from contextlib import AbstractContextManager
import logging
import typing

from .errors import (
  FailedToCreateMessageError,
  MessageDeletedError,
  ResponseNotSentError,
)
from .message_handle_protocols import (
  OutgoingMessageHandle,
  OutgoingRequestHandle,
  IncomingMessageHandle,
  IncomingRequestHandle,
)

if typing.TYPE_CHECKING:
  from ...capi import McpApi
  from ...capi.types import T_MessageHandle
  from .default_communications_manager import DefaultCommunicationsManager

  T = typing.TypeVar("T")


LOGGER = logging.getLogger('mapteksdk.internal.comms')


class _BaseMessageHandle(AbstractContextManager):
  """Base class for message handles.

  This handles freeing the raw message handle.

  Parameters
  ----------
  raw_handle
    The raw handle read from the C API.
  manager
    The manager to use to insert / extract from messages.
  """
  def __init__(
    self,
    raw_handle: T_MessageHandle,
    manager: DefaultCommunicationsManager
  ) -> None:
    self.__handle: T_MessageHandle | None = raw_handle
    self.__manager = manager

  def __enter__(self) -> typing.Self:
    return self

  def __exit__(
    self,
    exc_type: type[BaseException] | None,
    exc_value: BaseException | None,
    traceback
  ) -> bool | None:
    if self.__handle is not None:
      self._mcp.FreeMessage(self.__handle)
      self.__handle = None

  @property
  def _handle(self) -> T_MessageHandle:
    """The raw managed by this object."""
    if self.__handle is None:
      raise MessageDeletedError()
    return self.__handle

  @property
  def _manager(self) -> "DefaultCommunicationsManager":
    """The manager to use to insert / extract from messages."""
    return self.__manager

  @property
  def _mcp(self) -> McpApi:
    """The MCP DLL which can use the handle."""
    return self.__manager.mcp

  def _flag_freed(self):
    """Allow subclasses to flag the handle as freed.

    This will cause the message to not be freed during __exit__(). Subclasses
    can use this if they call a C API function which implicitly frees the
    message to prevent a double free.
    """
    self.__handle = None


class MessageHandle(_BaseMessageHandle, OutgoingMessageHandle):
  """Concrete implementation of a message handle which can be sent.

  Parameters
  ----------
  message_name
    The name of the message to send.
  destination
    The destination to send the message to.
  mcp
    MCP DLL to use to create and send the message.
  manager
    Manager to use to insert values into the message.
  """
  def __init__(
    self,
    message_name: str,
    destination: str,
    manager: DefaultCommunicationsManager
  ) -> None:
    self.__manager = manager
    raw_handle: T_MessageHandle = manager.mcp.NewMessage(
      destination.encode('utf-8'),
      message_name.encode('utf-8'),
      False # This is a Message and not a request.
    )
    if not raw_handle.value:
      raise FailedToCreateMessageError(
        "Failed to create the Message. The script may not be connected to the "
        "application or the application may not support messages."
      )
    super().__init__(raw_handle, manager)


  def insert(self, value, data_type=None):
    actual_data_type = data_type or type(value)
    self.__manager.insert(self._handle, actual_data_type, value)

  def send(self):
    self._mcp.Send(self._handle)
    self._flag_freed()


class ReceivedMessageHandle(_BaseMessageHandle, IncomingMessageHandle):
  """Concrete implementation of receiving a message sent with MessageHandle.

  This allows for extracting from the message. As a message requires no
  response, this provides no mechanism to send one.
  """
  def extract(self, data_type: type[T]) -> T:
    return self._manager.extract(self._handle, data_type)


class ReceivedResponseHandle(IncomingMessageHandle):
  """Handle to a response received for a request.

  These objects should not be created directly. They are created by the
  `RequestHandle.send()` function.
  This is disposed when the request this is a response for is disposed
  and thus this does not require its own context manager.
  """
  def __init__(
    self,
    raw_handle: T_MessageHandle,
    manager: DefaultCommunicationsManager
  ) -> None:
    if not raw_handle.value:
      raise FailedToCreateMessageError(
        "Failed to receive the response to a request."
      )
    self.__handle: T_MessageHandle | None = raw_handle
    self._manager = manager

  def extract(self, data_type: type[T]) -> T:
    return self._manager.extract(self._handle, data_type)

  def free(self):
    """Free the response handle.

    It is not necessary to call this directly.
    This is called automatically when the with block for the request this
    is a response for is exited.
    """
    if self.__handle is None:
      return
    self._manager.mcp.FreeMessage(self._handle)
    self.__handle = None

  @property
  def _handle(self) -> T_MessageHandle:
    if self.__handle is None:
      raise MessageDeletedError("operation")
    return self.__handle


class RequestHandle(_BaseMessageHandle, OutgoingRequestHandle):
  """Concrete implementation of a message which requires a response.

  Parameters
  ----------
  message_name
    The name of the message to send.
  destination
    The destination to send the message to.
  mcp
    MCP DLL to use to create and send the message.
  manager
    Manager to use to insert values into the message.
  """
  def __init__(
    self,
    message_name: str,
    destination: str,
    manager: DefaultCommunicationsManager
  ) -> None:
    raw_handle: T_MessageHandle = manager.mcp.NewMessage(
      destination.encode('utf-8'),
      message_name.encode('utf-8'),
      True # This is a request.
    )
    if not raw_handle.value:
      raise FailedToCreateMessageError(
        "Failed to create the Message. The script may not be connected to the "
        "application or the application may not support messages."
      )
    super().__init__(raw_handle, manager)
    self.__response: ReceivedResponseHandle | None = None
    self.__message_name = message_name
    self.__destination = destination

  def insert(self, value, data_type=None):
    actual_data_type = data_type or type(value)
    self._manager.insert(self._handle, actual_data_type, value)

  def send(self) -> ReceivedResponseHandle:
    response_handle: T_MessageHandle = self._mcp.SendAndGetResponseBlocking(
      self._handle)
    self._flag_freed()
    self.__response = ReceivedResponseHandle(
      response_handle,
      self._manager
    )
    LOGGER.info(
      'Received response back for %s from %s',
      self.__message_name,
      self.__destination
    )
    return self.__response

  def __exit__(
    self,
    exc_type: type[BaseException] | None,
    exc_value: BaseException | None,
    traceback
  ) -> bool | None:
    super().__exit__(exc_type, exc_value, traceback)
    if self.__response is not None:
      self.__response.free()


class ReceivedRequestHandle(_BaseMessageHandle, IncomingRequestHandle):
  """Concrete implementation for receiving a request.

  This enables for creating a response handle to send the response.
  """
  def __init__(
    self,
    raw_handle: T_MessageHandle,
    manager: DefaultCommunicationsManager
  ) -> None:
    super().__init__(raw_handle, manager)
    self.__response: ResponseHandle | None = None
    self.__failed_to_create_response = False

  def extract(self, data_type: type[T]) -> T:
    return self._manager.extract(self._handle, data_type)

  def response_handle(self) -> ResponseHandle:
    if self.__response is None:
      try:
        self.__response = ResponseHandle(self)
      except:
        self.__failed_to_create_response = True
        raise
    return self.__response

  def __exit__(
    self,
    exc_type: type[BaseException] | None,
    exc_value: BaseException | None,
    traceback
  ) -> bool | None:
    # If the response to a request is not sent then the requesting thread
    # will wait forever for the response to arrive. To avoid this, if the
    # response is not sent this class will attempt to send the response.
    # Sending just an end of message token should make the requesting thread
    # error out which is preferable to an infinite loop.
    response_not_sent = False
    try:
      if self.__response is None:
        # If this class already failed to create the response, trying again
        # is unlikely to work.
        if not self.__failed_to_create_response:
          response = self.response_handle()
          response.send()
          response_not_sent = True
      elif not self.__response.has_been_sent:
        self.__response.send()
        response_not_sent = True
    finally:
      # Always free the request and response handles to avoid a memory
      # leak.
      super().__exit__(exc_type, exc_value, traceback)
      if self.__response is not None:
        self.__response.free()
        self.__response = None
    if response_not_sent and exc_value is None:
      raise ResponseNotSentError(
        "The response to the request was not sent."
      )


class ResponseHandle(OutgoingMessageHandle):
  """The response to a received request.

  This allows for inserting data into the response and sending it.
  """
  def __init__(self, request: ReceivedRequestHandle) -> None:
    self._manager = request._manager
    self.__handle: T_MessageHandle | None = self._manager.mcp.BeginReply(
      request._handle)
    self.__has_been_sent = False
    if not self.__handle:
      raise FailedToCreateMessageError(
        "Failed to create reply to request."
      )

  @property
  def _handle(self) -> T_MessageHandle:
    if self.__handle is None:
      raise MessageDeletedError("operation")
    return self.__handle

  def insert(self, value, data_type=None):
    actual_data_type = data_type or type(value)
    self._manager.insert(self._handle, actual_data_type, value)

  def send(self) -> IncomingMessageHandle | None:
    # Set has been sent to True before sending. If send raises an exception,
    # then the request shouldn't try to resend the response
    self.__has_been_sent = True
    self._manager.mcp.Send(self._handle)
    # If Send completes successfully, it will free the message.
    self.__handle = None

  def free(self):
    """Free the message.

    This is called by the ReceivedRequestHandle which created this object,
    so this does not need to be called directly.
    """
    if self.__handle is None:
      return
    self._manager.mcp.FreeMessage(self._handle)
    self.__handle = None

  @property
  def has_been_sent(self):
    """If this response has been sent."""
    return self.__has_been_sent
