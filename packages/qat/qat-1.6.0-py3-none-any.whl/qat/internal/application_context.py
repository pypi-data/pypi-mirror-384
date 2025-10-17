# -*- coding: utf-8 -*-
# (c) Copyright 2023, Qat’s Authors

"""
Provides the ApplicationProxy class
"""

from dataclasses import dataclass
from pathlib import Path
import json
import os
import shlex
import subprocess

from qat.internal import qat_environment
from qat.test_settings import Settings
# Avoid circular imports
# pylint: disable = consider-using-from-import
import qat.internal.tcp_client as tcp_client
import qat.internal.tcp_server as tcp_server

class ApplicationContext():
    """
    Class implementing a proxy to interact with a running application
    """

    @dataclass
    class Internal():
        """
        Class holding internal attributes
        """
        def __init__(self):
            self.process = None
            self.client = None
            self.server = None
            self.has_ownership = False


    def __init__(self, name: str, path: str) -> None:
        self.name = name
        self.path = Path(path)
        self.pid = -1
        self.qt_version = None
        self.return_code = None
        self._config_file = None
        self._internal = ApplicationContext.Internal()
        self._internal.process = None
        self._internal.client = None
        self._internal.server = tcp_server.TcpServer(self)
        self._internal.server.start()


    def detach(self) -> None:
        """
        Detach this context: close communication and reset internal values.
        """
        self.close_comm()
        if self._internal.server is not None:
            self._internal.server.stop()
            self._internal.server = None
        self._internal.process = None
        self._internal.client = None
        self._internal.has_ownership = False


    @property
    def config_file(self):
        """Get the configuration file."""
        if self._config_file is None:
            self._config_file = qat_environment.create_qat_config_file_path(self.pid)
        return self._config_file


    @config_file.setter
    def config_file(self, value):
        """Set the configuration file."""
        self._config_file = value


    def get_name(self) -> str:
        """
        Return the name of the running application
        """
        return self.name


    def get_path(self) -> str:
        """
        Return the parent (folder) path of the running application
        """
        return self.path.parent


    def get_app_path(self) -> str:
        """
        Return the path of the running application
        """
        return self.path


    def launch(self, args: str, local_env: dict, is_posix=True):
        """
        Launch the application with the given args and environment
        """
        if 'QAT_MACOS_ARCH' in os.environ and os.environ['QAT_MACOS_ARCH'].lower() == 'intel':
            command = ['/usr/bin/arch', '-x86_64']
            for var in local_env:
                command.append('-e')
                command.append(f'{var}={local_env[var]}')
            command.append(str(self.path))
        else:
            command = [str(self.path)]
        if args and len(args) > 0:
            if is_posix:
                command = command + shlex.split(args)
            else:
                command = ' '.join(command) + ' ' + args

        self.pid = -1
        self.return_code = None
        self._config_file = None

        # process must stay alive
        # pylint: disable = consider-using-with
        self._internal.process = subprocess.Popen(
            command,
            cwd=str(self.path.parent),
            env=local_env
        )
        self.pid = self._internal.process.pid
        self._internal.has_ownership = True
        print(f"Application started with PID {self.pid}")


    def init_comm(self, port: int, timeout=None):
        """
        Connect a remote C++ client to the given application context's server.
        This client is used for connections and bindings.
        """
        if timeout is None:
            timeout = Settings.wait_for_object_timeout
        self._internal.client = tcp_client.TcpClient(port)
        host = self._internal.server.get_host()
        server_port = self._internal.server.get_port()
        command = {}
        command['command'] = 'communication'
        command['attribute'] = 'init'
        command['args'] = {'host': host, 'port': server_port}

        self.send_command(command, timeout)
        self._internal.server.wait_for_client(timeout / 1000)


    def close_comm(self):
        """
        Disconnect a remote C++ client from this application context's server
        """
        if self._internal.client is None:
            return
        command = {}
        command['command'] = 'communication'
        command['attribute'] = 'close'

        self.send_command(command, nb_trials=1, timeout=Settings.wait_for_app_stop_timeout)
        if self._internal.client is not None:
            self._internal.client.close()


    def init_version_info(self, timeout=None):
        """
        Retrieve and store version info (e.g. current Qt version)
        """
        if timeout is None:
            timeout = Settings.wait_for_object_timeout
        command = {}
        command['command'] = 'list'
        command['attribute'] = 'versionInfo'

        result = self.send_command(command, timeout)
        self.qt_version = result['qtVersion']


    def send_command(self, command: dict, timeout = None, nb_trials = 5):
        """
        Send the given command to the socket and return the response as a json object
        """
        if timeout is None:
            timeout = Settings.wait_for_object_timeout
        if not self.is_running():
            self._internal.client = None
            raise ConnectionAbortedError("Cannot send command: application is not running")
        if self._internal.client is None:
            raise ConnectionAbortedError("Cannot send command: application has been disconnected")
        result = self._internal.client.send_command(
            json.dumps(command),
            timeout,
            nb_trials)
        result = json.loads(result)
        if 'error' in result:
            if command['command'] in ['find', 'list']:
                raise LookupError(result['error'])

            raise RuntimeError(result['error'])
        return result


    def register_callback(self, callback_id, callback) -> int:
        """
        Register the given callback.
        Return the callback ID or None if the callback could not be registered.
        """
        if self._internal.server is not None:
            return self._internal.server.register_callback(callback_id, callback)
        return None


    def unregister_callback(self, callback_id):
        """
        Unregister the given callback
        """
        if self._internal.server is not None:
            self._internal.server.unregister_callback(callback_id)


    def register_close_callback(self, callback):
        """
        Register a callback called when an application terminates.
        """
        if self._internal.server is not None:
            self._internal.server.register_close_callback(callback)


    def is_running(self) -> bool:
        """
        Return whether the application is running or not
        """
        if self.pid < 0 or self.return_code is not None:
            return False
        if self._internal.process is not None:
            self.return_code = self._internal.process.poll()
        if self.return_code is not None:
            return False
        if self._internal.client is not None:
            return self._internal.client.is_connected()

        return False


    def is_finished(self) -> bool:
        """
        Return whether the application has been closed or not
        """
        if self.pid <= 0:
            return False
        if self.return_code is None and self._internal.process is not None:
            self.return_code = self._internal.process.poll()
        if self.return_code is not None:
            return True
        return False


    def get_exit_code(self) -> int:
        """
        Wait for the application to close then return its exit code.
        """
        if self._internal.process:
            try:
                self.return_code = self._internal.process.wait(Settings.wait_for_app_stop_timeout / 1000)
            except TimeoutError as error:
                raise RuntimeError("Cannot retrieve exit code: process is still running") from error
        if self.return_code is not None:
            return self.return_code

        raise ProcessLookupError(
            "Cannot retrieve exit code: process does not exist")


    def take_ownership(self):
        """
        Take or re-take ownership of this context for example after a call to 'detach'
        """
        self._internal.has_ownership = True


    def kill(self):
        """
        Kill the current application
        """
        try:
            self.close_comm()
        except: # pylint: disable = bare-except
            print('Could not close communication with application')
        if self._internal.server is not None:
            self._internal.server.stop()
            self._internal.server = None
        if self._internal.has_ownership and self.config_file is not None:
            if Path(self.config_file).is_file():
                os.remove(self.config_file)
        if self._internal.client is not None:
            self._internal.client.close()
            self._internal.client = None
        if not self._internal.has_ownership:
            return
        if self._internal.process is not None:
            self._internal.process.kill()
        elif self.pid > 0:
            os.kill(self.pid, 9)
            self.return_code = 9
