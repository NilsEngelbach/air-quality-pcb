# Air Quality Checker — PCB v9 (rev I)

Ninth iteration, derived from the routed v8 board. Same circuit and outline. The board is **re-placed and
re-routed**, the **GPIO assignment is cleaned up** so that each signal leaves the module towards its destination,
the **sensor island is smaller** with a narrower neck, **no copper sits beside the antenna** any more, and the
STEMMA QT rail gets a **100 nF cap at the connector** (C24).

**State (2026-10-08): layout done; schematic PDF and BOMs generated, Gerbers not yet.** Schematic ERC **0 violations**.
Board DRC with schematic parity **0 violations, 0 unconnected** (also after a zone refill). Parity lists the
7 board-only footprints (H1–H4, FID1–3) and one new warning, D2's value (`CHG` on the board, `CHG-GREEN` in the
schematic; F34). The four silkscreen-at-edge items are excluded as in v8. Still to do: Gerbers, drill and
position files (see *Regenerate outputs*), the order, the firmware port and the bench validation.

| Document | For |
|---|---|
| [`user-documentation.md`](user-documentation.md) | people using the device: controls, WiFi modes, setup, LEDs, troubleshooting |
| [`design_review.md`](design_review.md) | findings F1–F26 (v7/v8) and **F27–F34 (new in v9)**, each with validation checklists |
| [`layout_constraints.md`](layout_constraints.md) | the layout rules the v9 board follows: antenna, servo rail, island, widths |
| [`power_budget.md`](power_budget.md) | sleep floor, wake budget, battery life by WiFi mode (estimates, bench checklist) |

For v7 → v8 (boost removed, Espressif footprint) see [`../v8/README.md`](../v8/README.md). For v6 → v7
(ESP32-C3, switches, STEMMA QT, …) see [`../v7/README.md`](../v7/README.md).

---

## What changed vs v8

| # | Change | Why (finding) |
|---|---|---|
| 1 | **GPIO remap:** SERVO_PWM IO5 → **IO0**, VBAT_SENSE IO0 → **IO3** (ADC1_CH3), MODE_A IO3 → **IO4**, MODE_B IO4 → **IO5** | the mode switch now uses the module's left pads (towards SW4), servo and VBAT sense its right pads (towards J3 and the divider); shorter routes, fewer vias. **Firmware pin map changes** (F27) |
| 2 | **C24 100 nF** on QT_3V3 at J5 / U8 | HF decoupling at the connector and the ESD clamp; 0 µA in sleep (F28) |
| 3 | **LDO U4 + C10–C12 moved** right below the module (53.1, 44.6) | short +3V3 to the module (+3V3 copper 156 → 104 mm) (F29) |
| 4 | **Power path and servo switch regrouped** at J3: D1, Q3, C20, Q6, Q7, R27, R28, C22, C19, C13 | SERVO_PWR 25 → 15.5 mm, F.Cu, no vias (F29) |
| 5 | **USB ESD U6 rotated**, pin pairs flipped (connector on 6/4, MCU on 1/3) | still flow-through; connector-side D± 19 → 7.5 mm (F29) |
| 6 | RESET/BOOT, EN RC, VBAT divider, charge-detect divider, strap pull-ups, STEMMA QT FETs re-placed | shorter, uncrossed routes (F29) |
| 7 | **Sensor island** ≈ 9.5 × 7 mm, **4 mm neck**, **4 mm slots** (v8: ≈ 11.5 × 13 mm, 7 mm neck, 1 mm slots); U5 further out, C14/C15 on the island | better thermal isolation of the BME688 (F13, F30) |
| 8 | **ANTENNA_KEEPOUT** widened to x 29.5–80 (both layers), pour keepouts x 27.5–83; new GND via fence at y = 27.5 | no copper on the board shoulders beside the antenna (F7, F31) |
| 9 | Re-routed and re-stitched: 641 vias (605 GND, stitching at 0.8 / 0.4 mm); a few accepted width exceptions | (F5, F32) |
| 10 | Title block / back silkscreen **rev I** | |

Everything else is unchanged from v8: schematic topology, parts (apart from C24), outline apart from the island,
U1 position and EPAD vias, connectors, switches, LEDs and mounting holes.

## Pin map (ESP32-C3-WROOM-02)

| GPIO | Net | Function |
|---|---|---|
| IO0 | **SERVO_PWM** | servo signal via R17 (v8: IO5) |
| IO1 | VBUS_SENSE | ADC1_CH1, 5 V → 1.59 V (USB present) |
| IO2 | QT_PWR_N | **STEMMA QT power, active low** (strap pin, R2 10 k pull-up → port off at reset and in sleep) |
| IO3 | **VBAT_SENSE** | ADC1_CH3, divider 1 M / 270 k (4.2 V → 0.89 V, use 2.5 dB attenuation) (v8: IO0) |
| IO4 | **MODE_A** | SW4 POS1 → LOW = WiFi **OFF** (v8: IO3) |
| IO5 | **MODE_B** | SW4 POS3 → LOW = **CONTINUOUS**; both HIGH = SPARSE (v8: IO4) |
| IO6 / IO7 | SDA / SCL | I²C: BME688 (**0x76**) + STEMMA QT port (through Q9/Q10) |
| IO8 | STATUS_LED_N | blue side LED D3, **active-low**; strap (10 k pull-up) |
| IO9 | BOOT | SW2, strap (10 k pull-up) |
| IO10 | SERVO_EN | HIGH = servo rail on (Q7 → Q6); R4 100 k pull-down keeps it off |
| IO18 / IO19 | USB D− / D+ | native USB Serial/JTAG |
| IO20 | CHG_DET | charger STAT via divider: LOW = charging (only valid with VBUS present), HIGH = done |
| IO21 | — | not connected (spare) |

## Power architecture

Unchanged from v8:

```
USB-C VBUS ─┬─► MCP73831 (303 mA) ─► VBAT_RAW ◄── Q4 (reverse-polarity) ◄── LiPo J4
            │        └─ STAT ─► D2 (green) / R31-R32 ─► IO20
            │                        │
            │                  Q5 (SW3 drives the gate)
            │                        ▼
            └─►|D1|──► VSYS ◄── Q3 (USB priority) ── VBAT ─► R20/R21 ─► IO3
                        │
                        ├─► AP2112K-3.3 ─► +3V3 (ESP32-C3, BME688, LED) ─► Q8 (IO2) ─► QT_3V3 (C23, C24) ─► J5
                        └─► Q6 (SERVO_EN via Q7) ─► SERVO_PWR (C19 22 µF + C13 100 µF) ─► J3
```

Servo supply: **≈ 4.5 V on USB**, **3.0–4.2 V on battery** (F25). Sleep floor estimate **≈ 66 µA**. Battery
life by WiFi mode is in [`power_budget.md`](power_budget.md) (estimates until measured).

## Firmware port (air-quality-checker repo)

The firmware in [`../../air-quality-checker`](../../air-quality-checker) still targets the ESP8266 (v6 board).
The port follows [`../v7/README.md`](../v7/README.md#firmware-port-air-quality-checker-repo) (PlatformIO
`espressif32` / `esp32-c3-devkitm-1`, BSEC2 1.10.2610, BME688 at 0x76, `esp_deep_sleep`, `RTC_DATA_ATTR`) and
the v8 servo rules, **with the v9 pin map**:

```cpp
#define SERVO_PWM_PIN   0   // v8: 5
#define VBUS_SENSE_PIN  1
#define QT_PWR_N_PIN    2   // LOW = STEMMA QT on
#define VBAT_SENSE_PIN  3   // v8: 0 — ADC1_CH3, ADC_2_5db, VBAT = mV / 0.2126
#define MODE_A_PIN      4   // v8: 3 — LOW = OFF
#define MODE_B_PIN      5   // v8: 4 — LOW = CONTINUOUS
#define SDA_PIN         6
#define SCL_PIN         7
#define LED_PIN         8   // active-low
#define BOOT_PIN        9
#define SERVO_EN_PIN   10
#define CHG_DET_PIN    20   // LOW = charging (only with VBUS present)
```

- **Do not flash a v7/v8 pin map onto v9:** it would drive PWM into the battery divider and read the mode switch
  as an ADC.
- **Servo (F25):** SERVO_EN HIGH ≥ 50 ms before a move, LOW after it and before sleep; no PWM while SERVO_EN is LOW;
  skip moves below VBAT ≈ 3.5 V; move with WiFi idle.
- **Mode switch (F33):** read IO4/IO5 with `INPUT_PULLUP` at each wake, then switch them back to `INPUT`. If you use
  GPIO wake (switch gesture, instant mode change), enable pull-up + wake **only on the pin whose contact is open**.
  A pull-up on a closed contact costs ~70 µA in sleep and doubles the floor.
- **Re-provisioning:** BOOT/RESET are inside the enclosure. Add a switch gesture on SW4 (e.g. OFF → CONTINUOUS →
  OFF → CONTINUOUS within 5 s) and keep RESET-then-BOOT as the service path; `user-documentation.md` marks both.
- **Low battery (F19):** VBAT < ~3.3 V → one LED blink, then indefinite deep sleep.

## Files

| File | Purpose |
|---|---|
| `air-quality-pcb-v9.kicad_pro/.kicad_sch/.kicad_pcb` | v9 project (ERC clean; board DRC clean with parity) |
| `Espressif.pretty/`, `SamacSys_Parts.pretty/`, `fp-lib-table` | vendor footprints: U1 (Espressif) and SW4 (OS103011MA7QP1, Mouser / SamacSys) |
| `air-quality-pcb-v9.3dshapes/` | STEP models for the vendor footprints and the side LEDs |
| `README.md` | this file |
| `user-documentation.md` | end-user guide |
| `design_review.md` | findings F1–F34 with evidence, sources and validation checklists |
| `layout_constraints.md` | layout rules |
| `power_budget.md` | power and battery-life estimates, bench checklist |
| `schematic_v9.pdf` | plotted schematic |
| `bom_kicad_raw.csv` → `bom_pcbway_v9.csv` | schematic BOM export → PCBWay BOM (38 lines, 72 placements; SW3, SW4, J3, J4 THT; C24 joins the CL21B104KBCNNNC line), built with `python build_pcbway_bom.py v9` |
| *to generate* `gerbers/` | Gerbers, drill, position file — see below (`*.rpt` and `gerbers/` are git-ignored) |

### Regenerate outputs (run in `v9/`)

```sh
kicad-cli sch erc -o erc_v9.rpt air-quality-pcb-v9.kicad_sch
kicad-cli pcb drc --schematic-parity --refill-zones -o drc_v9.rpt air-quality-pcb-v9.kicad_pcb
kicad-cli sch export pdf -o schematic_v9.pdf air-quality-pcb-v9.kicad_sch
kicad-cli pcb export gerbers -o gerbers/ --subtract-soldermask --check-zones \
  --layers "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts" air-quality-pcb-v9.kicad_pcb
kicad-cli pcb export drill -o gerbers/ --format excellon --generate-map --map-format pdf air-quality-pcb-v9.kicad_pcb
kicad-cli pcb export pos -o gerbers/air-quality-pcb-v9-pos.csv --format csv --units mm --side both air-quality-pcb-v9.kicad_pcb
kicad-cli sch export bom -o bom_kicad_raw.csv --fields "Reference,Value,Footprint,Manufacturer,MPN,Description" \
  --group-by "" air-quality-pcb-v9.kicad_sch
python ../build_pcbway_bom.py v9
```

Then zip the `*.g*` files and the `.drl` into `gerbers/air-quality-pcb-v9-gerbers.zip`. Expect 72 placements
(v8: 71, + C24) and a smallest hole of 0.30 mm.

## Next steps

1. Housekeeping (F34): resolve the D2 value warning, fix the title-block comment ("(v7)") and the two keepout
   names, then generate Gerbers, drill and position files (and re-export the PDF/BOM if the schematic changed).
2. Optional before ordering: 3D export → enclosure check (switch actuators ~3.2 mm, USB face, LEDs, sensor-island
   opening, ≥ 15 mm around the antenna) and a 1:1 paper print of the SW4 footprint against a real part (F11).
3. **Order at PCBWay:** Gerber zip, `bom_pcbway_v9.csv`, position file. Order note: SW3/SW4 are THT; parts overhang the
   bottom flat, and the sensor island hangs on a 4 mm neck — no breakaway tabs on those sides.
4. Firmware port with the v9 pin map (above), then the validation checklists in `design_review.md` (F27–F33 are new)
   and the bench measurements in `power_budget.md` §8.
