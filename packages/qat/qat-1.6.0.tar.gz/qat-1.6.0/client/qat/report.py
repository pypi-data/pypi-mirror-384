# -*- coding: utf-8 -*-
# (c) Copyright 2023, Qat’s Authors

"""
Test report module
"""

from pathlib import Path
import time

from qat.test_settings import Settings
import qat

TIME_FORMAT = '%Y-%m-%dT%H_%M_%S'

class PropagatedException(Exception):
    """
    Custom exception class wrapping another exception.
    Intended to be thrown from the report when fail() is called.
    """

def start_report(
        name: str,
        report_filename: Path,
        report_class=qat.XmlReport):
    """ 
    Initialize a report with writer and return it
    """
    qat.get_state().current_report = report_class(name, report_filename)
    return qat.get_state().current_report


def stop_report():
    """ 
    Finalize a report and stop its writer
    """
    if qat.get_state().current_report is not None:
        qat.get_state().current_report.end_report()


def log(text: str, log_type="LOG"):
    """
    Add a message to the report
    """
    qat.get_state().current_report.log(text, log_type)


def verify(
        condition,
        description,
        details=""):
    """ 
    Add a verification to the report.
    If condition is False, raise an exception.
    """
    if condition:
        passed(description, details)
        return

    failed(description, details)


def passed(description, details=""):
    """ 
    Add a passed verification to the report".
    """
    qat.get_state().current_report.passed(description, details)


def failed(description, details=""):
    """ 
    Add a failed verification to the report".
    """
    if Settings.screenshot_on_fail:
        timestamp = time.strftime(TIME_FORMAT, time.localtime())
        report_folder = Path(qat.get_state().current_report.get_folder())
        file_name = 'fail_' + timestamp + '.png'
        file_name = report_folder / 'screenshots' / 'failures' / file_name
        try:
            qat.take_screenshot(file_name)
            qat.get_state().current_report.log(
                "Failure screenshot saved to " + file_name.as_posix())
        except: # pylint: disable = bare-except
            pass

    qat.get_state().current_report.failed(description, details)

    raise PropagatedException(details)


def attach_image(image, name, description) -> Path:
    """
    Add the given Image to the report and return its file name
    """
    timestamp = time.strftime(TIME_FORMAT, time.localtime())
    file_name = name + '_' + timestamp + '.png'
    file_name = qat.get_state().current_report.get_folder() / 'screenshots' / 'attached' / file_name
    image.save(file_name)
    qat.get_state().current_report.log(f'Attached image "{name}" has been saved to "{file_name}"')
    qat.get_state().current_report.log(description)
    return file_name
