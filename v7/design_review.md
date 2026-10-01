# v7 Design Review — Findings and Validation Checklist

Review of the v6 board (`v6/air-quality-pcb-v6.*`, state of 2026-09-30) and the
changes made for v7. Every finding lists the evidence, the source, what v7 does
about it, and how to validate it. Tick the boxes as you validate.

**Status legend:** ✅ done in the v7 schematic/netlist · 🟡 layout task, still open (placement and routing) ·
⬜ open decision, not changed · 🔬 needs bench or firmware validation

| # | Finding | Status |
|---|---|---|
| F1 | Power switch SW3 (0.3 A) carries the whole battery current | ✅ 🔬 |
| F2 | Servo rail is **not** off in deep sleep on v6 (boost passes VSYS through L1/D4) | ✅ 🔬 |
| F3 | v6 "DRC clean" is stale — the current v6 file has 8 violations | ✅ 🟡 |
| F4 | GND pads of U3 (charger) and U7 (boost) have only one thermal spoke | ✅ |
| F5 | All tracks are 0.2 mm, no net classes | ✅ 🟡 |
| F6 | Boost converter hot loop is ~20 mm long, with no input cap at U7 | ✅ 🟡 |
| F7 | ESP-12F antenna sits mid-board with copper all around | ✅ 🟡 |
| F8 | USB-UART bridge (CP2102N) is not needed with the ESP32-C3 | ✅ 🔬 |
| F9 | ESP32-C3 strapping / EN / USB requirements | ✅ 🔬 |
| F10 | v7 pin map (ADC1, deep-sleep wake pins) | ✅ 🔬 |
| F11 | Edge parts: overhang limits; switch actuators too short | ✅ 🟡 🔬 |
| F12 | MCP73831 runs in thermal regulation at 455 mA | ✅ (R14 3.3 k) 🟡 🔬 |
| F13 | BME688 needs thermal isolation from heat sources | 🟡 |
| F14 | AP2112K quiescent current dominates the v7 sleep floor | ✅ decided: keep |
| F15 | WROOM-02 library footprint uses 0.2 mm EPAD via drills | ✅ |
| F16 | BSEC2 supports the ESP32-C3 | ✅ 🔬 |
| F17 | VBUS_SENSE moved from CP2102N to ESP ADC | ✅ 🔬 |
| F18 | Round outline vs. straight-fronted edge parts | ✅ (cuts done) 🔬 |
| F19 | No battery under-voltage cutoff on board | ✅ decided: protected cells; firmware cutoff 🔬 |
| F20 | v6 power budget understated the sleep current | ✅ 🔬 |
| F21 | STEMMA QT port for optional sensors | ✅ 🟡 🔬 |
| F22 | Charge status to the MCU | ✅ 🔬 |
| F23 | CHG LED D2 invisible inside the enclosure | ✅ 🟡 |
| F24 | BME688 occupies the common add-on address 0x77 | ✅ 🔬 |

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
- **Validate:**
  - [ ] **On a v6 board first:** measure the J3 pin-2 current and voltage in deep sleep (expect ≈ VSYS − 0.3 V and
        ≥ 37 µA plus the servo idle current). This confirms the finding and quantifies the v6 loss.
  - [ ] v7 deep sleep: SERVO_5V = 0 V, BOOST_IN = 0 V.
  - [ ] Scope VSYS, +3V3 and BOOST_IN on a BOOST_EN rising edge: BOOST_IN ramps in ~5–10 ms;
        +3V3 dips < 100 mV (no ESP brownout).
  - [ ] Servo moves normally with BOOST_EN high ≥ 100 ms before the move.

## F3 — v6 DRC report is stale

- **Evidence:** `v6/drc_v6_check.rpt` is dated 10:07; the board was saved at 14:17.
  A fresh `kicad-cli pcb drc` on v6 gives **8 violations**: 4× copper-to-edge
  (SW3 0.47 / 0.47 mm, SW4 0.44 / 0.42 mm vs the 0.5 mm rule), 2× silkscreen clipped (SW3),
  2× starved thermal (F4).
- **v7 action:** SW3/SW4 replaced (F11); thermal fix (F4). v7 DRC currently shows only
  the expected unrouted state (`drc_v7_unrouted.rpt`).
- **Validate:**
  - [ ] After placement and routing: `run_drc` = 0 violations, and the report timestamp is newer than the board file.

## F4 — Starved thermals on the charger and boost GND pads

- **Evidence:** v6 DRC `starved_thermal` on U7 pin 2 and U3 pin 2 (1 spoke instead of 2).
  These are the two parts whose GND pin is their main heat path.
- **v7 action:** pad zone connection set to **solid** for the GND pads of U1 (pin 9 + EPAD),
  U3, U4 and U7.
- **Validate:**
  - [ ] After the zone refill, no `starved_thermal` on these pads. (The 5 current hits on J1/U6 are fine-pitch USB
        GND pads that lost their feeding traces; they clear when routed.)

## F5 — All traces are 0.2 mm, and there are no net classes

- **Evidence (v6 board dump):** every segment is 0.2 mm, including VBUS (138 mm of track),
  VBAT (59 mm), VSYS (47 mm), BOOST_SW (20 mm), SERVO_5V (47 mm).
  0.2 mm × 35 µm Cu ≈ 2.5 mΩ/mm → 0.25 V per 10 cm at 1 A. Heating is not the issue
  (IPC-2221 ≈ 0.7 A for +10 °C); voltage drop and inductance are (brownout during
  servo + WiFi peaks at low battery).
- **v7 action:** net classes in `air-quality-pcb-v7.kicad_pro` (Freerouting/`export_dsn` reads them):

  | Class | Width | Via | Nets |
  |---|---|---|---|
  | Power | 0.8 mm | 0.8/0.4 | BAT_IN, VBAT_RAW, VBAT, VSYS, BOOST_SW, SERVO_5V |
  | Supply | 0.5 mm | 0.8/0.4 | VBUS, +3V3, GND |
  | USB | 0.25 mm (diff pair 0.25/0.2) | 0.6/0.3 | USB_D±, USB_D*_CON, USB_D*_MCU |

  BOOST_IN is not in a class yet: route it ≥ 0.8 mm, or add it to Power.
- **Validate:**
  - [ ] `export_dsn` contains the classes; routed power tracks are ≥ the class widths.
  - [ ] At a 1 A battery load: VBAT_RAW → VSYS drop < 100 mV (incl. Q4, Q5, Q3).

## F6 — Boost converter hot loop

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

| GPIO | Net | Why |
|---|---|---|
| IO0 | VBAT_SENSE | ADC1_CH0 (ADC1 is calibrated; ADC2 is not usable reliably) |
| IO1 | VBUS_SENSE | ADC1_CH1 (F17) |
| IO2 | QT_PWR_N | strap (R2 pull-up) → STEMMA QT power, active low (F21) |
| IO3 / IO4 | MODE_A / MODE_B (SW4) | internal pull-ups; GPIO0–5 can wake from deep sleep |
| IO5 | SERVO_PWM | via R17 100 Ω |
| IO6 / IO7 | SDA / SCL | R18/R19 10 k pull-ups; BME688 0x76 + QT port |
| IO8 | STATUS_LED_N | strap, pull-up R5, LED active-low |
| IO9 | BOOT | strap, R3 + SW2 |
| IO10 | BOOST_EN | R4 100 k pull-down → Q7/Q6 and U7 EN |
| IO18 / IO19 | USB D− / D+ | via R25 / R24 |
| IO20 | CHG_DET | charger status via R31/R32 (F22) |
| IO21 | — | unconnected, spare |

- **Validate:**
  - [ ] Firmware port (see README) reads all inputs and drives all outputs as listed.
  - [ ] VBAT_SENSE reads 4.20 V ± 30 mV at full charge (ADC1, 2.5 dB attenuation, divider 0.2126).

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
    New footprint `AirQuality:SW_Slide_SP3T_Angled_CK_OS103011MA7Q`, built from the C&K OS datasheet p. I-42:
    posts Ø1.5 mm 12.2 mm apart; terminals Ø0.8 mm at 2.1 / 6.1 / 8.1 / 10.1 mm from the left post; body 12.6 × 4.3 mm.
    **Common = pin 2** (POS1 1–2, POS2 2–3, POS3 2–4) — differs from the PCM13 (common = 3);
    the schematic is wired for this.
  - With the posts' pads ending 0.5 mm behind the body front, the **body front can sit flush with
    the board edge** and the actuator protrudes **4.0 mm** (travel 2 mm per step).
- **Validate:**
  - [ ] **First article / paper print:** the OS103011MA7Q footprint matches a real part. The pin-row-to-body-front offset
        (2.25 mm) is copied from KiCad's OS102011MA1Q footprint because the datasheet drawing does not dimension it.
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
  (4.6 − 3.3) V × 0.35 A), U7/L1 during moves, ESP module, LEDs.
- **v7 action (layout):** U5 on the opposite side of the board from U1/U3/U4/U7, ideally on a
  peninsula with a milled slot on 2–3 sides; keep the existing SENSOR_KEEPOUT (no pour under U5).
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
- **v7 action:** project footprint `AirQuality:ESP32-C3-WROOM-02_EPADvia0.3` (same geometry,
  0.3 mm drills, 0.6 mm pads, 0.15 mm annular ring).
- **Validate:**
  - [ ] PCBWay DFM accepts it; X-ray / inspection shows no solder voids from wicking (tented or plugged vias are an option).

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
  an **antenna notch** x 41–69 down to y = 26.3, and the **sensor island** slots (see `layout_plan.md`).
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
- [ ] Measure the v6 and v7 sleep currents with the same firmware mode and record them in `v7/power_budget.md` (to be written after bench).

## F21 — STEMMA QT port

- **Why:** BME688 eCO₂ is a VOC-based estimate; a STEMMA QT / Qwiic port allows add-ons such as a
  real CO₂ sensor (SCD41), SHT4x, light sensors, without a board respin.
- **v7 action:** J5 JST SH 4P (SM04B-SRSS-TB): 1 GND, 2 QT_3V3, 3 SDA, 4 SCL (+ MP to GND).
  - **Switched power:** Q8 DMG2305UX (+3V3 → QT_3V3), gate = IO2 (QT_PWR_N). R2's 10 k strap pull-up
    keeps the port **off at reset and in deep sleep** → 0 µA when not in use. C23 10 µF on QT_3V3.
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

---

## Sources

- Espressif, [ESP32-C3 PCB layout guidelines](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c3/pcb-layout-design.html) and [schematic checklist](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c3/schematic-checklist.html)
- Espressif, [ESP32-C3-MINI-1 datasheet](https://documentation.espressif.com/esp32-c3-mini-1_datasheet_en.pdf) (strapping, current consumption tables — same ESP32-C3 chip); [ESP32-C3-WROOM-02-N4 at Digi-Key](https://www.digikey.com/en/products/detail/espressif-systems/ESP32-C3-WROOM-02-N4/14553031)
- Aerosemi, [MT3608 datasheet](https://www.olimex.com/Products/Breadboarding/BB-PWR-3608/resources/MT3608.pdf)
- Microchip, [MCP73831 datasheet](http://ww1.microchip.com/downloads/en/DeviceDoc/20001984g.pdf)
- C&K, OS series datasheet ([LCSC copy](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/1811061532_C-K-OS102011MA1QN1_C226259.pdf)); [OS103011MA7QP1 at Digi-Key](https://www.digikey.com/en/products/detail/c-k/OS103011MA7QP1/1981432); [OS102011MA1QN1 at LCSC](https://www.lcsc.com/product-detail/Slide-Switches_C-K-OS102011MA1QN1_C226259.html)
- Kingbright KPA-3010SGC ([Farnell](https://uk.farnell.com/kingbright/kpa-3010sgc/led-side-view-smd-green-12mcd/dp/8530335)); JST SH SM04B-SRSS-TB; onsemi BSS138
- Nexperia, [PMEG4030ER datasheet](https://assets.nexperia.com/documents/data-sheet/PMEG4030ER.pdf); Diodes Inc., [2N7002 datasheet](https://www.diodes.com/datasheet/download/2N7002.pdf)
- Bosch, [BSEC2 library](https://github.com/boschsensortec/Bosch-BSEC2-Library)
- PCBWay, [safety spacing](https://www.pcbway.com/blog/PCB_Manufacturing_Information/How_is_the_PCB_safety_spacing_designed_.html), [hole to edge](https://www.pcbway.com/helpcenter/Engineering_Questions/the_spacing_requirement_from_hole_to_the_edge_of_board.html)
