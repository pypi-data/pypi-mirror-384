# -*- coding: utf-8 -*-
# (c) Copyright 2023, Qat’s Authors

"""
Functions related to gestures
"""

from decimal import Decimal
import decimal
import math
import time

from qat.internal.application_context import ApplicationContext
from qat.internal import find_object
from qat.internal import touch_operations
from qat.internal.global_constants import QStyleHints


def round_float_to_int(value: float) -> int:
    """
    Return the given value rounded to the nearest integer (using ROUND_HALF_UP strategy)
    """
    decimal.getcontext().rounding = decimal.ROUND_HALF_UP
    return int(round(Decimal(str(value)), 0))


def flick(
        app_context: ApplicationContext,
        definition: dict,
        dx=0,
        dy=0):
    """
    Move the given Flickable by the given horizontal and vertical distances in pixels.
    """
    definition = find_object.object_to_definition(definition)
    find_object.wait_for_object(app_context, definition)

    args = {
        'dx': dx,
        'dy': dy
    }

    command = {}
    command['command'] = 'gesture'
    command['object'] = definition
    command['attribute'] = 'flick'
    command['args'] = args

    app_context.send_command(command)


def pinch(
        app_context: ApplicationContext,
        definition: dict,
        rotation = 0.,
        translation = None,
        scale = 1.0):
    """
    Generate a pinch event (zoom, rotation, pan).
    """
    if scale <= 0:
        raise ValueError("Scale argument must be a strict positive number")

    if translation is None:
        translation = [0, 0]

    definition = find_object.object_to_definition(definition)
    widget = find_object.wait_for_object(app_context, definition)
    w = widget.width
    h = widget.height

    initial_rotation = 0
    final_rotation = rotation

    # Compute initial and final positions
    initial_position = [(w - translation[0]) / 2, (h - translation[1]) / 2]

    if initial_position[0] <= 0 or initial_position[1] <= 0:
        raise ValueError("Translation is out of widget's boundaries")

    final_position = [sum(element) for element in zip(initial_position, translation)]

    # Scale the gesture depending on the widget's size
    available_distance = min(initial_position[0], initial_position[1], w - initial_position[0], h - initial_position[1])
    if scale < 1:
        initial_scale = 0.9 * available_distance
        final_scale = scale * initial_scale
    else:
        final_scale = 0.9 * available_distance
        initial_scale = final_scale / scale

    # Decompose the gesture into smaller steps
    num_steps = 10
    rotation_step = (final_rotation - initial_rotation) / num_steps
    horizontal_step = (final_position[0] - initial_position[0]) / num_steps
    vertical_step = (final_position[1] - initial_position[1]) / num_steps
    scale_step = (final_scale - initial_scale) / num_steps

    x1 = round_float_to_int(initial_position[0] - initial_scale)
    y1 = round_float_to_int(initial_position[1])
    x2 = round_float_to_int(initial_position[0] + initial_scale)
    y2 = round_float_to_int(initial_position[1])

    try:
        # Qt needs a minimal drag distance to initiate a gesture, so
        # send the first event a bit off on the X axis. That way, the first update
        # will start the gesture at the desired position. This has no effect on the
        # gesture itself.
        # see QStyleHints::startDragDistance
        minimum_drag_distance = 10
        try:
            style_hints = find_object.wait_for_object_exists(app_context, QStyleHints)
            minimum_drag_distance = style_hints.startDragDistance
        except (LookupError, AttributeError) as exc:
            print(f'Error getting startDragDistance: {exc}. Using default value {minimum_drag_distance}.')

        touch_operations.tap(
            app_context,
            definition,
            "press",
            x = [x1 + minimum_drag_distance, x2 - minimum_drag_distance],
            y = [y1, y2])

        for i in list(range(num_steps + 1)):
            # Add a small delay to create a more realistic gesture
            time.sleep(0.02)
            center_x = initial_position[0] + i * horizontal_step
            center_y = initial_position[1] + i * vertical_step
            angle = initial_rotation + i * rotation_step
            angle = math.radians(-angle)
            length = initial_scale + i * scale_step
            x1 = round_float_to_int(center_x - length * math.cos(angle))
            y1 = round_float_to_int(center_y + length * math.sin(angle))
            x2 = round_float_to_int(center_x + length * math.cos(angle))
            y2 = round_float_to_int(center_y - length * math.sin(angle))

            touch_operations.tap(
                app_context,
                definition,
                "move",
                x = [x1, x2],
                y = [y1, y2])
    finally:
        touch_operations.tap(
            app_context,
            definition,
            "release",
            x = [x1, x2],
            y = [y1, y2])


def native_pinch(
        app_context: ApplicationContext,
        definition: dict,
        angle: float = None,
        scale: float = None,
        check: bool = False):
    """
    Generate a native pinch event (zoom and/or rotation).
    """
    definition = find_object.object_to_definition(definition)

    # Handle optional arguments
    args = {}
    if angle is not None:
        args['angle'] = angle
    if scale is not None:
        args['scale'] = scale

    command = {}
    command['command'] = 'gesture'
    command['object'] = definition
    command['attribute'] = 'pinch'
    command['args'] = args

    result = app_context.send_command(command)

    if check and 'warning' in result:
        raise RuntimeWarning(result['warning'])
