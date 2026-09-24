# Air Quality Checker — PCB

> **Three board revisions are in this repo.** This README documents **v1**
> (108 × 108 mm square). A denser **round** revision lives in [`v2/`](v2/) —
> Ø 72 mm, with mounting holes and a wind logo, same circuit. [`v3/`](v3/) is
> the round board with the **BME688 soldered directly on-board** (no STEMMA QT
> breakout).

Custom 2-layer KiCad board for the [air-quality-checker](../air-quality-checker) firmware:
an ESP8266 air-quality monitor that reads a Bosch BME688 over I2C and moves an
SG92R micro servo to indicate the current IAQ level. Battery-powered with LiPo
charging over USB-C.

This board replaces the Adafruit Feather HUZZAH with an on-board design, so the
whole system fits on one PCB.

---

## What's on the board

| Block | Part | Notes |
|---|---|---|
| MCU | **ESP-12F** (ESP8266, 4 MB) | Castellated module, antenna keep-out respected |
| USB–serial | **CP2102N** QFN28 | USB-C → UART, with DTR/RTS auto-reset |
| Charger | **MCP73831** | Single-cell LiPo, 2.2 kΩ PROG ≈ 500 mA |
| Regulator | **AP2112K-3.3** | 3.3 V LDO @ 600 mA |
| Power path | **DMG2305UX** PFET + **B5819W** Schottky | USB powers the rail and charges the cell |
| Sensor | **STEMMA QT (JST-SH 4P)** | BME688 breakout over I2C (SDA GPIO4 / SCL GPIO5) |
| Actuator | **3-pin servo header** | SG92R, powered from VBAT through a 100 Ω signal resistor |
| User I/O | RESET + BOOT buttons, deep-sleep jumper, PWR and CHG LEDs | |
| Battery | **JST-PH 2P** | LiPo cell |

Board size: **108 × 108 mm**, 2 copper layers, 1.6 mm FR4.

---

## Schematic ↔ firmware pin map

| Net | ESP-12F pin | Function |
|---|---|---|
| `SDA` | GPIO4 | BME688 I2C data |
| `SCL` | GPIO5 | BME688 I2C clock |
| `SERVO_PWM` | GPIO13 | Servo PWM (through R17 100 Ω) |
| `GPIO16` | GPIO16 | Deep-sleep wake → RST via JP1 |
| `RST` | RST | Reset; pulled up by R2, driven by Q1 (DTR) |
| `GPIO0` | GPIO0 | Boot strap; pulled up by R3, driven by Q2 (RTS) |
| `UART_TX` | GPIO1/TXD | to CP2102N RXD |
| `UART_RX` | GPIO3/RXD | to CP2102N TXD |
| `GPIO2` | GPIO2 | On-board status LED (firmware `LED_PIN`) |
| `GPIO15` | GPIO15 | Pulled low (boot strap) |

`GPIO16 → RST` is required for `ESP.deepSleep()` to wake up (ESP8266 Errata 2.9).
The jumper **JP1** ships **bridged**; cut it only if you need GPIO16 for something else.

---

## Power architecture

```
USB-C (VBUS) ─┬─► MCP73831 ─► VBAT_RAW (LiPo JST-PH)
              │                 │
              │            SW3 (power switch)
              │                 │
              │                 ▼
              └─►|B5819W├──► VSYS ◄── Q3 (DMG2305UX, USB priority)
                            │
                            ├─► AP2112K-3.3 ─► +3V3 (ESP + BME688)
                            └─► Servo header V+   (C13 100 µF bulk)
```

When USB is present, Q3 turns off and the Schottky feeds VSYS, so the cell is not
loaded during charging. On battery, Q3 conducts and the cell drives VSYS.

> **Note:** the servo runs from **VBAT/VSYS** (~3.7–4.2 V), not the 3.3 V rail, per
> the SG92R's 4.8–6 V rating. Torque is slightly reduced at 3.7 V; add a boost
> converter if that matters.

---

## Fabrication

Gerbers and drill files are in `gerbers/` (regenerate with `kicad-cli`).
Recommended stack-up for JLCPCB/OSHPark: 2 layers, 1.6 mm, HASL, 0.2 mm min trace.

### Regenerate outputs

```sh
kicad-cli pcb export gerbers --output gerbers/ \
  --layers "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts" \
  air-quality-pcb.kicad_pcb
kicad-cli pcb export drill --output gerbers/ air-quality-pcb.kicad_pcb
kicad-cli sch export bom --output bom.csv air-quality-pcb.kicad_sch
kicad-cli pcb drc --output drc.rpt air-quality-pcb.kicad_pcb
kicad-cli sch erc --output erc.rpt air-quality-pcb.kicad_sch
```

---

## Verification status

| Check | Result |
|---|---|
| ERC (schematic) | **0 errors, 0 warnings** |
| DRC (board) | **0 violations, 0 unconnected** |
| Nets | 32, all routed; GND is a filled pour on both layers |
| Autorouter | Freerouting 2.4.1 (Specctra DSN/SES) |

---

## Design notes / caveats

- **Antenna keep-out:** U1's antenna region (top of the module) is kept clear of
  copper by the ESP-12E footprint. Do not route or pour under it.
- **USB-C CC resistors** R10/R11 (5.1 kΩ) are required for a USB-C source to
  provide VBUS.
- **CP2102N auto-program:** Q1/Q2 form the standard cross-coupled DTR/RTS reset
  and boot circuit used by the Feather; `pio run --target upload` works without
  touching the buttons.
- **BME688 pull-ups** live on the Adafruit breakout (10 kΩ) — none are fitted here.
- **Charging current** is set by R14 = 2.2 kΩ (≈ 500 mA: I = 1000 / R).

---

## Firmware

The firmware lives in the sibling [`air-quality-checker`](../air-quality-checker)
repo. It is unchanged and runs as-is on this board — same ESP8266, same I2C pins,
same servo pin (`GPIO13`), same LED pin (`GPIO2`).

---

## Files

| File | Purpose |
|---|---|
| `air-quality-pcb.kicad_pro` | Project |
| `air-quality-pcb.kicad_sch` | Schematic (ERC clean) |
| `air-quality-pcb.kicad_pcb` | Board (DRC clean, fully routed) |
| `schematic.pdf` | Plotted schematic |
| `render.png` / `render_bottom.png` | 3D renders |
| `bom.csv` | Bill of materials |
| `gerbers/` | Gerbers + drill (fabrication) |
