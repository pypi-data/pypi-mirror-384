#!/bin/python

from __future__ import annotations
# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
    # from .gateway import MBIOGateway

import socket


class MBIOSocket(object):
    def __init__(self, host, port):
        self._host=host
        self._port=port
        self._socket=None
        self._connected=False

    @property
    def host(self):
        return self._host

    def connect(self, timeout=3.0):
        try:
            if not self._connected:
                self._socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._socket.settimeout(timeout)
                self._socket.connect((self._host, self._port))
                # enable non blocking mode
                self._socket.settimeout(0)
                self._connected=True
                return True
            return self._connected
        except:
            pass

    def isConnected(self):
        return self._connected

    def disconnect(self):
        try:
            self._socket.close()
        except:
            pass
        self._socket=None
        self._connected=False

    def write(self, data):
        try:
            self.connect()
            self._socket.send(data)
            return True
        except:
            self.disconnect()

    def read(self):
        try:
            self.connect()
            data = self._socket.recv(4096)
            if not data:
                self.disconnect()
            return data
        except:
            pass


class MBIOSocketString(MBIOSocket):
    def write(self, data):
        return super().write(data.encode())

    def read(self):
        try:
            return super().read().decode()
        except:
            pass


if __name__ == "__main__":
    pass
