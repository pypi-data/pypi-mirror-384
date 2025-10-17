# -*- coding: utf-8 -*-
# (c) Copyright 2023, Qat’s Authors

"""
Hooks intended to be called from environment.py when using Behave
"""

from pathlib import Path
import os
from behave.model import Scenario, Status
from behave import fixture, use_fixture

from qat.report import PropagatedException
from qat import test_settings
import qat


@fixture
def app_autoclose(_):
    """
    Fixture closing any running application at the end of a feature or scenario
    """
    yield
    qat.close_all_apps()


def before_tag(context, tag):
    """
    Called before a tagged element starts.
    Add the 'fixture.app.autoclose' fixture.
    """
    if tag == 'fixture.app.autoclose':
        use_fixture(app_autoclose, context)


def before_all(context, suite_name):
    """
    Called before a test starts.
    Setup XML report file and initialize test settings from JSON file.
    """
    if 'report_file' in context.config.userdata:
        report_filename = Path(context.config.userdata['report_file'])
    else:
        report_filename = Path(os.getcwd()) / 'report' / 'results.xml'

    qat.get_state().current_report = qat.XmlReport(suite_name, report_filename)

    # Apply settings
    test_settings.load_test_settings()
    Scenario.continue_after_failed_step = test_settings.Settings.continue_after_fail


def before_feature(context, feature):
    """
    Called before a feature starts.
    Add an entry to the current report.
    """
    context.userData = {}
    test_name = Path(feature.filename).resolve().parent.stem
    qat.get_state().current_report.start_test_case(test_name)
    qat.get_state().current_report.start_feature(
        feature.name, '\n'.join(feature.description))


def before_scenario(_, scenario):
    """
    Called before a scenario starts.
    Add an entry to the current report.
    """
    qat.get_state().current_report.start_scenario(
        scenario.name, '\n'.join(scenario.description))
    # pylint: disable = protected-access
    if hasattr(scenario, '_row') and scenario._row is not None:
        qat.get_state().current_report.start_example(scenario._row.headings, scenario._row.cells)


def before_step(context, step):
    """
    Called before a step starts.
    Add an entry to the current report.
    """
    qat.get_state().current_report.start_step(step.name)
    if hasattr(step, 'text') and step.text is not None:
        context.multiLineText = step.text.splitlines()


def after_step(_, step):
    """
    Called after a step ends.
    Add an entry to the current report.
    """
    if step.status == Status.failed:
        if not isinstance(step.exception, PropagatedException):
            qat.get_state().current_report.failed(
                "Script Error", str(step.exception), step.exc_traceback)
    qat.get_state().current_report.end_step()


def after_scenario(*_):
    """
    Called after a scenario ends.
    Add an entry to the current report and close the current application.
    """
    qat.get_state().current_report.end_scenario()


def after_feature(*_):
    """
    Called after a feature ends.
    Add an entry to the current report and closes the report.
    """
    qat.get_state().current_report.end_feature()
    qat.get_state().current_report.end_test_case()


def after_all(*_):
    """
    Waits for the report to be written to disk
    """
    del qat.get_state().current_report
