"""Concrete implementations of `Factory` and `MessageComponent`.

The `Factory` and `MessageComponent` classes defined in this package are not
expected to be used directly; rather, client packages should use the
`default_manager()` function defined in the super package to get a factory
which combines all of the factories defined in this package together.

Notes
-----
Requiring all client classes to go through default_manager() allows for the
internal architecture of this package to be changed without requiring any
changes to the clients of this package (e.g. Factories can be combined,
split or replaced as required).

Warnings
--------
All of the classes defined in this subpackage should be considered internal
implementation details, even for other subpackages within the SDK.

Adding support for new types to this package
--------------------------------------------
1: Think about whether it is actually necessary to add a new type to this
   package. If you can't think of a way to achieve what you want without
   adding support for a new type (or achieving what you need without a new
   type is too difficult), then continue onto the next step.
2: Decide whether the new type should be handled by one of the existing
   factories or by a new factory. If it fits into the theme of an existing
   factory, got to step 4.
3: Add a new file to contain the new factory and create a class which
   implements `Factory` to that class.
4: Add a new class which implements `MessageComponent` to the same file as
   the factory for your new type. There are many examples of how this can be
   done in this package.
   The names of these classes typically start with an underscore because they
   are not intended to be referenced outside of the file in which they are
   defined.
5: Add the new `MessageComponent` to the factory in the class.
6: If you added a new factory, add the new factory to `default_manager.py`.
7: The new type should now be supported by the comms package.
"""
###############################################################################
#
# (C) Copyright 2024, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
