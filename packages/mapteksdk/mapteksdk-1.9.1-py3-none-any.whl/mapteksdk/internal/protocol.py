"""The protocol class from the typing package.

:TODO: SDK-506 Remove this compatibility module.

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

import sys
import typing

if sys.version_info < (3, 8):
  class Protocol:
    ...
else:
  Protocol = typing.Protocol
