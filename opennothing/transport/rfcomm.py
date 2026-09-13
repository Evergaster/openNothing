"""Transporte real sobre RFCOMM (Bluetooth Clasico, canal SPP)."""

import socket
from typing import Optional

from opennothing.transport.base import Transport


class RfcommTransport(Transport):
    name = "rfcomm"

    def __init__(
        self,
        mac: str,
        channel: int = 15,
        timeout: float = 5.0,
    ):
        self.mac = mac
        self.channel = channel
        self.timeout = timeout
        self._sock: Optional[socket.socket] = None

    def connect(self) -> None:
        if self._sock is not None:
            return
        sock = socket.socket(
            socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM
        )
        sock.settimeout(self.timeout)
        try:
            sock.connect((self.mac, self.channel))
        except Exception:
            sock.close()
            raise
        self._sock = sock

    def disconnect(self) -> None:
        if self._sock is not None:
            try:
                self._sock.close()
            finally:
                self._sock = None

    def send(self, data: bytes) -> None:
        if self._sock is None:
            raise RuntimeError("transporte no conectado")
        self._sock.sendall(data)

    def receive(self, timeout: Optional[float] = None) -> bytes:
        if self._sock is None:
            raise RuntimeError("transporte no conectado")
        previous = self._sock.gettimeout()
        if timeout is not None:
            self._sock.settimeout(timeout)
        try:
            return self._sock.recv(4096)
        except socket.timeout:
            raise TimeoutError from None
        finally:
            self._sock.settimeout(previous)

    def _timeout(self) -> Optional[float]:
        if self._sock is None:
            return None
        return self._sock.gettimeout()

    @property
    def connected(self) -> bool:
        return self._sock is not None