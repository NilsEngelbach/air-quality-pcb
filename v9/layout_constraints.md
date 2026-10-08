# v9 Layout Constraints

These are the rules for the v9 (rev I) board. The board is placed and routed; this file lists the rules it
follows, so a later change does not quietly break one. Each rule references a finding in
[`design_review.md`](design_review.md). Coordinates are board mm (KiCad), centre (55, 55), y grows downward.

**Changed vs v8:** GPIO remap (F27), C24 on QT_3V3 (F28), re-placement of the LDO, power path, servo switch,
USB ESD and buttons (F29), smaller sensor island (F30), no copper beside the antenna (F31), 0.8 / 0.4 mm
stitching (F32). Placement and routing history up to v8: [`../v7/layout_plan.md`](../v7/layout_plan.md),
[`../v8/layout_plan.md`](../v8/layout_plan.md).

---

## 1. Zoning

```
              ┌──── antenna notch (x 41–69) ────┐
     bare FR4 │  U1 ESP32-C3-WROOM-02 (55, 33.4) │ bare FR4      ← no copper above y ≈ 26.5 (F31)
              └──────────────────────────────────┘
   SW1/SW2, R1/C1 (left of U1)     U4 LDO + C10–C12 (below U1)      R20/R21, C17 (VBAT sense)
 ┌──────┐
 │ U5   │ sensor island          Q8, C23/C24, Q9/Q10, U8        D1, Q3, Q6/Q7, C20, C22, C19, C13 ─ J3 (right edge)
 └──────┘  (left edge)           (STEMMA QT block, J5)          U3 charger, R14, C9, R31/R32 ─ J4, Q4/Q5
              D3 ◜  SW4 (39)   ── J1 USB-C (56.5) ──   SW3 (66)  ◝ D2           ← bottom flat, y = 84
```

- Heat sources (U3, U4, U1) stay away from **U5**. In v9, U4 is 33 mm away, U1 40 mm and U3 56 mm (F13, F30).
- The **antenna end** of U1 points out of the board. Battery, servo, screws and USB cable stay
  ≥ 15 mm away from it in the housing.
- Signals leave the module on the side that faces their destination (F27): mode switch → left pads 3/4,
  servo PWM and VBAT sense → right pads 18/15.

## 2. ESP32-C3-WROOM-02 (U1) — F7, F9, F26, F31

| Rule | Value | Source |
|---|---|---|
| Footprint | `Espressif:ESP32-C3-WROOM-02` (vendor, `v9/Espressif.pretty`), origin (55, 33.4) | F26 |
| Antenna position | outside the board outline (best), or feed point at the edge; cut the board on both sides of and under the antenna | Espressif PCB layout guide |
| Keepout | board rule area **ANTENNA_KEEPOUT** x 29.5–80, y 15.4–26.5, F.Cu + B.Cu: no tracks / vias / pads / pour (footprints allowed). Plus pour-only keepouts x 27.5–83, y 15–26.5 on each layer. The footprint adds its own 18 × 6 mm keepout | F7, F31 |
| Housing | ≥ 15 mm free space around the antenna in all directions (battery!) | Espressif |
| GND | via fence along y = 27.5 (x 35.5–74.5, ~2 mm pitch, 0.8 / 0.4 mm); dense GND vias under the module (67 in v9) | Espressif, F31 |
| EPAD | 9 pads (0.7 mm, no drills), solid zone connection; **4 GND vias 0.6 / 0.3 mm in the gaps** at (55.385 \| 56.485, 33.15 \| 34.25), tented. Don't move them onto the pads (paste openings); keep other stitching off the EPAD | F26 |
| Drill | board minimum **0.3 mm** — no smaller vias anywhere | F26 |
| Decoupling | C2 10 µF + C3 100 nF at pad 1 (3V3), at (42 / 44, 29), vias straight to GND | Espressif |
| LDO | U4 directly below the module (53.1, 44.6); C10 at VIN, C11/C12 at VOUT — short +3V3 to pad 1 | F29 |
| EN | R1 10 k + C1 1 µF close to pad 2; SW1 RESET next to them | Espressif |
| USB | R24/R25 22 Ω **at the module** (IO19/IO18). D+/D− as a parallel pair, equal length, over solid GND, GND vias at transitions. Guideline < 30 mm and ≤ 1 via per line; v9 has 47–48 mm and 2 vias (accepted for full speed, F32) | Espressif |
| ADC input | C17 100 nF **at the ADC pad** (U1 pad 15 / IO3); the divider R20/R21 may sit at VBAT | F27 |
| Strap pull-ups | R2 (IO2), R5 (IO8), R3 (IO9): DC pull-ups, any position on their net (R5 sits at D3, R2 at Q8) | F9, F29 |

## 3. Servo rail — F2, F25, F29

No switching converter; the servo current is a slow motor load straight from VSYS.

1. **Q6** (75, 51), source on **VSYS** (0.8 mm), drain = **SERVO_PWR** (Power class) → C22 → C19 → C13 → J3.2.
   v9 route: 15.5 mm, F.Cu, no vias.
2. **C13 100 µF** (80.5, 54) right at J3 (motor bulk); **C19 22 µF** anywhere on SERVO_PWR.
3. Gate network **Q7 / R27 / R28 / C22** next to Q6, 0.2–0.3 mm. **C22** sits between SERVO_GATE and SERVO_PWR (soft start);
   keep it close to Q6.
4. **J3.3 (GND)** and C13's GND with ≥ 2 vias to the B.Cu plane: the servo's return current (up to ~0.6 A at start)
   should not flow through the module's ground area.
5. **SERVO_EN** (IO10 → R4, Q7 gate) and **SERVO_PWM** (IO0 → R17 at J3) are slow signals.
6. **C20 22 µF** stays as VSYS bulk at Q6 / Q3: it buffers the servo start on battery.

## 4. Charger, LDO, power path — F1, F4, F12

| Part | Rule |
|---|---|
| U3 MCP73831 (76.5, 68) | Large copper on pins 2 (GND, solid), 3 (VBAT) and 4 (VDD) with vias to B.Cu; J4 close to VBAT/VSS (datasheet §6.2); C7/C8 at VDD, C9 at VBAT. Up to ~1 W while fast charging. Pin necks at 0.65 mm are fine (F32) |
| U4 AP2112K (53.1, 44.6) | C10 at VIN, C11/C12 at VOUT; copper on GND/VIN for ≈ 0.45 W bursts. Fed by VSYS (0.8 mm, ~32 mm) |
| Q3 / D1 | at the servo switch (73, 54.8–58.3): VSYS is formed next to Q6 and C20 |
| Q4 / Q5 | on the battery path: short and wide (Power class). Q5 (81, 62) near J4; SW3 only carries the gate (PWR_GATE, R26), so its traces can be 0.2 mm |
| D1 | carries the servo current on USB too (B5819W, 1 A) |
| VBAT divider | R20/R21 at VBAT (68.5, 53.5), C17 at the ADC pad — see §2 |

## 5. Edge parts — how far they may overhang — F11, F18

The limit is the **frontmost copper or hole**: copper ≥ 0.5 mm (project rule; PCBWay min
0.3 mm), holes ≥ 0.5 mm from the routed edge. Bodies may overhang. Unchanged from v8.

| Part | Limiting feature | v9 placement | Result |
|---|---|---|---|
| **SW3** OS102011MA1QN1 | mounting-post pads end 0.5 mm behind the body front | (66, 81), body ~0.8 mm behind the flat | actuator **~3.2 mm** past the edge (accepted) |
| **SW4** OS103011MA7QP1 | same series and geometry | (39, 81) | actuator **~3.2 mm** past the edge |
| **J1** USB-C HRO TYPE-C-31-M-12 | front shield tab pads (1.85 mm behind the body front) | (56.5, 81.4) | receptacle face ≈ flush with the outer enclosure wall |
| **D3** KPA-3010 side LED (blue) | its pads, 0.8 mm behind the lens | (31.5, 81), on the arc left of the flat | lens up to ~0.3 mm past the edge; light pipe or thin window |
| **D2** KPA-3010SGC (green CHG) | same as D3 | (78.5, 81), mirror of D3 | same as D3 |
| **J5** STEMMA QT (JST SH, horizontal) | its SMD mounting tabs | (30, 67.5) | ≥ 15 mm from the antenna notch |
| **U1** antenna | keepout only | antenna end at or past the edge | see §2 |

- Enclosure slots for the switches: width ≥ 2.0 mm actuator + clearance; length ≈ actuator +
  travel (SPDT 2 mm → ~4 mm, SP3T 2 × 2 mm → ~6 mm) + clearance.
- On a Ø 72 mm circle, a straight face of width *w* has its corners
  36 − √(36² − (w/2)²) mm inside the edge: 9 mm → 0.28 mm, 12.6 mm → 0.56 mm, 18 mm → 1.14 mm.
- **PCBWay note:** parts overhang the bottom flat, and the sensor island hangs on a 4 mm neck — panelize with
  rails or tabs elsewhere, no breakaway tabs on those sides.

## 6. Track widths and vias — F5, F32

Net classes are in the project file (Freerouting reads them via `export_dsn`):

| Class | Width | Nets |
|---|---|---|
| Power | 0.8 mm | BAT_IN, VBAT_RAW, VBAT, VSYS, SERVO_PWR |
| Supply | 0.5 mm | VBUS, +3V3, GND |
| USB | 0.25 mm, diff pair 0.25 / 0.2 gap | USB_D±, USB_D*_CON, USB_D*_MCU |
| Default | 0.2 mm | signals (incl. SERVO_EN, SERVO_GATE, SERVO_PD) |

- Narrower segments are allowed only where the current is small or a pad forces a neck. The accepted
  list is in F32 (sensor-island +3V3, the VBAT_RAW gate/cap stubs, U3/U4/J1 pad necks, Q6 → C22).
  KiCad DRC does **not** check class widths, so re-check them by hand after any re-route.
- Vias: 0.6 / 0.3 and 0.8 / 0.4 mm only (minimum drill 0.3 mm). Stitching uses 0.8 / 0.4 mm.
- Prefer copper pours over long tracks for VBAT/VSYS where space allows.

## 7. Sensor island — F13, F30

- Island ≈ 9.5 × 7 mm (x 19.2–28.9, y 51.5–58.5), **4 mm neck** at y 53–57, **4 mm slots** above and below.
- U5 at (21.7, 55.0); C14/C15 on the island. C16 and R18/R19 stay on the main board.
- Keep the SENSOR_KEEPOUT (x 19–31, y 48–62, no pour on either layer). Only +3V3, GND, SDA and SCL cross the neck.
- Opening in the enclosure above the sensor; no heat source within ~15 mm.

## 8. STEMMA QT, charge detect and misc

- **J5** at (30, 67.5). **U8 (ESD) directly behind J5**, flow-through: J5.3/J5.4 → U8 pins 6/4,
  U8 pins 1/3 → Q9/Q10 drains. **Q9/Q10, R29/R30** between U8 and the main I²C bus. **Q8 + C23** feed QT_3V3;
  **C24 100 nF** between C23 and U8, close to U8 pin 5 / J5.2 (F28). IO2 (QT_PWR_N) is a slow signal.
- **USB ESD U6:** flow-through, connector on pins 6/4, MCU side on pins 1/3 (F29). Keep U6 between J1 and R24/R25.
- **R31/R32** (charge detect): together at the charger; CHG_DET is a slow signal to U1 pad 11.
- No test pads (decision: assembled boards; recovery = BOOT + RESET over USB with the enclosure open).
- BOOT/RESET (SW1/SW2) are internal: no enclosure access needed.
- **Re-routing:** a full re-route (delete all tracks and vias) also deletes the **4 EPAD vias** and the antenna
  via fence. Re-add the EPAD vias at the coordinates in §2, then stitch, then refill zones and run DRC with
  schematic parity.
