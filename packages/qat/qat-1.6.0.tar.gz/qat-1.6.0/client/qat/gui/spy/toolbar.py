# -*- coding: utf-8 -*-
# (c) Copyright 2024, Qat’s Authors

"""
Provides the main toolbar for the Spy window
"""

from collections.abc import Callable
import customtkinter as ctk

from qat.gui.image_loader import ImageLoader
from qat.gui.toolbar_items import ToolbarButton


class ToolBar(ctk.CTkFrame): # pylint: disable=too-many-ancestors
    """
    Main toolbar for ApplicationManager
    """
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._parent = parent
        self._icons = ImageLoader()
        self._pick_callback = None

        self.columnconfigure(3, weight=1)

        # Pick button
        self._pick_button = ToolbarButton(self, self._icons.get('spy_icon'), 'Picker')
        self._pick_button.grid(column=0, row=0, padx=0, pady=0, sticky='w')
        self._pick_button.configure(command=self._pick_event)

        # Up button
        self._up_button = ToolbarButton(self, self._icons.get('up_icon'), 'Up one level')
        self._up_button.grid(column=1, row=0, padx=0, pady=0, sticky='w')

        # Refresh button
        self._start_button = ToolbarButton(self, self._icons.get('refresh_icon'), 'Refresh')
        self._start_button.grid(column=2, row=0, padx=0, pady=0, sticky='w')

        # Help message
        help_message = ctk.CTkLabel(
            self,
            text='While picking, hold CTRL to interact with the application'
        )
        help_message.grid(column=3, row=0, padx=0, pady=0, sticky='w')


    def register_pick(self, callback: Callable):
        """
        Register a callback for the Pick button
        """
        self._pick_callback = callback


    def _pick_event(self):
        """
        Manage both highlighting and callback
        """
        if self._pick_callback is not None:
            is_picking = self._pick_callback()
            self._pick_button.highlight(is_picking)

    def register_up(self, callback: Callable):
        """
        Register a callback for the Up button
        """
        self._up_button.configure(command=callback)


    def register_refresh(self, callback: Callable):
        """
        Register a callback for the Refresh button
        """
        self._start_button.configure(command=callback)
