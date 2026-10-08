# Air Quality Checker — PCB v8 (rev H)

Eighth iteration, derived from the routed v7 board. Two changes: the **5 V servo boost is
gone** (the servo now runs from VSYS through the existing load switch), and the **board keeps
PCBWay's standard 0.3 mm minimum drill**: the ESP32-C3-WROOM-02 now uses Espressif's footprint, whose EPAD has no drills.

**State (2026-10-05): layout done, fabrication outputs exported.** Schematic ERC **0 errors / 0 warnings**
(`erc_v8.rpt`). Board DRC with schematic parity **0 errors, 0 unconnected** (`drc_v8.rpt`, also clean after a
zone refill); the only remaining warnings are 4 excluded silkscreen-clipped warnings (U1 at the antenna notch, J1 at the
bottom flat) and the 7 board-only footprints (H1–H4, FID1–3). Gerbers, drill, position file and the PCBWay
BOM are generated (see *Files*). What is left is the order itself and the bench validation. Rules:
[`layout_constraints.md`](layout_constraints.md); findings and validation checklists:
[`design_review.md`](design_review.md) (F1–F24 from v7, F25–F26 new).

For the v6 → v7 changes (ESP32-C3, CP2102N removal, switches, STEMMA QT, …) see [`../v7/README.md`](../v7/README.md).

---

## What changed vs v7

| # | Change | Why (finding) |
|---|---|---|
| 1 | **Boost removed:** U7 MT3608, L1 10 µH, D4 PMEG4030ER, C18 / C21 22 µF, R22 / R23 (feedback) | fewer parts; the servo runs from VSYS (F25) |
| 2 | **Servo rail = VSYS through Q6**: net `SERVO_PWR` (was BOOST_IN + SERVO_5V) = Q6 drain, C22, C19 22 µF, C13 100 µF, J3.2 | servo works on USB (≈ 4.5 V) and on battery (3.0–4.2 V); still 0 µA in sleep (F2, F25) |
| 3 | Nets renamed: **BOOST_EN → SERVO_EN** (IO10), BOOST_GATE → SERVO_GATE, BOOST_PD → SERVO_PD | no boost any more |
| 4 | **U1 footprint → `Espressif:ESP32-C3-WROOM-02`** (from [espressif/kicad-libraries](https://github.com/espressif/kicad-libraries), with STEP): EPAD = 9 pads, no drills | the stock footprint has 12 × 0.2 mm EPAD drills (F15, F26) |
| 5 | **4 GND vias 0.6 / 0.3 mm** in the EPAD gaps (tented); `min_through_hole_diameter` back to **0.3 mm** | PCBWay standard drill (F26) |
| 6 | Board rule area **ANTENNA_KEEPOUT** (28 × 11 mm, F.Cu + B.Cu) | Espressif's footprint only keeps out 18 × 6 mm; this keeps the stock footprint's larger keepout (F7, F26) |
| 7 | Net class **Power**: `/SERVO_5V` → `/SERVO_PWR`, `/BOOST_SW` dropped | (F5) |
| 8 | Title block / back silkscreen **rev H** | |
| 9 | **C19 moved** to (79.5, 49.5) next to C13/J3; SERVO_PWR runs Q6 → C22 → C19 → C13 → J3.2 on F.Cu, 0.8 mm, 25 mm | the boost output position no longer made sense (F25) |
| 10 | **GND stitching near the antenna:** a 15-via fence along the module's ground edge (y 27.5), a ~2.5 mm grid under the module, and vias on both sides of the antenna notch (the left side now has F.Cu pour) | Espressif layout guide: dense GND vias at the module and the antenna (F7) |
| 11 | Silkscreen pin labels **S / + / −** at the servo header J3 | J4 (LiPo) has none: the JST PH plug is keyed |

Everything else (power path, charger, LDO, STEMMA QT, switches, LEDs, outline, placement) is unchanged from v7.

## Pin map (ESP32-C3-WROOM-02)

| GPIO | Net | Function |
|---|---|---|
| IO0 | VBAT_SENSE | ADC1_CH0, divider 1 M / 270 k (4.2 V → 0.89 V, use 2.5 dB attenuation) |
| IO1 | VBUS_SENSE | ADC1_CH1, 5 V → 1.59 V (USB present) |
| IO2 | QT_PWR_N | **STEMMA QT power, active low** (strap pin, R2 10 k pull-up → port off at reset and in sleep) |
| IO3 | MODE_A | SW4 POS1 → LOW = WiFi **OFF** |
| IO4 | MODE_B | SW4 POS3 → LOW = **CONTINUOUS** (both HIGH = SPARSE) |
| IO5 | SERVO_PWM | servo signal via R17 |
| IO6 / IO7 | SDA / SCL | I²C: BME688 (**0x76**) + STEMMA QT port (through Q9/Q10) |
| IO8 | STATUS_LED_N | blue side LED D3, **active-low**; strap (10 k pull-up) |
| IO9 | BOOT | SW2, strap (10 k pull-up) |
| IO10 | **SERVO_EN** | HIGH = servo rail on (Q7 → Q6); R4 100 k pull-down keeps it off |
| IO18 / IO19 | USB D− / D+ | native USB Serial/JTAG |
| IO20 | CHG_DET | charger STAT via divider: LOW = charging (only valid with VBUS present), HIGH = done |
| IO21 | — | not connected (spare) |

## Power architecture

```
USB-C VBUS ─┬─► MCP73831 (303 mA) ─► VBAT_RAW ◄── Q4 (reverse-polarity) ◄── LiPo J4
            │        └─ STAT ─► D2 (green) / R31-R32 ─► IO20
            │                        │
            │                  Q5 (SW3 drives the gate)
            │                        ▼
            └─►|D1|──► VSYS ◄── Q3 (USB priority) ── VBAT
                        │
                        ├─► AP2112K-3.3 ─► +3V3 (ESP32-C3, BME688, LED) ─► Q8 (IO2) ─► QT_3V3 ─► J5
                        └─► Q6 (SERVO_EN via Q7) ─► SERVO_PWR (C19 22 µF + C13 100 µF) ─► J3
```

Servo supply: **≈ 4.5 V on USB** (VBUS − D1), **3.0–4.2 V on battery**. The SG92R is rated 4.8–6 V; on
battery it moves with less torque and speed (F25 — validate on the bench).

Sleep floor estimate unchanged: ≈ **66 µA** (ESP32-C3 5 µA + AP2112K 55 µA + VBAT divider 3.3 µA +
BME688 ~2 µA + R26 0.4 µA; servo rail and QT port 0). Measure before updating the battery tables.

## Firmware port (air-quality-checker repo)

As in [`../v7/README.md`](../v7/README.md#firmware-port-air-quality-checker-repo), with these servo changes:

- **IO10 is now `SERVO_EN`** (was BOOST_EN): drive it HIGH **≥ 50 ms before** a move (SERVO_PWR ramps at
  ~0.5 V/ms, ≈ 8 ms to VSYS), LOW again after the move and before deep sleep.
- **Skip or postpone servo moves when VBAT < ~3.5 V** on battery: the servo's start-up current can pull VSYS
  below the LDO's dropout and brown out the ESP32-C3 (F25).
- **Prefer moving the servo with WiFi off** (not during TX bursts). On a 500 mA USB 2.0 port, charger + WiFi + servo
  start can exceed the port budget.
- Never drive SERVO_PWM while SERVO_EN is LOW (it would back-feed the unpowered servo through R17).

## Files

| File | Purpose |
|---|---|
| `air-quality-pcb-v8.kicad_pro/.kicad_sch/.kicad_pcb` | v8 project (ERC clean; board DRC clean with parity) |
| `Espressif.pretty/`, `SamacSys_Parts.pretty/`, `fp-lib-table` | vendor footprints: U1 (Espressif) and SW4 (OS103011MA7QP1, Mouser / SamacSys) |
| `air-quality-pcb-v8.3dshapes/` | STEP models for the vendor footprints and the side LEDs |
| `design_review.md` | findings F1–F26 with evidence, sources and validation checklists |
| `layout_plan.md` | what changed on the board, and the remaining layout steps for v8 |
| `layout_constraints.md` | the rules: antenna, servo rail, edge overhang, widths |
| `schematic_v8.pdf` | plotted schematic |
| `erc_v8.rpt` / `drc_v8.rpt` | ERC (clean) / DRC with schematic parity (clean) |
| `gerbers/air-quality-pcb-v8-gerbers.zip` | **upload to PCBWay:** 9 Gerber layers + job file + drill file (Excellon, PTH and NPTH merged; smallest hole 0.30 mm) |
| `gerbers/` | the same files unzipped, plus `air-quality-pcb-v8-drl_map.pdf` and `air-quality-pcb-v8-pos.csv` (placement, mm, all top side: 71 parts + 3 fiducials) |
| `bom_kicad_raw.csv` → `bom_pcbway_v8.csv` | schematic BOM export → PCBWay BOM (38 lines, 71 placements; SW3, SW4, J3, J4 THT), built with `python build_pcbway_bom.py v8` |

### Regenerate outputs (run in `v8/`)

```sh
kicad-cli sch erc -o erc_v8.rpt air-quality-pcb-v8.kicad_sch
kicad-cli pcb drc --schematic-parity -o drc_v8.rpt air-quality-pcb-v8.kicad_pcb
kicad-cli pcb export gerbers -o gerbers/ --subtract-soldermask --check-zones \
  --layers "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts" air-quality-pcb-v8.kicad_pcb
kicad-cli pcb export drill -o gerbers/ --format excellon --generate-map --map-format pdf air-quality-pcb-v8.kicad_pcb
kicad-cli pcb export pos -o gerbers/air-quality-pcb-v8-pos.csv --format csv --units mm --side both air-quality-pcb-v8.kicad_pcb
kicad-cli sch export bom -o bom_kicad_raw.csv --fields "Reference,Value,Footprint,Manufacturer,MPN,Description" \
  --group-by "" air-quality-pcb-v8.kicad_sch
python ../build_pcbway_bom.py v8
```

Then zip the `*.g*` files and the `.drl` into `gerbers/air-quality-pcb-v8-gerbers.zip`.

## Next steps

1. **Order at PCBWay:** Gerber zip, `bom_pcbway_v8.csv`, `air-quality-pcb-v8-pos.csv`. Order note: SW3/SW4 are
   THT; parts overhang the bottom flat — no breakaway tabs on that side.
2. Optional before ordering: 1:1 paper print of the SW4 footprint against a real OS103011MA7QP1, and a 3D enclosure
   check ([`layout_plan.md`](layout_plan.md) step 5).
3. Firmware changes above, then the validation checklists in `design_review.md` (F25 and F26 are new).
