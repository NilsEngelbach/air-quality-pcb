# Air Quality Checker — PCB

Custom 2-layer KiCad boards for the [air-quality-checker](../air-quality-checker) firmware: a battery-powered
indoor air-quality monitor. A Bosch **BME688** measures the air, an **SG92R** micro servo points at the current IAQ
band, and readings can be uploaded over WiFi. A LiPo cell powers it and charges over USB-C. The device sleeps
~98 % of the time and wakes every 5 minutes.

The repo holds every board revision in its own folder. **The current board is [`v9/`](v9/) (rev I).**

---

## Current board — v9 (rev I)

| Block | Part | Notes |
|---|---|---|
| MCU | **ESP32-C3-WROOM-02-N4** | native USB Serial/JTAG (no USB-UART bridge), antenna in a board notch with no copper beside it |
| Sensor | **BME688** on-board, I²C 0x76 | on a slotted island at the board edge for thermal isolation |
| Indicator | **SG92R** servo header | from VSYS through a load switch (Q6): 0 µA in sleep, 4.5 V on USB / 3.0–4.2 V on battery |
| Charger | **MCP73831**, ~303 mA | charge status to the MCU (IO20) and a green side-view LED |
| Regulator | **AP2112K-3.3** | 600 mA LDO |
| Power path | DMG2305UX P-FETs + B5819W | USB priority, battery reverse-polarity protection, POWER switch drives a FET |
| Controls | POWER (SPDT) + **WiFi mode** (SP3T: OFF / SPARSE / CONTINUOUS) slide switches | right-angle, actuators through the enclosure wall |
| Indicators | blue STATUS + green CHG side-view LEDs | visible from the enclosure side |
| Expansion | **STEMMA QT / Qwiic** port | switched 3.3 V and bus isolation: 0 µA when off; e.g. for a real CO₂ sensor |
| Protection | 2 × USBLC6-2SC6 | USB data lines and the STEMMA QT port |
| Board | Ø 72 mm round, bottom flat for the controls, 2 layers, 1.6 mm FR4 | 0.3 mm minimum drill; assembled by PCBWay |

**State (2026-10-08):** layout done, ERC 0 / DRC 0 with schematic parity; schematic PDF and PCBWay BOM generated.
Gerbers, the ESP32-C3 firmware port and bench validation are still open.

| v9 document | For |
|---|---|
| [`v9/README.md`](v9/README.md) | changes vs v8, pin map, power architecture, firmware port, outputs, next steps |
| [`v9/user-documentation.md`](v9/user-documentation.md) | people using the device |
| [`v9/design_review.md`](v9/design_review.md) | findings F1–F34 with evidence and validation checklists |
| [`v9/layout_constraints.md`](v9/layout_constraints.md) | layout rules |
| [`v9/power_budget.md`](v9/power_budget.md) | sleep floor, wake budget, battery life per WiFi mode |

---

## Revisions

| Rev | Folder | Summary | Docs |
|---|---|---|---|
| A | [`v1/`](v1/) | 108 × 108 mm square. ESP-12F (ESP8266) + CP2102N, BME688 breakout over STEMMA QT, servo from VBAT | [README](v1/README.md) |
| B | [`v2/`](v2/) | Same circuit on a **Ø 72 mm round** board, mounting holes, wind logo | [README](v2/README.md) |
| C | [`v3/`](v3/) | **BME688 soldered on-board**, copper keep-out under the sensor | [README](v3/README.md) |
| D | [`v4/`](v4/) | GPIO2 status LED, battery sensing, USB ESD, battery reverse-polarity FET, spare-GPIO header, fiducials, **5 V servo boost** | [README](v4/README.md) |
| E | [`v5/`](v5/) | Production / assembly refresh (PCBWay BOM, replacement power switch); battery-life analysis | [power budget](v5/power_budget.md) |
| F | [`v6/`](v6/) | Gated servo boost, **3-position WiFi mode switch**, side-view status LED, MΩ battery divider | [README](v6/README.md), [user docs](v6/user-documentation.md), [power budget](v6/power_budget.md) |
| G | [`v7/`](v7/) | **ESP32-C3** (native USB, no CP2102N), FET-driven power switch, servo-rail load switch, long-actuator edge switches, STEMMA QT port, charge-status input, antenna notch and sensor island | [README](v7/README.md), [design review](v7/design_review.md) |
| H | [`v8/`](v8/) | **Servo boost removed** (servo from VSYS), Espressif WROOM-02 footprint so the board keeps the 0.3 mm minimum drill. Fabrication outputs were generated | [README](v8/README.md), [design review](v8/design_review.md) |
| I | [`v9/`](v9/) | Re-placed and re-routed v8: **GPIO remap**, LDO at the module, smaller sensor island, no copper beside the antenna, C24 on the STEMMA QT rail | [README](v9/README.md) and the documents above |

Each revision's README lists what changed against the one before. From v7 on, the design reviews number their
findings (F1, F2, …) and carry them forward, so a finding keeps its number across revisions.

---

## Repository layout

```
README.md                   this overview
build_pcbway_bom.py         KiCad BOM export → PCBWay BOM (python build_pcbway_bom.py v9)
a-sample-of-PCBWay-BOM.xlsx PCBWay's BOM template, the format the script produces
wind.svg                    wind logo used on the back silkscreen (v2+)
vN/
  air-quality-pcb-vN.kicad_pro / .kicad_sch / .kicad_pcb
  README.md, design_review.md, layout_constraints.md, power_budget.md, user-documentation.md   (as available)
  bom_kicad_raw.csv → bom_pcbway_vN.csv, schematic_vN.pdf                                       (as generated)
  Espressif.pretty/, SamacSys_Parts.pretty/, fp-lib-table, air-quality-pcb-vN.3dshapes/       (v7+: vendor footprints and STEP models)
```

Not in git (see `.gitignore`): `gerbers/`, `*.rpt` (ERC/DRC reports), KiCad backups and lock files. Regenerate
them with the `kicad-cli` commands in each revision's README (KiCad 10).

### PCBWay BOM

1. Export the schematic BOM ungrouped, with the fields `Reference,Value,Footprint,Manufacturer,MPN,Description`, to
   `vN/bom_kicad_raw.csv` (command in the revision README).
2. `python build_pcbway_bom.py vN` groups it into PCBWay's columns and writes `vN/bom_pcbway_vN.csv`.

---

## Firmware

The firmware lives in the sibling [`air-quality-checker`](../air-quality-checker) repo. It currently targets the
**ESP8266 boards (v1–v6)**. The ESP32-C3 boards (v7–v9) need a port: PlatformIO `espressif32`, ESP-IDF deep sleep,
the new pin map, BME688 at 0x76. The steps are in [`v7/README.md`](v7/README.md#firmware-port-air-quality-checker-repo),
with the servo rules from v8 and the **v9 pin map** in [`v9/README.md`](v9/README.md#firmware-port-air-quality-checker-repo).
The v7/v8 and v9 pin maps differ, so a v8 build must not be flashed onto a v9 board.
