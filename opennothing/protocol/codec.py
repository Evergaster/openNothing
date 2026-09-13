"""Codecs de payload: convierten bytes del wire en modelos y viceversa.

Sin I/O; la capa de protocolo permanece 100% testeable sin hardware.
"""

import time
from typing import Iterable, List, Optional, Tuple

from opennothing.protocol.constants import (
    BASS_LEVEL_MAX,
    BASS_LEVEL_MIN,
    EQ_GAIN_OFFSET,
    SIDE_SINGLE,
)
from opennothing.protocol.enums import AncMode, EqPreset, mode_from_report
from opennothing.protocol.models import (
    AdvancedEq,
    AncReport,
    BassBoost,
    BatteryReading,
    EqSetting,
    Firmware,
    LowLatency,
    SpatialAudio,
)

Groups = Tuple[Tuple[int, int], ...]


def _decode_groups(payload: bytes) -> Groups:
    return tuple(
        (payload[i], payload[i + 1])
        for i in range(0, len(payload) - 2, 3)
    )


def decode_anc_report(payload: bytes) -> AncReport:
    return AncReport(groups=_decode_groups(payload))


def decode_push_anc(payload: bytes) -> Optional[AncMode]:
    if len(payload) < 2:
        return None
    return mode_from_report(payload[1])


def decode_battery(payload: bytes) -> BatteryReading:
    pairs: List[Tuple[int, int]] = []
    if payload:
        count = payload[0]
        pairs = [
            (payload[i], payload[i + 1])
            for i in range(1, min(len(payload) - 1, 1 + count * 2), 2)
        ]
    return BatteryReading(levels=tuple(pairs))


def decode_firmware(payload: bytes) -> Firmware:
    try:
        version = payload.decode("ascii").rstrip("\x00")
    except UnicodeDecodeError:
        version = payload.hex()
    return Firmware(raw=payload, version=version)


def decode_device_model(payload: bytes) -> str:
    try:
        return payload.decode("ascii").rstrip("\x00")
    except UnicodeDecodeError:
        return payload.hex()


def decode_low_latency(payload: bytes) -> LowLatency:
    enabled = bool(payload) and payload[0] == 1
    return LowLatency(enabled=enabled, raw=payload)


def decode_bass_boost(payload: bytes) -> BassBoost:
    enabled = bool(payload) and payload[0] == 1
    level = payload[1] if len(payload) > 1 else 0
    return BassBoost(enabled=enabled, level=level, raw=payload)


def decode_spatial_audio(payload: bytes) -> SpatialAudio:
    enabled = bool(payload) and payload[0] == 1
    head_tracking = payload[1] if len(payload) > 1 else None
    return SpatialAudio(enabled=enabled, head_tracking=head_tracking, raw=payload)


def decode_eq(payload: bytes) -> EqSetting:
    preset = None
    if payload:
        try:
            preset = EqPreset(payload[0])
        except ValueError:
            preset = None
    return EqSetting(preset=preset, raw=payload)


def decode_advanced_eq_mode(payload: bytes) -> bool:
    return bool(payload) and payload[0] == 1


def decode_advanced_eq(payload: bytes) -> AdvancedEq:
    return AdvancedEq(
        gains_db=tuple(byte - EQ_GAIN_OFFSET for byte in payload),
        raw=payload,
    )


def encode_anc_read() -> bytes:
    return b"\x03"


def encode_anc_write(mode: AncMode) -> bytes:
    return bytes((0x01, int(mode) & 0xFF, 0x00))


def encode_low_latency(enabled: bool) -> bytes:
    return bytes((1 if enabled else 2,))


def encode_bass_boost(enabled: bool, level: int) -> bytes:
    level = max(BASS_LEVEL_MIN, min(int(level), BASS_LEVEL_MAX))
    return bytes((1 if enabled else 0, level))


def encode_spatial_audio(enabled: bool, head_tracking: Optional[bool]) -> bytes:
    if head_tracking is None:
        return bytes((1 if enabled else 0,))
    return bytes((1 if enabled else 0, 1 if head_tracking else 0))


def encode_eq_write(preset: EqPreset) -> bytes:
    return bytes((int(preset) & 0xFF,))


def encode_advanced_eq_mode(custom: bool) -> bytes:
    return bytes((1 if custom else 0,))


def encode_custom_eq(bands: Iterable[int]) -> bytes:
    return bytes(
        max(0, min(int(gain) + EQ_GAIN_OFFSET, EQ_GAIN_OFFSET * 2))
        for gain in bands
    )


def encode_in_ear_detection(enabled: bool) -> bytes:
    return bytes((0x01, 0x01, 1 if enabled else 0))


def encode_personalized_anc(level: int) -> bytes:
    return bytes((int(level) & 0xFF,))


def encode_smart_anc(enabled: bool) -> bytes:
    return bytes((1 if enabled else 0,))


def encode_gesture(device: int, button: int, gesture: int, action: int) -> bytes:
    return bytes(
        (
            0x01,
            int(device) & 0xFF,
            int(button) & 0xFF,
            int(gesture) & 0xFF,
            int(action) & 0xFF,
        )
    )


def encode_find_device(side: int, play: bool) -> bytes:
    on_off = 1 if play else 0
    if side == SIDE_SINGLE:
        return bytes((on_off,))
    return bytes((int(side) & 0xFF, on_off))


def encode_utc_time(timestamp: Optional[int] = None) -> bytes:
    if timestamp is None:
        timestamp = int(time.time())
    timestamp &= 0xFFFFFFFF
    return bytes(
        (
            timestamp & 0xFF,
            (timestamp >> 8) & 0xFF,
            (timestamp >> 16) & 0xFF,
            (timestamp >> 24) & 0xFF,
        )
    )