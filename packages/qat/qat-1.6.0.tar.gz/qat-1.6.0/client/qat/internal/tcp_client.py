# -*- coding: utf-8 -*-
# (c) Copyright 2023, Qat’s Authors

"""
A simple TCP client
"""

from threading import Lock

import errno
import socket
import time

from qat.test_settings import Settings


class TcpClient():
    """
    Class sending commands to a TCP server
    """

    def __init__(self, port: int) -> None:
        """
        Constructor.
        Create and connect a TCP socket to the given port on localhost
        """
        self._port = port
        self._lock = Lock()
        self._connection_errors = 0
        self._socket = None
        self._fsocket = None
        self._is_closed = False
        self.connect()


    def connect(self):
        """
        Create and connect a TCP socket to the current port on localhost
        """
        try:
            self.close()
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect(("localhost", self._port))
            self._socket.settimeout(Settings.wait_for_app_start_timeout / 1000)
            self._fsocket = self._socket.makefile(mode="rwb")
            self._is_closed = False
        except socket.error as error:
            self._socket = None
            print(f'Unable to connect to server: {error}')
            if error.errno != errno.ECONNREFUSED:
                raise
            time.sleep(0.5)


    def is_connected(self):
        """
        Return whether this client is connected or not
        """
        return self._socket is not None


    def close(self):
        """
        Close the underlying socket
        """
        with self._lock:
            self._is_closed = True
            if self._socket:
                self._socket.close()
                self._socket = None
            if self._fsocket:
                self._fsocket.close()
                self._fsocket = None


    def __del__(self) -> None:
        """
        Destructor.
        Close the TCP socket
        """
        self.close()


    def send_command(self, message: str, timeout=None, nb_trials=5) -> str:
        """
        Send the given message to the socket and return the response
        """
        if timeout is None:
            timeout = Settings.wait_for_object_timeout
        with self._lock:
            if self._is_closed:
                raise ConnectionAbortedError('Server has been disconnected')
            try:
                self._socket.settimeout(timeout / 1000)
                header = f"{len(message)}\r\n"
                self._fsocket.write(header.encode('utf-8'))
                self._fsocket.write(message.encode('utf-8'))
                self._fsocket.flush()

                header = self._fsocket.readline()
                length = int(header)
                result = self._fsocket.read(length).decode('utf-8')
                self._connection_errors = 0
                return result
            except (OSError, ValueError, AttributeError) as error:
                self._connection_errors += 1
                # Try to reconnect upon error
                print("Error sending command - trying to reconnect: " + str(error))
        if self._connection_errors >= nb_trials:
            self._connection_errors = 0
            raise ConnectionAbortedError('Lost communication with application')
        self.connect()
        return self.send_command(message, timeout)
