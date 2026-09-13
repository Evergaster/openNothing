"""openNothing: control de audifonos Nothing/CMF (SPP/RFCOMM).

Paquete por capas:

    transport   I/O de bytes (RFCOMM real / simulado)
    session     secuencia, framing, CRC, eventos
    device      API tipada por modelo
    controller  facade de un solo punto de entrada
"""

from opennothing.controller import CMFBudsController
from opennothing.errors import (
    ChecksumError,
    ConnectionLost,
    NotConnectedError,
    OpenNothingError,
    ProtocolError,
    Timeout,
    UnknownValueError,
)
from opennothing.protocol.constants import DEFAULT_CHANNEL, DEFAULT_TIMEOUT

__version__ = "0.1.0"

__all__ = [
    "CMFBudsController",
    "ChecksumError",
    "ConnectionLost",
    "NotConnectedError",
    "OpenNothingError",
    "ProtocolError",
    "Timeout",
    "UnknownValueError",
    "DEFAULT_CHANNEL",
    "DEFAULT_TIMEOUT",
    "__version__",
]