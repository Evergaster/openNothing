"""Capa de dispositivo: API tipada sobre la sesion de protocolo."""

from typing import Callable, Dict, Type

from opennothing.device.base import BudsDevice
from opennothing.device.cmf_pro_2 import CmfBudsPro2
from opennothing.device.registry import create_device, get_device_type, register_device

__all__ = [
    "BudsDevice",
    "CmfBudsPro2",
    "create_device",
    "get_device_type",
    "register_device",
]