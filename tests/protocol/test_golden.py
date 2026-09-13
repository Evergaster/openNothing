import unittest

from opennothing.protocol.constants import CRC_APP
from opennothing.protocol.packet import parse


class GoldenVectorsTests(unittest.TestCase):
    """Tramas reales capturadas del canal 15 (CMF Buds Pro 2)."""

    def test_read_supported_features_request(self):
        # 55 60 01 1e c0 01 00 0d | 03 | 99 89
        frame = bytes.fromhex("5560011ec001000d039989")
        packet = parse(frame, crc_scope=CRC_APP)
        self.assertEqual(packet.command, 0xC01E)
        self.assertEqual(packet.payload, b"\x03")
        self.assertEqual(packet.seq, 0x0D)
        self.assertIs(packet.crc_ok, True)

    def test_anc_write_request(self):
        # Creada con la app oficial y capturada byte a byte (blog RE + verificada).
        frame = bytes.fromhex("5560010ff00300cb010700c5af")
        packet = parse(frame, crc_scope=CRC_APP)
        self.assertEqual(packet.command, 0xF00F)
        self.assertEqual(packet.payload, b"\x01\x07\x00")
        self.assertIs(packet.crc_ok, True)

    def test_anc_event_push(self):
        # Push (control 0x0100) sin CRC con el reporte de modo ANC.
        frame = bytes.fromhex("55000103e0030000010700")
        packet = parse(frame)
        self.assertEqual(packet.command, 0xE003)
        self.assertIs(packet.has_crc, False)


if __name__ == "__main__":
    unittest.main()