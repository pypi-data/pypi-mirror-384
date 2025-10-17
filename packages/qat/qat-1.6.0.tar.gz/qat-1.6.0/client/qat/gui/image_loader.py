# -*- coding: utf-8 -*-
# (c) Copyright 2024, Qat’s Authors

"""
Factory and cache for images
"""

import os

from pathlib import Path
from PIL import Image

import customtkinter as ctk


class ImageLoader(): # pylint: disable=too-few-public-methods
    """
    Class loading and holding all required icons
    """
    def __init__(self):
        self.image_dir = Path(os.path.dirname(
            __file__)).resolve().absolute() / 'images'
        self._images = {}


    def get(self, file_name: str, size=(32, 32)) -> ctk.CTkImage :
        """
        Return an image corresponding to the given file name.
        Loads the image from disk if necessary. 
        """
        if len(Path(file_name).suffix) == 0:
            file_name += '.png'
        if file_name in self._images:
            return self._images[file_name]

        image = Image.open(self.image_dir / file_name)
        ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=size)
        self._images[file_name] = ctk_image
        return ctk_image
