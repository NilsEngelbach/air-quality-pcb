# v9 Design Review — Findings and Validation Checklist

F1–F24 are the review of the v6 board (`v6/air-quality-pcb-v6.*`, state of 2026-09-30) and the
changes made for v7. F25–F26 cover v8 (boost removed, 0.3 mm minimum drill). v9 (rev I) is built from
the routed v8 board, so all of them carry over. **F27–F34** cover the v9 changes: a GPIO remap, C24 on the
STEMMA QT rail, a re-placed and re-routed board, a smaller sensor island, a copper-free zone beside the
antenna, and some open housekeeping. Where v9 changes an earlier finding, the section has a **v9** note
(the **v8** notes stay as history). Every finding lists the evidence, the source, what the design does about
it, and how to validate it. Tick the boxes as you validate. Coordinates are board mm (KiCad), centre (55, 55),
y grows downward.

**Status legend:** ✅ done in the schematic/netlist/board · 🟡 layout task, still open ·
⬜ open decision, not changed · 🔬 needs bench or firmware validation · ➖ obsolete

| # | Finding | Status |
|---|---|---|
| F1 | Power switch SW3 (0.3 A) carries the whole battery current | ✅ 🔬 |
| F2 | Servo rail is **not** off in deep sleep on v6 (boost passes VSYS through L1/D4) | ✅ 🔬 (v8: Q6 now feeds the servo directly) |
| F3 | v6 "DRC clean" is stale — the current v6 file has 8 violations | ✅ (v9: DRC 0 / 0, 2026-10-08) |
| F4 | GND pads of U3 (charger) and U7 (boost) have only one thermal spoke | ✅ (U7 gone in v8) |
| F5 | All tracks are 0.2 mm, no net classes | ✅ (v9 exceptions: F32) |
| F6 | Boost converter hot loop is ~20 mm long, with no input cap at U7 | ➖ boost removed |
| F7 | ESP-12F antenna sits mid-board with copper all around | ✅ 🔬 (v9: F31) |
| F8 | USB-UART bridge (CP2102N) is not needed with the ESP32-C3 | ✅ 🔬 |
| F9 | ESP32-C3 strapping / EN / USB requirements | ✅ 🔬 |
| F10 | v7 pin map (ADC1, deep-sleep wake pins) | ✅ 🔬 (v9 remap: F27) |
| F11 | Edge parts: overhang limits; switch actuators too short | ✅ 🟡 🔬 |
| F12 | MCP73831 runs in thermal regulation at 455 mA | ✅ (R14 3.3 k) 🟡 🔬 |
| F13 | BME688 needs thermal isolation from heat sources | ✅ 🔬 (v9: F30) |
| F14 | AP2112K quiescent current dominates the v7 sleep floor | ✅ decided: keep |
| F15 | WROOM-02 library footprint uses 0.2 mm EPAD via drills | ✅ v8: Espressif footprint (F26) |
| F16 | BSEC2 supports the ESP32-C3 | ✅ 🔬 |
| F17 | VBUS_SENSE moved from CP2102N to ESP ADC | ✅ 🔬 |
| F18 | Round outline vs. straight-fronted edge parts | ✅ (cuts done) 🔬 |
| F19 | No battery under-voltage cutoff on board | ✅ decided: protected cells; firmware cutoff 🔬 |
| F20 | v6 power budget understated the sleep current | ✅ 🔬 (v9: [`power_budget.md`](power_budget.md)) |
| F21 | STEMMA QT port for optional sensors | ✅ 🟡 🔬 |
| F22 | Charge status to the MCU | ✅ 🔬 |
| F23 | CHG LED D2 invisible inside the enclosure | ✅ 🟡 |
| F24 | BME688 occupies the common add-on address 0x77 | ✅ 🔬 |
| F25 | **v8:** boost removed — servo runs from VSYS (4.5 V USB / 3.0–4.2 V battery) | ✅ 🟡 🔬 |
| F26 | **v8:** board must keep the 0.3 mm minimum drill — EPAD vias for the WROOM-02 | ✅ 🔬 |
| F27 | **v9:** GPIO remap — SERVO_PWM → IO0, VBAT_SENSE → IO3, MODE_A → IO4, MODE_B → IO5 | ✅ 🔬 (firmware) |
| F28 | **v9:** C24 100 nF HF decoupling on QT_3V3 at J5 / U8 | ✅ 🔬 |
| F29 | **v9:** re-placement — LDO at the module, power path regrouped at the servo switch, USB ESD flipped | ✅ 🔬 |
| F30 | **v9:** smaller sensor island (≈ 9.5 × 7 mm, 4 mm neck, 4 mm slots), U5 decoupling on the island | ✅ 🔬 |
| F31 | **v9:** no copper beside the antenna — keepouts widened to the board shoulders, new via fence | ✅ 🔬 |
| F32 | **v9:** routing — track-width exceptions, 0.8 / 0.4 mm stitching, USB pair length | ✅ (accepted) 🔬 |
| F33 | **v9:** mode-switch pull-ups must not stay on in deep sleep (~70 µA per closed contact) | ⬜ firmware 🔬 |
| F34 | **v9:** housekeeping — D2 value parity warning, title-block comment, keepout names, Gerbers not generated yet | 🟡 |

---

## F1 — Power switch SW3 is overloaded

- **Evidence (v6):** SW3 = C&K PCM12SMTBR, rated **0.3 A @ 6 V** (v6 BOM). It switched
  VBAT_RAW → VBAT, i.e. *all* battery current: servo move ≈ 400 mA battery-side
  (`v6/power_budget.md` §8), ESP32-C3 WiFi TX peaks up to 350 mA (module datasheet,
  Table 6-4). Combined peaks ≈ 0.75 A > 2× the switch rating.
- **v7 action:** SW3 only drives the gate of a new P-FET **Q5 (DMG2305UX, 20 V / 4.2 A)**.
  Q5 source = VBAT_RAW, drain = VBAT. SW3 common (pin 2) → gate; POS1 (1–2) → GND = **ON**;
  POS2 (2–3) → source = **OFF**. **R26 10 MΩ** gate–source holds Q5 off during the
  break-before-make gap (costs 0.42 µA while ON). Q5's body diode points VBAT → VBAT_RAW,
  so with SW3 OFF the battery cannot feed the system; USB still powers it via D1 (same as v6).
  The switch now carries µA, so a 0.1 A switch (F11) is fine.
- **Validate:**
  - [ ] SW3 ON: device runs from battery; Q5 V_DS < 50 mV at 0.5 A load.
  - [ ] SW3 OFF, no USB: VBAT ≈ 0 V, battery current < 1 µA (only charger leakage).
  - [ ] SW3 OFF + USB: device runs from USB, battery charges, Q5 stays off.
  - [ ] Slide SW3 slowly between positions: no brownout or latch-up.

## F2 — The servo rail is never really off on v6

- **Evidence (v6 schematic):** MT3608 is a non-synchronous boost: VSYS → L1 → SW node → D4
  → SERVO_5V. Pulling EN low (v6 change #1) stops switching but **does not disconnect**:
  SERVO_5V sits at ≈ VSYS − V_F(D4) in deep sleep. The servo stays powered, and the
  feedback divider R22 + R23 (93 kΩ) draws ≈ 37 µA. The v6 budget line "MT3608 + SG92R
  idle < 1 µA (EN low = shutdown)" only counts the MT3608's own shutdown current.
- **v7 action:** load switch in front of the boost input:
  **Q6 DMG2305UX** (VSYS → BOOST_IN, which feeds U7 IN, L1 and C18), gate pulled up by **R27 100 k**;
  **Q7 2N7002** pulls the gate down through **R28 47.5 k** when BOOST_EN (IO10) is high
  (V_GS ≈ −2.5 V at 3.7 V). **C22 100 nF** gate-drain gives a slow turn-on:
  ≈ 47 µA / 100 nF ≈ 0.5 V/ms, so BOOST_IN ramps in ~8 ms and the inrush into the
  ~166 µF downstream (C18 + C19 + C21 + C13) is ~80 mA instead of amps.
  Off state: R4 keeps BOOST_EN low → Q7 off → Q6 off → zero rail current.
- **v8:** the boost is gone and Q6's drain is the servo rail itself (`SERVO_PWR`; the control net is
  now `SERVO_EN`, gate/pull-down nets `SERVO_GATE`/`SERVO_PD`). Downstream capacitance is C19 + C13 = 122 µF,
  so the soft-start inrush is ≈ 60 mA. The off state is unchanged: zero rail current. See F25.
- **Validate:**
  - [ ] **On a v6 board first:** measure the J3 pin-2 current and voltage in deep sleep (expect ≈ VSYS − 0.3 V and
        ≥ 37 µA plus the servo idle current). This confirms the finding and quantifies the v6 loss.
  - [ ] v9 deep sleep: SERVO_PWR = 0 V.
  - [ ] Scope VSYS, +3V3 and SERVO_PWR on a SERVO_EN rising edge: SERVO_PWR ramps in ~5–10 ms;
        +3V3 dips < 100 mV (no ESP brownout).
  - [ ] Servo moves normally with SERVO_EN high ≥ 50 ms before the move.

## F3 — v6 DRC report is stale

- **Evidence:** `v6/drc_v6_check.rpt` is dated 10:07; the board was saved at 14:17.
  A fresh `kicad-cli pcb drc` on v6 gives **8 violations**: 4× copper-to-edge
  (SW3 0.47 / 0.47 mm, SW4 0.44 / 0.42 mm vs the 0.5 mm rule), 2× silkscreen clipped (SW3),
  2× starved thermal (F4).
- **v7 action:** SW3/SW4 replaced (F11); thermal fix (F4).
- **v8:** `drc_v8.rpt` (with schematic parity): 0 errors, 0 unconnected; 2 warnings (U1 silkscreen
  clipped at the antenna notch, F26) and the 7 board-only footprints.
- **v9:** ERC 0 violations. DRC with schematic parity (2026-10-08, also after a zone refill): **0 violations,
  0 unconnected**. Parity reports the 7 board-only footprints and one new warning, D2's value (F34). The four
  `silk_edge_clearance` items at the notch and the bottom flat are excluded in the project file.
- **Validate:**
  - [ ] After placement and routing: `run_drc` = 0 violations, and the report timestamp is newer than the board file.

## F4 — Starved thermals on the charger and boost GND pads

- **Evidence:** v6 DRC `starved_thermal` on U7 pin 2 and U3 pin 2 (1 spoke instead of 2).
  These are the two parts whose GND pin is their main heat path.
- **v7 action:** pad zone connection set to **solid** for the GND pads of U1 (pin 9 + EPAD),
  U3, U4 and U7.
- **v8:** U7 is removed. The solid connection is set again on U1 pin 9 and on all nine EPAD pads of the new
  footprint (F26).
- **Validate:**
  - [ ] After the zone refill, no `starved_thermal` on these pads. (The 5 current hits on J1/U6 are fine-pitch USB
        GND pads that lost their feeding traces; they clear when routed.)

## F5 — All traces are 0.2 mm, and there are no net classes

- **Evidence (v6 board dump):** every segment is 0.2 mm, including VBUS (138 mm of track),
  VBAT (59 mm), VSYS (47 mm), BOOST_SW (20 mm), SERVO_5V (47 mm).
  0.2 mm × 35 µm Cu ≈ 2.5 mΩ/mm → 0.25 V per 10 cm at 1 A. Heating is not the issue
  (IPC-2221 ≈ 0.7 A for +10 °C); voltage drop and inductance are (brownout during
  servo + WiFi peaks at low battery).
- **Action (v7, updated for v8, unchanged in v9):** net classes in `air-quality-pcb-v9.kicad_pro` (Freerouting/`export_dsn` reads them):

  | Class | Width | Via | Nets |
  |---|---|---|---|
  | Power | 0.8 mm | 0.8/0.4 | BAT_IN, VBAT_RAW, VBAT, VSYS, SERVO_PWR |
  | Supply | 0.5 mm | 0.8/0.4 | VBUS, +3V3, GND |
  | USB | 0.25 mm (diff pair 0.25/0.2) | 0.6/0.3 | USB_D±, USB_D*_CON, USB_D*_MCU |

  v8: SERVO_PWR (was BOOST_IN + SERVO_5V) is in Power; BOOST_SW is gone.
- **v9:** the re-route has some short segments below the class width (KiCad DRC does not enforce class widths).
  They are listed and accepted in F32.
- **Validate:**
  - [ ] `export_dsn` contains the classes; routed power tracks are ≥ the class widths.
  - [ ] At a 1 A battery load: VBAT_RAW → VSYS drop < 100 mV (incl. Q4, Q5, Q3).

## F6 — Boost converter hot loop (obsolete in v8)

> **v8:** the boost converter is removed (F25), so this finding and its checks no longer apply. Kept for the record.

- **Evidence (v6 placement):** U7–L1 14.5 mm, U7–D4 13.6 mm, D4–C19 20.5 mm, D4–C13 25.4 mm;
  BOOST_SW was a 20 mm track at 0.2 mm. **No cap at U7 IN**: the nearest VSYS cap was C18,
  11.7 mm away (C8 next to U7 is on VBUS). R22 sat ~8 mm from FB.
  MT3608 datasheet p.6: 22 µF in/out close to the IC on a strong GND plane, main traces
  short and wide, SW node small, FB divider close.
- **v7 action:** C18 → **22 µF at U7 IN** (BOOST_IN); **C21 22 µF** second output cap
  (0805 X5R 16 V loses capacitance at 5 V); D4 SS34 (SMA, 5.2 × 2.6 mm) →
  **PMEG4030ER** (SOD-123W, 2.6 × 1.7 mm, 40 V / 3 A). C20 22 µF is VSYS bulk ahead of Q6.
  Layout recipe in `layout_constraints.md` §3.
- **Validate:**
  - [ ] Layout: loop U7.1 → D4 → C19/C21 → GND → U7.2 fits within ~8 × 8 mm on F.Cu.
  - [ ] Scope the SW node: clean edges, ringing < 2 V overshoot. SERVO_5V ripple < 100 mV p-p during a servo move.

## F7 — Antenna placement

- **Evidence (v6):** ESP-12F centred at (53, 52) on the Ø72 mm board. Its antenna region
  (y ≈ 40–47.5 mm) is ~21 mm from the nearest edge, with GND pour on both layers around
  the keepout. No tracks cross the antenna.
- **Source:** Espressif ESP32-C3 HW design guidelines: antenna **outside** the base board,
  or the feed point as close to the edge as possible; cut the board on both sides of and under the antenna;
  **≥ 15 mm clearance in all directions** inside the housing; dense GND vias near the antenna.
- **v7 action:** module → ESP32-C3-WROOM-02 (18 × 20 mm). Its footprint carries an all-layer
  keepout of 28 × 11 mm (5 mm beyond each side and the antenna end). The old mid-board
  keepout zone was removed. Placement in `layout_constraints.md` §2.
- **v8:** Espressif's footprint only carries an 18 × 6 mm keepout (the antenna area of the module itself).
  The 28 × 11 mm area of the stock footprint is kept as the board rule area **ANTENNA_KEEPOUT**
  (x 41–69, y 15.4–26.4, F.Cu + B.Cu: no tracks, vias, pads or pour) — see F26.
- **v9:** ANTENNA_KEEPOUT is widened to the board shoulders beside the notch (x 29.5–80), the pours are kept off a
  slightly larger band, and the via fence is rebuilt — see F31.
- **Validate:**
  - [ ] Layout: antenna end at (or past) the board edge; no copper, tracks or vias in the keepout.
  - [ ] Bench: RSSI of v6 vs v7 at the same spot / AP distance (expect v7 ≥ v6).
  - [ ] In the enclosure: battery, servo and screws ≥ 15 mm from the antenna.

## F8 — UART bridge removed

- **Evidence:** the ESP32-C3 has an integrated USB Serial/JTAG controller (GPIO18/19)
  that supports flashing, console and automatic download mode (Espressif schematic
  checklist).
- **v7 action:** removed U2 (CP2102N), C4, C5, Q1, Q2, R6, R7 and JP1 (the C3 wakes from its
  internal RTC timer, so no GPIO16→RST link is needed). Added **R24/R25 22 Ω** series
  resistors (place at U1). C6 (4.7 µF) stays as VBUS bulk. **No test pads** (decision: boards
  are ordered assembled); recovery is BOOT + RESET over USB with the enclosure open. IO20 is
  re-used for CHG_DET (F22); IO21 is unconnected.
- **Validate:**
  - [ ] Board enumerates as USB JTAG/serial debug unit (VID 303A); `esptool` flashes without pressing buttons.
  - [ ] Manual recovery: hold BOOT, tap RESET → download mode.
  - [ ] Known behaviour: the USB port disappears during deep sleep — firmware should not rely on the console.

## F9 — ESP32-C3 strapping, EN and USB

- **Source:** module datasheet Table 4-3: SPI boot = GPIO9 high; download = GPIO9 low +
  GPIO8 high; GPIO2 "recommended to pull up due to glitches". EN RC = 10 k + 1 µF.
  Supply ≥ 500 mA, 10 µF + 0.1 µF at the module.
- **v7 action:** R2 → IO2 10 k pull-up; R5 → IO8 10 k pull-up (the status LED also sits on IO8,
  active-low, so LED off = strap high); R3 → IO9 10 k pull-up + SW2 BOOT; R1/C1 = 10 k /
  **1 µF** (was 100 nF); SW1 RESET now on EN; C2/C3 = 10 µF + 100 nF. AP2112K = 600 mA.
- **Validate:**
  - [ ] Boots into the application in every SW4 position, with and without USB.
  - [ ] LED stays dark during reset (IO8 high).
  - [ ] BOOT/RESET are **internal only** (decision). WiFi re-provisioning therefore needs a firmware gesture on
        SW4 (see README, firmware port). BOOT + RESET remain the service path: BOOT held while RESET is
        released = download mode.

## F10 — v7 pin map

> **v9:** IO0, IO3, IO4 and IO5 are reassigned — see **F27**. The table below is the **v9** map; the
> reasoning per pin is unchanged.

| GPIO | Net | Why |
|---|---|---|
| IO0 | SERVO_PWM (v7/v8: VBAT_SENSE) | via R17 100 Ω; any GPIO can drive LEDC PWM |
| IO1 | VBUS_SENSE | ADC1_CH1 (F17) |
| IO2 | QT_PWR_N | strap (R2 pull-up) → STEMMA QT power, active low (F21) |
| IO3 | VBAT_SENSE (v7/v8: MODE_A) | ADC1_CH3 (ADC1 is calibrated; ADC2 is not usable reliably) |
| IO4 / IO5 | MODE_A / MODE_B (SW4) (v7/v8: IO3 / IO4) | internal pull-ups while awake; GPIO0–5 can wake from deep sleep (mind F33) |
| IO6 / IO7 | SDA / SCL | R18/R19 10 k pull-ups; BME688 0x76 + QT port |
| IO8 | STATUS_LED_N | strap, pull-up R5, LED active-low |
| IO9 | BOOT | strap, R3 + SW2 |
| IO10 | SERVO_EN (v7: BOOST_EN) | R4 100 k pull-down → Q7/Q6 servo-rail switch |
| IO18 / IO19 | USB D− / D+ | via R25 / R24 |
| IO20 | CHG_DET | charger status via R31/R32 (F22) |
| IO21 | — | unconnected, spare |

- **Validate:**
  - [ ] Firmware port (see README) reads all inputs and drives all outputs as listed (v9 map).
  - [ ] VBAT_SENSE (IO3) reads 4.20 V ± 30 mV at full charge (ADC1, 2.5 dB attenuation, divider 0.2126).

## F11 — Edge parts: overhang limits and actuator length

- **Rule:** what limits overhang is the **frontmost copper or hole**, not the body.
  PCBWay: copper ≥ 0.3 mm, holes ≥ 0.5 mm from the routed edge; project rule
  `min_copper_edge_clearance` = 0.5 mm.
- **Evidence (v6):** SW3/SW4 (PCM12/PCM13): front SMD tabs sit 0.23 mm in front of the body,
  so the actuator tips reached only **0.71 / 0.55 mm** past the edge — they cannot reach through
  a 1.5–2 mm enclosure wall. D3 lens 0.2 mm past the edge; J1 front 0.7 mm past (front shield
  pad 0.88 mm inside).
- **v7 action:** right-angle THT slide switches with a **4 mm actuator** (C&K OS series):
  - SW3 **OS102011MA1QN1** (SPDT, 0.1 A / 12 V, BBM). KiCad footprint `SW_Slide_SPDT_Angled_CK_OS102011MA1Q`.
  - SW4 **OS103011MA7QP1** (SP3T ON-ON-ON, 0.1 A / 12 V, Digi-Key CKN9561-ND, active).
    Vendor footprint `SamacSys_Parts:OS103011MA7QP1` (Mouser / SamacSys, v3.2, with STEP), matching the C&K OS
    datasheet p. I-42: posts Ø1.5 mm 12.2 mm apart; terminals Ø0.8 mm at 2.1 / 6.1 / 8.1 / 10.1 mm from the left post;
    body 12.6 × 4.3 mm, centred on the pin row (body front 2.15 mm ahead of it).
    **Common = pin 2** (POS1 1–2, POS2 2–3, POS3 2–4) — differs from the PCM13 (common = 3);
    the schematic is wired for this.
  - With the posts' pads ending 0.5 mm behind the body front, the **body front can sit flush with
    the board edge** and the actuator protrudes **4.0 mm** (travel 2 mm per step).
- **v8/v9 (accepted):** SW3/SW4 sit at y = 81 with their bodies ~0.8 mm behind the bottom flat, so the actuators
  protrude **~3.2 mm**, not 4.0 mm. v9 did not move them. Size the enclosure wall and slots for 3.2 mm.
- **Validate:**
  - [ ] **First article / paper print:** the vendor footprint matches a real part (0.8 mm terminal holes are tight;
        check the pins drop in).
  - [ ] Enclosure: actuator passes the wall with ≥ 1.5 mm to grip; slot length = 2 mm actuator + travel
        (SPDT ≈ 4 mm, SP3T ≈ 6 mm) + clearance.
  - [ ] SW4 positions decode OFF / SPARSE / CONTINUOUS in that physical order.
  - [ ] PCBWay order note: THT parts SW3/SW4 + parts overhanging the edge — no breakaway tabs on those sides.

## F12 — Charger thermal (MCP73831, SOT-23-5)

- **Evidence:** R14 = 2.2 k → I_REG = 1000 V / 2.2 k ≈ 455 mA. Dissipation (5.0 − 3.7) V × 0.455 A
  ≈ 0.6 W typical, ≈ 0.9 W at the start of fast charge (3.0 V), datasheet worst case
  (5.5 − 2.7) × 0.455 ≈ 1.3 W. θJA = 230 °C/W minimum copper, ~130 °C/W with large copper
  (datasheet Table "Temperature specifications", §6.1.1.3) → the part sits in thermal
  regulation, and it heats the board (which affects BME688 readings while charging).
- **v7 action (decided):** **R14 = 3.3 k → I_REG ≈ 303 mA.** Dissipation (5.0 − 3.7) × 0.303 ≈ 0.39 W typical,
  worst case (5.5 − 2.7) × 0.303 ≈ 0.85 W. A 2000 mAh cell needs ≈ 7–8 h to full (fine overnight).
  Layout: large pours on pins 2/3/4 with vias, solid GND (done, F4), far from U5.
- **Validate:**
  - [ ] Thermal camera / thermocouple while charging an empty cell: U3 case temperature, charge current vs time.
  - [ ] BME688 temperature offset while charging vs not charging.

## F13 — BME688 thermal isolation

- **Evidence:** heat sources on board: U3 (up to ~1 W), U4 (≈ 0.45 W during TX bursts on USB:
  (4.6 − 3.3) V × 0.35 A), ESP module, LEDs (v7 also had U7/L1 during moves; removed in v8).
- **v7 action (layout):** U5 on the opposite side of the board from U1/U3/U4, ideally on a
  peninsula with a milled slot on 2–3 sides; keep the existing SENSOR_KEEPOUT (no pour under U5).
- **v9:** the island is smaller and its neck narrower, U5 sits further out, and C14/C15 moved onto the island
  (F30). The LDO U4 moved next to the module, so it is now **33 mm** from U5 (v8: ~44 mm); still well beyond the
  ~15 mm guideline. U3 (charger, the largest heat source) is 56 mm away.
- **Validate:**
  - [ ] Compare BME688 temperature vs a reference thermometer in sleep cycle, while charging, and on CONTINUOUS WiFi.

## F14 — LDO quiescent current

- **Evidence:** v7 sleep floor (estimate): ESP32-C3 deep sleep 5 µA (datasheet typ) +
  **AP2112K 55 µA** + VBAT divider 3.3 µA + R26 0.4 µA + BME688 ~2 µA ≈ **66 µA**.
  The LDO is ~80 % of it.
- **v7 (decided): keep the AP2112K.** Possible later option: a ≥ 500 mA LDO with µA-level Iq (e.g. Richtek RT9080-33 class;
  check dropout at 350 mA and the 1 µF output cap requirements) → floor ≈ 13 µA. The gain is only
  ~1.3 mAh/day against ~34 mAh/day total (wake phases dominate).
- **Validate:**
  - [ ] Measure the v7 sleep floor first; decide on the LDO swap with real numbers.

## F15 — WROOM-02 EPAD via drill

- **Evidence:** KiCad's `RF_Module:ESP32-C3-WROOM-02` uses 12 × 0.2 mm drills in the EPAD;
  the board minimum (and PCBWay standard) is 0.3 mm → `drill_out_of_range`.
- **v7 action:** keep the stock `RF_Module:ESP32-C3-WROOM-02` footprint (0.2 mm drills, 0.6 mm pads,
  0.2 mm annular ring) and lower the board minimum (`min_through_hole_diameter`) to **0.2 mm**.
  PCBWay builds 0.2 mm drills, possibly at extra cost. (An earlier v7 draft used a project copy with 0.3 mm drills.)
- **v8 (decided):** the board stays at the **0.3 mm** minimum drill. The 0.2 mm EPAD drills are gone with
  Espressif's own footprint — details and checks in **F26**.

## F16 — BSEC2 on the ESP32-C3

- **Evidence:** Bosch-BSEC2-Library `library.properties` (v1.10.2610 — the version the
  firmware already pins) lists `esp32c3`, and `src/esp32c3/libalgobsec.a` exists
  (riscv32-esp-elf-gcc build of BSEC v2.6.1.0).
- **Validate:**
  - [ ] PlatformIO env `platform = espressif32`, `board = esp32-c3-devkitm-1`, `boschsensortec/bsec2@1.10.2610` links.
  - [ ] IAQ accuracy reaches 3 and the BSEC state survives deep sleep (RTC memory / LittleFS).

## F17 — VBUS sensing

- **v7 action:** the CP2102N's VBUS_SENSE divider is re-used for ESP ADC1 (IO1), values
  swapped: R12 47.5 k (top), R13 22.1 k (bottom) → 5.0 V → 1.59 V (5.5 V → 1.75 V), inside
  the 12 dB ADC range and below the 3.3 V pin limit. Only loads VBUS, so no battery drain.
- **Validate:**
  - [ ] IO1 reads ~1.6 V on USB, ~0 V on battery; firmware can detect "on USB" (e.g. skip deep sleep for debugging).

## F18 — Round outline vs straight-fronted edge parts

- **Evidence:** a 9–13 mm wide straight face on a Ø72 mm circle leaves its corners
  0.3–0.6 mm (sagitta) inside the edge. The WROOM-02 (18 mm) has a 1.1 mm sagitta. The enclosure wall is curved too.
- **v7 action (done):** Edge.Cuts now has a **bottom flat at y = 84** (x 33.67–76.33) for SW4/J1/SW3,
  an **antenna notch** x 41–69 down to y = 26.3, and the **sensor island** slots (see [`../v7/layout_plan.md`](../v7/layout_plan.md);
  v9 reshapes the island, F30).
  D3 and D2 sit on the arc beside the flat.
- **Validate:**
  - [ ] Enclosure fit check with a 3D export (`export_3d`) before ordering.

## F19 — Battery cutoff

- No on-board under-voltage cutoff. **Decision: only cells with built-in protection (PCM) are used**, so no protection circuit is added.
- **Firmware:** if VBAT_SENSE < ~3.3 V → indefinite deep sleep (LED blink once).
- [ ] Verify the threshold with a bench supply ramped down.

## F20 — Power budget correction

- v6 `power_budget.md` sleep floor (~80 µA) **omits the servo rail** (F2): ≥ 37 µA through
  R22/R23 plus the SG92R idle current with power and no PWM (not in its datasheet — measure;
  micro servos often draw several mA, which would dominate the daily budget).
- v7 estimate: ~66 µA (F14), servo rail 0.
- v8: unchanged (~66 µA); removing the boost only drops parts that were already switched off by Q6.
- v9: unchanged (~66 µA; C24 sits on the switched QT rail). The estimate-based budget is now in
  [`power_budget.md`](power_budget.md). F33 is a firmware trap that would roughly double it.
- [ ] Measure the v6 and v9 sleep currents with the same firmware mode and replace the estimates in `power_budget.md`.

## F21 — STEMMA QT port

- **Why:** BME688 eCO₂ is a VOC-based estimate; a STEMMA QT / Qwiic port allows add-ons such as a
  real CO₂ sensor (SCD41), SHT4x, light sensors, without a board respin.
- **v7 action:** J5 JST SH 4P (SM04B-SRSS-TB): 1 GND, 2 QT_3V3, 3 SDA, 4 SCL (+ MP to GND).
  - **Switched power:** Q8 DMG2305UX (+3V3 → QT_3V3), gate = IO2 (QT_PWR_N). R2's 10 k strap pull-up
    keeps the port **off at reset and in deep sleep** → 0 µA when not in use. C23 10 µF on QT_3V3
    (v9: plus C24 100 nF at the connector, F28).
  - **Bus isolation:** Q9/Q10 BSS138 (gate = QT_3V3, source = SDA/SCL, drain = port side) with
    R29/R30 10 k port-side pull-ups. When the port is off, the FETs block the board pull-ups from
    back-feeding the unpowered sensor through its I/O clamps (≈ 0.3 mA per line otherwise).
  - **ESD:** U8 USBLC6-2SC6 at the connector, wired flow-through (connector → U8 pin 6/4, bus → U8 pin 1/3;
    the pin pairs are the same line inside the part, as with U6 on the USB data lines).
- **Validate:**
  - [ ] IO2 HIGH/input: QT_3V3 = 0 V, no current into J5; sleep floor unchanged.
  - [ ] IO2 LOW: QT_3V3 ≈ 3.3 V; +3V3 dip on enable < 100 mV with an SCD41 attached.
  - [ ] I²C scan with the port on: 0x76 (BME688) + the add-on; with the port off: only 0x76, no bus errors.
  - [ ] 400 kHz I²C works through Q9/Q10 with a 20–50 cm cable.

## F22 — Charge status to the MCU

- **v7 action:** charger STAT (U3.1, push-pull to VBUS = 5 V) → **R31 10 k / R32 18 k** → IO20 (CHG_DET):
  5.0 V → 3.21 V, 5.5 V → 3.54 V (below the 3.6 V pin maximum). STAT low = charging, high = done,
  hi-Z without VBUS (reads low → firmware must qualify with VBUS_SENSE). D2 still lights while charging.
- **Validate:**
  - [ ] IO20 reads LOW while charging, HIGH when full, and stays ≤ 3.6 V at VBUS = 5.5 V.

## F23 — Visible charge LED

- **v7 action:** D2 (top-view 0805, invisible inside the enclosure) → **Kingbright KPA-3010SGC**, green
  side-view, same footprint as D3; R15 1 k from VBUS gives ≈ 2.8 mA (Vf ≈ 2.2 V). Placed on the
  board edge next to the bottom flat (mirror of D3).
- **Validate:**
  - [ ] Polarity on first article (pad 1 = cathode, as for D3); visible through the enclosure.

## F24 — BME688 I²C address

- **v7 action:** BME688 SDO (pin 5) moved from +3V3 to GND → address **0x76**; 0x77 stays free
  for common add-on breakouts (BME280/680/688, BMP3xx default to 0x77).
- **Validate:**
  - [ ] Firmware uses `BME68X_I2C_ADDR_LOW` (0x76); I²C scan shows the BME688 at 0x76.

## F25 — Servo supply without the boost (v8)

- **Decision:** remove the MT3608 boost (U7, L1, D4, C18, C21, R22, R23). The servo must work on USB **and** on
  battery, so it runs from **VSYS** through the existing load switch Q6 (F2). VBUS alone was rejected:
  it is 0 V on battery.
- **Evidence:**
  - SG92R (TowerPro): rated **4.8–6 V**; all figures are given at 4.8 V (2.5 kg·cm, 0.1 s/60°). TowerPro
    publishes no current figures; micro servos of this class typically draw ~5–10 mA idle,
    ~150–250 mA moving and ~0.6 A or more at start/stall (estimate — measure).
  - SERVO_PWR = VSYS − Q6 drop (DMG2305UX, ≈ 50–70 mΩ → ≈ 15 mV at 250 mA):
    **USB ≈ 4.5–4.6 V** (VBUS − B5819W at ~0.5 A; within a few % of the rating), **battery 3.0–4.2 V**
    (below the rating: lower torque and speed, roughly proportional to voltage).
  - On battery, a start/stall pulse of ~0.6 A through the cell's protection, Q4/Q5/Q3 and the cell's internal
    resistance pulls VSYS down by roughly 0.2–0.3 V. The AP2112K needs VIN ≳ 3.3 V + dropout (≈ 0.1–0.25 V at the
    ESP's load) to hold +3V3; the module runs down to 3.0 V. Below VBAT ≈ 3.5 V a servo start can dip +3V3.
    C20 22 µF (VSYS) and C13 100 µF + C19 22 µF (SERVO_PWR) buffer the edge.
  - USB budget: with 5.1 kΩ CC pull-downs a USB 2.0 port only guarantees 500 mA. Charger 303 mA + ESP32-C3
    (WiFi TX peaks ~350 mA) + servo can exceed it; phone chargers (≥ 1.5 A) are fine.
  - USB inrush is unchanged: the servo bulk caps sit behind Q6's soft start (C22), not on VBUS.
- **v8 action:** `SERVO_PWR` net = Q6.D, C22, C19 22 µF, C13 100 µF, J3.2 (Power class). C20 stays as VSYS bulk.
  IO10 renamed `SERVO_EN`. Firmware: enable ≥ 50 ms before a move; skip moves below VBAT ≈ 3.5 V;
  move with WiFi idle; no PWM while SERVO_EN is low.
- **Validate:**
  - [ ] On battery at 4.2 / 3.7 / 3.5 V (bench supply in place of the cell): the servo reaches every IAQ position
        and holds it; record move time and current (peak and average).
  - [ ] Scope +3V3 during a servo start at VBAT = 3.5 V: no ESP brownout reset; adjust the firmware cut-off threshold.
  - [ ] On USB from a laptop port while charging an empty cell: servo move with WiFi on and off — no USB
        disconnect or brownout.
  - [ ] Sleep floor unchanged (servo rail 0 V, F20).

## F26 — EPAD vias with the 0.3 mm minimum drill (v8)

- **Constraint:** the board keeps PCBWay's standard minimum drill **0.3 mm** (`min_through_hole_diameter` 0.3).
  Both stock KiCad footprints (`RF_Module:ESP32-C3-WROOM-02` and `…-02U`) have 12 × 0.2 mm drills in the EPAD (F15).
- **Options considered:** (1) Espressif's footprint + board vias — **chosen**; (2) a project copy of the stock
  footprint with 0.3 mm drills (breaks the "no custom footprints" rule; 0.55 mm via pitch leaves 0.25 mm between holes);
  (3) no EPAD vias (weaker RF ground); (4) another module — a full re-layout.
- **v8 action:**
  - U1 → **`Espressif:ESP32-C3-WROOM-02`** from [espressif/kicad-libraries](https://github.com/espressif/kicad-libraries)
    (`v8/Espressif.pretty`, STEP in `air-quality-pcb-v8.3dshapes/`; v9 carries its own copies). The EPAD is a 3 × 3 array of 0.7 mm pads
    (pitch 1.05–1.15 mm), **no drills**. Its origin is 0.1 mm off the stock one; U1 now sits at **(55, 33.4)** so
    all pads are at the same board positions as in v7 (the routing still lands on them).
  - **4 GND vias 0.6 / 0.3 mm** at the gap crossings of the EPAD pads: **(55.385 | 56.485, 33.15 | 34.25)**. The via ring
    just touches the four pad corners (0.27 mm from the via centre), so the vias connect directly; the hole stays
    0.12 mm clear of the pad openings. Vias are tented (board setting), which limits wicking. The GND pour (solid
    connection) also joins the nine pads.
  - Board rule area **ANTENNA_KEEPOUT** replaces the stock footprint's built-in 28 × 11 mm keepout (F7).
- **v9:** U1 and the four EPAD vias are unchanged (checked: same coordinates, 0.6 / 0.3 mm). The new stitching uses
  0.8 / 0.4 mm vias; the smallest drill is still 0.3 mm (EPAD and signal vias).
- **Validate:**
  - [ ] DFM at PCBWay: no drill below 0.3 mm, no surcharge.
  - [ ] Gerber/3D check: the Espressif STEP model sits on the footprint (offset −9 / −7 mm in the footprint);
        the EPAD paste openings are the nine 0.7 mm squares.
  - [ ] First article: X-ray or a cross-check of the EPAD solder joint (no large voids, no solder through the tented vias).
  - [ ] RF (F7 check) is no worse than the v7 expectation.
  - [ ] The U1 silkscreen is clipped at the antenna notch (2 DRC warnings) — cosmetic; accept or hide those lines.

## F27 — GPIO remap (v9)

- **Change (schematic):**

  | Net | v8 | v9 | Module pad (side) |
  |---|---|---|---|
  | SERVO_PWM | IO5 (pad 4, left) | **IO0** | pad 18, right |
  | VBAT_SENSE | IO0 (pad 18, right) | **IO3** | pad 15, right |
  | MODE_A (SW4 → OFF) | IO3 (pad 15, right) | **IO4** | pad 3, left |
  | MODE_B (SW4 → CONTINUOUS) | IO4 (pad 3, left) | **IO5** | pad 4, left |

- **Why:** each signal now leaves the module on the side that faces its destination. SW4 is bottom-left (x 39),
  so both mode lines use the left pads. J3 is on the right edge (x 86), so the servo signal uses a right pad. The
  VBAT divider sits right of centre. In v8, MODE_A and SERVO_PWM left on the far side and crossed the board.
  Result: SERVO_PWM 49.8 → **34.2 mm, all F.Cu** (v8: 2 vias); MODE_A/MODE_B 2 vias each (v8: 4 / 6).
- **Checks against the ESP32-C3 rules (F9, F10):**
  - **ADC:** VBAT_SENSE on IO3 = **ADC1_CH3**, still ADC1. Divider, C17 and attenuation are unchanged.
  - **Deep-sleep wake:** MODE_A/MODE_B on IO4/IO5 are still within GPIO0–5 (deep-sleep wake capable).
  - **IO0 at power-up:** IO0/IO1 are the XTAL_32K pins (no 32 kHz crystal is fitted) and are not straps.
    Any level or glitch on IO0 during reset is harmless: R4 holds SERVO_EN low, so the servo rail is unpowered
    until the firmware enables it.
  - IO4/IO5 are also the pad-JTAG pins (MTMS/MTDI). Pad JTAG is not used; debugging goes over USB-JTAG.
- **Trade-off:** VBAT_SENSE now runs **30 mm** (v8: 11.6 mm, 2 vias). The node has ~213 kΩ source impedance, but
  C17 100 nF sits at the ADC pad (67, 30.5), so the line is low-impedance at RF and only DC reaches the pin.
- **Firmware:** the pin map changes (see README, *Firmware port*). The v8 map **must not** be flashed onto v9:
  it would drive PWM into the VBAT divider and sample the mode switch as an ADC.
- **Validate:**
  - [ ] Firmware pin map: `SERVO_PWM = 0`, `VBAT_SENSE = 3`, `MODE_A = 4`, `MODE_B = 5`.
  - [ ] VBAT_SENSE: spread of 8 consecutive samples < 20 mV, with WiFi idle and during a WiFi TX burst.
  - [ ] Power-up and reset with the servo connected: the servo does not twitch.
  - [ ] SW4 decodes OFF / SPARSE / CONTINUOUS on IO4 / IO5 (with F11).

## F28 — C24 on the STEMMA QT rail (v9)

- **Change:** **C24 100 nF** (0805 X7R, CL21B104KBCNNNC) from QT_3V3 to GND at (35.5, 63), between C23 10 µF
  (42, 63) and U8 (35.5, 66.5).
- **Why:** QT_3V3 had only the 10 µF bulk C23, ~6.5 mm from the connector. U8's VBUS pin (pin 5, the clamp
  reference) and J5.2 now get a small HF cap within ~3.5 mm, for add-on sensors with fast current edges and for the
  ESD clamp path. It sits on the switched rail, so it costs nothing in sleep.
- **Validate:**
  - [ ] With an add-on attached and IO2 LOW: QT_3V3 ripple at J5 < 50 mV p-p during the add-on's measurement.
  - [ ] Enable inrush (C23 + C24 + the add-on's caps through Q8): +3V3 dip < 100 mV (F21 check).

## F29 — Re-placement and re-route (v9)

The v9 board is re-placed and re-routed; outline, connectors, switches, LEDs, U1 and the mounting holes stay where
they were. Main moves:

| Block | v9 placement | Effect |
|---|---|---|
| **LDO** U4 + C10 (VIN), C11/C12 (VOUT) | U4 (53.1, 44.6), right below the module; C11/C12 at (51.5 / 49.5, 48) | +3V3 copper 156 → **104 mm**; the module's 3V3 pin is fed over a short path. VSYS now carries the ESP current over ~32 mm at 0.8 mm (≈ 20 mΩ, ≈ 7 mV at 350 mA) |
| **Power path + servo switch** D1, Q3, C20, Q6, Q7, R27, R28, C22, R4, C19, C13, R17 | grouped right of centre, next to J3: D1 (73, 54.8), Q3 (73, 58.3), Q6 (75, 51), C13 (80.5, 54) | SERVO_PWR 25.4 → **15.5 mm**, F.Cu, no vias. C20 (VSYS bulk) sits at Q6/Q3 |
| **VBAT divider** R20/R21 | (68.5, 53.5) / (67.5, 51.5) at VBAT; C17 stays at the ADC pad | see F27 |
| **Charge detect** R31/R32 | together at the charger, (71.4, 66) / (68.5, 68) | CHG_DET (slow) runs to U1 pad 11 |
| **USB ESD** U6 | (54, 73.5), rotated; pin pairs flipped: connector on pins 6/4, MCU side on 1/3 | still flow-through (1↔6 and 3↔4 are the same line inside the USBLC6). USB_D*_CON 19 / 17.5 → **7.5 / 6.0 mm** |
| **RESET / BOOT** SW1/SW2, R1/C1, R3 | SW1 (42, 38.5), SW2 (48, 43), next to the module's EN / IO9 side | internal buttons, short EN RC |
| **Strap pull-ups** | R5 (IO8) at (31, 74.5) next to D3/R16; R2 (IO2) at (41.5, 53.6) next to Q8 | DC pull-ups: position is not critical. R5 now sits at the LED end of STATUS_LED_N |
| **STEMMA QT** Q9, Q10, R29, U8, C24 | between J5 and the main I²C bus | see F28 |

- **Validate:**
  - [ ] Scope +3V3 at U1 pad 1 during WiFi TX on battery at VBAT 3.5 V: dip < 100 mV.
  - [ ] Enumeration and flashing over USB are reliable with a 1 m and a 2 m cable (F32 USB pair).
  - [ ] LDO case temperature during CONTINUOUS uploads on USB (F13 check).

## F30 — Sensor island (v9)

- **Change (Edge.Cuts):** the island is now **≈ 9.5 × 7 mm** (x 19.2–28.9, y 51.5–58.5). It is joined to the board
  by a **4 mm wide neck** (y 53–57, x 29.1–31.5), with **4 mm wide slots** above and below. v8: ≈ 11.5 × 13 mm, a
  7 mm neck, 1 mm slots. U5 moved 3.3 mm further out to (21.7, 55.0), and its decoupling caps C14/C15 moved onto the
  island at (26, 54 / 56.25). C16 10 µF and the I²C pull-ups R18/R19 stay on the main board at x 35.5.
- **Why:** less copper and less FR4 cross-section between the warm board and the sensor (F13); the wider slots also
  let room air reach the sensor from both sides.
- **Notes:** SENSOR_KEEPOUT (x 19–31, y 48–62, no pour) still covers the island and the neck. Only +3V3, GND, SDA and
  SCL cross the neck. The +3V3 run on the island is 0.2 mm, which is fine at the BME688's few mA (heater peaks
  included); see F32. The narrow neck is the mechanical weak point: no breakaway tab on this side, and don't use the
  island as a handling point.
- **Validate:**
  - [ ] BME688 temperature vs a reference: offset in sleep cycle, while charging and in CONTINUOUS, compared with a
        v8 board if one is built (F13).
  - [ ] Island survives depanelling and assembly (visual check for cracks at the neck).
  - [ ] Enclosure opening lines up with the island.

## F31 — No copper beside the antenna (v9)

- **Change:**
  - **ANTENNA_KEEPOUT** (F.Cu + B.Cu, no tracks / vias / pads / pour) widened from x 41–69 to **x 29.5–80**
    (y 15.4–26.5). It now covers the board shoulders on both sides of the antenna notch, not just the notch.
  - Two pour-only keepouts, **x 27.5–83, y 15–26.5**, one per layer (named `ANETNNA_KEEPOUT_1` on F.Cu and
    `ANTENNAb_KEEPOUT_2` on B.Cu — typos, F34). The pours now end at y ≈ 26.5 on both sides.
  - The v8 F.Cu pour and stitching vias in the upper-left lobe, e.g. (40, 24) and (37, 25.5), are gone. The new
    **via fence** (0.8 / 0.4 mm, GND) runs along y = 27.5 from x 35.5 to 74.5, mostly at 2 mm pitch (v8: 15 vias at
    1 mm pitch, x 48–62, 0.6 / 0.3 mm). 2 mm is far below λ/20 (≈ 6 mm at 2.4 GHz).
- **Why:** Espressif's layout guide asks for the antenna outside the base board or at its edge, with **no copper beside
  or under it**. With a notch only as wide as the module, the copper on the shoulders sat within a few mm of the
  antenna's ends. Bare laminate there is the closest a round board gets to "antenna outside the board".
- **Not changed:** H3 / H4 are still ~14 mm from the antenna area. Use nylon screws there, or accept the detuning
  (see F7 housing check).
- **Validate:**
  - [ ] RSSI at a fixed spot and AP distance: v9 ≥ v8 (or v7 expectation), board in its enclosure.
  - [ ] Gerber check: no copper on either layer above y ≈ 26.5 between x 27.5 and 83.

## F32 — Routing details (v9)

- **Track widths below the class width** (DRC does not flag these; all checked and accepted):

  | Net (class) | Where | Width / length | Why it is fine |
  |---|---|---|---|
  | +3V3 (Supply 0.5) | sensor island, C16 → C14/C15 → U5 | 0.2 mm, ~22 mm | BME688 draws a few mA; the island neck is too narrow for wide copper |
  | VBAT_RAW (Power 0.8) | to C9, R26 and SW3.3 | 0.2 mm, ~14 mm | gate network (µA) and a cap stub; the battery current runs on the 0.8 mm path |
  | VBAT_RAW (Power 0.8) | U3 pins 3–5 | 0.65 mm, ~5 mm | limited by the SOT-23-5 pad pitch |
  | VSYS (Power 0.8) | at U4 pins 1 / 3 (VIN, EN) and C10 | 0.3 mm, ~5.5 mm | pad necks; ≈ 2 mV at 350 mA |
  | SERVO_PWR (Power 0.8) | Q6 drain → C22 | 0.5 mm, 2.9 mm | ≈ 3 mΩ; < 2 mV at a 0.6 A servo start |
  | VBUS (Supply 0.5) | between the J1 VBUS pin pairs | 0.4 mm, ~7 mm | limited by the USB-C pad pitch |

- **Stitching:** 641 vias, 605 of them GND; 556 are 0.8 / 0.4 mm (v8: mostly 0.6 / 0.3). 67 vias under the module.
  The smallest drill is still 0.3 mm (the four EPAD vias and the signal vias), so the 0.3 mm board rule (F26) holds.
- **USB pair:** U6 → R24/R25 is **47.3 / 48.4 mm** (Δ 1.1 mm), each line with 2 vias. This misses the `< 30 mm,
  ≤ 1 via` guideline in `layout_constraints.md` §2, as v8 did (46–49 mm). At USB full speed (12 Mb/s, ≥ 4 ns edges)
  this is not critical; the connector side is now short (F29).
- **Validate:**
  - [ ] USB: enumeration, `esptool` flash at the default baud and a long serial log, with a 2 m cable (F29).
  - [ ] At a 1 A battery load: VBAT_RAW → VSYS drop < 100 mV (F5 check).

## F33 — Mode-switch pull-ups in deep sleep (v9, firmware)

- **Evidence:** SW4 has no external pull-ups; MODE_A/MODE_B rely on the ESP32-C3's internal pull-ups (~45 kΩ
  typ.). In OFF or CONTINUOUS, one contact is closed to GND. If the firmware leaves that pin's pull-up enabled across
  deep sleep (for example, to wake on a switch change, v7 README), it draws **3.3 V / 45 kΩ ≈ 70 µA**. That is more
  than the whole ~66 µA sleep floor (F14, F20), so the sleep current about doubles in two of the three positions.
  The v6 firmware already avoids this: it samples the pins with pull-ups, then releases them to Hi-Z.
- **Rule for the port:**
  - No GPIO wake: read IO4/IO5 with pull-ups at each wake, then set them to plain input before sleep. A mode change
    takes effect at the next timer wake (≤ 5 min). This is the simplest option and costs 0 µA.
  - With GPIO wake (for a switch gesture or instant mode change): enable the pull-up and the low-level wake **only on
    the pin whose contact is open**. An open contact costs 0 µA. Example: in SPARSE both are open, so wake on either.
    In OFF (IO4 closed), wake only on IO5 → moving to CONTINUOUS wakes the chip; moving to SPARSE takes effect at the
    next timer wake.
- **Validate:**
  - [ ] Sleep current in all three SW4 positions is the same within ±5 µA.

## F34 — Housekeeping (v9)

- [ ] **D2 value parity warning:** the board footprint value is `CHG` (silkscreen label), the schematic value
      `CHG-GREEN`. The BOM comes from the schematic, so ordering is not affected. Either set the schematic value to
      `CHG` or update the PCB from the schematic and re-check the silkscreen text.
- [ ] **Title block** comment 1 still reads "ESP32-C3 + BME688 + SG92R (v7)"; rev is I.
- [ ] **Keepout names** `ANETNNA_KEEPOUT_1` / `ANTENNAb_KEEPOUT_2` → e.g. `ANTENNA_POUR_KEEPOUT_F` / `_B` (cosmetic).
- [x] **Schematic PDF and BOMs** generated (2026-10-08): `schematic_v9.pdf`, `bom_kicad_raw.csv`,
      `bom_pcbway_v9.csv` (38 lines, 72 placements; C24 merged into the CL21B104KBCNNNC line, otherwise identical to v8).
- [ ] **Gerbers, drill and position files** (commands in the README).
- [ ] 3D export → enclosure check (switch actuators ~3.2 mm, F11; USB face; LEDs; island opening; ≥ 15 mm
      around the antenna).

---

## Sources

- Espressif, [ESP32-C3 PCB layout guidelines](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c3/pcb-layout-design.html) and [schematic checklist](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c3/schematic-checklist.html)
- Espressif, [ESP32-C3 datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-c3_datasheet_en.pdf) (pin functions: ADC1 channels, XTAL_32K on GPIO0/1, deep-sleep wake on GPIO0–5, internal pull-up value — F27, F33)
- Espressif, [ESP32-C3-MINI-1 datasheet](https://documentation.espressif.com/esp32-c3-mini-1_datasheet_en.pdf) (strapping, current consumption tables — same ESP32-C3 chip); [ESP32-C3-WROOM-02-N4 at Digi-Key](https://www.digikey.com/en/products/detail/espressif-systems/ESP32-C3-WROOM-02-N4/14553031)
- Espressif, [KiCad libraries](https://github.com/espressif/kicad-libraries) (WROOM-02 footprint and STEP, F26)
- Aerosemi, [MT3608 datasheet](https://www.olimex.com/Products/Breadboarding/BB-PWR-3608/resources/MT3608.pdf) (v7 boost, removed in v8)
- TowerPro SG92R specification (4.8–6 V, figures at 4.8 V); Diodes Inc. DMG2305UX and AP2112K datasheets (F25)
- Microchip, [MCP73831 datasheet](http://ww1.microchip.com/downloads/en/DeviceDoc/20001984g.pdf)
- C&K, OS series datasheet ([LCSC copy](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/1811061532_C-K-OS102011MA1QN1_C226259.pdf)); [OS103011MA7QP1 at Digi-Key](https://www.digikey.com/en/products/detail/c-k/OS103011MA7QP1/1981432); [OS102011MA1QN1 at LCSC](https://www.lcsc.com/product-detail/Slide-Switches_C-K-OS102011MA1QN1_C226259.html)
- Kingbright KPA-3010SGC ([Farnell](https://uk.farnell.com/kingbright/kpa-3010sgc/led-side-view-smd-green-12mcd/dp/8530335)); JST SH SM04B-SRSS-TB; onsemi BSS138
- Nexperia, [PMEG4030ER datasheet](https://assets.nexperia.com/documents/data-sheet/PMEG4030ER.pdf); Diodes Inc., [2N7002 datasheet](https://www.diodes.com/datasheet/download/2N7002.pdf)
- Bosch, [BSEC2 library](https://github.com/boschsensortec/Bosch-BSEC2-Library)
- PCBWay, [safety spacing](https://www.pcbway.com/blog/PCB_Manufacturing_Information/How_is_the_PCB_safety_spacing_designed_.html), [hole to edge](https://www.pcbway.com/helpcenter/Engineering_Questions/the_spacing_requirement_from_hole_to_the_edge_of_board.html)
