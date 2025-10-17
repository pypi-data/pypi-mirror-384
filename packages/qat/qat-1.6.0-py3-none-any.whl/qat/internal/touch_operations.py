# -*- coding: utf-8 -*-
# (c) Copyright 2023, Qat’s Authors

"""
Functions related to touch events
"""

from qat.internal.application_context import ApplicationContext
from qat.internal import find_object
from qat.internal import mouse_operations
from qat.test_settings import Settings


def tap(
        app_context: ApplicationContext,
        definition: dict,
        mode: str,
        x=None,
        y=None,
        modifier=mouse_operations.Modifier.NONE):
    """
    Press, release, tap or move finger on the given widget using the given parameters.
    """
    # pylint: disable=duplicate-code
    definition = find_object.object_to_definition(definition)
    find_object.wait_for_object(app_context, definition)

    args = {
        'modifier': modifier
    }
    if x is not None and y is not None:
        args['x'] = x
        args['y'] = y
    command = {}
    command['command'] = 'touch'
    command['object'] = definition
    command['attribute'] = mode
    command['args'] = args

    result = app_context.send_command(command)

    if 'warning' in result:
        raise RuntimeWarning(result['warning'])


def drag(
        app_context: ApplicationContext,
        definition: dict,
        mode: str,
        x=None,
        y=None,
        dx=0,
        dy=0,
        modifier=mouse_operations.Modifier.NONE):
    """
    Drag finger on the given widget using the given parameters.
    """
    # pylint: disable=duplicate-code
    definition = find_object.object_to_definition(definition)
    find_object.wait_for_object(app_context, definition)

    args = {
        'modifier': modifier
    }
    if x is not None and y is not None:
        args['x'] = x
        args['y'] = y
    args['dx'] = dx
    args['dy'] = dy
    command = {}
    command['command'] = 'touch'
    command['object'] = definition
    command['attribute'] = mode
    command['args'] = args

    result = app_context.send_command(command, Settings.long_operation_timeout)

    if 'warning' in result:
        raise RuntimeWarning(result['warning'])
