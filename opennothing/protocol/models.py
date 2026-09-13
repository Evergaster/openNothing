"""Modelos de dominio (inmutables) producidos por el codec del protocolo."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from opennothing.protocol.enums import Ear, EqPreset, AncMode, mode_from_report


@dataclass(frozen=True)
class AncReport:
    """Reporte de estado ANC: grupos (group, value) en orden de llegada.

    En el grupo 0x01 vive el modo ANC actual de los audifonos.
    """

    groups: Tuple[Tuple[int, int], ...]

    def as_dict(self) -> Dict[int, int]:
        return dict(self.groups)

    @property
    def mode(self) -> Optional[AncMode]:
        return mode_from_report(self.as_dict().get(1))

    @property
    def mode_name(self) -> Optional[str]:
        mode = self.mode
        return mode.name_es if mode is not None else None


@dataclass(frozen=True)
class BatteryReading:
    """Lectura de bateria: pares (id_auricular, porcentaje)."""

    levels: Tuple[Tuple[int, int], ...]

    def as_dict(self) -> Dict[int, int]:
        return dict(self.levels)

    def named(self) -> Dict[str, int]:
        return {EAR_NAMES[id_]: value for id_, value in self.levels}


EAR_NAMES = {Ear.LEFT: "left", Ear.RIGHT: "right", Ear.CASE: "case"}


@dataclass(frozen=True)
class Firmware:
    raw: bytes
    version: str


@dataclass(frozen=True)
class LowLatency:
    enabled: bool
    raw: bytes


@dataclass(frozen=True)
class BassBoost:
    enabled: bool
    level: int
    raw: bytes


@dataclass(frozen=True)
class SpatialAudio:
    enabled: bool
    head_tracking: Optional[int]
    raw: bytes


@dataclass(frozen=True)
class EqSetting:
    preset: Optional[EqPreset]
    raw: bytes

    @property
    def preset_name(self) -> Optional[str]:
        return EQ_NAMES_ES.get(self.preset)


EQ_NAMES_ES = {
    EqPreset.BALANCED: "balanceado",
    EqPreset.MORE_BASS: "mas bajos",
    EqPreset.MORE_TREBLE: "mas agudos",
    EqPreset.VOICE: "voz",
    EqPreset.CUSTOM: "personalizado",
}


@dataclass(frozen=True)
class AdvancedEq:
    gains_db: Tuple[int, ...]
    raw: bytes


@dataclass(frozen=True)
class Ack:
    """Confirmacion del dispositivo a un comando de escritura."""

    acknowledged: bool
    ack_seq: int
    ack_crc_ok: Optional[bool]


@dataclass(frozen=True)
class Verified(Ack):
    """Escritura confirmada leyendo el estado de vuelta."""

    confirmed: bool
    readback: Optional[bytes] = None


@dataclass(frozen=True)
class DeviceStatus:
    anc: AncReport
    battery: BatteryReading
    firmware: Firmware
    model: Optional[str] = None

    def as_dict(self) -> Dict[str, object]:
        result = {
            "anc": {
                "groups": self.anc.as_dict(),
                "mode": int(self.anc.mode) if self.anc.mode is not None else None,
                "mode_name": self.anc.mode_name,
            },
            "battery": self.battery.named(),
            "firmware": self.firmware.version,
        }
        if self.model:
            result["model"] = self.model
        return result