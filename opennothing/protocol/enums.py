"""Dominios tipados del protocolo: modos ANC, presets EQ y lados."""

from enum import IntEnum
from typing import Optional

from opennothing.errors import UnknownValueError


class AncMode(IntEnum):
    HIGH = 0x01
    MID = 0x02
    LOW = 0x03
    ADAPTIVE = 0x04
    OFF = 0x05
    TRANSPARENCY = 0x07

    @property
    def is_anc(self) -> bool:
        return self not in (AncMode.OFF, AncMode.TRANSPARENCY)

    @property
    def name_es(self) -> str:
        return _ANC_ES[self]


_ANC_ES = {
    AncMode.HIGH: "alto",
    AncMode.MID: "medio",
    AncMode.LOW: "bajo",
    AncMode.ADAPTIVE: "adaptativo",
    AncMode.OFF: "desactivado",
    AncMode.TRANSPARENCY: "transparencia",
}

ANC_MODE_ALIASES = {
    "high": AncMode.HIGH,
    "alto": AncMode.HIGH,
    "mid": AncMode.MID,
    "medium": AncMode.MID,
    "medio": AncMode.MID,
    "low": AncMode.LOW,
    "bajo": AncMode.LOW,
    "adaptive": AncMode.ADAPTIVE,
    "adaptativo": AncMode.ADAPTIVE,
    "off": AncMode.OFF,
    "desactivado": AncMode.OFF,
    "transparency": AncMode.TRANSPARENCY,
    "transparencia": AncMode.TRANSPARENCY,
}


class EqPreset(IntEnum):
    BALANCED = 0x00
    MORE_BASS = 0x01
    MORE_TREBLE = 0x02
    VOICE = 0x03
    CUSTOM = 0x04


EQ_PRESET_ALIASES = {
    "balanced": EqPreset.BALANCED,
    "balanceado": EqPreset.BALANCED,
    "more_bass": EqPreset.MORE_BASS,
    "morebass": EqPreset.MORE_BASS,
    "mas_bajos": EqPreset.MORE_BASS,
    "more_treble": EqPreset.MORE_TREBLE,
    "moretreble": EqPreset.MORE_TREBLE,
    "mas_agudos": EqPreset.MORE_TREBLE,
    "voice": EqPreset.VOICE,
    "voz": EqPreset.VOICE,
    "custom": EqPreset.CUSTOM,
    "personalizado": EqPreset.CUSTOM,
}


class Ear(IntEnum):
    LEFT = 0x02
    RIGHT = 0x03
    CASE = 0x05


EAR_NAMES = {
    Ear.LEFT: "left",
    Ear.RIGHT: "right",
    Ear.CASE: "case",
}


def _normalize_key(value: str) -> str:
    return value.strip().lower().replace("_", "").replace(" ", "")


def parse_anc_mode(value) -> AncMode:
    """Acepta AncMode, int o alias de texto (ingles/espanol)."""
    if isinstance(value, AncMode):
        return value
    if isinstance(value, int):
        try:
            return AncMode(value)
        except ValueError:
            raise UnknownValueError(f"modo ANC desconocido: 0x{value:02x}") from None
    if isinstance(value, str):
        try:
            return ANC_MODE_ALIASES[_normalize_key(value)]
        except KeyError:
            raise UnknownValueError(f"modo ANC desconocido: {value!r}") from None
    raise UnknownValueError(f"modo ANC desconocido: {value!r}")


def parse_eq_preset(value) -> EqPreset:
    if isinstance(value, EqPreset):
        return value
    if isinstance(value, int):
        try:
            return EqPreset(value)
        except ValueError:
            raise UnknownValueError(f"preset EQ desconocido: 0x{value:02x}") from None
    if isinstance(value, str):
        try:
            return EQ_PRESET_ALIASES[_normalize_key(value)]
        except KeyError:
            raise UnknownValueError(f"preset EQ desconocido: {value!r}") from None
    raise UnknownValueError(f"preset EQ desconocido: {value!r}")


def mode_from_report(value: int) -> Optional[AncMode]:
    try:
        return AncMode(value)
    except ValueError:
        return None