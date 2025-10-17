# -*- coding: utf-8 -*-

from qat import report
import qat

from scripts.object_dictionary import main_window

def test_launch():
    # Step #1: get the first registered application
    # If this step fails, run the 'qat-gui' command in the suite folder
    # to register any Qt application.
    registered_apps = qat.list_applications()
    if len(registered_apps) == 0:
        report.failed(
            'No application found',
            'Use qat-gui command or qat.register_application() to register an application'
        )
    app_name = list(registered_apps)[0]
    report.log(f"'{app_name}' is available")

    # Step #2: launch the application
    # If this step fails, verify that your application uses a supported
    # Qt version and that Qat is not blocked by any antivirus or firewall.
    app_context = qat.start_application(app_name)
    report.log(f"'{app_name}' was successful started")

    # Step #3: verify that the main window is opened
    # If this step fails, it means that there is no ApplicationWindow
    # displayed. You can edit its definition in scripts/object_dictionary.py.
    window = qat.wait_for_object_exists(main_window)

    report.verify(
        window.visible,
        "Main Window is opened",
        f"Property 'visible' is {window.visible}"
    )

    # Step #4: close the application
    qat.close_application(app_context)


if __name__ == "__main__":

    # Before running any test, you need to register the tested application.
    # You can do so by starting the 'qat-gui' command in the current directory
    # or by calling the qat.register_application() function:
    # qat.register_application(app_name, args)
    # Please refer to API documentation for details.

    # Create a test report
    report.start_report('demo', './report.xml')

    try:
        test_launch()
    finally:
        # This call is mandatory when the test ends, without it,
        # the report writer would still be running and the execution
        # would hang. It is recommended to use the 'teardown' feature of your
        # test framework (e.g. pytest) to guarantee this call is made.
        report.stop_report()
