# -*- coding: utf-8 -*-
# (c) Copyright 2024, Qat’s Authors

"""
Provides function for Qat environment management
"""
import os
from pathlib import Path
import tempfile


def get_temp_folder() -> Path:
    """
    Return the path to the temporary folder

    Note:
      Creates the environment variable 'TEMP' when it does not exist
    """

    if 'TEMP' not in os.environ:
        os.environ['TEMP'] = tempfile.gettempdir()
    return Path(os.environ['TEMP'])


def create_qat_config_file_path(application_context_pid: int) -> Path:
    """
    Return the path to the qat configuration file of the current application context

    Args:
      application_context_pid: PID of the current application context
    """
    if application_context_pid < 0:
        raise NameError(
            "Could not create the qat configuration path."
            f"The application context pid [{application_context_pid}] is invalid")
    return get_temp_folder() / f"qat-{application_context_pid}.txt"
