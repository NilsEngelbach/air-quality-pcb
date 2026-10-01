# Air Quality Checker — PCB v7 (rev G)

Seventh iteration: **ESP8266 → ESP32-C3** (native USB, no UART bridge), fixes from the
v6 design review, right-angle switches with longer actuators, a **STEMMA QT port** for
optional sensors, and charge-status sensing.

**State:** schematic complete, ERC **0 errors / 0 warnings** (`erc_v7.rpt`). Board synced
with the schematic (`drc_v7_unrouted.rpt`: schematic parity clean; the remaining items are
unrouted nets, the 7 board-only footprints that v6 already reported, and silkscreen at the new
cuts). The outline has its v7 cuts (antenna notch, bottom flat, sensor island).
**Placement is in progress; routing is open.**
Start with [`layout_plan.md`](layout_plan.md); the rules behind it are in
[`layout_constraints.md`](layout_constraints.md), and every finding with its validation checklist is in
[`design_review.md`](design_review.md).

---

## What changed vs v6

| # | Change | Why (finding) |
|---|---|---|
| 1 | **U1 ESP-12F → ESP32-C3-WROOM-02-N4** (18 × 20 mm, 4 MB) | newer MCU, native USB, 5 µA deep sleep (F7–F10) |
| 2 | **CP2102N block removed**: U2, C4, C5, Q1, Q2, R6, R7; JP1 removed; **no test pads** (boards are ordered assembled; recovery = BOOT + RESET over USB) | the C3 has USB Serial/JTAG built in; RTC-timer wake needs no GPIO16→RST (F8) |
| 3 | USB D± via **R24/R25 22 Ω** to IO19/IO18 | Espressif checklist (F8) |
| 4 | Strap pull-ups IO2 (R2), IO8 (R5), IO9 (R3); **C1 100 nF → 1 µF** (EN RC 10 k / 1 µF); SW1 on EN; SW2 on IO9 | ESP32-C3 boot and power-up requirements (F9) |
| 5 | **SW3 drives P-FET Q5** (+ R26 10 MΩ) instead of switching the battery current | PCM12 was rated 0.3 A, peaks ≈ 0.75 A (F1) |
| 6 | **Servo-rail load switch Q6/Q7** (+ R27, R28, C22) in front of the MT3608 | in v6 a disabled boost still fed VSYS → L1 → D4 → servo (F2) |
| 7 | Boost: **C18 22 µF at U7 IN** (BOOST_IN), **C21 22 µF** 2nd output cap, **C20 22 µF** VSYS bulk, **D4 SS34 → PMEG4030ER** (SOD-123W) | MT3608 layout rules, smaller hot loop (F6) |
| 8 | **SW3 → C&K OS102011MA1QN1, SW4 → C&K OS103011MA7QP1** (right-angle THT, **4 mm actuator**) | v6 actuators reached only 0.55–0.71 mm past the edge (F11) |
| 9 | R4 10 k → **100 k** (BOOST_EN pull-down); VBUS_SENSE divider swapped to 47.5 k / 22.1 k → ESP ADC IO1 | (F10, F17) |
| 10 | **Net classes** Power 0.8 mm / Supply 0.5 mm / USB 0.25 mm | v6 was 0.2 mm everywhere (F5) |
| 11 | Solid zone connection on the GND pads of U1/U3/U4/U7 | v6 starved thermals (F4) |
| 12 | Project footprint library `AirQuality.pretty`: OS103011MA7Q switch, WROOM-02 with 0.3 mm EPAD vias | no stock footprint / 0.2 mm drills (F11, F15) |
| 13 | **Charger R14 2.2 k → 3.3 k** (≈ 455 → 303 mA) | thermal regulation and board heating near the sensor (F12) |
| 14 | **D2 CHG LED → Kingbright KPA-3010SGC** (green, side-view), on the board edge like D3 | the top-view 0805 was invisible inside the enclosure (F23) |
| 15 | **STEMMA QT port J5** (JST SH 4P): switched 3V3 (Q8, IO2), bus isolation (Q9/Q10 BSS138 + R29/R30), ESD (U8 USBLC6), C23 | optional add-on sensors, e.g. a real CO₂ sensor (SCD41), with zero sleep current (F21) |
| 16 | **Charge status → IO20** (CHG_DET) via R31/R32 divider from the charger's STAT pin | firmware can report "charging/done" (F22) |
| 17 | **BME688 I²C address 0x77 → 0x76** (SDO to GND) | keeps 0x77 free for common add-on breakouts (F24) |
| 18 | Board outline: **antenna notch, bottom flat, sensor island slot**; title block / silkscreen **rev G** | (F7, F13, F18) |

Decisions: LDO stays AP2112K (F14); batteries **with built-in protection** are used, so no
protection circuit (F19); BOOT/RESET buttons are **internal only**.

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
| IO10 | BOOST_EN | HIGH = servo rail on (Q6) + MT3608 enabled |
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
                        └─► Q6 (BOOST_EN via Q7) ─► BOOST_IN ─► MT3608 ─► SERVO_5V ─► J3
```

Sleep-floor estimate: ≈ **66 µA** (ESP32-C3 5 µA + AP2112K 55 µA + VBAT divider 3.3 µA +
BME688 ~2 µA + R26 0.4 µA; servo rail and QT port 0). The v6 figure of 80 µA missed the servo rail (F2, F20).
Measure before updating the battery tables.

## Firmware port (air-quality-checker repo)

- PlatformIO: `platform = espressif32`, `board = esp32-c3-devkitm-1` (or a custom board JSON),
  `build_flags = -DARDUINO_USB_MODE=1 -DARDUINO_USB_CDC_ON_BOOT=1`. Keep `boschsensortec/bsec2@1.10.2610`:
  it ships `src/esp32c3/libalgobsec.a` (F16).
- **BME688 address is now 0x76** (`BME68X_I2C_ADDR_LOW`) — update the sensor init.
- `ESP.deepSleep()` → `esp_sleep_enable_timer_wakeup()` + `esp_deep_sleep_start()`;
  `rtcData` → `RTC_DATA_ATTR`. Optional: wake on a mode-switch change with
  `esp_deep_sleep_enable_gpio_wakeup()` on IO3/IO4.
- Pins as above. Note the changes: **LED now IO8**, **BOOST_EN now IO10** (keep ≥ 100 ms before
  a move), mode pins IO3/IO4, servo IO5, I2C IO6/IO7.
- **STEMMA QT:** drive IO2 LOW to power the port, wait for the add-on sensor's start-up time, use it, then
  set IO2 back to input/HIGH before deep sleep (R2 holds it off). Never leave it LOW across sleep.
- **Charge status:** `charging = VBUS_SENSE > ~1.2 V && digitalRead(20) == LOW`; `done = VBUS present && HIGH`.
- ADC: `analogSetPinAttenuation(0, ADC_2_5db)`, `analogReadMilliVolts(0) / 0.2126` → VBAT.
- The USB console disappears during deep sleep; log to LittleFS when debugging sleep.
- **Re-provisioning without reachable buttons:** BOOT/RESET are internal. Add a switch gesture instead,
  e.g. "SW4 moved OFF → CONTINUOUS → OFF → CONTINUOUS within 5 s" (IO3/IO4 can wake the chip) forces the
  setup portal. The BOOT + RESET path stays as the service/recovery path with the enclosure open. Update
  the user documentation accordingly.

## Files

| File | Purpose |
|---|---|
| `air-quality-pcb-v7.kicad_pro/.kicad_sch/.kicad_pcb` | v7 project (ERC clean; board synced with the cuts, placement in progress) |
| `AirQuality.pretty/`, `fp-lib-table` | project footprints (OS103011MA7Q switch, WROOM-02 EPAD 0.3 mm) |
| `design_review.md` | findings F1–F24 with evidence, sources and validation checklists |
| `layout_plan.md` | step-by-step placement and routing plan with coordinates |
| `layout_constraints.md` | the rules behind it: antenna, boost loop, edge overhang, widths |
| `bom_kicad_raw.csv` / `bom_pcbway_v7.csv` | BOM (raw / PCBWay: 43 lines, 78 placements, incl. 2 THT switches) |
| `schematic_v7.pdf` | plotted schematic |
| `erc_v7.rpt` / `drc_v7_unrouted.rpt` | ERC (clean) / DRC with schematic parity (expected: unrouted only) |

## Next steps

1. Finish placement per `layout_plan.md` (D2 was re-added in the staging area because its footprint changed).
2. Route (plan step 8), then DRC to zero and the pre-order checklist.
3. Port the firmware (above), then work through the validation checklists in `design_review.md`.
