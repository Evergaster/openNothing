import unittest

from opennothing.protocol.enums import AncMode, EqPreset
from opennothing.protocol.models import AncReport, BatteryReading, DeviceStatus, Firmware
from opennothing.protocol.codec import (
    decode_anc_report,
    decode_advanced_eq,
    decode_bass_boost,
    decode_battery,
    decode_eq,
    decode_firmware,
    decode_low_latency,
    decode_spatial_audio,
    encode_anc_read,
    encode_anc_write,
    encode_bass_boost,
    encode_custom_eq,
    encode_eq_write,
    encode_find_device,
    encode_low_latency,
    encode_spatial_audio,
    encode_utc_time,
)


class CodecTests(unittest.TestCase):
    def test_anc_report_golden(self):
        # Respuesta capturada real (cap#668) al READ_ANC: grupos {2:1, 1:5},
        # modo en el grupo 1 = 5 -> desactivado.
        report = decode_anc_report(bytes.fromhex("020100010500"))
        self.assertIs(report.mode, AncMode.OFF)
        self.assertEqual(report.as_dict(), {2: 1, 1: 5})

    def test_decode_push_anc(self):
        from opennothing.protocol.codec import decode_push_anc

        self.assertIs(decode_push_anc(b"\x01\x07\x00"), AncMode.TRANSPARENCY)

    def test_anc_read_write_payloads(self):
        self.assertEqual(encode_anc_read(), b"\x03")
        self.assertEqual(encode_anc_write(AncMode.TRANSPARENCY), b"\x01\x07\x00")

    def test_battery_golden(self):
        # Captura real: 02 02 64 03 64 -> izq 100%, der 100%.
        battery = decode_battery(bytes.fromhex("0202640364"))
        self.assertEqual(battery.named(), {"left": 100, "right": 100})

    def test_firmware_ascii(self):
        fw = decode_firmware(b"1.0.1.74\x00\x00")
        self.assertEqual(fw.version, "1.0.1.74")

    def test_low_latency(self):
        self.assertTrue(decode_low_latency(b"\x01").enabled)
        self.assertFalse(decode_low_latency(b"\x02").enabled)
        self.assertEqual(encode_low_latency(True), b"\x01")
        self.assertEqual(encode_low_latency(False), b"\x02")

    def test_bass_boost(self):
        self.assertTrue(decode_bass_boost(b"\x01\x0a").enabled)
        self.assertEqual(decode_bass_boost(b"\x01\x0a").level, 10)
        self.assertEqual(encode_bass_boost(True, 10), b"\x01\x0a")
        self.assertEqual(encode_bass_boost(True, 20), b"\x01\x0a")
        self.assertEqual(encode_bass_boost(True, -3), b"\x01\x00")

    def test_spatial_audio(self):
        spatial = decode_spatial_audio(b"\x01\x00")
        self.assertTrue(spatial.enabled)
        self.assertEqual(encode_spatial_audio(True, None), b"\x01")
        self.assertEqual(encode_spatial_audio(True, False), b"\x01\x00")

    def test_eq(self):
        self.assertIs(decode_eq(b"\x01").preset, EqPreset.MORE_BASS)
        self.assertEqual(encode_eq_write(EqPreset.CUSTOM), b"\x04")

    def test_custom_eq_offset(self):
        bands = (-4, 0, 3, 5, 4, 0, -2, -5)
        raw = encode_custom_eq(bands)
        self.assertEqual(raw, bytes.fromhex("0206090b0a060401"))
        decoded = decode_advanced_eq(raw).gains_db
        self.assertEqual(tuple(decoded), bands)

    def test_find_device(self):
        self.assertEqual(encode_find_device(0x05, True), b"\x01")
        self.assertEqual(encode_find_device(0x05, False), b"\x00")
        self.assertEqual(encode_find_device(0x02, True), b"\x02\x01")

    def test_utc_time_le(self):
        payload = encode_utc_time(0x60FB0F30)
        self.assertEqual(payload, bytes.fromhex("300ffb60"))

    def test_device_status_dict(self):
        status = DeviceStatus(
            anc=decode_anc_report(bytes.fromhex("020100010500")),
            battery=BatteryReading(levels=((2, 100), (3, 100))),
            firmware=Firmware(raw=b"1.0.1.74", version="1.0.1.74"),
            model="B172",
        )
        data = status.as_dict()
        self.assertEqual(data["anc"]["mode"], 5)
        self.assertEqual(data["battery"], {"left": 100, "right": 100})
        self.assertEqual(data["model"], "B172")


if __name__ == "__main__":
    unittest.main()