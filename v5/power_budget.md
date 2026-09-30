# Power Budget — v5 board (findings)

Analysis of the v5 hardware (`air-quality-pcb-v5.kicad_sch`) running the current
firmware (`air-quality-checker`, default build: BSEC ULP 300 s, WiFi disabled).
These findings motivate the v6 revision. All numbers are engineering estimates
from datasheet typicals + the firmware duty cycle; verify on the bench with a
multimeter in series with the battery line.

---

## 1. Duty cycle (firmware as-is)

One BSEC-ULP cycle = **300 s**:

- **Awake ~5 s**: ESP8266 boot (~0.3 s), `delay(100)`, BSEC init + state restore,
  one ULP measurement incl. ~2 s gas-heater scan, optional servo move (0.7 s,
  only on IAQ *band* change), RTC/EEPROM state save.
- **Deep sleep ~295 s**: everything except +3V3 rail, LDO and the always-on
  loads listed below is off.

288 cycles per day.

## 2. Power when active

| Contributor | Current | Notes |
|---|---|---|
| ESP-12F (CPU + boot/RF cal) | ~75 mA avg, peaks ~170 mA | WiFi never enabled in default build |
| BME688 during gas scan | + ~3.9 mA for ~2 s | heater plate energized only during scan |
| Status LED D3 (GPIO2, R16 1 kΩ) | + ~2 mA | only while awake |
| **Typical wake** | **~80 mA ≈ 0.30 W @ 3.7 V** | **~110 µAh per wake** |
| Servo move (band change only) | ~250 mA @ 5 V ≈ 1.3 W for 0.7 s | ~400 mA from battery through the boost at ~85 % eff.; ~78 µAh/move; assumed ~2 moves/day |

Daily active-side total: 288 × 110 µAh ≈ 31.7 mAh + ~0.2 mAh servo ≈ **~32 mAh/day**.

## 3. Power when sleeping (v5 schematic, per netlist)

| Contributor | Current | Per day |
|---|---|---|
| ESP-12F deep sleep | ~20 µA | 0.48 mAh |
| AP2112K quiescent (Iq) | ~55 µA | 1.32 mAh |
| VBAT_SENSE divider R20 100k + R21 27k (permanently across VBAT) | ~29 µA | 0.70 mAh |
| BME688 digital sleep | 0.15 µA | ~0 |
| Leakage / misc (MCP73831 reverse, FETs, caps) | ~2 µA | 0.05 mAh |
| **Sleep floor (servo rail gated)** | **~106 µA ≈ 0.4 mW** | **~2.5 mAh** |

Notable **zero-cost** items on v5 (verified in netlist): CP2102N is purely
VBUS-powered, CHG LED hangs off VBUS, I2C pull-ups idle high — none of these
touch the battery.

## 4. The catch: servo + boost are powered 24/7 on v5

Netlist facts:

- `U7` (MT3608) pin 4 (EN) and pin 5 (IN) are both tied to **VSYS** → the boost
  converter is always enabled.
- Servo header `J3` pin 2 sits on **SERVO_5V** permanently.

Consequences, referred to the 3.7 V battery (boost ~85 % efficient):

| Load | @ 5 V | @ battery | Per day |
|---|---|---|---|
| SG92R idle, PWM detached (driver IC still alive) | ~4–6 mA (typ. for SG90/SG92R-class analog servos — **measure**) | ~6–9 mA | 150–215 mAh |
| MT3608 Iq (~100 µA) + FB divider R22+R23 93 kΩ (~54 µA @ 5 V) | — | ~0.2 mA | ~4.8 mAh |

**≈ 170 mAh/day extra** — five times everything else combined. With the rail
ungated, 30 days needs ~8 Ah and 90 days ~25 Ah: impractical.

**Fix (adopted in v6):** drive MT3608 EN from **GPIO15** (existing R4 10 kΩ
pull-down keeps it off at boot and during deep sleep). Firmware raises EN ~100 ms
before a servo move and drops it afterwards. MT3608 shutdown current < 1 µA.

## 5. BME688 "keep-warm" concern — does not apply here

The gas heater is **not** kept warm between samples. In BSEC ULP mode
(`bme688_sel_33v_300s_4d` in `BirdySensor.cpp`) the heater plate is only pulsed
during the ~2 s scan at each 300 s sample, then cools to ambient; BSEC explicitly
models the 300 s cold gap (that is exactly why LP mode is incompatible with deep
sleep — see the comment block in `BirdySensor.cpp`). The sensor's constant draw
is its 0.15 µA digital sleep current.

Honest sensor average: Bosch's ULP figure **~90 µA ≈ 2.2 mAh/day**, already
included in section 2/6.

Do **not** switch to BSEC LP (3 s): 0.9 mA average ≈ 21.6 mAh/day extra **and**
it breaks calibration across deep sleep.

## 6. Bottom line (WiFi off, servo rail gated as in v6)

| Term | Per day |
|---|---|
| Wake activity (288 × ~110 µAh) | ~31.7 mAh |
| Sleep floor (v5: 106 µA; v6 with 1 M/270 k divider: ~80 µA) | 2.5 / 1.9 mAh |
| Servo moves (~2/day) | ~0.2 mAh |
| **Total** | **~34–35 mAh/day** |

### Battery sizing (nameplate × 0.75 usable)

Derating accounts for cutoff at ~3.5 V (AP2112K dropout), LiPo self-discharge
~3 %/month, temperature and aging reserve.

| Target | Required energy | Min. nameplate | Practical cell |
|---|---|---|---|
| 30 days | ~1.0 Ah | **≥ 1.4 Ah** | 2000 mAh LiPo pouch |
| 60 days | ~2.0 Ah | **≥ 2.7 Ah** | 1× 18650 (3300–3500 mAh) or 3000 mAh pouch |
| 90 days | ~3.1 Ah | **≥ 4.1 Ah** | 5000 mAh pouch or 2× 18650 parallel |

Sanity check: a 2000 mAh pouch yields ~45 days; a single quality 18650 yields
~70–75 days.

### With the servo rail left ungated (v5 as shipped)

~35 + ~170 ≈ **~205 mAh/day** → 30 d ≈ 8.2 Ah, 60 d ≈ 16.4 Ah, 90 d ≈ 24.6 Ah.
Not viable on a handheld cell. **Gate the rail.**

## 7. WiFi cost preview (for the v6 mode switch)

One upload (association + DHCP + TLS + HTTPS POST, ~4–6 s @ ~120 mA avg) costs
~130–200 µAh extra per wake:

| Mode | Extra | Total/day |
|---|---|---|
| WiFi off | — | ~35 mAh |
| Sparse (1 upload/h, amortized over 12 wakes) | ~4–5 mAh | ~39–40 mAh |
| Continuous (upload every wake) | ~45–58 mAh | ~80–93 mAh |

Full sizing for all three modes lives in `v6/README.md`.

## 8. Ways to shave further (not in v6)

- Trim wake window ~5 → ~3.5 s (drop `delay(100)`, fewer serial prints,
  `WiFi.mode(WIFI_OFF)` early): −~8 mAh/day.
- Lower-Iq LDO than AP2112K (55 µA): e.g. TLV755P (25 µA, same SOT-23-5
  pinout) — saves ~0.7 mAh/day; not swapped in v6 (600 mA rating is comfortable,
  change is low-value vs. risk).
- `VBAT_SENSE` divider 100k/27k → 1M/270k (**is** in v6): 29 → 3.3 µA.

## 9. Assumptions

- v5 board, firmware default build (`env:huzzah`, WiFi disabled), BSEC ULP 300 s.
- ~2 servo band-changes per day; indoor temperature.
- Wake window ~5 s at ~80 mA average.
- Servo idle current 4–6 mA @ 5 V is the literature value for SG90/SG92R-class
  analog servos — **verify on the bench**; even the low end dominates the budget.
- Recharge time at MCP73831 ~455 mA (R14 2.2 kΩ): 2000 mAh ≈ 4.5–5 h;
  5000 mAh ≈ 11–12 h.
