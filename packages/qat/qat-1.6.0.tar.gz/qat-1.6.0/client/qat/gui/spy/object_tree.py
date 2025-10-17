# -*- coding: utf-8 -*-
# (c) Copyright 2024, Qat’s Authors

"""
Provides the object tree view for the Spy window
"""

from collections.abc import Callable
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

import qat

# Object types to filter out from the objects tree
TYPES_TO_FILTER = [
    'RootItem',
    'Qat::QmlPlugin::ObjectPicker',
    'Qat::QWidgetPlugin::ObjectPicker',
    'Qat::WindowsNativePlugin::ObjectPicker',
    'Qat::CocoaNativePlugin::ObjectPicker' ]

class ObjectTree(ctk.CTkFrame): # pylint: disable=too-many-ancestors
    """
    Implements a tree view to display widgets.
    Based on tkinter TreeView, with custom theme.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.current_root_objects = []
        self.ids = {}
        self._selected_object = None
        self._selection_callback = None
        self._is_picking = False
        self._picker_connections = []

        self.tree = ttk.Treeview(
            self, columns='type', selectmode='browse')

        # Default column is accessed using #0
        self.tree.heading('#0', text="Object")
        self.tree.heading('type', text='Type')

        self.tree.bind('<<TreeviewOpen>>', self._item_opened)
        self.tree.bind('<<TreeviewSelect>>', self._item_selected)

        self.tree.grid(row=0, column=0, sticky='nsew')

        # Add a scrollbar
        scrollbar = ctk.CTkScrollbar(
            self,
            orientation='vertical',
            command=self.tree.yview
        )
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky='ns')

        self._populate_tree([])


    def register_selection_changed(self, callback: Callable):
        """
        Register the given callback to listen to application selection.
        """
        self._selection_callback = callback
        # Call the callback to initialize the current value
        callback(self._selected_object)


    def _populate_tree(self, root_object_list):
        """
        Populate the object tree from the given root objects
        """
        if not isinstance(root_object_list, list):
            root_object_list = [root_object_list]

        self.current_root_objects = root_object_list
        if len(root_object_list) == 0:
            root_object_list = qat.list_top_windows()

        self.tree.delete(*self.tree.get_children())

        self.ids = {}

        for root_object in root_object_list:
            root_id = self.tree.insert('', tk.END, text=str(
                root_object), values=(root_object.className,), open=False)
            self.ids[root_id] = root_object

            if len(root_object.children) > 0:
                self.tree.insert(root_id, index=0, text="loading",
                                 values=("loading",), open=False)


    def _item_opened(self, _):
        """
        Callback when an item is opened in the tree.
        Populate children of the expanded object.
        """
        try:
            self.configure(cursor='watch')
            self.update()
            selected_id = self.tree.selection()[0]
            selected_children_ids = self.tree.get_children(selected_id)
            if len(selected_children_ids) > 1:
                # Tree has already been expanded
                return
            for temp_id in selected_children_ids:
                self.tree.delete(temp_id)
            children = self.ids[selected_id].children
            for child in reversed(children):
                # Prevent the following types to show up in the objects tree
                if child['type'] in TYPES_TO_FILTER:
                    continue
                tree_id = self.tree.insert(selected_id, index=0, text=str(
                    child), values=(child['type'],), open=False)
                self.ids[tree_id] = child
                if child['children']:
                    self.tree.insert(tree_id, index=0, text="loading",
                                    values=("loading",), open=False)
        finally:
            self.configure(cursor='arrow')


    def _item_selected(self, _):
        """
        Callback when an item is selected in the tree.
        Propagate the selection to populate the property table.
        """
        if len(self.tree.selection()) > 0:
            selected_object = self.ids[self.tree.selection()[0]]
        else:
            selected_object = None
        try:
            if selected_object == self._selected_object:
                return
        except (RuntimeError, AttributeError):
            # _selected_object may have expired in cache, continue to reset selection
            pass
        self._selected_object = selected_object
        if self._selection_callback is not None:
            self._selection_callback(self._selected_object)


    def pick_item(self):
        """
        Toggle picking mode
        """
        self._is_picking = not self._is_picking
        if self._is_picking:
            self._wait_for_picker()
        else:
            try:
                for conn in self._picker_connections:
                    qat.disconnect(conn)
                self._picker_connections = []
                qat.deactivate_picker()
            except: # pylint: disable=bare-except
                print('error while deactivating picker')
        return self._is_picking


    def refresh(self):
        """
        Refresh all elements (and preserve selection if possible)
        """
        self._populate_tree(self.current_root_objects)
        if self._selection_callback is not None:
            self._selection_callback(None)


    def go_up(self):
        """
        Select the parent object in the tree
        """
        # If no item is selected choose the first item in tree
        if len(self.tree.selection()) > 0:
            selected_id = self.tree.selection()[0]
        else:
            selected_id = self.tree.get_children('')[0]

        parent = self.tree.parent(selected_id)
        if parent:
            self.tree.focus(parent)
            self.tree.selection_set(parent)
        else:
            if self._selection_callback is not None:
                self._selection_callback(None)
            selected_object = self.ids[selected_id]
            try:
                parent_object = selected_object.parent
                if parent_object.get_definition() is not None:
                    self._populate_tree(parent_object)
                else:
                    self._populate_tree([])
            except Exception: # pylint: disable=broad-exception-caught
                pass


    def _wait_for_picker(self):
        """
        Connect to the object picker to retrieve the picked object
        """
        def set_picked_object(picked_object):
            self._populate_tree(picked_object)
            first_id = self.tree.get_children('')[0]
            self.tree.focus(first_id)
            self.tree.selection_set(first_id)

        if self._is_picking:
            try:
                qat.activate_picker()
                picker_def = {
                    'objectName': 'QatObjectPicker'
                }

                pickers = qat.find_all_objects(picker_def)
                self._picker_connections = []
                for picker in pickers:
                    self._picker_connections.append(qat.connect(
                        picker, 'pickedObject', set_picked_object))
            except: # pylint: disable=bare-except
                print('error while activating picker')
