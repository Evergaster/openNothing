"""CRC-16/MODBUS del protocolo Nothing/CMF.

El dispositivo aplica el CRC sobre el payload solamente, mientras que la app
oficial lo aplica sobre cabecera + payload. En ambos casos se almacena en dos
bytes little-endian.
"""

POLY = 0xA001
INIT = 0xFFFF
CRC_SIZE = 2


def crc16_modbus(data: bytes) -> int:
    crc = INIT
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ POLY
            else:
                crc >>= 1
    return crc


def crc_bytes_le(crc: int) -> bytes:
    return bytes((crc & 0xFF, (crc >> 8) & 0xFF))