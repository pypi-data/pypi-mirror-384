"""Interaction with a view in an applicable Maptek application.

The first step is opening a new view which returns a view controller for the
new view. From there you can control the view by adding/removing objects,
hiding/showing objects and querying what objects are in the view.

>>> from mapteksdk.project import Project
>>> import mapteksdk.operations as operations
>>> project = Project()
>>> view = operations.open_new_view()
>>> view.add_objects([project.find_object('/cad')])
>>> view.close()
>>> project.unload_project()
"""
###############################################################################
#
# (C) Copyright 2024, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

from .enums import (
  ManipulationMode,
  ObjectFilter,
  PredefinedView,
  SectionMode,
  SectionStepDirection,
  TransientGeometryRestrictMode,
  TransientGeometrySettings,
)
from .errors import ViewNoLongerExists
from .save_to_image import save_to_image
from .view import (
  ViewController,
  ViewWindow,
)
