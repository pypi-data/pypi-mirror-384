# -*- coding: utf-8 -*-
# (c) Copyright 2023, Qat’s Authors

"""
Local definition of Qat constants
"""

from dataclasses import dataclass
import json
from qat.internal import global_constants

@dataclass
class Settings:
    """
    Data class holding local definition of constants.
    Values can be changed from a testSettings.json file.
    """
    wait_for_object_timeout = global_constants.WAIT_FOR_OBJECT_TIMEOUT
    wait_for_app_start_timeout = global_constants.WAIT_FOR_APP_START
    wait_for_app_stop_timeout = global_constants.WAIT_FOR_APP_STOP
    wait_for_app_attach_timeout = global_constants.WAIT_FOR_APP_ATTACH
    long_operation_timeout = global_constants.LONG_OPERATION_TIMEOUT

    screenshot_on_fail = global_constants.SCREENSHOT_ON_FAIL
    continue_after_fail = global_constants.CONTINUE_AFTER_FAIL
    lock_ui = global_constants.LOCK_UI

    loaded = False


def load_test_settings():
    """
    Parse the testSettings.json file to initialize constant values
    """
    if Settings.loaded:
        return
    try:
        with open('testSettings.json', 'rt', encoding='utf-8') as file:
            settings = json.load(file)
            if 'waitForObjectTimeout' in settings:
                Settings.wait_for_object_timeout = settings['waitForObjectTimeout']
            if 'waitForAppStartTimeout' in settings:
                Settings.wait_for_app_start_timeout = settings['waitForAppStartTimeout']
            if 'waitForAppStopTimeout' in settings:
                Settings.wait_for_app_stop_timeout = settings['waitForAppStopTimeout']
            if 'waitForAppAttachTimeout' in settings:
                Settings.wait_for_app_attach_timeout = settings['waitForAppAttachTimeout']
            if 'longOperationTimeout' in settings:
                Settings.long_operation_timeout = settings['longOperationTimeout']
            if 'screenshotOnFail' in settings:
                Settings.screenshot_on_fail = settings['screenshotOnFail']
            if 'continueAfterFail' in settings:
                Settings.continue_after_fail = settings['continueAfterFail']
            if 'lockUI' in settings:
                Settings.lock_ui = settings['lockUI']
            Settings.loaded = True
    except: # pylint: disable=bare-except
        print("Could not load testSettings.json, using default values.")
