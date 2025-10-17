# -*- coding: utf-8 -*-
# (c) Copyright 2023, Qat’s Authors

"""
Functions related to object identification
"""

from copy import deepcopy
import time

from qat.test_settings import Settings
from qat.internal.application_context import ApplicationContext
from qat.internal.qt_object import QtObject


def object_to_definition(object_or_def, accessible_only = False) -> dict:
    """
    Return the definition dictionary of the given object.
    If accessible_only is True, recursively append 'visible': True 
    and 'enabled': True to definition.
    """
    if isinstance(object_or_def, QtObject):
        definition = object_or_def.get_definition()
    elif isinstance(object_or_def, str):
        # Single string is interpreted as an objectName
        definition = {'objectName': object_or_def}
    else:
        definition = object_or_def
    for key in definition:
        if isinstance(definition[key], (QtObject,dict)):
            definition[key] = object_to_definition(definition[key], accessible_only)

    if accessible_only:
        if 'visible' not in definition:
            definition['visible'] = True
        if 'enabled' not in definition:
            definition['enabled'] = True

    return definition


def list_top_windows(
        app_context: ApplicationContext) -> list:
    """
    Return all the top windows of the application.
    """
    command = {}
    command['command'] = 'list'
    command['attribute'] = 'topWindows'

    result = app_context.send_command(command)

    objects = []
    if result['object']:
        for obj in result['object']:
            objects.append(QtObject(app_context, obj))
    return objects


def find_all_objects(
        app_context: ApplicationContext,
        definition: dict) -> list:
    """
    Return all objects matching the given definition.
    """
    definition = deepcopy(object_to_definition(definition))
    command = {}
    command['command'] = 'list'
    command['attribute'] = 'object'
    command['object'] = definition

    result = app_context.send_command(command)

    objects = []
    if result['object']:
        for obj in result['object']:
            objects.append(QtObject(app_context, obj))
    return objects


def wait_for_object_exists(
        app_context: ApplicationContext,
        definition: dict,
        timeout=Settings.wait_for_object_timeout) -> QtObject:
    """
    Wait for the given object to exist in the AUT.
    """
    start_time = round(1000 * time.time())
    definition = deepcopy(object_to_definition(definition))
    command = {}
    command['command'] = 'find'
    command['object'] = definition

    last_error = None
    while (round(1000 * time.time()) - start_time) < timeout:
        try:
            app_context.send_command(command, timeout)
            return QtObject(app_context, definition)
        except LookupError as error:
            last_error = error
            time.sleep(0.2)

    if last_error is not None:
        raise last_error
    return None


def wait_for_object(
        app_context: ApplicationContext,
        definition: dict,
        timeout=Settings.wait_for_object_timeout) -> QtObject:
    """
    Wait for the given object to be accessible (i.e visible and enabled) in the AUT.
    """
    local_definition = deepcopy(object_to_definition(definition))
    local_definition = object_to_definition(local_definition, accessible_only=True)
    return wait_for_object_exists(app_context, local_definition, timeout)


def wait_for_object_missing(
        app_context: ApplicationContext,
        definition: dict,
        timeout=Settings.wait_for_object_timeout):
    """
    Wait for the given object to be deleted from the AUT.
    """
    start_time = round(1000 * time.time())

    while (round(1000 * time.time()) - start_time) < timeout:
        try:
            result = wait_for_object_exists(app_context, definition, 100)
            if result is None or result.is_null():
                return
            time.sleep(0.2)
        except LookupError:
            return

    raise TimeoutError(f'Object "{definition}" still exists after {timeout} ms')
