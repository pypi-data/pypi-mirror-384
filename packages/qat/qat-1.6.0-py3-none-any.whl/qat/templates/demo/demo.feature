Feature: Simple demo of a BDD test

@fixture.app.autoclose
Scenario: Verify that application is ready for testing

   # If this step fails, run the 'qat-gui' command in the suite folder
   # to register any Qt application.
   Given An application is registered

      # If this step fails, verify that your application uses a supported
      # Qt version and that Qat is not blocked by any antivirus or firewall.
      When This application is started

         # If this step fails, it means that there is no ApplicationWindow displayed
         # (or several ones). You can edit its definition in scripts/object_dictionary.py.
         Then The Main Window is opened