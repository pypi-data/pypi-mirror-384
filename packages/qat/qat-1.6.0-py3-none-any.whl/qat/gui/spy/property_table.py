# -*- coding: utf-8 -*-
# (c) Copyright 2024, Qat’s Authors

"""
Provides the property view for the Spy window
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

import qat

# pylint: disable=too-many-ancestors
class PropertyTable(ctk.CTkFrame):
    """
    Implements a tree-table view to display widget properties.
    Based on tkinter TreeView, with custom theme.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._selected_object = None

        self.properties_tree = ttk.Treeview(
            self, columns=("value"), selectmode='browse')

        # Define headings
        self.properties_tree.heading('#0', text='Property')
        self.properties_tree.heading('value', text='Value')
        self.properties_tree.bind('<<TreeviewOpen>>', self._property_opened)

        self.properties_tree.grid(row=0, column=0, sticky='nsew')

        # Add a scrollbar
        scrollbar = ctk.CTkScrollbar(
            self,
            orientation='vertical',
            command=self.properties_tree.yview
        )
        self.properties_tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky='ns')


    def set_selected_object(self, selected_object):
        """
        Set the selected object, usually from the object tree.
        """
        self._selected_object = selected_object
        self._populate_properties()


    def _populate_properties(self):
        """
        Populate the property table for the given object
        """
        # pylint: disable=broad-exception-caught
        try:
            self.configure(cursor='watch')
            self.properties_tree.delete(*self.properties_tree.get_children())
            if self._selected_object is None:
                return
            properties = self._sort_properties(self._selected_object)
            for prop in reversed(properties):
                try:
                    value = prop[1]
                    if isinstance(value, qat.QtObject) and value.is_null():
                        value = '<null>'
                    tree_id = self.properties_tree.insert(
                        '', index=0, text=prop[0], values=(str(value),), open=False)
                    if isinstance(value, (qat.QtObject, qat.QtCustomObject)) or prop[0] == '<methods>':
                        self.properties_tree.insert(
                            tree_id,
                            tk.END,
                            text='Loading',
                            open=False)
                except Exception:
                    pass
        finally:
            self.configure(cursor='arrow')


    def _sort_properties(self, qt_object) -> list:
        """
        Sort given properties to move most important ones to the beginning of the list
        """
        properties = qt_object.list_properties()
        properties = dict(properties)
        properties = dict(sorted(properties.items()))
        # Parent and children are in the tree
        if 'children' in properties:
            del properties['children']
        if 'parent' in properties:
            del properties['parent']
        top_properties_names = ['objectName', 'type', 'id', 'text']
        top_properties = {}
        for top_prop in top_properties_names:
            if top_prop in properties:
                top_properties[top_prop] = properties[top_prop]
                del properties[top_prop]
        if isinstance(qt_object, qat.QtObject):
            top_properties['<methods>'] = ''

        return list(top_properties.items()) + list(properties.items())


    def _property_opened(self, _):
        """
        Callback when an item is opened in the property table.
        Populate children of the expanded object.
        """
        try:
            self.configure(cursor='watch')
            self.update()
            # Object selected in the table
            selected_id = self.properties_tree.selection()
            selected_text = self.properties_tree.item(selected_id)["text"]
            if selected_text in ['<signals>', '<slots>']:
                # Internal properties
                return
            # Clear previous data
            selected_children_ids = self.properties_tree.get_children(selected_id)
            for temp_id in selected_children_ids:
                self.properties_tree.delete(temp_id)
            # Build property name using dot notation for nested properties
            parent = self.properties_tree.parent(selected_id)
            current_object = self._selected_object
            if current_object is None:
                return

            ancestors = []
            while len(parent) > 0:
                property_name = self.properties_tree.item(parent)["text"]
                ancestors.append(property_name)
                parent = self.properties_tree.parent(parent)

            for parent in reversed(ancestors):
                current_object = getattr(current_object, parent)

            # Get the property value
            property_name = self.properties_tree.item(selected_id)["text"]
            # Special case: virtual property to group methods
            if property_name == '<methods>':
                method_dict = {}
                for method_type, prototype, return_type in current_object.list_methods():
                    if method_type not in method_dict:
                        method_dict[method_type] = []
                    method_dict[method_type].append((prototype, return_type))
                for method_type in sorted(method_dict):
                    if len(method_type) == 0:
                        new_id = selected_id
                    else:
                        new_id = self.properties_tree.insert(
                            selected_id,
                            tk.END,
                            text=f'<{method_type}s>',
                            values=('',), open=False)
                    for prototype, return_type in method_dict[method_type]:
                        self.properties_tree.insert(
                            new_id,
                            tk.END,
                            text=prototype,
                            values=(return_type,), open=False)
                return

            value = getattr(current_object, property_name)
            if isinstance(value, qat.QtObject):
                self._add_object(selected_id, value)
            elif isinstance(value, qat.QtCustomObject):
                self._add_custom_object(selected_id, value)
        finally:
            self.configure(cursor='arrow')


    def _add_object(self, tree_id, qt_object: qat.QtObject):
        """
        Add the given object to the property table
        """
        properties = self._sort_properties(qt_object)
        for prop in properties:
            try:
                property_value = prop[1]
                child_id = self.properties_tree.insert(
                    tree_id,
                    tk.END,
                    text=prop[0],
                    values=(str(property_value),), open=False)
                if isinstance(property_value, qat.QtCustomObject):
                    self._add_custom_object(child_id, property_value)
                elif isinstance(property_value, qat.QtObject) or prop[0] == '<methods>':
                    self.properties_tree.insert(
                        child_id,
                        tk.END,
                        text='Loading',
                        open=False)

            except Exception: # pylint: disable=broad-exception-caught
                pass


    def _add_custom_object(self, tree_id, custom_object: qat.QtCustomObject):
        """
        Add the given custom object to the property table
        """
        for prop in custom_object:
            try:
                property_value = custom_object[prop]
                self.properties_tree.insert(
                    tree_id,
                    tk.END,
                    text=prop,
                    values=(str(property_value),),
                    open=False)
            except: # pylint: disable=bare-except
                pass
