"""Transporte de bytes: abstraccion sobre el canal RFCOMM.

La sesion solo conoce esta interfaz, por lo que se puede sustituir por un
transporte simulado en tests sin tocar el resto de la pila.
"""

from abc import ABC, abstractmethod
from typing import Optional


class Transport(ABC):
    name = "base"

    @abstractmethod
    def connect(self) -> None:
        """Abre el canal. Debe ser idempotente si ya esta abierto."""

    @abstractmethod
    def disconnect(self) -> None:
        """Cierra el canal. Debe ser seguro si ya esta cerrado."""

    @abstractmethod
    def send(self, data: bytes) -> None:
        """Envia una trama completa al dispositivo."""

    @abstractmethod
    def receive(self, timeout: Optional[float] = None) -> bytes:
        """Devuelve un trozo de datos recibido (bloqueante con plazo).

        Devuelve b"" solo cuando el dispositivo cerro la conexion y levanta
        `TimeoutError` si transcurre `timeout` sin datos.
        """

    @property
    @abstractmethod
    def connected(self) -> bool:
        """True mientras el canal este abierto."""

    # Optional para los casos que no lo expongan.
    def _timeout(self) -> Optional[float]:
        return None

    def __enter__(self) -> "Transport":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.disconnect()