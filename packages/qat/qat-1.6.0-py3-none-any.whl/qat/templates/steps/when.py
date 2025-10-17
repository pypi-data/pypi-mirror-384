# -*- coding: utf-8 -*-

"""
When steps implementation
"""

from behave import When

from qat import report
import qat

@When("This application is started")
def step(context):
    app_name = context.userData['app_name']
    # Save application context to context so other steps can use it later
    context.userData['app_context'] = qat.start_application(app_name)
    report.log(f"'{app_name}' was successful started")

