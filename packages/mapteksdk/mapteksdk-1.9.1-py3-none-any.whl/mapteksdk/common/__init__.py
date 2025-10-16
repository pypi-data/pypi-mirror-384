"""Shared helpers and utilities used throughout the API."""
###############################################################################
#
# (C) Copyright 2020, Maptek Pty Ltd. All rights reserved.
#
###############################################################################

import ctypes

import numpy as np


def convert_to_rgba(colour):
  """Converts a list representing a colour into a valid
  rgba colour - a list of length 4 in the form
  [red, green, blue, alpha] with each value between 0 and
  255.

  This conversion can take three different forms:

  1. If the list contains three elements, the alpha is assumed to
     be 255 (fully visible).

  2. If the list contains a single element, the colour is treated
     as a shade of grey.

  3. The colour is already rgba - no conversion is performed.

  If none of the above cases are applicable, a ValueError is raised.

  Parameters
  ----------
  colour : array_like
    List of colours to convert. This can either be a Greyscale colour
    ([intensity]), a RGB colour [red, green, blue] or a RGBA colour
    ([red, green, blue, alpha]).

  Returns
  -------
  ndarray
    ndarray representing colour in the form [red, green, blue, alpha].

  Raises
  ------
  ValueError
    If the colour cannot be converted to a valid rgba colour.

  Notes
  -----
  A user of the SDK generally does not need to call this function
  because it is called internally by all functions which take a colour.

  Each element in a rgba array is represented as an unsigned 8 bit integer.
  If a value is assigned which is greater than 255 or less than 0, integer
  overflow will occur. The colour will be set to value % 256.

  Alpha represents the transparency of the object - an alpha of 0 indicates
  a completely transparent (and hence invisible) colour whereas an alpha
  of 255 indicates a completely opaque object.

  Examples
  --------
  Convert greyscale colour to RGBA

  >>> from mapteksdk.common import convert_to_rgba
  >>> colour = [125]
  >>> convert_to_rgba(colour)
  array([125, 125, 125, 255])

  Convert RGB colour to RGBA

  >>> from mapteksdk.common import convert_to_rgba
  >>> colour = [120, 120, 0]
  >>> convert_to_rgba(colour)
  array([120, 120, 0, 255])

  """
  if isinstance(colour, np.ndarray):
    if colour.dtype != ctypes.c_uint8:
      colour = colour.astype(ctypes.c_uint8)
  else:
    colour = np.array(colour, dtype=ctypes.c_uint8)

  if colour.shape == (1,):
    colour = np.hstack((colour, colour, colour, [255]))
  elif colour.shape == (3,):
    colour = np.hstack((colour, [255]))
  elif colour.shape != (4,):
    error_message = (f"Invalid colour: {colour}\n"
                     "Colours must be RGB, RGBA or Greyscale")
    raise ValueError(error_message)

  return colour
