# -*- coding: utf-8 -*-
# (c) Copyright 2024, Qat’s Authors

"""
Provides the main toolbar for the ApplicationManager
"""

from collections.abc import Callable
import customtkinter as ctk

import qat
from qat.gui.image_loader import ImageLoader
from qat.gui.toolbar_items import ToolbarButton, ToolbarCombo
from qat.internal.preferences import get_preferences
from qat.internal import app_launcher


class ToolBar(ctk.CTkFrame): # pylint: disable=too-many-ancestors
    """
    Main toolbar for ApplicationManager
    """
    def __init__(self, parent, open_spy_callback: Callable, msg_dlg_callback: Callable):
        super().__init__(parent, fg_color="transparent")
        self._open_spy_callback = open_spy_callback
        self._msg_dlg_callback = msg_dlg_callback
        applications = qat.list_applications()
        icons = ImageLoader()

        # Combobox
        app_list = list(applications.keys())
        self._last_app = ''
        self._combobox_value = ctk.StringVar(value='')
        def on_combo_changed(value):
            self._last_app = value
        self._combobox = ToolbarCombo(
            self,
            width=250,
            height=40,
            variable=self._combobox_value,
            values=app_list,
            command=on_combo_changed
        )
        self._combobox.grid(row=0, column=0, sticky='nswe')
        if len(app_list) > 0:
            self._combobox_value.set(app_list[0])
            self._last_app = app_list[0]

        # Start button
        self._start_button = ToolbarButton(
            self,
            icons.get('start_icon'),
            'Start'
        )
        self._start_button.configure(command = self.start_application)
        self._start_button.grid(column=1, row=0, padx=0, pady=0, sticky='w')

        # Attach button
        self._attach_button = ToolbarButton(self, icons.get('attach_icon'), 'Attach')
        self._attach_button.configure(command = self.attach_to_application)
        self._attach_button.grid(column=2, row=0, padx=0, pady=0, sticky='w')

        # Add button
        self._add_button = ToolbarButton(self, icons.get('add_icon'), 'Add')
        self._add_button.grid(column=3, row=0, padx=0, pady=0, sticky='w')

        # Delete button
        self._delete_button = ToolbarButton(
            self,
            icons.get('delete_icon'),
            'Delete'
        )
        self._delete_button.configure(command = self.delete_application)
        self._delete_button.grid(column=4, row=0, padx=0, pady=0, sticky='w')

        # Theme selector
        self._them_value = ctk.StringVar(value='')
        theme_button = ToolbarCombo(
            self,
            height=36,
            values=["System theme", "Light theme", "Dark theme"],
            variable=self._them_value,
            command=self.set_theme
        )
        # Align to the right
        self.grid_columnconfigure(5, weight=1)
        theme_button.grid(column=5, row=0, padx=0, pady=0, sticky='e')

        # Init theme from preferences
        with get_preferences(True) as preferences:
            try:
                theme = preferences.gui.theme
            except AttributeError:
                theme = ''
            theme = theme.capitalize()
            if theme not in ['System', 'Light', 'Dark']:
                theme = 'System'
        self._them_value.set(theme + ' theme')
        ctk.set_appearance_mode(theme.lower())


    def set_theme(self, name: str):
        """
        Change the current theme of the GUI.
        """
        for theme in ['System', 'Light', 'Dark']:
            if name.find(theme) >= 0:
                self._them_value.set(name)
                ctk.set_appearance_mode(theme.lower())
                with get_preferences(False) as preferences:
                    preferences.gui.theme = theme

                break


    def register_app_changed(self, callback: Callable[[str], None]):
        """
        Register the given callback to listen to application selection.
        """
        self._combobox_value.trace_add('write', lambda *_: callback(self._combobox_value.get()))
        # Call the callback to initialize the current value
        callback(self._combobox_value.get())


    def register_new_app(self, callback: Callable[[str], None]):
        """
        Register the given callback to listen to application creation.
        """
        def new_app(cb):
            self._combobox_value.set('')
            self._combobox.configure(state="disabled")
            self._start_button.configure(state="disabled")
            self._attach_button.configure(state="disabled")
            self._add_button.configure(state="disabled")
            self._delete_button.configure(state="disabled")
            if cb is not None:
                cb()
        self._add_button.configure(command = lambda: new_app(callback))


    def select_app(self, app_name: str, editing: bool):
        """
        Change the current application.
        """
        if editing:
            self._combobox.configure(state="disabled")
            self._start_button.configure(state="disabled")
            self._attach_button.configure(state="disabled")
            self._add_button.configure(state="disabled")
            self._delete_button.configure(state="disabled")
            return

        if len(app_name) == 0:
            app_name = self._last_app
        else:
            self._last_app = app_name

        self._refresh_app_list()
        self._combobox_value.set(app_name)
        self._combobox.configure(state="normal")
        self._start_button.configure(state="normal")
        self._attach_button.configure(state="normal")
        self._add_button.configure(state="normal")
        self._delete_button.configure(state="normal")


    def _refresh_app_list(self):
        """
        Retrieve current app list from API and update the combobox accordingly
        """
        applications = qat.list_applications()
        app_list = list(applications.keys())
        self._combobox.configure(values=app_list)
        if self._last_app in app_list:
            self._combobox_value.set(self._last_app)
        elif len(app_list) > 0:
            self._combobox_value.set(app_list[0])
        else:
            self._combobox_value.set('')


    def delete_application(self):
        """
        Remove current application from both configurations (local and global)
        """
        current_app = self._combobox_value.get()
        if len(current_app) == 0:
            print('No application selected, cannot delete it')
            return
        msg = f"Remove '{current_app}' from the application list?"

        if self._msg_dlg_callback(msg):
            qat.unregister_application(current_app, False)
            qat.unregister_application(current_app, True)
            self._refresh_app_list()


    def start_application(self):
        """
        Start current application and show Spy window
        """
        self._open_spy_callback(self._combobox_value.get(), False)


    def attach_to_application(self):
        """
        Attach to current application and show Spy window
        """
        try:
            pid = app_launcher.get_pid_from_name(self._last_app, 100)
            if pid > 0:
                self._open_spy_callback(self._combobox_value.get(), True)
        except ProcessLookupError:
            self._msg_dlg_callback(f'Application "{self._last_app}" is not running', False)
