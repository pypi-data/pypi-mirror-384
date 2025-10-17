# -*- coding: utf-8 -*-
# (c) Copyright 2024, Qat’s Authors

"""
Module providing a stack layout
"""

import customtkinter as ctk

class StackLayout(ctk.CTkFrame): # pylint: disable=too-many-ancestors
    """
    Implement a stack layout allowing to display one frame at a time.
    """
    def __init__(self, parent, **kargs):
        super().__init__(parent, **kargs)

        self._frames = {}
        self._current_frame = None


    def add(self, name: str, frame: ctk.CTkFrame):
        """
        Add a frame to the stack
        """
        self._frames[name] = frame
        if self._current_frame is not None:
            self._current_frame.grid_forget()
        self._current_frame = frame


    def show(self, name):
        """
        Display the given frame
        """
        if self._current_frame is not None:
            self._current_frame.grid_forget()

        self._current_frame = self._frames[name]
        self._current_frame.grid(row=0, column=0, sticky='nsew')
