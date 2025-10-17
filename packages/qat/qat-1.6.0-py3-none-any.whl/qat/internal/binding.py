# -*- coding: utf-8 -*-
# (c) Copyright 2023, Qat’s Authors

"""
Provides a class to manage bindings
"""

import qat


class Binding():
    """
    Automatically manage a Qat connection
    """

    def __init__(
            self,
            remote_object: dict,
            remote_property: str,
            local_object,
            local_property: str):
        """
        Establish a new connection between the remote object's property
        and the local object's member
        """
        self._remote_object = remote_object
        self._remote_property = remote_property
        self._local_object = local_object
        self._local_property = local_property
        self._conn_id = None
        self.connect()


    def __del__(self):
        """
        Disconnect the binding upon destruction
        """
        try:
            self.disconnect()
        except: # pylint: disable=bare-except
            pass


    def __call__(self, *args):
        """
        Implement a functor to use this binding object as a connection callback.
        Set the local property's value upon connection update
        """
        args = list(args)
        if len(args) != 1:
            print('Invalid binding call: must have a single mandatory argument')
            return
        setattr(self._local_object, self._local_property, args[0])


    def connect(self):
        """
        Connect (or re-connect) this binding to the remote object.
        """
        self._conn_id = qat.connect(
            self._remote_object, self._remote_property, self)
        # Initialize current value
        current_value = getattr(self._remote_object, self._remote_property)
        self(current_value)


    def disconnect(self) -> bool:
        """
        Disconnect this binding. Receiver will not be updated anymore.
        """
        if self._conn_id is not None:
            result = qat.disconnect(self._conn_id)
            self._conn_id = None
            return result
        return True
