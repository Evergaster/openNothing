"""Facade: un objeto que ata transporte + sesion + dispositivo.

Uso tipico:

    with CMFBudsController.connect(mac="2C:BE:EE:70:76:30", model="B172") as buds:
        status = buds.get_status()
        print(status)
        buds.set_anc_mode("transparency")
"""

from typing import Optional

from opennothing.device import BudsDevice, create_device
from opennothing.protocol.constants import DEFAULT_CHANNEL, DEFAULT_MAC, DEFAULT_TIMEOUT
from opennothing.protocol.models import DeviceStatus
from opennothing.session import ProtocolSession
from opennothing.transport import RfcommTransport, ScriptedTransport


class CMFBudsController:
    def __init__(self, device: BudsDevice, session: ProtocolSession):
        self.device = device
        self.session = session

    @classmethod
    def connect(
        cls,
        mac: str = DEFAULT_MAC,
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