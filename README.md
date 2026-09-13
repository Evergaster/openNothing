# openNothing

Controla tus audifonos **Nothing / CMF** desde la linea de comandos, usando
Bluetooth Clasico (SPP / RFCOMM). Validado en hardware real con **CMF Buds Pro 2**
(modelo B172, nombre interno `espeon`).

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Licencia MIT](https://img.shields.io/badge/licencia-MIT-green.svg)](LICENSE)
[![Plataforma](https://img.shields.io/badge/plataforma-Linux-lightgrey.svg)](#)

Sin app oficial, sin nube y sin dependencias del telefono: habla directamente
con los audifonos por el canal SPP que usa la app original, con verificacion
de cada escritura.

## Funcionalidades

| Ajuste | Soporta |
|---|---|
| Cancelacion de ruido (ANC) | alto / medio / bajo / adaptativo / off / transparencia |
| Modo juego (baja latencia) | on / off |
| Refuerzo de graves | on / off + nivel 0..10 |
| Audio espacial | on / off + head tracking |
| Ecualizador | 5 presets + EQ custom de 8 bandas |
| Diagnostico | bateria, firmware, modelo, features, gestos, smart ANC |
| Eventos | escucha pushes del dispositivo en tiempo real |

Todas las escrituras se confirman de vuelta (`ack + readback`), de modo que
siempre sabes si el ajuste realmente se aplico.

## Instalacion

Con [`uv`](https://docs.astral.sh/uv/) (recomendado):

```bash
uv tool install .
```

o con `make`:

```bash
make install          # instala el comando `opennothing` en ~/.local/bin
make uninstall        # lo elimina
```

Desde la fuente, en un venv:

```bash
uv venv .venv && uv pip install -e .
```

## Uso rapido

```bash
# estado completo: modelo, firmware, ANC y bateria
opennothing status

# cambiar la cancelacion de ruido
opennothing anc transparencia
opennothing anc alto

# escribir y verificar otros ajustes
opennothing low-latency on
opennothing bass-boost on --level 10
opennothing spatial-audio on --tracking off
opennothing eq more_bass
opennothing eq-custom -4 0 3 5 4 0 -2 -5

# escuchar los eventos que emite el dispositivo
opennothing events
```

> Todos los comandos aceptan `--mac`, `--channel`, `--model`, `--timeout` y
> `--scripted` (demo sin hardware). Referencia completa por comando en
> [`COMANDOS.md`](COMANDOS.md).

## Arquitectura

Disenado por capas, cada una depende solo de la anterior. El protocolo y la
sesion son testeables **sin Bluetooth** gracias a `ScriptedTransport`:

```
opennothing/
  protocol/    # puro, sin I/O: crc, packet (build/parse), enums, models, codec
  transport/   # Transport (ABC), RfcommTransport (real), ScriptedTransport (simulado)
  session.py   # secuencia, framing, CRC y cola de eventos
  device/      # BudsDevice (API tipada) + CmfBudsPro2 + registry por codigo
  controller.py # facade: CMFBudsController.connect(...)
  cli.py       # linea de comandos
```

## Protocolo

Cada trama es una cabecera de 8 bytes, el payload y (salvo en eventos) 2
bytes de CRC-16:

```
[0x55] [control:LE2] [cmd:LE2] [len:LE2] [fsn:1] [payload...] [crc:LE2]
```

| Direccion | Detalle |
|---|---|
| Requests (app → buds) | `control=0x0160`, CRC sobre **cabecera + payload** |
| Respuestas (buds → app) | mismo formato, CRC sobre **solo el payload**, `cmd & 0x7FFF` |
| Eventos / pushes | `control=0x0100`, **sin CRC** |
| CRC | CRC-16/MODBUS (`0xA001`, init `0xFFFF`), little-endian |

El protocolo se documento a partir de capturas reales del canal 15. La
asimetria de CRC (app sobre todo el frame, dispositivo solo sobre el payload)
quedo verificada contra **119 tramas reales** y se validaba en cada test con
*golden vectors* de esa misma sesion.

## Tests

```bash
make test                 # con uv
python3 -m unittest discover -s tests -v    # con unittest puro
```

Los tests comparan la pila de protocolo contra trafico real verificado byte a
byte, sin necesidad de hardware.

## Notas

- La escritura ANC se confirma de forma asincrona: el ACK llega al instante,
  pero el cambio de modo tarda ~1s en aplicarse. Controlalo con `--settle`.
- Los comandos de escritura reportan `ack` (trama aceptada) y `confirmado`
  (relectura que coincide con lo pedido).
- Probado en Linux con `rfcomm`. Requiere derechos sobre el dispositivo
  Bluetooth (grupo `bluetooth` o permisos de TTY).

## Licencia

MIT. Proyecto personal con fines de experimentacion; no afiliado con
Nothing Technology Ltd. Ni Nothing ni CMF son marcas usadas con intencion de
infringir sus derechos.