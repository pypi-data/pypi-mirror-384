# -*- coding: utf-8 -*-
# (c) Copyright 2023, Qat’s Authors

"""
Functions related to keyboard
"""

from qat.internal.application_context import ApplicationContext
from qat.internal import find_object


def type_in(
        app_context: ApplicationContext,
        definition: dict,
        text: str):
    """
    Type the given text in the given object.
    """
    definition = find_object.object_to_definition(definition)

    command = {}
    command['command'] = 'keyboard'
    command['object'] = definition
    command['attribute'] = 'type'
    command['args'] = text

    result = app_context.send_command(command)

    if 'warning' in result:
        raise RuntimeWarning(result['warning'])


def shortcut(
        app_context: ApplicationContext,
        definition: dict,
        key_combination: str):
    """
    Trigger the given shortcut on the given object.
    """

    definition = find_object.object_to_definition(definition)

    command = {}
    command['command'] = 'keyboard'
    command['object'] = definition
    command['attribute'] = 'shortcut'
    command['args'] = key_combination

    app_context.send_command(command)


def press_key(
        app_context: ApplicationContext,
        definition: dict,
        key: str):
    """
    Press the given key on the given object.
    """
    definition = find_object.object_to_definition(definition)

    command = {}
    command['command'] = 'keyboard'
    command['object'] = definition
    command['attribute'] = 'press'
    command['args'] = key

    app_context.send_command(command)


def release_key(
        app_context: ApplicationContext,
        definition: dict,
        key: str):
    """
    Release the given key on the given object.
    """
    definition = find_object.object_to_definition(definition)

    command = {}
    command['command'] = 'keyboard'
    command['object'] = definition
    command['attribute'] = 'release'
    command['args'] = key

    app_context.send_command(command)
