# -*- coding: utf-8 -*-
# (c) Copyright 2023, Qat’s Authors

"""
Global definition of Qat constants
"""

# Global timeout in ms when waiting for objects
WAIT_FOR_OBJECT_TIMEOUT = 3 * 1000
WAIT_FOR_APP_START = 60 * 1000
WAIT_FOR_APP_STOP = 30 * 1000
WAIT_FOR_APP_ATTACH = 3 * 1000

# Extended timeout for long operation (e.g. drag-and-drop)
LONG_OPERATION_TIMEOUT = 10 * 1000

# Actions on failure
SCREENSHOT_ON_FAIL = True
CONTINUE_AFTER_FAIL = False

# Define when the GUI should be locked (i.e. ignoring user inputs)
# Can be one of "auto" (default), "always" or "never"
LOCK_UI = "auto"

# Object definition used as a target to send native events
Platform = {'id': 'NativeInterface', 'type': 'Qat::internal'}

# Object definition providing access to the QApplication instance (qGuiApp)
QApp = {'id': 'GlobalApplication', 'type': 'Qat::internal'}

# Object definition providing access to the QStyleHints instance (from qGuiApp)
QStyleHints = {'id': 'QStyleHints', 'type': 'Qat::internal'}
