# -*- coding: utf-8 -*-
# (c) Copyright 2024, Qat’s Authors

"""
Provides the main toolbar for the ApplicationManager
"""

from collections.abc import Callable
from tktooltip import ToolTip
import customtkinter as ctk

class ToolbarButton(ctk.CTkButton): # pylint: disable=too-many-ancestors
    """
    Custom CTk button displaying an icon and providing a tooltip.
    Intended to be used in toolbars.
    """
    def __init__(self, parent, icon: ctk.CTkImage, tooltip: str = None):
        super().__init__(parent, text='', image=icon, corner_radius=0)
        # Make it square
        self.configure(width = int(self.cget('height')))
        self.configure(fg_color="transparent")
        self.configure(hover_color="#1f538d")
        if tooltip is not None:
            ToolTip(self, msg=tooltip, delay=0.5)


    def highlight(self, state: bool):
        """
        Display the border of the button
        """
        if state:
            self.configure(fg_color="#1f538d")
        else:
            self.configure(fg_color="transparent")


class ToolbarCombo(ctk.CTkFrame): # pylint: disable=too-many-ancestors
    """
    A customized CTkOptionMenu embedded into a frame to create a border.
    """
    # pylint: disable=too-many-arguments
    def __init__(
            self,
            parent,
            width = None, # Default is automatic width (adapt to content)
            height: int = 40,
            border_width: int = 2,
            variable = None,
            values: list = None,
            command: Callable = None
        ):
        super().__init__(parent, fg_color=["#cecece", "#3c3c3c"])
        self._combobox = ctk.CTkOptionMenu(
            self,
            height=height - 2 * border_width,
            hover=False,
            variable=variable,
            values=values,
            command=command
        )
        if width is not None:
            self._combobox.configure(width=width)
        self._combobox.grid(row=0, column=0, padx=border_width, pady=border_width, sticky='nswe')


    def configure(self, require_redraw: bool = False, **kwargs):
        """
        Forward configuration to underlying combobox
        """
        self._combobox.configure(require_redraw, **kwargs)


    def get_values(self):
        """
        Return the list of current values in the underlying combobox
        """
        return self._combobox.cget('values')
