# Power Budget — v6 board

Update of [`v5/power_budget.md`](../v5/power_budget.md) for the v6 revision.
Same duty cycle and wake behavior as v5 (BSEC ULP 300 s, ~5 s awake + ~295 s
deep sleep, 288 cycles/day); v6 changes the *constant* drains and adds the
WiFi mode switch, so the budget is split by mode.

All numbers are estimates (datasheet typicals + firmware duty cycle). Verify on
the bench: sleep target ≤ 0.1 mA.

---

## 1. What v6 fixes vs v5

| | v5 | v6 | Saves |
|---|---|---|---|
| Servo rail | MT3608 EN tied to VSYS — boost + SG92R powered 24/7 (~170 mAh/day) | EN driven by **GPIO15**; R4 10 kΩ keeps it off at boot and in deep sleep; firmware raises it ~100 ms before a move | ~170 mAh/day |
| VBAT_SENSE divider | 100 k/27 k = 29 µA continuous | **1 M/270 k** = 3.3 µA (same ratio, 4.2 V → 0.89 V; C17 100 nF keeps the ADC happy) | ~0.6 mAh/day |
| Status LED | top-view 0805, R16 1 kΩ | side-view KPA-3010QBC-D, R16 **220 Ω** (~2 mA drive — blue InGaN Vf ≈ 2.8–3.0 V barely conducts through 1 kΩ on 3.3 V) | brightness, not power |

The mode switch costs nothing electrically: GPIO12/14 are read once at boot with
the ESP internal pull-ups and are never pulled up during deep sleep, so a closed
switch contact draws zero.

## 2. Sleep floor (all modes)

| Contributor | v5 | v6 |
|---|---|---|
| ESP-12F deep sleep | 20 µA | 20 µA |
| AP2112K quiescent | 55 µA | 55 µA |
| VBAT_SENSE divider | 29 µA | 3.3 µA |
| MT3608 + SG92R idle | ~7 mA (rail always on) | **< 1 µA** (EN low = shutdown) |
| BME688 sleep + leakage | ~2 µA | ~2 µA |
| **Total** | **~7.2 mA** | **~80 µA (0.3 mW)** |

→ **1.9 mAh/day** in every mode. The BME688 heater is not kept warm between
samples (ULP pulses it ~2 s per 300 s cycle); its ~90 µA ULP average is inside
the wake budget.

## 3. Wake budget (per 300 s cycle)

| Phase | Current | Charge/cycle |
|---|---|---|
| Boot + BSEC restore + one ULP measurement (incl. ~2 s heater scan ~3.9 mA) + LED | ~80 mA for ~5 s | ~110 µAh |
| WiFi upload (association + DHCP + TLS + HTTPS POST, ~4–6 s @ ~120 mA) — only in WiFi modes | ~120 mA | ~170 µAh per upload |
| Servo move (only on IAQ band change, ~2/day) | ~250 mA @ 5 V for 0.7 s | ~78 µAh/move (~0.2 mAh/day) |

## 4. Daily totals by mode

| Mode | Per cycle | Per day |
|---|---|---|
| **OFF** (SW4 POS.1) | ~110 µAh | **~34 mAh** |
| **SPARSE 1/h** (POS.2, upload amortized over 12 wakes) | ~124 µAh | **~38 mAh** |
| **SPARSE 1/2 h** (POS.2, 24 h cadence) | ~118 µAh | **~36 mAh** |
| **CONTINUOUS** (POS.3, upload every wake) | ~245–310 µAh | **~75–90 mAh** |

## 5. Battery sizing (nameplate × 0.75 usable)

Derating: cutoff ~3.5 V, LiPo self-discharge ~3 %/month, temperature, aging.

| Mode | 30 days | 60 days | 90 days |
|---|---|---|---|
| OFF | ≥ 1.4 Ah → **2000 mAh pouch** | ≥ 2.7 Ah → **1× 18650 (3300–3500)** | ≥ 4.1 Ah → **5000 mAh pouch / 2× 18650** |
| SPARSE 1/h | ≥ 1.5 Ah → **2000 mAh** | ≥ 3.0 Ah → **1× 18650 (3500)** | ≥ 4.6 Ah → **5000–6000 mAh / 2× 18650** |
| SPARSE 1/2 h | ≥ 1.45 Ah → **2000 mAh** | ≥ 2.9 Ah → **1× 18650** | ≥ 4.3 Ah → **5000 mAh** |
| CONTINUOUS | ≥ 3.4 Ah → **5000 mAh** | ≥ 6.8 Ah → **10 Ah pouch / 3× 18650** | ≥ 10 Ah → **4× 18650 — or just power it over USB** |

Reading: **sparse mode is nearly free** — an hourly upload costs ~4 mAh/day and
barely changes the cell choice. Continuous mode triples the energy need and only
makes sense for short deployments or mains/USB-powered operation.

## 6. WiFi setup mode power

Provisioning (captive portal AP + web server, ESP fully awake) draws ~150–250 mA
continuously, plus ~2 mA for the blinking LED. A 5-minute setup session costs
~15–20 mAh one-time — negligible, but do initial setup on USB power anyway
(the board charges the cell at the same time, so it is free).

The check happens once per boot: switch moved to SPARSE or CONTINUOUS and **no
credentials stored** → setup mode (LED blinks *long–short–short*), which stays
awake until configured or times out (~3 min) back into deep sleep.

## 7. Firmware contract for these numbers

- Servo boost: `BOOST_EN` (GPIO15) HIGH ≥ 100 ms before moving, LOW right after;
  never HIGH across a deep sleep. MT3608 shutdown < 1 µA.
- Modes: read GPIO12/14 once at boot (`INPUT_PULLUP`). POS.1 = GPIO12 low → OFF;
  POS.2 = open (both high) → SPARSE; POS.3 = GPIO14 low → CONTINUOUS.
- Sparse buffering: readings land in LittleFS between uploads; upload batch,
  then truncate. Cadence via the existing `rtcData.bootCount` (12 = 1 h, 24 = 2 h).
- Stay on BSEC **ULP** 300 s. LP mode would add ~21.6 mAh/day and break
  calibration across deep sleep.

## 8. Bench verification checklist

1. Sleep current, switch OFF, servo rail gated: expect **~0.08 mA** (v5 would
   read ~7 mA — if you see that on v6, EN is not low).
2. Same with switch in SPARSE/CONTINUOUS: identical (the switch draws nothing).
3. Servo move: brief ~400 mA battery-side pulse; rail silent afterwards.
4. One hour of SPARSE: ~1.6 mAh consumed per hour including the upload.
