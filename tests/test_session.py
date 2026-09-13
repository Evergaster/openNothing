import unittest

from opennothing.errors import NotConnectedError, Timeout
from opennothing.protocol.constants import CRC_DEVICE, Command
from opennothing.protocol.packet import parse
from opennothing.session import ProtocolSession
from opennothing.transport.fake import ScriptedTransport


class SessionTests(unittest.TestCase):
    def _make(self, **kwargs):
        self.transport = ScriptedTransport()
        return ProtocolSession(self.transport, **kwargs)

    def test_request_reply_command_and_seq(self):
        session = self._make()
        session.connect()
        self.transport.on(Command.READ_ANC, b"\x03\x01\x07")
        packet = session.request(Command.READ_ANC, b"\x03")
        self.assertEqual(packet.command, 0x401E)
        self.assertEqual(packet.payload, b"\x03\x01\x07")
        self.assertEqual(self.transport.sent[0][2], 1)
        self.assertEqual(packet.seq, 1)

    def test_seq_wraps(self):
        session = self._make()
        session.connect()
        self.transport.on(Command.READ_FIRMWARE, b"1.0.1.74")
        for _ in range(300):
            session.request(Command.READ_FIRMWARE)
        self.assertEqual(self.transport.sent[-1][2], 300 & 0xFF)

    def test_ack_empty_payload(self):
        session = self._make()
        session.connect()
        self.transport.on(Command.SET_UTC_TIME, b"")
        ack = session.request(Command.SET_UTC_TIME, b"\x00\x00\x00\x00")
        self.assertEqual(ack.payload, b"")
        self.assertIs(ack.crc_ok, True)

    def test_events_are_preserved_across_requests(self):
        session = self._make()
        session.connect()
        self.transport.inject(Command.PUSH_ANC, b"\x01\x07\x00", seq=0)
        self.transport.on(Command.READ_FIRMWARE, b"1.0.1.74")
        session.request(Command.READ_FIRMWARE)
        events = session.drain_events()
        self.assertEqual([e.command for e in events], [Command.PUSH_ANC])

    def test_poll_events_blocking_and_stop(self):
        session = self._make()
        session.connect()
        self.transport.inject(Command.PUSH_BATTERY, b"\x02\x02\x64\x03\x64", seq=0)
        events = session.poll_events()
        first = next(events)
        self.assertEqual(first.command, Command.PUSH_BATTERY)
        self.transport.disconnect()
        with self.assertRaises(StopIteration):
            next(events)

    def test_timeout_raises(self):
        transport = ScriptedTransport(auto_reply=False)
        transport.connect()
        session = ProtocolSession(transport, timeout=0.3)
        session.connect()
        with self.assertRaises(Timeout):
            session.request(0xC042)

    def test_request_without_connection(self):
        session = self._make()
        session.connect()
        session.disconnect()
        with self.assertRaises(NotConnectedError):
            session.request(Command.READ_FIRMWARE)

    def test_frames_split_across_receives(self):
        # Tramas de dispositivo fragmentadas a niveles de bytes deben
        # ensamblarse, clasificarse y entregarse sin confundirse.
        from opennothing.protocol.packet import build

        a_reply = build(0x400E, b"\x01\x02", seq=1, crc_scope=CRC_DEVICE)
        b_reply = build(0x401E, b"\x03\x01\x07", seq=2, crc_scope=CRC_DEVICE)

        transport = ScriptedTransport()
        transport.connect()
        session = ProtocolSession(transport)
        session.connect()

        half = 3
        transport.feed_bytes(a_reply[:half])
        transport.feed_bytes(a_reply[half:])
        transport.feed_bytes(b_reply[:half])
        transport.feed_bytes(b_reply[half:])

        packet = session.request(Command.READ_ANC, b"\x03", reply=0x401E)
        self.assertEqual(packet.command, 0x401E)
        self.assertEqual(packet.payload, b"\x03\x01\x07")
        events = session.drain_events()
        self.assertEqual([e.command for e in events], [0x400E])


if __name__ == "__main__":
    unittest.main()