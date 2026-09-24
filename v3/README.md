# Air Quality Checker — PCB v3 (round, on-board BME688)

Third iteration: the same round board as [v2](../v2/), but the Bosch **BME688 is
soldered directly on the PCB** instead of hanging off a STEMMA QT breakout.

> The power/USB/MCU section is identical to v2; only the sensor front-end
> changed. See the root [README](../README.md) for the full electrical
> description and the schematic↔firmware pin map.

---

## What changed vs. v2

| | v2 | v3 |
|---|---|---|
| Sensor | BME688 **breakout** on a STEMMA QT cable | **BME688 soldered on-board** (`U5`, LGA-8 3×3 mm) |
| Connector | J2 JST-SH 4-pin (STEMMA QT) | **removed** |
| Sensor support | on the breakout | **C14/C15/C16** decoupling + **R18/R19** I²C pull-ups on-board |
| Thermal | — | **copper keep-out** under the sensor on both layers |
| Shape / holes / logo | Ø 72 mm, 4 × M2.5, wind logo | unchanged |
| Rev | B | **C** |

Everything else is unchanged: ESP-12F, CP2102N, MCP73831, AP2112K,
DMG2305UX/B5819W power path, servo header, LiPo JST-PH, RESET/BOOT buttons,
deep-sleep jumper, PWR/CHG LEDs.

---

## The on-board BME688

| | |
|---|---|
| Ref | `U5` — `Sensor:BME680` symbol, value **BME688** |
| Footprint | `Package_LGA:Bosch_LGA-8_3x3mm_P0.8mm_ClockwisePinNumbering` |
| Interface | I²C, **address 0x77** |
| Decoupling | `C14` 100 nF (VDD), `C15` 100 nF (VDDIO), `C16` 10 µF bulk |
| Pull-ups | `R18`/`R19` 10 kΩ on SDA/SCL to +3V3 (the breakout used to provide these) |

Wiring (I²C mode):

| Pin | Name | Net | Note |
|---|---|---|---|
| 1, 7 | GND | `GND` | |
| 2 | CSB | `+3V3` | high ⇒ I²C mode |
| 3 | SDI | `SDA` | |
| 4 | SCK | `SCL` | |
| 5 | SDO | `+3V3` | high ⇒ address **0x77** (firmware `BME68X_I2C_ADDR_HIGH`) |
| 6 | VDDIO | `+3V3` | |
| 8 | VDD | `+3V3` | |

> The sensor sits near the top edge with a **4.4 mm copper keep-out** on both
> layers so the ground pour does not thermally load the gas sensor. Give the
> enclosure a vent above it.

> **ERC note:** the stock KiCad `Sensor:BME680` symbol types SDO as
> `bidirectional` (to cover SPI too). Since SDO is only the I²C address-select
> input here, the generated schematic retypes that one pin to `input`; this
> removes a spurious `pin_to_pin` warning against the LDO's power output.

---

## Mechanical

- **Diameter:** 72 mm (outline Ø 72.05 mm on Edge.Cuts).
- **Mounting holes:** 4 × M2.5 (2.7 mm drill) on the 45°/135°/225°/315° diagonals.
- **Connectors on the rim:**
  - USB-C (J1) — bottom
  - servo 3-pin header (J3) — right
  - LiPo JST-PH (J4) — left
- **Logo:** `wind.svg` converted to filled silkscreen polygons on the **bottom**
  silkscreen, with `AIR QUALITY CHECKER` / `REV C 2026`.

---

## Verification status

| Check | Result |
|---|---|
| ERC (schematic) | **0 errors, 0 warnings** |
| DRC (board) | **0 violations, 0 unconnected** |
| Nets | 32, all routed; GND pour on both layers |
| Schematic ↔ PCB netlist | exact match (32 nets, 52 footprints) |
| Sensor keep-out | no copper under `U5` on F.Cu/B.Cu (verified) |
| Autorouter | Freerouting 2.4.1 (Specctra DSN/SES) |

---

## Fabrication

Gerbers and drill files are in `gerbers/`. Recommended stack-up for
JLCPCB/OSHPark: 2 layers, 1.6 mm, HASL, 0.2 mm min trace.

### Regenerate outputs

```sh
kicad-cli pcb export gerbers --output gerbers/ \
  --layers "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts" \
  air-quality-pcb-v3.kicad_pcb
kicad-cli pcb export drill --output gerbers/ air-quality-pcb-v3.kicad_pcb
kicad-cli sch export bom --output bom_v3.csv air-quality-pcb-v3.kicad_sch
kicad-cli sch export pdf --output schematic_v3.pdf air-quality-pcb-v3.kicad_sch
kicad-cli pcb drc --output drc_v3.rpt air-quality-pcb-v3.kicad_pcb
kicad-cli sch erc --output erc_v3.rpt air-quality-pcb-v3.kicad_sch
```

---

## Design notes

- **Antenna keep-out:** U1's antenna region stays clear of copper.
- **GND:** a single filled pour on both layers with solid pad connections; the
  circular outline is approximated by a 96-point polygon inset 0.5 mm, and the
  sensor keep-out is cut from it.
- **Routing:** all signal traces ≥ 0.2 mm; the servo and power nets use wider
  traces. Freerouting's 150 µm segments were widened to 0.2 mm and re-verified.
- **Placement** was legalized against the *real* KiCad courtyards (including
  offset courtyards on connectors) so DRC is clean. The five small parts packed
  around the sensor have their silkscreen references hidden to keep the dense
  cluster DRC-clean.

---

## Files

| File | Purpose |
|---|---|
| `air-quality-pcb-v3.kicad_pro` | Project |
| `air-quality-pcb-v3.kicad_sch` | Schematic (ERC clean) |
| `air-quality-pcb-v3.kicad_pcb` | Board (DRC clean, fully routed) |
| `schematic_v3.pdf` | Plotted schematic |
| `render_v3_top.png` / `render_v3_bottom.png` | 3D renders |
| `bom_v3.csv` | Bill of materials |
| `gerbers/` | Gerbers + drill (fabrication) |
