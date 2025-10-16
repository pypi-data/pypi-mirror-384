"""The base classes for all objects in a Project.

This package contains DataObject and Topology.

DataObject is the absolute base class of every object which can appear in the
Project explorer.

Topology is the base class of every object which has its own geometry.

"""
###############################################################################
#
# (C) Copyright 2024, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations
import typing

from .data_object import DataObject, StaticType
from .appearance import Appearance
from .topology import Topology
from ..errors import AlreadyOpenedError
# Extent is importable from here for backwards compatibility.
from ...geometry import Extent

if typing.TYPE_CHECKING:
  # This needs to be type checking only to avoid confusing Sphinx due to
  # these classes being documented in more than one location.
  __all__ = [
    "DataObject",
    "Topology",
    "Extent",
    "Appearance",
    "AlreadyOpenedError",
    "StaticType",
  ]
