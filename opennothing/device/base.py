"""Dispositivo generico: API tipada y verificada sobre la sesion.

Esta clase no conoce RFCOMM ni sockets: recibe una `ProtocolSession` ya
conectada. Las subclases solo personalizan detalles de producto (payload de
lectura ANC, codigo de producto, etc.).
"""

import time
from abc import ABC
from typing import Callable, Iterator, Optional

from opennothing.protocol.codec import (
    decode_advanced_eq,
    decode_advanced_eq_mode,
    decode_anc_report,
    decode_bass_boost,
    decode_battery,
    decode_device_model,
    decode_eq,
    decode_firmware,
    decode_low_latency,
    decode_spatial_audio,
    encode_advanced_eq_mode,
    encode_anc_read,
    encode_anc_write,
    encode_bass_boost,
    encode_custom_eq,
    encode_eq_write,
    encode_find_device,
    encode_gesture,
    encode_in_ear_detection,
    encode_low_latency,
    encode_personalized_anc,
    encode_smart_anc,
    encode_spatial_audio,
    encode_utc_time,
)
from opennothing.protocol.constants import Command, response_of
from opennothing.protocol.enums import AncMode, EqPreset, parse_anc_mode, parse_eq_preset
from opennothing.protocol.models import (
    AdvancedEq,
    AncReport,
    BassBoost,
    BatteryReading,
    EqSetting,
    Firmware,
    LowLatency,
    SpatialAudio,
    Verified,
)
from opennothing.protocol.packet import Packet
from opennothing.session import ProtocolSession

Confirm = Callable[[bytes], bool]


def _always(_: bytes) -> bool:
    return True


class BudsDevice(ABC):
    product_code = "unknown"

    def __init__(self, session: ProtocolSession):
        self.session = session

    # -- primitivas de bajo nivel -------------------------------------------

    def request(self, command: int, payload: bytes = b"") -> Packet:
        return self.session.request(command, payload, response_of(command))

    def _write_verified(
        self,
        command: int,
        payload: bytes,
        read_command: Optional[int] = None,
        settle: float = 0.0,
        confirm: Optional[Confirm] = None,
    ) -> Verified:
        ack = self.session.request(command, payload)
        acknowledged = ack.payload == b""
        if settle > 0:
            time.sleep(settle)
        readback = None
        confirmed = False
        if read_command is not None:
            try:
                packet = self.session.request(read_command, b"")
                readback = packet.payload
                confirmed = (confirm or _always)(readback)
            except Exception:
                pass
        return Verified(
            acknowledged=acknowledged,
            confirmed=confirmed,
            ack_seq=ack.seq,
            ack_crc_ok=ack.crc_ok,
            readback=readback,
        )

    # -- lecturas ------------------------------------------------------------

    def read_anc(self) -> AncReport:
        return decode_anc_report(self.request(Command.READ_ANC, self._anc_read_payload()).payload)

    def read_battery(self) -> BatteryReading:
        return decode_battery(self.request(Command.READ_BATTERY).payload)

    def read_firmware(self) -> Firmware:
        return decode_firmware(self.request(Command.READ_FIRMWARE).payload)

    def read_device_model(self) -> str:
        return decode_device_model(self.request(Command.READ_DEVICE_MODEL).payload)

    def read_low_latency(self) -> LowLatency:
        return decode_low_latency(self.request(Command.READ_LOW_LATENCY).payload)

    def read_bass_boost(self) -> BassBoost:
        return decode_bass_boost(self.request(Command.READ_BASS_BOOST).payload)

    def read_spatial_audio(self) -> SpatialAudio:
        return decode_spatial_audio(self.request(Command.READ_SPATIAL_AUDIO).payload)

    def read_eq(self) -> EqSetting:
        return decode_eq(self.request(Command.READ_EQ).payload)

    def read_advanced_eq_mode(self) -> bool:
        return decode_advanced_eq_mode(self.request(Command.READ_ADVANCED_EQ_MODE).payload)

    def read_advanced_eq(self) -> AdvancedEq:
        return decode_advanced_eq(self.request(Command.READ_ADVANCED_EQ_VALUES).payload)

    def read_supported_features(self) -> bytes:
        return self.request(Command.READ_SUPPORTED_FEATURES).payload

    def read_extra_features(self) -> bytes:
        return self.request(Command.READ_EXTRA_FEATURES).payload

    def read_gestures(self) -> bytes:
        return self.request(Command.READ_GESTURES).payload

    def read_smart_anc(self) -> bytes:
        return self.request(Command.READ_SMART_ANC).payload

    def read_earphone_status(self) -> bytes:
        return self.request(Command.READ_EARPHONE_STATUS).payload

    # -- escrituras ----------------------------------------------------------

    def set_anc_mode(self, value, settle: float = 1.0) -> Verified:
        mode = parse_anc_mode(value)
        return self._write_verified(
            Command.SET_ANC,
            encode_anc_write(mode),
            read_command=Command.READ_ANC,
            settle=settle,
            confirm=lambda raw: decode_anc_report(raw).mode == mode,
        )

    def set_low_latency(self, enabled: bool) -> Verified:
        return self._write_verified(
            Command.SET_LOW_LATENCY,
            encode_low_latency(enabled),
            read_command=Command.READ_LOW_LATENCY,
            confirm=lambda raw: decode_low_latency(raw).enabled == enabled,
        )

    def set_bass_boost(self, enabled: bool, level: Optional[int] = None) -> Verified:
        current = self.read_bass_boost()
        request_level = current.level if level is None else int(level)
        return self._write_verified(
            Command.SET_BASS_BOOST,
            encode_bass_boost(enabled, request_level),
            read_command=Command.READ_BASS_BOOST,
            confirm=lambda raw: decode_bass_boost(raw).enabled == enabled,
        )

    def set_spatial_audio(
        self, enabled: bool, head_tracking: Optional[bool] = None
    ) -> Verified:
        return self._write_verified(
            Command.SET_SPATIAL_AUDIO,
            encode_spatial_audio(enabled, head_tracking),
            read_command=Command.READ_SPATIAL_AUDIO,
            confirm=lambda raw: decode_spatial_audio(raw).enabled == enabled,
        )

    def set_eq_preset(self, value) -> Verified:
        preset = parse_eq_preset(value)
        return self._write_verified(
            Command.SET_EQ,
            encode_eq_write(preset),
            read_command=Command.READ_EQ,
            confirm=lambda raw: decode_eq(raw).preset == preset,
        )

    def set_custom_eq(self, bands, enable_custom: bool = True) -> Verified:
        self.set_advanced_eq_mode(enable_custom)
        return self._write_verified(
            Command.SET_ADVANCED_EQ_VALUES,
            encode_custom_eq(bands),
            read_command=Command.READ_ADVANCED_EQ_VALUES,
            confirm=lambda raw: decode_advanced_eq(raw).gains_db == tuple(int(g) for g in bands),
        )

    def set_advanced_eq_mode(self, custom: bool) -> Verified:
        return self._write_verified(
            Command.SET_ADVANCED_EQ_MODE,
            encode_advanced_eq_mode(custom),
            read_command=Command.READ_ADVANCED_EQ_MODE,
            confirm=lambda raw: decode_advanced_eq_mode(raw) == custom,
        )

    def set_in_ear_detection(self, enabled: bool) -> Verified:
        return self._write_verified(
            Command.SET_EXTRA_FEATURES,
            encode_in_ear_detection(enabled),
        )

    def set_personalized_anc(self, level: int) -> Verified:
        value = max(0, min(int(level), 100))
        return self._write_verified(Command.SET_PERSONALIZED_ANC, encode_personalized_anc(value))

    def set_smart_anc(self, enabled: bool) -> Verified:
        return self._write_verified(
            Command.SET_SMART_ANC,
            encode_smart_anc(enabled),
            read_command=Command.READ_SMART_ANC,
        )

    def set_gesture(self, device: int, button: int, gesture: int, action: int) -> Verified:
        return self._write_verified(
            Command.SET_GESTURES,
            encode_gesture(device, button, gesture, action),
        )

    def set_find_device(self, play: bool, side: int = 0x05) -> Verified:
        return self._write_verified(
            Command.SET_FIND_DEVICE,
            encode_find_device(side, play),
        )

    def set_utc_time(self, timestamp: Optional[int] = None) -> Verified:
        return self._write_verified(Command.SET_UTC_TIME, encode_utc_time(timestamp))

    # -- personalizacion de producto ---------------------------------------

    def _anc_read_payload(self) -> bytes:
        return encode_anc_read()

    def poll_events(self) -> Iterator[Packet]:
        return self.session.poll_events()