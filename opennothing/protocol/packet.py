"""Codificacion y parseo de tramas del protocolo Nothing/CMF.

Formato de trama:

    [0x55] [control.2.LE] [cmd.2.LE] [len.2.LE] [fsn] [payload] [crc.2.LE]

- Los requests de la app usan control 0x0160 y CRC sobre cabecera + payload.
- Las respuestas del dispositivo usan CRC sobre el payload solamente.
- Los eventos no solicitados usan control 0x0100 y no llevan CRC.
"""

from dataclasses import dataclass
from typing import Optional

from opennothing.errors import ChecksumError, ProtocolError
from opennothing.protocol.constants import (
    CRC_APP,
    CRC_DEVICE,
    CTRL_REQUEST,
    MASK_CRC,
    MASK_REQUEST,
    SOF,
)
from opennothing.protocol.crc import CRC_SIZE, crc16_modbus, crc_bytes_le

HEADER_SIZE = 8


@dataclass(frozen=True)
class Packet:
    command: int
    seq: int
    payload: bytes
    control: int
    has_crc: bool
    crc_stored: Optional[int] = None
    crc_ok: Optional[bool] = None

    @property
    def is_reply(self) -> bool:
        return not bool(self.command & MASK_REQUEST)


def _compute_crc(frame: bytes, plen: int, crc_scope: str) -> int:
    """CRC con el alcance correcto segun quien firma la trama.

    - App: cabecera + payload (sin contar los bytes de CRC almacenados).
    - Dispositivo: solo el payload.
    """
    if crc_scope == CRC_APP:
        crc_data = frame[: HEADER_SIZE + plen]
    elif crc_scope == CRC_DEVICE:
        crc_data = frame[HEADER_SIZE : HEADER_SIZE + plen]
    else:
        raise ProtocolError(f"crc_scope desconocido: {crc_scope!r}")
    return crc16_modbus(crc_data)


def build(
    command: int,
    payload: bytes = b"",
    seq: int = 0,
    control: int = CTRL_REQUEST,
    crc_scope: str = CRC_APP,
) -> bytes:
    """Serializa un request en el formato de la app (CRC sobre header+payload)."""
    payload = bytes(payload)
    header = bytes(
        (
            SOF,
            control & 0xFF,
            (control >> 8) & 0xFF,
            command & 0xFF,
            (command >> 8) & 0xFF,
            len(payload) & 0xFF,
            (len(payload) >> 8) & 0xFF,
            seq & 0xFF,
        )
    )
    body = header + payload
    if crc_scope == CRC_APP:
        crc = crc16_modbus(body)
    elif crc_scope == CRC_DEVICE:
        crc = crc16_modbus(payload)
    else:
        raise ProtocolError(f"crc_scope desconocido: {crc_scope!r}")
    return body + crc_bytes_le(crc)


def frame_length(data: bytes) -> Optional[int]:
    """Longitud total de la primera trama en `data`, o None si falta.

    Requiere al menos los 8 bytes de cabecera.
    """
    if len(data) < HEADER_SIZE:
        return None
    if data[0] != SOF:
        raise ProtocolError(f"SOF invalido: 0x{data[0]:02x}")
    plen = data[5] | (data[6] << 8)
    has_crc = bool(data[1] & MASK_CRC)
    return HEADER_SIZE + plen + (CRC_SIZE if has_crc else 0)


def parse(
    data: bytes,
    crc_scope: str = CRC_DEVICE,
    validate: bool = True,
) -> Packet:
    """Decodifica una trama completa (debe caber entera en `data`)."""
    size = frame_length(data)
    if size is None:
        raise ProtocolError("trama trunca (< 8 bytes)")
    if len(data) < size:
        raise ProtocolError(
            f"trama incompleta: {len(data)}/{size} bytes disponibles"
        )
    frame = data[:size]
    plen = frame[5] | (frame[6] << 8)
    control = frame[1] | (frame[2] << 8)
    has_crc = bool(control & MASK_CRC)
    crc_stored = None
    crc_ok = None
    if has_crc:
        crc_stored = frame[-2] | (frame[-1] << 8)
        computed = _compute_crc(frame, plen, crc_scope)
        crc_ok = computed == crc_stored
        if validate and not crc_ok:
            raise ChecksumError(
                f"CRC invalido: esperado 0x{crc_stored:04x}, "
                f"recomputed 0x{computed:04x}"
            )
    return Packet(
        command=frame[3] | (frame[4] << 8),
        seq=frame[7],
        payload=frame[HEADER_SIZE : HEADER_SIZE + plen],
        control=control,
        has_crc=has_crc,
        crc_stored=crc_stored,
        crc_ok=crc_ok,
    )