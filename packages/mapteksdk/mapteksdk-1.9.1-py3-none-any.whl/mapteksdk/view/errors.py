"""Errors thrown by the view subpackage."""
###############################################################################
#
# (C) Copyright 2024, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

class ViewNoLongerExists(RuntimeError):
  """Exception for when a view is expected but it no longer exists.

  The most common occurrence for this exception is when the view has been
  closed.
  """
