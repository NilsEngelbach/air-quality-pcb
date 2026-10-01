# v7 Layout Constraints (placement guide)

These are the rules for placing the v7 board; the step-by-step order with coordinates is in
[`layout_plan.md`](layout_plan.md). Each rule references a finding in
[`design_review.md`](design_review.md). The outline already has the v7 cuts (antenna notch,
bottom flat, sensor island) and all parts are parked off-board for manual placement.
**Removed vs v6:** U2, C4, C5, Q1, Q2, R6, R7, JP1, the old ESP-12F and the mid-board "Keep out" zone.
**Added vs v6:** U1 WROOM-02, R24/R25, Q5/R26, Q6/Q7/R27/R28/C22, C20/C21, the STEMMA QT block
(J5, Q8, Q9, Q10, R29, R30, C23, U8) and R31/R32 (charge detect).

---

## 1. Zoning

The chosen zoning — **U1 top centre** with an antenna notch, **J1, SW4, SW3 and D3 on a bottom flat**,
**BME688 on a slotted island at the left edge**, boost and servo on the right, charger and power path
bottom-right/centre — and the step-by-step order with coordinates are in
[`layout_plan.md`](layout_plan.md).

- Heat sources (U3, U4, U7/L1, U1) stay away from **U5**.
- The **antenna end** of U1 points out of the board; battery, servo, screws and USB cable stay
  ≥ 15 mm away from it in the housing.

## 2. ESP32-C3-WROOM-02 (U1) — F7, F9

| Rule | Value | Source |
|---|---|---|
| Antenna position | outside the board outline (best), or feed point at the edge; cut the board on both sides of and under the antenna | Espressif PCB layout guide |
| Keepout | built into the footprint: 28 × 11 mm, all layers, no tracks / vias / pour / pads / parts. Keep it free of the board and all parts | footprint |
| Housing | ≥ 15 mm free space around the antenna in all directions (battery!) | Espressif |
| GND | dense GND vias along the module's GND pads and the board edge next to the antenna; solid GND under the rest of the module | Espressif |
| EPAD | solder to GND, 12 vias (0.3 mm drills, project footprint) | F15 |
| Decoupling | C2 10 µF + C3 100 nF at pin 1 (3V3), vias straight to GND | Espressif |
| EN | R1 10 k + C1 1 µF close to pin 2; SW1 RESET nearby | Espressif |
| USB | R24/R25 22 Ω **at the module** (IO19/IO18). D+/D− as a parallel pair, equal length, over solid GND, ≤ 1 via each, GND vias at transitions. 90 Ω is impractical on 1.6 mm 2-layer; keep the run short (< 30 mm) — fine for USB full-speed | Espressif |
| Strap pull-ups | R2 (IO2), R5 (IO8), R3 (IO9) near the module | F9 |

## 3. Servo boost — current loops — F2, F6

The high-di/dt loop of a boost converter is **SW → diode → output cap → GND → IC GND**.
That loop carries the 1.2 MHz pulsed current.

1. Put everything on **F.Cu** in roughly **8 × 8 mm**: C18 → U7 → L1 → D4 → C19/C21.
2. **D4 anode** right at U7 pin 1 (SW). **C19/C21** right at the D4 cathode; their GND pads
   return to U7 pin 2 over a short top-layer copper area, then ≥ 4 vias to B.Cu GND.
3. **C18 (22 µF)** directly at U7 pin 5 (IN), with its GND next to pin 2.
4. **L1** pad next to pin 1. The SW node is just pads plus a short, wide copper area — no trace.
5. **R22/R23** right at pin 3 (FB). Take the R22 top from the C19/C21 node, not from the far
   end of SERVO_5V. Keep FB away from L1 and the SW node.
6. Unbroken **B.Cu GND** under the whole converter; no signals under L1 or the SW node.
7. **C13 (100 µF)** at the servo header J3 (bulk for the motor), not in the switching loop.
8. **Q6/Q7/R27/R28/C22** (load switch) between VSYS and C18, close to the converter;
   BOOST_IN ≥ 0.8 mm.
9. Keep the converter away from the antenna keepout and from U5.

## 4. Charger, LDO, power path — F1, F4, F12

| Part | Rule |
|---|---|
| U3 MCP73831 | Large copper on pins 2 (GND, solid — done), 3 (VBAT) and 4 (VDD) with vias to B.Cu; battery connector J4 close to VBAT/VSS (datasheet §6.2); C7/C8 at VDD, C9 at VBAT. Up to ~1 W while fast charging |
| U4 AP2112K | C10 at VIN, C11/C12 at VOUT; copper on GND/VIN for ≈ 0.45 W bursts |
| Q3/Q4/Q5 | On the battery path: short and wide (Power class). Q5 near SW3; SW3 only carries the gate, so its traces can be thin |
| D1 | Between J1 VBUS and VSYS, short |
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
| **J5** STEMMA QT (JST SH, horizontal) | its SMD mounting tabs | connector face flush with the edge, cable exits outward | right edge, ≥ 15 mm from the antenna notch |
| **U1** antenna | keepout only (no copper in the antenna area) | antenna end at or past the edge | see §2 |

- Enclosure slots for the switches: width ≥ 2.0 mm actuator + clearance; length ≈ actuator +
  travel (SPDT 2 mm → ~4 mm, SP3T 2 × 2 mm → ~6 mm) + clearance.
- On a Ø 72 mm circle, a straight face of width *w* has its corners
  36 − √(36² − (w/2)²) mm inside the edge: 9 mm → 0.28 mm, 12.6 mm → 0.56 mm, 18 mm → 1.14 mm.
  Flats in the outline at these spots make the overhang uniform and the enclosure simpler.
- **PCBWay note:** parts overhang the edge on those sides — panelize with rails or tabs elsewhere.

## 6. Track widths — F5

Net classes are in the project file (Freerouting reads them via `export_dsn`):

| Class | Width | Nets |
|---|---|---|
| Power | 0.8 mm | BAT_IN, VBAT_RAW, VBAT, VSYS, BOOST_SW (pads only, see §3), SERVO_5V (+ route BOOST_IN like Power) |
| Supply | 0.5 mm | VBUS, +3V3, GND |
| USB | 0.25 mm, diff pair 0.25 / 0.2 gap | USB_D±, USB_D*_CON, USB_D*_MCU |
| Default | 0.2 mm | signals |

Prefer copper pours over long tracks for VBAT/VSYS where space allows.

## 7. Sensor — F13

- U5 on the cool side, ideally on a peninsula (milled slot on 2–3 sides, ≥ 1 mm wide, `Edge.Cuts`).
- Keep the SENSOR_KEEPOUT (no pour under U5); only the four I2C/power traces cross the slot bridge.
- Opening in the enclosure above the sensor; no heat source within ~15 mm.

## 8. STEMMA QT, charge detect and misc

- **J5** at the right edge (see §5). **U8 (ESD) directly behind J5**, flow-through: J5.3/J5.4 → U8 pins 6/4,
  U8 pins 1/3 → Q9/Q10 drains. **Q9/Q10, R29/R30** between U8 and the main I²C bus; **Q8 + C23** near J5
  (QT_3V3 0.3–0.5 mm). IO2 (QT_PWR_N) is a slow signal; route it anywhere.
- **R31/R32** (charge detect): R32 near U1 pin 11 (IO20), R31 near U3 STAT, or both together; signal only.
- No test pads (decision: assembled boards; recovery = BOOT + RESET over USB with the enclosure open).
- BOOT/RESET (SW1/SW2) are internal: no enclosure access needed, place them for routing convenience.
- After placement, follow the root `AGENTS.md` procedure (prep → GND fill → route → refill → DRC →
  stitching vias with `densifyRefs` updated to `["U1","U4","U7"]` → Gerbers).
