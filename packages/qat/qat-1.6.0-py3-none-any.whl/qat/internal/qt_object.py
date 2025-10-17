# -*- coding: utf-8 -*-
# (c) Copyright 2023, Qat’s Authors

"""
Provides the QtObject class
"""

from copy import deepcopy
import json
import os

import qat.internal.application_context as app_ctxt
import qat

# Avoid cyclic imports
# pylint: disable = consider-using-from-import
import qat.internal.qt_method as qt_method
from qat.internal.qt_custom_object import QtCustomObject


class QtObject():
    """
    Local representation of a remote Qt object
    """

    def __init__(self, context: app_ctxt.ApplicationContext, definition: dict) -> None:
        """
        Store the application context and a copy of the object's definition
        """
        self.__dict__['_definition'] = deepcopy(definition)
        self.__dict__['_app_context'] = context


    def __del__(self):
        if '_definition' in self.__dict__ and self.__dict__['_definition'] is not None:
            if '_temp_image_file' in self.__dict__['_definition']:
                tmp_file = self.__dict__['_definition']['_temp_image_file']
                if os.path.exists(tmp_file):
                    try:
                        os.remove(tmp_file)
                    except OSError as error:
                        print("Could not delete temp file: " + str(error))


    def get_definition(self) -> dict:
        """
        Return the definition of this object as a dictionary of properties
        """
        return self.__dict__['_definition']


    def is_null(self) -> bool:
        """
        Return whether this object is a NULL pointer or not
        """
        if self.__dict__['_definition'] is None:
            return True
        if 'cache_uid' not in self.__dict__['_definition']:
            return False
        return int(self.__dict__['_definition']['cache_uid']) == 0


    def property(self, name: str):
        """
        Get the remote attribute of this object.
        """
        return getattr(self, name)


    def _get_app_context(self) -> app_ctxt.ApplicationContext:
        context = self.__dict__['_app_context']
        if context is None or not context.is_running():
            # Context was lost. Use current context
            context = qat.current_application_context()
            if context is None or not context.is_running():
                return None
            self.__dict__['_app_context'] = qat.current_application_context()
            definition = self.__dict__['_definition']
            if definition is not None and 'cache_uid' in definition:
                definition['cache_uid'] = self.cache_uid
        return self.__dict__['_app_context']


    def __str__(self):
        """
        Custom string representation of a QtObject: objectName, id or <unnamed>
        """
        definition = self.__dict__['_definition']
        if 'objectName' in definition:
            return definition['objectName']
        if 'id' in definition:
            return definition['id']
        text = ''
        try:
            text = self.objectName
        except AttributeError:
            try:
                text = self.id
            except AttributeError:
                pass
        if len(text) == 0:
            text = '<unnamed>'
        return str(text)


    def list_properties(self) -> list:
        """
        Return the list of all available properties for this object.
        """
        command = {}
        command['command'] = 'list'
        command['object'] = self.__dict__['_definition']
        command['attribute'] = "properties"

        try:
            result = self._get_app_context().send_command(command)
        except LookupError as error:
            raise AttributeError(str(error)) from error


        property_list = []
        object_tag = "<object>:"
        if 'properties' in result:
            for name in result['properties']:
                value = result['properties'][name]
                if isinstance(value, str) and value.startswith(object_tag):
                    object_def = json.loads(value[len(object_tag):])
                    value = QtObject(self.__dict__['_app_context'], object_def)
                    if value.is_null():
                        value = "<null>"
                elif isinstance(value, dict):
                    value = QtCustomObject(value)
                property_list.append((name, value))
            return property_list

        raise RuntimeError("Unknown error while listing properties")


    def list_methods(self) -> list:
        """
        Return the list of all available methods for this object.
        """
        command = {}
        command['command'] = 'list'
        command['object'] = self.__dict__['_definition']
        command['attribute'] = "methods"

        try:
            result = self._get_app_context().send_command(command)
        except LookupError as error:
            raise AttributeError(str(error)) from error


        method_list = []
        if 'methods' in result:
            for method in result['methods']:
                method_list.append((method['type'], method['name'], method['returnType']))
            return method_list

        raise RuntimeError("Unknown error while listing methods")


    def __getattr__(self, name: str):
        """
        Get the remote attribute of this object.
        """
        command = {}
        command['command'] = 'get'
        command['object'] = self.__dict__['_definition']
        command['attribute'] = name

        try:
            result = self._get_app_context().send_command(command)
        except RuntimeError as error:
            raise AttributeError(str(error)) from error

        # Objects such as ImageWrapper can be re-generated dynamically so
        # update their cache UID automatically.
        if 'cache_uid' in self.__dict__['_definition'] and 'cache_uid' in result:
            self.__dict__['_definition']['cache_uid'] = result['cache_uid']

        if 'value' in result:
            # Parse attribute value
            json_value = result['value']
            if isinstance(json_value, dict):
                return QtCustomObject(json_value)
            return json_value
        if 'object' in result:
            # Parse object definition
            return QtObject(self.__dict__['_app_context'], result['object'])
        if 'children' in result:
            # Build children
            children = []
            for child in result['children']:
                children.append(QtObject(self.__dict__['_app_context'], child))
            return children
        if 'found' in result and result['found']:
            # Attribute is a method
            return qt_method.QtMethod(self, name)

        raise AttributeError(f"Unknown error while getting attribute '{name}'")


    def __contains__(self, item):
        return self.__dict__['_definition'].__contains__(item)


    def __getitem__(self, key):
        definition = self.__dict__['_definition']
        if key in definition:
            return definition.__getitem__(key)
        return self.__getattr__(key)


    def __setattr__(self, name: str, value):
        """
        Set the remote attribute of this object.
        """

        if isinstance(value, QtCustomObject):
            value = value.get_attribute_dict()

        command = {}
        command['command'] = 'set'
        command['object'] = self.__dict__['_definition']
        command['attribute'] = name
        command['args'] = value

        try:
            self._get_app_context().send_command(command)
        except RuntimeError as error:
            raise AttributeError(str(error)) from error


    def __eq__(self, other):
        if other is None:
            return self.is_null()
        if isinstance(other, dict):
            other = qat.wait_for_object_exists(other)

        return self.cache_uid == other.cache_uid
