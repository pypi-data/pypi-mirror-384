# -*- coding: utf-8 -*-
# (c) Copyright 2024, Qat’s Authors

"""
Provides the SpyWindow class as the root window
"""

import os
from pathlib import Path
from tkinter import ttk
import tkinter

import customtkinter as ctk

from qat.gui.spy.object_tree import ObjectTree
from qat.gui.spy.property_table import PropertyTable
from qat.gui.spy.toolbar import ToolBar
import qat


class SpyWindow(ctk.CTkToplevel):
    """
    Main window of Qat Spy when connected to an application
    """
    def __init__(
            self,
            *args,
            fg_color = None,
            **kwargs):
        super().__init__(*args, fg_color=fg_color, **kwargs)
        self.title('Qat Spy')
        self.geometry('1000x600')
        current_path = Path(os.path.dirname(__file__)).resolve().absolute()

        def set_icon():
            try:
                image_dir = current_path.parent / 'images'
                self.iconbitmap(image_dir / "qat_icon.ico")
            except tkinter.TclError:
                # Icons may not be supported on some platforms
                pass
        if qat.app_launcher.is_windows():
            self.after(250, set_icon)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._configure_theme()

        toolbar = ToolBar(self)
        toolbar.grid(row=0, column=0, sticky='new', padx=5, pady=5)

        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(column=0, row=1, padx=5, pady=5, sticky='nsew')
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1, uniform=1)
        main_frame.columnconfigure(1, weight=1, uniform=1)

        # Object tree
        tree = ObjectTree(main_frame)
        tree.grid(row=0, column=0, sticky='nsew')

        # Property table
        table = PropertyTable(main_frame)
        table.grid(row=0, column=1, sticky='nsew')

        # Register callbacks
        tree.register_selection_changed(table.set_selected_object)
        toolbar.register_pick(tree.pick_item)
        toolbar.register_up(tree.go_up)
        toolbar.register_refresh(tree.refresh)

        # Close the Spy when application is terminated
        qat.current_application_context().register_close_callback(self.destroy)


    def _configure_theme(self):
        """
        Customize Treeview appearance based on current theme.
        """
        theme = ctk.get_appearance_mode()
        index = 1 if theme.lower() == 'dark' else 0

        bg_color = ctk.ThemeManager.theme["CTkEntry"]["fg_color"][index]
        text_color = ctk.ThemeManager.theme["CTkLabel"]["text_color"][index]
        selected_color = ctk.ThemeManager.theme["CTkEntry"]["border_color"][index]

        treestyle = ttk.Style()
        # Configure tree content
        treestyle.theme_use('default')
        treestyle.configure(
            "Treeview",
            background=bg_color,
            foreground=text_color,
            fieldbackground=bg_color,
            borderwidth=0)
        treestyle.map('Treeview', background=[('selected', selected_color)], foreground=[('selected', text_color)])

        # Configure header
        treestyle.configure(
            "Treeview.Heading",
            background=bg_color,
            foreground=text_color)
        treestyle.map(
            'Treeview.Heading',
            background=[('selected', bg_color)],
            foreground=[('selected', selected_color)])
