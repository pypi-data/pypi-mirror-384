# -*- coding: utf-8 -*-

"""
Given steps implementation
"""

from behave import Given
from qat import report
import qat

@Given("An application is registered")
def step(context):
    registered_apps = qat.list_applications()
    if len(registered_apps) == 0:
        report.failed(
            'No application found',
            'Use qat-gui command or qat.register_application() to register an application'
        )
    app_name = list(registered_apps)[0]
    report.log(f"'{app_name}' is available")
    # Add application name to context so other steps can access it
    context.userData['app_name'] = app_name
