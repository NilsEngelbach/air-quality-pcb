# Air Quality Checker — PCB v4 (round, on-board BME688 + refinements)

Fourth iteration: the [v3](../v3/) round board with a batch of functional and
manufacturing improvements — a proper activity LED, battery monitoring, USB ESD
protection, battery reverse-polarity protection, a spare-GPIO header, fiducials,
and a 5 V boost for the servo.

> The core (ESP-12F, CP2102N, MCP73831, AP2112K, power path, on-board BME688)
> is unchanged from v3. See the root [README](../README.md) for the full
> electrical description and the schematic↔firmware pin map.

---

## What changed vs. v3

| | v3 | v4 |
|---|---|---|
| Power LED | `D3` **always-on** PWR-RED (~1.3 mA, even in deep sleep) | `D3` is now a **GPIO2 status LED** (active-LOW, dark in deep sleep) |
| Battery monitoring | — | **`VBAT_SENSE`** divider into the ESP **ADC/TOUT** (R20/R21/C17) |
| USB protection | none | **`U6` USBLC6-2SC6** ESD array in-line on D+/D− |
| Battery protection | none | **`Q4` P-FET** reverse-polarity protection at the LiPo input |
| Expansion | — | **`J5`** 1×4 header: GPIO12 / GPIO14 / +3V3 / GND |
| Assembly | — | **3 fiducials** (FID1–3) |
| Servo rail | VSYS (~3.7–4.7 V) | **`U7` MT3608 5 V boost** → `SERVO_5V` |
| USB-C port | faced **along** the board edge (cable blocked by the board) | **rotated to face the board edge** — cable plugs in |
| Part choices | some footprints had no 3D model | swapped to **modeled equivalents** (see below) |
| Rev | C | **D** |

Everything else is unchanged: round Ø 72 mm, 4 × M2.5 holes, wind logo,
RESET/BOOT buttons, deep-sleep jumper, CHG LED, servo header, LiPo JST-PH.

---

## New blocks

### Status LED (replaces the power LED)
`D3` (STATUS) is wired `+3V3 → R16 1 kΩ → D3 → GPIO2`, i.e. **active-LOW** to
match the firmware (`LED_PIN = 2`). When the firmware drives GPIO2 low the LED
lights; in deep sleep the ESP only weakly holds the pin (~2 µA), so the LED goes
dark. This removes the ~1.3 mA that the old always-on PWR-LED drew 24/7.

### Battery voltage sense
`VBAT → R20 100 kΩ → VBAT_SENSE → R21 27 kΩ → GND`, with `C17` 100 nF filtering,
into **U1 pin 2 (ADC/TOUT)**. 4.2 V → ~0.89 V, inside the ESP8266 ADC's 0–1.0 V
range. Firmware can read it to estimate charge.

### USB ESD protection
`U6` (USBLC6-2SC6) sits in-line between the USB-C connector and the CP2102N:
the connector side is `USB_DP_CON`/`USB_DM_CON`, the chip side is `USB_D+`/`USB_D-`.
`VBUS` and `GND` are the clamp rails.

### Battery reverse-polarity protection
`Q4` (DMG2305UX P-FET): **drain → `BAT_IN` (J4)**, **source → `VBAT_RAW`**,
**gate → GND**. A correctly-wired cell turns the FET on; a reversed cell keeps it
off and its body diode blocks. (The JST-PH connector is keyed, so this is
belt-and-suspenders. Note the charger, which lives on `VBAT_RAW`, is not isolated
from a reversed cell while USB is plugged in.)

### Spare-GPIO breakout
`J5` 1×4: **1 = GPIO12, 2 = GPIO14, 3 = +3V3, 4 = GND** — the two usable free
ESP8266 GPIOs, for a future second sensor.

### Servo 5 V boost
`U7` (MT3608) steps `VSYS` up to `SERVO_5V` ≈ **5.07 V**
(`Vout = 0.6 V × (1 + R22/R23) = 0.6 × (1 + 82 k/11 k)`), so the SG92R sees its
rated 4.8–6 V. `L1` = 10 µH, `D4` = SS34 Schottky, `C18` = 10 µF in,
`C19` = 22 µF out, `EN` tied to `VSYS`. `C13` (100 µF) stays as the servo bulk cap.

### Fiducials
Three `Fiducial_1mm_Mask2mm` marks on the outer ring for pick-and-place alignment.
They are placed **after** routing (at track-free spots) so they can't interfere
with the autorouter or end up sitting on a trace.

### USB-C orientation & part choices
The USB-C receptacle is rotated so its **port faces the board edge** (the v3
orientation had it facing along the edge, which would have blocked the cable).
The connector sits at the bottom edge; the spare header `J5` is 2 mm to the side
with vertical pins, so it does not obstruct the cable.

For a complete 3D view, footprints that KiCad ships models for were preferred:

| Ref | Part | Footprint | 3D model |
|---|---|---|---|
| `J1` | USB-C (HRO TYPE-C-31-M-12) | `USB_C_Receptacle_HRO_TYPE-C-31-M-12` | **stand-in**: GCT USB4105 (equivalent 16P top-mount) |
| `SW1`,`SW2` | tactile reset/boot | `SW_Push_1P1T_NO_CK_KMR2` | yes |
| `SW3` | power switch | `SW_SPDT_PCM12` | yes |
| `J4` | LiPo | `JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical` (THT) | yes |

> `J1` keeps the HRO part (and its exact footprint) because the modelled USB-C
> footprints (GCT/Amphenol) perturb the autorouter enough to leave a net
> unrouted on this dense board; only its 3D *model* is swapped for rendering.
> The other three are real modelled parts and route cleanly.

---

## Verification status

| Check | Result |
|---|---|
| ERC (schematic) | **0 errors, 0 warnings** |
| DRC (board) | **0 violations, 0 unconnected** |
| Nets | 41, all routed (670 tracks, 80 vias) |
| Schematic ↔ PCB netlist | exact match (41 nets, 65 footprints) |
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
  air-quality-pcb-v4.kicad_pcb
kicad-cli pcb export drill --output gerbers/ air-quality-pcb-v4.kicad_pcb
kicad-cli sch export bom --output bom_v4.csv air-quality-pcb-v4.kicad_sch
kicad-cli sch export pdf --output schematic_v4.pdf air-quality-pcb-v4.kicad_sch
kicad-cli pcb drc --output drc_v4.rpt air-quality-pcb-v4.kicad_pcb
kicad-cli sch erc --output erc_v4.rpt air-quality-pcb-v4.kicad_sch
```

---

## Design notes

- **Antenna keep-out:** U1's antenna region stays clear of copper.
- **GND:** a single filled pour on both layers; the circular outline is a
  96-point polygon inset 0.5 mm, and the sensor keep-out is cut from it.
- **Routing:** all signal traces ≥ 0.2 mm. Freerouting's 150 µm segments were
  widened to 0.2 mm and re-verified.
- **Silkscreen:** the small passives packed into the sensor, battery-sense and
  servo-boost clusters have their reference text hidden (their refs would clip
  neighbours); the BOM still lists them.
- **ERC note:** the stock `Sensor:BME680` symbol types SDO as `bidirectional`;
  since it is only the I²C address-select input here, the generated schematic
  retypes that one pin to `input`.

---

## Files

| File | Purpose |
|---|---|
| `air-quality-pcb-v4.kicad_pro` | Project |
| `air-quality-pcb-v4.kicad_sch` | Schematic (ERC clean) |
| `air-quality-pcb-v4.kicad_pcb` | Board (DRC clean, fully routed) |
| `schematic_v4.pdf` | Plotted schematic |
| `render_v4_top.png` / `render_v4_bottom.png` | 3D renders |
| `bom_v4.csv` | Bill of materials |
| `gerbers/` | Gerbers + drill (fabrication) |
