# Air Quality Checker — PCB v2 (round)

Second iteration of the [air-quality-checker](../air-quality-checker) board: the
same ESP8266 + BME688 + SG92R design as [v1](../), but on a **compact round
PCB** with mounting holes and a wind logo.

> The circuit is identical to v1 — only the mechanical form factor, placement
> density and silkscreen changed. See the root [README](../README.md) for the
> full electrical description and the schematic↔firmware pin map.

---

## What changed vs. v1

| | v1 | v2 |
|---|---|---|
| Shape | 108 × 108 mm square | **Ø 72 mm circle** |
| Board area | 11 664 mm² | **4 072 mm² (−65 %)** |
| Mounting | none | **4 × M2.5 holes** on the diagonal |
| Logo | none | **wind mark** + wordmark on the back silk |
| Placement | grid | polar, courtyard-legalized |

Everything on the electrical side is unchanged: ESP-12F, CP2102N, MCP73831,
AP2112K, DMG2305UX/B5819W power path, STEMMA QT, servo header, LiPo JST-PH,
RESET/BOOT buttons, deep-sleep jumper, PWR/CHG LEDs.

---

## Mechanical

- **Diameter:** 72 mm (outline Ø 72.05 mm on Edge.Cuts).
- **Mounting holes:** 4 × M2.5 (2.7 mm drill) on the 45°/135°/225°/315°
  diagonals, positioned to clear every component courtyard.
- **Connectors on the rim** for cable access:
  - USB-C (J1) — bottom
  - STEMMA QT (J2) — top
  - servo 3-pin header (J3) — right
  - LiPo JST-PH (J4) — left
- **Logo:** `wind.svg` (3 filled paths) converted to filled silkscreen polygons
  on the **bottom** silkscreen, together with `AIR QUALITY CHECKER` / `REV B`.

### Regenerating the logo

`wind.svg` lives in the repo root. The generator parses its paths
(lines + elliptical arcs) and emits `gr_poly` fills on `B.SilkS`:

```
python svg_to_poly.py wind.svg          # sanity-check the path bounds
```

---

## Verification status

| Check | Result |
|---|---|
| ERC (schematic) | **0 errors, 0 warnings** |
| DRC (board) | **0 violations, 0 unconnected** |
| Nets | 32, all routed; GND pour on both layers |
| Schematic ↔ PCB netlist | exact match (32 nets) |
| Autorouter | Freerouting 2.4.1 (Specctra DSN/SES) |

---

## Fabrication

Gerbers and drill files are in `gerbers/`. Recommended stack-up for
JLCPCB/OSHPark: 2 layers, 1.6 mm, HASL, 0.2 mm min trace.

### Regenerate outputs

```sh
kicad-cli pcb export gerbers --output gerbers/ \
  --layers "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts" \
  air-quality-pcb-v2.kicad_pcb
kicad-cli pcb export drill --output gerbers/ air-quality-pcb-v2.kicad_pcb
kicad-cli sch export bom --output bom_v2.csv air-quality-pcb-v2.kicad_sch
kicad-cli sch export pdf --output schematic_v2.pdf air-quality-pcb-v2.kicad_sch
kicad-cli pcb drc --output drc_v2.rpt air-quality-pcb-v2.kicad_pcb
kicad-cli sch erc --output erc_v2.rpt air-quality-pcb-v2.kicad_sch
```

---

## Design notes

- **Antenna keep-out:** U1's antenna region points up and stays clear of copper;
  no traces or pour run under it.
- **GND:** a single filled pour on both layers with solid (full) pad connections;
  the circular outline is approximated by a 96-point polygon inset 0.5 mm.
- **Routing:** all signal traces are ≥ 0.2 mm; the servo and power nets use wider
  traces. Freerouting's 150 µm segments were widened to 0.2 mm and re-verified.
- **Placement** was legalized against the *real* KiCad courtyards (including
  offset courtyards on connectors) so DRC is clean.

---

## Files

| File | Purpose |
|---|---|
| `air-quality-pcb-v2.kicad_pro` | Project |
| `air-quality-pcb-v2.kicad_sch` | Schematic (ERC clean) |
| `air-quality-pcb-v2.kicad_pcb` | Board (DRC clean, fully routed) |
| `schematic_v2.pdf` | Plotted schematic |
| `render_v2_top.png` / `render_v2_bottom.png` | 3D renders |
| `bom_v2.csv` | Bill of materials |
| `gerbers/` | Gerbers + drill (fabrication) |
