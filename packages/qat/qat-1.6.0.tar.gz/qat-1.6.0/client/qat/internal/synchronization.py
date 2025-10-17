# -*- coding: utf-8 -*-
# (c) Copyright 2023, Qat’s Authors

"""
Functions related to timing and synchronization
"""

import time

from collections.abc import Callable

from qat.test_settings import Settings
from qat.internal.application_context import ApplicationContext
from qat.internal.find_object import wait_for_object_exists


def wait_for_property(
        app_context: ApplicationContext,
        definition: dict,
        property_name: str,
        reference,
        comparator: Callable,
        timeout = Settings.wait_for_object_timeout,
        check = False) -> bool:
    """
    Wait for the given property to reach the given condition.
    property_name can be a nested property (using dot notation, e.g. 'color.name')
    """
    start_time = round(1000 * time.time())

    last_error = None
    nested_properties = property_name.split('.')
    while (round(1000 * time.time()) - start_time) < timeout:
        try:
            last_error = None
            qtobject = wait_for_object_exists(app_context, definition, timeout)
            current_object = qtobject
            for prop in nested_properties:
                value = getattr(current_object, prop)
                current_object = value
            if comparator(value, reference):
                return True
            raise ValueError(f'Property "{property_name}" is "{value}" (ref is {reference})')
        except (LookupError, ValueError, AttributeError) as error:
            last_error = error
            time.sleep(0.1)

    if not check:
        if last_error is not None:
            print(f'Warning: {last_error}')
        return False

    if last_error is not None:
        raise last_error
    raise TimeoutError("Property did not reach the given condition before timeout")
