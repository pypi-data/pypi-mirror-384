# -*- coding: utf-8 -*-
# (c) Copyright 2023, Qat’s Authors

"""
Sample file for Behave integration
"""

from pathlib import Path
from qat import bdd_hooks


def before_tag(context, tag):
    """
    Called before a tagged element starts.
    Add the 'fixture.app.autoclose' fixture.
    """
    bdd_hooks.before_tag(context, tag)


def before_all(context):
    """
    Called before a test starts.
    """
    suite_name = Path(__file__).resolve().parent.stem
    bdd_hooks.before_all(context, suite_name)


def before_feature(context, feature):
    """
    Called before a feature starts.
    """
    bdd_hooks.before_feature(context, feature)
    context.userData = {}


def before_scenario(context, scenario):
    """
    Called before a scenario starts.
    """
    bdd_hooks.before_scenario(context, scenario)


def before_step(context, step):
    """
    Called before a step starts.
    """
    bdd_hooks.before_step(context, step)


def after_step(context, step):
    """
    Called after a step ends.
    """
    bdd_hooks.after_step(context, step)


def after_scenario(context, scenario):
    """
    Called after a scenario ends.
    """
    bdd_hooks.after_scenario(context, scenario)


def after_feature(context, feature):
    """
    Called after a feature ends.
    """
    bdd_hooks.after_feature(context, feature)


def after_all(context):
    """
    Called after a test has run.
    """
    bdd_hooks.after_all(context)
