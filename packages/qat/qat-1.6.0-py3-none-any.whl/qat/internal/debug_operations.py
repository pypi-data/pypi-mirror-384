# -*- coding: utf-8 -*-
# (c) Copyright 2023, Qat’s Authors

"""
Functions used for development and debugging purposes
"""

from qat.internal.application_context import ApplicationContext


def activate_picker(app_context: ApplicationContext):
    """
    Activate the object picker
    """
    command = {}
    command['command'] = 'action'
    command['attribute'] = 'picker'
    command['args'] = 'enable'

    app_context.send_command(command)


def deactivate_picker(app_context: ApplicationContext):
    """
    Deactivate the object picker
    """
    command = {}
    command['command'] = 'action'
    command['attribute'] = 'picker'
    command['args'] = 'disable'

    app_context.send_command(command)


def lock_application(app_context: ApplicationContext):
    """
    Lock application GUI by filtering external/user events
    """
    command = {}
    command['command'] = 'action'
    command['attribute'] = 'lock'
    command['args'] = 'enable'

    app_context.send_command(command)


def unlock_application(app_context: ApplicationContext):
    """
    Unlock application GUI by allowing external/user events
    """
    command = {}
    command['command'] = 'action'
    command['attribute'] = 'lock'
    command['args'] = 'disable'

    app_context.send_command(command)
