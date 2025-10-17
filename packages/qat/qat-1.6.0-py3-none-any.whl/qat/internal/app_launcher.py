# -*- coding: utf-8 -*-
# (c) Copyright 2023, Qat’s Authors

"""
Classes and functions to manage application lifecycle
"""

from importlib import resources as res
from pathlib import Path
from typing import Optional
import xml.etree.ElementTree as xml
import json
import os
import platform
import subprocess
import sys
import time

import qat.internal.application_context as app_ctxt
from qat.internal import debug_operations, qat_environment
from qat.test_settings import Settings

import qat.test_settings


def is_linux() -> bool:
    """
    Return whether the current platform is Linux or not
    """
    system = platform.system()
    return system == "Linux"


def is_windows() -> bool:
    """
    Return whether the current platform is Windows or not
    """
    system = platform.system()
    return system == "Windows"


def is_macos() -> bool:
    """
    Return whether the current platform is MacOS or not
    """
    system = platform.system()
    return system == "Darwin"


def is_debugging() -> bool:
    """
    Return whether the debugger is currently active or not
    """
    try:
        if hasattr(sys, 'gettrace') and sys.gettrace() is not None:
            return True
        if hasattr(sys, 'monitoring') and sys.monitoring.get_tool(sys.monitoring.DEBUGGER_ID) is not None:
            return True
    except AttributeError:
        pass
    if 'COVERAGE' in os.environ:
        return len(os.environ['COVERAGE']) == 0
    return False


def get_injector(app_path: Path) -> Path:
    """
    Return the path to the Injector application.
    """
    if is_windows():
        injector_name = 'injector.exe'
    elif is_linux():
        injector_name = 'libinjector.so'
    elif is_macos():
        injector_name = 'libinjector.dylib'
    else:
        raise NotImplementedError('Current platform is not supported')

    # Find injector in installed package
    try:
        injector_path = res.files('qat') / 'bin'
        injector_exe = injector_path / injector_name
        if os.path.exists(injector_exe):
            return injector_exe
    except: # pylint: disable = bare-except
        print("Warning: Qat requires Python >= 3.9")

    # Find injector in dev environment
    for root_path in [
        Path(os.getcwd()) / 'client' / 'qat' / 'bin',
        Path(os.getcwd()) / 'build']:
        matches = list(root_path.glob(f"**/{injector_name}"))
        if len(matches) > 0:
            return matches[0]

    # Last try: get locally installed binaries
    injector_exe = app_path / injector_name
    if not os.path.exists(injector_exe):
        raise FileNotFoundError("Could not find Injector binaries")

    return injector_exe


def inject_dll(context: app_ctxt.ApplicationContext):
    """
    Call Injector application to load the qat server DLL into the target application
    """
    injector_exe = get_injector(context.get_path())
    injector_path = injector_exe.parent
    try:
        subprocess.run(
            [injector_exe, str(context.pid), str(
                injector_path / "injector.dll")],
            cwd=injector_path,
            shell=False,
            check=True,
            timeout=Settings.wait_for_app_start_timeout)
    except subprocess.TimeoutExpired as error:
        # Injector may have run too early
        context.kill()
        raise TimeoutError("Application could not start (timeout)") from error
    except:
        context.kill()
        raise


def get_port_from_file(context: app_ctxt.ApplicationContext) -> int:
    """
    Parse the temporary file associated to the given context to retrieve its port number
    """
    port = -1
    delay = 0.2
    nb_tries = 10 * int(1/delay)  # 10 seconds
    last_error = None
    for _ in range(nb_tries):
        try:
            last_error = None
            # Read server port from config file
            with open(context.config_file, 'rt', encoding="utf-8") as file:
                content = file.readline()
                content = content.strip()
                port = int(content)
                break
        except (OSError, ValueError) as error:
            time.sleep(delay)
            # Handle cases when the application exits prematurely
            if context.is_finished():
                print('Abort: app terminated')
                break
            last_error = error
    if port < 0:
        if last_error is not None:
            print(f"Error reading pid file {last_error}")
        context.kill()
        raise ProcessLookupError(
            "Could not retrieve server port number. "
            "Cannot establish communication with application.")
    return port


def connect_to(context: app_ctxt.ApplicationContext):
    """
    Establish a TCP communication with the target application
    """
    port = get_port_from_file(context)

    # Establish TCP communication
    try:
        context.init_comm(port)
    except: # pylint: disable=bare-except
        # Process IDs can be reused, causing get_port_from_file()
        # to read an obsolete file. Make sure to parse the new file
        port = get_port_from_file(context)
        context.init_comm(port)

    # Add version info to context
    context.init_version_info()


def get_pid_from_name(process_name: str, timeout: int):
    """
    Return the Process ID corresponding to the given process name
    """
    apps = qat.list_applications()
    if process_name in apps:
        app_path = Path(apps[process_name]['path'])
        if app_path.is_file():
            process_name = Path(apps[process_name]['path']).name

    start_time = round(1000 * time.time())
    if is_windows():
        command = ("Get-CimInstance -ClassName Win32_Process "
            f"-Filter \"Name <> 'powershell.exe' AND CommandLine like '%{process_name}%'\" "
            "| Select -ExpandProperty ProcessId")
        args = ['powershell', '-command', command]
    else:
        args = ['pgrep', '-f', f'{process_name}']

    while (round(1000 * time.time()) - start_time) < timeout:
        try:
            result = subprocess.check_output(
                args, text=True, shell=False)
            pid = int(result.split()[0].strip())
            return int(pid)
        except (ValueError, subprocess.CalledProcessError, IndexError):
            time.sleep(0.2)

    raise ProcessLookupError(f"Could not find process '{process_name}'")


def get_app_path_from_pid(pid: int, timeout: int):
    """
    Get absolute application path given its process ID
    """
    start_time = round(1000 * time.time())
    if is_linux():
        args = ['readlink', '-f', f'/proc/{pid}/exe']
    elif is_windows():
        command = f'Get-Process -Id {pid} -FileVersionInfo | Select -ExpandProperty FileName'
        args = ['powershell', '-command', command]
    elif is_macos():
        args = ['ps', 'p', f'{pid}', '-o', 'command']
    else:
        raise NotImplementedError('Current platform is not supported')

    while (round(1000 * time.time()) - start_time) < timeout:
        try:
            result = subprocess.check_output(args, text=True, shell=False)
        except subprocess.CalledProcessError:
            result = ''
        paths = result.split('\n')
        if is_macos():
            # Remove header
            paths = paths[1:]
        if len(paths) > 0 and len(paths[0]) > 0:
            return Path(paths[0]).resolve()
        time.sleep(0.2)

    raise ProcessLookupError(f"Could not find process '{pid}'")


def can_attach(pid: int) -> bool:
    """
    Return whether Qat can attach to the given process
    """
    if is_windows():
        return True
    try:
        cmd = 'lsof' if is_macos() else 'pmap'
        with subprocess.Popen(
            [cmd, '-p', f'{pid}'],
            text=True,
            shell=False,
            stdout=subprocess.PIPE) as lsof_process:

            result = subprocess.run(
                ['grep', 'libinjector'],
                text=True,
                shell=False,
                check=False,
                stdin=lsof_process.stdout,
                stdout=subprocess.PIPE)
            result = result.stdout.strip()
            return len(result) > 0

    except subprocess.CalledProcessError as exc:
        raise ProcessLookupError('Application process was not found') from exc


def attach_to(name_or_pid) -> app_ctxt.ApplicationContext:
    """
    Attach to the given application by name or process ID.
    If a name is given, it must correspond to a registered application.
    """
    qat.test_settings.load_test_settings()
    timeout = Settings.wait_for_app_attach_timeout
    if isinstance(name_or_pid, str) and len(name_or_pid) > 0:
        pid = get_pid_from_name(name_or_pid, timeout)
    # 'bool' is a subclass of 'int' in Python
    elif isinstance(name_or_pid, int) and not isinstance(name_or_pid, bool):
        pid = name_or_pid
    else:
        raise ValueError(
            "Invalid argument given to attach_to_application(): must be app name or process ID")

    if not can_attach(pid):
        raise ConnectionError(
            'The application must be launched by Qat (by calling qat.start_application()) '
            'in order to use qat.attach_to_application()')

    app_path = get_app_path_from_pid(pid, timeout)
    context = app_ctxt.ApplicationContext(name_or_pid, app_path)
    context.pid = pid

    if is_windows():
        inject_dll(context)
    connect_to(context)

    return context


def get_config_file(shared: Optional[bool] = None) -> Path:
    """
    Return the current config file
    """
    local_file = Path(os.getcwd()) / 'applications.json'
    shared_file = Path.home() / '.qat' / 'applications.json'

    # Select local file if it exists or if shared file does not
    if shared is None:
        if local_file.is_file():
            config_file = local_file
        elif shared_file.is_file():
            config_file = shared_file
        else:
            config_file = local_file
    elif shared:
        config_file = shared_file
    else:
        config_file = local_file

    return config_file


def list_applications() -> dict:
    """
    List all registered applications (shared and local)
    """
    applications = {}
    # Load shared applications first
    try:
        with open(get_config_file(True), 'r', encoding='utf-8') as file:
            applications = json.load(file)
        for app in applications.values():
            app['shared'] = True
    except: # pylint: disable=bare-except
        pass

    # Load local applications, overwriting shared ones in case of conflict
    try:
        local_application = {}
        with open(get_config_file(False), 'r', encoding='utf-8') as file:
            local_application = json.load(file)
        for app in local_application.values():
            app['shared'] = False
        applications.update(local_application)
    except: # pylint: disable=bare-except
        pass
    return applications


def register_application(config_file: Path, name: str, path: str, args='') -> None:
    """
    Add the given application to the given configuration file.

    Args:
      config_file: Path to the file to be modified.
      name: Must be a unique name for this application. It will be used when calling :func:`start_application` for example.
      path: The absolute path to the application executable.
      args (optional): The default arguments used when launching the application (e.g. when using Qat-Spy). 
        They can be overridden when calling :func:`start_application`.
    """
    applications = {}
    try:
        with open(config_file, 'r', encoding='utf-8') as file:
            applications = json.load(file)
    except: # pylint: disable=bare-except
        print("Invalid configuration file. Content will be overwritten.")
    if isinstance(path, Path):
        path = str(path)
    applications[name] = {
        "path": path,
        "args": args
    }
    if not config_file.is_file():
        os.makedirs(config_file.parent, exist_ok=True)
        with open(config_file, "w", encoding="utf-8") as file:
            file.write("{}")
            file.close()
    with open(config_file, 'w', encoding='utf-8') as file:
        json.dump(applications, file, indent=3)


def unregister_application(config_file: Path, name: str) -> None:
    """
    Remove the given application from the configuration file.

    Args:
      config_file: Path to the file to be modified.
      name: The unique name of the application, must be the same as the one given to :func:`register_application`.
    """
    applications = {}
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as file:
            applications = json.load(file)

    if name in applications:
        del applications[name]
        if len(applications) > 0:
            with open(config_file, 'w', encoding='utf-8') as file:
                json.dump(applications, file, indent=3)
        else:
            os.remove(config_file)


def cleanup_temp_files():
    """
    Delete old temporary files
    """
    temp_folder = qat_environment.get_temp_folder()
    for file in temp_folder.glob('qat-*.txt'):
        pid = file.stem[4:]
        if is_linux():
            try:
                result = subprocess.run(
                    ['ps', '-p', f'{pid}', '-h', '-o', 'pid'],
                    text=True,
                    shell=False,
                    check=False,
                    stdout=subprocess.PIPE).stdout

            except subprocess.CalledProcessError:
                continue
        elif is_windows():
            command = f'Get-Process -Id {pid} | Select -ExpandProperty ProcessName'
            try:
                result = subprocess.run(
                    ['powershell', '-command', command],
                    text=True,
                    shell=False,
                    check=False,
                    stdout=subprocess.PIPE).stdout
            except subprocess.CalledProcessError:
                continue
        elif is_macos():
            try:
                result = subprocess.run(
                    ['ps', '-p', f'{pid}', '-o', 'pid'],
                    text=True,
                    shell=False,
                    check=False,
                    stdout=subprocess.PIPE).stdout
                # Remove header
                result = '\n'.join(result.splitlines()[1:])

            except subprocess.CalledProcessError:
                continue
        else:
            raise NotImplementedError('Current platform is not supported')
        result = result.strip()
        if len(result) == 0:
            try:
                os.remove(file)
            except OSError:
                print(f'Could not delete temporary file {file}')


def find_app_exec(app_name: str, app_path: Path) -> Path:
    """
    Look for application executable in the given folder.
    Raise a FileNotFoundError is no executable was found.
    """
    if not app_path or not os.path.exists(app_path):
        raise FileNotFoundError(f"Application path not found ({app_path})")
    app_path = Path(app_path).resolve()
    if not app_path.is_file() and is_macos():
        # Handle app bundles
        exec_path = get_macos_app(app_path, app_name)
        if exec_path.is_file() and os.access(exec_path, os.X_OK):
            return exec_path
    if not app_path.is_file():
        # Append app name as file name
        exec_name = app_name
        if is_windows():
            exec_name += '.exe'
        app_path /= exec_name
    if not app_path.exists():
        raise FileNotFoundError(f"'{app_name}' application not found ({app_path})")
    return app_path


def get_macos_app(app_path: Path, app_name: str):
    """
    Return the path of the executable inside a MacOS app.
    """
    plist_path = app_path / 'Contents' / 'Info.plist'
    if not plist_path.is_file():
        return app_path / app_name
    contents = xml.parse(plist_path)
    root = contents.getroot()
    if len(root) == 1:
        for i in range(len(root[0])):
            if root[0][i].text == 'CFBundleExecutable':
                exec_name = root[0][i + 1].text
                return app_path / 'Contents' / 'MacOS' / exec_name

    return app_path / 'Contents' / 'MacOS' / app_name


def _format_app_args(app_name: str, args: str):
    """
    Resolve app path and arguments to format them for the launcher.
    """
    apps = list_applications()
    if app_name not in apps:
        raise ValueError(
            f"Application '{app_name}' is not defined in "
            "configuration file 'applications.json'")
    app_path = apps[app_name]['path']
    is_script = False
    if str(app_path).endswith('.py'):
        app_path = Path(app_path)
        is_script = True
    else:
        app_path = find_app_exec(app_name, app_path)
    if args is None:
        args = apps[app_name]['args']

    if is_script:
        if args is None:
            args = ''
        args = str(app_path) + ' ' + args
        app_path = Path(sys.executable)

    return app_path, args


def start_application(app_name: str, args: str, detached=False) -> app_ctxt.ApplicationContext:
    """
    Start the given application, inject the server library (except if detached is True)
    and return the corresponding application context
    """

    if not (is_linux() or is_windows() or is_macos()):
        raise NotImplementedError(f"'{platform.system()}' platform is not supported.")

    qat.test_settings.load_test_settings()

    app_path, args = _format_app_args(app_name, args)

    cleanup_temp_files()

    # Prepare environment
    local_env = dict(os.environ)
    if 'TEMP' not in local_env:
        local_env['TEMP'] = str(qat_environment.get_temp_folder())

    if is_linux():
        local_env['LD_PRELOAD'] = str(get_injector(app_path.parent))
    elif is_macos():
        local_env['DYLD_INSERT_LIBRARIES'] = str(get_injector(app_path.parent))

    # Launch application
    for attempt in range(2):
        try:
            context = app_ctxt.ApplicationContext(app_name, app_path)
            context.launch(args, local_env, not is_windows())

            if detached:
                return context

            if is_windows():
                inject_dll(context)

            connect_to(context)

            # Lock GUI
            lock_ui = Settings.lock_ui.lower()
            if lock_ui == "always" or (lock_ui == "auto" and not is_debugging()):
                debug_operations.lock_application(context)

            break

        except Exception as error:
            port = get_port_from_file(context)
            print(error)
            print(f"Failed to connect to application (port {port}). Stopping process {context.pid}...")
            context.kill()
            print(f"Application {app_name} was killed.")
            if attempt == 0:
                continue
            raise error

    print(f"Application {app_name} successfully started and ready for testing")
    return context
