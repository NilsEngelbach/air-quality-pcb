# v8 Layout Constraints

These are the rules for the v8 board. The board started as the placed and routed v7 board, so placement
is done; what is left for v8 is in [`layout_plan.md`](layout_plan.md). Each rule references a finding in
[`design_review.md`](design_review.md).
**Removed vs v7:** the servo boost (U7 MT3608, L1, D4, C18, C21, R22, R23).
**Changed vs v7:** U1 footprint (Espressif, F26), servo rail `SERVO_PWR` straight from Q6 (F25),
board rule area ANTENNA_KEEPOUT, minimum drill 0.3 mm.

---

## 1. Zoning

Unchanged from v7: **U1 top centre** with an antenna notch, **J1, SW4, SW3 on the bottom flat** (D2/D3 on the arc
beside it), **BME688 on a slotted island at the left edge**, servo load switch and J3 on the right, charger and
power path bottom-right/centre. The original placement steps are in [`../v7/layout_plan.md`](../v7/layout_plan.md).

- Heat sources (U3, U4, U1) stay away from **U5**.
- The **antenna end** of U1 points out of the board; battery, servo, screws and USB cable stay
  ≥ 15 mm away from it in the housing.

## 2. ESP32-C3-WROOM-02 (U1) — F7, F9, F26

| Rule | Value | Source |
|---|---|---|
| Footprint | `Espressif:ESP32-C3-WROOM-02` (vendor, `v8/Espressif.pretty`), origin (55, 33.4) — pads at the same board positions as the stock footprint in v7 | F26 |
| Antenna position | outside the board outline (best), or feed point at the edge; cut the board on both sides of and under the antenna | Espressif PCB layout guide |
| Keepout | board rule area **ANTENNA_KEEPOUT** x 41–69, y 15.4–26.4 (28 × 11 mm), F.Cu + B.Cu: no tracks / vias / pads / pour (footprints allowed, so U1 itself passes). The footprint adds its own 18 × 6 mm keepout under the antenna | F7, F26 |
| Housing | ≥ 15 mm free space around the antenna in all directions (battery!) | Espressif |
| GND | dense GND vias along the module's GND pads and the board edge next to the antenna; solid GND under the rest of the module | Espressif |
| EPAD | 9 pads (0.7 mm, no drills), solid zone connection; **4 GND vias 0.6 / 0.3 mm in the gaps** at (55.385 \| 56.485, 33.15 \| 34.25), tented. Don't move them onto the pads (paste openings) | F26 |
| Drill | board minimum **0.3 mm** — no smaller vias anywhere | F26 |
| Decoupling | C2 10 µF + C3 100 nF at pin 1 (3V3), vias straight to GND | Espressif |
| EN | R1 10 k + C1 1 µF close to pin 2; SW1 RESET nearby | Espressif |
| USB | R24/R25 22 Ω **at the module** (IO19/IO18). D+/D− as a parallel pair, equal length, over solid GND, ≤ 1 via each, GND vias at transitions. 90 Ω is impractical on 1.6 mm 2-layer; keep the run short (< 30 mm) — fine for USB full-speed | Espressif |
| Strap pull-ups | R2 (IO2), R5 (IO8), R3 (IO9) near the module | F9 |

## 3. Servo rail — F2, F25

No switching converter any more; the servo current is a slow motor load straight from VSYS.

1. **Q6** (load switch) source on **VSYS** (0.8 mm), drain = **SERVO_PWR** (Power class, 0.8 mm) → C19 → C13 → J3.2.
2. **C13 100 µF** right at J3 (motor bulk); **C19 22 µF** may sit anywhere on SERVO_PWR (it was a boost output cap).
3. Gate network **Q7 / R27 / R28 / C22** next to Q6, 0.2–0.3 mm. **C22** sits between SERVO_GATE and SERVO_PWR (soft start);
   keep it close to Q6.
4. **J3.3 (GND)** and C13's GND with ≥ 2 vias to the B.Cu plane: the servo's return current (up to ~0.6 A at start)
   should not flow through the module's ground area.
5. **SERVO_EN** (IO10 → R4, Q7 gate) is a slow signal: any route.
6. **C20 22 µF** stays as VSYS bulk next to Q6's source / U4 VIN — it buffers the servo start on battery.

## 4. Charger, LDO, power path — F1, F4, F12

| Part | Rule |
|---|---|
| U3 MCP73831 | Large copper on pins 2 (GND, solid — done), 3 (VBAT) and 4 (VDD) with vias to B.Cu; battery connector J4 close to VBAT/VSS (datasheet §6.2); C7/C8 at VDD, C9 at VBAT. Up to ~1 W while fast charging |
| U4 AP2112K | C10 at VIN, C11/C12 at VOUT; copper on GND/VIN for ≈ 0.45 W bursts |
| Q3/Q4/Q5 | On the battery path: short and wide (Power class). Q5 near SW3; SW3 only carries the gate, so its traces can be thin. In v8 they also carry the servo current on battery |
| D1 | Between J1 VBUS and VSYS, short. On USB it carries the servo current too (B5819W, 1 A) |
| C20 | VSYS bulk next to Q6 source / U4 VIN |

## 5. Edge parts — how far they may overhang — F11, F18

The limit is the **frontmost copper or hole**: copper ≥ 0.5 mm (project rule; PCBWay min
0.3 mm), holes ≥ 0.5 mm from the routed edge. Bodies may overhang.

| Part | Limiting feature | Placement | Result |
|---|---|---|---|
| **SW3** OS102011MA1QN1 | mounting-post pads end 0.5 mm behind the body front | body front **flush with the edge** | actuator **4.0 mm** past the edge |
| **SW4** OS103011MA7QP1 | same series and geometry | body front flush with the edge | actuator **4.0 mm** past the edge |
| **J1** USB-C HRO TYPE-C-31-M-12 | front shield tab pads (1.85 mm behind the body front) | body front up to **~1.3 mm** past the edge (v6: 0.7 mm) | aim: receptacle face ≈ flush with the outer enclosure wall |
| **D3** KPA-3010 side LED | its pads, 0.8 mm behind the lens | lens up to **~0.3 mm** past the edge (v6: 0.2 mm) | better: flush, plus a light pipe or thin window |
| **D2** KPA-3010SGC (green CHG) | same as D3 | same as D3 | on the arc right of the flat, mirror of D3 |
| **J5** STEMMA QT (JST SH, horizontal) | its SMD mounting tabs | connector face flush with the edge, cable exits outward | ≥ 15 mm from the antenna notch |
| **U1** antenna | keepout only (no copper in the antenna area) | antenna end at or past the edge | see §2 |

- Enclosure slots for the switches: width ≥ 2.0 mm actuator + clearance; length ≈ actuator +
  travel (SPDT 2 mm → ~4 mm, SP3T 2 × 2 mm → ~6 mm) + clearance.
- On a Ø 72 mm circle, a straight face of width *w* has its corners
  36 − √(36² − (w/2)²) mm inside the edge: 9 mm → 0.28 mm, 12.6 mm → 0.56 mm, 18 mm → 1.14 mm.
- **PCBWay note:** parts overhang the edge on those sides — panelize with rails or tabs elsewhere.

## 6. Track widths — F5

Net classes are in the project file (Freerouting reads them via `export_dsn`):

| Class | Width | Nets |
|---|---|---|
| Power | 0.8 mm | BAT_IN, VBAT_RAW, VBAT, VSYS, SERVO_PWR |
| Supply | 0.5 mm | VBUS, +3V3, GND |
| USB | 0.25 mm, diff pair 0.25 / 0.2 gap | USB_D±, USB_D*_CON, USB_D*_MCU |
| Default | 0.2 mm | signals (incl. SERVO_EN, SERVO_GATE, SERVO_PD) |

Vias: 0.6 / 0.3 and 0.8 / 0.4 mm only (minimum drill 0.3 mm). Prefer copper pours over long tracks for VBAT/VSYS where space allows.

## 7. Sensor — F13

- U5 on the cool side, on the slotted island (unchanged from v7).
- Keep the SENSOR_KEEPOUT (no pour under U5); only the four I2C/power traces cross the slot bridge.
- Opening in the enclosure above the sensor; no heat source within ~15 mm.

## 8. STEMMA QT, charge detect and misc

- **J5** at the edge (see §5). **U8 (ESD) directly behind J5**, flow-through: J5.3/J5.4 → U8 pins 6/4,
  U8 pins 1/3 → Q9/Q10 drains. **Q9/Q10, R29/R30** between U8 and the main I²C bus; **Q8 + C23** near J5
  (QT_3V3 0.3–0.5 mm). IO2 (QT_PWR_N) is a slow signal; route it anywhere.
- **R31/R32** (charge detect): R32 near U1 pin 11 (IO20), R31 near U3 STAT, or both together; signal only.
- No test pads (decision: assembled boards; recovery = BOOT + RESET over USB with the enclosure open).
- BOOT/RESET (SW1/SW2) are internal: no enclosure access needed.
- Re-routing with the root `AGENTS.md` procedure: stitching vias with `densifyRefs: ["U1","U4"]` (U7 no longer exists).
  Note that its step 1 (`delete_trace net="*"`, `includeVias=true`) also deletes the **4 EPAD vias** — re-add them
  at the coordinates in §2.
