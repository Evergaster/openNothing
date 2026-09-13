"""Sesion de protocolo: secuencia, framing, CRC y eventos.

Depende solo de la interfaz `Transport`; media entre bytes crudos y paquetes.
"""

import time
from collections import deque
from typing import Deque, Iterator, Optional

from opennothing.errors import ConnectionLost, NotConnectedError, Timeout
from opennothing.protocol.constants import CRC_APP, CRC_DEVICE, DEFAULT_TIMEOUT, MASK_REQUEST
from opennothing.protocol.packet import Packet, build, frame_length, parse


class ProtocolSession:
    def __init__(
        self,
        transport,
        timeout: float = DEFAULT_TIMEOUT,
        rx_crc_scope: str = CRC_DEVICE,
    ):
        self._transport = transport
        self._timeout = timeout
        self._rx_crc_scope = rx_crc_scope
        self._seq = 0
        self._rx_buffer = b""
        self._events: Deque[Packet] = deque()

    def connect(self) -> None:
        self._transport.connect()
        self._seq = 0
        self._rx_buffer = b""
        self._events.clear()

    def disconnect(self) -> None:
        self._transport.disconnect()

    def __enter__(self) -> "ProtocolSession":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.disconnect()

    @property
    def connected(self) -> bool:
        return getattr(self._transport, "connected", False)

    @property
    def events_queue_size(self) -> int:
        return len(self._events)

    def drain_events(self) -> list:
        """Drena en vez de escuchar: solo lo ya recibido, sin bloquear."""
        for packet in self._drain():
            self._events.append(packet)
        pending = list(self._events)
        self._events.clear()
        return pending

    def request(
        self,
        command: int,
        payload: bytes = b"",
        reply: Optional[int] = None,
    ) -> Packet:
        """Envia un comando y espera su respuesta (por defecto response_of)."""
        self._ensure_connected()
        if reply is None:
            reply = command & 0x7FFF
        self._seq = (self._seq + 1) & 0xFF
        raw = build(command, payload, self._seq, crc_scope=CRC_APP)
        self._transport.send(raw)
        return self._read_until(reply)

    def poll_events(self) -> Iterator[Packet]:
        """Escucha eventos no solicitados (pushes) de forma bloqueante.

        Consume primero lo ya recibido; luego hace receive() esperando mas
        datos. Termina cuando el transporte se detiene o cierra la conexion.
        """
        self._ensure_connected()
        while True:
            for packet in self._drain():
                self._events.append(packet)
            if self._events:
                yield self._events.popleft()
                continue
            try:
                chunk = self._transport.receive(self._timeout)
            except TimeoutError:
                continue
            if not chunk:
                return
            self._rx_buffer += chunk

    def _ensure_connected(self) -> None:
        if not self.connected:
            raise NotConnectedError("no hay sesion conectada")

    def _drain(self) -> Iterator[Packet]:
        """Extrae todas las tramas completas que ya haya en el buffer."""
        while True:
            packet = self._next_from_buffer()
            if packet is None:
                return
            yield packet

    def _next_from_buffer(self) -> Optional[Packet]:
        size = frame_length(self._rx_buffer)
        if size is None:
            return None
        if size > len(self._rx_buffer):
            return None
        raw = self._rx_buffer[:size]
        self._rx_buffer = self._rx_buffer[size:]
        return parse(raw, crc_scope=self._rx_crc_scope, validate=True)

    def _read_until(self, expected: int) -> Packet:
        deadline = time.monotonic() + self._timeout
        while True:
            for packet in self._drain():
                if packet.command == expected:
                    return packet
                self._events.append(packet)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise Timeout(f"sin respuesta 0x{expected:04x} (timeout)")
            try:
                chunk = self._transport.receive(remaining)
            except TimeoutError:
                raise Timeout(f"sin respuesta 0x{expected:04x} (timeout)") from None
            if not chunk:
                raise ConnectionLost("el dispositivo cerro la conexion")
            self._rx_buffer += chunk