"""CMF Buds Pro 2.

Modelo B172 (nombre interno "espeon"). A diferencia de otros modelos,
el READ_ANC de este hardware se hace enviando el payload 0x03.
"""

from opennothing.device.base import BudsDevice
from opennothing.device.registry import register_device


@register_device("cmf buds pro 2", "espeon", "cmfbudspro2")
class CmfBudsPro2(BudsDevice):
    product_code = "B172"
    product_name = "CMF Buds Pro 2"

    def _anc_read_payload(self) -> bytes:
        return b"\x03"