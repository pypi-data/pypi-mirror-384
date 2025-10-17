# -*- coding: utf-8 -*-
# (c) Copyright 2023, Qat’s Authors

"""
Provides the QtMethod class
"""

# Avoid cyclic imports
# pylint: disable = consider-using-from-import
# pylint: disable = cyclic-import

from dataclasses import dataclass
from pathlib import Path
import json

import qat.internal.qt_object as qt_object
import qat.internal.qt_custom_object as qt_custom_object

@dataclass
class QtMethod():
    """
    Bind a remote Qt method to a local object
    """

    def __init__(self, qobject, name: str) -> None:
        """
        Constructor the current value of a Qt variable
        """
        if not isinstance(qobject, qt_object.QtObject):
            raise ValueError(
                f"Cannot create Method {name}: no valid QtObject given")
        self._object = qobject
        self._name = name

    def __call__(self, *args):
        """
        Call this method with the given arguments.
        """
        args = list(args)
        for index, item in enumerate(args):
            if isinstance(item, qt_custom_object.QtCustomObject):
                args[index] = item.get_attribute_dict()
            elif isinstance(item, qt_object.QtObject):
                args[index] = item.get_definition()
            elif isinstance(item, Path):
                args[index] = str(item)
            else:
                args[index] = item

        command = {}
        command['command'] = 'call'
        command['object'] = self._object.__dict__['_definition']
        command['attribute'] = self._name
        command['args'] = args

        result = self._object._app_context.send_command(command)

        if 'value' in result:
            value = result['value']
            if 'returnValue' in value:
                value = value['returnValue']
                if isinstance(value, dict):
                    return qt_custom_object.QtCustomObject(value)
                return value
            if 'returnObject' in value:
                value = json.loads(value)
                return qt_object.QtObject(
                    self._object.__dict__['_app_context'],
                    value['returnObject'])

        raise RuntimeError(f"Calling '{self._name}' did not return any value")
