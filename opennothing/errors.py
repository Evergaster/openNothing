class OpenNothingError(Exception):
    """Base de todos los errores de openNothing."""


class ProtocolError(OpenNothingError):
    """Trama malformada, SOF invalido, sincronizacion perdida."""


class ChecksumError(ProtocolError):
    """El CRC de una respuesta del dispositivo no es valido."""


class Timeout(OpenNothingError):
    """No llego la respuesta esperada dentro del plazo."""


class ConnectionLost(OpenNothingError):
    """El transporte reporto cierre de la conexion."""


class NotConnectedError(OpenNothingError):
    """Se pidio una operacion sin sesion activa."""


class UnknownValueError(ValueError):
    """Valor de dominio (modo ANC, preset EQ, lado) no reconocido."""