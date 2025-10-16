"""Colour schemes which can be applied to objects."""
###############################################################################
#
# (C) Copyright 2024, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

import enum

class ColourScheme(enum.Enum):
  """Defines colour schemes which can be applied to objects."""
  NONE = 0
  """No colour scheme."""
  GREYSCALE = 1
  """Ranges from black to white in the RGB colour space."""
  UNIFORM_GREYSCALE = 2
  """Ranges from black to white in the CIELUV colour space."""
  HEAT = 3
  """Heat scale in the CIELUV colours space."""
  # RANDOM_TINT = 4
  # """Random tint isn't really a colour scheme."""
  CARTOGRAPHIC = 5
  """A common colour scheme found in many atlases.

  Breaks the range into intervals from 0, 200, 500, 1000, 2000,
  3000, 4000 and 4000+ metres. Data with a mean sea level of 0.0
  will be coloured correctly.
  """
  PURPLE_WHITE = 6
  """Ranges from purple to white in the CIELUV colour space."""
  YELLOW_BLUE = 7
  """Ranges from yellow to blue in the CIELUV colour space."""
  PURPLE_GREEN = 8
  """Ranges from purple to green in the CIELUV colour space."""
  SPECTRUM = 9
  """Hue spectrum in the HLS colour space."""
  LIGHT_SPECTRUM = 10
  """Hue spectrum in the CIELUV colour space."""
  BOM_SPECTRUM = 11
  """Spectrum used by the Australian Bureau of Meteorology."""
  BRIGHT_SPECTRUM = 12
  """Spectrum of bright colours.

  This ranges from Electric blue to purple to hot pink to orange
  in the CIELUV colour space.
  """
  PASTEL_SPECTRUM = 13
  """Spectrum of pastel colours.

  This ranges from pink to lilac to light blue to primrose.
  """
  CIRCULAR_SPECTRUM = 19
  """Spectrum from blue to red, and back to blue through pink and purple."""
  SYMMETRIC_BLUE_WHITE_RED = 14
  """Zero crossing blue / white / red in CIELUV space."""
  SYMMETRIC_CYAN_BLUE_WHITE_RED_YELLOW = 15
  """Zero crossing in the RGB space."""
  SYMMETRIC_LINEAR_GREY_SCALE = 16
  """Zero crossing linear black, grey and white."""
  SYMMETRIC_WAVE_GREY_SCALE = 17
  """Zero crossing wavy greyscale.

  The minimum, maximum and zero values are all coloured grey.
  Values below zero get darker, reaching almost black, before
  getting lighter close to the minimum.
  Values greater than zero get lighter, reaching almost white,
  before getting darker close to the maximum.
  """
