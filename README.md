# openNothing

Control de audifonos **Nothing / CMF** por Bluetooth Clasico (SPP / RFCOMM),
validado en hardware con **CMF Buds Pro 2** (modelo B172, nombre interno
`espeon`).

## Protocolo

Cada trama tiene 8 bytes de cabecera, el payload y (salvo en eventos) 2 bytes
de CRC-16:

```
[0x55] [control:LE2] [cmd:LE2] [len:LE2] [fsn:1] [payload...] [crc:LE2]
```

| quiero | detalle |
|---|---|
| Requests (app -> buds) | `control=0x0160`, CRC sobre **cabecera + payload** |
| Respuestas (buds -> app) | mismo formato, CRC sobre **solo el payload**, `cmd & 0x7FFF` |
| Eventos / pushes | `control=0x0100`, **sin CRC** |
| CRC | CRC-16/MODBUS (`0xA001`, init `0xFFFF`), bytes little-endian |

Esta asimetria de CRC (app sobre todo el frame, dispositivo solo sobre el
payload) se verifico con 119 tramas reales del canal 15.

## Arquitectura

```
opennothing/
  protocol/   # puro, sin I/O: crc, packet (build/parse), enums, models, codec
  transport/  # Transport (ABC), RfcommTransport (real), ScriptedTransport (tests)
  session.py  # secuencia + framing + CRC + cola de eventos
  device/     # BudsDevice (API tipada) + CmfBudsPro2 + registry por codigo de producto
  controller.py  # facade: CMFBudsController.connect(...)
  cli.py      # linea de comandos
```

Cada capa depende solo de la anterior: se puede testear el protocolo y la
sesion sin Bluetooth gracias a `ScriptedTransport`.

## Uso

```bash
# instalacion en modo editable
python3 -m pip install -e .

# estado completo
python3 -m opennothing status --mac 2C:BE:EE:70:76:30

# cambiar ANC (aplicacion asincrona: espera 1s por defecto antes de leer)
python3 -m opennothing anc transparencia
python3 -m opennothing anc alto

# escribir y verificar otros ajustes
python3 -m opennothing low-latency on
python3 -m opennothing bass-boost on --level 10
python3 -m opennothing spatial-audio on --tracking off
python3 -m opennothing eq more_bass
python3 -m opennothing eq-custom --enable -4 0 3 5 4 0 -2 -5

# demo sin hardware
python3 -m opennothing status --scripted
```

Referencia completa de cada subcomando, argumentos y valores aceptados en
[`COMANDOS.md`](COMANDOS.md).

## Tests

```bash
python3 -m unittest discover -s tests -v
```

Los tests usan *golden vectors* capturados de una sesion real, de modo que la
pila de protocolo se valida contra tráfico verificado byte a byte sin necesidad
de hardware.

## Notas

- La escritura ANC se confirma de forma asincrona: el ACK llega al instante, pero
  el cambio de modo tarda ~1s en aplicarse.
- `set_anc_mode` devuelve `Verified(acknowledged, confirmed, ack_seq,
  ack_crc_ok, readback)` para saber si la confirmacion de vuelta fue exitosa.
- Modos ANC: `01` alto, `02` medio, `03` bajo, `04` adaptativo, `05` off, `07`
  transparencia.