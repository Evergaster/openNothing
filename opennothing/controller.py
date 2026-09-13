"""Facade: un objeto que ata transporte + sesion + dispositivo.

Uso tipico (la MAC se detecta automaticamente):

    with CMFBudsController.connect(model="B172") as buds:
        status = buds.get_status()
        print(status)
        buds.set_anc_mode("transparency")
"""

from typing import Optional

from opennothing.device import BudsDevice, create_device
from opennothing.errors import OpenNothingError
from opennothing.protocol.constants import DEFAULT_CHANNEL, DEFAULT_TIMEOUT
from opennothing.protocol.models import DeviceStatus
from opennothing.session import ProtocolSession
from opennothing.transport import RfcommTransport, ScriptedTransport


def _looks_like_buds(name: str, model: str) -> bool:
    """Heuristica: el nombre sugiere unos buds Nothing/CMF."""
    lower = name.lower()
    return "cmf" in lower or "nothing" in lower or model.upper() in name.upper()


def discover_default_mac(model: str = "B172") -> str:
    """Detecta la MAC de los buds via BlueZ sin depender de la MAC del usuario.

    Lista los dispositivos emparejados con ``bluetoothctl`` y devuelve el
    unico candidato tipo Nothing/CMF. Si hay cero o varios, lanza
    :class:`OpenNothingError` con una pista accionable.
    """
    import subprocess

    try:
        out = subprocess.run(
            ["bluetoothctl", "devices"],
            capture_output=True, text=True, timeout=10,
        )
    except FileNotFoundError as exc:
        raise OpenNothingError(
            "no se encontro 'bluetoothctl' (bluez).\n"
            "Instala bluez:  sudo apt install bluez"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise OpenNothingError(
            "bluetoothctl tardo demasiado en responder"
        ) from exc

    candidates = []
    for line in (out.stdout or "").splitlines():
        parts = line.split(None, 2)
        if len(parts) == 3 and parts[0] == "Device":
            mac, name = parts[1], parts[2]
            if _looks_like_buds(name, model):
                candidates.append((mac, name))

    if not candidates:
        raise OpenNothingError(
            "no se detecto ningun dispositivo Nothing/CMF emparejado.\n"
            "Empareja los buds por Bluetooth y reintenta, o pasa --mac."
        )
    if len(candidates) > 1:
        listed = "\n".join(f"  {m}  {n}" for m, n in candidates)
        raise OpenNothingError(
            "varios dispositivos compatibles detectados:\n"
            + listed
            + "\nUsa --mac para elegir cual."
        )
    return candidates[0][0]


class CMFBudsController:
    def __init__(self, device: BudsDevice, session: ProtocolSession):
        self.device = device
        self.session = session

    @classmethod
    def connect(
        cls,
        mac: Optional[str] = None,
        channel: int = DEFAULT_CHANNEL,
        timeout: float = DEFAULT_TIMEOUT,
        model: str = "B172",
        scripted: bool = False,
    ) -> "CMFBudsController":
        if scripted:
            transport = ScriptedTransport()
            transport.connect()
            session = ProtocolSession(transport, timeout=timeout)
            return cls(create_device(model, session), session)
        if mac is None:
            mac = discover_default_mac(model)
        session = ProtocolSession(
            RfcommTransport(mac, channel, timeout), timeout
        )
        device = create_device(model, session)
        controller = cls(device, session)
        controller.session.connect()
        return controller

    def get_status(self) -> DeviceStatus:
        return DeviceStatus(
            anc=self.device.read_anc(),
            battery=self.device.read_battery(),
            firmware=self.device.read_firmware(),
            model=self.device.read_device_model(),
        )

    # re-expone la API del dispositivo tipada
    def __getattr__(self, name: str):
        return getattr(self.device, name)

    def close(self) -> None:
        self.session.disconnect()

    def __enter__(self) -> "CMFBudsController":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()