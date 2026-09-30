# Air Quality Checker — User Documentation (v6 board)

A battery-powered indoor air quality monitor. It wakes every 5 minutes,
measures the air with a BME688 sensor, points a servo-driven indicator at the
current air-quality band, optionally uploads readings over WiFi, and goes back
to deep sleep. A full charge lasts weeks to months depending on the WiFi mode.

---

## 1. Controls & indicators at a glance

| Item | Name | What it does |
|---|---|---|
| **SW3** | POWER (slide) | Master battery switch. ON = device runs, OFF = battery disconnected (shipping/storage). |
| **SW4** | WIFI MODE (3-position slide) | Selects OFF / SPARSE / CONTINUOUS upload behavior. See §3. |
| **SW1** | RESET (button) | Restarts the device immediately. |
| **SW2** | BOOT (button) | Two roles: firmware flashing (with RESET) and WiFi re-provisioning. See §6. |
| **D2** | CHG (green LED) | On = battery charging over USB-C. Off = charge complete or USB unplugged. |
| **D3** | STATUS (blue LED, board edge) | Device state — see §5. Visible through the enclosure side. |
| **J1** | USB-C | Charging + data (firmware flashing, serial log). |
| **J4** | LiPo (JST PH 2-pin) | Battery connector. |
| **J3** | SERVO (3-pin) | Servo indicator connector. |
| **JP1** | DEEPSLEEP (solder jumper) | Links GPIO16→RESET so the device can wake from deep sleep. **Factory-bridged — do not change.** |

---

## 2. Getting started

1. **Charge first.** Connect USB-C. The green CHG LED lights while charging
   and goes out when the battery is full (~2–3 h for a 2000 mAh cell).
2. **Choose a WiFi mode** on SW4 (see §3). If unsure, start with OFF — the
   device works fully offline.
3. **Slide POWER on.** The blue STATUS LED starts blinking (sensor
   stabilizing) and the servo may move to its initial position.
4. **Expect a learning period.** The gas sensor needs ~48 h of cumulative
   runtime to reach full accuracy (level 3). Meaningful readings start much
   earlier (accuracy ≥ 1), but treat the first days as warm-up. Calibration
   state is saved across sleep cycles, so this happens only once.

> Do first-time WiFi setup (§4) while on USB power — a setup session costs
> ~15–20 mAh, and on USB it is free.

---

## 3. WiFi modes (SW4)

Slide positions are laid out **OFF – SPARSE – CONTINUOUS** left to right.
The mode is read once at every wake; you can change it at any time, no
reflash needed.

| Position | Mode | Behavior | Daily energy | Typical battery life* |
|---|---|---|---|---|
| Left (POS.1) | **OFF** | Never uses WiFi. Measurements + servo only. | ~34 mAh | ~6 weeks on 2000 mAh |
| Middle (POS.2) | **SPARSE** | Buffers readings on the device, uploads one batch **every hour**. | ~38 mAh | ~5–6 weeks on 2000 mAh |
| Right (POS.3) | **CONTINUOUS** | Uploads every 5-minute sample. | ~75–90 mAh | ~6 weeks on 5000 mAh |

\* Rule of thumb at nameplate × 0.75 usable capacity. Details:
[`power_budget.md`](power_budget.md). SPARSE is nearly free compared to OFF;
CONTINUOUS roughly triples the energy need — for long deployments in
CONTINUOUS, consider USB power.

Data uploaded per reading: IAQ, accuracy, temperature, humidity, pressure,
eCO₂, bVOC, and battery voltage.

---

## 4. WiFi setup (provisioning)

Credentials are **never compiled into the firmware** — they are entered once
through a captive portal and stored on the device (they survive firmware
updates; only a full flash erase wipes them).

### First-time setup

1. Slide SW4 to **SPARSE** or **CONTINUOUS** and power on (or press RESET).
2. With no credentials stored, the device starts the setup portal:
   the STATUS LED blinks **long – short – short** and a WiFi network named
   **`Birdy-Setup-<chipid>`** appears.
3. Join that network with your phone — the setup page opens automatically
   (or browse to `192.168.4.1`).
4. Enter WiFi SSID + password, API URL, API key, and the Birdy ID, then
   **Save & Reboot**. The device reboots into the selected mode and starts
   uploading.
5. If nobody configures within **~3 minutes**, the device goes back to sleep
   to protect the battery and offers the portal again on the next wake
   (every 5 min until configured, or until you switch to OFF).

### Re-provisioning (change WiFi later)

With credentials already stored, the device would normally connect straight
away. To force the portal again:

**Press and release RESET, then press BOOT within ~0.5 s.** The STATUS LED
shows the long–short–short pattern and `Birdy-Setup-<chipid>` appears again.

---

## 5. STATUS LED (blue) — what it means

| Pattern | Meaning |
|---|---|
| Solid ON (a few seconds, then off) | Normal wake, sensor calibrated (accuracy ≥ 1) |
| Blinking ½ s on / ½ s off | Sensor still stabilizing (accuracy = 0) — normal after first power-on |
| **Long – short – short** (repeating) | **WiFi setup mode active** — join `Birdy-Setup-<chipid>` |
| Off | Deep sleep (normal — the device sleeps ~98 % of the time) or no power |

The green CHG LED is independent: on = charging, off = full or unplugged.

---

## 6. Buttons in detail

### RESET (SW1)
Restarts the device. Use it after changing the WiFi mode switch if you don't
want to wait for the next 5-minute wake, or as the first step of any
troubleshooting.

### BOOT (SW2)
- **Re-provisioning:** press within ~0.5 s after RESET → forces WiFi setup
  mode (see §4). This is how you change WiFi credentials in the field.
- **Firmware flashing (recovery):** hold BOOT, tap RESET, release BOOT → the
  ESP8266 enters UART download mode for flashing over USB. You normally never
  need this — the USB chip does it automatically during a programmed upload —
  but it is the manual un-brick path if an upload went wrong.

---

## 7. Everyday behavior — what "normal" looks like

- The device is asleep most of the time (STATUS LED off). Every 5 minutes it
  wakes for a few seconds: LED on or blinking, a quiet servo move *if* the
  air-quality band changed, then back to sleep.
- **The servo does not move on every reading** — only when the IAQ band
  changes. Hours of stillness are normal and save the battery.
- The servo pointer sweeps 0°–180° across seven bands:

| IAQ | Band | Pointer |
|---|---|---|
| 0–50 | Excellent | far left (0°) |
| 51–100 | Good | 30° |
| 101–150 | Lightly polluted | 60° |
| 151–200 | Moderately polluted | 90° |
| 201–250 | Heavily polluted | 120° |
| 251–350 | Severely polluted | 150° |
| > 350 | Extremely polluted | far right (180°) |

- Notes on the numbers: **eCO₂ is a VOC-based estimate, not a true CO₂
  measurement.** Readings are trends, not lab-grade absolutes; the sensor is
  designed for indoor air.

---

## 8. Power, battery, charging

- **Charging:** any USB-C source. Charge current ~450 mA; a 2000 mAh cell
  fills in ~2–3 h. The device works normally while charging.
- **Battery options** (JST PH 2-pin, mind the polarity): 2000 mAh pouch for
  OFF/SPARSE deployments up to ~30–60 days; 18650 cells (3300–3500 mAh each)
  for longer; see the table in §3. For CONTINUOUS mode beyond ~30 days, use
  USB power instead.
- **POWER off** disconnects the battery completely — use it for shipping and
  storage. The battery then only self-discharges (~3 %/month).
- **Battery monitoring:** the device measures its own battery voltage every
  wake and (in WiFi modes) uploads it with each reading.
- LiPo basics: don't charge unattended on flammable surfaces, don't use
  damaged/swollen cells, charge between 0–45 °C.

---

## 9. Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| No LEDs, nothing happens | POWER switch off? Battery empty or unplugged? Charge over USB-C and retry. |
| STATUS blinks long–short–short | Device is in WiFi setup mode — join `Birdy-Setup-<chipid>` and configure (§4). If unwanted, slide SW4 to OFF. |
| No uploads, but LED looks normal | SW4 in OFF? WiFi credentials wrong → re-provision (§4). Router out of range? In SPARSE, uploads happen only once per hour. |
| Servo never moves | Normal if the IAQ band is stable — it only moves on band *changes*. |
| Servo twitches but doesn't complete a move | Battery low (servo rail sags) — charge. |
| Readings stuck at "stabilizing" for days | Sensor needs ~48 h cumulative burn-in. If it never improves after that, contact support — calibration state may be corrupt. |
| Green CHG LED never lights on USB | Battery already full, or USB source dead, or battery disconnected. |
| Need to reflash firmware | Connect USB-C, hold BOOT, tap RESET, release BOOT → download mode. |

---

## 10. Quick reference

| | |
|---|---|
| Wake cycle | every ~5 min (290 s sleep + ~5–10 s awake) |
| Sleep current | ~80 µA (whole device) |
| Battery | 3.7 V LiPo, JST PH 2-pin |
| Charging | USB-C, ~450 mA, green LED = charging |
| WiFi modes | OFF / SPARSE (hourly batch) / CONTINUOUS (every sample) |
| Setup portal | `Birdy-Setup-<chipid>`, ~3 min timeout |
| Sensor | BME688 (temp, humidity, pressure, VOC gas → IAQ) |
| Full accuracy | after ~48 h cumulative runtime (one-time) |
