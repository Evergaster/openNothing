"""Transporte simulado: responde de forma determinista para tests y demos.

Convierte cada peticion recibida en una respuesta del estilo dispositivo
(CRC sobre payload, comando = response_of(command), mismo fsn) y encola
tramas de evento inyectadas. Bloquea en receive() hasta que haya datos o el
transporte se detenga, imitando el comportamiento del socket real.
"""

import threading
from collections import deque
from typing import Deque, Dict, List, Optional, Tuple

from opennothing.protocol.constants import CRC_DEVICE, Command, response_of
from opennothing.protocol.packet import Packet, build, frame_length, parse


class ScriptedTransport:
    name = "scripted"

    def __init__(
        self,
        replies: Optional[Dict[int, bytes]] = None,
        latency: float = 0.0,
        auto_reply: bool = True,
    ):
        self._replies: Dict[int, bytes] = dict(replies or {})
        self._queue: Deque[bytes] = deque()
        self._condition = threading.Condition()
        self._stopped = False
        self.latency = latency
        self.auto_reply = auto_reply
        self.sent: List[Tuple[Command, bytes, int]] = []

    def on(self, command: int, payload: bytes) -> "ScriptedTransport":
        """Registra el payload de respuesta para un comando."""
        self._replies[command] = bytes(payload)
        return self

    def inject(self, command: int, payload: bytes = b"", seq: int = 0) -> None:
        """Encola una trama de dispositivo fabricada (p. ej. un push)."""
        raw = build(command, payload, seq, crc_scope=CRC_DEVICE)
        with self._condition:
            self._queue.append(raw)
            self._condition.notify_all()

    def clear_sent(self) -> None:
        self.sent.clear()

    def connect(self) -> None:
        with self._condition:
            self._stopped = False

    def disconnect(self) -> None:
        with self._condition:
            self._stopped = True
            self._condition.notify_all()

    def send(self, data: bytes) -> None:
        size = frame_length(data)
        if size is None:
            raise ValueError("trama de envio incompleta")
        frame = parse(data[:size], validate=False)
        self.sent.append((frame.command, frame.payload, frame.seq))
        if not self.auto_reply:
            return  # sin respuesta: se simula un dispositivo que no contesta
        reply_payload = self._replies.get(int(frame.command), b"")
        raw = build(
            response_of(frame.command), reply_payload, frame.seq,
            crc_scope=CRC_DEVICE,
        )
        with self._condition:
            self._queue.append(raw)
            self._condition.notify_all()

    def receive(self, timeout: Optional[float] = None) -> bytes:
        with self._condition:
            if not self._queue and not self._stopped:
                if timeout is None:
                    self._condition.wait()
                else:
                    self._condition.wait(timeout)
            if self._stopped:
                return b""
            if not self._queue:
                raise TimeoutError("sin datos en transporte simulado")
            return self._queue.popleft()

    def feed_bytes(self, raw: bytes) -> None:
        """Encola una trama cruda (tamano fijo), util para inyectar golden frames."""
        with self._condition:
            self._queue.append(raw)
            self._condition.notify_all()

    @property
    def connected(self) -> bool:
        with self._condition:
            return not self._stopped