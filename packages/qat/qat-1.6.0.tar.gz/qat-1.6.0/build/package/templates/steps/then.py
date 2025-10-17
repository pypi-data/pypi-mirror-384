# -*- coding: utf-8 -*-

"""
Then steps implementation
"""

from behave import Then

from qat import report
import qat

from scripts.object_dictionary import bdd_mapping

@Then("The {name} is opened")
def step(_, name):
    object_definition = bdd_mapping[name]

    window = qat.wait_for_object(object_definition)

    report.verify(
        window.visible,
        f"{name} is opened",
        f"Property 'visible' is {window.visible}"
    )
