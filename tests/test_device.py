import unittest

from opennothing.device import CmfBudsPro2, create_device
from opennothing.protocol.constants import Command
from opennothing.protocol.enums import AncMode
from opennothing.session import ProtocolSession
from opennothing.transport.fake import ScriptedTransport


def _device(replies):
    transport = ScriptedTransport(replies)
    transport.connect()
    session = ProtocolSession(transport)
    session.connect()
    return CmfBudsPro2(session), transport


class DeviceTests(unittest.TestCase):
    def test_read_anc(self):
        buds, _ = _device({Command.READ_ANC: bytes.fromhex("020100010500")})
        report = buds.read_anc()
        self.assertIs(report.mode, AncMode.OFF)

    def test_read_battery(self):
        buds, _ = _device({Command.READ_BATTERY: bytes.fromhex("0202640364")})
        reading = buds.read_battery()
        self.assertEqual(reading.named(), {"left": 100, "right": 100})

    def test_read_firmware_and_model(self):
        buds, _ = _device(
            {
                Command.READ_FIRMWARE: b"1.0.1.74",
                Command.READ_DEVICE_MODEL: b"B172",
            }
        )
        self.assertEqual(buds.read_firmware().version, "1.0.1.74")
        self.assertEqual(buds.read_device_model(), "B172")

    def test_read_low_latency_and_boost(self):
        buds, _ = _device(
            {
                Command.READ_LOW_LATENCY: b"\x01",
                Command.READ_BASS_BOOST: b"\x01\x0a",
                Command.READ_SPATIAL_AUDIO: b"\x01\x00",
            }
        )
        self.assertTrue(buds.read_low_latency().enabled)
        self.assertEqual(buds.read_bass_boost().level, 10)
        self.assertTrue(buds.read_spatial_audio().enabled)

    def test_set_anc_confirmed(self):
        buds, transport = _device(
            {
                Command.SET_ANC: b"",
                Command.READ_ANC: b"\x01\x07\x00",
            }
        )
        result = buds.set_anc_mode(AncMode.TRANSPARENCY, settle=0)
        self.assertTrue(result.acknowledged)
        self.assertTrue(result.confirmed)
        self.assertEqual(transport.sent[0][0], Command.SET_ANC)
        self.assertEqual(transport.sent[0][1], b"\x01\x07\x00")

    def test_set_anc_not_confirmed_when_mode_differs(self):
        buds, _ = _device(
            {
                Command.SET_ANC: b"",
                Command.READ_ANC: b"\x01\x07\x02",  # el dispositivo aplico "medio"
            }
        )
        result = buds.set_anc_mode(AncMode.HIGH, settle=0)
        self.assertTrue(result.acknowledged)
        self.assertFalse(result.confirmed)

    def test_set_anc_readback_present_when_mode_differs(self):
        buds, _ = _device(
            {Command.SET_ANC: b"", Command.READ_ANC: b"\x01\x07\x00"}
        )
        result = buds.set_anc_mode(AncMode.OFF, settle=0)
        self.assertFalse(result.confirmed)
        self.assertIsNotNone(result.readback)

    def test_set_bass_boost_keeps_current_level(self):
        buds, transport = _device(
            {
                Command.READ_BASS_BOOST: b"\x01\x0a",
                Command.SET_BASS_BOOST: b"",
            }
        )
        result = buds.set_bass_boost(True)
        self.assertTrue(result.confirmed)
        # el request de SET preserva el nivel leido (10) al activarlo
        set_calls = [s for s in transport.sent if s[0] == Command.SET_BASS_BOOST]
        self.assertEqual(set_calls[-1][1], b"\x01\x0a")

    def test_set_eq_custom(self):
        buds, transport = _device(
            {
                Command.SET_ADVANCED_EQ_MODE: b"",
                Command.READ_ADVANCED_EQ_MODE: b"\x01",
                Command.SET_ADVANCED_EQ_VALUES: b"",
                Command.READ_ADVANCED_EQ_VALUES: bytes.fromhex("0206090b0a060401"),
            }
        )
        result = buds.set_custom_eq((-4, 0, 3, 5, 4, 0, -2, -5))
        self.assertTrue(result.acknowledged)
        self.assertTrue(result.confirmed)

    def test_create_device_via_registry(self):
        transport = ScriptedTransport()
        transport.connect()
        session = ProtocolSession(transport)
        session.connect()
        device = create_device("B172", session)
        self.assertIsInstance(device, CmfBudsPro2)

    def test_unknown_model_raises(self):
        transport = ScriptedTransport()
        transport.connect()
        session = ProtocolSession(transport)
        session.connect()
        with self.assertRaises(KeyError):
            create_device("NO_EXISTE", session)


if __name__ == "__main__":
    unittest.main()