"""The InlineMessage class for the comms module.

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

from .base_message import BaseMessage


class InlineMessage(BaseMessage):
  """A base class for types that are used within a Message.

  The inline nature is referring to the fact that the fields will be added
  to the message one after another without being contained within a group.

  For example consider the following types:

  >>>   class Person(InlineMessage):
  >>>     name: str
  >>>     email: str
  >>>
  >>>   class Employee(Message):
  >>>     employee: Person
  >>>     manager: Person
  >>>
  >>>   class EmployeeAlt(Message):
  >>>     employee_name: str
  >>>     employee_email: str
  >>>     manager_name: str
  >>>     manager_email: str

  Employee and EmployeeAlt are equivalent, they both send and receive the
  same messages so you could send a message with one type and receive it
  with the other.

  Type hinting a property as InlineMessage (i.e. Not a subclass of
  InlineMessage) will allow for any InlineMessage to be placed in the message
  at that location. This is useful for where other metadata in the message
  determines what appears later in the message.
  """
