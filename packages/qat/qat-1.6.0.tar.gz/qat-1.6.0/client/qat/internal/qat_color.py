# -*- coding: utf-8 -*-
# (c) Copyright 2024, Qat’s Authors

"""
Functions related to colors
"""

import binascii

COLOR_CONSTANTS=[
    "white", "black", "red", "darkRed", "green", "darkGreen", "blue", "darkBlue",
    "cyan", "darkCyan", "magenta", "darkMagenta", "yellow", "darkYellow", "gray",
    "darkGray", "lightGray"]

def is_valid_color(color: str) -> bool:
    """
    Return True when the given string is a valid color, False otherwise

    Args:
      color: A color in HexRGB, HexARGB format or recognized color keyword.
    
    Returns:
      Return True when the given string is a valid color, False otherwise.
    """

    # HexRGB/HexARGB format starts with a # and the length is respectively 7/9
    if color.startswith('#') and 7 <= len(color) <= 9:
        try:
            binascii.unhexlify(color[1:])
            return True
        except Exception: # pylint: disable = broad-exception-caught
            return False

    return color in COLOR_CONSTANTS
