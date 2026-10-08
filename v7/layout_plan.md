# v7 Manual Layout Plan

A step-by-step placement and routing plan for the v7 board, starting with the
outline and the big parts. It implements the rules in
[`layout_constraints.md`](layout_constraints.md) (findings F-numbers →
[`design_review.md`](design_review.md)) with these fixed requirements:

- **MCU (U1) top centre**
- **USB-C (J1) bottom centre**
- **power switch SW3, WiFi switch SW4, status LED D3 and charge LED D2 on the bottom edge**
- BOOT/RESET internal only; STEMMA QT port J5 on the left edge

Coordinates are board mm (KiCad), centre (55, 55), radius 36, y grows downward
(top edge y = 19, bottom edge y = 91). They are **starting points**: confirm each step
with the courtyard and DRC checks listed.

```
                        ┌──── antenna notch ────┐
               H3 ●    │   U1 ESP32-C3-WROOM-02  │    ● H4
                       │  C2/C3·R1/C1 │ R24/R25·C17│
     ┌─slot─┐          └──────────────────────────┘
     │ U5   │◄bridge      SW1 SW2 (buttons)          boost U7/L1/D4    J3
     │BME688│  R18/R19                     Q6/Q7    C18–C21  C13     servo
     └─slot─┘  Q8 Q9 Q10          power path: D1 Q3 U4 C10–12 C20
   J5 QT ◄U8   R29 R30 C23                         charger U3, Q4, Q5, J4
               H2 ●                                     ● H1
           D3 ╲   [  SW4  ] [ J1 USB-C ] [ SW3 ]   ╱ D2
                ─────────── bottom flat ──────────
```

Zoning logic: the **heat sources** (charger, LDO, boost, module) sit top, right and bottom-right.
The **sensor** sits alone on the left, on a slotted island. Signal pins line up with the module sides:
I²C, LED and BOOT are on its **left** pins (sensor left); BOOST_EN, USB and ADC are on its
**right** pins (boost right, USB down the right-centre).

---

## Step 0 — Decisions and housekeeping (before moving anything)

1. Decisions (done): charger R14 = 3.3 k (303 mA), LDO stays AP2112K, protected cells, buttons internal,
   bottom flat + antenna notch + sensor island are already cut.
2. Set the grid to 0.25 mm (0.1 mm for fine work) and enable courtyard display.
3. Remember the placement aids: the new parts are in the staging area at x ≈ 100–150.
   The old U5 position (53.5, 23.2) and the **SENSOR_KEEPOUT** rule area at the top are now
   where the module goes — they move in step 4.
4. **FID3** is already moved to (30, 40) (it sat on the sensor slot). **Move FID2** (24.26, 68.82) out of
   the STEMMA QT spot, e.g. to (27.5, 74.5). Keep the three fiducials non-collinear and near the edge.

**Check:** nothing yet.

## Step 1 — Board outline: bottom flat and antenna notch (Edge.Cuts)

*(Done — the cuts below are in the board file.)*

1. **Bottom flat (F18):** replace the bottom arc with a straight line at **y = 84** — chord from
   x ≈ 33.7 to 76.3 (≈ 42.7 mm). That gives one straight front face for SW4, J1 and SW3
   (all straight-fronted parts, see step 2). Enclosure: same flat.
2. **Antenna notch (F7):** a rectangular cut-out **x 41 … 69**, from the circle down to **y = 26.3**,
   so the WROOM-02 antenna hangs over air (Espressif's preferred "antenna outside the base board",
   while the board keeps its round outline). The footprint keepout (28 × 11 mm) then lies
   almost entirely in the notch.
   *Alternative without a notch:* same U1 position, antenna over the keepout (no copper);
   electrically acceptable, slightly weaker RF.
3. **Sensor island slot (F13)** — on the left edge, see step 4 for the shape.
4. Mounting holes H1–H4 stay where they are (enclosure); fiducials as in step 0.

**Check:** `Edge.Cuts` closed (DRC "board outline" clean); GND zones refill inside the new outline.

## Step 2 — Edge parts on the bottom flat (largest mechanical constraints first)

All front faces sit on the flat (y = 84). Left → right: **D3 · SW4 · J1 · SW3 · D2**.

| Ref | Rotation | Position (approx.) | Edge rule |
|---|---|---|---|
| **J1** USB-C | receptacle opening down | origin ≈ (55, 81.3) | body front ≈ 1.0 mm past the edge (max ~1.3 mm). Front shield pads ≥ 0.5 mm inside the edge |
| **SW4** OS103011MA7QP1 | actuator down | pin 1 ≈ (36.4, 81.75) | **body front flush with y = 84** (pin row 2.15 mm behind it) → actuator 4 mm out |
| **SW3** OS102011MA1QN1 | actuator down | pin 1 ≈ (65.6, 81.75) | same as SW4 |
| **D3** KPA-3010 (blue status) | lens facing outward at ~133° | ≈ (30.9, 80.8), on the arc just left of the flat | lens flush to ≤ 0.3 mm past the edge; pads ≥ 0.5 mm inside |
| **D2** KPA-3010SGC (green CHG) | lens facing outward at ~47° | ≈ (79.1, 80.8), on the arc just right of the flat (mirror of D3) | same as D3; clear of H1's keepout (x 71–77, y 71–77) |

- Order rationale: SW3 and D2 sit next to the charger/power area (SW3's gate trace goes to Q5, D2 is
  driven from the charger's STAT pin). SW4 and D3 sit on the left because IO8 (LED) is on the module's left pins.
- Courtyards: SW4 spans x ≈ 32.7–48.1, J1 ≈ 49.7–60.3, SW3 ≈ 61.9–73.3. Keep ≥ 1 mm gaps.
  H2/H1 keepouts end at y = 77.1 — the switch bodies start at y ≈ 79.
- Physical order of the WiFi switch: POS1 (OFF) … POS3 (CONTINUOUS). With the actuator pointing down,
  check which end is POS1 and label the silkscreen **OFF – SPARSE – CONT** and **ON / OFF** accordingly.
- **U6 (USBLC6)** directly behind J1, ≈ (55, 75); **R10/R11** (CC 5.1 k) between J1 and U6;
  **C6** (VBUS bulk) next to J1's VBUS pins.

**Check:** `check_courtyard_overlaps`; DRC copper-edge on J1/SW3/SW4/D3; 3D view — the actuators and the USB face
line up on the flat.

## Step 3 — MCU U1 at the top centre

1. **U1** origin **(55, 33.3)**, rotation 0 (antenna up). The antenna end is at y ≈ 20.2, the module bottom at y ≈ 40.2,
   pads 1/18 at y = 27.3. The notch edge (26.3) clears the pads by 0.55 mm.
2. **Left-side pins** (x ≈ 46.3): 1 3V3 · 2 EN · 3 IO4 · 4 IO5 · 5 IO6 · 6 IO7 · 7 IO8 · 8 IO9 · 9 GND.
   Place in the column x ≈ 39.5–44.5 (between H3's keepout, which ends at x = 38.9, and the pads):
   - **C2 10 µF + C3 100 nF** at pin 1 (y ≈ 28–30), GND vias right at their pads.
   - **R1 10 k + C1 1 µF** at pin 2 (EN).
   - **R5** (IO8 pull-up) near pin 7; **R3** (IO9 pull-up) near pin 8.
3. **Right-side pins** (x ≈ 63.8): 18 IO0 · 17 IO1 · 16 IO2 · 15 IO3 · 14 IO19 · 13 IO18 · 12 TXD · 11 RXD · 10 IO10.
   Column x ≈ 65.5–70.5 (H4's keepout starts at x = 71.1):
   - **C17 100 nF right at pin 18 (IO0)**: VBAT_SENSE is a 1 MΩ node. R21 270 k next to it,
     R20 1 M may be further away on the VBAT side.
   - **R2** (IO2 pull-up = STEMMA QT power off) at pin 16.
   - **R32 18 k** (charge-detect divider bottom) near pin 11 (IO20).
   - **R24/R25 22 Ω** right at pins 14/13 (USB D+/D−).
   - **R4 100 k** (BOOST_EN pull-down) at pin 10.
4. **Buttons SW1 (RESET) / SW2 (BOOT):** internal only (decision) — below the module, ≈ (49.5, 46) and
   (56, 46), or wherever routing is easiest. Keep them reachable with the enclosure open (service/recovery).
5. Keep **all other parts and copper out of the notch/keepout**, and nothing taller than the module
   within a few mm of the antenna.

**Check:** courtyards; DRC rule-area violations around U1 = 0.

## Step 4 — Sensor island on the left edge (F13)

1. **Move U5** to ≈ **(25, 55)**. Orient it so the **pin row 5–8** (SDO, VDDIO, GND, VDD) faces the
   bridge, i.e. points toward the board centre (+x).
2. **Move the SENSOR_KEEPOUT** rule area (both layers) with it, centred on U5.
3. **Slot** (Edge.Cuts, 1.0 mm wide): an island of about x 19.5–31 × y 48–62. Horizontal slots at
   y ≈ 48 and y ≈ 62 from the outer edge to x = 31; vertical slot pieces at x = 31 for y 48–51.5 and 58.5–62.
   That leaves a **~7 mm bridge** (y 51.5–58.5) to the main board.
4. **On the island:** C14 at pin 8 (VDD), C15 at pin 6 (VDDIO), both GND pads to pin 7 (see the
   C14/C15/C16 notes), **SDO (pin 5) to GND** (I²C address 0x76 — a short trace to the GND via;
   pin 6 sits between it and pin 7), CSB (pin 2) to +3V3, pin 1 GND.
5. **On the main-board side of the bridge:** C16 10 µF (where +3V3 enters), R18/R19 I²C pull-ups
   ≈ (34, 52–56).
6. Nothing hot within ~15 mm: the nearest heat source, the module, is ~22 mm away; the charger and LDO are at the other side.

**Check:** island ≥ 0.5 mm copper-to-slot clearance; only +3V3, GND, SDA, SCL cross the bridge.

## Step 5 — Power: charger, battery path, LDO (bottom-right and centre)

Work outward from the USB VBUS pins and the battery connector.

1. **J4 LiPo** at the right-lower rim, ≈ **(83, 64)**, rotated so the cable exits toward the battery
   compartment. Keep the battery itself ≥ 15 mm from the antenna (enclosure).
2. **Charger U3** ≈ **(68, 64)** (between H1's keepout, which starts at y = 71.1, and the boost area):
   C7 4.7 µF + C8 100 nF at VDD (pin 4), C9 4.7 µF at VBAT (pin 3), R14 3.3 k at PROG, R15 next to it
   (D2 itself is on the edge, step 2), **R31 10 k** at STAT (CHG_DET divider top; the CHG_DET trace runs to
   R32/IO20). **Large copper on pins 2/3/4 with vias** (≈ 0.4 W typ., ≤ 0.85 W while charging, F12).
3. **Battery path** (Power class, short): J4 → **Q4** (reverse polarity) → **Q5** (power FET,
   ≈ (72, 70)… place near SW3's gate trace) → VBAT → **Q3** → VSYS.
   R26 10 M next to Q5's gate/source. The SW3 gate trace can be thin (signal).
4. **Power path + LDO** in the centre-bottom above J1, ≈ x 48–62 × y 60–72:
   **D1** (VBUS → VSYS), **R9**, **U4 AP2112K** with C10 at VIN, C11/C12 at VOUT, **C20** VSYS bulk.
   R20/R21 divider start from VBAT here (R20 1 M); the VBAT_SENSE trace runs up to C17 at the module.
5. **VBUS sense R12/R13** near J1/D1; the VBUS_SENSE trace goes to IO1 (module right side).

**Check:** VBAT_RAW → VSYS path ≤ ~25 mm, all at ≥ 0.8 mm. U4 and U3 ≥ 20 mm from U5.

## Step 6 — Servo boost and servo connector (right side)

1. **J3 servo header** at the right rim, ≈ **(85, 52)**, cable side outward. **C13 100 µF** right
   next to J3.2/J3.3.
2. **Boost core** ≈ **(77, 48)**: U7, then the hot loop **U7.1 → D4 → C19/C21 → GND → U7.2 within ~8 × 8 mm**
   on F.Cu; **C18 22 µF at pin 5**, **L1** at pin 1 (SW node = pads + short copper only),
   **R22/R23 at pin 3**, R22's top taken from C19/C21.
3. **Load switch** Q6 + Q7 + R27 + R28 + C22 between the VSYS area and C18, ≈ (70, 52).
   BOOST_IN ≥ 0.8 mm.
4. Unbroken B.Cu GND under the converter; ≥ 4 vias at the C19/C21/U7 GND node.
   The antenna keepout (y ≤ 26) and the sensor island are far away.

**Check:** loop area visually; SERVO_5V → J3 ≥ 0.8 mm; no signal traces under L1.

## Step 6b — STEMMA QT port (left edge, below the sensor island)

1. **J5** (JST SH, horizontal) at ≈ **(24, 67)**, opening facing outward (−x), connector face flush with
   the edge. It stays ≥ 1.5 mm below the island's lower slot (y 62.5) and ≥ 15 mm from the antenna.
2. **U8 (USBLC6, ESD)** directly behind J5, flow-through: J5.3 → U8.6, J5.4 → U8.4; U8.1/U8.3 continue to the FETs.
3. **Q9/Q10 (BSS138), R29/R30, Q8 + C23** in the free area x ≈ 33–45, y ≈ 58–70 (between the bridge and the
   power-path area; H2's keepout starts at x 32.9 / y 71.1). Q9/Q10 sources join the main SDA/SCL bus.
4. QT_3V3 0.3–0.5 mm; IO2 (QT_PWR_N) is a slow control signal — any route.

**Check:** J5 copper ≥ 0.5 mm from the edge and slot; I²C stubs short; nothing from this block on the island.

## Step 7 — Remaining small parts and silkscreen

- R16 (LED series) + D3 trace: IO8 → down the left side to D3.
- R17 (servo series) near J3 or near IO5 — either is fine.
- Silkscreen: switch positions (ON/OFF, OFF–SPARSE–CONT), USB, LiPo polarity (+/−), servo pinout
  (S/+/−), **QT** at J5, **CHG** at D2, board name and **v7 / rev G** (the back-silk text already says REV G —
  move it onto the board), sensor-area marking.
- Text/logo off the antenna notch and the sensor island.

**Check:** full DRC (placement only — unrouted is expected): no courtyard, edge or keepout errors.
Do an **enclosure fit check** with a 3D export before routing.

## Step 7b — Placement review (2026-10-01): fixes before routing

Measured on the placed board (no courtyard overlaps; zoning matches the plan). Fix these first:

| # | Issue (measured) | Fix |
|---|---|---|
| 1 | **D2 off the board and facing inward**: pads 0.6–3.1 mm outside the arc, rotation 0 points the lens into the board (DRC copper-edge error) | Put it on the arc mirrored to D3: **≈ (81.8, 77.5), rotation −130°** (lens points outward at ~40°, flush with the edge). Nudge R15 up ~0.5 mm if the courtyards touch. |
| 2 | **Boost hot loop too large**: D4 anode 7.3 mm from U7 SW (behind L1), C19/C21 GND 9–12.5 mm from U7 GND | Make it compact around U7's top pin row (FB 71.55 · GND 72.5 · SW 73.45, y 46.36): **D4 vertical directly above the SW pin, cathode up** (≈ (74.8, 43.0), rot −90° → anode ≈ y 44.4, cathode ≈ y 41.6); **C19 vertical just left of D4** (≈ (72.4, 42.6), rot −90°, + pad up next to the D4 cathode, GND pad ≈ 2.8 mm above U7 pin 2); **C21** next to it (right of D4 or above, + toward the cathode); move **R22/R23 to the left of U7** next to FB (pin 3), R22's top fed from C19+, R23 to GND. Keep L1 where it is (its SW pad 3.7 mm from the SW pin is fine); C18 directly at U7 pin 5. Loop U7.1 → D4 → C19 → U7.2 ≈ 2 × 4 mm. |
| 3 | LDO output caps C11/C12 7 mm from U4 VOUT | Move C11/C12 within 2–3 mm of U4 pin 5 (69.14, 68.05); shift C9/R31 slightly if needed. |
| 4 | Module decoupling: C3 (100 nF) 7.3 mm, C2 (10 µF) 4.8 mm from U1 pin 1 (46.25, 27.5) | C3 closest (≤ 2 mm), C2 next (e.g. C3 ≈ (44.0, 28.6), C2 ≈ (41.5, 28.6), both vertical, + pad toward pin 1); move R1 down/left (the EN RC stays near pin 2). Keep ≥ 0.5 mm from the notch edge (y 26.3). |
| 5 | C14/C15 GND pads face the sensor (+ pads on the far side) | Rotate C14 and C15 by 180° so the **+ pads face U5 pins 8 (VDD) / 6 (VDDIO)**; the GND pads go to pin 7 / a GND via outside the sensor keepout. |
| 6 | SW3/SW4 bodies 0.6 mm inside the flat → actuators 3.4 mm out (target 4.0) | Optional but recommended: move **D3 to the arc** mirrored to D2 (≈ (28.2, 77.5), rot 130°) and shift the row left: **SW4 pin 1 ≈ (38.4, 81.75), J1 ≈ (55.6, 81.4), SW3 pin 1 ≈ (64.9, 81.75)**; move U6/R10/R11/C6 with J1 and R16 right of D3. Both switch bodies are then flush (posts 0.5 mm from the flat) and the actuators protrude the full 4 mm. SW3 can't go lower where it is now — its right post would hit the arc. |
| 7 | J5 opening ≈ 5 mm inside the edge, FID2 in front of it | If the QT cable leaves the enclosure: move J5 ≈ 3.5 mm left (x ≈ 25.5; the mounting pads must stay ≥ 0.5 mm from the arc) and move FID2 (e.g. to (27.5, 74.5), or elsewhere if D3 moves there per #6). If the add-on sensor stays inside the enclosure, J5 can stay. |
| 8 | Silkscreen: 13 overlaps, 17 over pads, 5 clipped at the cuts (U1, J1, J4) | Cosmetic — tidy before ordering (step 9). |

Re-run `check_courtyard_overlaps` / DRC after the moves.

## Step 8 — Routing, in priority order (detailed)

### 8.0 Setup (once)

1. **Board Setup → Pre-defined sizes:** tracks 0.2 / 0.25 / 0.3 / 0.5 / 0.8 / 1.0 mm; vias 0.6/0.3 and 0.8/0.4.
   The net classes (Power 0.8, Supply 0.5, USB 0.25 / diff 0.25-0.2, Default 0.2) set the defaults automatically.
2. **Layer strategy (2-layer):** **B.Cu = GND plane**, kept as unbroken as possible. Route on **F.Cu**;
   use B.Cu only for short jumpers (< 10 mm, crossing at right angles), **never** under U7/L1/D4 (SW node),
   under the USB pair, or in the antenna area.
3. Zones: keep both GND pours; unfill while routing so you see the real copper, refill (B) to check.
   Zone settings: clearance 0.3 mm, min width 0.25 mm, thermal reliefs (solid for U1/U3/U4/U7 GND — already set),
   **remove isolated islands = always**.
4. Interactive router: *Walk around* mode; Route → Differential pair for USB.

### 8.1 Boost converter (most critical — EMI and efficiency)

All on F.Cu, copper areas rather than thin traces:
1. **SW node:** U7.1 → D4 anode → L1.2 as one short, wide copper (≥ 1.0 mm, ≤ 5 mm total). Nothing else near it.
2. **Output:** D4 cathode → C19 + / C21 + (≥ 1.0 mm), then SERVO_5V (0.8 mm) to C13 and J3.2.
3. **Hot-loop GND:** C19/C21 GND pads → U7 pin 2 directly on F.Cu (short, wide), plus **≥ 4 vias** to B.Cu at that GND node.
4. **Input:** BOOST_IN from Q6 drain → C18 + → U7.5 and L1.1 (0.8–1.0 mm). C18 GND with 2 vias.
5. **Feedback (quiet):** R22 top from the C19/C21 + pad (Kelvin tap, not from far along SERVO_5V); FB node R22/R23/U7.3
   as short 0.2 mm traces on the side **away** from the SW node; R23 GND via next to it.
6. **Load switch:** Q6 S ← VSYS (0.8 mm); gate network Q6/Q7/R27/R28/C22 at 0.2–0.3 mm; BOOST_EN (IO10) thin to Q7.G and U7.4.
- **Check:** no B.Cu traces under L1/U7/D4; loop area ≈ the size of the parts; DRC clean locally.

### 8.2 Battery and power path (current-carrying, Power class 0.8 mm or pours)

1. **J4.1 → Q4 (BAT_IN) → VBAT_RAW** (Q4.2, U3.3, C9, Q5.S, R26) → **Q5.D → VBAT** → Q3.D (and the thin VBAT
   tap to R20) → **Q3.S → VSYS**. J4.2 GND: wide + 2–3 vias.
2. **VSYS distribution:** D1 cathode, C20, U4 pins 1/3 (+ C10), Q6.S, R27. Consider a small F.Cu VSYS **polygon** instead of tracks.
3. **VBUS (0.5–0.8 mm):** J1 **A4/A9/B4/B9 all joined** → C6 → U6.5 → D1 anode → U3.4 (C7/C8) → R15 → D2;
   thin branches to R9, Q3 gate, R12 (VBUS_SENSE).
4. **Charger thermal copper:** U3 pins 2/3/4 on generous copper (pours), U3 GND solid + vias; same for U4 GND.
5. **+3V3 (0.5 mm trunk):** U4.5 → C11/C12 → module pin 1 (C3/C2 at the pin) → branches at 0.3 mm to R1/R2/R3/R5,
   R16, R18/R19, Q8.S, and **taper to ~0.25 mm across the sensor bridge** to C14/C15/U5.
- **Check:** no 0.2 mm segment on a Power/Supply net (DRC `track_width` uses the net class).

### 8.3 USB data (signal integrity)

1. **At J1:** join D+ (A6/B6) and D− (A7/B7) of both plug orientations with short stubs (a via under or next to the connector).
2. **J1 → U6 flow-through** (USB_DP_CON → U6.1, U6.6 → USB_D+; USB_DM_CON → U6.3, U6.4 → USB_D−). U6 GND (pin 2) straight to the plane with a via.
3. **Differential pair** USB_D+/D− (0.25 / 0.2) from U6 up to R24/R25 at the module: run together, equal length (mismatch < 2 mm),
   over solid B.Cu GND, away from the SW node, VBUS and the antenna end. ≤ 1 via per line, with a GND via next to each.
4. CC1/CC2 → R10/R11, short.
- **Check:** ~40–45 mm total length is fine for full-speed; no B.Cu cuts under the pair.

### 8.4 Sensitive analog and control around the module

1. **VBAT_SENSE:** R21/C17 at IO0 (pin 18); keep the 1 MΩ node short; the long VBAT → R20 trace is low-current (0.2 mm).
2. **VBUS_SENSE:** R12/R13 node → IO1, 0.2 mm, away from the SW node and USB.
3. **EN (R1/C1/SW1)**, **BOOT (R3/SW2)**, **IO8 (R5/D3)**, **IO2 (R2/Q8 gate)**, **IO20 (R32/R31)** — short, 0.2 mm.
- Keep everything out of the antenna notch keepout (the rule area enforces it).

### 8.5 I²C and the sensor island

1. SDA/SCL from U1 pins 5/6 (left side) → R18/R19 → **across the bridge on F.Cu** → U5 pins 3/4.
2. Branches to the Q9/Q10 sources (QT port). QT side: J5 → U8 (flow-through) → Q9/Q10 drains and R29/R30;
   QT_3V3 from Q8.D (0.3–0.5 mm) → C23 → J5.2 / U8.5.
3. On the island only: +3V3 (≈ 0.25 mm), GND, SDA, SCL. SDO (pin 5) to GND.
- **Check:** nothing else crosses the bridge; no via inside the 4.4 mm SENSOR_KEEPOUT square.

### 8.6 Remaining signals

MODE_A (SW4 → IO3, right side of the module), MODE_B (SW4 → IO4, left side), STATUS_LED_N/LED_STAT (IO8 → D3, R16),
SERVO_PWM (IO5 → R17 → J3.1, long — fine), CHG_STAT/LED_CHG (U3 → D2, R15, R31), BOOST_EN (IO10 → R4, Q7, U7.4),
QT_PWR_N (IO2 → Q8). All 0.2 mm on F.Cu; short B.Cu jumpers where unavoidable.

> **Auto-routing the rest?** Possible after 8.1–8.5: **lock** the hand-routed tracks, add temporary rule areas
> (no tracks on B.Cu) under the boost and along the USB pair, then `export_dsn` → Freerouting → `import_ses`.
> **Do not** run step 1 of the root `AGENTS.md` procedure (`delete_trace net="*"`) — it deletes everything.

### 8.7 GND pours and stitching

1. Refill both GND zones; check every GND pad is connected (DRC `unconnected_items` = 0) and no starved thermals remain.
2. **Stitching vias** (0.6/0.3 mm):
   - **Antenna:** a dense via fence (~2–3 mm pitch) along the GND copper bordering the notch and along the module's GND pads
     (Espressif: dense GND vias near the antenna). None inside the keepout (the rule area blocks them).
   - **Board perimeter:** every ~5 mm (≤ λ/20 at 2.4 GHz ≈ 6 mm), including both sides of the bottom flat and around J1's shield.
   - **Power parts:** ≥ 4 at the boost GND node, 2–3 at U3/U4/C18/C20/J4 GND, 1 next to every decoupling cap GND pad.
   - **Island:** tie the island's GND to the main plane across the bridge (trace + 1–2 vias outside the sensor keepout).
   - MCP option: `add_gnd_stitching_vias` with `strategies: ["grid","around_refs","in_zones"]`,
     `densifyRefs: ["U1","U4","U7","J1"]` — then check that none landed in the sensor keepout or on the island where unwanted.
3. Refill again, then DRC.

### 8.8 Final checks before Step 9

- `run_drc` (with schematic parity) = **0 violations**; zones filled (`query_zones` → `isFilled`).
- Visual: boost loop compact; USB pair parallel; no B.Cu splits under critical paths; antenna notch clean.
- Silkscreen cleanup (Step 7b #8) and labels (ON/OFF, OFF–SPARSE–CONT, QT, CHG, LiPo +/−, servo S/+/−, v7 rev G).
- 3D export for the enclosure fit check.

## Step 9 — Before ordering

- [ ] DRC/ERC clean, reports regenerated (new timestamps).
- [ ] 3D export → enclosure: switch actuators through the wall, USB face flush, LED visible,
      battery and servo ≥ 15 mm from the antenna.
- [ ] Paper print 1:1 of the SW4 footprint against a real OS103011MA7QP1 (F11).
- [ ] Gerbers, drill, position file; BOM via `build_pcbway_bom.py v7`; PCBWay note: THT SW3/SW4,
      parts overhang the bottom flat, no breakaway tabs on that side.
- [ ] Then the bench checklists in `design_review.md`.
