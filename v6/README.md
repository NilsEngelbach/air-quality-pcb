# Air Quality Checker — PCB v6

Sixth iteration: the v5 board plus the **power-budget fixes**, a **3-position
WiFi mode switch**, and a **side-view status LED**. The layout has been
F8-synced and updated: SW4 + D3 placed, re-routed, zones refilled — DRC clean
(`drc_v6_check.rpt`). Gerbers are still to be generated.

> Baseline: v5 (round Ø 72 mm, on-board BME688, ESP-12F, CP2102N, MCP73831,
> AP2112K, MT3608 servo boost). See [`v5/power_budget.md`](../v5/power_budget.md)
> for the findings that motivated this revision, and [`power_budget.md`](power_budget.md)
> for the v6 numbers per WiFi mode.

---

## What changed vs v5

| # | Change | Why |
|---|---|---|
| 1 | **MT3608 EN (U7-4) driven by GPIO15** instead of VSYS | v5 kept the boost + SG92R alive 24/7 (~170 mAh/day — five times everything else). GPIO15's existing R4 10 kΩ pull-down holds EN low at boot and during deep sleep; MT3608 shutdown < 1 µA |
| 2 | **SW4: 3-position slide switch** (PCM13SMTR, SP3T ON-ON-ON) selects the WiFi mode | user-selectable OFF / SPARSE / CONTINUOUS without reflashing |
| 3 | **D3 → Kingbright KPA-3010QBC-D** side-view (right-angle) blue LED, R16 1 kΩ → **220 Ω** | LED must face out of the enclosure side; on 3.3 V a blue InGaN LED (Vf ≈ 2.8–3.0 V) barely conducts through 1 kΩ — 220 Ω gives ~2 mA |
| 4 | **VBAT_SENSE divider 100 k/27 k → 1 M/270 k** (R20/R21) | 29 µA → 3.3 µA continuous; same ratio (4.2 V → 0.89 V), C17 100 nF covers the ADC sampling |

No other nets touched. ERC: **0 errors, 0 warnings** (`erc_v6.rpt`).

---

## 1. WiFi mode switch (SW4)

C&K **PCM13SMTR**, SP3T ON-ON-ON right-angle slide switch
(`Button_Switch_SMD:SW_SP3T_PCM13`). Datasheet truth table (terminal 3 = common):

| Slide position | Connected terminals | v6 wiring | Firmware decode (INPUT_PULLUP) |
|---|---|---|---|
| POS.1 | 1–3 | pad 1 → **GPIO12** | GPIO12 = LOW → **WiFi OFF** |
| POS.2 | 2–3 | pad 2 → NC (no-connect) | both HIGH → **SPARSE** (upload 1×/hour) |
| POS.3 | 3–4 | pad 4 → **GPIO14** | GPIO14 = LOW → **CONTINUOUS** (upload every 5-min sample) |

Common (pad 3) → **GND**. Deliberately **no external pull-ups**: the pins are
read once at boot with the ESP8266 internal pull-ups; +3V3 stays alive in deep
sleep, so an external pull-up across a closed contact would leak ~330 µA 24/7.

Layout order on the slider is POS.1–POS.2–POS.3, i.e. **OFF – SPARSE –
CONTINUOUS** left to right when oriented like the schematic.

## 2. Servo boost gating (GPIO15)

Firmware contract: drive GPIO15 HIGH ≥ 100 ms before moving the servo, LOW
immediately after, never HIGH across a deep sleep. GPIO15 is a boot-strap pin —
R4 keeps it LOW at boot, which is exactly the required default (boost off).

## 3. Side-view status LED (D3)

Kingbright **KPA-3010QBC-D** (blue, right-angle, 3.0×2.0×1.0 mm), same circuit:
`+3V3 → R16 220 Ω → D3 → GPIO2`, active-LOW. Place it at the **board edge,
facing outward**. Pad 3 of the footprint is a mechanical dummy pad (stays
unconnected); verify polarity on the first board (pad 1 = cathode per the
Kingbright/KiCad pairing).

### LED behavior spec

| State | Pattern |
|---|---|
| Normal, IAQ accuracy ≥ 1 | solid ON while awake, OFF in deep sleep (as today) |
| Normal, accuracy = 0 (stabilizing) | 500 ms blink (as today) |
| **WiFi setup mode active** | **long – short – short** (600 ms ON, 200 ms OFF, 200 ms ON, 200 ms OFF, 200 ms ON, 1 s OFF, repeat) |
| WiFi OK (credentials found, normal upload) | no setup blinking; LED follows normal status |

## 4. WiFi credentials — setup flow (no flashing)

Credentials are **never compiled in**. At every boot where the mode switch is
SPARSE or CONTINUOUS:

1. Firmware checks for stored credentials (ESP8266 SDK flash sector /
   `WiFi.SSID()` non-empty, plus API config in LittleFS).
2. **Credentials present** → connect and upload (sparse: batch from LittleFS);
   LED shows normal status.
3. **No credentials** → enter **setup mode**: start captive-portal AP
   `Birdy-Setup-<chipid>` (WiFiManager or minimal custom AP+form), blink
   *long–short–short* so the user sees setup is waiting. User joins with a
   phone, enters SSID/password (+ API URL/key), device stores them in flash
   and reboots into the selected mode.
4. Setup timeout (~3 min) → back to deep sleep to protect the battery.
5. Re-provisioning later: hold **BOOT** (SW2) during RESET → forces setup mode
   regardless of stored credentials.

Stored credentials survive normal firmware flashes (SDK sector + LittleFS are
only wiped by a full flash erase). Energy cost of a setup session: ~15–20 mAh —
do first-time setup on USB power.

## 5. Power summary (details: [`power_budget.md`](power_budget.md))

Sleep floor **~80 µA** (was ~7.2 mA on v5 with the servo rail ungated).
Sizing at nameplate × 0.75:

| Mode | Daily | 30 days | 60 days | 90 days |
|---|---|---|---|---|
| OFF | ~34 mAh | 2000 mAh | 1× 18650 | 5000 mAh / 2× 18650 |
| SPARSE 1/h | ~38 mAh | 2000 mAh | 1× 18650 (3500) | 5000–6000 mAh / 2× 18650 |
| CONTINUOUS | ~75–90 mAh | 5000 mAh | 10 Ah / 3× 18650 | 4× 18650 — better: USB power |

---

## Schematic ↔ firmware pin map (delta vs v5)

| Net | ESP-12F pin | Function |
|---|---|---|
| `GPIO12` | GPIO12 | WiFi mode bit 0 (SW4 POS.1, LOW = OFF) |
| `GPIO14` | GPIO14 | WiFi mode bit 1 (SW4 POS.3, LOW = CONTINUOUS) |
| `GPIO15` | GPIO15 | **MT3608 enable** (boost for servo), was tied to VSYS |

Everything else unchanged (SDA/SCL GPIO4/5, SERVO_PWM GPIO13, LED GPIO2,
GPIO16→RST via JP1, VBAT_SENSE on ADC).

## Open work (not in this revision)

- **Gerbers**: layout is done (SW4 near SW3 at the board edge, D3 at the edge
  facing out; routed + refilled per repo `AGENTS.md`, DRC clean) — fabrication
  outputs not yet generated.
- **Firmware**: mode decode at boot, sparse-mode LittleFS buffering
  (`rtcData.bootCount % 12`), setup-mode captive portal, LED *long–short–short*
  pattern, BOOST_EN handling around `birdyServo.setIaq()`.

## Files

| File | Purpose |
|---|---|
| `air-quality-pcb-v6.kicad_pro/.kicad_sch` | Project + schematic (ERC clean) |
| `air-quality-pcb-v6.kicad_pcb` | v6 layout: synced, SW4 + D3 placed, routed, zones refilled |
| `drc_v6_check.rpt` | DRC report: 0 violations |
| `power_budget.md` | v6 power analysis per WiFi mode |
| `schematic_v6.pdf` | Plotted schematic |
| `bom_kicad_raw.csv` / `bom_pcbway_v6.csv` | BOM (raw / PCBWay assembly format) |
| `erc_v6.rpt` | ERC report: 0 violations |
