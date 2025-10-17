
# Qat (Qt Application Tester)

## Description
Qat is a testing framework for Qt-based applications.

Qat provides a Python API to interact with any existing Qt application by accessing QML/QtQuick/QWidget elements and simulating user manipulations.

It is also integrated to [behave](https://github.com/behave/behave) to support Behavior-Driven Development (BDD) with the [Gherkin language](https://cucumber.io/docs/gherkin/).

Although Qat uses the GUI to interact with the tested application, it is oriented towards BDD and functional testing rather than UI or non-regression testing.

The main objective of Qat is to provide quick feedback to developers and easy integration to build systems.

## Requirements
Qat requires Python >= 3.9.

Qat supports C++ applications as well as Python bindings such as PySide and PyQt.

Tested applications don't need to be modified but they must be compiled in release mode with a compatible compiler and a dynamically-linked Qt version:

| Qt             | Linux (gcc) | Windows (MSVC) | Mac OS (Arm & Intel) |
| -------------- | ----------- | -------------- | -------------------- |
| __5.15 (LTS)__ | __yes__     | __yes__        | __yes<sup>1</sup>__  |
| __6.0__        | _no_        | _no_           | _no_                 |
| __6.1__        | _no_        | _no_           | _no_                 |
| __6.2 (LTS)__  | __yes__     | __yes__        | __yes__              |
| __6.3__        | __yes__     | __yes__        | __yes__              |
| __6.4__        | __yes__     | __yes__        | __yes__              |
| __6.5 (LTS)__  | __yes__     | __yes__        | __yes__              |
| __6.6__        | __yes__     | __yes__        | __yes__              |
| __6.7__        | __yes__     | __yes__        | __yes__              |
| __6.8 (LTS)__  | __yes__     | __yes__        | __yes__              |
| __6.9__        | __yes__     | __yes__        | __yes__              |
| __6.10__       | __yes__     | __yes__        | __yes__              |

---
<sup>1</sup> Qt 5 requires [Rosetta](https://support.apple.com/en-ca/102527) to run on Silicon machines

## Installation

Qat can be installed with Pip:
```bash
pip install qat
```
This will also install the following dependencies:
- behave (for BDD testing)
- customtkinter and pillow (for GUI)
- tkinter-tooltip (for GUI)
- xmlschema (for test report)

### Tkinter

If [`tkinter`](https://docs.python.org/3/library/tkinter.html) did not come pre-packaged with your python installation, you may need to install it manually.

#### Arch / Manjaro / Other derivatives

To install [`tkinter`](https://archlinux.org/packages/extra/x86_64/tk/), run the following command as root:

```bash
pacman -S tk
```

#### Debian / Other derivatives

To install [`tkinter`](https://packages.debian.org/bookworm/python3-tk/), run the following command as root:

```bash
apt-get install python3-tk 
```

#### Fedora

To install [`tkinter`](https://pkgs.org/download/python3-tkinter/), run the following command as root:

```bash
dnf install python3-tkinter
```

#### MacOS

To install [`tkinter`](https://formulae.brew.sh/formula/python-tk@3.12), run the following command as root:

```bash
brew install python-tk
```

## Setup

The recommended approach is to install [VSCode](https://code.visualstudio.com/download) with the following extensions:
- Python
- Pylance
- Test Explorer UI
- Behave VSC (for BDD)

Any Python (+ Gherkin) environment can be used (PyCharm, Eclipse/Pydev, VSCode, ...) but the present documentation will use VSCode as a tutorial.

## Usage

### Creating a test
Once Qat is installed and setup is completed, navigate to the folder where you want to store your tests. From there, open a command prompt and run:
```bash
qat-create-suite
```

That will generate all the files to run a demo BDD test.

If you prefer using a pure Python test, run:
```bash
qat-create-suite script
```

Then you need to register the application you want to test. The easiest way is to use the Qat GUI, but you can also use the [Python API](https://qat.readthedocs.io/en/1.6.0/doc/Python%20API%20reference.html).
In the current test folder, run the following command:
```bash
qat-gui
```

This will open the _Application Manager_ window:
!["App manager"](https://qat.readthedocs.io/en/1.6.0/_images/app_mgr.png)

Enter an application name in the _Name_ field, then the application path and arguments in the fields below.
> Note: When using PySide or PyQt, enter the path to the main script of the application.

!["New app"](https://qat.readthedocs.io/en/1.6.0/_images/new_app.png)

Click on the _Save_ button to register the application.
!["App saved"](https://qat.readthedocs.io/en/1.6.0/_images/new_app_saved.png)

Now you can close the window and launch VSCode:
```bash
code .
```

### Running a test

The Python demo can be run like any other script: open _demo.py_ in VSCode then click on _Run Python file_. For real tests, it is recommended to use a test framework such as __Pytest__ or __Unittest__.

The BDD demo can be launched from the _Test Explorer_:
!["VSCode BDD demo"](https://qat.readthedocs.io/en/1.6.0/_images/vscode_demo.png "VSCode BDD demo")

In both cases, the demo will verify that an application has been registered (see previous steps), start it and verify that the main window is opened. An XML report will also be generated.

When the demo is successful, it confirms that Qat is properly working on your machine. Otherwise, please refer to the test itself for indications on how to solve the issue.


### Configuring test execution
Test settings are available in _testSettings.py_.
The easiest way to change these values is to add a _testSettings.json_ file to the root of your test suite.

This file can contain the following parameters:
```json
{
   "waitForObjectTimeout": 3000,
   "waitForAppStartTimeout": 60000,
   "waitForAppStopTimeout": 30000,
   "waitForAppAttachTimeout": 3000,
   "longOperationTimeout": 10000,
   "screenshotOnFail": true,
   "continueAfterFail": false,
   "lockUI": "auto"
}
```
If a key is missing, the default value will be used.
During execution, values are available in the _Settings_ class.

If you need to access those values from a script, you can add the following import to your script:

```python
from qat import Settings

# Increase timeout value when finding objects
Settings.wait_for_object_timeout = 5000
```

All timeouts are in milliseconds.

__screenshotOnFail__ determines whether a screenshot of the application is taken and added to the report after each failure. Default is __True__.

__continueAfterFail__ determines whether the test execution should continue after a step has failed (BDD only). Default is __False__

__lockUI__ determines when Qat will lock the application's interface so that it ignores user inputs. Can be one of "always", "never" or "auto" (default, application will not be locked when debugging a test script).
Locking the UI allows users to continue working when a test is running, without affecting the test execution.

For more details on API functions please refer to the [Python API reference](https://qat.readthedocs.io/en/1.6.0/doc/Python%20API%20reference.html).

You can also explore the [tutorials](https://qat.readthedocs.io/en/1.6.0/doc/Tutorials.html).

## Support
You can report any bug, question or feature request by creating a Gitlab issue from [this page](https://gitlab.com/testing-tool/qat/-/issues).

For details, see [the issues workflow](https://qat.readthedocs.io/en/1.6.0/doc/contributing/Issues_Workflow.html).

## Contributing
Contributions are welcome and accepted through Merge Requests.
Please refer to [Contributing](https://qat.readthedocs.io/en/1.6.0/doc/Contributing.html) for detailed instructions.

## Authors and acknowledgment
The complete list of authors and contributors is available [here](https://qat.readthedocs.io/en/1.6.0/doc/AUTHORS.html).

Qat is built on Gitlab using [Docker images](https://bugfreeblog.duckdns.org/docker-qt-tags) provided by [Luca Carlon](https://bugfreeblog.duckdns.org/about-me)

## License
Qat is licensed under the [MIT License](https://opensource.org/license/mit/).

Qat contains a copy of Niels Lohmann's [json library](https://github.com/nlohmann/json) which is licensed under the [MIT License](https://opensource.org/license/mit/).

Qat uses components from the [Qt framework](https://www.qt.io/) which is licensed under the [LGPLv3 License](https://www.gnu.org/licenses/lgpl-3.0.html).
Please note that Qat does not distribute any Qt binary: it uses DLL injection to dynamically link to the Qt binaries used by the target application.

The User Interface of Qat uses [_CustomTkinter_](https://customtkinter.tomschimansky.com/) and [_tkinter-tooltip_](https://github.com/gnikit/tkinter-tooltip) both under the [MIT License](https://opensource.org/license/mit/).
