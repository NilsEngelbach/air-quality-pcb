# Air Quality Checker — User Documentation (v9 board)

A battery-powered indoor air-quality monitor. Every 5 minutes it wakes up, measures the air with a Bosch
BME688 sensor, turns a pointer (servo) to the current air-quality band, can upload the reading over WiFi, and
goes back to sleep. Depending on the WiFi mode and the battery, one charge lasts weeks to months.

> **Firmware status:** this guide describes the v9 board running the ESP32-C3 firmware. That firmware port is
> still to be done (see [`README.md`](README.md), *Firmware port*). The behaviour below follows the current
> firmware (v6 board) adapted to v9. Points marked **(planned)** depend on features that the port still has to add.

---

## 1. Controls and indicators

All controls sit on one edge of the device, the **control edge**:

```
   ●STATUS        [ WIFI MODE ]        ( USB-C )        [ POWER ]        CHG●
   blue LED        3-position          charge +          on / off       green LED
                   slide switch        data              slide switch
```

| Item | Name | What it does |
|---|---|---|
| **SW3** | POWER (slide) | Main switch. ON = the device runs from the battery. OFF = battery disconnected (storage, shipping). USB still charges and powers the device when OFF. |
| **SW4** | WIFI MODE (3-position slide) | OFF / SPARSE / CONTINUOUS — see §3. |
| **J1** | USB-C | Charging, and firmware updates / log output. |
| **D3** | STATUS (blue LED) | Device state — see §5. |
| **D2** | CHG (green LED) | On = battery charging. Off = full, or no USB. |

Inside the enclosure (only needed for service):

| Item | Name | What it does |
|---|---|---|
| **SW1** | RESET (button) | Restarts the device. |
| **SW2** | BOOT (button) | WiFi re-setup and firmware recovery — see §6. |
| **J4** | LiPo (JST PH 2-pin) | Battery connector. The plug is keyed. |
| **J3** | SERVO (3-pin) | Pointer servo. Pin labels on the board: **S** (signal) / **+** / **−**. |
| **J5** | STEMMA QT / Qwiic (4-pin JST SH) | Optional add-on sensor, e.g. a true CO₂ sensor. Powered only while it is used. |

---

## 2. Getting started

1. **Charge first.** Connect USB-C. The green CHG LED lights while charging and goes out when the battery is full
   (~7–8 h for a 2000 mAh cell; the charger is deliberately gentle to keep heat away from the sensor).
2. **Choose a WiFi mode** on WIFI MODE (§3). If unsure, start with **OFF**: the device works fully offline.
3. **Slide POWER on.** The blue STATUS LED blinks (sensor stabilising) and the pointer moves to its first position.
4. **Expect a learning period.** The gas sensor needs about **48 hours** of running time to reach full accuracy.
   Readings are usable much earlier, but treat the first two days as warm-up. The calibration is kept across sleep
   cycles, so this happens only once, or again after the battery was completely empty.

> Do the first WiFi setup (§4) on USB power. A setup session keeps the device fully awake for a few minutes.

---

## 3. WiFi modes (WIFI MODE switch)

The two end positions are **OFF** and **CONTINUOUS**; the middle position is **SPARSE**. Check the labels on your
enclosure for which end is which. The mode is read at every wake, so a change takes effect within 5 minutes.
No reflash is needed.

| Position | Mode | Behaviour | Typical battery life* (2000 mAh) |
|---|---|---|---|
| End | **OFF** | Never uses WiFi. Measurement and pointer only. | ~3–4 months |
| Middle | **SPARSE** | Stores readings on the device and uploads them as one batch **every hour**. | ~3 months |
| Other end | **CONTINUOUS** | Uploads every 5-minute reading. | ~4 weeks |

\* Estimates, not yet measured on this board. Details and other battery sizes:
[`power_budget.md`](power_budget.md). SPARSE costs little more than OFF. For long CONTINUOUS deployments, use USB power.

Each upload contains IAQ, accuracy, temperature, humidity, pressure, eCO₂, bVOC and battery voltage.

---

## 4. WiFi setup (provisioning)

WiFi credentials are **never built into the firmware**. You enter them once in a setup page on the device; they
are stored on the device and survive firmware updates (only a full flash erase removes them).

### First-time setup

1. Set WIFI MODE to **SPARSE** or **CONTINUOUS** and slide POWER on.
2. With no credentials stored, the device starts its setup portal: the STATUS LED blinks
   **long – short – short**, and a WiFi network named **`Birdy-Setup-<id>`** appears.
3. Join that network with your phone. The setup page opens by itself (otherwise browse to `192.168.4.1`).
4. Enter WiFi name and password, API URL, API key and Birdy ID, then tap **Save & Reboot**. The device restarts in
   the selected mode and starts uploading.
5. If nobody completes the setup within **~3 minutes**, the device goes back to sleep to save the battery. It offers
   the portal again at the next wake (every 5 minutes), until it is configured or you switch to OFF.

### Changing the WiFi later

- **(planned) Without opening the enclosure:** a switch gesture on WIFI MODE will force the setup portal, for example
  OFF → CONTINUOUS → OFF → CONTINUOUS within 5 seconds. The exact gesture is defined by the firmware port.
- **With the enclosure open (same sequence as on the v6 board):** press and release **RESET**, then press
  **BOOT** within about half a second. The STATUS LED shows long – short – short and `Birdy-Setup-<id>` appears again.

> Order matters: if BOOT is still **held while RESET is released**, the chip starts in firmware-download mode
> instead (§6). Nothing breaks: just press RESET again.

---

## 5. STATUS LED (blue)

| Pattern | Meaning |
|---|---|
| On for a few seconds, then off | Normal wake, sensor calibrated |
| Blinking ½ s on / ½ s off | Sensor still stabilising — normal during the first days |
| **Long – short – short**, repeating | **WiFi setup portal active** — join `Birdy-Setup-<id>` |
| Off | Asleep (normal: the device sleeps ~98 % of the time), or no power |
| **(planned)** One blink, then nothing for a long time | Battery empty: the device has switched itself off to protect the cell — charge it |

The green CHG LED is independent: on = charging, off = full or unplugged.

---

## 6. Buttons (inside the enclosure)

### RESET (SW1)
Restarts the device immediately. Use it after a WiFi mode change if you don't want to wait for the next wake, or as
the first step when troubleshooting.

### BOOT (SW2)
- **WiFi re-setup:** RESET, then BOOT within ~0.5 s (§4).
- **Firmware recovery:** hold BOOT, tap RESET, release BOOT. The chip then waits in download mode and shows up as a
  USB serial/JTAG device, ready for flashing. Normal firmware updates over USB-C don't need this. It is the recovery
  path if an update went wrong, or if the computer cannot see the device because it is asleep (§9).

---

## 7. Everyday behaviour

- The device is asleep most of the time (STATUS LED off). Every 5 minutes it wakes for a few seconds: the LED lights or
  blinks, the pointer moves *if* the air-quality band changed, then it sleeps again.
- **The pointer only moves when the band changes.** Hours without movement are normal and save battery.
- The pointer sweeps 0°–180° across seven bands:

| IAQ | Band | Pointer |
|---|---|---|
| 0–50 | Excellent | far left (0°) |
| 51–100 | Good | 30° |
| 101–150 | Lightly polluted | 60° |
| 151–200 | Moderately polluted | 90° |
| 201–250 | Heavily polluted | 120° |
| 251–350 | Severely polluted | 150° |
| > 350 | Extremely polluted | far right (180°) |

- **On battery the pointer moves more slowly** than on USB. The servo runs directly from the battery (3.0–4.2 V)
  instead of a 5 V supply. This is expected.
- **(planned)** When the battery is low (below ~3.5 V), the pointer stops moving to protect the electronics.
  Readings and uploads continue. Charge the device.
- **eCO₂ is an estimate derived from the VOC reading, not a real CO₂ measurement.** For real CO₂, add a CO₂ sensor
  on the STEMMA QT port (§8). Treat all readings as trends; the sensor is designed for indoor air.

---

## 8. Power, battery, charging

- **Charging:** any USB-C charger or computer port. Charge current is ~300 mA; a 2000 mAh cell takes ~7–8 h. The
  device keeps working while it charges.
- **On a laptop port** the device can briefly draw close to the port's 500 mA limit (charging + WiFi + pointer). A
  phone charger (≥ 1.5 A) avoids that.
- **Battery:** single-cell LiPo / Li-ion, 3.7 V, **with built-in protection circuit**, JST PH 2-pin plug (keyed).
  Rough sizes: 1000–2000 mAh for OFF/SPARSE; 18650 cells (3300–3500 mAh) for long deployments; see
  [`power_budget.md`](power_budget.md).
- **POWER off** disconnects the battery from the electronics. Use it for storage and shipping. The cell then only
  self-discharges (~3 % per month).
- **Battery monitoring:** the device measures its battery voltage at every wake and uploads it (WiFi modes).
- **STEMMA QT add-on:** plug in while the device is off. Add-ons cost battery only while they measure, but a CO₂
  sensor measuring every 5 minutes roughly doubles the consumption in OFF mode.
- **Placement:** keep metal (battery, screws, cables) and your hand away from the WiFi antenna end of the board.
  Don't block the sensor opening in the enclosure.
- LiPo safety: don't charge unattended on flammable surfaces; don't use damaged or swollen cells; charge at 0–45 °C.

---

## 9. Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| No LEDs, nothing happens | POWER off? Battery empty or unplugged? Connect USB-C (green LED should light) and press RESET. |
| STATUS blinks long – short – short | WiFi setup portal is active — join `Birdy-Setup-<id>` (§4). If unwanted, switch WIFI MODE to OFF. |
| No uploads, LED looks normal | WIFI MODE on OFF? Wrong credentials → re-setup (§4). Router out of range? In SPARSE, uploads happen only once per hour. |
| Pointer never moves | Normal while the air-quality band stays the same. |
| Pointer moves slowly or stops part-way | Battery low — charge. On USB it should move normally. |
| Pointer stopped updating, readings still upload | **(planned)** low-battery servo cut-off — charge. |
| Readings stay "stabilising" for days | The sensor needs ~48 h of running time. If it never improves, the stored calibration may be damaged; a firmware reset clears it. |
| Green CHG LED never lights on USB | Battery already full, battery unplugged, or the USB source provides no power. |
| Computer doesn't find the device for a firmware update | It is asleep (the USB port only exists while it is awake). Use the recovery sequence: hold BOOT, tap RESET, release BOOT (§6). |
| Device restarts when the pointer moves | Battery very low, or a weak USB port while charging — charge, or use a stronger charger. |

---

## 10. Quick reference

| | |
|---|---|
| Wake cycle | every ~5 min (~290 s sleep + a few seconds awake) |
| Sleep current | ~66 µA, whole device (estimate) |
| Battery | 3.7 V LiPo / Li-ion with protection, JST PH 2-pin |
| Charging | USB-C, ~300 mA, green LED = charging |
| WiFi modes | OFF / SPARSE (hourly batch) / CONTINUOUS (every reading) |
| Setup portal | `Birdy-Setup-<id>`, ~3 min timeout, `192.168.4.1` |
| Sensor | BME688: temperature, humidity, pressure, VOC gas → IAQ, eCO₂, bVOC |
| Full accuracy | after ~48 h of running time (one-time) |
| Add-on port | STEMMA QT / Qwiic, 3.3 V, switched off between readings |
| Firmware update | over USB-C (native USB); recovery: hold BOOT, tap RESET, release BOOT |
