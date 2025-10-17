# -*- coding: utf-8 -*-
# (c) Copyright 2024, Qat’s Authors

"""
Provides the editor area for the ApplicationManager
"""

from collections.abc import Callable
from pathlib import Path
import customtkinter as ctk
from customtkinter import filedialog

import qat
from qat import app_launcher

# pylint: disable=too-many-ancestors
# pylint: disable=too-many-instance-attributes
class EditorArea(ctk.CTkFrame):
    """
    Editor area for ApplicationManager
    """
    def __init__(self, parent, msg_dlg_callback: Callable):
        super().__init__(parent)
        self._app_modified_cb = None
        self._current_app_name = ''
        self._current_app_def = None
        self._msg_dlg_callback = msg_dlg_callback
        self._disable_cb = False

        # Labels
        name_label = ctk.CTkLabel(self, text="Name:")
        name_label.grid(row=0, column=0, sticky='w', padx = 10)
        path_label = ctk.CTkLabel(self, text="Path:")
        path_label.grid(row=1, column=0, sticky='w', padx = 10)
        args_label = ctk.CTkLabel(self, text="Arguments:")
        args_label.grid(row=2, column=0, sticky='w', padx = 10)

        self.grid_rowconfigure(0, pad=10)
        self.grid_rowconfigure(1,pad=10)
        self.grid_rowconfigure(2,pad=10)
        self.grid_rowconfigure(3,pad=20)
        self.grid_rowconfigure(4,pad=20, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Text fields
        self._app_name = ctk.StringVar(value='')
        self._app_name.trace_add('write', self.edit)
        self._app_name_field = ctk.CTkEntry(
            self,
            textvariable=self._app_name
        )
        self._app_name_field.grid(row=0, column=1, sticky='ew')

        self._app_path = ctk.StringVar(value='')
        self._app_path.trace_add('write', self.edit)
        app_path_field = ctk.CTkEntry(
            self,
            textvariable=self._app_path)
        app_path_field.grid(row=1, column=1, sticky='ew')

        self._app_arg = ctk.StringVar(value='')
        self._app_arg.trace_add('write', self.edit)
        app_args_field = ctk.CTkEntry(
            self,
            textvariable=self._app_arg)
        app_args_field.grid(row=2, column=1, sticky='ew')

        # Browse button
        self._browse_button = ctk.CTkButton(
            self,
            text="Browse...",
            command=self.browse_application
        )
        self._browse_button.grid(column=2, row=1, sticky='e', padx=10)

        # Sharing checkbox
        self._shared_box_state = ctk.BooleanVar(value=False)
        self._shared_box_state.trace_add('write', self.edit)
        shared_checkbox = ctk.CTkCheckBox(
            self,
            text="Shared with all test suites",
            variable=self._shared_box_state
        )
        shared_checkbox.grid(row=3, column=1, sticky='w')

        # Save/Cancel buttons
        button_bar = ctk.CTkFrame(self, fg_color="transparent")
        button_bar.grid(row=4, column=1, sticky='es', ipady=20)

        self._cancel_btn = ctk.CTkButton(
            button_bar,
            text="Cancel",
            state='disabled',
            command=self.cancel
        )
        self._cancel_btn.grid(row=0, column=0, sticky='es', padx=20)
        button_bar.columnconfigure(0, weight=1)

        self._save_btn = ctk.CTkButton(
            button_bar,
            text="Save",
            state='disabled',
            command=self.save
        )
        self._save_btn.grid(row=0, column=1, sticky='es')


    def set_app(self, app_name: str):
        """
        Populate content for the given application
        """
        self._disable_cb = True
        self._current_app_name = app_name
        if len(app_name) == 0:
            self._current_app_def = None
            # Reset fields when we are creating a new one
            self._app_name.set('')
            self._app_path.set('')
            self._app_arg.set('')
            self._shared_box_state.set(False)
            self._cancel_btn.configure(state='normal')
            self._app_name_field.focus()
        else:
            app_list = qat.list_applications()
            self._current_app_def = app_list[app_name]
            self._app_name.set(app_name)
            self._app_path.set(self._current_app_def['path'])
            self._app_arg.set(self._current_app_def['args'])
            self._shared_box_state.set(self._current_app_def['shared'])
            self._cancel_btn.configure(state='disabled')

        self._save_btn.configure(state='disabled')
        self._disable_cb = False


    def register_app_modified(self, callback: Callable[[str, bool], None]):
        """
        Register a callback called when fields are modified or saved.
        """
        self._app_modified_cb = callback


    def edit(self, *_):
        """
        Switch to edit mode: save/cancel button will be enabled
        """
        if self._disable_cb:
            return

        is_modified = False
        if self._current_app_def is None:
            # Creating a new app: cancel button should always be available
            self._cancel_btn.configure(state='normal')
            is_modified = len(self._app_name.get()) > 0 and len(self._app_path.get()) > 0
        else:
            # Editing an existing app: detect actual changes by comparing
            # current values with original ones
            is_modified = self._app_name.get() != self._current_app_name or \
                self._app_path.get() != self._current_app_def['path'] or \
                self._app_arg.get() != self._current_app_def['args'] or \
                self._shared_box_state.get() != self._current_app_def['shared']
            self._cancel_btn.configure(state='normal' if is_modified else 'disabled')
        # Save button should be available only when modifications are applicable
        if is_modified and len(self._app_name.get()) > 0 and len(self._app_path.get()) > 0:
            self._save_btn.configure(state='normal')
        else:
            self._save_btn.configure(state='disabled')
        # Send notification to listener when editing an existing app
        if self._app_modified_cb is not None and len(self._current_app_name) > 0:
            self._app_modified_cb(self._current_app_name, is_modified)


    def cancel(self):
        """
        Cancel current modifications
        """
        self.set_app(self._current_app_name)
        if self._app_modified_cb is not None:
            self._app_modified_cb(self._current_app_name, False)


    def save(self):
        """
        Save current modifications
        """
        # Remove current application from all configurations
        rename = True
        if len(self._current_app_name) > 0:
            if self._current_app_name != self._app_name.get():
                msg = f"Rename '{self._current_app_name}' to '{self._app_name.get()}'?" + \
                    "\n\nClick Cancel to create a new application instead."
                rename = self._msg_dlg_callback(msg)

        if self._app_name.get() != self._current_app_name:
            applications = qat.list_applications()
            app_list = list(applications.keys())
            if self._app_name.get() in app_list:
                msg = f"'{self._app_name.get()}' already exists. Replace it?"
                if not self._msg_dlg_callback(msg):
                    return
        if rename:
            qat.unregister_application(self._current_app_name, False)
            qat.unregister_application(self._current_app_name, True)

        # Register new application
        shared = self._shared_box_state.get()
        qat.register_application(
            self._app_name.get(),
            self._app_path.get(),
            self._app_arg.get(),
            shared
        )
        if self._app_modified_cb is not None:
            self._app_modified_cb(self._app_name.get(), False)


    def browse_application(self):
        """
        Use a File selector dialog to select an application
        """
        extension = '*'
        if app_launcher.is_windows():
            extension = '*.exe;*.py'
        filename = filedialog.askopenfilename(
            initialdir="C:/",
            title="Select a File",
            filetypes=[("Applications", extension)],
            parent=self
        )

        if filename:
            self._app_path.set(filename)
            if len(self._app_name.get()) == 0:
                self._app_name.set(Path(filename).stem)
