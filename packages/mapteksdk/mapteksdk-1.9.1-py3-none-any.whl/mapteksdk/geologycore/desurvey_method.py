"""Desurvey methods available for drillhole databases."""
###############################################################################
#
# (C) Copyright 2022, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

import enum

class DesurveyMethod(enum.Enum):
  """Desurvey methods for drillhole databases."""
  NONE = 0
  """Placeholder indicating no desurvey information."""

  SEGMENT_FOLLOWING = 1
  """The segment following desurvey algorithm.

  Each drillhole interval following a survey measurement is positioned using
  that measurement.
  """

  SEGMENT_PRECEDING = 2
  """The segment preceding desurvey algorithm.

  Each drillhole interval preceding a survey measurement is positioned using
  that measurement.
  """

  TANGENT = 3
  """The tangent desurvey algorithm.

  Each drillhole interval about a survey measurement is positioned using
  that measurement as a tangent.
  """

  TANGENT_WITH_LENGTH = 4
  """The tangent with length desurvey algorithm.

  Interpolate additional survey information at a given distance down the
  hole. Each drillhole interval about a survey measurement is positioned
  using that measurement as a tangent.
  """

  # :TODO: SDK-935 As of 2023-06-27 this is not supported by the viewer.
  # Restore this option when it is supported.
  # BALANCED_TANGENT = 5
  # """The balanced tangent desurvey algorithm.

  # Each drillhole interval about a survey measurement is positioned using a
  # spherical arc with a minimum curvature or a maximum radius of curvature
  # between stations.

  # Notes
  # -----
  # Requires project.api_version >= (1, 9) to read if a drillhole database
  # uses this desurvey method.
  # Requires project.api_version >= (1, 10) to set a drillhole database to use
  # this desurvey method,
  # """

  # :TODO: SDK-935 As of 2023-06-27 this is not supported by the viewer.
  # Restore this option when it is supported.
  # MINIMUM_CURVATURE = 6
  # """The minimum curvature desurvey algorithm.

  # Each drillhole interval about a survey measurement is positioned using a
  # spherical arc with a minimum curvature or a maximum radius of curvature
  # between stations, as with the "Balanced Tangent" method, but with a
  # "Ratio Factor" to take into account the 'dogleg' severity.
  # Optionally, the tangent_length property may be set to interpolate additional
  # survey measurements at the given distance down the hole.

  # Notes
  # -----
  # Requires project.api_version >= (1, 9) to read if a drillhole database
  # uses this desurvey method.
  # Requires project.api_version >= (1, 10) to set a drillhole database to use
  # this desurvey method,
  # """

  UNDEFINED = 254
  """The desurvey method is not defined.

  This is often the desurvey method for drillhole databases created
  prior to Vulcan GeologyCore 2022.1 (Prior to this version, the desurvey
  method was stored on the Drillhole rather than the DrillholeDatabase.).
  """

  UNKNOWN = 255
  """The desurvey method is not recognised by the Python SDK."""

  @property
  def supports_length(self):
    """True if this desurvey method supports specifying the tangent length.

    This is true for TANGENT_WITH_LENGTH and MINIMUM_CURVATURE.
    """
    return self in {
      DesurveyMethod.TANGENT_WITH_LENGTH,
      # :TODO: SDK-935 Restore this when uncommenting the member.
      # DesurveyMethod.MINIMUM_CURVATURE,
    }
