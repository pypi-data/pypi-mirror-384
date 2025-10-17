# -*- coding: utf-8 -*-
# (c) Copyright 2024, Qat’s Authors

"""
Global internal state of the API
"""

class GlobalState: # pylint: disable=too-few-public-methods
    """Holds the global state of the API, per thread."""

    def __init__(self):
        self.current_report = None
        self.current_app_context = None
        self.app_context_list = []


    def close_apps(self):
        """
        Close all current applications belonging to the this state
        """
        try:
            self.current_app_context = None
            for ctxt in self.app_context_list:
                ctxt.kill()
            self.app_context_list.clear()
        except Exception: # pylint: disable=broad-exception-caught
            pass
