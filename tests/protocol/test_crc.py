import unittest

from opennothing.protocol.crc import crc16_modbus, crc_bytes_le


class CrcTests(unittest.TestCase):
    def test_check_value_standard(self):
        # Valor canonico de verificacion CRC-16/MODBUS para "123456789".
        self.assertEqual(crc16_modbus(b"123456789"), 0x4B37)

    def test_empty_payload(self):
        # El CRC de un payload vacio es 0xFFFF; el dispositivo lo usa en los
        # Acks de escritura (CRC solo sobre el payload vacio).
        self.assertEqual(crc16_modbus(b""), 0xFFFF)

    def test_little_endian(self):
        self.assertEqual(crc_bytes_le(0xFFFF), b"\xff\xff")
        self.assertEqual(crc_bytes_le(0xAFC5), b"\xc5\xaf")
        self.assertEqual(crc_bytes_le(0x8999), b"\x99\x89")

    def test_golden_blog_anc_write(self):
        # Captura del RE blog de Nothing Ear(2): write 0xF00F mode=07,
        # CRC de la app sobre cabecera + payload = int 0xAFC5.
        frame = bytes.fromhex("5560010ff00300cb010700")
        self.assertEqual(crc16_modbus(frame), 0xAFC5)

    def test_golden_capture_read_anc(self):
        # Captura real (cap#664): 0xC01E con payload [03], CRC cabecera+payload.
        frame = bytes.fromhex("5560011ec001000d03")
        self.assertEqual(crc16_modbus(frame), 0x8999)

    def test_golden_device_reply_payload_only(self):
        # Cap#668: la respuesta 0x401E verifica SOLO contra el payload.
        payload = bytes.fromhex("020100010500")
        self.assertEqual(crc16_modbus(payload), 0xA96E)
        header_and_payload = bytes.fromhex("5560011e4006000d020100010500")
        self.assertNotEqual(crc16_modbus(header_and_payload), 0xA96E)


if __name__ == "__main__":
    unittest.main()