import unittest

from opennothing.errors import ChecksumError, ProtocolError
from opennothing.protocol.constants import CRC_APP, CRC_DEVICE, Command
from opennothing.protocol.packet import build, frame_length, parse


class BuildParseTests(unittest.TestCase):
    def test_build_matches_captured_request(self):
        # Golden vector verificado (crc_final_check.py): write ANC de la app.
        raw = build(Command.SET_ANC, b"\x01\x07\x00", seq=0xCB)
        self.assertEqual(
            raw,
            bytes.fromhex("5560010ff00300cb010700c5af"),
        )

    def test_build_matches_capture_664(self):
        raw = build(Command.READ_ANC, b"\x03", seq=0x0D)
        self.assertEqual(raw, bytes.fromhex("5560011ec001000d039989"))

    def test_roundtrip_request_app_scope(self):
        raw = build(Command.READ_ANC, b"\x03", seq=0x0D, crc_scope=CRC_APP)
        packet = parse(raw, crc_scope=CRC_APP)
        self.assertEqual(packet.command, 0xC01E)
        self.assertEqual(packet.payload, b"\x03")
        self.assertEqual(packet.seq, 0x0D)
        self.assertIs(packet.crc_ok, True)

    def test_asimetria_crc_app_vs_device(self):
        # Mismo comando y payload: app y dispositivo usan alcances distintos.
        request = build(Command.SET_ANC, b"", seq=0xD5, crc_scope=CRC_APP)
        device_reply = build(0x700F, b"", seq=0xD5, crc_scope=CRC_DEVICE)
        # Con payload vacio el dispositivo emite CRC 0xFFFF...
        self.assertEqual(device_reply, bytes.fromhex("5560010f700000d5ffff"))
        # ...mientras que la app NO (su CRC cubre la cabecera).
        self.assertNotEqual(request, device_reply)
        # Cada una valida solo con el scope que la genero.
        self.assertIs(parse(request, crc_scope=CRC_APP).crc_ok, True)
        self.assertIs(parse(device_reply, crc_scope=CRC_DEVICE).crc_ok, True)
        # Y fracasa con el scope del otro (prueba de la asimetria).
        with self.assertRaises(ChecksumError):
            parse(request, crc_scope=CRC_DEVICE)
        with self.assertRaises(ChecksumError):
            parse(device_reply, crc_scope=CRC_APP)

    def test_checksum_error_on_tamper(self):
        raw = build(Command.READ_FIRMWARE, b"1.0.1.74", seq=1, crc_scope=CRC_APP)
        mangled = raw[:-1] + bytes((raw[-1] ^ 0xFF,))
        with self.assertRaises(ChecksumError):
            parse(mangled, crc_scope=CRC_APP)

    def test_bad_sof(self):
        with self.assertRaises(ProtocolError):
            frame_length(b"\x56" + bytes(7))

    def test_truncated(self):
        raw = build(Command.READ_ANC, b"\x03", seq=0x0D)
        self.assertIsNone(frame_length(raw[:4]))
        with self.assertRaises(ProtocolError):
            parse(raw[:7])

    def test_incomplete_frame_in_buffer(self):
        raw = build(Command.READ_ANC, b"\x03", seq=0x0D)
        self.assertEqual(frame_length(raw[:8]), 8 + 1 + 2)
        with self.assertRaises(ProtocolError):
            parse(raw[:8])

    def test_event_no_crc(self):
        # Push capturado: control 0x0100, SIN CRC, payload del reporte ANC.
        raw = bytes.fromhex("55000103e0030000010700")
        packet = parse(raw)
        self.assertEqual(packet.control, 0x0100)
        self.assertEqual(packet.command, 0xE003)
        self.assertEqual(packet.payload, b"\x01\x07\x00")
        self.assertIs(packet.has_crc, False)
        self.assertIsNone(packet.crc_ok)


if __name__ == "__main__":
    unittest.main()