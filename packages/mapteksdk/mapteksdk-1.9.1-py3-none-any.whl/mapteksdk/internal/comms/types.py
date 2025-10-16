"""Types defined for the comms package.

The types defined in this file are used to determine how integers and floats
should be serialised via the MCP. For example, given the message:

>>> class IntegerMessage(Message):
...     @classmethod
...     def message_name(cls) -> str:
...         return "IntegerMessage"
...     value: Int8u

By type hinting "value" as "Int8u" this indicates that when the message is
sent that it should be sent as an 8 bit unsigned integer. When assigning a
value to a property type hinted like this, you can assign a plain Python
integer - it is not required to cast the value to the serialisation type:

>>> message = IntegerMessage(manger)
>>> message.value = 16

The main exception to this is for properties annotated with typing.Union or
typing.Any. For such properties, the type must be determined at runtime which
means you must explicitly convert the value to the serialisation type:

>>> class AnyMessage(Message):
...     @classmethod
...     def message_name(cls) -> str:
...         return "AnyMessage"
...     value: typing.Any
>>>
>>> message = AnyMessage(manager)
>>> # This must cast the value to Int8u so that send() knows what type to
>>> # send the property as.
>>> message.value = Int8u(42)

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

import typing

from ..serialised_text import SerialisedText, ReceivedSerialisedText

if typing.TYPE_CHECKING:
  # When type checking, consider all integer types to be aliases for int and
  # all float types to be aliases of float.
  # This ensures that, for example, assigning an int to a property expecting
  # an Int8u will not be flagged as an error by the static type checker.
  #
  # At runtime, these names instead refer to distinct subtypes of int or float
  # which allows for them to be distinguished in the type hints and via calls
  # to isinstance(). This allows for messages to be sent using the correct
  # types.
  Int8u = int
  Int16u = int
  Int32u = int
  Int64u = int
  Int8s = int
  Int16s = int
  Int32s = int
  Int64s = int
  Float  = float
  Double = float
else:
  class Int8u(int):
    """An integer which should be sent as a 8 bit unsigned integer.

    Notes
    -----
    Values of this type can contain any value a normal Python int can hold.
    If the value is outside of the range of an 8 bit unsigned integer,
    integer overflow will occur when the message is sent.
    """


  class Int16u(int):
    """An integer which should be sent as a 16 bit unsigned integer.

    Notes
    -----
    Values of this type can contain any value a normal Python int can hold.
    If the value is outside of the range of a 16 bit unsigned integer,
    integer overflow will occur when the message is sent.
    """

  class Int32u(int):
    """An integer which should be sent as a 32 bit unsigned integer.

    Notes
    -----
    Values of this type can contain any value a normal Python int can hold.
    If the value is outside of the range of a 32 bit unsigned integer,
    integer overflow will occur when the message is sent.
    """


  class Int64u(int):
    """An integer which should be sent as a 64 bit unsigned integer.

    Notes
    -----
    Values of this type can contain any value a normal Python int can hold.
    If the value is outside of the range of a 64 bit unsigned integer,
    integer overflow will occur when the message is sent.
    """

  class Int8s(int):
    """An integer which should be sent as a 8 bit signed integer.

    Notes
    -----
    Values of this type can contain any value a normal Python int can hold.
    If the value is outside of the range of a 8 bit signed integer,
    integer overflow will occur when the message is sent.
    """


  class Int16s(int):
    """An integer which should be sent as a 16 bit signed integer.

    Notes
    -----
    Values of this type can contain any value a normal Python int can hold.
    If the value is outside of the range of a 16 bit signed integer,
    integer overflow will occur when the message is sent.
    """

  class Int32s(int):
    """An integer which should be sent as a 32 bit signed integer.

    Notes
    -----
    Values of this type can contain any value a normal Python int can hold.
    If the value is outside of the range of a 32 bit signed integer,
    integer overflow will occur when the message is sent.
    """


  class Int64s(int):
    """An integer which should be sent as a 64 bit signed integer.

    Notes
    -----
    Values of this type can contain any value a normal Python int can hold.
    If the value is outside of the range of a 64 bit signed integer,
    integer overflow will occur when the message is sent.
    """


  class Float(float):
    """A float which should be sent as a 32 bit float.

    This sent as an IEEE single precision floating point number.

    Notes
    -----
    Values of this type can contain any value a normal Python float can hold.
    If the value is outside of the range of a 32 bit float,
    float overflow will occur when the message is sent.
    """


  class Double(float):
    """A float which should be sent as a 64 bit float.

    This is sent as an IEEE double precision floating point number.

    Notes
    -----
    Values of this type can contain any value a normal Python float can hold.
    If the value is outside of the range of a 64 bit float,
    float overflow will occur when the message is sent.
    """


Integers: typing.TypeAlias = typing.Union[
  Int8s, Int16s, Int32s, Int64s, Int8u, Int16u, Int32u, Int64u,
]
"""Type alias for any integer type defined in this file."""

Floats: typing.TypeAlias = typing.Union[Float, Double,]
"""Type alias for any floating point type defined in this file."""

Primitives: typing.TypeAlias = typing.Union[
  Integers, Floats, bool, str, SerialisedText, ReceivedSerialisedText
]
"""Type alias for any primitive type supported in this file."""
