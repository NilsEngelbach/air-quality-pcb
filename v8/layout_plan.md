# v8 Layout Plan

v8 starts from the **placed and routed v7 board**. This plan records what was changed on the board
(steps 1–4, all done on 2026-10-05) and the pre-order checklist (step 5). The rules are in [`layout_constraints.md`](layout_constraints.md);
the findings (F-numbers) are in [`design_review.md`](design_review.md). The full v7 placement and routing plan
(outline cuts, coordinates, routing priorities) is still valid for everything not mentioned here:
[`../v7/layout_plan.md`](../v7/layout_plan.md).

Coordinates are board mm (KiCad), centre (55, 55), y grows downward.

---

## Step 1 — Done on the board (2026-10-05)

1. **Boost removed:** footprints U7, L1, D4, C18, C21, R22, R23 deleted, with the copper that only served them
   (BOOST_SW / BOOST_FB tracks, the U7 EN stub and its via at (73.5, 48.5), GND stubs to the removed pads, dangling
   SERVO_PWR stubs).
2. **Nets renamed/merged** to match the schematic: BOOST_IN + SERVO_5V → **SERVO_PWR**, BOOST_EN → **SERVO_EN**,
   BOOST_GATE → SERVO_GATE, BOOST_PD → SERVO_PD.
3. **One SERVO_PWR track added** (F.Cu, 0.8 mm) to close the gap the boost left: C22.1 (69.5, 48.95) → (71.0, 48.95)
   → (76.5, 43.45) → C19.1 (77.5, 43.45). The jog around the old D4 pad on the C19 → C13/J3 run was straightened
   (now (78.65 → 81.35, 43.45)). Both were replaced in step 2.
4. **U1 → `Espressif:ESP32-C3-WROOM-02`**, origin (55, 33.4) so every pad is where the stock footprint had it;
   pads 9 and the nine EPAD pads have a solid zone connection.
5. **4 EPAD vias** 0.6 / 0.3 mm, GND, at (55.385, 33.15), (56.485, 33.15), (55.385, 34.25), (56.485, 34.25).
6. **Rule area ANTENNA_KEEPOUT** (F.Cu + B.Cu, x 41–69, y 15.4–26.4): no tracks, vias, pads or pour.
7. Project: `min_through_hole_diameter` 0.3 mm; Power class `/SERVO_PWR`; back silkscreen **REV H**.
8. Zones refilled. `drc_v8.rpt` (schematic parity): **0 errors, 0 unconnected**; 2 warnings (U1 silkscreen clipped
   at the notch, see step 3) and the 7 board-only footprints.

## Step 2 — Routing clean-up in the old boost area (done)

1. **C19 moved** to (79.5, 49.5), next to C13/J3. **SERVO_PWR** now runs Q6.D (68.32, 50.6) → C22.1 → C19.1 →
   C13.1 (81.81, 54.91) → J3.2 (86.0, 54.46): F.Cu only, 0.8 mm, 25 mm, no vias.
2. **SERVO_EN** keeps its route (0.2 mm, 4 vias, ~9 mm on B.Cu). It is a slow signal; the detour costs nothing
   electrically, so it was left as is.
3. **Leftover GND vias:** (70.5, 51.0) kept as stitching; (75.34, 46.3) and (81.5, 40.0) removed or moved by the
   stitching pass.
4. **Servo return:** C13's GND pad has 5 GND vias within 2.5 mm, C19's 2. J3.3 is a THT pad (its barrel reaches
   both pours) with one more via at 2.5 mm.

**Checked:** no Power-class segment under 0.8 mm, no dangling tracks, `unconnected_items` = 0.

## Step 3 — U1 checks (EPAD and antenna) (done)

1. The **4 EPAD vias** are at their coordinates (step 1.5); the hole stays 0.12 mm clear of the pad openings. A
   stitching pass had added 4 more vias right against the EPAD pads (one hole 0.02 mm from a pad); they were removed.
   Keep any later stitching away from the EPAD.
2. **ANTENNA_KEEPOUT** is clean: no copper, tracks or vias in it, and the GND pours stop at it.
3. **Silkscreen:** Espressif's module outline lines at x = 46 and x = 64 cross the notch edge (y 26.3), and J1's
   outline crosses the bottom flat → 4 `silk_edge_clearance` warnings, **excluded** in the DRC settings (the fab clips
   silk at the edge). Do not edit the vendor footprints.

## Step 4 — Pours, stitching, DRC (done)

1. **Stitching** (0.6 / 0.3 mm; the board has 399 vias, 339 of them GND):
   - antenna fence: 15 vias at y = 27.5, x 48–62 (1 mm pitch) along the module's ground edge, 1.1 mm from the
     antenna area;
   - ~56 vias in a ~2.5 mm grid under the module (tented, fine under the module body);
   - both sides of the notch: right (70.2, 23.5), (70.18, 26.38), (74.1, 26.03), (70.0, 28.0); left (40.0, 24.0),
     (40.0, 27.0), (37.0, 25.5), (37.5, 28.0), (34.5, 27.0), (32.0, 29.0), (38.0, 30.0). The left vias also brought
     back the F.Cu pour in the upper-left lobe, which had been removed as an unconnected island.
   - If you run the root `AGENTS.md` re-route procedure, its step 1 deletes all vias — **re-add the 4 EPAD vias**
     (step 1.5) and redo the stitching.
2. Zones refilled. DRC with schematic parity: **0 errors, 0 unconnected** (also after a refill check).
3. **Silkscreen:** servo pin labels **S / + / −** at J3 (the J3 value "SERVO" and reference sit beside them). No
   polarity labels at J4: the JST PH plug is keyed. Part names come from the visible value fields (WIFI_MODE, POWER,
   STATUS, SERVO, LiPo, RESET, BOOT). Back: AIR QUALITY CHECKER, **REV H 2026**.

## Step 5 — Before ordering

- [x] DRC/ERC clean, reports regenerated (`drc_v8.rpt`, `erc_v8.rpt`, 2026-10-05 13:56).
- [x] No drill < 0.3 mm in the drill file (F26): PTH 0.30–1.50 mm, NPTH 0.65 / 2.70 mm.
- [x] BOM: `Espressif:ESP32-C3-WROOM-02` added to `build_pcbway_bom.py` (package map; WROOM-02 note no longer
      mentions 0.2 mm vias). `bom_pcbway_v8.csv`: 38 lines, 71 placements; U7, L1, D4, C18, C21, R22, R23 are gone.
- [x] Gerbers, drill, position file in `gerbers/` (upload `gerbers/air-quality-pcb-v8-gerbers.zip`). PCBWay note:
      THT SW3/SW4, parts overhang the bottom flat, no breakaway tabs on that side.
- [x] **Switch actuators accepted as placed:** SW3/SW4 stay at y = 81; their bodies sit ~0.8 mm behind the flat, so the
      actuators stick out ~3.2 mm (not the 4.0 mm in F11). Size the enclosure wall and slots for that.
- [ ] 3D export → enclosure: switch actuators through the wall, USB face flush, LEDs visible,
      battery and servo ≥ 15 mm from the antenna. H3/H4 are 13.9 mm from the antenna area — use nylon screws there.
- [ ] Paper print 1:1 of the SW4 footprint against a real OS103011MA7QP1 (F11).
- [ ] Then the bench checklists in `design_review.md` (F25 servo on battery, F26 EPAD first).
