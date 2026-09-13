# Comandos de openNothing

Referencia de todos los subcomandos del CLI. El paquete se invoca de tres
formas equivalentes:

```bash
opennothing <comando> [args]        # binario global (uv tool install / make install)
python3 -m opennothing <comando>    # desde la fuente (python3 -m pip install -e .)
make run ARGS="<comando> [args]"    # via Makefile (requiere uv)
```

## Argumentos comunes

Todos los subcomandos aceptan estos flags, que se pueden poner antes o
después del subcomando:

| Flag | Por defecto | Descripcion |
|---|---|---|
| `--mac <MAC>` | `2C:BE:EE:70:76:30` | MAC del dispositivo Bluetooth |
| `--channel <n>` | `15` | Canal SPP/RFCOMM del servicio |
| `--model <codigo>` | `B172` | Codigo de producto (B172 = CMF Buds Pro 2) |
| `--timeout <s>` | `5.0` | Timeout de conexion/lectura, en segundos |
| `--scripted` | off | Usa transporte simulado: demo sin hardware |

Cada comando conecta al dispositivo, ejecuta la operacion y cierra la sesion.
Toda escritura devuelve esta informacion de verificacion:

- `ack=...`  → el ACK llego al instante (`True`) y la trama era valida.
- `confirmado=...` → se releyo el ajuste y coincide con lo pedido
  (`True`). Con algunos comandos el cambio tarda ~1s en aplicarse (ver cada
  apartado).

## `status`

Lee el estado general: modelo, firmware, modo ANC y bateria.

```bash
opennothing status
opennothing status --mac 2C:BE:EE:70:76:30
opennothing status --scripted    # demo sin hardware
```

Salida:

```
modelo:      CMF Buds Pro 2
firmware:    2.4.5
ANC:         transparencia
bateria left: 90%
bateria right: 88%
bateria case: 96%
```

## `anc`

Lee o cambia el modo de cancelacion de ruido.

```bash
opennothing anc                 # leer el modo actual
opennothing anc alto            # escribir un modo
opennothing anc off
opennothing anc --settle 0.2 off   # ajustar la espera de confirmacion
```

Modos aceptados (alias espanol/ingles, o codigo numerico):

| Modo | Alias | Codigo |
|---|---|---|
| Cancelacion alta | `alto`/`high` | `01` |
| Cancelacion media | `medio`/`mid`/`medium` | `02` |
| Cancelacion baja | `bajo`/`low` | `03` |
| Adaptativo | `adaptativo`/`adaptive` | `04` |
| Desactivado | `off`/`desactivado` | `05` |
| Transparencia | `transparencia`/`transparency` | `07` |

`--settle` (por defecto `1.0`) controla cuantos segundos espera entre la
escritura y la relectura de confirmacion. El ACK llega al instante, pero el
cambio de modo tarda ~1s en aplicarse; baja hasta `0.2` si el ACK es de
confianza y quieres respuestas mas rapidas.

Al escribir, muestra el modo leido de vuelta:

```
ack=True confirmado=True
ANC ahora: alto
```

## `low-latency`

Modo juego / baja latencia del pack.

```bash
opennothing low-latency          # leer (on/off)
opennothing low-latency on
opennothing low-latency off
```

Acepta `on`/`off` (tambien `1`/`0`/`true`/`false`).

## `bass-boost`

Refuerzo de graves.

```bash
opennothing bass-boost                  # leer (estado + nivel)
opennothing bass-boost on
opennothing bass-boost on --level 10    # nivel 0..10
opennothing bass-boost off
```

`--level` es opcional (0..10). Si se omite y se enciende, conserva el nivel
actual.

## `spatial-audio`

Audio espacial y head tracking.

```bash
opennothing spatial-audio               # leer (on/off + tracking)
opennothing spatial-audio on
opennothing spatial-audio on --tracking on
opennothing spatial-audio off
```

`--tracking` es opcional y solo acepta `on`/`off`. Si se omite, el tracking
queda como este.

## `eq`

Preset de ecualizacion.

```bash
opennothing eq                    # leer preset actual
opennothing eq more_bass
opennothing eq balanced
opennothing eq voice
opennothing eq custom             # pretende el EQ custom (ver eq-custom)
```

Presets (alias espanol/ingles):

| Preset | Codigo |
|---|---|
| `balanced`/`balanceado` | `00` |
| `more_bass`/`mas_bajos` | `01` |
| `more_treble`/`mas_agudos` | `02` |
| `voice`/`voz` | `03` |
| `custom`/`personalizado` | `04` |

## `eq-custom`

Ecualizador avanzado de 8 bandas (gains en dB, cada uno `-8..8`).

```bash
opennothing eq-custom -4 0 3 5 4 0 -2 -5
opennothing eq-custom --enable -4 0 3 5 4 0 -2 -5
```

- `--enable` activa el modo EQ custom antes de escribir (por defecto ya lo
  activa). Pasarlo es redundante.
- Los 8 valores son obligatorios y en orden de banda, de graves a agudos.
- Tras escribir, muestra los gains confirmados por el dispositivo:
  ```
  ack=True confirmado=True
  gains leidos: (-4, 0, 3, 5, 4, 0, -2, -5)
  ```

## `features`

Dump de diagnostico: capacidades soportadas y estado del dispositivo.

```bash
opennothing features
```

Salida (hex crudo, sin interpretar):

```
supported:  <16 bytes>
extra:      <16 bytes>
earphones:  <16 bytes>
gestures:   <16 bytes>
smart-anc:  <16 bytes>
```

## `events`

Escucha los pushes/eventos que emite el dispositivo (bateria, cambio de ANC,
detector de ajuste...) hasta `Ctrl-C`.

```bash
opennothing events
```

Cada evento se imprime como `evento 0x<cmd>: <payload hex>`. Salida puntual:

```
escuchando eventos del dispositivo (Ctrl-C para salir)...
evento 0xe001: 0080...
evento 0xe003: 0102...
^C
```

## Codigos de salida

- `0`: exito.
- `!= 0`: error (dispositivo no encontrado, timeout, trama invalida o valor
  desconocido). El mensaje de error se imprime en stderr con el detalle.

## Modo simulado (`--scripted`)

Todos los comandos aceptan `--scripted` para probarlos sin hardware
(trafico grabado de una sesion real). Es la forma mas segura de verificar el
flujo:

```bash
opennothing anc alto --scripted
opennothing status --scripted
```