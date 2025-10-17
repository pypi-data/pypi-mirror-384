# -*- coding: utf-8 -*-
# (c) Copyright 2023, Qat’s Authors

"""
Functions related to screenshots
"""

from pathlib import Path
import tempfile
import time
import os

from qat.internal.application_context import ApplicationContext
from qat.internal.qt_object import QtObject
from qat.internal import find_object
from qat.test_settings import Settings


def take_screenshot(
        app_context: ApplicationContext,
        path=None):
    """
    Take a screenshot of each current main window and save 
    them to the given path. If no path is provided, screenshots will be
    saved to the 'screenshots' subfolder of the current directory
    """
    if path is None:
        path = os.getcwd() + "/screenshots/"
    path = Path(path)
    if not path.is_absolute():
        path = path.absolute()

    command = {}
    command['command'] = 'action'
    command['attribute'] = 'screenshot'
    command['args'] = str(path)
    if path.stem == path.name:
        command['args'] += '/'

    app_context.send_command(command)


def grab_screenshot(
        app_context: ApplicationContext,
        definition,
        delay=0,
        timeout=Settings.wait_for_object_timeout):
    """
    Take a screenshot of the given widget after an optional delay in ms
    """
    definition = find_object.object_to_definition(definition)
    if delay > 0:
        time.sleep(delay / 1000)
    command = {}
    command['command'] = 'action'
    command['attribute'] = 'grab'
    command['object'] = definition
    command['args'] = ''

    result = app_context.send_command(command, timeout)

    if 'found' in result and not result['found']:
        raise LookupError("Cannot grab image: object not found")
    if 'cache_uid' not in result:
        raise RuntimeError("Cannot grab image: failed to create image")

    result = {
        'cache_uid': result['cache_uid']
    }
    image = QtObject(app_context, result)
    start_time = round(1000 * time.time())
    while image.width < 0 and (round(1000 * time.time()) - start_time) < timeout:
        time.sleep(0.2)

    if image.width < 0:
        raise RuntimeError('Failed to grab image')

    with tempfile.NamedTemporaryFile(suffix='.png', delete=True) as temp_file:
        temp_file.close()
        image.save(temp_file.name)

        result['_temp_image_file'] = temp_file.name
        image = QtObject(app_context, result)

        return image
