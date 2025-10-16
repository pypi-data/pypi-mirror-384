"""The SubMessage class for the comms module.

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

from .repeating_fields import MessageWithRepeatingField


class SubMessage(MessageWithRepeatingField):
  """A logical grouping of data preserved across the communication system.

  In comparison to an inline message think of a sub-message as having a
  marker at the start to flag the start of a sub-message, where as inline
  message is the same as if the children were part of the outer message.

  A unique feature of a sub-message is support for having a repeating field
  which enables list-like behaviour. However unlike a list which records
  how many elements are in it first so the receiver knows how many to look
  for instead the receiver reads until the end of the sub-message.

  Like Message and Inline message it requires annotating instance variables
  to specify their type and thus describe what fields there are. See Message
  for more information.

  See Also
  --------
  Message : Very similar. They are sendable as well.
  InlineMessage : Provides a logical group which isn't preserved across
                  communication.
  """
