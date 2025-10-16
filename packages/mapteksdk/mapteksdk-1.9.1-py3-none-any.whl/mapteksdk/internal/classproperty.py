###############################################################################
#
# (C) Copyright 2022, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
"""A decorator for adding read-only properties to classes.

This is equivalent to (and more robust than) using both the @classmethod and
@property decorators on the function.

Warnings
--------
Vendors and clients should not develop scripts or applications against
this package. The contents may change at any time without warning.

Notes
-----
In Python 3.8 to 3.11, it was possible to use both the @classmethod
and @property decorator on a function. Because chaining decorators was
removed in Python 3.11, it is preferable to use this decorator instead
of chaining decorators.

See https://github.com/python/cpython/issues/89519 for more information
on the removal of decorator chaining.
"""
class ClassProperty:
  """A decorator which converts a function into a class property.

  This creates a read-only property on the class.

  Examples
  --------
  Basic usage to create a property on a class.

  >>> class Example:
  ...     @ClassProperty
  ...     def hello_world(cls):
  ...         return "hello world!"
  >>> print(Example.hello_world)
  hello world!

  Raising a deprecation warning for an enum member due to changing the casing
  of a member.

  >>> import enum
  >>> import warnings
  >>> class ExampleEnum(enum.Enum):
  ...     APPLE = 1
  ...     BANANA = 2
  ...     @ClassProperty
  ...     def apple(cls):
  ...         warnings.warn(
  ...             "ExampleEnum.apple is deprecated. "
  ...             "Use ExampleEnum.APPLE instead",
  ...             DeprecationWarning)
  ...         return cls.APPLE

  """
  def __init__(self, value):
    self.value = value

  def __get__(self, obj, owner):
    return self.value(owner)
