"""Interfaz de linea de comandos orientada a uso interactivo."""

import argparse
from typing import Optional

from opennothing import CMFBudsController
from opennothing.protocol.constants import DEFAULT_CHANNEL, DEFAULT_TIMEOUT


def _build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--mac", default=None,
                        help="MAC del dispositivo (si se omite, se detecta automaticamente)")
    common.add_argument("--channel", type=int, default=DEFAULT_CHANNEL)
    common.add_argument("--model", default="B172", help="codigo de producto (B172)")
    common.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    common.add_argument("--scripted", action="store_true",
                        help="usa transporte simulado (demo/sin hardware)")

    parser = argparse.ArgumentParser(
        prog="opennothing", parents=[common],
        description="Control de audifonos Nothing/CMF",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", parents=[common], help="estado: ANC, bateria, firmware")

    anc = sub.add_parser("anc", parents=[common], help="leer o cambiar el modo ANC")
    anc.add_argument("mode", nargs="?", default=None,
                     help="alto|medio|bajo|adaptativo|off|transparencia (si se omite, lee)")
    anc.add_argument("--settle", type=float, default=1.0, help="espera (s) entre write y readback")

    ll = sub.add_parser("low-latency", parents=[common], help="modo juego (la baja latencia del pack)")
    ll.add_argument("value", nargs="?", default=None, help="on|off")

    bass = sub.add_parser("bass-boost", parents=[common], help="refuerzo de graves")
    bass.add_argument("value", nargs="?", default=None, help="on|off")
    bass.add_argument("--level", type=int, default=None, help="nivel 0..10")

    spatial = sub.add_parser("spatial-audio", parents=[common], help="audio espacial")
    spatial.add_argument("value", nargs="?", default=None, help="on|off")
    spatial.add_argument("--tracking", choices=("on", "off"), default=None, help="head tracking")

    eq = sub.add_parser("eq", parents=[common], help="preset de ecualizacion")
    eq.add_argument("preset", nargs="?", default=None,
                    help="balanced|more_bass|more_treble|voice|custom (si se omite, lee)")

    eqc = sub.add_parser("eq-custom", parents=[common], help="ecualizador avanzado (gains en dB, 8 bandas)")
    eqc.add_argument("--enable", action="store_true", help="activar modo EQ custom")
    eqc.add_argument("bands", nargs="+", type=float, help="gains, p. ej. -4 0 3 5 4 0 -2 -5")

    sub.add_parser("features", parents=[common],
                   help="lee lo que soporta el dispositivo + extra de fabrica")
    sub.add_parser("events", parents=[common],
                   help="escucha pushes del dispositivo hasta Ctrl-C")

    return parser


def main(argv: Optional[list] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    with CMFBudsController.connect(
        mac=args.mac,
        channel=args.channel,
        timeout=args.timeout,
        model=args.model,
        scripted=args.scripted,
    ) as buds:
        if args.command == "status":
            status = buds.get_status()
            print(f"modelo:      {status.model}")
            print(f"firmware:    {status.firmware.version}")
            print(f"ANC:         {status.anc.mode_name}")
            for side, level in status.battery.named().items():
                print(f"bateria {side}: {level}%")
        elif args.command == "anc":
            if args.mode is None:
                report = buds.read_anc()
                print(f"ANC: {report.mode_name}", report.as_dict())
            else:
                result = buds.set_anc_mode(args.mode, settle=args.settle)
                print(f"ack={result.acknowledged} confirmado={result.confirmed}")
                print(f"ANC ahora: {buds.read_anc().mode_name}")
        elif args.command == "low-latency":
            if args.value is None:
                print(f"low-latency: {'on' if buds.read_low_latency().enabled else 'off'}")
            else:
                result = buds.set_low_latency(args.value in ("on", "1", "true"))
                print(f"ack={result.acknowledged} confirmado={result.confirmed}")
        elif args.command == "bass-boost":
            if args.value is None:
                boost = buds.read_bass_boost()
                print(f"bass-boost: {'on' if boost.enabled else 'off'} nivel={boost.level}")
            else:
                result = buds.set_bass_boost(args.value in ("on", "1", "true"), level=args.level)
                print(f"ack={result.acknowledged} confirmado={result.confirmed}")
        elif args.command == "spatial-audio":
            if args.value is None:
                spatial = buds.read_spatial_audio()
                print(f"spatial: {'on' if spatial.enabled else 'off'} tracking={spatial.head_tracking}")
            else:
                tracking = {"on": True, "off": False}.get(args.tracking) if args.tracking else None
                result = buds.set_spatial_audio(args.value in ("on", "1", "true"), tracking)
                print(f"ack={result.acknowledged} confirmado={result.confirmed}")
        elif args.command == "eq":
            if args.preset is None:
                setting = buds.read_eq()
                print(f"EQ: {setting.preset_name}")
            else:
                result = buds.set_eq_preset(args.preset)
                print(f"ack={result.acknowledged} confirmado={result.confirmed}")
        elif args.command == "eq-custom":
            result = buds.set_custom_eq(args.bands, enable_custom=args.enable)
            print(f"ack={result.acknowledged} confirmado={result.confirmed}")
            print(f"gains leidos: {buds.read_advanced_eq().gains_db}")
        elif args.command == "features":
            print(f"supported:  {buds.read_supported_features().hex()}")
            print(f"extra:      {buds.read_extra_features().hex()}")
            print(f"earphones:  {buds.read_earphone_status().hex()}")
            print(f"gestures:   {buds.read_gestures().hex()}")
            print(f"smart-anc:  {buds.read_smart_anc().hex()}")
        elif args.command == "events":
            print("escuchando eventos del dispositivo (Ctrl-C para salir)...")
            try:
                for packet in buds.poll_events():
                    print(f"evento 0x{packet.command:04x}: {packet.payload.hex()}")
            except KeyboardInterrupt:
                print("\nadios")
    return 0