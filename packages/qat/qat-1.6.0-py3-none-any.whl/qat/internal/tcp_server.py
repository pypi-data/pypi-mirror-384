# -*- coding: utf-8 -*-
# (c) Copyright 2023, Qat’s Authors

"""
A simple TCP server
"""

from threading import Condition, Event, Lock, Thread

import inspect
import json
import socketserver
import time

from qat.internal.qt_custom_object import QtCustomObject


class QatRequestHandler(socketserver.StreamRequestHandler):
    """
    Request handler derived from StreamRequestHandler
    """
    def handle(self):
        print(f'New connection from {self.client_address[0]}')
        while True:
            try:
                header = self.rfile.readline().strip()
            except ConnectionResetError:
                break
            except Exception as e: # pylint: disable=broad-exception-caught
                print(f'Error reading connected socket: {e}')
                break
            if header == b'':
                print('Connection was closed by the client')
                break

            try:
                length = int(header)
                if length == 0:
                    while not self.server.is_ready.is_set():
                        time.sleep(0.1)
                    with self.server.startup_sync:
                        self.server.startup_sync.notify_all()
                    continue
                content = self.rfile.read(length).decode('utf-8')
                self.execute_callback(json.loads(content))
            except Exception as error: # pylint: disable=broad-exception-caught
                # Avoid stopping the server upon errors
                print('Error in request handler: ' + str(error))

        for cb in self.server.app_closed_callback:
            cb()


    def execute_callback(self, content: dict):
        """
        Execute the callback 
        """
        # Avoid cyclic import
        # pylint: disable = import-outside-toplevel
        # pylint: disable = cyclic-import
        from qat.internal.qt_object import QtObject
        callback_id = content['id']
        with self.server.callbacks_lock:
            if callback_id in self.server.callbacks:
                callback_elements = self.server.callbacks[callback_id]
                context = callback_elements[0]
                callback = callback_elements[1]
            else:
                print(f"Unknown callback ID: {callback_id}")
                return

        if 'args' in content:
            arg_list = []
            for arg in content['args']:
                if 'value' in arg:
                    value = arg['value']
                    if isinstance(value, dict):
                        arg_list.append(QtCustomObject(value))
                    else:
                        arg_list.append(value)
                elif 'object' in arg:
                    arg_list.append(QtObject(context, arg['object']))

            num_cb_args = len(inspect.signature(callback).parameters)
            arg_tuple = tuple(arg_list[:num_cb_args])
            callback(*arg_tuple)

        else:
            callback()


class QatThreadedTcpRequestServer(socketserver.ThreadingTCPServer):
    """
    A ThreadingTCPServer with additional fields
    """

    def __init__(self, server_address) -> None:
        super().__init__(server_address, QatRequestHandler)
        self.callbacks_lock = Lock()
        self.callbacks = {}
        self.app_closed_callback = []
        self.startup_sync = Condition()
        self.is_ready = Event()


class TcpServer():
    """
    Class implementing a TCP server
    """
    daemon_threads = True

    def __init__(self, context, host="127.0.0.1", port=None) -> None:
        """
        Constructor.
        """
        self._context = context
        self._host = host
        self._port = port
        self._server = None
        self._thread = None


    def start(self):
        """
        Start the server thread
        """
        self._server = QatThreadedTcpRequestServer((self._host, 0))
        self._server.daemon_threads = True
        self._port = self._server.socket.getsockname()[1]
        self._thread = Thread(target=self._internal_serve, daemon=True)
        print(f'Starting Python TCP server on port {self._port}')
        self._thread.start()


    def stop(self):
        """
        Stop the server thread
        """
        print('Stopping Python TCP server')
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server.app_closed_callback.clear()
            with self._server.callbacks_lock:
                self._server.callbacks.clear()
            self._server = None
        if self._thread is not None:
            self._thread.join(timeout = 5)
            if self._thread.is_alive():
                print('TCP server thread is still running and will be aborted.')
            self._thread = None


    def __del__(self) -> None:
        """
        Destructor.
        Stop the TCP server
        """
        self.stop()


    def _internal_serve(self):
        try:
            self._server.serve_forever()
        except Exception as error: # pylint: disable=broad-exception-caught
            # Avoid raising exceptions from threads
            print(error)


    def get_host(self) -> str:
        """
        Return the host address
        """
        return self._host


    def get_port(self) -> int:
        """
        Return the server port
        """
        return self._port


    def wait_for_client(self, timeout):
        """
        Wait for a client to communicate with this server.
        Intended to be used just after initializing a communication,
        allowing synchronization between client and server.
        """
        with self._server.startup_sync:
            self._server.is_ready.set()
            if not self._server.startup_sync.wait(timeout):
                raise TimeoutError("TCP server did not receive any message from application")


    def register_callback(self, callback_id, callback) -> int:
        """
        Register the given callback.
        """
        with self._server.callbacks_lock:
            self._server.callbacks[callback_id] = (self._context, callback)

        return callback_id


    def unregister_callback(self, callback_id):
        """
        Unregister the given callback
        """
        with self._server.callbacks_lock:
            if callback_id in self._server.callbacks:
                del self._server.callbacks[callback_id]


    def register_close_callback(self, callback) -> None:
        """
        Register a callback called when an application terminates.
        """
        self._server.app_closed_callback.append(callback)
