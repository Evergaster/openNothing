"""Registro de modelos de dispositivo por codigo de producto."""

from typing import Dict, List, Type

from opennothing.device.base import BudsDevice

_REGISTRY: Dict[str, Type[BudsDevice]] = {}
_ALIASES: Dict[str, str] = {}


def register_device(*aliases: str):
    """Decorador: registra una clase de dispositivo bajo su product_code y alias."""

    def _register(cls: Type[BudsDevice]) -> Type[BudsDevice]:
        codes = [str(cls.product_code).lower()] + [a.lower() for a in aliases]
        for code in codes:
            _REGISTRY[code] = cls
            _ALIASES[code] = str(cls.product_code).lower()
        return cls

    return _register


def get_device_type(key: str) -> Type[BudsDevice]:
    """Resuelve por codigo de producto o alias (case-insensitive)."""
    return _REGISTRY[str(key).lower()]


def create_device(key: str, session) -> BudsDevice:
    return get_device_type(key)(session)


def known_models() -> List[str]:
    return sorted({_ALIASES.get(code, code) for code in _REGISTRY})