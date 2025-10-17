# -*- coding: utf-8 -*-
# (c) Copyright 2023, Qat’s Authors

"""
Functions related to mouse
"""

from dataclasses import dataclass

from qat.internal.application_context import ApplicationContext
from qat.test_settings import Settings
from qat.internal import find_object

# Mouse events require many arguments
# pylint: disable = too-many-arguments

@dataclass
class Button():
    """
    Mouse button constants
    """
    NONE = 'none'
    LEFT = 'left'
    RIGHT = 'right'
    MIDDLE = 'middle'


@dataclass
class Modifier():
    """
    Key modifier constants
    """
    NONE = 'none'
    ALT = 'alt'
    CTL = 'ctrl'
    SHIFT = 'shift'


def click(
        app_context: ApplicationContext,
        definition: dict,
        mode: str,
        x=None,
        y=None,
        modifier=Modifier.NONE,
        button=Button.LEFT,
        check=False):
    """
    Click, double-click or move the mouse on the given widget using the given parameters.
    """
    # pylint: disable=duplicate-code
    definition = find_object.object_to_definition(definition)
    find_object.wait_for_object(app_context, definition)

    args = {
        'button': button,
        'modifier': modifier
    }
    if x is not None and y is not None:
        args['x'] = x
        args['y'] = y
    command = {}
    command['command'] = 'mouse'
    command['object'] = definition
    command['attribute'] = mode
    command['args'] = args

    result = app_context.send_command(command)

    if check and 'warning' in result:
        raise RuntimeWarning(result['warning'])


def drag(
        app_context: ApplicationContext,
        definition: dict,
        mode: str,
        x=None,
        y=None,
        dx=0,
        dy=0,
        modifier=Modifier.NONE,
        button=Button.LEFT,
        check=False):
    """
    Drag the mouse using the given parameters.
    """
    # pylint: disable=duplicate-code
    definition = find_object.object_to_definition(definition)
    find_object.wait_for_object(app_context, definition)

    args = {
        'button': button,
        'modifier': modifier
    }
    if x is not None and y is not None:
        args['x'] = x
        args['y'] = y
    args['dx'] = dx
    args['dy'] = dy
    command = {}
    command['command'] = 'mouse'
    command['object'] = definition
    command['attribute'] = mode
    command['args'] = args

    result = app_context.send_command(command, Settings.long_operation_timeout)

    if check and 'warning' in result:
        raise RuntimeWarning(result['warning'])
