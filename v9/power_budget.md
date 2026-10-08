# Power Budget — v9 board

Update of [`v6/power_budget.md`](../v6/power_budget.md) for the ESP32-C3 boards (v7 → v9). The duty cycle is
the same as on v6: BSEC ULP with one sample per 300 s, a short wake and ~290 s of deep sleep, 288 wakes per day.
The WiFi mode switch (SW4) splits the budget by mode.

> **All numbers are estimates** (datasheet typicals and the firmware's duty cycle). Nothing here is measured on a
> v7–v9 board yet. The ESP32-C3 firmware port does not exist yet, so the wake time is the biggest unknown.
> Replace the estimates with bench numbers (§8) before sizing batteries for a real deployment.

---

## 1. What changed since v6

| | v6 (ESP8266) | v9 (ESP32-C3) | Effect |
|---|---|---|---|
| MCU deep sleep | ESP-12F ~20 µA | WROOM-02 **~5 µA** | −15 µA |
| Servo rail in sleep | boost "off" but VSYS still reached the servo via L1/D4 (F2): ≥ 37 µA + servo idle | **0** (Q6 load switch) | the v6 budget had missed this |
| Servo supply | 5 V boost, ~400 mA battery-side per move | **VSYS directly** (3.0–4.2 V on battery), no converter loss | less charge per move, but lower torque (F25) |
| Wake current | ESP8266 calibrates its RF at every boot: ~80 mA assumed | ESP32-C3 keeps the radio off unless WiFi starts: **~25–40 mA** assumed | the main gain in OFF/SPARSE |
| USB bridge | CP2102N (only on VBUS) | none (native USB) | no battery effect |
| Charge current | ~455 mA | **~303 mA** (R14 3.3 k, F12) | longer charge time (§6) |
| STEMMA QT port | — | switched by Q8: **0 µA** when off | optional add-on load (§5) |

## 2. Sleep floor (all modes)

| Contributor | Current | Note |
|---|---|---|
| ESP32-C3 deep sleep (RTC timer) | ~5 µA | module datasheet typical |
| AP2112K-3.3 quiescent | ~55 µA | ~80 % of the floor; LDO swap deferred (F14) |
| VBAT divider R20 + R21 (1 M + 270 k) | 3.3 µA | on VBAT, behind Q5 → 0 with POWER off |
| BME688 sleep + board leakage | ~2 µA | |
| R26 10 MΩ (Q5 gate, POWER on) | 0.4 µA | |
| MCP73831 reverse leakage into VBAT_RAW | < 1 µA | only without VBUS; flows even with POWER off |
| Servo rail (Q6 off), STEMMA QT (Q8 off), LEDs, SW4 contacts | 0 | SW4: only if the pull-ups are off in sleep — **F33** |
| **Total** | **≈ 66 µA** | **≈ 1.6 mAh/day** in every mode |

**Trap (F33):** if the firmware keeps the ESP's internal pull-up on a closed SW4 contact during sleep (OFF or
CONTINUOUS position), that adds ~70 µA and **doubles the floor**.

**POWER switch off (SW3):** only the battery side remains: the charger's reverse leakage (< 1 µA) and the cell's
self-discharge (~3 %/month).

## 3. Wake budget (per 300 s cycle)

| Phase | Assumption | Charge per event |
|---|---|---|
| Boot from deep sleep + BSEC state restore + one ULP sample + LED | ~25–40 mA for ~4–6 s (CPU at 160 MHz, radio off; BME688 heater pulses inside) | **~30–65 µAh**, typ. ~40 µAh |
| WiFi upload (associate + DHCP + TLS + HTTPS POST) | ~4–6 s at ~100–130 mA average (TX peaks ~350 mA) | **~110–220 µAh**, typ. ~150 µAh |
| Servo move (only when the IAQ band changes) | SERVO_EN 50 ms ahead, ~150–250 mA for ~1 s at 3.7 V | **~40–70 µAh** per move |

At 3.7 V the servo is slower than at 4.8 V, so a move takes longer, but no boost converter loss is paid.
A few moves per day cost < 0.5 mAh/day, which is negligible.

## 4. Daily totals by mode (typical, with the range)

| Mode (SW4) | What happens | Per day |
|---|---|---|
| **OFF** | 288 wakes, no WiFi | 288 × 40 µAh + floor ≈ **13 mAh** (10–21) |
| **SPARSE** | as OFF, plus one batch upload per hour (every 12th wake) | 13 + 24 × 150 µAh ≈ **17 mAh** (13–26) |
| **CONTINUOUS** | upload at every wake | 288 × (40 + 150) µAh + floor ≈ **56 mAh** (42–84) |

For comparison, the v6 estimates were 34 / 38 / 75–90 mAh/day. The difference is mostly the wake current (§1). It is
also the least certain number, so measure it first.

## 5. Battery life (usable = nameplate × 0.75)

The derating covers the cut-off at ~3.3–3.5 V, temperature and ageing. Typical values; the ranges from §4 give
roughly −40 % / +30 %. Runs longer than ~3 months also lose ~3 %/month to self-discharge.

| Mode | 1000 mAh | 2000 mAh | 3500 mAh (18650) |
|---|---|---|---|
| OFF | ~8 weeks | ~16 weeks | ~6 months |
| SPARSE | ~6 weeks | ~12 weeks | ~5 months |
| CONTINUOUS | ~2 weeks | ~4 weeks | ~6–7 weeks |

**Reading:** SPARSE costs ~30 % more than OFF. CONTINUOUS costs about 4× as much: use it for short campaigns
or with USB power.

### Optional add-on on the STEMMA QT port

An add-on only costs energy while IO2 powers the port. Example, **Sensirion SCD41** (real CO₂) in single-shot mode:
the measurement takes ~5 s, so the ESP stays awake ~5 s longer, and the sensor draws its measurement current
on top of that. Rough estimate: **+40–70 µAh per reading → +12–20 mAh/day** if it measures at every wake. That about
doubles OFF-mode consumption. Measuring CO₂ every 3rd wake (15 min) keeps it at +4–7 mAh/day. Check Sensirion's
notes on automatic self-calibration when the sensor is power-cycled between readings.

## 6. USB power and charging

| | Value |
|---|---|
| Charge current (CC phase) | ~303 mA (R14 = 3.3 kΩ) |
| Charge time, empty → full | ~4 h for 1000 mAh, **~7–8 h for 2000 mAh**, ~13 h for 3500 mAh |
| Port budget | a USB 2.0 port only guarantees 500 mA with the 5.1 kΩ CC pull-downs |
| Worst-case draw on USB | charger 303 mA + ESP32-C3 TX peaks ~350 mA + servo start ~0.6 A |

The device runs normally while charging. On a laptop port, charging plus a WiFi burst plus a servo start can exceed
500 mA for a moment. The firmware avoids this by moving the servo with WiFi idle (F25). Phone chargers (≥ 1.5 A)
are fine.

## 7. Firmware contract for these numbers

- **Sleep:** `esp_sleep_enable_timer_wakeup()` + `esp_deep_sleep_start()`. Before sleeping: SERVO_EN (IO10) LOW,
  STATUS LED off (IO8 HIGH/input), STEMMA QT off (IO2 HIGH/input), SW4 pins IO4/IO5 as plain inputs (F33).
- **Servo:** SERVO_EN HIGH ≥ 50 ms before a move, LOW after it; no PWM on IO0 while SERVO_EN is LOW; skip moves
  below VBAT ≈ 3.5 V; move with WiFi idle (F25).
- **Mode switch:** read IO4/IO5 with pull-ups at each wake, then release them. GPIO wake only on an open contact (F33).
- **BSEC:** stay on **ULP** (300 s). LP mode costs more and breaks calibration across deep sleep.
- **Low battery:** below ~3.3 V on VBAT_SENSE → indefinite deep sleep (F19).
- **Sparse cadence:** batch every 12 wakes (1 h), as on v6.

## 8. Bench verification checklist

1. **Sleep current**, POWER on, SW4 in each position, no USB: expect **~66 µA**, the same in all three
   positions (± 5 µA). A ~70 µA jump in OFF or CONTINUOUS means F33.
2. **POWER off:** battery current < 1 µA.
3. **Wake in OFF mode:** current profile and duration of one wake (scope over a shunt, or a power profiler).
   Update §3 and §4.
4. **One upload** (CONTINUOUS): charge per upload. Then **one hour of SPARSE** as a cross-check.
5. **Servo move** on battery at 4.2 / 3.7 / 3.5 V: peak and average current, move time (F25).
6. **Charge time** of the cell you deploy, and the charger temperature (F12).
7. Record the results here and replace the estimate tables.
