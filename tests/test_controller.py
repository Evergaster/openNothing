import unittest

from opennothing import CMFBudsController
from opennothing.protocol.constants import Command
from opennothing.session import ProtocolSession
from opennothing.transport.fake import ScriptedTransport


class ControllerTests(unittest.TestCase):
    def test_get_status_facade(self):
        transport = ScriptedTransport(
            {
                Command.READ_ANC: bytes.fromhex("020100010500"),
                Command.READ_BATTERY: bytes.fromhex("0202640364"),
                Command.READ_FIRMWARE: b"1.0.1.74",
                Command.READ_DEVICE_MODEL: b"B172",
            }
        )
        transport.connect()
        session = ProtocolSession(transport)
        session.connect()
        controller = CMFBudsController(
            device=__import__("opennothing.device", fromlist=["create_device"]).create_device(
                "B172", session
            ),
            session=session,
        )
        status = controller.get_status()
        self.assertEqual(status.model, "B172")
        self.assertEqual(status.firmware.version, "1.0.1.74")
        self.assertEqual(status.battery.named(), {"left": 100, "right": 100})
        self.assertEqual(status.anc.mode_name, "desactivado")

    def test_connect_scripted_defaults(self):
        # La fabrica scripted conecta toda la pila sin hardware: el transporte
        # simulado responde a todo, asi que el estado queda "vacio" pero valido.
        controller = CMFBudsController.connect(model="B172", scripted=True)
        status = controller.get_status()
        self.assertIsNotNone(status.firmware)
        controller.close()

    def test_delegates_to_device(self):
        transport = ScriptedTransport(
            {Command.READ_ANC: b"\x01\x07\x00"}
        )
        transport.connect()
        session = ProtocolSession(transport)
        session.connect()
        from opennothing.device import create_device

        controller = CMFBudsController(device=create_device("B172", session), session=session)
        report = controller.read_anc()
        self.assertEqual(report.mode_name, "transparencia")


if __name__ == "__main__":
    unittest.main()