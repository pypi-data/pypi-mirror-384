"""Errors raised by internal C API classes.

Warnings
--------
Vendors and clients should not develop scripts or applications against
this module. The contents may change at any time without warning.
"""

class DllDirectoryClosedError(Exception):
  """Exception raised when a DLL directory has been closed."""
